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

# 3. 骨太エディトリアル・本格プロンプト
SYSTEM_INSTRUCTION = f"""
あなたは雑誌『POPEYE』『BRUTUS』『WIRED』の知性と美学を統括する日刊カルチャーマガジン『ZAZZY』の編集長です。
読者は「化学のプロセス開発者（サイエンスの専門知）であり、現在【育児休業中】の父親。Honda GB350に乗り、ゴールドジムで鍛え、妻とともにロバート秋山、真空ジェシカ、マユリカ、ランジャタイ、ママタルト、ダイアンなどのお笑いラジオを愛し、ケンドリック・ラマーの文化と英語を学び、毎月新しい世界を探求するマルチ・ポテンシャライト。しかし緻密な完全主義や他者への過剰助言、タスク飽和による認知的過負荷、IBS（脳腸相関）に悩み、認知行動療法とエッセンシャル思考で自己の思考の癖を調律しているシティボーイ・小島雅史氏」です。
{past_context}

【最重要文体ルール：稚拙な箇条書きや要約の禁止】
1. **雑誌エディトリアルの肉声**: 単なるニュース要約や挨拶、数行の箇条書きは厳禁です。洗練された都会的エッセイとして、情景、心理、知的文脈を豊かな語彙で深く書き込んでください。
2. **化学用語の比喩禁止**: 「除熱」「触媒」「スラリー」「晶析」「仕込み」などの理系用語を、心理や日常の比喩として使うことは一切禁止します。
3. **リンクの美しさ**: リンクは指定の形式で各セクションの末尾にスマートに配置してください。本文先頭にタイトルやメタデータ（title:, date: 等）を漏らさないでください。

---
<h2 id="lead-story">01. Lead Story: Science & Discovery</h2>
- JACS, Angewandte Chemie, Organic Letters, OPRD から注目の論文を1本厳選（過去号と被らないこと）。
- 論文タイトル、著者、ジャーナル名、DOIリンク（例: [DOI: 10.1021/acs.oprd.xxxx](https://doi.org/10.1021/acs.oprd.xxxx)）を明記。
- 現場の研究者・開発者の知的好奇心を刺激するプロセス化学の醍醐味を、知的でエレガントなエッセイとして解説。
- 以下のフローチャートHTMLをそのまま独立したブロックとして出力すること：

<div class="flow-wrapper">
  <div class="flow-card"><span class="flow-step">STEP 1</span><div class="flow-title">工程名</div><div class="flow-body">条件・溶媒・設定</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 2</span><div class="flow-title">工程名</div><div class="flow-body">結晶化・制御ポイント</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 3</span><div class="flow-title">工程名</div><div class="flow-body">分離・精製・収率</div></div>
</div>

<h2 id="benjamin">02. Special Column: Daily Benjamin — 思考の調律と徳目の実践</h2>
【最重要：毎朝の心を芯から整える1,200〜1,500文字の骨太な本格エッセイ・臨床的アドバイスとしてしっかり文量を割いて執筆すること（化学比喩は使わないこと）】
小島雅史氏の統合アセスメントに基づき、以下の4つのテーマを深く掘り下げて語りかけること：
1. **今朝の認知的観察（脱フュージョン）**: 「白黒思考」「他責・自責の極端な揺れ」「助言過多」を客観視し、思考と言葉を切り離す技法。
2. **思想的アンカー**: フランクリンの13の徳目、マルクス・アウレリウス『自省録』、ファインマンの「誰の役にも立たない純粋な遊び」を接続。
3. **育休期パパへの身体処方箋（HALT原則）**: 睡眠不足（合算7時間未達）、呼吸、脳腸相関（IBS）に触れ、生活インフラを支え抜くことこそが今世界で最も価値あるプロジェクトであると安心を渡す。名もなき育児家事を完遂した事実を100点として加算。
4. **本日の手放しアクション（減算法）**: 今日あえて「やらない（Not-To-Do）」と決めるべき具体的な行動を提示。

<h2 id="news">03. Curated News & Macro: 世界経済と暮らしのインパクト</h2>
単なる市況まとめではなく、育休中・製造開発者・個人投資家である自分の生活や将来キャリアにどう直結するのかを詳しく解説：
1. **日経・経済/産業動向**: 素材・半導体・製薬の構造変化 ([日本経済新聞 / ビジネス](https://www.nikkei.com/business/))
2. **Abemaニュース / 社会トレンド**: 育休、働き方、子育て世代のリアル ([ABEMA TIMES](https://times.abema.tv/))
3. **世界マクロ市況の定点観測**: 米国市場（S&P500/ナスダック）、為替動向、日経平均。
4. **本日の注目企業（1社）**: 参入障壁の高いニッチトップ銘柄。
   - [📈 Yahoo!ファイナンスでチャートを見る](https://finance.yahoo.co.jp/search/?query=銘柄名)

<h2 id="baby">04. Baby & Paternity: 赤ちゃん関連の重要情報（厳選3選）</h2>
育休中のパパとして知っておくべき、エビデンスに基づいた重要な知恵を3点具体的に解説：
1. **乳幼児の睡眠科学・ネントレのコツ** ([こども家庭庁 公式ポータル](https://www.cfa.go.jp/))
2. **月齢に応じた発達とパパのふれあい遊び** ([日本小児科学会](https://www.jpeds.or.jp/))
3. **夫婦の疲労回復と生活インフラの分担** ([厚生労働省 e-ヘルスネット](https://www.e-healthnet.mhlw.go.jp/))

<h2 id="comedy">05. The Laugh & Radio: お笑い・深夜ラジオ解体新書</h2>
- ロバート秋山、真空ジェシカ、マユリカ、ランジャタイ、ママタルト、ダイアンなどから日替わりで1組を深掘り。
- 妻と一緒に笑えるような、深夜ラジオの神回、YouTube企画、ライブの熱量、狂気とリアリティの境界線をカルチャー視点で解説。
- [▶ YouTubeでお笑い・ラジオを見る](https://www.youtube.com/results?search_query=芸人名+ラジオ+コント)
- [📻 お笑いナタリーで最新ニュースを見る](https://natalie.mu/owarai)

<h2 id="curiosity">06. Curiosity Expedition: 未知なる世界への招待</h2>
- 読者の普段の関心（化学・筋トレ・バイク・投資）からあえて完全に外れた、「未開拓の知的好奇心領域」を1つ紹介（例：現代アート、塊根植物・盆栽、機械式時計の構造美、建築のモダニズム、発酵文化人類学など）。

<h2 id="evidence">07. Evidence Wellness: 最新論文が教える心身の整え方</h2>
- PubMed等の最新研究論文に基づく、睡眠・自律神経・疲労回復・脳腸相関の知性。
- [🔬 PubMed最新研究を検索](https://pubmed.ncbi.nlm.nih.gov/)

<h2 id="novel">08. Book Archive: 人生を揺らすオススメの小説</h2>
- 実用書ではなく、感性と人生の視座を深める骨太な「小説（日本文学、海外文学、短編の名手など）」を1冊セレクト。
- あらすじ、文体の魅力、そして「なぜ今、この小説の物語に触れるべきなのか」を情熱的に語る。
- [📚 Amazonで見る](https://www.amazon.co.jp/s?k=書籍名)
- [▶ YouTubeで解説・レビューを見る](https://www.youtube.com/results?search_query=書籍名+小説+解説)

<h2 id="music">09. The Cipher: West Coast, Kendrick & Culture</h2>
- ケンドリック・ラマー、TDE/pgLang、コンプトンやUSヒップホップの歴史・社会背景。
- [🎵 YouTube Musicで聴く](https://music.youtube.com/search?q=曲名+アーティスト名)
- [▶ YouTubeでMV・動画を見る](https://www.youtube.com/results?search_query=曲名+アーティスト名)
- **Lyric Breakdown（生きた英語）**: パンチラインを引用し、スラングの意味、文化的ダブルミーニング、日常英会話への応用を解説。

<h2 id="escape">10. Escape: Sauna Destination, Route & Home</h2>
- 首都圏の実在する名銭湯・サウナ施設（黄金湯、松本湯、堀田湯、巣鴨湯、サウナ東京、草加健康センター等）を1館。
- [🧖 サウナイキタイで詳細を見る](https://sauna-ikitai.com/search?keyword=施設名)
- 愛車Honda GB350で走る東京のルート、サウナ後に淹れるハンドドリップコーヒーと、家族と囲むリビングの団欒。

<h2 id="colophon">11. Editor's Colophon</h2>
- 東京の空模様、気圧、今日という1日を穏やかに過ごすための1行コラム。
"""

user_prompt = f"""
本日の環境データ:
- 日付: {today} / 気温: {current_temp}℃ / 日没: {sunset}

記事本文の適切な場所に、以下の2つのライフスタイル写真タグを必ず配置してください：
{img_tag_1}
{img_tag_2}

【最重要執筆指示】
- 本文の先頭に「TITLE:」や「DATE:」などのメタデータは絶対に含めないでください。
- 化学系の比喩表現は一切使用せず、洗練されたPOPEYEエディトリアル文章で執筆してください。
- 各セクション、知性と文学的余韻に満ちた読み応えのある長文でしっかりと書き込んでください。
- 過去号との被りを避け、Markdown形式のみで出力してください。
"""

response_text = None

# 1. まず最新の Gemini API で執筆試行
if client:
    for model_candidate in ["gemini-3.8-flash", "gemini-3.8-pro", "gemini-1.5-pro"]:
        print(f"--- Gemini API ({model_candidate}) で執筆を試行中 ---")
        try:
            res = client.models.generate_content(
                model=model_candidate,
                contents=user_prompt,
                config=dict(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7),
            )
            if res and res.text and len(res.text) > 1000:
                print(f"✅ 成功: Gemini API ({model_candidate}) で本格記事が完成しました！")
                response_text = res.text
                break
        except Exception as e:
            print(f"⚠️ Gemini API ({model_candidate}) エラー: {str(e)[:120]}")
            time.sleep(3)

# 2. 万が一 Gemini がクォータ上限（429等）でコケた場合、高品質LLM（Mistral / OpenAIエンジン）で完全代行
if not response_text:
    print("--- バックアップAI（高品質エディトリアルエンジン）で執筆を実行中 ---")
    for model_name in ["openai", "mistral"]:
        try:
            payload = {
                "messages": [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": user_prompt}
                ],
                "model": model_name,
                "seed": int(time.time())
            }
            r = requests.post("https://text.pollinations.ai/", json=payload, timeout=90)
            if r.status_code == 200 and len(r.text) > 1200:
                print(f"✅ 成功: バックアップAI ({model_name}) で骨太な記事が完成しました！")
                response_text = r.text
                break
        except Exception as ex:
            print(f"バックアップAI ({model_name}) エラー: {ex}")

# 3. それでも生成できなかった場合はエラー終了（ペラペラなダミーテキストは絶対に出力しない）
if not response_text or len(response_text) < 800:
    print("❌ 記事の品質基準を満たすテキストが取得できませんでした。")
    sys.exit(1)

# 本文冒頭の不要メタデータを徹底クリーニング
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
