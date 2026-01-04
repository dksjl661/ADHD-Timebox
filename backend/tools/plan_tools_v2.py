import datetime
import json
import os
from typing import Dict, List, Optional, Tuple, Union


# 【新增 1】定义一个强力调试函数，直接写文件，绕过控制台
def debug_log(message):
    try:
        # 获取 backend 目录 (假设当前脚本在 backend/tools 下)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_path = os.path.join(base_dir, "FORCE_DEBUG.txt")

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass  # 绝不报错


# 【新增 2】模块加载证明
debug_log(">>> plan_tools_v2 模块已被加载！<<<")


class PlanManager:
    """
    管理 daily_tasks_YYYY-MM-DD.json 的读写与冲突检测。
    设计目标：为 PlannerAgent 提供可靠的上下文感知与时间盒调整能力。
    """

    def __init__(self, plan_dir: Optional[str] = None, calendar=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_plan_dir = os.path.join(base_dir, "adhd_brain")
        self.plan_dir = plan_dir or default_plan_dir
        os.makedirs(self.plan_dir, exist_ok=True)
        self.calendar = calendar

    # -- 公共方法 --

    def get_current_context(self) -> str:
        """
        返回当前日期/时间/时区，以及今日计划摘要（若存在）。
        确保 Agent 在生成或调整时不会落入过去时间。
        """
        now = datetime.datetime.now().astimezone()
        now_text = now.strftime("%Y-%m-%d %H:%M %Z (UTC%z)")
        today = now.date()
        tasks, path, err = self._load_tasks(today.isoformat(), create_if_missing=False)
        header = f"当前时间：{now_text}"
        if err:
            return f"{header}\n今日计划读取失败：{err}"
        if tasks is None or not tasks:
            return (
                f"{header}\n今日尚未生成计划文件：{self._plan_path(today.isoformat())}"
            )

        summary_lines = []
        plan_date = self._plan_date_from_path(path)
        normalized = self._normalize_for_summary(tasks, plan_date)
        for idx, task in enumerate(normalized, start=1):
            start_text = (
                task["start_dt"].strftime("%H:%M")
                if task["start_dt"]
                else (task["raw_start"] or "-")
            )
            end_text = (
                task["end_dt"].strftime("%H:%M")
                if task["end_dt"]
                else (task["raw_end"] or "-")
            )
            title = task.get("title") or f"任务{idx}"
            status = task.get("status", "pending")
            status_mark = f" [{status}]" if status != "pending" else ""
            summary_lines.append(
                f"{idx}. {start_text}-{end_text} | {title}{status_mark}"
            )
        summary = "\n".join(summary_lines)
        return f"{header}\n今日计划：\n{summary}"

    def create_daily_plan(self, tasks: Union[List[Dict], str]) -> str:
        """
        覆盖写入今日计划。

        Args:
            tasks: 任务列表。每个任务必须是字典，且严格包含以下键：
                - "title": (str) 任务标题。注意：必须用 "title"，不要用 "name" 或 "task"。
                - "start": (str) 开始时间，格式 "YYYY-MM-DD HH:MM"。
                - "end": (str) 结束时间，格式 "YYYY-MM-DD HH:MM"。
                - "type": (str, optional) 任务类型，默认为 "work"。
        """
        # 【新增 3】函数入口证明
        debug_log(f"create_daily_plan 被调用！参数类型: {type(tasks)}")

        # 记录一下原始数据的前 100 个字符，看看传进来的是啥
        debug_log(f"原始数据摘要: {str(tasks)[:100]}...")

        original_tasks = tasks
        if isinstance(tasks, str):
            try:
                tasks = json.loads(tasks)
            except json.JSONDecodeError as exc:
                err_msg = f"JSON 解析崩溃: {exc}"
                debug_log(err_msg)  # 【新增】记录错误
                return (
                    "❌ 计划生成失败：tasks 需为列表或可解析的 JSON 字符串，"
                    f"解析错误：{exc}"
                )

        if not isinstance(tasks, list):
            err_msg = f"类型错误: 期望 list, 实际是 {type(original_tasks).__name__}"
            debug_log(err_msg)  # 【新增】记录错误
            return (
                "❌ 计划生成失败：tasks 必须是任务字典的列表，"
                f"当前类型 {type(original_tasks).__name__}。"
            )

        now = datetime.datetime.now().astimezone()
        plan_date = now.date()
        normalized_tasks = []
        errors: List[str] = []

        for idx, task in enumerate(tasks):
            if not isinstance(task, dict):
                errors.append(f"第 {idx + 1} 条任务格式需为字典。")
                continue

            title = (task.get("title") or "").strip()
            if not title:
                errors.append(f"第 {idx + 1} 条缺少标题。")
                continue

            start_dt = self._normalize_to_dt(task.get("start"), plan_date)
            end_dt = self._normalize_to_dt(task.get("end"), plan_date)
            if not start_dt or not end_dt:
                errors.append(
                    f"{title} 的时间格式无法解析：{task.get('start')} -> {task.get('end')}"
                )
                continue
            if start_dt.date() != plan_date or end_dt.date() != plan_date:
                errors.append(f"{title} 的日期不是今天（{plan_date.isoformat()}）。")
                continue
            if end_dt <= start_dt:
                errors.append(f"{title} 的结束时间必须晚于开始时间。")
                continue
            if start_dt < now:
                errors.append(
                    f"{title} 的开始时间 ({start_dt.strftime('%H:%M')}) 已早于当前时间。"
                )
                continue

            normalized_task = {**task}
            normalized_task["id"] = (
                task.get("id") or f"task_{int(now.timestamp())}_{idx}"
            )
            normalized_task["title"] = title
            normalized_task["start"] = start_dt.strftime("%Y-%m-%d %H:%M")
            normalized_task["end"] = end_dt.strftime("%Y-%m-%d %H:%M")
            normalized_task.setdefault("type", "work")
            normalized_task.setdefault("status", "pending")  # 默认状态
            normalized_tasks.append(normalized_task)

        if errors:
            debug_log(f"校验失败，errors: {errors}")  # 【新增】记录校验错误
            return "❌ 计划未保存：" + "；".join(errors)
        if not normalized_tasks:
            debug_log("未发现有效任务")  # 【新增】记录无任务
            return "❌ 计划未保存：未提供有效任务。"

        normalized_tasks.sort(key=lambda t: t.get("start", ""))

        path = self._plan_path(plan_date.isoformat())
        debug_log(f"准备写入文件，目标路径: {path}")  # 【新增】记录路径

        try:
            with open(path, "w") as f:
                json.dump(normalized_tasks, f, ensure_ascii=False, indent=2)
            debug_log("✅ 文件写入成功！")  # 【新增】确认写入
        except Exception as e:
            debug_log(f"❌ 致命错误：文件写入失败 - {e}")  # 【新增】捕获 IO 错误
            return f"❌ 文件写入失败：{e}"

        # 自动同步到日历
        sync_available = bool(self.calendar and hasattr(self.calendar, "create_event"))
        sync_success = 0
        sync_failure = 0
        failure_details: List[str] = []

        for task in normalized_tasks:
            title = task.get("title") or task.get("id") or "未命名任务"
            sync_msg = self._sync_calendar(
                title, task.get("start", ""), task.get("end", "")
            )
            if "同步失败" in sync_msg:
                sync_failure += 1
                failure_details.append(f"{title}: {sync_msg.lstrip('，')}")
            elif sync_msg:
                sync_success += 1

        sync_summary = ""
        if not sync_available:
            sync_summary = " 日历同步未执行：Calendar 未配置或不支持。"
        else:
            sync_summary = (
                f" 日历同步：成功 {sync_success} 个，失败 {sync_failure} 个。"
            )
            if failure_details:
                sync_summary += " 失败详情：" + "；".join(failure_details)

        return (
            f"✅ 今日计划已保存，共 {len(normalized_tasks)} 条任务。路径：{path}"
            f"{sync_summary}"
        )

    def update_schedule(
        self, task_id: str, new_start: str, new_end: str, force: bool = False
    ) -> str:
        """
        修改已有任务或插入新任务。
        - 冲突时返回 CONFLICT 消息（除非 force=True）
        - 成功后写回 JSON，并尝试同步日历
        """
        plan_date_str = datetime.date.today().isoformat()
        tasks, path, err = self._load_tasks(plan_date_str, create_if_missing=True)
        if err:
            return f"❌ 更新失败：{err}"
        if tasks is None:
            return f"❌ 更新失败：计划文件格式异常：{path}"

        plan_date = self._plan_date_from_path(path)
        start_dt = self._normalize_to_dt(new_start, plan_date)
        end_dt = self._normalize_to_dt(new_end, plan_date)
        if not start_dt or not end_dt:
            return f"❌ 时间格式无法解析：{new_start} -> {new_end}"
        if start_dt.date() != plan_date or end_dt.date() != plan_date:
            return f"❌ 仅支持调整今日（{plan_date.isoformat()}）的时间盒。"
        if end_dt <= start_dt:
            return "❌ 结束时间必须晚于开始时间。"
        if start_dt < datetime.datetime.now().astimezone():
            return f"❌ 新开始时间 {start_dt.strftime('%H:%M')} 早于当前时间。"

        target_task = self._find_task(tasks, task_id)
        conflicts = self._find_conflicts(
            tasks, start_dt, end_dt, plan_date, exclude=target_task
        )

        if conflicts and not force:
            conflict_names = ", ".join(
                [c.get("title") or c.get("id") or "未命名任务" for c in conflicts]
            )
            return f"CONFLICT: {conflict_names}"

        if conflicts:
            for c in conflicts:
                tasks.remove(c)

        start_text = start_dt.strftime("%Y-%m-%d %H:%M")
        end_text = end_dt.strftime("%Y-%m-%d %H:%M")
        created = False

        if target_task:
            target_task["start"] = start_text
            target_task["end"] = end_text
        else:
            new_task = {
                "id": task_id,
                "title": task_id,
                "start": start_text,
                "end": end_text,
                "type": "work",
                "status": "pending",  # 默认状态
            }
            tasks.append(new_task)
            target_task = new_task
            created = True

        tasks.sort(key=lambda t: t.get("start", ""))
        with open(path, "w") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

        sync_msg = self._sync_calendar(
            target_task.get("title") or task_id, start_text, end_text
        )
        action = "已添加" if created else "已更新"
        replaced = f"，替换了 {len(conflicts)} 个冲突任务" if conflicts else ""
        return f"✅ {action} {task_id}: {start_text[11:]}-{end_text[11:]}{replaced}{sync_msg}"

    def list_tasks(self) -> str:
        """列出今日计划的所有任务及状态。"""
        today = datetime.date.today().isoformat()
        tasks, path, err = self._load_tasks(today, create_if_missing=False)
        if err:
            return f"❌ {err}"
        if tasks is None or not tasks:
            return f"今日无计划：{self._plan_path(today)}"

        plan_date = self._plan_date_from_path(path)
        normalized = self._normalize_for_summary(tasks, plan_date)
        lines = [f"计划文件：{path}"]
        for idx, task in enumerate(normalized, start=1):
            start_text = (
                task["start_dt"].strftime("%H:%M")
                if task["start_dt"]
                else (task["raw_start"] or "-")
            )
            end_text = (
                task["end_dt"].strftime("%H:%M")
                if task["end_dt"]
                else (task["raw_end"] or "-")
            )
            title = task.get("title") or f"任务{idx}"
            status = task.get("status", "pending")
            lines.append(
                f"{idx}. {start_text}-{end_text} | {title} [{status}] (id={task.get('id', '?')})"
            )
        return "\n".join(lines)

    # -- 内部辅助方法 --

    def _plan_path(self, date_str: str) -> str:
        return os.path.join(self.plan_dir, f"daily_tasks_{date_str}.json")

    def _plan_date_from_path(self, path: str) -> datetime.date:
        try:
            return datetime.datetime.strptime(
                os.path.basename(path).replace("daily_tasks_", "").replace(".json", ""),
                "%Y-%m-%d",
            ).date()
        except Exception:
            return datetime.date.today()

    def _load_tasks(
        self, target_date: str, create_if_missing: bool
    ) -> Tuple[Optional[List[Dict]], str, Optional[str]]:
        path = self._plan_path(target_date)
        if not os.path.exists(path):
            if create_if_missing:
                return [], path, None
            return None, path, f"未找到计划文件：{path}"
        try:
            with open(path, "r") as f:
                tasks = json.load(f)
        except Exception as exc:
            return None, path, f"读取计划失败：{exc}"
        if not isinstance(tasks, list):
            return None, path, "计划文件格式应为列表。"
        return tasks, path, None

    def _normalize_to_dt(
        self, raw_value: Optional[str], plan_date: datetime.date
    ) -> Optional[datetime.datetime]:
        """将各种常见格式解析为带时区的 datetime。"""
        if not raw_value or not isinstance(raw_value, str):
            return None
        value = raw_value.strip()
        tzinfo = datetime.datetime.now().astimezone().tzinfo

        try:
            dt = datetime.datetime.fromisoformat(value.replace("T", " "))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tzinfo)
            return dt.astimezone(tzinfo)
        except Exception:
            pass

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                dt = datetime.datetime.strptime(value, fmt)
                return dt.replace(tzinfo=tzinfo)
            except ValueError:
                continue

        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                t = datetime.datetime.strptime(value, fmt).time()
                return datetime.datetime.combine(plan_date, t).replace(tzinfo=tzinfo)
            except ValueError:
                continue

        return None

    def _find_task(self, tasks: List[Dict], task_id: str) -> Optional[Dict]:
        for task in tasks:
            if task.get("id") == task_id or task.get("title") == task_id:
                return task
        return None

    def _find_conflicts(
        self,
        tasks: List[Dict],
        start_dt: datetime.datetime,
        end_dt: datetime.datetime,
        plan_date: datetime.date,
        exclude: Optional[Dict] = None,
    ) -> List[Dict]:
        conflicts: List[Dict] = []
        for task in tasks:
            if task is exclude:
                continue
            t_start = self._normalize_to_dt(task.get("start"), plan_date)
            t_end = self._normalize_to_dt(task.get("end"), plan_date)
            if not t_start or not t_end:
                continue
            if start_dt < t_end and end_dt > t_start:
                conflicts.append(task)
        return conflicts

    def _normalize_for_summary(
        self, tasks: List[Dict], plan_date: datetime.date
    ) -> List[Dict]:
        """为摘要排序并附带解析后的时间，便于展示。"""
        normalized = []
        for task in tasks:
            start_dt = self._normalize_to_dt(task.get("start"), plan_date)
            end_dt = self._normalize_to_dt(task.get("end"), plan_date)
            normalized.append(
                {
                    **task,
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                    "raw_start": task.get("start"),
                    "raw_end": task.get("end"),
                }
            )
        normalized.sort(
            key=lambda t: t.get("start_dt")
            or datetime.datetime.max.replace(
                tzinfo=datetime.datetime.now().astimezone().tzinfo
            )
        )
        return normalized

    def _sync_calendar(self, title: str, start: str, end: str) -> str:
        """尝试同步到 Google Calendar，失败不抛异常。"""
        # 1. 检查日历对象是否存在
        if not self.calendar or isinstance(self.calendar, str):  # 防御性编程
            debug_log(f"[Calendar] 未配置或类型错误: {type(self.calendar)}")
            return ""

        # 检查是否是那个 Fallback 类 (Dummy)
        if hasattr(self.calendar, "reason"):
            debug_log(f"[Calendar] 处于 Fallback 模式: {self.calendar.reason}")
            return ""

        if not hasattr(self.calendar, "create_event"):
            debug_log("[Calendar] 对象缺少 create_event 方法")
            return ""

        # 2. 格式清洗：将 "2026-01-03 19:30" 转为 "2026-01-03T19:30:00"
        # Google Calendar API 通常更喜欢 ISO 格式
        def to_iso(time_str):
            try:
                if "T" not in time_str:
                    # 补全秒数和 T
                    return time_str.replace(" ", "T") + ":00"
                return time_str
            except Exception:
                return time_str

        iso_start = to_iso(start)
        iso_end = to_iso(end)

        debug_log(f"[Calendar] 尝试写入: {title} | {iso_start} -> {iso_end}")

        try:
            # 尝试调用，优先适配常见库的参数名
            try:
                self.calendar.create_event(
                    title=title, start_time=iso_start, end_time=iso_end
                )
            except TypeError:
                # 再次尝试另一种参数风格
                self.calendar.create_event(title=title, start=iso_start, end=iso_end)

            debug_log(f"[Calendar] ✅ 写入成功: {title}")
            return "，并已同步到日历"

        except Exception as exc:
            # 【关键】把具体的报错写进日志文件
            debug_log(
                f"[Calendar] ❌ 写入失败: {exc} | 参数: {title}, {iso_start}-{iso_end}"
            )
            return f"，但日历同步失败：{exc}"
