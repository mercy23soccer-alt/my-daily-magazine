import os
import sys
import io
import time
import glob
import re
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
from PIL import Image
from google import genai

# 日本時間（JST = UTC+9）を明示的に取得
JST = timezone(timedelta(hours=9))
now_jst = datetime.now(JST)
today = now_jst.strftime("%Y-%m-%d")

api_key = os.environ.get("GEMINI_API_KEY")
client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Gemini初期化スキップ: {e}")

# 1. 天気の取得
weather_res = requests.get(
    "https://api.open-meteo.com/v1/forecast?latitude=35.68&longitude=139.76&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m&daily=sunset&timezone=Asia%2FTokyo"
).json()
current = weather_res.get("current", {})
daily = weather_res.get("daily", {})
current_temp = str(current.get("temperature_2m", "22"))
sunset = daily.get("sunset", ["18:00"])[0].split("T")[-1]

# 2. 過去記事の重複防止スキャン
past_posts = sorted(glob.glob("src/content/posts/*.md"), reverse=True)
past_context = ""
if past_posts:
    try:
        with open(past_posts[0], "r", encoding="utf-8") as f:
            past_context = f"\n【重要：前回号のトピック（これらと重複禁止）】\n{f.read()[:2000]}\n"
    except Exception as e:
        print(f"過去記事スキップ: {e}")

# 写真タグ定義
img_tag_1 = f'<div class="magazine-photo-box"><img src="/my-daily-magazine/images/{today}_scene1.jpg" alt="Today\'s Scene 1" /><p class="photo-caption">SCENE 01 / TOKYO CITY LIFE</p></div>'
img_tag_2 = f'<div class="magazine-photo-box"><img src="/my-daily-magazine/images/{today}_scene2.jpg" alt="Today\'s Scene 2" /><p class="photo-caption">SCENE 02 / STEAM, ROAST & HOME</p></div>'

# 3. 執筆プロンプト
SYSTEM_INSTRUCTION = f"""
あなたは雑誌『POPEYE』『BRUTUS』の知性と美学を宿した日刊カルチャー誌『ZAZZY』の編集長です。
読者は「化学のプロセス開発者であり現在育休中の父親。Honda GB350に乗り、筋トレとお笑い深夜ラジオを愛し、認知的脱フュージョンと減算法で思考を調律するシティボーイ・小島雅史氏」です。
{past_context}

【執筆ルール】
- 本文冒頭に「TITLE:」や「DATE:」などのメタデータは絶対に書かないこと。
- 化学用語（除熱、触媒、スラリー、晶析等）を比喩として使うことは一切禁止。洗練された都会的エッセイ文章で綴ること。
- 箇条書きや要約ではなく、各セクション豊かな情緒と知性のある本格的な長文で書き込むこと。

見出し構成：
<h2 id="lead-story">01. Lead Story: Science & Discovery</h2>
OPRD, JACS等から注目のプロセス化学論文。DOIリンクと以下のフローチャートHTMLを出力：
<div class="flow-wrapper">
  <div class="flow-card"><span class="flow-step">STEP 1</span><div class="flow-title">工程名</div><div class="flow-body">条件・溶媒</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 2</span><div class="flow-title">工程名</div><div class="flow-body">制御ポイント</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 3</span><div class="flow-title">工程名</div><div class="flow-body">結晶・分離</div></div>
</div>

<h2 id="benjamin">02. Special Column: Daily Benjamin — 思考の調律と徳目の実践</h2>
1,200字以上の本格エッセイ：認知的観察（脱フュージョン）、徳目や自省録、HALT原則（睡眠・身体疲労の肯定、育休インフラ死守＝100点）、手放し減算法。

<h2 id="news">03. Curated News & Macro: 世界経済と暮らしのインパクト</h2>
日経・Abemaニュース・市況と、技術者・投資家・育休パパ視点での生活インパクト解説。
- [日本経済新聞 / ビジネス](https://www.nikkei.com/business/)
- [ABEMA TIMES](https://times.abema.tv/)

<h2 id="baby">04. Baby & Paternity: 赤ちゃん関連の重要情報（厳選3選）</h2>
睡眠科学、月齢発達、夫婦の疲労回復。
- [こども家庭庁 公式ポータル](https://www.cfa.go.jp/)
- [日本小児科学会](https://www.jpeds.or.jp/)

<h2 id="comedy">05. The Laugh & Radio: お笑い・深夜ラジオ解体新書</h2>
ロバート秋山、真空ジェシカ、マユリカ、ランジャタイ等の深夜ラジオやコント解体。
- [▶ YouTubeでお笑い・ラジオを見る](https://www.youtube.com/results?search_query=お笑い+ラジオ)

<h2 id="curiosity">06. Curiosity Expedition: 未知なる世界への招待</h2>
普段の関心を越える知的好奇心領域（現代アート、塊根植物、建築、時計構造等）。

<h2 id="evidence">07. Evidence Wellness: 最新論文が教える心身の整え方</h2>
PubMed論文に基づく睡眠・自律神経・脳腸相関。
- [🔬 PubMed最新研究](https://pubmed.ncbi.nlm.nih.gov/)

<h2 id="novel">08. Book Archive: 人生を揺らすオススメの小説</h2>
感性を刺激する骨太な名作小説の推薦。
- [📚 Amazonで見る](https://www.amazon.co.jp/)

<h2 id="music">09. The Cipher: West Coast, Kendrick & Culture</h2>
ケンドリック・ラマー等の楽曲解説と生きた英語リリック。

<h2 id="escape">10. Escape: Sauna Destination, Route & Home</h2>
実在の名サウナ施設、GB350の走行ルート、夜のハンドドリップ珈琲。
- [🧖 サウナイキタイ](https://sauna-ikitai.com/)

<h2 id="colophon">11. Editor's Colophon</h2>
気圧、空模様、今日を穏やかに過ごすための1行。
"""

user_prompt = f"""
本日の環境データ: 日付 {today} / 気温 {current_temp}℃ / 日没 {sunset}
本文の適切な位置に以下の画像タグを必ず配置してください：
{img_tag_1}
{img_tag_2}
POPEYEエディトリアル調の洗練された長文で執筆してください。Markdown形式で出力してください。
"""

response_text = None

if client:
    print("--- Gemini API で執筆中 ---")
    try:
        res = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_prompt,
            config=dict(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7),
        )
        if res and res.text and len(res.text) > 800:
            print("✅ 成功: Gemini APIで記事が完成しました！")
            response_text = res.text
    except Exception as e:
        print(f"⚠️ Gemini一時エラー: {str(e)[:100]}")

if not response_text:
    print("--- バックアップAIエンジンで執筆中 ---")
    try:
        combined_prompt = f"{SYSTEM_INSTRUCTION}\n\n---\n{user_prompt}"
        payload = {
            "messages": [{"role": "user", "content": combined_prompt}],
            "model": "openai",
            "seed": int(time.time())
        }
        r = requests.post("https://text.pollinations.ai/", json=payload, timeout=60)
        if r.status_code == 200 and len(r.text) > 800:
            print("✅ 成功: バックアップAIで記事が完成しました！")
            response_text = r.text
    except Exception as ex:
        print(f"バックアップAIエラー: {ex}")

if not response_text or len(response_text) < 500:
    print("❌ 記事生成に失敗しました。")
    sys.exit(1)

clean_text = re.sub(
    r'^(title:.*?\n|TITLE:.*?\n|date:.*?\n|DATE:.*?\n|temp:.*?\n|TEMP:.*?\n|sunset:.*?\n|SUNSET:.*?\n|wind:.*?\n|WIND:.*?\n|bike:.*?\n|BIKE:.*?\n)+',
    '',
    response_text.strip(),
    flags=re.MULTILINE | re.IGNORECASE
).strip()

if '<div class="flow-wrapper">' in clean_text:
    parts = clean_text.split('<div class="flow-wrapper">')
    reconstructed = parts[0]
    for p in parts[1:]:
        if '</div>' not in p or p.find('</div>') > 1000:
            p = p.replace('\n\n', '</div>\n\n', 1)
        reconstructed += '<div class="flow-wrapper">' + p
    clean_text = reconstructed

# 4. ライフスタイル写真2枚の生成
os.makedirs("public/images", exist_ok=True)
prompt_1 = "Authentic lifestyle 35mm candid film photograph of a rider enjoying a classic Honda GB350 motorcycle along a scenic Tokyo coastal road at sunset, natural golden hour lighting, cinematic grain, POPEYE magazine aesthetic"
prompt_2 = "Candid lifestyle 35mm film photograph of a relaxed young Japanese father drinking coffee peacefully with his baby and family in a bright living room, warm morning light, POPEYE magazine documentary style"

scenes = [
    (prompt_1, f"public/images/{today}_scene1.jpg"),
    (prompt_2, f"public/images/{today}_scene2.jpg")
]

def generate_and_save_photo(prompt_text, file_path):
    if client:
        try:
            img_res = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt_text,
                config=dict(number_of_images=1, aspect_ratio="16:9")
            )
            for gen_img in img_res.generated_images:
                img = Image.open(io.BytesIO(gen_img.image.image_bytes))
                img.save(file_path, "JPEG")
                return
        except Exception:
            pass

    try:
        clean_prompt = quote(prompt_text)
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1200&height=675&nologo=true&seed={int(time.time())}"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(r.content)
    except Exception as ex:
        print(f"画像保存エラー: {ex}")

for p_text, s_path in scenes:
    generate_and_save_photo(p_text, s_path)

# 5. 保存
os.makedirs("src/content/posts", exist_ok=True)
frontmatter_block = f"""---
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
    f.write(frontmatter_block + clean_text)

print(f"Successfully published issue: {file_path}")
