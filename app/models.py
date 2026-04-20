"""
models.py — 数据模型

定义 User 和 Task 两个核心模型。
使用纯 Python 类模拟数据库模型，不依赖 ORM，降低环境复杂度。
"""

from datetime import datetime


class User:
    def __init__(self, user_id: int, username: str, email: str):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.created_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }

    def is_valid(self) -> bool:
        """检查用户数据是否合法"""
        if not self.username or not self.username.strip():
            return False
        if not self.email or "@" not in self.email:
            return False
        return True


class Task:
    # 任务状态常量
    STATUS_PENDING    = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_DONE       = "done"
    STATUS_CANCELLED  = "cancelled"

    VALID_STATUSES = [STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED]

    def __init__(self, task_id: int, title: str, owner_id: int, priority: int = 1):
        self.task_id   = task_id
        self.title     = title
        self.owner_id  = owner_id
        self.priority  = priority       # 1=低 2=中 3=高
        self.status    = self.STATUS_PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "task_id":    self.task_id,
            "title":      self.title,
            "owner_id":   self.owner_id,
            "priority":   self.priority,
            "status":     self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def update_status(self, new_status: str) -> bool:
        """更新任务状态，返回是否成功"""
        if new_status not in self.VALID_STATUSES:
            return False
        self.status = new_status
        self.updated_at = datetime.now()
        return True

    def is_high_priority(self) -> bool:
        return self.priority == 3
