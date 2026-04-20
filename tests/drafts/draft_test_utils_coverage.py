import pytest
from datetime import datetime, timedelta
from app.utils import (
    validate_email, validate_username, format_datetime,
    parse_datetime, is_overdue, days_until_due,
    truncate_text, slugify, paginate, mask_email,
    generate_task_code, calculate_workdays, get_overdue_tasks_count
)


class TestValidateEmail:
    """测试邮箱验证函数"""
    def test_valid_common_email(self):
        """测试正常的通用邮箱格式"""
        assert validate_email("test@example.com") is True

    def test_valid_email_with_plus(self):
        """测试含+号的邮箱格式（注册常用别名）"""
        assert validate_email("user+tag@example.co.uk") is True

    def test_invalid_email_no_at(self):
        """测试不含@的无效邮箱"""
        assert validate_email("testexample.com") is False

    def test_invalid_email_no_domain_dot(self):
        """测试域名不含.的无效邮箱"""
        assert validate_email("test@examplecom") is False


class TestValidateUsername:
    """测试用户名验证函数"""
    def test_valid_normal_username(self):
        """测试符合要求的常规用户名"""
        assert validate_username("user_123") is True

    def test_valid_min_length_username(self):
        """测试3位最小长度边界"""
        assert validate_username("a_b") is True

    def test_valid_max_length_username(self):
        """测试20位最大长度边界"""
        assert validate_username("a" * 19 + "_") is True

    def test_invalid_empty_username(self):
        """测试空用户名"""
        assert validate_username("") is False

    def test_invalid_short_username(self):
        """测试小于3位的用户名"""
        assert validate_username("ab") is False

    def test_invalid_long_username(self):
        """测试大于20位的用户名"""
        assert validate_username("a" * 21) is False

    def test_invalid_username_start_with_number(self):
        """测试以数字开头的用户名"""
        assert validate_username("1user") is False

    def test_invalid_username_with_special_char(self):
        """测试含非法特殊字符的用户名"""
        assert validate_username("user!") is False


class TestFormatDatetime:
    """测试日期时间格式化函数"""
    def test_format_normal_datetime(self):
        """测试正常日期时间的格式化"""
        dt = datetime(2024, 5, 20, 14, 30, 45)
        assert format_datetime(dt) == "2024-05-20 14:30:45"


class TestParseDatetime:
    """测试日期时间解析函数"""
    def test_parse_full_format(self):
        """测试完整的YYYY-MM-DD HH:MM:SS格式解析"""
        dt_str = "2024-05-20 14:30:45"
        expected = datetime(2024, 5, 20, 14, 30, 45)
        assert parse_datetime(dt_str) == expected

    def test_parse_date_only_hyphen(self):
        """测试仅日期的YYYY-MM-DD格式解析"""
        dt_str = "2024-05-20"
        expected = datetime(2024, 5, 20, 0, 0, 0)
        assert parse_datetime(dt_str) == expected

    def test_parse_date_only_slash(self):
        """测试仅日期的YYYY/MM/DD格式解析"""
        dt_str = "2024/05/20"
        expected = datetime(2024, 5, 20, 0, 0, 0)
        assert parse_datetime(dt_str) == expected

    def test_parse_invalid_format(self):
        """测试无效格式的日期时间字符串解析"""
        dt_str = "20-05-2024 2:30 PM"
        assert parse_datetime(dt_str) is None


class TestIsOverdue:
    """测试任务超期判断函数"""
    def test_is_overdue_true(self):
        """测试已超期的任务"""
        due_date = datetime.now() - timedelta(hours=1)
        assert is_overdue(due_date) is True

    def test_is_overdue_false(self):
        """测试未超期的任务"""
        due_date = datetime.now() + timedelta(days=1)
        assert is_overdue(due_date) is False


class TestDaysUntilDue:
    """测试距离截止日期天数函数"""
    def test_days_until_due_positive(self):
        """测试未超期，返回正数"""
        due_date = datetime.now() + timedelta(days=5)
        # 允许±1天误差（防止测试运行跨天）
        assert days_until_due(due_date) in (4, 5)

    def test_days_until_due_negative(self):
        """测试已超期，返回负数"""
        due_date = datetime.now() - timedelta(days=3)
        assert days_until_due(due_date) in (-4, -3)

    def test_days_until_due_zero(self):
        """测试当天截止，返回0"""
        due_date = datetime.now() + timedelta(hours=12)
        assert days_until_due(due_date) == 0


class TestTruncateText:
    """测试文本截断函数"""
    def test_truncate_text_no_need(self):
        """测试文本长度不超过max_length，直接返回"""
        text = "短文本"
        assert truncate_text(text, max_length=10) == text

    def test_truncate_text_need(self):
        """测试文本长度超过max_length，截断并加suffix"""
        text = "a" * 10
        max_length = 5
        suffix = "..."
        expected = "aa..."  # 5-3=2个a
        assert truncate_text(text, max_length=max_length, suffix=suffix) == expected

    def test_truncate_text_custom_suffix(self):
        """测试自定义后缀的截断"""
        text = "非常长的需要截断的文本内容"
        max_length = 10
        suffix = " [省略]"
        expected = text[:10 - len(suffix)] + suffix
        assert truncate_text(text, max_length=max_length, suffix=suffix) == expected


class TestSlugify:
    """测试URL友好转换函数"""
    def test_slugify_normal_text(self):
        """测试正常文本的转换"""
        text = "Hello World!"
        assert slugify(text) == "hello-world"

    def test_slugify_with_multiple_spaces(self):
        """测试含多个连续空格的文本转换"""
        text = "  Hello   World  "
        assert slugify(text) == "hello-world"

    def test_slugify_with_underscores(self):
        """测试含下划线的文本转换（替换为-）"""
        text = "hello_world_123"
        assert slugify(text) == "hello-world-123"

    def test_slugify_with_trailing_hyphens(self):
        """测试含前后连字符的文本转换（去除首尾）"""
        text = "-hello-world-"
        assert slugify(text) == "hello-world"

    def test_slugify_with_special_chars(self):
        """测试含大量特殊字符的文本转换（保留字母数字空格-）"""
        text = "你好 Hello!@#$%^&*()_+ World 123"
        assert slugify(text) == "hello-world-123"


class TestPaginate:
    """测试列表分页函数"""
    def test_paginate_first_page(self):
        """测试第一页的分页"""
        items = list(range(25))
        result = paginate(items, page=1, page_size=10)
        assert result["items"] == list(range(10))
        assert result["total"] == 25
        assert result["total_pages"] == 3

    def test_paginate_last_page(self):
        """测试最后一页的分页"""
        items = list(range(25))
        result = paginate(items, page=3, page_size=10)
        assert result["items"] == list(range(20, 25))

    def test_paginate_page_less_than_one(self):
        """测试页码小于1的情况（自动修正为1）"""
        items = list(range(25))
        result = paginate(items, page=0, page_size=10)
        assert result["page"] == 1
        assert result["items"] == list(range(10))

    def test_paginate_empty_items(self):
        """测试空列表的分页"""
        items = []
        result = paginate(items, page=1, page_size=10)
        assert result["items"] == []
        assert result["total"] == 0
        assert result["total_pages"] == 0


class TestMaskEmail:
    """测试邮箱脱敏函数"""
    def test_mask_email_normal_local(self):
        """测试本地部分大于1位的邮箱脱敏"""
        email = "user@example.com"
        assert mask_email(email) == "u***@example.com"

    def test_mask_email_short_local(self):
        """测试本地部分小于等于1位的邮箱脱敏"""
        email = "a@example.com"
        assert mask_email(email) == "a***@example.com"

    def test_mask_email_no_at(self):
        """测试不含@的非邮箱字符串，直接返回"""
        email = "notanemail"
        assert mask_email(email) == "notanemail"


class TestGenerateTaskCode:
    """测试任务编号生成函数"""
    def test_generate_task_code_default_prefix(self):
        """测试默认前缀的任务编号生成"""
        assert generate_task_code(42) == "TASK-0042"

    def test_generate_task_code_custom_prefix(self):
        """测试自定义前缀的任务编号生成"""
        assert generate_task_code(123, prefix="BUG") == "BUG-0123"

    def test_generate_task_code_single_digit(self):
        """测试个位数任务ID的补零"""
        assert generate_task_code(5) == "TASK-0005"


class TestCalculateWorkdays:
    """测试工作日计算函数"""
    def test_calculate_workdays_same_weekday(self):
        """测试同一工作日的计算（返回1）"""
        start = datetime(2024, 5, 20)  # 周一
        end = datetime(2024, 5, 20)
        assert calculate_workdays(start, end) == 1

    def test_calculate_workdays_weekend_in_between(self):
        """测试含周末的计算"""
        start = datetime(2024, 5, 17)  # 周五
        end = datetime(2024, 5, 20)    # 下周一
        assert calculate_workdays(start, end) == 2

    def test_calculate_workdays_full_weekend(self):
        """测试整个周期都是周末的计算（返回0）"""
        start = datetime(2024, 5, 18)  # 周六
        end = datetime(2024, 5, 19)    # 周日
        assert calculate_workdays(start, end) == 0


class TestGetOverdueTasksCount:
    """测试超期任务统计函数"""
    @pytest.fixture
    def mock_task(self):
        """模拟任务类的 fixture"""
        class MockTask:
            def __init__(self, deadline=None):
                self.deadline = deadline
        return MockTask

    def test_get_overdue_tasks_count_with_overdue(self, mock_task):
        """测试含超期任务的统计"""
        now = datetime.now()
        tasks = [
            mock_task(deadline=now - timedelta(days=1)),
            mock_task(deadline=now + timedelta(days=1)),
            mock_task(deadline=None),
            mock_task(),  # 没有deadline属性？不，这里都有，不过原代码有hasattr
            mock_task(deadline=now - timedelta(hours=2))
        ]
        # 移除没有deadline的测试，用hasattr的话可以加
        tasks.append(type('', (), {})())  # 完全没有deadline属性的对象
        assert get_overdue_tasks_count(tasks) == 2

    def test_get_overdue_tasks_count_no_overdue(self, mock_task):
        """测试不含超期任务的统计"""
        now = datetime.now()
        tasks = [
            mock_task(deadline=now + timedelta(days=1)),
            mock_task(deadline=None),
            type('', (), {})()
        ]
        assert get_overdue_tasks_count(tasks) == 0