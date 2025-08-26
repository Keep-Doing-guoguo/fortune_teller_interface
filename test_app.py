#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/8/21 17:49
@source from: 
"""
import base64
import requests

url = "http://127.0.0.1:9000/v2"

# 读取并编码图片
with open("/Volumes/PSSD/未命名文件夹/fortune_teller-main/data_img/myhand.png", "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode("utf-8")

data = {
    "text": "请帮我分析一下手势",
    "image": img_base64,
    "feature": "婚姻线"
}

resp = requests.post(url, json=data)#

print('debug')
#这个脚本都可以进行测试，也可以测试fastapi的程序；也可以测试flask的程序；
# 两种模式区别
# 	•	base64 模式（你现在用的）
# 	•	前端自己把图片转成 base64，然后发 JSON。
# 	•	Swagger UI 只能输入字符串，看不到文件上传按钮。
# 	•	文件上传模式（用 UploadFile）
# 	•	前端/Swagger UI 直接上传文件，后端收到二进制流。
# 	•	Swagger UI 里就会显示 上传图片按钮。
#
# ⸻
#
# 👉 建议：
# 如果是测试/Swagger UI 方便，改成 UploadFile；
# 如果是生产接口（特别是前端调用），继续用 base64，因为跨平台、跨语言更通用。