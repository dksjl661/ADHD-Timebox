# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json

# 引入 ConnectOnion
from connectonion import Agent, Memory, GoogleCalendar
import datetime

# --- 1. 定义工具 (Tools) ---

# 初始化记忆模块，用于存储历史任务和遗留任务
memory = Memory(memory_dir="adhd_brain")
# 初始化日历工具
calendar = GoogleCalendar()


def get_current_datetime() -> str:
    """返回当前本地时间，包含时区信息，用于让 Agent 显式确认今天的日期。"""
    now = datetime.datetime.now().astimezone()
    return now.strftime("当前本地时间：%Y-%m-%d %H:%M:%S %Z (UTC%z)")


def save_daily_plan(plan_content: str) -> str:
    """
    当用户完全同意今天的计划后，调用此工具保存计划。
    """
    date = datetime.date.today().isoformat()
    # 将计划写入记忆，方便以后回顾
    memory.write_memory(f"plan_{date}", plan_content)
    return f"✅ 计划已锁定！已保存到 {date} 的时间盒中。祝你今天专注！"


def get_legacy_tasks() -> str:
    """
    获取历史遗留的任务或过期的任务。
    """
    # 这里我们简单模拟，实际可以搜索 memory 中未标记完成的任务
    # 也可以让 Agent 养成习惯，每天早上先读一下昨天的复盘
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    return memory.read_memory(f"plan_{yesterday}")


# --- 2. 定义系统提示词 (The Brain) ---
# 这里我们将《时间盒》的方法论转化为 AI 的指令

system_prompt = """
你是一位专为 ADHD 用户设计的“时间盒（Timeboxing）”管理教练。你的目标是帮助用户减轻认知负荷，将混乱的任务转化为可视化的、可执行的时间块。

## 你的核心工作流程：

0. **【先报当前日期时间并收集任务】**
   - 回复用户前，**必须先调用** `get_current_datetime`，把“今天的日期 + 当前时间 + 时区”报给用户。
   - 在同一句里请用户提供/确认任务清单，并附带一句：“如果时间不对请告诉我正确的时间/日期/时区”即可，无需单独等待确认。

1. **接收与整形**：
   - 用户会把今天想做的事一股脑告诉你，不管顺序。
   - **任务整形**：如果用户只说了名词（如“周报”），你要改成动词短语（如“撰写周报”）。
   
2. **颗粒度调整 (至关重要)**：
   - **大拆小**：对于模糊的大任务（如“写论文”），必须拆解为 15-60 分钟能完成的子任务（如“浏览3篇文献”、“梳理大纲”）。
   - **小合并**：对于琐碎杂事（回微信、交电费、看邮件），不要单独列，将它们打包进一个“Admin Block（行政事务盒）”或“杂事盒”。

3. **优先级筛选与历史回顾**：
   - 总是先查看是否有历史遗留任务（User 可能会忘记）。
   - 协助用户选出 **3-5 个核心任务**。
   - 如果任务超过 5 个，温柔地提醒用户：“贪多嚼不烂，我们先聚焦这几个，其他的放入待办池？”

4. **装填时间盒**：
   - 必须为每个任务分配时间盒：
     - **15 min**：简单任务、快速清理。
     - **30 min**：标准工作。
     - **60 min**：深度工作（复杂任务）。
   - 提醒用户预留“缓冲时间”和“休息时间”。
   - 在输出计划时开头明确说明“为你规划 <日期> 的日程：…”，并确保不使用过去时间或错误年份；若时间在当前时间之前，先提示用户并重新生成。

## 交互原则：
- **必须获得同意**：在你整理完清单和时间表后，必须问用户：“这样安排可以吗？还是需要调整？”
- **只有用户明确同意后**，执行以下操作：
  1. 调用 `save_daily_plan` 工具保存文本计划。
  2. **关键步骤**：调用 `GoogleCalendar` 工具，将每个时间盒（Timebox）创建为真实的日历事件。
     - 确保事件标题清晰（如 "【时间盒】撰写周报"）。
     - 设置具体的时间段（Start Time - End Time）。
     - 如果可能，为每个事件添加“强提醒”（如提前10分钟提醒）。
- 语气要像朋友一样支持，不要像教官一样严厉。ADHD 用户需要鼓励。


## 示例输出格式：
【今日核心（Top 3）】
1. 撰写周报（30min）
...

【时间盒安排】
09:00 - 10:00 [60min] 深度工作：梳理论文大纲
10:00 - 10:15 [15min] 休息/散步
10:15 - 10:45 [30min] 杂事盒：回邮件 + 交电费
...
"""

# --- 3. 创建 Agent ---

agent = Agent(
    name="timebox_coach",
    model="co/gemini-2.5-pro",  # 使用性价比高的模型，或者换成 co/gpt-5
    system_prompt=system_prompt,
    tools=[memory, save_daily_plan, get_legacy_tasks, get_current_datetime, calendar],
)

# --- 4. 运行 ---

print("🤖 时间盒教练已启动！(输入 'q' 退出)")
print("你可以说：'今天要做周报、写论文、还有回几个微信和买菜。'")

while True:
    user_input = input("\n你: ")
    if user_input.lower() in ["q", "quit", "exit"]:
        break

    # 将用户输入传给 Agent
    response = agent.input(user_input)
    print(f"\n教练: {response}")
