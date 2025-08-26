#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/8/10 12:13
@source from: 
"""
#!/usr/bin/env python
# coding=utf-8


import dashscope
from config import API_KEY
dashscope.api_key = API_KEY

def generate_response(tokenizer,model,messages):
    # 把 messages 转换成 dashscope 支持的格式
    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])

    response = dashscope.Generation.call(
        model="qwen-plus",
        prompt=prompt
    )
    return response["output"]["text"]

# messages = [
#     {"role": "user", "content": "你好"},
#     {"role": "assistant", "content": "你好，有什么我可以帮你的吗？"},
#     {"role": "user", "content": "给我讲个笑话"},
# ]
#
#
# tokenizer = None
# model = None
#
# answer = generate_response(tokenizer,model,messages)
# print(answer)
