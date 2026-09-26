import os
import sys
import io
import time
import glob
import re
import requests
from datetime import datetime
from urllib.parse import quote
from PIL import Image
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Gemini Client 初期化エラー: {e}")

today = datetime.now().strftime("%Y-%m-%d")

# 1. 天気の取得
weather_res = requests.get(
    "https://api.open-meteo.com/v1/forecast?latitude=35.68&longitude=139.76&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m&daily=sunset&timezone=Asia%2FTokyo"
).json()
current = weather_res.get("current", {})
daily = weather_res.get("daily", {})
current_temp = str(current.get("temperature_2m", "22"))
sunset = daily.get("sunset", ["18:00"])[0].split("T")[-1]

# 2. 直近の過去記事を読み込み、トピック重複を防止
past_posts = sorted(glob.glob("src/content/posts/*.md"), reverse=True)
past_context = ""
if past_posts:
    try:
        with open(past_posts[0], "r", encoding="utf-8") as f:
            past_context = f"\n【重要：前回号のトピック（これらと内容・銘柄・選曲・書籍・小説・サウナ施設・紹介芸人・論文が絶対に重複しないこと）】\n{f.read()[:2000]}\n"
    except Exception as e:
        print(f"過去記事読み込みスキップ: {e}")

# 画像タグ定義
img_tag_1 = f'<div class="magazine-photo-box"><img src="/my-daily-magazine/images/{today}_scene1.jpg" alt="Today\'s Scene 1" /><p class="photo-caption">SCENE 01 / TOKYO CITY LIFE</p></div>'
img_tag_2 = f'<div class="magazine-photo-box"><img src="/my-daily-magazine/images/{today}_scene2.jpg" alt="Today\'s Scene 2" /><p class="photo-caption">SCENE 02 / STEAM, ROAST & HOME</p></div>'

# 3. 記事執筆用プロンプト
SYSTEM_INSTRUCTION = f"""
あなたは雑誌『POPEYE』の知性とシティボーイ精神を宿した日刊プライベートマガジン『ZAZZY』の編集長です。
読者は「化学のプロセス開発者（サイエンスの専門知）であり、現在【育児休業中】の父親。Honda GB350に乗り、ゴールドジムで鍛え、妻とともにロバート秋山、真空ジェシカ、マユリカ、ランジャタイ、ママタルト、ダイアンなどのお笑いラジオを愛し、ケンドリック・ラマーの文化と英語を学び、毎月新しい世界を探求するマルチ・ポテンシャライト。しかし緻密な完全主義や他者への過剰助言、タスク飽和による認知的過負荷、IBS（脳腸相関）に悩み、認知行動療法とエッセンシャル思考で自己の思考の癖を調律しているシティボーイ・小島雅史氏」です。
{past_context}

【執筆ルール】
- 本文の冒頭にタイトルやメタデータ（title:, date:, temp:, bike: など）は一切書かないでください。いきなり「01. Lead Story」の見出しから書き始めてください。
- 日常の思考やメンタル、ビジネス、カルチャーを語る際に、「除熱」「触媒」「スラリー」「晶析」「仕込み」「反応熱」といった理系・化学用語を比喩として使うことは一切禁止します。
- 洗練されたカルチャー誌の編集者のように、都会的で軽やか、情緒と知性が調和した美しい日本語で表現してください。

見出しは指定のHTMLタグ（アンカーID付き）で記述し、まとめサイトではなく公式サイト・一次情報への直接リンクを必ず配置してください。

---
<h2 id="lead-story">01. Lead Story: Science & Discovery</h2>
- JACS, Angewandte Chemie, Organic Letters, OPRD から注目の論文を1本厳選（過去号と被らないこと）。
- 【必須】論文タイトル、著者、ジャーナル名、DOIリンクを明記。
- 【重要：フローチャートは前後に必ず空行を入れ、完全に閉じること】
以下のHTMLコードをそのまま独立したブロックとして出力してください：

<div class="flow-wrapper">
  <div class="flow-card"><span class="flow-step">STEP 1</span><div class="flow-title">工程名</div><div class="flow-body">条件・溶媒・設定</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 2</span><div class="flow-title">工程名</div><div class="flow-body">結晶化・制御ポイント</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 3</span><div class="flow-title">工程名</div><div class="flow-body">分離・精製・収率</div></div>
</div>

- 現場の知恵をスマートなサイエンスエッセイとして解説。

<h2 id="benjamin">02. Special Column: Daily Benjamin — 思考の調律と徳目の実践</h2>
【最重要：毎朝の心を芯から整える1,200〜1,500文字の骨太な本格エッセイとしてしっかり執筆すること（化学比喩は禁止）】
1. **今朝の認知的観察（脱フュージョン）**: 白黒思考、個人化、助言過多への客観視。
2. **思想的アンカー**: フランクリンの13の徳目、マルクス・アウレリウスの自省録、ファインマンの遊び。
3. **育休期パパへの身体処方箋（HALT原則）**: 睡眠不足、呼吸、IBS、名もなき育児家事の肯定。
4. **本日の手放しアクション（減算法）**: あえてやらないNot-To-Do。

<h2 id="news">03. Curated News & Macro: 世界経済と暮らしのインパクト</h2>
1. **日経・経済/産業動向**: 素材・半導体の構造変化 ([日本経済新聞 / ビジネス](https://www.nikkei.com/business/))
2. **Abemaニュース / 社会トレンド**: 育休、働き方のリアル ([ABEMA TIMES](https://times.abema.tv/))
3. **世界マクロ市況の定点観測**: 米国市場、日経平均、ドル円、米長期金利。
4. **本日の注目企業（1社）**: 参入障壁の高いニッチトップ銘柄。
   - [📈 Yahoo!ファイナンスでチャートを見る](https://finance.yahoo.co.jp/search/?query=銘柄名)

<h2 id="baby">04. Baby & Paternity: 赤ちゃん関連の重要情報（厳選3選）</h2>
1. **乳幼児の睡眠科学・ネントレ** ([こども家庭庁](https://www.cfa.go.jp/))
2. **月齢に応じた発達とふれあい遊び** ([日本小児科学会](https://www.jpeds.or.jp/))
3. **夫婦の疲労回復と生活インフラ分担** ([厚生労働省 e-ヘルスネット](https://www.e-healthnet.mhlw.go.jp/))

<h2 id="comedy">05. The Laugh & Radio: お笑い・深夜ラジオ解体新書</h2>
- ロバート秋山、真空ジェシカ、マユリカ、ランジャタイ、ママタルト、ダイアンなどから日替わりで1組を深掘り。
- [▶ YouTubeでお笑い・ラジオを見る](https://www.youtube.com/results?search_query=芸人名+ラジオ+コント)
- [📻 お笑いナタリーで最新ニュースを見る](https://natalie.mu/owarai)

<h2 id="curiosity">06. Curiosity Expedition: 未知なる世界への招待</h2>
- 読者の普段の関心から外れた「未開拓の知的好奇心領域」を紹介（現代アート、塊根植物、時計機構、建築など）。

<h2 id="evidence">07. Evidence Wellness: 最新論文が教える心身の整え方</h2>
- PubMed等の論文に基づく、睡眠・自律神経・疲労回復の知性。
- [🔬 PubMed最新研究を検索](https://pubmed.ncbi.nlm.nih.gov/)

<h2 id="novel">08. Book Archive: 人生を揺らすオススメの小説</h2>
- 感性を刺激する骨太な傑作小説を1冊セレクト。
- [📚 Amazonで見る](https://www.amazon.co.jp/s?k=書籍名)
- [▶ YouTubeで解説を見る](https://www.youtube.com/results?search_query=書籍名+小説+解説)

<h2 id="music">09. The Cipher: West Coast, Kendrick & Culture</h2>
- ケンドリック・ラマー等の楽曲、リリック解説、生きた英語。
- [🎵 YouTube Musicで聴く](https://music.youtube.com/search?q=曲名+アーティスト名)

<h2 id="escape">10. Escape: Sauna Destination, Route & Home</h2>
- 実在する名銭湯・サウナ施設を1館。GB350で走るルートと自宅珈琲。
- [🧖 サウナイキタイで詳細を見る](https://sauna-ikitai.com/search?keyword=施設名)

<h2 id="colophon">11. Editor's Colophon</h2>
- 東京の空模様、気圧、今日を穏やかに過ごすための1行コラム。
"""

user_prompt = f"""
本日の環境データ:
- 日付: {today} / 気温: {current_temp}℃ / 日没: {sunset}

記事本文の適切な場所に、以下の2つのライフスタイル写真タグを必ず配置してください：
{img_tag_1}
{img_tag_2}

【重要】本文の先頭に「TITLE:」や「DATE:」などのメタデータは絶対に含めないでください。
化学系の比喩表現は使わず、POPEYEエディトリアル文体で執筆してください。
過去号との被りを避け、Markdown形式のみで出力してください。
"""

response_text = None

# 1. まず Gemini API で試行
if client:
    print("--- Gemini API (gemini-3.8-flash) で執筆を試行中 ---")
    try:
        res = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_prompt,
            config=dict(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7),
        )
        if res and res.text:
            print("✅ 成功: Gemini API で記事が完成しました！")
            response_text = res.text
    except Exception as e:
        print(f"⚠️ Gemini API 一時停止/制限中: {str(e)[:120]}")

# 2. Gemini が 429（上限）等の場合、完全無料のバックアップAI（Pollinations Text API）へ自動切替
if not response_text:
    print("--- バックアップAIエンジンで記事生成を実行中 ---")
    try:
        payload = {
            "messages": [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": user_prompt}
            ],
            "seed": int(time.time())
        }
        r = requests.post("https://text.pollinations.ai/", json=payload, timeout=90)
        if r.status_code == 200 and len(r.text) > 300:
            print("✅ 成功: バックアップAIエンジンで記事が完成しました！")
            response_text = r.text
    except Exception as ex:
        print(f"バックアップAIエラー: {ex}")

# 3. 万が一すべてのAI通信が途絶えた場合の安全テキスト
if not response_text:
    print("⚠️ 緊急エディションを出力してサイト停止を防ぎます。")
    response_text = f"""
<h2 id="lead-story">01. Lead Story: Science & Discovery</h2>
本日も最新のサイエンスとプロセス化学の知見からスタートします。

<h2 id="benjamin">02. Special Column: Daily Benjamin — 思考の調律と徳目の実践</h2>
育休期の現在は、生活インフラを支え抜くことこそが最大のプロジェクトです。睡眠不足と身体の緊張に目を向け、名もなき育児家事を完遂した今日を100点として加算しましょう。

{img_tag_1}

<h2 id="news">03. Curated News & Macro: 世界経済と暮らしのインパクト</h2>
- [日本経済新聞 / ビジネス](https://www.nikkei.com/business/)
- [ABEMA TIMES](https://times.abema.tv/)

<h2 id="escape">10. Escape: Sauna Destination, Route & Home</h2>
Honda GB350の心地よい鼓動とともに、静かな夜とハンドドリップ珈琲の香りを味わいましょう。

{img_tag_2}

<h2 id="colophon">11. Editor's Colophon</h2>
本日も穏やかで健やかな一日をお過ごしください。
"""

# 万が一本文冒頭にメタデータが漏れた場合の強制除去クリーニング
clean_text = re.sub(
    r'^(title:.*?\n|TITLE:.*?\n|date:.*?\n|DATE:.*?\n|temp:.*?\n|TEMP:.*?\n|sunset:.*?\n|SUNSET:.*?\n|wind:.*?\n|WIND:.*?\n|bike:.*?\n|BIKE:.*?\n)+',
    '',
    response_text.strip(),
    flags=re.MULTILINE | re.IGNORECASE
).strip()

# フローチャートの閉じタグ補完
if '<div class="flow-wrapper">' in clean_text:
    parts = clean_text.split('<div class="flow-wrapper">')
    reconstructed = parts[0]
    for p in parts[1:]:
        if '</div>' not in p or p.find('</div>') > 1000:
            p = p.replace('\n\n', '</div>\n\n', 1)
        reconstructed += '<div class="flow-wrapper">' + p
    clean_text = reconstructed

# 4. リアルなライフスタイル写真2枚を生成
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
                print(f"Imagenで生成成功: {file_path}")
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
            print(f"フォトエンジンで生成保存完了: {file_path}")
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
