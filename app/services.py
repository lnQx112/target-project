"""
services.py — 业务逻辑层

注意：此文件故意埋入了 3 个 bug，用于触发 Agent 场景二（失败分类）。
bug 位置已在注释中标注，方便对照测试结果。
"""

from models import User, Task


# 内存存储，模拟数据库
_users: dict[int, User] = {}
_tasks: dict[int, Task] = {}
_next_user_id = 1
_next_task_id = 1


# ── User 相关 ────────────────────────────────────────────────

def create_user(username: str, email: str) -> User:
    """创建新用户"""
    global _next_user_id
    user = User(_next_user_id, username, email)
    if not user.is_valid():
        raise ValueError(f"用户数据不合法: username={username}, email={email}")
    _users[_next_user_id] = user
    _next_user_id += 1
    return user


def get_user(user_id: int) -> User | None:
    """根据 ID 获取用户，不存在返回 None"""
    return _users.get(user_id)


def list_users() -> list[User]:
    """返回所有用户列表"""
    return list(_users.values())


def delete_user(user_id: int) -> bool:
    """删除用户，同时删除该用户的所有任务"""
    if user_id not in _users:
        return False
    del _users[user_id]
    # 删除该用户的所有任务
    to_delete = [tid for tid, t in _tasks.items() if t.owner_id == user_id]
    for tid in to_delete:
        del _tasks[tid]
    return True


# ── Task 相关 ────────────────────────────────────────────────

def create_task(title: str, owner_id: int, priority: int = 1) -> Task:
    """
    创建新任务。

    BUG #1: 没有校验 owner_id 是否存在，
    导致可以为不存在的用户创建任务。
    正确做法应该先 get_user(owner_id)，不存在则抛出异常。
    """
    global _next_task_id
    task = Task(_next_task_id, title, owner_id, priority)
    _tasks[_next_task_id] = task
    _next_task_id += 1
    return task


def get_task(task_id: int) -> Task | None:
    """根据 ID 获取任务"""
    return _tasks.get(task_id)


def list_tasks_by_user(user_id: int) -> list[Task]:
    """获取某个用户的所有任务"""
    return [t for t in _tasks.values() if t.owner_id == user_id]


def update_task_status(task_id: int, new_status: str) -> bool:
    """更新任务状态"""
    task = get_task(task_id)
    if task is None:
        return False
    return task.update_status(new_status)


def get_high_priority_tasks() -> list[Task]:
    """
    获取所有高优先级任务。

    BUG #2: 优先级比较用了字符串比较而不是整数比较，
    导致 priority=3 的任务无法被正确筛选出来。
    正确做法: t.priority == 3 或 t.is_high_priority()
    """
    return [t for t in _tasks.values() if t.priority == "3"]  # BUG: 应为整数 3


def get_task_summary() -> dict:
    """
    返回任务统计摘要。

    BUG #3: 计算完成率时除数没有做零值保护，
    当没有任务时会触发 ZeroDivisionError。
    正确做法: total = len(_tasks) or 1
    """
    total = len(_tasks)
    done  = len([t for t in _tasks.values() if t.status == Task.STATUS_DONE])
    return {
        "total":           total,
        "done":            done,
        "completion_rate": done / total,   # BUG: total 为 0 时崩溃
        "pending":         len([t for t in _tasks.values() if t.status == Task.STATUS_PENDING]),
        "in_progress":     len([t for t in _tasks.values() if t.status == Task.STATUS_IN_PROGRESS]),
    }


def clear_all():
    """清空所有数据（测试用）"""
    global _next_user_id, _next_task_id
    _users.clear()
    _tasks.clear()
    _next_user_id = 1
    _next_task_id = 1
