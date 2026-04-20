"""
agent_impact.py — 场景五：上线前变更影响评估

工作流程:
  1. 获取本次发布版本和上一个版本之间的所有 commit diff
  2. 用豆包分析变更范围、影响模块、风险等级
  3. 给出建议的重点回归测试范围
  4. 向不同角色发送评估报告
  5. 高风险时通知管理者，由人工决定是否继续发布

退出码:
  0 = 低/中风险，流水线可继续
  1 = 高风险，建议人工介入确认

接收方: 开发者（dev）+ 测试人员（qa）+ 运维（ops）+ 管理者（manager，仅高风险）
触发时机: 发布流水线开始前
"""

import sys
import json
import requests
from openai import OpenAI
import config
import notifier


client = OpenAI(api_key=config.DOUBAO_API_KEY, base_url=config.DOUBAO_BASE_URL)


def get_compare_diff(base_tag: str, head_tag: str) -> dict:
    """
    获取两个版本之间的代码差异。

    参数:
        base_tag: 上一个版本的 tag，如 "v1.2.0"
        head_tag: 本次发布的 tag 或分支，如 "v1.3.0" 或 "main"
    """
    url = f"https://api.github.com/repos/{config.GITHUB_REPO}/compare/{base_tag}...{head_tag}"
    headers = {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    # 提取关键信息
    commits = [
        {
            "sha": c["sha"][:7],
            "message": c["commit"]["message"].split("\n")[0],  # 只取第一行
            "author": c["commit"]["author"]["name"],
        }
        for c in data.get("commits", [])
    ]

    files = [
        {
            "filename": f["filename"],
            "status": f["status"],          # added / modified / removed
            "additions": f["additions"],
            "deletions": f["deletions"],
            "patch": f.get("patch", "")[:500],  # 只取前 500 字符
        }
        for f in data.get("files", [])
    ]

    return {
        "total_commits": len(commits),
        "total_files": len(files),
        "commits": commits[:20],    # 最多取 20 个 commit
        "files": files[:30],        # 最多取 30 个文件
    }


def evaluate_impact(diff_data: dict, base_tag: str, head_tag: str) -> dict:
    """
    调用豆包评估变更影响。

    返回格式:
    {
        "risk_level": "low / medium / high",
        "risk_reasons": ["风险原因列表"],
        "affected_modules": ["受影响的模块列表"],
        "regression_focus": ["建议重点回归测试的范围"],
        "release_suggestion": "建议的发布策略",
        "summary": "整体评估摘要"
    }
    """
    diff_text = json.dumps(diff_data, ensure_ascii=False, indent=2)

    prompt = f"""你是一个资深发布工程师，请评估以下版本变更的发布风险。

版本对比: {base_tag} → {head_tag}

## 变更数据
{diff_text[:5000]}

请从以下维度评估风险：
1. 变更规模（文件数量、代码行数）
2. 变更类型（核心逻辑、配置、依赖、测试）
3. 高风险文件（认证、支付、数据库迁移等）
4. 是否有删除操作（删除比新增风险更高）

请以 JSON 格式返回，结构如下：
{{
    "risk_level": "low 或 medium 或 high",
    "risk_reasons": ["风险原因，每条一句话，中文"],
    "affected_modules": ["受影响的模块名称"],
    "regression_focus": ["建议重点回归测试的功能点，每条一句话，中文"],
    "release_suggestion": "建议的发布策略，如：灰度发布、全量发布、建议推迟等，中文",
    "summary": "2-3句话的整体评估摘要，中文"
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


def send_notifications(result: dict, diff_data: dict, base_tag: str, head_tag: str):
    """向各角色发送评估报告"""
    risk = result.get("risk_level", "low")
    risk_label = {"low": "🟢 低风险", "medium": "🟡 中风险", "high": "🔴 高风险"}.get(risk, "未知")
    level = {"low": "info", "medium": "warning", "high": "error"}.get(risk, "info")

    reasons = "\n".join(f"- {r}" for r in result.get("risk_reasons", [])) or "无"
    modules = "\n".join(f"- {m}" for m in result.get("affected_modules", [])) or "无"
    regression = "\n".join(f"- {r}" for r in result.get("regression_focus", [])) or "无"

    base_content = (
        f"**版本**: {base_tag} → {head_tag}\n"
        f"**变更规模**: {diff_data['total_commits']} 个 commit，{diff_data['total_files']} 个文件\n"
        f"**风险等级**: {risk_label}\n\n"
        f"**风险原因**:\n{reasons}\n\n"
        f"**受影响模块**:\n{modules}\n\n"
        f"**建议回归测试范围**:\n{regression}\n\n"
        f"**发布建议**: {result.get('release_suggestion', '无')}"
    )

    # 通知测试人员：重点回归范围
    notifier.send(role="qa", title=f"🚀 发布前影响评估 - {risk_label}", content=base_content, level=level)

    # 通知开发者：变更摘要
    notifier.send(
        role="dev",
        title=f"🚀 {head_tag} 发布影响评估",
        content=f"**摘要**: {result.get('summary', '无')}\n\n{base_content}",
        level=level,
    )

    # 通知运维：发布建议
    notifier.send(
        role="ops",
        title=f"🚀 {head_tag} 即将发布 - {risk_label}",
        content=(
            f"**发布建议**: {result.get('release_suggestion', '无')}\n\n"
            f"**风险等级**: {risk_label}\n"
            f"**变更规模**: {diff_data['total_commits']} commits，{diff_data['total_files']} 文件"
        ),
        level=level,
    )

    # 高风险时额外通知管理者
    if risk == "high":
        notifier.send(
            role="manager",
            title=f"🔴 高风险发布需要确认 - {head_tag}",
            content=(
                f"**本次发布被评估为高风险，建议人工确认后再继续。**\n\n"
                f"{base_content}"
            ),
            level="error",
        )


def run(base_tag: str, head_tag: str) -> int:
    """Agent 主入口"""
    print(f"[agent_impact] 开始评估 {base_tag} → {head_tag} 的变更影响")

    diff_data = get_compare_diff(base_tag, head_tag)
    print(f"[agent_impact] 获取到 {diff_data['total_commits']} 个 commit，{diff_data['total_files']} 个文件")

    result = evaluate_impact(diff_data, base_tag, head_tag)
    send_notifications(result, diff_data, base_tag, head_tag)

    risk = result.get("risk_level", "low")
    exit_code = 1 if risk == "high" else 0

    print(f"[agent_impact] 评估完成，风险等级: {risk}，退出码: {exit_code}")
    return exit_code


if __name__ == "__main__":
    # 用法: python agent_impact.py <上一版本tag> <本次版本tag>
    # 例如: python agent_impact.py v1.2.0 v1.3.0
    if len(sys.argv) < 3:
        print("用法: python agent_impact.py <上一版本tag> <本次版本tag>")
        sys.exit(1)
    exit_code = run(sys.argv[1], sys.argv[2])
    sys.exit(exit_code)
