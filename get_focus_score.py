#!/usr/bin/env python3
"""
focus_score.py – Capture a desktop screenshot (local file or HTTP), send it to
OpenAI GPT-4o-mini Vision API, and print an integer focus score (0-100).
"""
import base64
import json
import requests
import openai

# ==== User-configurable constants ====
OPENAI_API_KEY = ""
USE_HTTP = False
LOCAL_IMAGE_PATH = r"C:\Users\Administrator\Desktop\QQ20250703-180057.png"
HTTP_IMAGE_URL = "http://localhost:8080/screen.jpg"
MODEL_ID = "o3"  

PROMPT = (
    "这是一个从用户电脑屏幕截取的图片，请你分析用户此时分心的概率。\n"
    "请注意：评判分心的概率可以通过用户是否在工作，例如是否在使用代码编辑器、视频编辑器、工作软件等等，或者通过分析用户电脑屏幕截图中是否是网页，网页是什么内容，如果正在看视频，是否与工作有关？例如如果是看教学视频，则判断正在工作或学习，如果是看娱乐或游戏视频，则判断正在休息或分心。\n"
    "请你直接输出一个集中注意力的分数，0分代表完全走神，100分代表非常集中，你可以在0-100之间自由选择一个分数来评判用户集中注意力的成绩。\n"
    "请以JSON格式返回，格式为: {\"focus_score\": 数字}"
)

openai.api_key = OPENAI_API_KEY

def load_image_bytes():
    if USE_HTTP:
        resp = requests.get(HTTP_IMAGE_URL, timeout=10)
        resp.raise_for_status()
        return resp.content
    with open(LOCAL_IMAGE_PATH, "rb") as f:
        return f.read()

def image_to_b64(data: bytes) -> str:
    return base64.b64encode(data).decode()

def get_focus_score(img_b64: str) -> int:
    try:
        response = openai.chat.completions.create(
            model=MODEL_ID,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "你是一名专注度分析助手，只返回 JSON。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {
                            "type": "image_url", 
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}"
                            }
                        },
                    ],
                },
            ],
        )
        
        payload = json.loads(response.choices[0].message.content)
        score = payload.get("focus_score", -1)

        if isinstance(score, (int, float)) and 0 <= score <= 100:
            return int(score)
        else:
            print(f"Warning：返回的分数不在有效范围内: {score}")
            return -1
            
    except Exception as e:
        print(f"Error：{type(e).__name__}: {str(e)}")
        return -1

def main():
    try:
        print("Loading IMG...")
        img_bytes = load_image_bytes()
        print(f"Images Size: {len(img_bytes)} bytes")
        
        img_b64 = image_to_b64(img_bytes)
        print("Sending Post to OpenAI API...")
        
        score = get_focus_score(img_b64)
        
        if score >= 0:
            print(f"Focus score: {score}")
        else:
            print("Don't get the Focus score")
            
    except Exception as e:
        print(f"Program Error：{type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    main()
