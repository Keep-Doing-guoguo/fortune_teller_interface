#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/8/10 12:13
@source from: 
"""
#!/usr/bin/env python
# coding=utf-8

"""
把 OpenAI 兼容写法改为 DashScope 官方 SDK 流式调用
pip install dashscope
环境变量或代码里设置 DASSCOPE_API_KEY 均可
"""

import os
from typing import Generator, List, Dict, Optional
from http import HTTPStatus
from dashscope import Generation
from config import API_KEY,BASE_URL

# 方式二：也支持从环境变量读取（如果上面不想写死，注释掉上一行并 export DASSCOPE_API_KEY）
os.environ.setdefault("DASHSCOPE_API_KEY", API_KEY)


def _ensure_api_key() -> str:
    """读取 DashScope API Key，没有就报错。"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY 未设置！请在代码里或环境变量配置你的 DashScope Key。")
    return api_key


def generate_stream_response(
    tokenizer=None,
    model: Optional[str] = None,
    messages: List[Dict[str, str]] = None,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> Generator[str, None, None]:
    """
    使用 DashScope 官方 SDK 的流式输出。
    用法与原来一样：
        for chunk in generate_stream_response(messages=history):
            print(chunk, end="", flush=True)
    参数：
      - messages: [{"role":"user"/"assistant"/"system","content":"..."}]
      - model: 不传则默认 "qwen-plus"
    """
    _ensure_api_key()
    model = model or "qwen-plus"

    # 调用 DashScope 的流式接口
    # result_format="message" 表示返回 Chat 格式的增量内容
    stream = Generation.call(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        model=model,
        messages=messages,
        stream=True,
        result_format="message",
        temperature=temperature,
        top_p=top_p,
    )

    # 逐步吐出增量内容
    for resp in stream:
        # 成功的增量
        if resp.status_code == HTTPStatus.OK and resp.output and resp.output.choices:
            # choices 是一个列表，拿第一条
            choice = resp.output.choices[0]
            # 增量内容在 choice.message.content
            if hasattr(choice, "message") and getattr(choice.message, "content", None):
                yield choice.message.content
        # 流式结束事件（可选处理）
        elif resp.status_code == HTTPStatus.OK and getattr(resp, "finish_reason", None):
            # 如需在结束时做处理，可以在这里判断 finish_reason
            pass
        else:
            # 出错就抛异常，外层可捕获
            raise RuntimeError(
                f"DashScope stream error: status={resp.status_code}, code={getattr(resp, 'code', None)}, message={getattr(resp, 'message', None)}"
            )


if __name__ == "__main__":
    # 示例：与原来一样的 history
    history = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么我可以帮你的吗？"},
        {"role": "user", "content": "介绍一下明朝的第一位皇帝。"},
    ]

    # 流式打印
    for token in generate_stream_response(messages=history):
        print(token, end="", flush=True)
    print()

