"""
agent_coverage.py — 场景四：测试覆盖率智能补全

工作流程:
  1. 读取 pytest-cov 生成的覆盖率报告
  2. 找出覆盖率低于阈值的模块
  3. 读取这些模块的源码
  4. 用豆包生成补充测试用例草稿
  5. 以 PR 形式提交草稿，通知测试人员审核

退出码:
  0 = 覆盖率达标或草稿已生成
  1 = 覆盖率严重不足且生成失败

接收方: 测试人员（qa）
触发时机: 每次构建后，或定期（如每天凌晨）
"""

import sys
import json
import xml.etree.ElementTree as ET
import requests
from openai import OpenAI
import config
import notifier


client = OpenAI(api_key=config.DOUBAO_API_KEY, base_url=config.DOUBAO_BASE_URL)

# 覆盖率低于此阈值的模块才会触发补全
# TODO: 根据团队要求调整
COVERAGE_THRESHOLD = 60.0


def parse_coverage_report(report_path: str) -> list[dict]:
    """
    解析 pytest-cov 生成的 XML 覆盖率报告。

    生成报告的命令:
      pytest --cov=your_package --cov-report=xml:coverage.xml

    返回覆盖率低于阈值的模块列表:
    [{"file": "src/foo.py", "coverage": 45.2, "missing_lines": [12, 13, 45]}]

    TODO: 如果你用的是 JSON 格式报告，需要调整解析逻辑
    """
    tree = ET.parse(report_path)
    root = tree.getroot()

    low_coverage = []
    for cls in root.iter("class"):
        filename = cls.get("filename", "")
        line_rate = float(cls.get("line-rate", 1.0)) * 100

        if line_rate < COVERAGE_THRESHOLD:
            missing_lines = [
                int(line.get("number"))
                for line in cls.iter("line")
                if line.get("hits") == "0"
            ]
            low_coverage.append({
                "file": filename,
                "coverage": round(line_rate, 1),
                "missing_lines": missing_lines[:20],  # 最多取 20 行，避免太长
            })

    # 按覆盖率从低到高排序
    return sorted(low_coverage, key=lambda x: x["coverage"])


def get_source_code(file_path: str) -> str:
    """
    从 GitHub 获取源文件内容。

    TODO: 如果 Agent 运行在 Jenkins 上，也可以直接读本地文件：
          with open(file_path, "r", encoding="utf-8") as f:
              return f.read()
    """
    url = f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw",
    }
    resp = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def generate_test_draft(source_code: str, file_path: str, missing_lines: list[int]) -> str:
    """调用豆包为低覆盖率模块生成补充测试用例草稿"""
    prompt = f"""你是一个测试工程师，请为以下 Python 模块生成补充测试用例。

重点覆盖未被测试的行（行号：{missing_lines}）。

## 源文件路径
{file_path}

## 源代码
```python
{source_code[:4000]}
```

请生成完整的 pytest 测试用例，要求：
1. 每个测试函数只测一个场景
2. 包含正常情况和边界情况
3. 使用清晰的中文注释说明每个测试的目的
4. 直接返回可运行的 Python 代码，不要有其他说明文字

只返回代码，用 ```python 包裹。"""

    response = client.chat.completions.create(
        model=config.DOUBAO_MODEL,
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.LLM_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return raw.strip()


def run(report_path: str) -> int:
    """Agent 主入口"""
    print(f"[agent_coverage] 开始分析覆盖率报告: {report_path}")

    low_modules = parse_coverage_report(report_path)
    if not low_modules:
        print(f"[agent_coverage] 所有模块覆盖率均达标（>{COVERAGE_THRESHOLD}%），跳过")
        notifier.send(
            role="qa",
            title="✅ 测试覆盖率达标",
            content=f"所有模块覆盖率均高于 {COVERAGE_THRESHOLD}%，无需补充测试。",
            level="info",
        )
        return 0

    print(f"[agent_coverage] 发现 {len(low_modules)} 个低覆盖率模块，开始生成草稿...")

    drafts = []
    for module in low_modules[:5]:  # 每次最多处理 5 个，避免 token 超限
        try:
            source = get_source_code(module["file"])
            draft = generate_test_draft(source, module["file"], module["missing_lines"])
            drafts.append({
                "file": module["file"],
                "coverage": module["coverage"],
                "draft": draft,
            })
            print(f"[agent_coverage] 已生成草稿: {module['file']} ({module['coverage']}%)")
        except Exception as e:
            print(f"[agent_coverage] 生成草稿失败 {module['file']}: {e}")

    # 构建飞书通知内容
    module_list = "\n".join(
        f"- `{m['file']}` 覆盖率 **{m['coverage']}%**"
        for m in low_modules
    )
    draft_list = "\n".join(
        f"- `{d['file']}` 草稿已生成"
        for d in drafts
    )

    notifier.send(
        role="qa",
        title=f"📊 发现 {len(low_modules)} 个低覆盖率模块",
        content=(
            f"**覆盖率阈值**: {COVERAGE_THRESHOLD}%\n\n"
            f"**低覆盖率模块**:\n{module_list}\n\n"
            f"**已生成草稿**:\n{draft_list or '无'}\n\n"
            f"请在代码仓库中查看草稿 PR 并审核合并。\n\n"
            f"TODO: 草稿 PR 链接（需实现 create_github_pr 后自动填入）"
        ),
        level="warning",
    )

    return 0


if __name__ == "__main__":
    # 用法: python agent_coverage.py <覆盖率报告路径>
    # 例如: python agent_coverage.py coverage.xml
    if len(sys.argv) < 2:
        print("用法: python agent_coverage.py <覆盖率报告路径>")
        sys.exit(1)
    exit_code = run(sys.argv[1])
    sys.exit(exit_code)
