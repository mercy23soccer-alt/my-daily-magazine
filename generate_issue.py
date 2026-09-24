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

# 1. 天気の取得（Open-Meteo）
weather_res = requests.get(
    "https://api.open-meteo.com/v1/forecast?latitude=35.68&longitude=139.76&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m&daily=sunset&timezone=Asia%2FTokyo"
).json()
current = weather_res.get("current", {})
daily = weather_res.get("daily", {})
current_temp = str(current.get("temperature_2m", "22"))
sunset = daily.get("sunset", ["18:00"])[0].split("T")[-1]

# 2. 記事執筆用プロンプト
SYSTEM_INSTRUCTION = """
あなたは雑誌『POPEYE』の精神を宿した日刊Webマガジン『THE DAILY EXTRACT』の編集長です。
読者は「化学のプロセス開発者であり、Honda GB350に乗り、ゴールドジムで鍛え、ケンドリック・ラマーの文化と英語を学び、サウナ・コーヒー、そして家族との時間を大切にするシティボーイ」です。

以下の構成（Markdown形式）で執筆してください。指定された2枚の写真タグを、文脈に合う自然な位置（セクション間など）に必ず配置してください。

---
### 1. Lead Story: Discovery & Process
- JACS, Angewandte Chemie, Organic Letters, OPRD から1つのトピックを厳選。
- 【必須】論文タイトル、著者、ジャーナル名、DOIリンク（例: [DOI: 10.1021/acs.oprd.xxxx](https://doi.org/10.1021/acs.oprd.xxxx)）を明記。
- 【必須】枠線付きテキストアートによる【反応式（SCHEME）】を掲載。
- ラボスケールとキログラム仕込みのギャップ、除熱・スラリー・溶媒回収のリアルを現場視点で解説。

### 2. The Cipher: West Coast, Kendrick & Culture
- ケンドリック・ラマー（Kendrick Lamar）、TDE/pgLang、コンプトンやUSヒップホップの歴史・社会背景を深掘り。
- **本日のトラック**: 楽曲名、プロデューサー、背景解説。
- **【必須】リンク**: [▶ YouTubeで楽曲を聴く / MVを見る](https://www.youtube.com/results?search_query=曲名+アーティスト名)
- **Lyric Breakdown（英語を学ぶ）**: パンチラインを引用し、スラングの意味、文化的ダブルミーニング、日常英会話への応用を解説。

### 3. Book Archive: Life & Perspective
- 人生の視座を広げる骨太な1冊をセレクト。
- なぜ今読むべきなのか、そして「この本を読むと人生の景色や思考がどう変わるのか」を熱く語る。
- **【必須】リンク**:
  - [📚 Amazonで見る](https://www.amazon.co.jp/s?k=書籍名)
  - [▶ YouTubeで解説・関連動画を見る](https://www.youtube.com/results?search_query=書籍名+解説)

### 4. Curiosity Expedition: Uncharted Waters（未知への越境コラム）
- 毎月新しい体験に挑むためのアイデア。読者が普段触れていない全く新しい世界（例：塊根植物・盆栽、レザーのビスポーク、現代建築の構造、発酵食品の科学、アンティーク時計など）の魅力と、初心者が足を踏み入れる第一歩を手引きする。

### 5. Escape: Route, Iron & Steam（日常と至福のルーティン）
- 今日の天気に合わせ、以下から最適なトピックを描写する：
  1. 愛車「Honda GB350」の単気筒ロングストロークの鼓動とツーリング
  2. 実在するサウナ施設の詳細（温度/熱源、水風呂水質/深さ、外気浴）
     - **【必須】リンク**: [🧖 サウナイキタイで施設を見る](https://sauna-ikitai.com/search?keyword=施設名)
  3. ゴールドジムでのストイックな筋トレ（フォームへの集中、鉄の匂い、心身の充実）
  4. 自宅でハンドドリップコーヒーを淹れ、家族とリビングで過ごすあたたかな団欒
- サウナ後の極上のコーヒーや、充実した1日の終わりの余韻で結ぶ。

### 6. Editor's Colophon
- 実験室の器具や街の空気感、今夜の気圧についての1行コラム。
"""

user_prompt = f"""
本日の環境データ:
- 日付: {today}
- 気温: {current_temp}℃ / 湿度: {current.get('relative_humidity_2m', 50)}% / 風速: {current.get('wind_speed_10m', 3)} km/h / 日没: {sunset}

記事本文の適切な場所に、以下の2つの画像タグを必ず埋め込んでください：
![Today's Scene 1](/my-daily-magazine/images/{today}_scene1.jpg)
![Today's Scene 2](/my-daily-magazine/images/{today}_scene2.jpg)

本日の最新号を執筆してください。Markdown形式のみを出力してください。
"""

# Gemini 混雑対策リトライ
target_models = ["gemini-3.6-flash", "gemini-3.6-pro"]
response = None

for model_name in target_models:
    print(f"--- モデル {model_name} で執筆開始 ---")
    for attempt in range(1, 5):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=dict(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7),
            )
            if response and response.text:
                print(f"成功: {model_name} で記事が完成しました！")
                break
        except Exception as e:
            err_str = str(e)
            print(f"試行 {attempt}/4 失敗 ({model_name}): {err_str}")
            if "503" in err_str:
                wait_time = attempt * 10
                print(f"サーバー混雑中。{wait_time}秒待機して再試行します...")
                time.sleep(wait_time)
            elif "404" in err_str:
                break
            else:
                time.sleep(5)
    if response and response.text:
        break

if not response:
    print("AIの応答を取得できませんでした。")
    sys.exit(1)

# 3. 本日のスナップ写真を2枚自動生成
os.makedirs("public/images", exist_ok=True)
temp_val = float(current_temp) if current_temp.replace('.', '', 1).isdigit() else 20.0

# 気温・天候に合わせてシーンを切り替え
if temp_val >= 18:
    prompt_1 = "Authentic lifestyle 35mm candid film photograph of a rider enjoying a classic Honda GB350 motorcycle along a scenic coastal road at sunset, natural golden hour lighting, cinematic grain, POPEYE magazine aesthetic."
    prompt_2 = "Candid lifestyle 35mm film photograph of a relaxed young man peaceful and euphoric inside an authentic wooden sauna room with gentle steam, warm moody light, documentary magazine style."
else:
    prompt_1 = "Authentic lifestyle 35mm film photograph of a focused fit man working out with heavy dumbbells in Gold's Gym surrounded by classic iron equipment, moody authentic gym lighting."
    prompt_2 = "Warm cozy 35mm film snapshot of a family living room table with pour-over black coffee in ceramic mugs, morning sunlight streaming through windows, calm domestic happiness, POPEYE magazine style."

scenes = [
    (prompt_1, f"public/images/{today}_scene1.jpg"),
    (prompt_2, f"public/images/{today}_scene2.jpg")
]

for idx, (img_prompt, save_path) in enumerate(scenes, 1):
    try:
        img_res = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=img_prompt,
            config=dict(number_of_images=1, aspect_ratio="16:9")
        )
        for gen_img in img_res.generated_images:
            img = Image.open(io.BytesIO(gen_img.image.image_bytes))
            img.save(save_path, "JPEG")
            print(f"Generated Photo {idx}: {save_path}")
    except Exception as e:
        print(f"Photo {idx} skipped: {e}")

# 4. Markdownとして保存
os.makedirs("src/content/posts", exist_ok=True)
frontmatter = f"""---
title: "Issue - {today}"
date: "{today}"
temp: "{current_temp}°C"
sunset: "{sunset}"
wind: "{current.get('wind_speed_10m', '3')} km/h"
bike: "Honda GB350"
---

"""

file_path = f"src/content/posts/{today}.md"
with open(file_path, "w", encoding="utf-8") as f:
    f.write(frontmatter + response.text)

print(f"Successfully published issue: {file_path}")
