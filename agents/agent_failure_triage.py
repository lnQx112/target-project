"""
agent_failure_triage.py — 场景二：测试失败智能分类

工作流程:
  1. 读取 Jenkins 传入的测试失败报告（JSON 格式）
  2. 用豆包对每条失败进行分类
  3. 按分类走不同的后续流程：
     - 环境问题 → 通知运维，建议重试
     - 代码 bug  → 通知开发者，附定位分析
     - 测试过时  → 通知测试人员，建议更新
  4. 输出结构化报告，Jenkins 根据退出码决定是否拦截流水线

退出码:
  0 = 全部是环境问题或测试过时，流水线可继续
  1 = 存在代码 bug，流水线应拦截

接收方: 按分类分别通知 dev / qa / ops
触发时机: CI 测试阶段失败后
"""

import sys
import json
import requests
from openai import OpenAI
import config
import notifier


client = OpenAI(api_key=config.DOUBAO_API_KEY, base_url=config.DOUBAO_BASE_URL)


def parse_junit_report(report_path: str) -> list[dict]:
    """
    解析 pytest 生成的 JSON 测试报告。

    TODO: 如果你用的是 JUnit XML 格式，需要改用 xml.etree.ElementTree 解析
          pytest 生成 JSON 报告需要安装: pip install pytest-json-report
          运行命令: pytest --json-report --json-report-file=report.json
    """
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    failures = []
    for test in data.get("tests", []):
        if test.get("outcome") == "failed":
            failures.append({
                "test_id": test.get("nodeid", ""),
                "error_message": test.get("call", {}).get("longrepr", ""),
                "duration": test.get("call", {}).get("duration", 0),
            })
    return failures


def classify_failures(failures: list[dict]) -> dict:
    """
    调用豆包对所有失败进行分类。

    返回格式:
    {
        "classifications": [
            {
                "test_id": "tests/test_foo.py::test_bar",
                "category": "code_bug",   # code_bug / env_issue / outdated_test
                "reason": "...",
                "suggestion": "..."
            }
        ],
        "summary": {
            "code_bug": 2,
            "env_issue": 1,
            "outdated_test": 1
        }
    }
    """
    failures_text = json.dumps(failures, ensure_ascii=False, indent=2)

    prompt = f"""你是一个资深测试工程师，请对以下测试失败进行分类分析。

分类规则：
- code_bug: 代码逻辑错误导致的失败，需要开发者修复
- env_issue: 环境问题（网络超时、依赖版本冲突、数据库连接失败等），重试可能解决
- outdated_test: 测试用例本身过时了（接口已变更但测试没更新），需要测试人员更新

## 失败列表
{failures_text}

请以 JSON 格式返回，结构如下：
{{
    "classifications": [
        {{
            "test_id": "测试用例 ID",
            "category": "code_bug 或 env_issue 或 outdated_test",
            "reason": "判断依据，中文说明",
            "suggestion": "建议的处理方式，中文说明"
        }}
    ],
    "summary": {{
        "code_bug": 数量,
        "env_issue": 数量,
        "outdated_test": 数量
    }}
}}

只返回 JSON，不要有其他文字。"""

    response = client.chat.completions.create(
        model=config.DOUBAO_MODEL,
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.LLM_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(raw)


def send_notifications(result: dict, build_url: str):
    """按分类向不同角色发送飞书通知"""
    classifications = result.get("classifications", [])
    summary = result.get("summary", {})

    # 按分类分组
    bugs = [c for c in classifications if c["category"] == "code_bug"]
    env_issues = [c for c in classifications if c["category"] == "env_issue"]
    outdated = [c for c in classifications if c["category"] == "outdated_test"]

    # 通知开发者：代码 bug
    if bugs:
        bug_list = "\n".join(
            f"- `{b['test_id']}`\n  原因：{b['reason']}\n  建议：{b['suggestion']}"
            for b in bugs
        )
        notifier.send(
            role="dev",
            title=f"🐛 发现 {len(bugs)} 个代码 Bug",
            content=(
                f"**构建地址**: {build_url}\n\n"
                f"**需要修复的测试失败**:\n{bug_list}"
            ),
            level="error",
        )

    # 通知运维：环境问题
    if env_issues:
        env_list = "\n".join(
            f"- `{e['test_id']}`：{e['reason']}"
            for e in env_issues
        )
        notifier.send(
            role="ops",
            title=f"⚠️ 发现 {len(env_issues)} 个环境问题",
            content=(
                f"**构建地址**: {build_url}\n\n"
                f"**环境问题列表**:\n{env_list}\n\n"
                f"建议检查网络、依赖版本或数据库连接后重试。"
            ),
            level="warning",
        )

    # 通知测试人员：过时的测试
    if outdated:
        outdated_list = "\n".join(
            f"- `{o['test_id']}`：{o['suggestion']}"
            for o in outdated
        )
        notifier.send(
            role="qa",
            title=f"📝 发现 {len(outdated)} 个过时测试用例",
            content=(
                f"**构建地址**: {build_url}\n\n"
                f"**需要更新的测试**:\n{outdated_list}"
            ),
            level="warning",
        )

    # 向管理者发送总览
    notifier.send(
        role="manager",
        title="📊 测试失败分析报告",
        content=(
            f"**构建地址**: {build_url}\n\n"
            f"**分类汇总**:\n"
            f"- 🐛 代码 Bug: {summary.get('code_bug', 0)} 个\n"
            f"- ⚠️ 环境问题: {summary.get('env_issue', 0)} 个\n"
            f"- 📝 过时测试: {summary.get('outdated_test', 0)} 个"
        ),
        level="error" if summary.get("code_bug", 0) > 0 else "warning",
    )


def run(report_path: str, build_url: str) -> int:
    """
    Agent 主入口。
    返回退出码：0 = 可继续，1 = 需要拦截
    """
    print(f"[agent_failure_triage] 开始分析测试报告: {report_path}")

    failures = parse_junit_report(report_path)
    if not failures:
        print("[agent_failure_triage] 没有失败的测试，跳过")
        return 0

    print(f"[agent_failure_triage] 发现 {len(failures)} 个失败，开始分类...")
    result = classify_failures(failures)

    send_notifications(result, build_url)

    # 有代码 bug 才拦截流水线
    has_code_bug = result.get("summary", {}).get("code_bug", 0) > 0
    exit_code = 1 if has_code_bug else 0

    print(f"[agent_failure_triage] 分析完成，退出码: {exit_code}")
    return exit_code


if __name__ == "__main__":
    # 用法: python agent_failure_triage.py <报告路径> <构建URL>
    # 例如: python agent_failure_triage.py report.json http://jenkins/job/xxx/42
    if len(sys.argv) < 3:
        print("用法: python agent_failure_triage.py <报告路径> <构建URL>")
        sys.exit(1)
    exit_code = run(sys.argv[1], sys.argv[2])
    sys.exit(exit_code)
