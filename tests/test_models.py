import unittest
from datetime import datetime
from app.models import Task

class TestTask(unittest.TestCase):
    def test_task_init_without_deadline(self):
        task = Task(1, "测试无截止时间的任务", 100, 2)
        self.assertIsNone(task.deadline)
        task_dict = task.to_dict()
        self.assertIn("deadline", task_dict)
        self.assertIsNone(task_dict["deadline"])
    
    def test_task_init_with_deadline(self):
        deadline = datetime(2024, 12, 31, 23, 59, 59)
        task = Task(2, "测试有截止时间的任务", 200, 3, deadline)
        self.assertEqual(task.deadline, deadline)
        task_dict = task.to_dict()
        self.assertEqual(task_dict["deadline"], deadline.isoformat())

if __name__ == "__main__":
    unittest.main()