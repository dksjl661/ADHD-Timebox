import os
import sys
import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import threading
import uvicorn
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Add current directory to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import OrchestratorAgent
from tools.idle_watcher import IdleWatcher
from tools.plan_tools_v2 import PlanManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

# Global instances
orchestrator_agent: Optional[OrchestratorAgent] = None
idle_watcher: Optional[IdleWatcher] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global orchestrator_agent, idle_watcher
    logger.info("Initializing Orchestrator Agent...")
    orchestrator_agent = OrchestratorAgent()
    
    # Initialize IdleWatcher
    def _on_idle(payload):
        try:
            logger.info(f"Idle detected: {payload}")
            # Future: Push to WebSocket
        except Exception as e:
            logger.error(f"Error in idle handler: {e}")

    logger.info("Starting IdleWatcher...")
    idle_watcher = IdleWatcher(
        context_tool=orchestrator_agent.focus_agent.context_tool if orchestrator_agent and hasattr(orchestrator_agent, 'focus_agent') else None,
        on_idle=_on_idle,
        interval_seconds=30,
        idle_threshold_seconds=300,
        cooldown_seconds=600,
        focus_only=True
    )
    idle_watcher.start()
    
    yield
    
    # Shutdown
    if idle_watcher:
        idle_watcher.stop()
    logger.info("Backend shut down.")

app = FastAPI(title="ADHD Timebox Backend", lifespan=lifespan)

# CORS - Allow all for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    status: str

class Task(BaseModel):
    id: str
    title: str
    priority: str = "medium"
    estimatedMinutes: Optional[int] = None
    cognitiveLoad: Optional[str] = "medium"
    status: Optional[str] = "pending"
    start: Optional[str] = None
    end: Optional[str] = None

class TaskList(BaseModel):
    tasks: List[Task]

class RecommendationRequest(BaseModel):
    context: Dict[str, Any] # Flexible context

class RecommendationResponse(BaseModel):
    taskId: str
    durationMinutes: int
    reason: str
    preferLowCognitiveLoad: bool

# --- Endpoints ---

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not orchestrator_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        response = orchestrator_agent.route(request.message)
        # The route method returns a string directly
        return ChatResponse(response=response, status="success")
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks", response_model=List[Dict])
async def get_tasks():
    if not orchestrator_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Use PlanManager to list tasks
        pm = orchestrator_agent.plan_manager
        today = datetime.date.today()
        plan_date, date_err = pm._parse_plan_date("today", today)
        tasks, _, _ = pm._load_tasks(plan_date.isoformat(), create_if_missing=True)
        
        # Map to frontend Task format
        mapped_tasks = []
        if tasks:
            for t in tasks:
                mapped_tasks.append({
                    "id": t.get("id") or t.get("title"),
                    "title": t.get("title"),
                    "priority": t.get("priority", "medium"), # backend might not have this, default
                    "estimatedMinutes": None, # backend uses start/end for duration
                    "cognitiveLoad": "medium", # backend might not have this
                    "status": t.get("status", "pending")
                })
        return mapped_tasks
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest):
    # Retrieve tasks from backend state
    tasks = await get_tasks()
    
    if not tasks:
         # Fallback if no tasks
         return RecommendationResponse(
             taskId="dummy",
             durationMinutes=25,
             reason="No tasks found, please add some.",
             preferLowCognitiveLoad=False
         )

    # Simple heuristic for now: pick first pending task
    pending_tasks = [t for t in tasks if t["status"] != "completed"]
    if not pending_tasks:
         return RecommendationResponse(
             taskId="dummy",
             durationMinutes=15,
             reason="All tasks completed! Take a break.",
             preferLowCognitiveLoad=True
         )
         
    target_task = pending_tasks[0]
    
    return RecommendationResponse(
        taskId=target_task["id"],
        durationMinutes=25, # Default, or calculate from start/end
        reason="Scheduled next task",
        preferLowCognitiveLoad=False
    )

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
