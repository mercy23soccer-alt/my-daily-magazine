import os
import sys
import io
import time
import requests
from datetime import datetime
from urllib.parse import quote
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
current_temp = str(current.get("temperature_2m", "22"))
sunset = daily.get("sunset", ["18:00"])[0].split("T")[-1]

# 2. 記事執筆用プロンプト
SYSTEM_INSTRUCTION = """
あなたは雑誌『POPEYE』の精神を宿した日刊Webマガジン『THE DAILY EXTRACT』の編集長です。
読者は「化学のプロセス開発者であり、Honda GB350に乗り、ゴールドジムで鍛え、ケンドリック・ラマーの文化と英語を学び、株式投資にも明るく、サウナ・コーヒー、そして家族との時間を大切にするシティボーイ」です。

以下の各セクション構成を厳密に守り、見出しは指定のHTMLアンカーID付き（例: <h2 id="...">）で記述してください。

---
<h2 id="lead-story">1. Lead Story: Discovery & Process</h2>
- JACS, Angewandte Chemie, Organic Letters, OPRD から1つのトピックを厳選。
- 【必須】論文タイトル、著者、ジャーナル名、DOIリンク（例: [DOI: 10.1021/acs.oprd.xxxx](https://doi.org/10.1021/acs.oprd.xxxx)）を明記。
- 【必須】```text による枠組みを使った等幅アスキーアート【反応式（SCHEME）】を掲載（文字ズレしないよう整えること）。
- キログラム仕込みの除熱、スラリー移送、晶析、溶媒回収のリアルを現場視点で解説。

<h2 id="news">2. Today's Curated News: 5 Picks</h2>
読者の関心領域から本日のニュースを5つ厳選し、鋭い1行コメントとリンクを添える：
1. **化学・製薬・プロセス開発**: 業界動向 ([ニュース検索](https://news.google.com/search?q=化学+プロセス開発+製薬))
2. **Honda & モビリティ**: バイク・モビリティ ([ニュース検索](https://news.google.com/search?q=Honda+バイク+GB350))
3. **ウェルネス & サウナ**: サウナ・温浴トレンド ([ニュース検索](https://news.google.com/search?q=サウナ+トレンド))
4. **USヒップホップ & ストリート**: 音楽カルチャー ([ニュース検索](https://news.google.com/search?q=Kendrick+Lamar+hiphop))
5. **フィジカル & トレーニング**: 筋トレ・栄養学 ([ニュース検索](https://news.google.com/search?q=筋トレ+フィットネス+栄養学))

<h2 id="market">3. Market Catalyst: 株式投資と注目テーマ</h2>
- **本日の注目テーマ（1つ）**: 半導体材料、フロー合成、バイオものづくり、次世代バッテリーなど。
- **本日の厳選銘柄（1社）**: 「ニッチトップの化学・素材メーカー」「参入障壁の高い中小型成長株」を1社選定。
  - 企業名、証券コード
  - ビジネスモデルと参入障壁（Moat）
  - 今後のカタリスト（業績変化、需要拡大の根拠）
  - [📈 Yahoo!ファイナンスでチャートを見る](https://finance.yahoo.co.jp/search/?query=銘柄名)
  - ※投資の最終判断は自己責任で行ってください。

<h2 id="music">4. The Cipher: West Coast, Kendrick & Culture</h2>
- ケンドリック・ラマー、TDE/pgLang、コンプトンやUSヒップホップの歴史・社会背景を深掘り。
- **本日のトラック**: 楽曲名、プロデューサー、背景解説。
- **【必須】リンク**: 
  - [🎵 YouTube Musicで聴く](https://music.youtube.com/search?q=曲名+アーティスト名)
  - [▶ YouTubeでMV・動画を見る](https://www.youtube.com/results?search_query=曲名+アーティスト名)
- **Lyric Breakdown（英語を学ぶ）**: パンチラインを1節引用し、スラングの意味、文化的ダブルミーニング、日常英会話への応用を解説。

<h2 id="book">5. Book Archive: Life & Perspective</h2>
- 思考や人生の視座を広げる骨太な1冊をセレクト。
- なぜ今読むべきなのか、そして「この本を読むと人生の景色や思考がどう変わるのか」を熱く語る。
- **【必須】リンク**:
  - [📚 Amazonで見る](https://www.amazon.co.jp/s?k=書籍名)
  - [▶ YouTubeで解説を見る](https://www.youtube.com/results?search_query=書籍名+解説)

<h2 id="curiosity">6. Curiosity Expedition: Uncharted Waters</h2>
- 毎月新しい体験に挑むためのアイデア。読者が普段触れていない全く新しい世界（塊根植物・盆栽、レザーのビスポーク、現代建築の構造、発酵食品の科学、アンティーク時計など）の魅力と、初心者が足を踏み入れる第一歩を手引きする。

<h2 id="escape">7. Escape: Route, Iron & Steam</h2>
- 今日の天気に合わせ、愛車「Honda GB350」の単気筒の鼓動、ゴールドジムでの筋トレ、サウナ（サウナイキタイリンク付き）、そして家族と囲むハンドドリップコーヒーの団欒を描く。
- **【必須】リンク**: [🧖 サウナイキタイで施設を見る](https://sauna-ikitai.com/search?keyword=施設名)

<h2 id="colophon">8. Editor's Colophon</h2>
- 実験室の器具や街の風景、今夜の気圧についての1行コラム。
"""

img_tag_1 = f'<img src="/my-daily-magazine/images/{today}_scene1.jpg" alt="Today\'s Scene 1" />'
img_tag_2 = f'<img src="/my-daily-magazine/images/{today}_scene2.jpg" alt="Today\'s Scene 2" />'

user_prompt = f"""
本日の環境データ:
- 日付: {today}
- 気温: {current_temp}℃ / 湿度: {current.get('relative_humidity_2m', 50)}% / 風速: {current.get('wind_speed_10m', 3)} km/h / 日没: {sunset}

記事本文の適切な場所に、以下の2つのHTMLタグを必ず配置してください：
{img_tag_1}
{img_tag_2}

本日の最新号を執筆してください。Markdown形式のみを出力してください。
"""

# Gemini 呼び出し（混雑・レート制限対策リトライ）
model_name = "gemini-3.6-flash"
response = None

print(f"--- モデル {model_name} で執筆開始 ---")
for attempt in range(1, 6):
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=dict(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7),
        )
        if response and response.text:
            print("成功: 記事が書き上がりました！")
            break
    except Exception as e:
        err_str = str(e)
        print(f"⚠️ 試行 {attempt}/5 でエラー検知: {err_str}")
        if "503" in err_str:
            wait_time = attempt * 15
            print(f"Googleサーバー混雑中。{wait_time}秒待機して再試行します...")
            time.sleep(wait_time)
        elif "429" in err_str:
            wait_time = 35
            print(f"短時間アクセス制限（429）を検知。{wait_time}秒間クールダウンします...")
            time.sleep(wait_time)
        else:
            time.sleep(8)

if not response:
    print("すべての試行が制限またはエラーにより失敗しました。")
    sys.exit(1)

# 3. リアルなスナップ写真を2枚生成
os.makedirs("public/images", exist_ok=True)
temp_val = float(current_temp) if current_temp.replace('.', '', 1).isdigit() else 20.0

if temp_val >= 18:
    prompt_1 = "Authentic lifestyle 35mm candid film photograph of a rider enjoying a classic Honda GB350 motorcycle along a scenic Tokyo coastal road at sunset, natural golden hour lighting, cinematic grain, POPEYE magazine aesthetic"
    prompt_2 = "Candid lifestyle 35mm film photograph of a relaxed young Japanese man peaceful inside an authentic wooden sauna room with gentle steam, warm moody light, documentary magazine style"
else:
    prompt_1 = "Authentic lifestyle 35mm film photograph of a focused fit man working out with heavy dumbbells in Gold's Gym surrounded by classic iron equipment, authentic gym lighting"
    prompt_2 = "Warm cozy 35mm film snapshot of a family living room table with pour-over black coffee in ceramic mugs, gentle morning sunlight streaming through windows, calm domestic happiness, POPEYE magazine style"

scenes = [
    (prompt_1, f"public/images/{today}_scene1.jpg"),
    (prompt_2, f"public/images/{today}_scene2.jpg")
]

def generate_and_save_photo(prompt_text, file_path):
    try:
        img_res = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=prompt_text,
            config=dict(number_of_images=1, aspect_ratio="16:9")
        )
        for gen_img in img_res.generated_images:
            img = Image.open(io.BytesIO(gen_img.image.image_bytes))
            img.save(file_path, "JPEG")
            print(f"Imagenで生成成功: {file_path}")
            return
    except Exception as e:
        print(f"Imagen制限検知。フォトエンジンへ切替: {e}")

    try:
        clean_prompt = quote(prompt_text)
        url = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){clean_prompt}?width=1200&height=675&nologo=true&seed={int(time.time())}"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(r.content)
            print(f"フォトエンジンで生成保存完了: {file_path}")
    except Exception as ex:
        print(f"画像保存エラー: {ex}")

for p_text, s_path in scenes:
    generate_and_save_photo(p_text, s_path)

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
