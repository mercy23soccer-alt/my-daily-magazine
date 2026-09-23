import os
import requests
from datetime import datetime
from google import genai
from google.genai import types

# 1. 天気の取得
weather_res = requests.get(
    "https://api.open-meteo.com/v1/forecast?latitude=35.68&longitude=139.76&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m&daily=sunset&timezone=Asia%2FTokyo"
).json()

current = weather_res["current"]
daily = weather_res["daily"]
today = datetime.now().strftime("%Y-%m-%d")
current_temp = current['temperature_2m']
sunset = daily['sunset'][0].split('T')[1]

# 2. AIへの指示
SYSTEM_INSTRUCTION = """
あなたは雑誌『POPEYE』のような軽妙で知的な語り口を持つ日刊マガジン『THE DAILY EXTRACT』の専任エディターです。
読者は「化学のプロセス開発に関心があり、バイクの鼓動を愛し、いい音とサウナが好きなシティボーイ」です。
安易な美辞麗句は避け、道具愛に溢れた文体（「〜なんだ」「〜してみてほしい」「ぼくらの」）で書いてください。

以下の4セクションを必ず含めてください：
1. **Lead Story: Discovery & Process**: JACS, Angewandte Chemie, Organic Letters, OPRDの中から1つの反応を取り上げ、現場視点で解説する。必ず枠組みを使ったアスキーアート風の【反応式（SCHEME）】を掲載すること。
2. **Soundtrack of the Dusk**: 本日の気温・日没に合わせたネオソウル/オルタナティブR&Bの楽曲3選とライナーノーツ。
3. **Escape: Route & Steam**: 今日の気候に合わせたバイク走行の描写と、その先のサウナ（熱環境、水風呂、外気浴）のショートエッセイ。
4. **Editor's Colophon**: 街や実験器具、本日の気圧についての1行コラム。
"""

user_prompt = f"""
本日の環境データ:
- 日付: {today}
- 気温: {current_temp}℃ / 湿度: {current['relative_humidity_2m']}% / 気圧: {current['surface_pressure']} hPa
- 風速: {current['wind_speed_10m']} km/h / 日没: {sunset}

本日の最新号を執筆してください。前置きは書かず、Markdown本文のみを出力してください。
"""

# 3. Gemini API呼び出し
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=user_prompt,
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.7,
    ),
)

# 4. 保存
os.makedirs("src/content/posts", exist_ok=True)
frontmatter = f"""---
title: "Issue - {today}"
date: "{today}"
temp: "{current_temp}°C"
sunset: "{sunset}"
wind: "{current['wind_speed_10m']} km/h"
---

"""

file_path = f"src/content/posts/{today}.md"
with open(file_path, "w", encoding="utf-8") as f:
    f.write(frontmatter + response.text)

print(f"Successfully generated: {file_path}")
