"""
utils.py — 工具函数

注意：此文件覆盖率故意保持低于 60%，用于触发 Agent 场景四（覆盖率补全）。
大量函数没有对应的测试用例。
"""

import re
from datetime import datetime, timedelta


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def validate_username(username: str) -> bool:
    """
    验证用户名格式：
    - 长度 3-20 个字符
    - 只允许字母、数字、下划线
    - 不能以数字开头
    """
    if not username or len(username) < 3 or len(username) > 20:
        return False
    pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
    return bool(re.match(pattern, username))


def validate_priority(priority: int) -> bool:
    """验证优先级是否合法（1/2/3）"""
    return priority in (1, 2, 3)


def format_datetime(dt: datetime) -> str:
    """将 datetime 格式化为可读字符串"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_datetime(dt_str: str) -> datetime | None:
    """将字符串解析为 datetime，失败返回 None"""
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


def is_overdue(due_date: datetime) -> bool:
    """判断任务是否已超期"""
    return datetime.now() > due_date


def days_until_due(due_date: datetime) -> int:
    """返回距离截止日期还有多少天，已超期返回负数"""
    delta = due_date - datetime.now()
    return delta.days


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断文本，超出部分用 suffix 替代"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def slugify(text: str) -> str:
    """
    将文本转换为 URL 友好的 slug 格式。
    例如: "Hello World!" → "hello-world"
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def paginate(items: list, page: int, page_size: int = 10) -> dict:
    """
    对列表进行分页。

    返回:
    {
        "items": [...],
        "total": 100,
        "page": 1,
        "page_size": 10,
        "total_pages": 10
    }
    """
    if page < 1:
        page = 1
    total = len(items)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items":       items[start:end],
        "total":       total,
        "page":        page,
        "page_size":   page_size,
        "total_pages": total_pages,
    }


def mask_email(email: str) -> str:
    """
    对邮箱进行脱敏处理。
    例如: "user@example.com" → "u***@example.com"
    """
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        return f"{local}***@{domain}"
    return f"{local[0]}***@{domain}"


def generate_task_code(task_id: int, prefix: str = "TASK") -> str:
    """生成任务编号，如 TASK-0042"""
    return f"{prefix}-{task_id:04d}"


def calculate_workdays(start: datetime, end: datetime) -> int:
    """计算两个日期之间的工作日数量（不含周末）"""
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # 0-4 是周一到周五
            count += 1
        current += timedelta(days=1)
    return count


def get_overdue_tasks_count(tasks: list) -> int:
    """统计超期任务数量"""
    now = datetime.now()
    return sum(
        1 for t in tasks
        if hasattr(t, "deadline") and t.deadline and t.deadline < now
    )
