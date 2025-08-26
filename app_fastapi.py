# app_fastapi.py
# ------------------------------------------------------
# FastAPI skeleton for your palm-reading project
# /ping: health
# /v1:  base64 图片上传OSS -> 非流式返回
# /v2:  base64 图片上传OSS -> 流式返回
# /v3:  base64 图片本地上传，不经过OSS -> 流式返回
# 自动文档: /docs, /redoc
# ------------------------------------------------------

import io
from typing import Optional, Dict, Any, Generator, List

from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from PIL import Image

from fastapi import UploadFile, File, Form
import pathlib
import base64
import uvicorn
# =============== 这里导入你自己的模块（填充业务逻辑）================
from MLLM.pic2url import pic2url
from MLLM.MMML_MY import MMML
from MLLM.preprocess import preprocess_hand_image
from RAG.utils import rag_matching
from RAG.Knowledge import KnowledgeBase
from LLM.api_model_qwen_no_stream import generate_response
from LLM.api_model_qwen import generate_stream_response
# ==================================================================

# -------------------- 配置区：提示词模板 ---------------------------
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

# -------------------- Pydantic 输入/输出模型 -----------------------
class V1Request(BaseModel):
    text: str = Field(..., description="用户问题")
    image: str = Field(..., description="base64 编码图片（不含 data:image/jpeg;base64, 前缀）")
    feature: str = Field(..., description="目标手相特征键（如“感情线/生命线/…”）")

class V2Request(V1Request):
    """与V1相同，只是返回改为流式"""
    pass

class V3Request(BaseModel):
    text: str = Field(..., description="作为 MMML_res 参与分析或直接问题")
    feature: str = Field(..., description="目标特征")

class CommonResponse(BaseModel):
    status: int
    statusText: str
    body: Optional[str] = None


# ------------------------ FastAPI 初始化 ---------------------------
app = FastAPI(
    title="Palm Reader API",
    version="1.0.0",
    description="基于 FastAPI 的手相问答后端骨架（待你填充业务逻辑）"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # 如需更安全可改为你的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------- 应用级共享状态（依赖注入） -------------------
@app.on_event("startup")
async def on_startup():
    """
    启动时初始化所需资源（模型、知识库、tokenizer等）
    """
    # TODO: 替换为你的初始化逻辑
    model_dir = "/path/to/bge-small-zh-v1.5"
    instruction = "为这个句子生成表示以用于检索相关文章"
    knowledge_base = KnowledgeBase(model_dir, instruction)
    knowledge_base.load_knowledge("./RAG/data/knowledge_embeddings_with_indices.pkl")
    tokenizer, model = None, "qwen-plus"
    # 保存到 app.state 里
    app.state.knowledge_base = knowledge_base
    app.state.tokenizer = tokenizer
    app.state.model = model

# --------------------------- 工具函数 ------------------------------
def decode_base64_to_image(b64_str: str, save_path: str) -> str:
    """将 base64 字符串转为图片并保存，返回路径"""
    try:
        img = Image.open(io.BytesIO(base64.b64decode(b64_str)))
        img.save(save_path)
        return save_path
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image: {e}")

def build_prompt(mmml_res: str, rag_res: str, user_text: str) -> str:
    return PROMPT.format(MMML_res=mmml_res, RAG_res=rag_res, user_input=user_text)

# ---------------------------- 路由 -------------------------------
@app.get("/ping", response_model=Dict[str, str], summary="健康检查")
async def ping():
    return {"msg": "pong"}

@app.post("/v1", response_model=CommonResponse, summary="图片(base64) + 文本：非流式返回")
async def v1(req: V1Request):
    """
    - image: base64（纯体，不要带 data:image/jpeg;base64, 前缀）
    - feature: 用于从 MMML 结果中取对应条目
    """
    # 1) base64 -> 本地图片
    image_path = "./uploaded_image.jpg"
    decode_base64_to_image(req.image, image_path)

    # 2) （可选）预处理
    preprocess_hand_image(image_path)

    # 3) 上传图到云/图床，得到 URL
    cloud_url = pic2url(image_path)
    print('cloud_url:',cloud_url)


    # 4) 多模态分析（MMML）
    mmml_res = MMML(cloud_url)     # 应返回一个 dict
    print('mmml_res:',mmml_res)
    # 5) RAG 检索
    rag_res = rag_matching(mmml_res, app.state.knowledge_base, req.feature, topk=1)
    print('rag_res:',rag_res)
    #
    # 6) 组织 prompt
    #mmml_text = mmml_res.get(req.feature, "未找到对应特征")
    if req.feature and req.feature in mmml_res:
        mmml_text = mmml_res[req.feature]
    else:
        # 拼接所有的手相分析结果
        mmml_text = "\n".join([f"{k}: {v}" for k, v in mmml_res.items()])

    prompt = build_prompt(mmml_text, rag_res, req.text)
    #
    # # 7) 构造 history 并非流式回复
    history = [{"role": "user", "content": prompt}]
    answer = generate_response(app.state.tokenizer, app.state.model, history)

    return CommonResponse(status=200, statusText="OK", body=answer)


@app.post("/v2", summary="图片(base64) + 文本：流式返回")
async def v2(req: V2Request):
    """
    - image: base64（纯体，不要带 data:image/jpeg;base64, 前缀）
    - feature: 用于从 MMML 结果中取对应条目
    - 返回方式：StreamingResponse，逐段返回文本
    """
    # 1) base64 -> 本地图片
    image_path = "./uploaded_image.jpg"
    decode_base64_to_image(req.image, image_path)

    # 2) （可选）预处理
    preprocess_hand_image(image_path)

    # 3) 上传图到云/图床
    cloud_url = pic2url(image_path)

    # 4) 多模态分析
    mmml_res = MMML(cloud_url)

    # 5) RAG 检索
    rag_res = rag_matching(mmml_res, app.state.knowledge_base, req.feature, topk=1)

    # 6) prompt 组织
    if req.feature and req.feature in mmml_res:
        mmml_text = mmml_res[req.feature]
    else:
        mmml_text = "\n".join([f"{k}: {v}" for k, v in mmml_res.items()])
    prompt = build_prompt(mmml_text, rag_res, req.text)

    # 7) 构造 history
    history = [{"role": "user", "content": prompt}]

    # 8) 使用 StreamingResponse 包装生成器
    def token_stream() -> Generator[str, None, None]:
        for chunk in generate_stream_response(app.state.tokenizer, app.state.model, history):
            yield chunk

    return StreamingResponse(token_stream(), media_type="text/plain")




@app.post("/v3", response_model=CommonResponse, summary="表单上传图片：非流式，多模态+RAG（非流式回答）")
async def v3(
    file: UploadFile = File(..., description="表单上传的图片文件（jpg/png/webp 等）"),
    question: str = Form("这张手相图怎么看？", description="给大模型的用户问题"),
    feature: str | None = Form(None, description="手相特征键；留空则汇总全部特征")
):
    """
    """
    # 1) 保存表单图片
    save_dir = pathlib.Path("./uploads")
    save_dir.mkdir(parents=True, exist_ok=True)
    filename = file.filename or "uploaded_image.jpg"
    image_path = save_dir / filename
    image_path.write_bytes(await file.read())
    abs_path = str(image_path.resolve())

    print(abs_path)
    # 2) 预处理（如需关闭，注释下一行）
    #preprocess_hand_image(abs_path)

    # 3)
    from MLLM.bendi_base64_upload import bendi_upload

    # 4) 多模态分析（返回字典）
    mmml_res= bendi_upload(abs_path)
    print('mmml_res:',mmml_res)
    rag_res = rag_matching(mmml_res, app.state.knowledge_base, topk=1)

    # 5) RAG 检索：如果给了 feature，就针对该特征；否则把所有特征拼起来作为查询
    if feature and feature in mmml_res:
        mmml_text = mmml_res[feature]
    else:
        # 汇总所有特征文本
        mmml_text = "\n".join([f"{k}: {v}" for k, v in mmml_res.items()])

    # 6) 组装 prompt 并非流式生成
    prompt = build_prompt(mmml_text, rag_res, question)
    history = [{"role": "user", "content": prompt}]
    answer = generate_response(app.state.tokenizer, app.state.model, history)

    return CommonResponse(status=200, statusText="OK", body=answer)


if __name__ == "__main__":
    # host=0.0.0.0: 对外可访问
    # port=9000: 端口号
    # reload=True: 开发模式自动热重载
    uvicorn.run("app_fastapi:app", host="0.0.0.0", port=9000, reload=True)
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