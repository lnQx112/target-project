import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.utils import get_overdue_tasks_count


class MockTask:
    """模拟任务的简单类"""
    def __init__(self, deadline=None):
        self.deadline = deadline


class TestGetOverdueTasksCount(unittest.TestCase):
    @patch('app.utils.datetime')
    def test_no_tasks_returns_zero(self, mock_datetime):
        """测试空任务列表返回0"""
        self.assertEqual(get_overdue_tasks_count([]), 0)
    
    @patch('app.utils.datetime')
    def test_tasks_without_deadline_attr_returns_zero(self, mock_datetime):
        """测试任务无deadline属性返回0"""
        tasks = [object(), object()]
        self.assertEqual(get_overdue_tasks_count(tasks), 0)
    
    @patch('app.utils.datetime')
    def test_tasks_with_none_deadline_returns_zero(self, mock_datetime):
        """测试任务deadline为None返回0"""
        tasks = [MockTask(), MockTask(deadline=None)]
        self.assertEqual(get_overdue_tasks_count(tasks), 0)
    
    @patch('app.utils.datetime')
    def test_deadline_equal_now_returns_zero(self, mock_datetime):
        """测试deadline等于当前时间不算超期"""
        fixed_now = datetime(2024, 5, 20, 12, 0, 0)
        mock_datetime.now.return_value = fixed_now
        tasks = [MockTask(deadline=fixed_now)]
        self.assertEqual(get_overdue_tasks_count(tasks), 0)
    
    @patch('app.utils.datetime')
    def test_deadline_later_now_returns_zero(self, mock_datetime):
        """测试deadline晚于当前时间不算超期"""
        fixed_now = datetime(2024, 5, 20, 12, 0, 0)
        later_time = fixed_now + timedelta(seconds=1)
        mock_datetime.now.return_value = fixed_now
        tasks = [MockTask(deadline=later_time)]
        self.assertEqual(get_overdue_tasks_count(tasks), 0)
    
    @patch('app.utils.datetime')
    def test_deadline_earlier_now_returns_one(self, mock_datetime):
        """测试deadline早于当前时间算超期"""
        fixed_now = datetime(2024, 5, 20, 12, 0, 0)
        earlier_time = fixed_now - timedelta(seconds=1)
        mock_datetime.now.return_value = fixed_now
        tasks = [MockTask(deadline=earlier_time)]
        self.assertEqual(get_overdue_tasks_count(tasks), 1)
    
    @patch('app.utils.datetime')
    def test_mixed_tasks_returns_correct_count(self, mock_datetime):
        """测试多种超期与非超期混合的任务列表统计正确"""
        fixed_now = datetime(2024, 5, 20, 12, 0, 0)
        mock_datetime.now.return_value = fixed_now
        tasks = [
            object(),  # 无deadline属性
            MockTask(deadline=None),  # deadline为None
            MockTask(deadline=fixed_now),  # 等于当前
            MockTask(deadline=fixed_now + timedelta(days=1)),  # 晚于当前
            MockTask(deadline=fixed_now - timedelta(days=1)),  # 早1天
            MockTask(deadline=fixed_now - timedelta(hours=2)),  # 早2小时
            MockTask(deadline=fixed_now - timedelta(milliseconds=100)),  # 早100ms
        ]
        self.assertEqual(get_overdue_tasks_count(tasks), 3)


if __name__ == '__main__':
    unittest.main()
