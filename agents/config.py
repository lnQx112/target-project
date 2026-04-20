# ============================================================
# 全局配置文件
# 所有 Agent 共用，填入真实值后即可运行
# ============================================================


# ── 豆包大模型（字节跳动）────────────────────────────────────
# 官网: https://console.volcengine.com/ark
# TODO: 注册后在控制台创建 API Key 填入下方
DOUBAO_API_KEY  = "PLACEHOLDER_DOUBAO_API_KEY"
DOUBAO_MODEL    = "doubao-pro-32k"          # TODO: 按需替换模型名
DOUBAO_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"


# ── 飞书机器人 Webhook ───────────────────────────────────────
# 在飞书群里添加「自定义机器人」，复制 Webhook 地址填入下方
# 文档: https://open.feishu.cn/document/client-docs/bot-5/add-custom-bot
# TODO: 按角色分别配置不同的群，也可以都填同一个群
FEISHU_WEBHOOK_DEV     = "https://open.feishu.cn/open-apis/bot/v2/hook/PLACEHOLDER"  # 开发者群
FEISHU_WEBHOOK_QA      = "https://open.feishu.cn/open-apis/bot/v2/hook/PLACEHOLDER"  # 测试群
FEISHU_WEBHOOK_OPS     = "https://open.feishu.cn/open-apis/bot/v2/hook/PLACEHOLDER"  # 运维群
FEISHU_WEBHOOK_MANAGER = "https://open.feishu.cn/open-apis/bot/v2/hook/PLACEHOLDER"  # 管理者群


# ── GitHub 配置 ──────────────────────────────────────────────
# TODO: 在 GitHub Settings → Developer settings → Personal access tokens 创建
# 需要的权限: repo（读取代码和 PR）、pull_requests（写评论）
GITHUB_TOKEN = "PLACEHOLDER_GITHUB_TOKEN"
GITHUB_REPO  = "your-org/your-repo"        # TODO: 替换为你的仓库，格式: 组织/仓库名


# ── Jenkins 配置 ─────────────────────────────────────────────
# TODO: Jenkins 的访问地址和凭证
JENKINS_URL      = "http://your-jenkins-server:8080"  # TODO: 替换为实际地址
JENKINS_USER     = "PLACEHOLDER_JENKINS_USER"
JENKINS_TOKEN    = "PLACEHOLDER_JENKINS_API_TOKEN"


# ── Agent 行为配置 ───────────────────────────────────────────
# 大模型温度，0 = 最确定性，适合代码分析场景
LLM_TEMPERATURE = 0

# 单次 LLM 调用最大 token 数
LLM_MAX_TOKENS = 4096

# HTTP 请求超时（秒）
REQUEST_TIMEOUT = 30
