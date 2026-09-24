import os
import sys
import io
import time
import requests
from datetime import datetime
from PIL import Image
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found.")
    sys.exit(1)

client = genai.Client(api_key=api_key)
today = datetime.now().strftime("%Y-%m-%d")

# 1. 天気の取得
weather_res = requests.get(
    "https://api.open-meteo.com/v1/forecast?latitude=35.68&longitude=139.76&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m&daily=sunset&timezone=Asia%2FTokyo"
).json()
current = weather_res.get("current", {})
daily = weather_res.get("daily", {})
current_temp = current.get("temperature_2m", "22")
sunset = daily.get("sunset", ["18:00"])[0].split("T")[-1]

# 2. 記事執筆用プロンプト（GB350 / 詳細サウナ / 論文リンク）
SYSTEM_INSTRUCTION = """
あなたは雑誌『POPEYE』のスタイルを極めた日刊Webマガジン『THE DAILY EXTRACT』の編集長です。
読者は「化学のプロセス開発者であり、Honda GB350を相棒にし、サウナの熱環境にうるさく、グッドミュージックを愛するシティボーイ」です。

【執筆ルール】
1. **Lead Story: Discovery & Process**
   - JACS, Angewandte Chemie, Organic Letters, OPRD から1つのトピックを厳選。
   - 【必須】論文タイトル、著者、ジャーナル名、DOIリンク（例: [DOI: 10.1021/acs.oprd.xxxx](https://doi.org/10.1021/acs.oprd.xxxx)）を明記。
   - 【必須】枠線付きのテキストアートによる「反応式（SCHEME）」を必ず掲載。
   - ラボスケール（フラスコ）とパイロットプラント（キログラム仕込み）のギャップ、除熱・スラリー・溶媒留去の泥臭い課題をPOPEYE風の軽妙な語り口で解説。

2. **Soundtrack of the Dusk**
   - 今日の気温・風速・日没に合わせたオルタナティブR&B／ネオソウルのトラック3選。

3. **Escape: Route & Steam（Honda GB350 × サウナ）**
   - あなたの愛車は「Honda GB350」。348cc空冷単気筒のトコトコとした小気味よい鼓動感、低回転のトルク、アスファルトを蹴る感触を生き生きと描写。
   - 目的地の実在する（または具体的で魅力的な）サウナ施設をピックアップ。サウナ室の温度・熱源（薪・対流・ボナ）、オートロウリュの間隔、水風呂の温度・深さ・水質（地下水・井戸水）、外気浴の風通しやインフィニティチェアの有無まで、マニアが納得する解像度で描写する。

4. **Editor's Note**
   - 街や道具のディテールに関する小粋な1行コラム。
"""

user_prompt = f"""
本日の環境データ:
- 日付: {today}
- 気温: {current_temp}℃ / 湿度: {current.get('relative_humidity_2m', 55)}% / 風速: {current.get('wind_speed_10m', 3)} km/h / 日没: {sunset}

本日のIssue記事を執筆してください。Markdown形式のみを出力してください。
"""

# 混雑（503エラー）対策：最大3回自動でリトライする
response = None
for attempt in range(3):
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_prompt,
            config=dict(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7),
        )
        break
    except Exception as e:
        print(f"AI混雑のため再試行します (回数: {attempt + 1}/3)... {e}")
        time.sleep(5)

if not response:
    print("AIの応答を取得できませんでした。")
    sys.exit(1)

# 3. 本日のグラフィック（イラスト）をAIで自動生成
os.makedirs("public/covers", exist_ok=True)
cover_rel_path = f"/covers/{today}.jpg"
cover_save_path = f"public{cover_rel_path}"

image_prompt = (
    f"A stylish, modern retro editorial graphic illustration in Japanese city pop magazine style like POPEYE. "
    f"A rider enjoying a Honda GB350 classic motorcycle on a quiet scenic Japanese road under an evening dusk sky with gentle golden light. "
    f"Minimalist, flat clean shapes, high contrast vintage color palette, cozy aesthetic."
)

try:
    img_result = client.models.generate_images(
        model="imagen-3.0-generate-002",
        prompt=image_prompt,
        config=dict(number_of_images=1, aspect_ratio="16:9")
    )
    for gen_img in img_result.generated_images:
        img = Image.open(io.BytesIO(gen_img.image.image_bytes))
        img.save(cover_save_path, "JPEG")
        print(f"Generated daily graphic: {cover_save_path}")
except Exception as e:
    print(f"Image generation skipped: {e}")
    cover_rel_path = ""

# 4. Markdownとして保存
os.makedirs("src/content/posts", exist_ok=True)
frontmatter = f"""---
title: "Issue - {today}"
date: "{today}"
temp: "{current_temp}°C"
sunset: "{sunset}"
wind: "{current.get('wind_speed_10m', '3')} km/h"
cover: "{cover_rel_path}"
bike: "Honda GB350"
---

"""

file_path = f"src/content/posts/{today}.md"
with open(file_path, "w", encoding="utf-8") as f:
    f.write(frontmatter + response.text)

print(f"Successfully published issue: {file_path}")
