# ============================================================
# 全局配置文件
# 所有敏感信息从环境变量读取，不要把真实的 key 写在这里
# 真实的值请填写在 target-project/.env 文件中
# ============================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（本地开发用，Jenkins 上直接用环境变量）
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

# ── 豆包大模型（字节跳动）────────────────────────────────────
# 官网: https://console.volcengine.com/ark
DOUBAO_API_KEY  = os.environ.get("DOUBAO_API_KEY", "PLACEHOLDER_DOUBAO_API_KEY")
DOUBAO_MODEL    = os.environ.get("DOUBAO_MODEL", "doubao-seed-2-0-code-preview-260215")
DOUBAO_BASE_URL = os.environ.get("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")


# ── 飞书机器人 Webhook ───────────────────────────────────────
# 在飞书群里添加「自定义机器人」，复制 Webhook 地址填入 .env
FEISHU_WEBHOOK_DEV     = os.environ.get("FEISHU_WEBHOOK_DEV",     "PLACEHOLDER")
FEISHU_WEBHOOK_QA      = os.environ.get("FEISHU_WEBHOOK_QA",      "PLACEHOLDER")
FEISHU_WEBHOOK_OPS     = os.environ.get("FEISHU_WEBHOOK_OPS",     "PLACEHOLDER")
FEISHU_WEBHOOK_MANAGER = os.environ.get("FEISHU_WEBHOOK_MANAGER", "PLACEHOLDER")


# ── GitHub 配置 ──────────────────────────────────────────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "PLACEHOLDER_GITHUB_TOKEN")
GITHUB_REPO  = os.environ.get("GITHUB_REPO",  "lnQx112/target-project")


# ── Jenkins 配置 ─────────────────────────────────────────────
JENKINS_URL   = os.environ.get("JENKINS_URL",   "http://localhost:8080")
JENKINS_USER  = os.environ.get("JENKINS_USER",  "PLACEHOLDER_JENKINS_USER")
JENKINS_TOKEN = os.environ.get("JENKINS_TOKEN", "PLACEHOLDER_JENKINS_API_TOKEN")


# ── Agent 行为配置 ───────────────────────────────────────────
LLM_TEMPERATURE = 0
LLM_MAX_TOKENS  = 4096
REQUEST_TIMEOUT = 30
