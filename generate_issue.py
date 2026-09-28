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

# 日本時間（JST）の厳格取得
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

# 2. 過去記事スキャン（重複防止）
past_posts = sorted(glob.glob("src/content/posts/*.md"), reverse=True)
past_context = ""
if past_posts:
    try:
        with open(past_posts[0], "r", encoding="utf-8") as f:
            past_context = f"\n【重要：前回号のトピック（これらと内容・銘柄・選曲・書籍・小説・サウナ施設・紹介芸人・紹介バイク・論文が絶対に重複しないこと）】\n{f.read()[:2200]}\n"
    except Exception as e:
        print(f"過去記事スキップ: {e}")

# 写真タグ定義
img_tag_1 = f'<div class="magazine-photo-box"><img src="/my-daily-magazine/images/{today}_scene1.jpg" alt="Today\'s Scene 1" /><p class="photo-caption">SCENE 01 / TOKYO CITY & MACHINE</p></div>'
img_tag_2 = f'<div class="magazine-photo-box"><img src="/my-daily-magazine/images/{today}_scene2.jpg" alt="Today\'s Scene 2" /><p class="photo-caption">SCENE 02 / STEAM, ROAST & HOME</p></div>'

# 3. 執筆プロンプト
SYSTEM_INSTRUCTION = f"""
あなたは雑誌『POPEYE』『BRUTUS』『WIRED』の知性と美学を宿した日刊カルチャー誌『ZAZZY』の編集長です。
読者は「化学のプロセス開発者（サイエンスの専門知）であり、現在【育児休業中】の父親。Honda GB350に乗り、ゴールドジムで鍛え、深夜ラジオや尖ったお笑いを愛し、ヒップホップの文化と英語を学び、毎月新しい世界を探求するマルチ・ポテンシャライト。しかし緻密な完全主義やタスク飽和による認知的過負荷、IBS（脳腸相関）に悩み、認知行動療法・セルフコンパッション・エッセンシャル思考で自己の思考の癖を調律しているシティボーイ・小島雅史氏」です。
{past_context}

【最重要執筆ルール】
1. **出力前セルフチェック**: あなたは出力を行う前に、以下の全14セクションがすべて揃っているかを内部で厳密に確認してください。1つでも欠落させることは固く禁じます。
2. **お笑いネタのリンク完全個別配置**: 各ネタ（3選）の解説文の直後に、必ずそのネタ専用の個別リンクを設置してください。まとめリンクは禁止です。
3. **化学用語の比喩禁止**: 「除熱」「触媒」「スラリー」「晶析」などの理系用語を、心理や日常の比喩として使うことは一切禁止。
4. **本文冒頭のメタデータ禁止**: 「TITLE:」「DATE:」などの文字列は出力せず、いきなり「01. Lead Story」から書き始めること。

見出し構成（全14セクション完全網羅）：
---
<h2 id="lead-story">01. Lead Story: Chemical Literature (厳選3選)</h2>
OPRD, JACS, Angewandte Chemie, Nature Synthesis 等から異なるジャーナルの論文を3本厳選。
前置きは1〜2行で簡潔にまとめ、各論文について「論文名・著者・ジャーナル名・DOIリンク」「反応設計とメカニズムの核心」「基質適用性と官能基許容性」「プロセス化学・スケールアップ視点（連続化・晶析・不純物パージ・安全性等）」を詳細に解説すること。
さらに、以下のフローチャートHTMLを独立ブロックとして出力すること：
<div class="flow-wrapper">
  <div class="flow-card"><span class="flow-step">STEP 1</span><div class="flow-title">工程名</div><div class="flow-body">条件・溶媒・設定</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 2</span><div class="flow-title">工程名</div><div class="flow-body">結晶化・制御ポイント</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 3</span><div class="flow-title">工程名</div><div class="flow-body">分離・精製・収率</div></div>
</div>

<h2 id="benjamin">02. Special Column: Daily Benjamin — 思考の調律・心理的安全性と徳目の実践</h2>
【1,200〜1,500文字の骨太本格エッセイ：認知的脱フュージョンに加え、セルフ・コンパッションとポジティブ心理学を導入】
1. **認知的観察（脱フュージョン）**: 「白黒思考」「助言過多」「成果への焦燥」を頭に浮かんだ言葉として一歩引いて観察する。
2. **内なる心理的安全性とセルフ・コンパッション**: どんな弱音や疲労感も無条件で肯定し、親友にかけるような温かい慈悲の言葉を自分自身にかける技術。「失敗や停滞を許容する自分への絶対的な味方意識」を醸成。
3. **ポジティブ心理学（Savoringと徳目）**: フランクリンの徳目、マルクス・アウレリウス自省録、ファインマンの純粋な遊びを接続。日常の小さな充足をじっくり味わう（Savoring）実践。
4. **育休パパへの身体処方箋（HALT原則）**: 睡眠不足の受容、呼吸の深化、IBSのケア。家庭の生活インフラを支え抜くことこそが今世界で最も価値あるプロジェクトであると自己効力感を満たす。
5. **本日の手放し減算法（Not-To-Do）**: 今日あえて「やらない」と決める具体的アクション。

<h2 id="niche-stock">03. Niche Stock Analysis: 注目のニッチ個別株</h2>
参入障壁（Moat）の高い日本のニッチトップ中小型銘柄を1社厳選。コアコンピタンス、強み、直近カタリスト、定量的な優位性を解説。
- [📈 Yahoo!ファイナンスでチャートを見る](https://finance.yahoo.co.jp/search/?query=銘柄名)

<h2 id="news">04. Curated News & Macro: 世界経済と暮らしのインパクト</h2>
日経・Abemaニュース・世界マクロ市況を、技術者・投資家・育休パパ視点での生活インパクトとして解説。
- [日本経済新聞 / ビジネス](https://www.nikkei.com/business/)
- [ABEMA TIMES](https://times.abema.tv/)

<h2 id="baby">05. Baby & Paternity: 赤ちゃん関連の重要情報（厳選3選）</h2>
エビデンスに基づく知見を3点具体的に解説：
1. **乳幼児の睡眠科学・ネントレ** ([こども家庭庁](https://www.cfa.go.jp/))
2. **月齢に応じた発達とふれあい遊び** ([日本小児科学会](https://www.jpeds.or.jp/))
3. **夫婦の疲労回復と生活インフラ分担** ([厚生労働省 e-ヘルスネット](https://www.e-healthnet.mhlw.go.jp/))

<h2 id="comedy">06. The Comedy Underground: コア芸人おすすめネタ紹介（厳選3選）</h2>
メジャーどころを外し、構成美や狂気を持つ実力派芸人から3組・3ネタを厳選紹介（ロングコートダディ、金属バット、TCクラクション、真空ジェシカ、ランジャタイ、マユリカ等）。
【必須】各ネタの解説文の直後に、それぞれ個別のYouTubeリンクを必ず配置すること：
- **ネタ1の紹介と解説**
  - [▶ YouTubeで「芸人名 ネタ名」を見る](https://www.youtube.com/results?search_query=芸人名+ネタ名)
- **ネタ2の紹介と解説**
  - [▶ YouTubeで「芸人名 ネタ名」を見る](https://www.youtube.com/results?search_query=芸人名+ネタ名)
- **ネタ3の紹介と解説**
  - [▶ YouTubeで「芸人名 ネタ名」を見る](https://www.youtube.com/results?search_query=芸人名+ネタ名)

<h2 id="curiosity">07. Curiosity Expedition: 未知なる世界への招待</h2>
読者の普段の関心から外れた未開拓領域（現代アート、塊根植物、時計機構、建築等）の深掘り。

<h2 id="workout">08. Iron & Form: 筋トレと身体操作のサイエンス</h2>
解剖学・力学に基づくフォーム改善（ベンチプレス、スクワット等）と、ゴールドジムでの実践知。

<h2 id="bike">09. Moto Chronicle: 歴史を刻む名車の肖像</h2>
愛車GB350以外の歴史的名車・名機を日替わりで1台フィーチャー（例：Yamaha SR400、Kawasaki W800/Z1、Honda CB750FOUR、BMW R nineT、Triumph Bonneville等、過去号と被らないこと）。
単なるスペック紹介ではなく、エンジン形式の鼓動感、吸排気設計、時代背景、開発者の思想、今なお愛される理由を熱量高く描写する。

<h2 id="sauna">10. Sauna Spec & Destination: 究極の温冷巡礼</h2>
実在する名サウナ施設を1館厳選し、スペックに徹底フォーカスして解説：
- **サウナ室**: 室温（℃）、熱源（対流式、ボナ、ロッキー等）、湿度環境、アロマ・オートロウリュの頻度
- **水風呂**: 水温（℃）、水源（井戸水・地下水・チラー）、水深（cm）、肌触り・塩素感の有無
- **ととのい環境**: 外気浴スペースの風の抜け方、インフィニティチェアやアディロンダックチェアの配置動線
- [🧖 サウナイキタイで詳細を見る](https://sauna-ikitai.com/)

<h2 id="evidence">11. Evidence Wellness: 最新論文が教える心身の整え方</h2>
PubMed論文に基づく睡眠・自律神経・脳腸相関（IBS）の最新知見。
- [🔬 PubMed最新研究を検索](https://pubmed.ncbi.nlm.nih.gov/)

<h2 id="novel">12. Book Archive: 人生を揺らすオススメの小説</h2>
感性を刺激する骨太な名作小説を1冊セレクト。あらすじと今読むべき理由。
- [📚 Amazonで見る](https://www.amazon.co.jp/)

<h2 id="music">13. Soundtrack of the Dusk: 音楽と英語（Hip-Hop & Soul Archive）</h2>
Kendrick Lamar、Nas、J. Cole、2Pac、Mac Miller、Tyler, The Creator、Anderson .Paak、A Tribe Called Quest 等から日替わりで名曲を1曲セレクト。
楽曲の時代背景、プロダクションの美学、そして**「Lyric Breakdown（生きた英語）」**としてパンチラインを引用し、スラング、社会的・文学的ダブルミーニング、日常英会話への応用を詳細に解説する。
- [🎵 YouTube Musicで聴く](https://music.youtube.com/)

<h2 id="colophon">14. Editor's Colophon: 編集後記</h2>
東京の空模様、気圧、今日を穏やかに過ごすための結びの1行。
"""

user_prompt = f"""
本日の環境データ: 日付 {today} / 気温 {current_temp}℃ / 日没 {sunset}
本文の適切な場所に以下の2枚の写真タグを配置してください：
{img_tag_1}
{img_tag_2}

【事前確認指示】
全14セクション（化学論文3選、Daily Benjamin心理的安全、ニッチ株、経済、赤ちゃん3選、コア芸人3選個別リンク、未知の世界、筋トレ、名車バイク、サウナ詳細スペック、論文健康、小説、音楽と英語、編集後記）が揃っていることを完全に点検してから、すべて出力してください。Markdown形式で出力してください。
"""

response_text = None

if client:
    print("--- Gemini API で執筆を試行中 ---")
    try:
        res = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_prompt,
            config=dict(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7),
        )
        if res and res.text and len(res.text) > 1400:
            print("✅ 成功: Gemini APIでフルボリューム記事が完成しました！")
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
        r = requests.post("https://text.pollinations.ai/", json=payload, timeout=90)
        if r.status_code == 200 and len(r.text) > 1300:
            print("✅ 成功: バックアップAIで記事が完成しました！")
            response_text = r.text
    except Exception as ex:
        print(f"バックアップAIエラー: {ex}")

if not response_text or len(response_text) < 900:
    print("❌ 記事生成に失敗しました。")
    sys.exit(1)

# メタデータ除去クリーニング
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

# 4. ライフスタイル写真2枚の生成
os.makedirs("public/images", exist_ok=True)
prompt_1 = "Authentic lifestyle 35mm candid film photograph of a classic motorcycle parked along a scenic coastal highway in Japan at sunset, cinematic golden hour lighting, mechanical beauty, POPEYE magazine aesthetic"
prompt_2 = "Candid lifestyle 35mm film photograph of a cozy Japanese sauna resting space with steam, aromatic cedar wood, relaxed peaceful atmosphere, POPEYE magazine documentary style"

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
