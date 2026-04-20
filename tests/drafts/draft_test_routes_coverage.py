import pytest
from unittest.mock import patch, MagicMock
from app.routes import app


@pytest.fixture
def client():
    """创建Flask测试客户端"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ── 用户接口测试 ─────────────────────────────────────────────────

@patch("app.routes.services")
@patch("app.routes.validate_username")
@patch("app.routes.validate_email")
def test_create_user_empty_body(mock_validate_email, mock_validate_username, mock_services, client):
    """测试创建用户时请求体为空的场景"""
    response = client.post("/users", json=None)
    assert response.status_code == 400
    assert "请求体不能为空" in response.get_json()["error"]
    mock_validate_username.assert_not_called()
    mock_validate_email.assert_not_called()
    mock_services.create_user.assert_not_called()


@patch("app.routes.services")
@patch("app.routes.validate_username")
@patch("app.routes.validate_email")
def test_create_user_invalid_username(mock_validate_email, mock_validate_username, mock_services, client):
    """测试创建用户时用户名不合法的场景"""
    mock_validate_username.return_value = False
    response = client.post("/users", json={"username": "123", "email": "test@example.com"})
    assert response.status_code == 400
    assert "用户名不合法" in response.get_json()["error"]
    mock_validate_username.assert_called_once_with("123")
    mock_validate_email.assert_not_called()
    mock_services.create_user.assert_not_called()


@patch("app.routes.services")
@patch("app.routes.validate_username")
@patch("app.routes.validate_email")
def test_create_user_invalid_email(mock_validate_email, mock_validate_username, mock_services, client):
    """测试创建用户时邮箱不合法的场景"""
    mock_validate_username.return_value = True
    mock_validate_email.return_value = False
    response = client.post("/users", json={"username": "test_user", "email": "invalid-email"})
    assert response.status_code == 400
    assert "邮箱格式不合法" in response.get_json()["error"]
    mock_validate_username.assert_called_once_with("test_user")
    mock_validate_email.assert_called_once_with("invalid-email")
    mock_services.create_user.assert_not_called()


@patch("app.routes.services")
@patch("app.routes.validate_username")
@patch("app.routes.validate_email")
def test_create_user_value_error(mock_validate_email, mock_validate_username, mock_services, client):
    """测试创建用户时服务层抛出ValueError的场景（如用户已存在）"""
    mock_validate_username.return_value = True
    mock_validate_email.return_value = True
    mock_services.create_user.side_effect = ValueError("用户名已存在")
    response = client.post("/users", json={"username": "test_user", "email": "test@example.com"})
    assert response.status_code == 400
    assert response.get_json()["error"] == "用户名已存在"
    mock_services.create_user.assert_called_once_with("test_user", "test@example.com")


@patch("app.routes.services")
def test_get_user_not_found(mock_services, client):
    """测试获取不存在的用户的场景"""
    mock_services.get_user.return_value = None
    response = client.get("/users/999")
    assert response.status_code == 404
    assert "用户 999 不存在" in response.get_json()["error"]
    mock_services.get_user.assert_called_once_with(999)


@patch("app.routes.services")
@patch("app.routes.paginate")
def test_list_users_pagination(mock_paginate, mock_services, client):
    """测试用户列表分页的场景"""
    mock_user1 = MagicMock()
    mock_user1.to_dict.return_value = {"id": 1, "username": "user1"}
    mock_user2 = MagicMock()
    mock_user2.to_dict.return_value = {"id": 2, "username": "user2"}
    mock_services.list_users.return_value = [mock_user1, mock_user2]
    mock_paginate.return_value = {"items": [{"id": 1}], "total": 2, "page": 1, "page_size": 1}
    response = client.get("/users?page=1&page_size=1")
    assert response.status_code == 200
    mock_services.list_users.assert_called_once()
    mock_paginate.assert_called_once_with([{"id": 1, "username": "user1"}, {"id": 2, "username": "user2"}], 1, 1)


@patch("app.routes.services")
def test_delete_user_not_found(mock_services, client):
    """测试删除不存在的用户的场景"""
    mock_services.delete_user.return_value = False
    response = client.delete("/users/999")
    assert response.status_code == 404
    assert "用户 999 不存在" in response.get_json()["error"]
    mock_services.delete_user.assert_called_once_with(999)


# ── 任务接口测试 ─────────────────────────────────────────────────

@patch("app.routes.services")
def test_create_task_empty_body(mock_services, client):
    """测试创建任务时请求体为空的场景"""
    response = client.post("/tasks", json=None)
    assert response.status_code == 400
    assert "请求体不能为空" in response.get_json()["error"]
    mock_services.create_task.assert_not_called()


@patch("app.routes.services")
def test_create_task_empty_title(mock_services, client):
    """测试创建任务时标题为空的场景"""
    response = client.post("/tasks", json={"title": "   ", "owner_id": 1, "priority": 1})
    assert response.status_code == 400
    assert "任务标题不能为空" in response.get_json()["error"]
    mock_services.create_task.assert_not_called()


@patch("app.routes.services")
def test_create_task_missing_owner_id(mock_services, client):
    """测试创建任务时缺少owner_id的场景"""
    response = client.post("/tasks", json={"title": "test task", "priority": 1})
    assert response.status_code == 400
    assert "owner_id 不能为空" in response.get_json()["error"]
    mock_services.create_task.assert_not_called()


@patch("app.routes.services")
@patch("app.routes.validate_priority")
def test_create_task_invalid_priority(mock_validate_priority, mock_services, client):
    """测试创建任务时优先级不合法的场景"""
    mock_validate_priority.return_value = False
    response = client.post("/tasks", json={"title": "test task", "owner_id": 1, "priority": 0})
    assert response.status_code == 400
    assert "priority 只能是 1、2、3" in response.get_json()["error"]
    mock_validate_priority.assert_called_once_with(0)
    mock_services.create_task.assert_not_called()


@patch("app.routes.services")
def test_get_task_not_found(mock_services, client):
    """测试获取不存在的任务的场景"""
    mock_services.get_task.return_value = None
    response = client.get("/tasks/999")
    assert response.status_code == 404
    assert "任务 999 不存在" in response.get_json()["error"]
    mock_services.get_task.assert_called_once_with(999)


@patch("app.routes.services")
def test_update_task_status_empty_body(mock_services, client):
    """测试更新任务状态时请求体为空的场景"""
    response = client.patch("/tasks/1/status", json=None)
    assert response.status_code == 400
    assert "请提供 status 字段" in response.get_json()["error"]
    mock_services.update_task_status.assert_not_called()


@patch("app.routes.services")
def test_update_task_status_missing_status(mock_services, client):
    """测试更新任务状态时缺少status字段的场景"""
    response = client.patch("/tasks/1/status", json={"other": "value"})
    assert response.status_code == 400
    assert "请提供 status 字段" in response.get_json()["error"]
    mock_services.update_task_status.assert_not_called()


@patch("app.routes.services")
def test_update_task_status_failure(mock_services, client):
    """测试更新任务状态时服务层返回失败的场景（任务不存在或状态不合法）"""
    mock_services.update_task_status.return_value = False
    response = client.patch("/tasks/999/status", json={"status": "done"})
    assert response.status_code == 400
    assert "任务 999 不存在或状态值不合法" in response.get_json()["error"]
    mock_services.update_task_status.assert_called_once_with(999, "done")


@patch("app.routes.services")
def test_get_task_summary_zero_division_error(mock_services, client):
    """测试获取任务概览时服务层抛出ZeroDivisionError的场景"""
    mock_services.get_task_summary.side_effect = ZeroDivisionError
    response = client.get("/tasks/summary")
    assert response.status_code == 500
    assert "暂无任务数据" in response.get_json()["error"]
    mock_services.get_task_summary.assert_called_once()


@patch("app.routes.services")
def test_list_user_tasks_user_not_found(mock_services, client):
    """测试获取不存在用户的任务列表的场景"""
    mock_services.get_user.return_value = None
    response = client.get("/users/999/tasks")
    assert response.status_code == 404
    assert "用户 999 不存在" in response.get_json()["error"]
    mock_services.get_user.assert_called_once_with(999)
    mock_services.list_tasks_by_user.assert_not_called()