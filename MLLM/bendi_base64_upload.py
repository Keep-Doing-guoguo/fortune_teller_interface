#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/8/26 11:03
@source from: 
"""
import base64
import dashscope
import json
import re
from config import API_KEY

dashscope.api_key = API_KEY
def bendi_upload(file_path):
    # 读取本地图片 -> base64
    with open(file_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    messages = [
        {
            "role": "user",
            "content": [
                {"image": f"data:image/jpeg;base64,{img_b64}"},
                {"text": "描述一下这个掌纹感情线，生命线，智慧线，婚姻线，事业线,格式按照 **感情线**：内容\n给出,最后一行给出掌纹不科学"}
            ]
        }
    ]

    resp = dashscope.MultiModalConversation.call(
        model="qwen-vl-max-latest",
        messages=messages
    )
    content = resp["output"]["choices"][0]["message"]["content"][0]['text']
    # 使用正则表达式提取每条掌纹后的文本
    patterns = {
        "生命线": r"\*\*生命线\*\*：(.*?)\n",
        "智慧线": r"\*\*智慧线\*\*：(.*?)\n",
        "感情线": r"\*\*感情线\*\*：(.*?)\n",
        "婚姻线": r"\*\*婚姻线\*\*：(.*?)\n",
        "事业线": r"\*\*事业线\*\*：(.*?)\n",
    }
    print(content)
    palm_lines = {}
    for line_name, pattern in patterns.items():
        match = re.search(pattern, content, re.S)
        if match:
            palm_lines[line_name] = match.group(1).strip()
        else:
            palm_lines[line_name] = "未提及"

    print(json.dumps(palm_lines, ensure_ascii=False, indent=2))
    return palm_lines
    #print(resp["output"]["choices"][0]["message"]["content"])

bendi_upload('/Volumes/PSSD/未命名文件夹/fortune_teller-main/uploads/uploaded_image.jpg')

'''
[{'text': '**感情线**：感情线从手掌边缘延伸至中指下方，线条清晰且较为平直，显示出情感表达较为稳定，对人际关系有较强的敏感度，但情绪波动相对较小。\n\n**生命线**：生命线从拇指根部开始，环绕大鱼际区域，弧度适中，线条较深，表明生命力较强，身体健康状况良好，具有较强的抗压能力与恢复力。\n\n**智慧线**：智慧线横贯手掌中部，从拇指侧延伸至小指侧，线条清晰且略带弯曲，显示出思维活跃、逻辑性强，具备良好的学习能力和判断力，但偶尔可能过于理性而忽略感性因素。\n\n**婚姻线**：婚姻线位于小指根部下方，出现两条平行的短线，其中一条较长且明显，另一条较短，表明在感情关系中有过一次较为稳定的婚姻或长期伴侣关系，可能存在一段短暂的情感经历或波折。\n\n**事业线**：事业线从掌心中央向上延伸，穿过智慧线并接近中指下方，线条清晰且有分叉，说明事业心强，有明确的职业目标，适合从事需要创造力和独立决策的工作，职业生涯中可能会经历阶段性的转折或挑战。\n\n掌纹不科学'}]
'''


