"""
test_models.py — 模型层测试

故意只覆盖部分场景，用于触发 Agent 场景一（测试用例维护）和场景四（覆盖率补全）。
缺少的测试用例已在注释中标注。
"""

import pytest
from datetime import datetime
from models import User, Task


class TestUser:

    def test_create_user(self):
        """正常创建用户"""
        user = User(1, "alice", "alice@example.com")
        assert user.user_id == 1
        assert user.username == "alice"
        assert user.email == "alice@example.com"

    def test_user_to_dict(self):
        """to_dict 返回正确的字段"""
        user = User(1, "alice", "alice@example.com")
        d = user.to_dict()
        assert d["user_id"] == 1
        assert d["username"] == "alice"
        assert d["email"] == "alice@example.com"
        assert "created_at" in d

    def test_user_is_valid(self):
        """合法用户通过校验"""
        user = User(1, "alice", "alice@example.com")
        assert user.is_valid() is True

    def test_user_invalid_empty_username(self):
        """空用户名不合法"""
        user = User(1, "", "alice@example.com")
        assert user.is_valid() is False

    # 缺少的测试（故意不写，供 Agent 场景四补全）：
    # - test_user_invalid_no_at_in_email
    # - test_user_invalid_whitespace_username
    # - test_user_to_dict_created_at_format


class TestTask:

    def test_create_task_default_priority(self):
        """默认优先级为 1"""
        task = Task(1, "写文档", 1)
        assert task.priority == 1
        assert task.status == Task.STATUS_PENDING

    def test_task_to_dict(self):
        """to_dict 返回正确字段"""
        task = Task(1, "写文档", 1, priority=2)
        d = task.to_dict()
        assert d["task_id"] == 1
        assert d["title"] == "写文档"
        assert d["priority"] == 2
        assert d["status"] == "pending"

    def test_update_status_valid(self):
        """合法状态更新成功"""
        task = Task(1, "写文档", 1)
        result = task.update_status(Task.STATUS_IN_PROGRESS)
        assert result is True
        assert task.status == Task.STATUS_IN_PROGRESS

    def test_update_status_invalid(self):
        """非法状态更新失败"""
        task = Task(1, "写文档", 1)
        result = task.update_status("flying")
        assert result is False
        assert task.status == Task.STATUS_PENDING

    def test_task_without_deadline(self):
        """创建任务时不指定截止日期"""
        task = Task(1, "写文档", 1)
        assert task.deadline is None
        assert task.to_dict()["deadline"] is None

    def test_task_with_deadline(self):
        """创建任务时指定截止日期"""
        deadline = datetime(2025, 12, 31, 23, 59, 59)
        task = Task(1, "写文档", 1, deadline=deadline)
        assert task.deadline == deadline
        assert task.to_dict()["deadline"] == deadline.isoformat()

    # 缺少的测试（故意不写，供 Agent 场景四补全）：
    # - test_is_high_priority_true
    # - test_is_high_priority_false
    # - test_update_status_updates_updated_at
    # - test_task_valid_statuses_list
