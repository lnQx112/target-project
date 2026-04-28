import pytest
from flask import json
from app.routes import app
from unittest.mock import patch, MagicMock


# 测试固件：创建测试客户端
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ── 用户接口补充测试 ─────────────────────────────────────────────────

@patch('app.routes.services.create_user')
def test_create_user_request_body_empty(mock_create_user, client):
    """测试创建用户时请求体为空，覆盖行7-9：检查请求体并返回400错误"""
    response = client.post('/users', json=None)
    assert response.status_code == 400
    assert response.json == {"error": "请求体不能为空"}
    mock_create_user.assert_not_called()


@patch('app.routes.validate_username', return_value=False)
@patch('app.routes.validate_email', return_value=True)
@patch('app.routes.services.create_user')
def test_create_user_invalid_username(mock_create_user, mock_validate_email, mock_validate_username, client):
    """测试创建用户时用户名不合法，覆盖行16-17：用户名校验失败分支"""
    response = client.post('/users', json={"username": "123abc", "email": "test@test.com"})
    assert response.status_code == 400
    assert "用户名不合法" in response.json["error"]
    mock_create_user.assert_not_called()


@patch('app.routes.validate_username', return_value=True)
@patch('app.routes.validate_email', return_value=False)
@patch('app.routes.services.create_user')
def test_create_user_invalid_email(mock_create_user, mock_validate_email, mock_validate_username, client):
    """测试创建用户时邮箱不合法，覆盖行18-19：邮箱校验失败分支"""
    response = client.post('/users', json={"username": "valid_user", "email": "invalid-email"})
    assert response.status_code == 400
    assert "邮箱格式不合法" in response.json["error"]
    mock_create_user.assert_not_called()


@patch('app.routes.validate_username', return_value=True)
@patch('app.routes.validate_email', return_value=True)
@patch('app.routes.services.create_user', side_effect=ValueError("用户名已存在"))
def test_create_user_service_value_error(mock_create_user, mock_validate_email, mock_validate_username, client):
    """测试创建用户时services抛出ValueError，覆盖行20、22-23：异常捕获分支"""
    response = client.post('/users', json={"username": "exist_user", "email": "test@test.com"})
    assert response.status_code == 400
    assert response.json["error"] == "用户名已存在"


# ── 任务接口补充测试 ─────────────────────────────────────────────────

@patch('app.routes.services.create_task')
def test_create_task_request_body_empty(mock_create_task, client):
    """测试创建任务时请求体为空，覆盖行25-27：检查请求体并返回400错误"""
    response = client.post('/tasks', json=None)
    assert response.status_code == 400
    assert response.json == {"error": "请求体不能为空"}
    mock_create_task.assert_not_called()


@patch('app.routes.validate_priority', return_value=True)
@patch('app.routes.services.create_task')
def test_create_task_empty_title(mock_create_task, mock_validate_priority, client):
    """测试创建任务时标题为空，覆盖行28-30：标题空校验分支"""
    response = client.post('/tasks', json={"title": "   ", "owner_id": 1, "priority": 2})
    assert response.status_code == 400
    assert response.json["error"] == "任务标题不能为空"
    mock_create_task.assert_not_called()


@patch('app.routes.validate_priority', return_value=True)
@patch('app.routes.services.create_task')
def test_create_task_owner_id_none(mock_create_task, mock_validate_priority, client):
    """测试创建任务时owner_id为空，覆盖行31-32：owner_id非空校验分支"""
    response = client.post('/tasks', json={"title": "测试任务", "priority": 1})
    assert response.status_code == 400
    assert response.json["error"] == "owner_id 不能为空"
    mock_create_task.assert_not_called()


@patch('app.routes.services.create_task')
def test_create_task_invalid_priority(mock_create_task, client):
    """测试创建任务时priority不合法，覆盖行33-34：priority校验分支"""
    response = client.post('/tasks', json={"title": "测试任务", "owner_id": 1, "priority": 4})
    assert response.status_code == 400
    assert "priority 只能是 1、2、3" in response.json["error"]
    mock_create_task.assert_not_called()


@patch('app.routes.services.update_task_status', return_value=False)
def test_update_task_status_missing_status_or_failure(mock_update_status, client):
    """测试更新任务状态时缺少status字段或更新失败，覆盖PATCH接口的两个错误分支"""
    # 先测缺少status
    response1 = client.patch('/tasks/1/status', json={"other": "value"})
    assert response1.status_code == 400
    assert response1.json["error"] == "请提供 status 字段"
    # 再测更新失败
    response2 = client.patch('/tasks/1/status', json={"status": "done"})
    assert response2.status_code == 400
    assert "任务 1 不存在或状态值不合法" in response2.json["error"]


@patch('app.routes.services.get_task_summary', side_effect=ZeroDivisionError)
def test_get_task_summary_zero_division_error(mock_summary, client):
    """测试获取任务摘要时触发ZeroDivisionError，覆盖500错误分支"""
    response = client.get('/tasks/summary')
    assert response.status_code == 500
    assert response.json["error"] == "暂无任务数据"