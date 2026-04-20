"""
临时测试脚本，验证豆包 API 是否能正常调用。
测试完可以删掉这个文件。
"""

from openai import OpenAI
import sys
sys.path.insert(0, "agents")
import config

print(f"API Key: {config.DOUBAO_API_KEY[:10]}...")
print(f"Base URL: {config.DOUBAO_BASE_URL}")
print(f"Model: {config.DOUBAO_MODEL}")
print("发送测试请求...")

client = OpenAI(
    api_key=config.DOUBAO_API_KEY,
    base_url=config.DOUBAO_BASE_URL,
)

response = client.chat.completions.create(
    model=config.DOUBAO_MODEL,
    messages=[{"role": "user", "content": "你好，回复'OK'两个字就行"}],
    max_tokens=10,
)

print(f"响应: {response.choices[0].message.content}")
print("测试通过！")
