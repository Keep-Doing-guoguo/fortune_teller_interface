#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/8/26 11:05
@source from: 
"""
# server_fastapi.py
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import base64
import uvicorn

app = FastAPI(title="Upload Demo", version="1.0")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.post("/v1/upload")
async def upload(
    file: UploadFile = File(..., description="要上传的图片文件"),
    text: str = Form("", description="用户输入的文本，可选"),
    feature: str = Form("", description="可选的特征字段"),
):
    """
    接收 multipart/form-data：
    - file: 图片文件（input type=file）
    - text: 文本字段
    - feature: 业务标记（可选）
    """
    try:
        # 读取文件字节
        content = await file.read()
        # 如果你要传给多模态模型，可转为 base64
        img_b64 = base64.b64encode(content).decode("utf-8")
        data_url = f"data:image/{file.filename.split('.')[-1].lower()};base64,{img_b64}"

        # TODO: 你的业务逻辑：
        # 1) 送到多模态模型：用 data_url 或 img_b64 组装 messages 调接口
        # 2) 或先保存到本地/OSS：open("xxx.jpg","wb").write(content)
        # 3) 或做图像预处理

        return JSONResponse({
            "status": 200,
            "statusText": "OK",
            "filename": file.filename,
            "size": len(content),
            "text": text,
            "feature": feature,
            "image_base64_head": data_url[:60] + "..."  # 仅演示
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("server_fastapi:app", host="0.0.0.0", port=9000, reload=True)