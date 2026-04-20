"""
test_services.py — 业务逻辑层测试

包含会触发 bug 的测试用例，用于触发 Agent 场景二（失败分类）。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
import services


@pytest.fixture(autouse=True)
def reset_storage():
    """每个测试前清空内存存储，保证测试隔离"""
    services.clear_all()
    yield
    services.clear_all()


class TestUserService:

    def test_create_user_success(self):
        """正常创建用户"""
        user = services.create_user("alice", "alice@example.com")
        assert user.user_id == 1
        assert user.username == "alice"

    def test_create_user_invalid_email(self):
        """非法邮箱抛出异常"""
        with pytest.raises(ValueError):
            services.create_user("alice", "not-an-email")

    def test_get_user_exists(self):
        """获取存在的用户"""
        services.create_user("alice", "alice@example.com")
        user = services.get_user(1)
        assert user is not None
        assert user.username == "alice"

    def test_get_user_not_exists(self):
        """获取不存在的用户返回 None"""
        assert services.get_user(999) is None

    def test_delete_user_success(self):
        """删除用户成功"""
        services.create_user("alice", "alice@example.com")
        result = services.delete_user(1)
        assert result is True
        assert services.get_user(1) is None

    def test_delete_user_also_deletes_tasks(self):
        """删除用户时同时删除其任务"""
        services.create_user("alice", "alice@example.com")
        services.create_task("任务1", 1)
        services.delete_user(1)
        assert services.get_task(1) is None


class TestTaskService:

    def test_create_task_success(self):
        """正常创建任务"""
        services.create_user("alice", "alice@example.com")
        task = services.create_task("写文档", 1, priority=2)
        assert task.task_id == 1
        assert task.title == "写文档"
        assert task.priority == 2

    def test_update_task_status_success(self):
        """正常更新任务状态"""
        services.create_user("alice", "alice@example.com")
        services.create_task("写文档", 1)
        result = services.update_task_status(1, "in_progress")
        assert result is True

    def test_update_task_status_invalid(self):
        """非法状态更新失败"""
        services.create_user("alice", "alice@example.com")
        services.create_task("写文档", 1)
        result = services.update_task_status(1, "flying")
        assert result is False

    def test_get_high_priority_tasks(self):
        """
        获取高优先级任务。
        此测试会失败，触发 Agent 场景二（BUG #2：字符串比较）。
        """
        services.create_user("alice", "alice@example.com")
        services.create_task("低优先级", 1, priority=1)
        services.create_task("高优先级", 1, priority=3)
        high = services.get_high_priority_tasks()
        # BUG #2 会导致这里返回空列表，断言失败
        assert len(high) == 1
        assert high[0].title == "高优先级"

    def test_get_task_summary_empty(self):
        """
        空数据时获取摘要。
        此测试会失败，触发 Agent 场景二（BUG #3：ZeroDivisionError）。
        """
        # BUG #3 会导致这里抛出 ZeroDivisionError
        summary = services.get_task_summary()
        assert summary["total"] == 0
        assert summary["completion_rate"] == 0

    def test_get_task_summary_with_data(self):
        """有数据时获取摘要"""
        services.create_user("alice", "alice@example.com")
        services.create_task("任务1", 1)
        services.create_task("任务2", 1)
        services.update_task_status(1, "done")
        summary = services.get_task_summary()
        assert summary["total"] == 2
        assert summary["done"] == 1

    def test_list_tasks_by_user(self):
        """获取用户的任务列表"""
        services.create_user("alice", "alice@example.com")
        services.create_user("bob", "bob@example.com")
        services.create_task("alice的任务", 1)
        services.create_task("bob的任务", 2)
        alice_tasks = services.list_tasks_by_user(1)
        assert len(alice_tasks) == 1
        assert alice_tasks[0].title == "alice的任务"
