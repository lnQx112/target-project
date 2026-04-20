"""
notifier.py — 飞书通知模块
所有 Agent 共用，按角色发送到不同的飞书群
"""

import requests
import config


# 角色到 Webhook 的映射
ROLE_WEBHOOKS = {
    "dev":     config.FEISHU_WEBHOOK_DEV,
    "qa":      config.FEISHU_WEBHOOK_QA,
    "ops":     config.FEISHU_WEBHOOK_OPS,
    "manager": config.FEISHU_WEBHOOK_MANAGER,
}


def send(role: str, title: str, content: str, level: str = "info") -> bool:
    """
    向指定角色的飞书群发送通知。

    参数:
        role:    接收角色，可选 "dev" / "qa" / "ops" / "manager"
        title:   消息标题
        content: 消息正文（支持飞书 markdown）
        level:   消息级别 "info" / "warning" / "error"，影响标题颜色

    返回:
        True 表示发送成功，False 表示失败
    """
    webhook = ROLE_WEBHOOKS.get(role)
    if not webhook or "PLACEHOLDER" in webhook:
        print(f"[notifier] 跳过发送：{role} 的 Webhook 未配置")
        return False

    # 颜色映射
    color_map = {"info": "green", "warning": "orange", "error": "red"}
    color = color_map.get(level, "green")

    # 飞书卡片消息格式
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color,
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": content},
                }
            ],
        },
    }

    try:
        resp = requests.post(
            webhook, json=payload, timeout=config.REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        print(f"[notifier] 已发送到 {role} 群：{title}")
        return True
    except requests.RequestException as e:
        print(f"[notifier] 发送失败：{e}")
        return False


def send_to_all(title: str, content: str, level: str = "info"):
    """向所有角色群广播消息"""
    for role in ROLE_WEBHOOKS:
        send(role, title, content, level)
