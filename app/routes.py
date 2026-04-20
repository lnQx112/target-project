"""
routes.py — HTTP 接口层

提供任务管理系统的 REST API。
"""

from flask import Flask, request, jsonify
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
import services
from utils import validate_email, validate_username, validate_priority, paginate

app = Flask(__name__)


# ── 用户接口 ─────────────────────────────────────────────────

@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体不能为空"}), 400

    username = data.get("username", "").strip()
    email    = data.get("email", "").strip()

    if not validate_username(username):
        return jsonify({"error": "用户名不合法，需 3-20 位字母/数字/下划线，不能以数字开头"}), 400
    if not validate_email(email):
        return jsonify({"error": "邮箱格式不合法"}), 400

    try:
        user = services.create_user(username, email)
        return jsonify(user.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = services.get_user(user_id)
    if user is None:
        return jsonify({"error": f"用户 {user_id} 不存在"}), 404
    return jsonify(user.to_dict())


@app.route("/users", methods=["GET"])
def list_users():
    page      = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 10, type=int)
    users     = [u.to_dict() for u in services.list_users()]
    return jsonify(paginate(users, page, page_size))


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    success = services.delete_user(user_id)
    if not success:
        return jsonify({"error": f"用户 {user_id} 不存在"}), 404
    return jsonify({"message": f"用户 {user_id} 已删除"}), 200


# ── 任务接口 ─────────────────────────────────────────────────

@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体不能为空"}), 400

    title    = data.get("title", "").strip()
    owner_id = data.get("owner_id")
    priority = data.get("priority", 1)

    if not title:
        return jsonify({"error": "任务标题不能为空"}), 400
    if owner_id is None:
        return jsonify({"error": "owner_id 不能为空"}), 400
    if not validate_priority(priority):
        return jsonify({"error": "priority 只能是 1、2、3"}), 400

    task = services.create_task(title, owner_id, priority)
    return jsonify(task.to_dict()), 201


@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = services.get_task(task_id)
    if task is None:
        return jsonify({"error": f"任务 {task_id} 不存在"}), 404
    return jsonify(task.to_dict())


@app.route("/tasks/<int:task_id>/status", methods=["PATCH"])
def update_task_status(task_id):
    data = request.get_json()
    if not data or "status" not in data:
        return jsonify({"error": "请提供 status 字段"}), 400

    success = services.update_task_status(task_id, data["status"])
    if not success:
        return jsonify({"error": f"任务 {task_id} 不存在或状态值不合法"}), 400
    return jsonify({"message": "状态已更新"})


@app.route("/tasks/high-priority", methods=["GET"])
def get_high_priority_tasks():
    tasks = services.get_high_priority_tasks()
    return jsonify([t.to_dict() for t in tasks])


@app.route("/tasks/summary", methods=["GET"])
def get_task_summary():
    try:
        summary = services.get_task_summary()
        return jsonify(summary)
    except ZeroDivisionError:
        return jsonify({"error": "暂无任务数据"}), 500


@app.route("/users/<int:user_id>/tasks", methods=["GET"])
def list_user_tasks(user_id):
    user = services.get_user(user_id)
    if user is None:
        return jsonify({"error": f"用户 {user_id} 不存在"}), 404
    tasks = services.list_tasks_by_user(user_id)
    return jsonify([t.to_dict() for t in tasks])


if __name__ == "__main__":
    app.run(debug=True, port=5001)
