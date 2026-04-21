# target-project

一个用于验证 CI/CD AI Agent 能力的靶子项目，基于 Python + Flask 构建的任务管理系统后端，集成了五个 AI Agent 实现智能化的 CI/CD 流水线。

## 项目结构

```
target-project/
├── app/
│   ├── models.py        # 数据模型（User、Task）
│   ├── services.py      # 业务逻辑（含故意埋入的 bug）
│   ├── routes.py        # HTTP 接口
│   └── utils.py         # 工具函数（覆盖率故意低于 60%）
├── tests/
│   ├── test_models.py   # 模型测试（故意不完整）
│   ├── test_services.py # 服务测试（含会触发 bug 的用例）
│   └── drafts/          # AI 生成的测试用例草稿（人工审核后合并）
├── agents/
│   ├── config.py                 # 全局配置（从环境变量读取）
│   ├── notifier.py               # 飞书通知模块
│   ├── agent_failure_triage.py   # 场景二：测试失败智能分类
│   ├── agent_coverage.py         # 场景四：覆盖率智能补全
│   ├── agent_pr_review.py        # 场景三：PR 代码审查辅助
│   ├── agent_test_updater.py     # 场景一：测试用例自动维护
│   └── agent_impact.py           # 场景五：发布影响评估
├── Jenkinsfile          # Jenkins Pipeline 配置
├── pytest.ini           # pytest 配置
├── requirements.txt
└── .env                 # 本地环境变量（不推送到 GitHub）
```

## 五个 AI Agent

| Agent | 触发时机 | 功能 |
|-------|---------|------|
| 场景一：测试用例维护 | PR 合并到 main 后 | 分析代码变更，生成测试用例更新草稿 PR |
| 场景二：失败分类 | 测试失败后 | 将失败分类为代码 Bug / 环境问题 / 测试过时，按分类通知对应角色 |
| 场景三：PR 审查 | PR 创建或更新时 | 检查新接口是否缺少测试，在 PR 上自动发表审查评论 |
| 场景四：覆盖率补全 | 每次构建后 | 找出低覆盖率模块，生成补充测试用例草稿 PR |
| 场景五：影响评估 | 发布前 | 分析两个版本之间的变更，评估发布风险等级 |

## 故意设计的缺陷

| 位置 | 缺陷 | 触发的 Agent |
|------|------|-------------|
| `services.py:get_high_priority_tasks` | 用字符串 `"3"` 比较整数优先级（已修复，可手动还原测试） | 场景二 |
| `services.py:get_task_summary` | 空数据时 ZeroDivisionError（已修复，可手动还原测试） | 场景二 |
| `utils.py` | 大量函数无测试覆盖 | 场景四 |
| `tests/` | 测试用例不完整 | 场景一、三 |

## 环境配置

**第一步：复制环境变量模板**

在项目根目录创建 `.env` 文件，填入以下内容：

```
DOUBAO_API_KEY=你的豆包APIKey
DOUBAO_MODEL=doubao-seed-2-0-code-preview-260215
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

FEISHU_WEBHOOK_DEV=你的飞书WebhookURL
FEISHU_WEBHOOK_QA=你的飞书WebhookURL
FEISHU_WEBHOOK_OPS=你的飞书WebhookURL
FEISHU_WEBHOOK_MANAGER=你的飞书WebhookURL

GITHUB_TOKEN=你的GitHubToken
GITHUB_REPO=你的用户名/target-project
```

**第二步：在 Jenkins Credentials 中配置同名变量**

Jenkins 运行时不读取 `.env` 文件，需要在 `Manage Jenkins → Credentials` 中添加：
- `DOUBAO_API_KEY`（Secret text）
- `GITHUB_TOKEN_ENV`（Secret text）
- `FEISHU_WEBHOOK`（Secret text）

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试（预期 1 个用例失败）
pytest tests/ -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=xml:coverage.xml

# 启动服务（本地开发用）
python app/routes.py
```

## 手动运行 Agent

```bash
# 场景一：分析 PR #1 的测试用例变更
python agents/agent_test_updater.py 1

# 场景二：分析测试失败报告
python agents/agent_failure_triage.py report.json http://localhost:8080/job/target-project/1/

# 场景三：审查 PR #1
python agents/agent_pr_review.py 1

# 场景四：分析覆盖率
python agents/agent_coverage.py coverage.xml

# 场景五：评估 v1.0.0 到 v1.1.0 的发布影响
python agents/agent_impact.py v1.0.0 v1.1.0
```

## Jenkins 流水线

流水线按以下顺序执行：

```
拉代码 → 安装依赖 → PR审查（有PR时）→ 跑测试 → 失败分类
                                                    ↓
                                          覆盖率分析 → 影响评估（发布时）→ 更新测试用例
```

**触发方式：** 目前为手动触发（`Build Now`）。如需自动触发，需要将 Jenkins 暴露到公网并在 GitHub 配置 Webhook。

## 技术栈

- **业务系统**：Python、Flask
- **测试框架**：pytest、pytest-cov、pytest-json-report
- **CI/CD**：Jenkins Pipeline
- **AI 大模型**：豆包（火山引擎 ARK）
- **通知**：飞书自定义机器人
- **GitHub 集成**：PyGithub、GitHub REST API
