"""
agent_pr_review.py — 场景三：PR 代码审查辅助

工作流程:
  1. 获取 GitHub PR 的 diff
  2. 用豆包检查：
     - 有没有新增接口但缺少对应测试
     - 有没有修改接口但测试没跟着改
     - 有没有明显的边界情况未覆盖
  3. 在 PR 上自动发表评论（不拦截，只提醒）
  4. 通知开发者和测试人员

退出码: 始终为 0（只提醒，不拦截）

接收方: 开发者（dev）+ 测试人员（qa）
触发时机: PR 创建或更新时
"""

import sys
import json
import requests
from openai import OpenAI
import config
import notifier


client = OpenAI(api_key=config.DOUBAO_API_KEY, base_url=config.DOUBAO_BASE_URL)


def get_pr_info(pr_number: int) -> dict:
    """获取 PR 的基本信息和 diff"""
    headers = {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    base = f"https://api.github.com/repos/{config.GITHUB_REPO}"

    # PR 基本信息
    pr_resp = requests.get(f"{base}/pulls/{pr_number}", headers=headers, timeout=config.REQUEST_TIMEOUT)
    pr_resp.raise_for_status()
    pr_data = pr_resp.json()

    # PR 变更文件列表
    files_resp = requests.get(f"{base}/pulls/{pr_number}/files", headers=headers, timeout=config.REQUEST_TIMEOUT)
    files_resp.raise_for_status()
    files = files_resp.json()

    # 分离业务代码和测试代码
    source_files = []
    test_files = []
    for f in files:
        path = f["filename"]
        patch = f.get("patch", "")
        if "test" in path.lower():
            test_files.append({"path": path, "patch": patch})
        else:
            source_files.append({"path": path, "patch": patch})

    return {
        "title": pr_data.get("title", ""),
        "author": pr_data.get("user", {}).get("login", ""),
        "pr_url": pr_data.get("html_url", ""),
        "source_files": source_files,
        "test_files": test_files,
    }


def review_pr(pr_info: dict) -> dict:
    """
    调用豆包审查 PR，返回审查结果。

    返回格式:
    {
        "missing_tests": ["缺少测试的接口或函数描述"],
        "outdated_tests": ["需要更新的测试描述"],
        "uncovered_cases": ["未覆盖的边界情况描述"],
        "overall_risk": "low / medium / high",
        "comment": "适合直接发到 PR 评论区的 markdown 文本"
    }
    """
    source_diff = "\n\n".join(
        f"### {f['path']}\n{f['patch'][:1500]}"
        for f in pr_info["source_files"]
    )
    test_diff = "\n\n".join(
        f"### {f['path']}\n{f['patch'][:1500]}"
        for f in pr_info["test_files"]
    )

    prompt = f"""你是一个代码审查专家，专注于测试覆盖率分析。

请审查以下 PR 的变更，重点检查：
1. 新增或修改的接口/函数有没有对应的测试
2. 已有测试是否需要随代码变更而更新
3. 有没有明显的边界情况（空值、越界、异常路径）未被测试覆盖

## 业务代码变更
{source_diff[:4000] or "（无业务代码变更）"}

## 测试代码变更
{test_diff[:2000] or "（无测试代码变更）"}

请以 JSON 格式返回，结构如下：
{{
    "missing_tests": ["缺少测试的具体描述，每条一句话"],
    "outdated_tests": ["需要更新的测试描述，每条一句话"],
    "uncovered_cases": ["未覆盖的边界情况，每条一句话"],
    "overall_risk": "low 或 medium 或 high",
    "comment": "适合发到 PR 评论区的 markdown 格式审查意见，用中文，语气友好"
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


def post_pr_comment(pr_number: int, comment: str):
    """在 GitHub PR 上发表评论"""
    url = f"https://api.github.com/repos/{config.GITHUB_REPO}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {"body": f"🤖 **AI 代码审查建议**\n\n{comment}\n\n---\n*此评论由 AI Agent 自动生成，仅供参考，最终决策由人工审核。*"}
    resp = requests.post(url, json=payload, headers=headers, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()
    print(f"[agent_pr_review] 已在 PR #{pr_number} 发表评论")


def run(pr_number: int):
    """Agent 主入口"""
    print(f"[agent_pr_review] 开始审查 PR #{pr_number}")

    pr_info = get_pr_info(pr_number)
    result = review_pr(pr_info)

    # 在 PR 上发表评论
    post_pr_comment(pr_number, result.get("comment", "无审查意见"))

    # 风险等级映射
    risk = result.get("overall_risk", "low")
    risk_label = {"low": "🟢 低", "medium": "🟡 中", "high": "🔴 高"}.get(risk, "未知")
    level = {"low": "info", "medium": "warning", "high": "error"}.get(risk, "info")

    missing = "\n".join(f"- {m}" for m in result.get("missing_tests", [])) or "无"
    outdated = "\n".join(f"- {o}" for o in result.get("outdated_tests", [])) or "无"
    uncovered = "\n".join(f"- {u}" for u in result.get("uncovered_cases", [])) or "无"

    content = (
        f"**PR**: [{pr_info['title']}]({pr_info['pr_url']})\n"
        f"**作者**: {pr_info['author']}\n"
        f"**风险等级**: {risk_label}\n\n"
        f"**缺少测试**:\n{missing}\n\n"
        f"**需要更新的测试**:\n{outdated}\n\n"
        f"**未覆盖的边界情况**:\n{uncovered}"
    )

    notifier.send(role="dev", title=f"🔍 PR 审查完成 - 风险{risk_label}", content=content, level=level)
    notifier.send(role="qa", title=f"🔍 PR #{pr_number} 测试覆盖分析", content=content, level=level)

    print(f"[agent_pr_review] 完成，风险等级: {risk}")


if __name__ == "__main__":
    # 用法: python agent_pr_review.py <PR编号>
    if len(sys.argv) < 2:
        print("用法: python agent_pr_review.py <PR编号>")
        sys.exit(1)
    run(int(sys.argv[1]))
