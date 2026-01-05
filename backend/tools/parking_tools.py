"""Shared parking lot service for focus/orchestration agents."""

import datetime
import json
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(str, Enum):
    SEARCH = "search"
    MEMO = "memo"
    TODO = "todo"


class ParkingService:
    """Core parking service that stores thoughts and runs optional background search."""

    def __init__(self, brain_dir: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.brain_dir = brain_dir or os.path.join(base_dir, "adhd_brain")
        self.parking_dir = os.path.join(self.brain_dir, "thought_parking")
        os.makedirs(self.parking_dir, exist_ok=True)

        self._current_file = os.path.join(self.parking_dir, "current_parking.json")
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._session_id: Optional[str] = None
        self._lock = threading.RLock()

    # ── Public API ─────────────────────────────────────────────

    def dispatch_task(
        self,
        content: str,
        task_type: str = TaskType.SEARCH.value,
        source: str = "unknown",
        run_async: bool = True,
    ) -> str:
        """
        Primary entry: stash a thought or query, optionally processed in background.
        """
        normalized_type = (task_type or TaskType.SEARCH.value).lower()
        task_id = str(uuid.uuid4())[:8]
        now = datetime.datetime.now()

        task = {
            "id": task_id,
            "content": content,
            "type": normalized_type,
            "source": source,
            "status": TaskStatus.PENDING.value,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "session_id": self._session_id,
            "result": None,
            "error": None,
        }

        self._append_task(task)
        self._log_to_daily(
            f"[{now.strftime('%H:%M:%S')}] 📥 收到: {content} (from {source})"
        )

        if run_async and normalized_type == TaskType.SEARCH.value:
            # Fire-and-forget search so it never blocks focus flow.
            self._executor.submit(self._process_task_background, task_id)

        preview = content[:30]
        suffix = "..." if len(content) > 30 else ""
        return f"📥 已记录：「{preview}{suffix}」"

    def get_session_summary(self, session_id: Optional[str] = None) -> str:
        """
        Retrieve summary for the current or specified session.
        """
        target_session = session_id or self._session_id
        tasks = self._load_tasks()
        session_tasks = [
            t
            for t in tasks
            if t.get("session_id") == target_session or target_session is None
        ]

        if not session_tasks:
            return "📭 本次专注期间没有暂存的念头。"

        lines = ["📋 **专注期间暂存的念头处理报告：**", ""]
        for task in session_tasks:
            status = task.get("status", TaskStatus.PENDING.value)
            content = task.get("content", "")[:50]
            result = task.get("result")

            if status == TaskStatus.COMPLETED.value and result:
                tail = "..." if len(result) > 200 else ""
                lines.append(f"✅ 「{content}」")
                lines.append(f"   → {result[:200]}{tail}")
            elif status == TaskStatus.PENDING.value:
                lines.append(f"⏳ 「{content}」 - 仍在处理中")
            elif status == TaskStatus.FAILED.value:
                lines.append(f"❌ 「{content}」 - 处理失败")
            else:
                lines.append(f"📝 「{content}」 - 已记录")
            lines.append("")

        return "\n".join(lines).rstrip()

    def list_pending_tasks(self) -> str:
        """List all pending tasks for quick inspection."""
        tasks = self._load_tasks()
        pending = [t for t in tasks if t.get("status") == TaskStatus.PENDING.value]

        if not pending:
            return "📭 当前没有待处理的暂存念头。"

        lines = [f"📋 待处理任务 ({len(pending)} 个)："]
        for task in pending:
            content = task.get("content", "")[:40]
            lines.append(f"  - {content} [{task.get('type', TaskType.MEMO.value)}]")
        return "\n".join(lines)

    def start_session(self) -> str:
        """Mark the beginning of a focus session."""
        self._session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return self._session_id

    def end_session(self) -> str:
        """End active session and return a formatted summary."""
        summary = self.get_session_summary()
        self._session_id = None
        return summary

    # ── Internal helpers ──────────────────────────────────────

    def _load_tasks(self) -> List[Dict[str, Any]]:
        with self._lock:
            if not os.path.exists(self._current_file):
                return []
            try:
                with open(self._current_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
            except Exception:
                return []

    def _save_tasks(self, tasks: List[Dict[str, Any]]):
        with self._lock:
            with open(self._current_file, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)

    def _append_task(self, task: Dict[str, Any]):
        with self._lock:
            tasks = self._load_tasks()
            tasks.append(task)
            self._save_tasks(tasks)

    def _update_task(self, task_id: str, updates: Dict[str, Any]):
        with self._lock:
            tasks = self._load_tasks()
            for task in tasks:
                if task.get("id") == task_id:
                    task.update(updates)
                    break
            self._save_tasks(tasks)

    def _log_to_daily(self, message: str):
        # Logging to a text file is append-only, less critical to lock but good practice.
        # However, Python's file append is atomic on POSIX for small writes.
        # We'll lock to be consistent.
        with self._lock:
            today = datetime.date.today().isoformat()
            log_path = os.path.join(self.parking_dir, f"thought_parking_{today}.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(message + "\n")

    def _process_task_background(self, task_id: str):
        """Execute background work for search tasks without blocking user flow."""
        self._update_task(task_id, {"status": TaskStatus.PROCESSING.value})

        tasks = self._load_tasks()
        task = next((t for t in tasks if t.get("id") == task_id), None)
        if not task:
            return

        content = task.get("content", "")

        try:
            result = self._perform_search(content)
            self._update_task(
                task_id,
                {
                    "status": TaskStatus.COMPLETED.value,
                    "result": result,
                    "completed_at": datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                },
            )
            self._log_to_daily(
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ 完成: {content[:30]}"
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            self._update_task(
                task_id, {"status": TaskStatus.FAILED.value, "error": str(exc)}
            )
            self._log_to_daily(
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ 失败: {content[:30]} - {exc}"
            )

    def _perform_search(self, query: str) -> str:
        """
        Use a temporary Agent equipped with WebFetch to research the query.
        Fixed based on WebFetch documentation limitations.
        """
        try:
            # 引入组件
            from connectonion import Agent, WebFetch
        except ImportError:
            return "[系统错误] 无法导入 ConnectOnion 组件。"

        try:
            # [关键修改] 提示词适配 WebFetch 的能力
            # WebFetch 只能处理 URL，不能处理关键词搜索。
            # 我们通过 System Prompt 引导 Agent 尝试构建 URL (如 Wikipedia) 或 告知用户需要 URL。

            system_instruction = (
                "你是一个基于 WebFetch 工具的网页分析助手。"
                "【重要】你的工具 WebFetch 只能接收 URL (例如 https://example.com)，不能接收搜索关键词。"
                "1. 如果用户提供的是一个 URL：请使用 fetch 或 analyze_page 工具获取内容并总结。"
                "2. 如果用户提供的是关键词（非 URL）："
                "   - 尝试猜测相关的 Wikipedia URL (例如 https://en.wikipedia.org/wiki/Keyword) 并尝试抓取。"
                "   - 或者直接告诉用户：'WebFetch 工具无法进行搜索，请提供具体的 URL'。"
                "不要尝试编造不存在的 URL。"
            )

            # 初始化 Agent
            # 根据文档，WebFetch 不需要参数初始化
            web_tool = WebFetch()

            searcher = Agent(
                name="parking_searcher",
                model="co/gemini-2.5-pro",
                tools=[web_tool],
                system_prompt=system_instruction,
                quiet=True,
            )

            # 构建 Prompt，引导模型正确调用工具
            prompt = f"请分析以下内容：\n\n{query}\n\n如果这是网址，请总结它；如果这不是网址，请尝试通过构造 URL (如维基百科) 来获取信息。"

            # 执行
            result = searcher.input(prompt)
            return str(result)

        except Exception as e:
            # 捕获所有工具调用层面的错误，防止 500 崩溃
            import traceback

            traceback.print_exc()
            return f"[处理失败] Agent 遇到错误: {str(e)}"


class ParkingToolkit:
    """Agent-facing toolkit wrapper around ParkingService."""

    def __init__(self, service: Optional[ParkingService] = None):
        self.service = service or ParkingService()

    def park_thought(
        self, content: str, thought_type: str = TaskType.SEARCH.value
    ) -> str:
        """
        Stash a thought or query for background processing.
        thought_type: search | memo | todo
        """
        normalized_type = (thought_type or TaskType.SEARCH.value).lower()
        return self.service.dispatch_task(
            content=content,
            task_type=normalized_type,
            source="focus_mode",
            run_async=True,
        )

    def get_parking_summary(self) -> str:
        """Return processed results for the active focus session."""
        return self.service.get_session_summary()
