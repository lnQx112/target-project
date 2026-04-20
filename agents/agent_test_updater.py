"""
agent_test_updater.py — 场景一：版本更新后自动维护测试用例

工作流程:
  1. 从 GitHub 获取最新的代码 diff
  2. 用豆包分析 diff，理解哪些接口/逻辑发生了变化
  3. 找到受影响的测试文件
  4. 生成需要修改的测试用例草稿
  5. 以 PR 的形式提交草稿，通知开发者和测试人员审核

接收方: 开发者（dev）+ 测试人员（qa）
触发时机: PR 合并到主干后
"""

import sys
import json
import requests
from openai import OpenAI
import config
import notifier


# ── LLM 客户端 ───────────────────────────────────────────────
client = OpenAI(api_key=config.DOUBAO_API_KEY, base_url=config.DOUBAO_BASE_URL)


def get_pr_diff(pr_number: int) -> str:
    """从 GitHub 获取指定 PR 的代码 diff"""
    url = f"https://api.github.com/repos/{config.GITHUB_REPO}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()

    files = resp.json()
    diff_text = ""
    for f in files:
        diff_text += f"\n### 文件: {f['filename']}\n"
        diff_text += f['patch'] if 'patch' in f else "(二进制文件，跳过)"
    return diff_text


def get_test_files() -> list[str]:
    """
    从 GitHub 获取仓库中所有测试文件的路径列表。

    TODO: 根据你们项目的测试文件命名规范调整 glob 参数
          默认查找 test_*.py 和 *_test.py
    """
    url = f"https://api.github.com/repos/{config.GITHUB_REPO}/git/trees/HEAD"
    headers = {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    # recursive=1 递归获取所有文件
    resp = requests.get(url, params={"recursive": 1}, headers=headers, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()

    tree = resp.json().get("tree", [])
    test_files = [
        item["path"] for item in tree
        if item["type"] == "blob"
        and (item["path"].startswith("test_") or item["path"].endswith("_test.py")
             or "/tests/" in item["path"])
    ]
    return test_files


def get_file_content(file_path: str) -> str:
    """从 GitHub 获取指定文件的内容"""
    url = f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw",  # 直接返回原始内容
    }
    resp = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def analyze_diff_and_generate_updates(diff: str, test_files_content: dict) -> dict:
    """
    调用豆包分析 diff，生成测试用例更新草稿。

    返回格式:
    {
        "affected_tests": ["tests/test_foo.py", ...],
        "suggestions": [
            {
                "file": "tests/test_foo.py",
                "action": "modify",   # modify / add / delete
                "description": "...",
                "draft_code": "..."
            }
        ],
        "summary": "本次变更影响了 X 个测试文件..."
    }
    """
    test_context = "\n\n".join(
        f"# {path}\n{content[:2000]}"  # 每个文件最多取前 2000 字符避免超 token
        for path, content in test_files_content.items()
    )

    prompt = f"""你是一个测试工程师。以下是一次代码变更的 diff，以及现有的测试文件内容。

请分析：
1. 哪些现有测试用例需要修改（接口变了、参数变了、返回值变了）
2. 哪些地方需要新增测试用例
3. 哪些测试用例可能因为代码删除而需要移除

## 代码变更 diff
{diff[:6000]}

## 现有测试文件
{test_context[:4000]}

请以 JSON 格式返回，结构如下：
{{
    "affected_tests": ["受影响的测试文件路径列表"],
    "suggestions": [
        {{
            "file": "tests/drafts/draft_test_xxx_pr{pr_number}.py",
            "action": "add",
            "description": "需要新增哪些测试用例，用中文说明",
            "draft_code": "完整的草稿测试代码，注意不要修改原有测试文件"
        }}
    ],
    "summary": "整体影响的中文摘要，2-3句话"
}}

重要规则：
- 草稿文件统一放在 tests/drafts/ 目录下
- 文件名格式：draft_test_<模块名>_pr{pr_number}.py
- 不要修改原有测试文件，只生成新的草稿文件
- 只返回 JSON，不要有其他文字。"""

    response = client.chat.completions.create(
        model=config.DOUBAO_MODEL,
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.LLM_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.choices[0].message.content.strip()
    # 去掉可能的 markdown 代码块包裹
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(raw)


def create_github_pr(branch_name: str, file_path: str, new_content: str, pr_title: str, pr_body: str) -> str:
    """
    在 GitHub 上创建一个包含测试用例草稿的 PR。
    返回 PR 的 URL。

    TODO: 这里简化了流程，实际需要：
          1. 创建新分支
          2. 提交文件修改
          3. 创建 PR
          完整实现可参考 PyGithub 库：pip install PyGithub
    """
    # TODO: 用 PyGithub 实现完整的 PR 创建流程
    # from github import Github
    # g = Github(config.GITHUB_TOKEN)
    # repo = g.get_repo(config.GITHUB_REPO)
    # ...
    print(f"[agent_test_updater] TODO: 创建 PR，分支: {branch_name}")
    return f"https://github.com/{config.GITHUB_REPO}/pull/PLACEHOLDER"


def run(pr_number: int):
    """Agent 主入口"""
    print(f"[agent_test_updater] 开始分析 PR #{pr_number}")

    # 1. 获取 diff
    diff = get_pr_diff(pr_number)
    if not diff.strip():
        print("[agent_test_updater] diff 为空，跳过")
        return

    # 2. 获取测试文件内容
    test_files = get_test_files()
    test_files_content = {}
    for path in test_files[:10]:  # 最多取 10 个文件，避免 token 超限
        try:
            test_files_content[path] = get_file_content(path)
        except Exception:
            pass

    # 3. 调用 LLM 分析
    result = analyze_diff_and_generate_updates(diff, test_files_content)

    # 4. 如果有需要更新的测试，创建 PR
    pr_url = "（无需更新）"
    if result.get("suggestions"):
        # 草稿文件统一放到 tests/drafts/ 目录，不覆盖原有测试文件
        suggestion = result["suggestions"][0]
        draft_file = suggestion.get("file", f"tests/drafts/draft_test_pr{pr_number}.py")
        # 确保路径在 tests/drafts/ 下
        if not draft_file.startswith("tests/drafts/"):
            draft_file = f"tests/drafts/draft_test_pr{pr_number}.py"

        pr_url = create_github_pr(
            branch_name=f"auto/update-tests-for-pr-{pr_number}",
            file_path=draft_file,
            new_content=suggestion.get("draft_code", ""),
            pr_title=f"[自动] 测试用例草稿 - 关联 PR #{pr_number}",
            pr_body=f"## AI 生成的测试用例草稿\n\n{result['summary']}\n\n> 请审核后手动将有价值的用例复制到正式测试文件，然后删除此草稿文件。",
        )

    # 5. 发送飞书通知
    affected = "\n".join(f"- `{f}`" for f in result.get("affected_tests", []))
    suggestions = "\n".join(
        f"- **{s['file']}**：{s['description']}"
        for s in result.get("suggestions", [])
    )

    notifier.send(
        role="qa",
        title="📋 测试用例需要更新",
        content=(
            f"**关联 PR**: #{pr_number}\n\n"
            f"**影响摘要**: {result.get('summary', '无')}\n\n"
            f"**受影响的测试文件**:\n{affected or '无'}\n\n"
            f"**建议修改**:\n{suggestions or '无'}\n\n"
            f"**草稿 PR**: {pr_url}"
        ),
        level="warning" if result.get("suggestions") else "info",
    )
    notifier.send(
        role="dev",
        title="📋 测试用例更新草稿已生成",
        content=f"PR #{pr_number} 合并后，测试团队已收到更新建议。\n草稿 PR: {pr_url}",
        level="info",
    )

    print(f"[agent_test_updater] 完成，草稿 PR: {pr_url}")


if __name__ == "__main__":
    # 用法: python agent_test_updater.py <PR编号>
    # 例如: python agent_test_updater.py 42
    if len(sys.argv) < 2:
        print("用法: python agent_test_updater.py <PR编号>")
        sys.exit(1)
    run(int(sys.argv[1]))
