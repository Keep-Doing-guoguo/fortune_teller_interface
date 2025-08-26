#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/8/25 20:23
@source from: 
"""
from MLLM.MMML_MY import MMML
from MLLM.preprocess import preprocess_hand_image
from RAG.utils import rag_matching
from RAG.Knowledge import KnowledgeBase
from LLM.api_model_qwen_no_stream import generate_response
from LLM.api_model_qwen import generate_stream_response

PROMPT = """
你是一个算命大师,你需要结合用户的手相特征和已知信息回答用户的问题

现在用户的手相特征如下:
---
{MMML_res}
---

目前已知的信息是:
---
{RAG_res}
---

用户的问题是:
---
{user_input}
---
"""

def build_prompt(mmml_res: str, rag_res: str, user_text: str) -> str:
    return PROMPT.format(MMML_res=mmml_res, RAG_res=rag_res, user_input=user_text)


MMML_res = MMML(
        "https://image-bed-datawhale.oss-cn-beijing.aliyuncs.com/test/myhand.png"
    )#https://image-bed-datawhale.oss-cn-beijing.aliyuncs.com/test/myhand.png


model_dir = "/path/to/bge-small-zh-v1.5"
instruction = "为这个句子生成表示以用于检索相关文章"
knowledge_base = KnowledgeBase(model_dir, instruction)
knowledge_base.load_knowledge("./RAG/data/knowledge_embeddings_with_indices.pkl")

feature = None
# feature = 你要分析的哪一条手相线的名字。
# 	•	一般取值范围：感情线 / 生命线 / 智慧线 / 婚姻线 / 事业线。
RAG_res = rag_matching(MMML_res, knowledge_base, feature, topk=1)#拿到大模型对掌纹的描述，然后去知识库里面进行匹配内容；
print('rag_res:',RAG_res)
    #
    # 6) 组织 prompt
text = '分析一下自己的手势'
#mmml_text = MMML_res.get(feature, "未找到对应特征")

if feature and feature in MMML_res:
    mmml_text = MMML_res[feature]
else:
    # 拼接所有的手相分析结果
    mmml_text = "\n".join([f"{k}: {v}" for k, v in MMML_res.items()])

content = PROMPT.format(
                MMML_res=mmml_text, RAG_res=RAG_res, user_input=text
            )
    #
    # # 7) 构造 history 并非流式回复

history = [{"role": "user", "content": content}]
tokenizer = None
model = "qwen-plus"
answer = generate_response(tokenizer, model, history)

print(answer)

'''
下面这个就是input_data
{
  "生命线": "生命线从拇指根部开始，环绕大鱼际区域，走向较为圆润，长度适中，显示生命力较强，身体健康状况良好，但需注意避免过度劳累。",
  "智慧线": "智慧线从拇指与食指之间向小指方向延伸，线条明显，略有分叉，显示出思维活跃、逻辑性强，具有较强的学习能力和分析能力，但有时可能过于追求完美。",
  "感情线": "感情线较为清晰，从拇指根部延伸至小指下方，线条平直且较深，表明情感表达较为稳定，内心情感丰富但不轻易外露，可能在感情中较为理性。",
  "婚姻线": "婚姻线位于小指下方，有两条较浅的横线，其中一条较明显，另一条较模糊，暗示感情经历可能较为复杂，或有过短暂的感情关系，但最终可能会有稳定的情感归宿。",
  "事业线": "事业线从手掌底部向上延伸，贯穿掌心，线条清晰且略呈波浪状，说明事业心强，有明确的目标和规划，工作上容易获得成就，但过程中可能经历起伏。"
}

feature；gusture

'''


