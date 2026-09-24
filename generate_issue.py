import os
import sys
import requests
from datetime import datetime
from google import genai

# 1. APIキーのチェック（設定されていない場合は分かりやすくエラーを出す）
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("【エラー】GEMINI_API_KEY が見つかりません！Settings > Secrets に正しく登録されているか確認してください。")
    sys.exit(1)

# 2. 天気の取得（Open-Meteo）
weather_res = requests.get(
    "https://api.open-meteo.com/v1/forecast?latitude=35.68&longitude=139.76&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m&daily=sunset&timezone=Asia%2FTokyo"
).json()

current = weather_res.get("current", {})
daily = weather_res.get("daily", {})
today = datetime.now().strftime("%Y-%m-%d")
current_temp = current.get("temperature_2m", "20")
sunset = daily.get("sunset", ["18:00"])[0].split("T")[-1]

# 3. AIへの指示文
prompt = f"""
あなたは雑誌『POPEYE』のような軽妙で知的な語り口を持つ日刊Webマガジン『THE DAILY EXTRACT』の専任エディターです。
読者は「化学のプロセス開発に関心があり、バイクの鼓動を愛し、いい音とサウナが好きなシティボーイ」です。
安易な美辞麗句（「素晴らしい」など）は避け、道具愛と現場感に溢れた文体（「〜なんだ」「〜してみてほしい」「ぼくらの」）で書いてください。

本日の環境データ:
- 日付: {today}
- 気温: {current_temp}℃ / 湿度: {current.get('relative_humidity_2m', 50)}% / 風速: {current.get('wind_speed_10m', 3)} km/h / 日没: {sunset}

以下の4セクション（Markdown形式）で本日の記事を執筆してください：
1. **Lead Story: Discovery & Process**: JACS, Angewandte Chemie, Organic Letters, OPRDの中から1つの反応を取り上げ、スケールアップの現場視点で解説する。必ず枠組みを使ったアスキーアート風の【反応式（SCHEME）】を掲載すること。
2. **Soundtrack of the Dusk**: 本日の気温・日没に合わせたネオソウル/オルタナティブR&Bの楽曲3選とライナーノーツ。
3. **Escape: Route & Steam**: 今日の気候に合わせたバイク走行の描写と、その先のサウナ（熱環境、水風呂、外気浴）のショートエッセイ。
4. **Editor's Colophon**: 街や実験器具、本日の気圧についての1行コラム。

前置きや挨拶は一切書かず、記事のMarkdown本文のみを出力してください。
"""

# 4. Gemini APIの呼び出し
client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
)

# 5. 記事をMarkdownとして保存
os.makedirs("src/content/posts", exist_ok=True)
frontmatter = f"""---
title: "Issue - {today}"
date: "{today}"
temp: "{current_temp}°C"
sunset: "{sunset}"
wind: "{current.get('wind_speed_10m', '3')} km/h"
---

"""

file_path = f"src/content/posts/{today}.md"
with open(file_path, "w", encoding="utf-8") as f:
    f.write(frontmatter + response.text)

print(f"Successfully generated: {file_path}")
