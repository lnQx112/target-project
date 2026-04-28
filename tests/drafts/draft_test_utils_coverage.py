import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from app.utils import (
    validate_email, validate_username, validate_priority,
    format_datetime, parse_datetime, is_overdue, days_until_due,
    truncate_text, slugify, paginate, mask_email, generate_task_code,
    calculate_workdays, get_overdue_tasks_count
)


# ==================== validate_email 测试 ====================
def test_validate_email_valid_common():
    """测试普通有效邮箱"""
    assert validate_email("test@example.com") is True


def test_validate_email_valid_with_special_chars():
    """测试允许的特殊字符邮箱（+._-）"""
    assert validate_email("test.name+tag_123@sub-domain.example.co.uk") is True


def test_validate_email_invalid_no_at():
    """测试没有@的无效邮箱"""
    assert validate_email("testexample.com") is False


def test_validate_email_invalid_no_domain_dot():
    """测试域名没有后缀点的无效邮箱"""
    assert validate_email("test@example") is False


def test_validate_email_invalid_empty():
    """测试空字符串邮箱"""
    assert validate_email("") is False


# ==================== validate_username 测试 ====================
def test_validate_username_valid_normal():
    """测试普通有效用户名（字母开头，长度适中）"""
    assert validate_username("User_123") is True


def test_validate_username_valid_min_length():
    """测试用户名最小长度（3字符）"""
    assert validate_username("ab_") is True


def test_validate_username_valid_max_length():
    """测试用户名最大长度（20字符）"""
    assert validate_username("a" * 20) is True


def test_validate_username_invalid_empty():
    """测试空用户名"""
    assert validate_username("") is False


def test_validate_username_invalid_too_short():
    """测试用户名过短（<3字符）"""
    assert validate_username("ab") is False


def test_validate_username_invalid_too_long():
    """测试用户名过长（>20字符）"""
    assert validate_username("a" * 21) is False


def test_validate_username_invalid_start_with_digit():
    """测试以数字开头的无效用户名"""
    assert validate_username("1user") is False


def test_validate_username_invalid_special_char():
    """测试含非法字符的无效用户名"""
    assert validate_username("user!") is False


# ==================== validate_priority 测试 ====================
def test_validate_priority_valid_1():
    """测试优先级1"""
    assert validate_priority(1) is True


def test_validate_priority_valid_2():
    """测试优先级2"""
    assert validate_priority(2) is True


def test_validate_priority_valid_3():
    """测试优先级3"""
    assert validate_priority(3) is True


def test_validate_priority_invalid_0():
    """测试优先级0"""
    assert validate_priority(0) is False


def test_validate_priority_invalid_4():
    """测试优先级4"""
    assert validate_priority(4) is False


def test_validate_priority_invalid_str():
    """测试字符串类型的优先级"""
    assert validate_priority("1") is False


# ==================== format_datetime 测试 ====================
def test_format_datetime_normal():
    """测试正常格式化datetime"""
    dt = datetime(2024, 5, 20, 14, 30, 45)
    assert format_datetime(dt) == "2024-05-20 14:30:45"


# ==================== parse_datetime 测试 ====================
def test_parse_datetime_format1():
    """测试第一种格式解析：%Y-%m-%d %H:%M:%S"""
    dt_str = "2024-05-20 14:30:45"
    expected = datetime(2024, 5, 20, 14, 30, 45)
    assert parse_datetime(dt_str) == expected


def test_parse_datetime_format2():
    """测试第二种格式解析：%Y-%m-%d"""
    dt_str = "2024-05-20"
    expected = datetime(2024, 5, 20, 0, 0, 0)
    assert parse_datetime(dt_str) == expected


def test_parse_datetime_format3():
    """测试第三种格式解析：%Y/%m/%d"""
    dt_str = "2024/05/20"
    expected = datetime(2024, 5, 20, 0, 0, 0)
    assert parse_datetime(dt_str) == expected


def test_parse_datetime_invalid_format():
    """测试无效格式解析返回None"""
    dt_str = "2024.05.20"
    assert parse_datetime(dt_str) is None


# ==================== is_overdue 测试 ====================
@patch("app.utils.datetime")
def test_is_overdue_true(mock_datetime):
    """测试已超期的情况"""
    mock_now = datetime(2024, 5, 21, 0, 0, 0)
    mock_datetime.now.return_value = mock_now
    due_date = datetime(2024, 5, 20, 23, 59, 59)
    assert is_overdue(due_date) is True


@patch("app.utils.datetime")
def test_is_overdue_false(mock_datetime):
    """测试未超期的情况"""
    mock_now = datetime(2024, 5, 20, 0, 0, 0)
    mock_datetime.now.return_value = mock_now
    due_date = datetime(2024, 5, 21, 0, 0, 0)
    assert is_overdue(due_date) is False


@patch("app.utils.datetime")
def test_is_overdue_exact_now(mock_datetime):
    """测试刚好等于当前时间的情况"""
    mock_now = datetime(2024, 5, 20, 12, 0, 0)
    mock_datetime.now.return_value = mock_now
    assert is_overdue(mock_now) is False


# ==================== days_until_due 测试 ====================
@patch("app.utils.datetime")
def test_days_until_due_positive(mock_datetime):
    """测试还有正天数到期"""
    mock_now = datetime(2024, 5, 20)
    mock_datetime.now.return_value = mock_now
    due_date = datetime(2024, 5, 25)
    assert days_until_due(due_date) == 5


@patch("app.utils.datetime")
def test_days_until_due_negative(mock_datetime):
    """测试已超期返回负数"""
    mock_now = datetime(2024, 5, 20)
    mock_datetime.now.return_value = mock_now
    due_date = datetime(2024, 5, 15)
    assert days_until_due(due_date) == -5


@patch("app.utils.datetime")
def test_days_until_due_zero(mock_datetime):
    """测试当天到期返回0"""
    mock_now = datetime(2024, 5, 20, 12, 30)
    mock_datetime.now.return_value = mock_now
    due_date = datetime(2024, 5, 20, 23, 59)
    assert days_until_due(due_date) == 0


# ==================== truncate_text 测试 ====================
def test_truncate_text_no_need():
    """测试文本长度未超过max_length，不截断"""
    text = "Hello World"
    assert truncate_text(text, 20) == text


def test_truncate_text_exact_max_length():
    """测试文本长度刚好等于max_length，不截断"""
    text = "Hello World"
    assert truncate_text(text, len(text)) == text


def test_truncate_text_default_params():
    """测试使用默认参数截断"""
    text = "a" * 101
    expected = "a" * 97 + "..."
    assert truncate_text(text) == expected


def test_truncate_text_custom_suffix():
    """测试使用自定义后缀截断"""
    text = "Hello World!"
    assert truncate_text(text, 8, "!!") == "Hello!!"


# ==================== slugify 测试 ====================
def test_slugify_normal_text():
    """测试普通文本转slug"""
    text = "Hello World!"
    assert slugify(text) == "hello-world"


def test_slugify_with_multiple_spaces():
    """测试含多个空格的文本"""
    text = "   Hello   World   "
    assert slugify(text) == "hello-world"


def test_slugify_with_underscores():
    """测试含下划线的文本"""
    text = "Hello_World_123"
    assert slugify(text) == "hello-world-123"


def test_slugify_with_multiple_hyphens():
    """测试含多个连字符的文本"""
    text = "Hello--World!!--Test"
    assert slugify(text) == "hello-world-test"


def test_slugify_with_leading_trailing_hyphens():
    """测试首尾含连字符的文本"""
    text = "-Hello-World-"
    assert slugify(text) == "hello-world"


def test_slugify_empty_after_clean():
    """测试清洗后为空的文本"""
    text = "!!!$$$@@@"
    assert slugify(text) == ""


# ==================== paginate 测试 ====================
def test_paginate_normal_page():
    """测试正常分页"""
    items = list(range(25))
    result = paginate(items, 2, 10)
    assert result["items"] == [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    assert result["total"] == 25
    assert result["page"] == 2
    assert result["page_size"] == 10
    assert result["total_pages"] == 3


def test_paginate_page_less_than_one():
    """测试页码小于1的情况（自动重置为1）"""
    items = list(range(10))
    result = paginate(items, 0)
    assert result["page"] == 1
    assert result["items"] == items


def test_paginate_last_page():
    """测试最后一页"""
    items = list(range(25))
    result = paginate(items, 3, 10)
    assert result["items"] == [20, 21, 22, 23, 24]


def test_paginate_empty_list():
    """测试空列表分页"""
    items = []
    result = paginate(items, 1)
    assert result["items"] == []
    assert result["total"] == 0
    assert result["total_pages"] == 0


def test_paginate_page_exceeds_total_pages():
    """测试页码超过总页数的情况"""
    items = list(range(10))
    result = paginate(items, 3)
    assert result["items"] == []


# ==================== mask_email 测试 ====================
def test_mask_email_normal():
    """测试普通邮箱脱敏"""
    email = "user@example.com"
    assert mask_email(email) == "u***@example.com"


def test_mask_email_local_length_one():
    """测试本地部分长度为1的邮箱脱敏"""
    email = "a@example.com"
    assert mask_email(email) == "a***@example.com"


def test_mask_email_no_at():
    """测试没有@的邮箱不处理"""
    email = "userexample.com"
    assert mask_email(email) == email


def test_mask_email_local_length_two():
    """测试本地部分长度为2的邮箱脱敏"""
    email = "ab@example.com"
    assert mask_email(email) == "a***@example.com"


# ==================== generate_task_code 测试 ====================
def test_generate_task_code_normal():
    """测试生成普通任务编号"""
    assert generate_task_code(42) == "TASK-0042"


def test_generate_task_code_custom_prefix():
    """测试自定义前缀的任务编号"""
    assert generate_task_code(42, "BUG") == "BUG-0042"


def test_generate_task_code_large_id():
    """测试超过4位的任务ID"""
    assert generate_task_code(12345) == "TASK-12345"


def test_generate_task_code_zero_id():
    """测试ID为0的情况"""
    assert generate_task_code(0) == "TASK-0000"


# ==================== calculate_workdays 测试 ====================
def test_calculate_workdays_same_day_workday():
    """测试同一天是工作日的情况"""
    start = end = datetime(2024, 5, 20)  # 周一
    assert calculate_workdays(start, end) == 1


def test_calculate_workdays_same_day_weekend():
    """测试同一天是周末的情况"""
    start = end = datetime(2024, 5, 25)  # 周六
    assert calculate_workdays(start, end) == 0


def test_calculate_workdays_full_week():
    """测试完整一周的工作日"""
    start = datetime(2024, 5, 20)  # 周一
    end = datetime(2024, 5, 26)    # 周日
    assert calculate_workdays(start, end) == 5


def test_calculate_workdays_ends_on_weekend():
    """测试结束于周末的情况"""
    start = datetime(2024, 5, 20)  # 周一
    end = datetime(2024, 5, 25)    # 周六
    assert calculate_workdays(start, end) == 5


def test_calculate_workdays_starts_on_weekend():
    """测试开始于周末的情况"""
    start = datetime(2024, 5, 25)  # 周六
    end = datetime(2024, 5, 28)    # 周二
    assert calculate_workdays(start, end) == 2


def test_calculate_workdays_start_after_end():
    """测试开始时间大于结束时间的情况"""
    start = datetime(2024, 5, 28)
    end = datetime(2024, 5, 20)
    assert calculate_workdays(start, end) == 0


# ==================== get_overdue_tasks_count 测试 ====================
class MockTask:
    def __init__(self, deadline=None):
        self.deadline = deadline


@patch("app.utils.datetime")
def test_get_overdue_tasks_count_normal(mock_datetime):
    """测试统计超期任务（包含有效、无效、超期、未超期）"""
    mock_now = datetime(2024, 5, 20, 12, 0)
    mock_datetime.now.return_value = mock_now
    tasks = [
        MockTask(datetime(2024, 5, 19)),  # 超期
        MockTask(datetime(2024, 5, 21)),  # 未超期
        MockTask(None),                   # 无deadline
        MockTask(datetime(2024, 5, 20, 11, 59)),  # 超期
        object(),                         # 无deadline属性
    ]
    assert get_overdue_tasks_count(tasks) == 2


@patch("app.utils.datetime")
def test_get_overdue_tasks_count_empty(mock_datetime):
    """测试空任务列表"""
    mock_now = datetime(2024, 5, 20)
    mock_datetime.now.return_value = mock_now
    assert get_overdue_tasks_count([]) == 0


@patch("app.utils.datetime")
def test_get_overdue_tasks_count_all_overdue(mock_datetime):
    """测试所有任务都超期"""
    mock_now = datetime(2024, 5, 20)
    mock_datetime.now.return_value = mock_now
    tasks = [
        MockTask(datetime(2024, 5, 19)),
        MockTask(datetime(2024, 5, 18)),
    ]
    assert get_overdue_tasks_count(tasks) == 2