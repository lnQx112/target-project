# target-project

一个用于验证 CI/CD Agent 能力的靶子项目。

## 项目结构

```
target-project/
├── app/
│   ├── models.py      # 数据模型（User、Task）
│   ├── services.py    # 业务逻辑（含 3 个故意埋入的 bug）
│   ├── routes.py      # HTTP 接口
│   └── utils.py       # 工具函数（覆盖率故意低于 60%）
├── tests/
│   ├── test_models.py  # 模型测试（故意不完整）
│   └── test_services.py # 服务测试（含会触发 bug 的用例）
├── agents/            # 五个 CI/CD Agent（从 agents/ 目录复制过来）
├── Jenkinsfile
└── requirements.txt
```

## 故意设计的缺陷

| 位置 | 缺陷 | 触发的 Agent |
|------|------|-------------|
| `services.py:create_task` | 未校验 owner_id 是否存在 | 场景二：失败分类 |
| `services.py:get_high_priority_tasks` | 用字符串 `"3"` 比较整数优先级 | 场景二：失败分类 |
| `services.py:get_task_summary` | 空数据时 ZeroDivisionError | 场景二：失败分类 |
| `utils.py` | 大量函数无测试覆盖 | 场景四：覆盖率补全 |
| `tests/` | 测试用例不完整 | 场景一、三 |

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试（会有 2 个用例失败，这是预期行为）
pytest tests/ -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=xml:coverage.xml

# 启动服务
python app/routes.py
```

## 配置 Agent

把 `agents/` 目录下的 `config.py` 填入真实的 API Key 后，即可运行各个 Agent：

```bash
# 场景二：分析测试失败
python agents/agent_failure_triage.py report.json http://localhost:8080/job/xxx/1

# 场景四：分析覆盖率
python agents/agent_coverage.py coverage.xml
```
