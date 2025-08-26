#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/8/21 15:56
@source from: 
"""
import numpy as np
from config import key
def model(text):
    #
    import requests

    url = "https://api.siliconflow.cn/v1/embeddings"
    headers = {
        "Authorization": f"Bearer sk-{key}",  # 替换成你的 token
        "Content-Type": "application/json"
    }
    data = {
        "model": "BAAI/bge-large-zh-v1.5",
        "input": f"{text}"
    }

    response = requests.post(url, headers=headers, json=data)


    a = response.json()['data'][0]['embedding']
    return np.array(a)
    # print(response.status_code)
    # print(response.json())

#model('a')

