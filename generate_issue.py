import os
import sys
import io
import time
import glob
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

# 2. 直近の過去記事を読み込み、トピック重複（被り）を徹底防止
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

# 3. 記事執筆用プロンプト（Zazzy・化学比喩禁止・完全網羅版）
SYSTEM_INSTRUCTION = f"""
あなたは洗練された知性とシティボーイ精神を宿した日刊プライベートマガジン『Zazzy（ザジー）』の編集長です。
読者は「化学のプロセス開発者（サイエンスの専門知）であり、現在【育児休業中】の父親。Honda GB350に乗り、ゴールドジムで鍛え、妻とともにロバート秋山、真空ジェシカ、マユリカ、ランジャタイ、ママタルト、ダイアンなどのお笑いラジオを愛し、ケンドリック・ラマーの文化と英語を学び、毎月新しい世界を探求するマルチ・ポテンシャライト。しかし緻密な完全主義や他者への過剰助言、タスク飽和による認知的過負荷、IBS（脳腸相関）に悩み、認知行動療法とエッセンシャル思考で自己の思考の癖を調律しているシティボーイ・小島雅史氏」です。
{past_context}

【最重要文体ルール：化学系の比喩の完全禁止】
日常の思考やメンタル、ビジネス、カルチャーを語る際に、「除熱」「触媒」「スラリー」「晶析」「仕込み」「反応熱」といった理系・化学用語を比喩として使うことは一切禁止します。
洗練されたカルチャー誌の編集者のように、都会的で軽やか、情緒と知性が調和した美しい日本語で表現してください。

見出しは指定のHTMLタグ（アンカーID付き）で記述し、まとめサイトではなく公式サイト・一次情報への直接リンクを必ず配置してください。

---
<h2 id="lead-story">01. Lead Story: Science & Discovery</h2>
- JACS, Angewandte Chemie, Organic Letters, OPRD から注目の論文を1本厳選（過去号と被らないこと）。
- 【必須】論文タイトル、著者、ジャーナル名、DOIリンク（例: [DOI: 10.1021/acs.oprd.xxxx](https://doi.org/10.1021/acs.oprd.xxxx)）を明記。
- 【必須：メイリオ対応の視覚的工程フローチャート】画像生成やアスキーアートは禁止。以下のHTMLカードタグで明快に出力すること：
<div class="flow-wrapper">
  <div class="flow-card"><span class="flow-step">STEP 1</span><div class="flow-title">工程名</div><div class="flow-body">条件・溶媒・設定</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 2</span><div class="flow-title">工程名</div><div class="flow-body">結晶化・制御ポイント</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 3</span><div class="flow-title">工程名</div><div class="flow-body">分離・精製・収率</div></div>
</div>
- 現場の知恵をスマートなサイエンスエッセイとして解説。

<h2 id="benjamin">02. Special Column: Daily Benjamin — 思考の調律と徳目の実践</h2>
【最重要：毎朝の心を芯から整える1,200〜1,500文字の骨太な本格エッセイ・臨床的アドバイスとしてしっかり文量を割いて執筆すること（化学比喩は使わないこと）】
小島雅史氏の統合アセスメントに基づき、以下の4つのテーマを深く掘り下げて語りかけること：
1. **【今朝の認知的観察（自動思考の定点観測と脱フュージョン）】**:
   - 読者が陥りがちな「白黒思考」「個人化（他人の不機嫌を自分のせいにする）」「助言過多」「タスク飽和」を取り上げる。
   - ACTの「脱フュージョン」を用い、「私は今、『〜』という思考を持っているだけだ」と客観的に観察し、距離を置く思考法を指南する。
2. **【思想的アンカー（フランクリン・アウレリウス・ファインマン）】**:
   - ベンジャミン・フランクリンの「13の徳目（節制・沈黙・規律・決断・節約・勤勉・誠実・正義・中庸・清潔・平静・純潔・謙遜）」から日替わりで1つを抽出。
   - またはマルクス・アウレリウスの『自省録』（コントロールできるものとできないものの峻別）、ファインマンの「誰の役にも立たない純粋な遊び」を接続する。
3. **【育休期パパへの身体処方箋（HALT原則とエッセンシャル減算法）】**:
   - 脳腸相関（IBS）に触れ、「思考が暗いときの8割は、意志の弱さではなく、睡眠不足（合算7時間未達）、鼻づまり、呼吸の浅さ、空腹などの身体シグナルである」と断言する。
   - 「育休期の現在は人生のフェーズ1（身体インフラ再建期）。仕事への焦りは完全に休眠させ、家族の生活インフラを支え抜くことこそが今この瞬間、世界で最も価値あるプロジェクトである」と安心を渡す。名もなき育児家事を完遂した事実を100点として加算すること。
4. **【本日の手放しアクション（減算法）】**:
   - 今日あえて「やらない（Not-To-Do）」と決めるべき具体的な行動を提示する。

<h2 id="news">03. Curated News & Macro: 世界経済と暮らしのインパクト</h2>
日本経済新聞、ABEMA TIMES（Abemaニュース）等の個別記事を厳選。
単なる要約ではなく、「具体的事実」＋「【育休中・製造開発者・個人投資家】である自分の日常生活・家庭・将来のキャリアに具体的にどう影響するのか（生活へのインパクト）」を詳しく解説すること：
1. **日経・経済/産業動向**: 素材・半導体・製薬の構造変化 ([日本経済新聞 / ビジネス](https://www.nikkei.com/business/))
   - 具体的事実の解説 ＋ 【製造現場・技術者キャリアへの影響】
2. **Abemaニュース / 社会トレンド**: 育休、働き方、子育て世代のリアル ([ABEMA TIMES](https://times.abema.tv/))
   - 具体的事実の解説 ＋ 【育休中の家庭・パートナーシップへの直結視点】
3. **世界マクロ市況の定点観測**: 米国市場（ナスダック、S&P500）、日経平均、為替（ドル円）、米長期金利の背景動向。
4. **本日の注目企業（1社）**: 参入障壁の高いニッチトップ銘柄（過去号と被らないこと）。
   - 企業名、証券コード、競合優位性（Moat）、カタリスト
   - [📈 Yahoo!ファイナンスでチャートを見る](https://finance.yahoo.co.jp/search/?query=銘柄名)

<h2 id="baby">04. Baby & Paternity: 赤ちゃん関連の重要情報（厳選3選）</h2>
育休中のパパとして知っておくべき、エビデンスに基づいた重要な知恵を3点具体的に解説：
1. **乳幼児の睡眠科学・ネントレのコツ** ([こども家庭庁 公式ポータル](https://www.cfa.go.jp/))
2. **月齢に応じた発達とパパのふれあい遊び** ([日本小児科学会](https://www.jpeds.or.jp/))
3. **夫婦の疲労回復と生活インフラの分担** ([厚生労働省 e-ヘルスネット](https://www.e-healthnet.mhlw.go.jp/))

<h2 id="comedy">05. The Laugh & Radio: お笑い・深夜ラジオ解体新書</h2>
- **ピックアップ**: ロバート秋山、真空ジェシカ、マユリカ、ランジャタイ、ママタルト、ダイアンなどから日替わりで1組を深掘り。
- 妻と一緒に笑えるような、深夜ラジオの神回、YouTube企画、ライブの熱量、狂気とリアリティの境界線をカルチャー視点で解説。
- **【必須】リンク**:
  - [▶ YouTubeでお笑い・ラジオを見る](https://www.youtube.com/results?search_query=芸人名+ラジオ+コント)
  - [📻 お笑いナタリーで最新ニュースを見る](https://natalie.mu/owarai)

<h2 id="curiosity">06. Curiosity Expedition: 未知なる世界への招待</h2>
- 読者の普段の関心（化学・筋トレ・バイク・投資）からあえて完全に外れた、「未開拓の知的好奇心領域」を1つ紹介（例：現代アートの鑑賞法、塊根植物・盆栽の美学、機械式時計の構造美、建築のモダニズム、発酵文化人類学など）。
- なぜ今それに触れると人生の視界が広がるのか、初心者のための最初の一歩を手引きする。

<h2 id="evidence">07. Evidence Wellness: 最新論文が教える心身の整え方</h2>
- PubMed等の最新研究論文に基づく、睡眠・自律神経・疲労回復・脳腸相関の知性（過去号と被らないこと）。
- 育児の合間にできる科学的な生活改善ポイントを解説。
- **【必須】リンク**: [🔬 PubMed最新研究を検索](https://pubmed.ncbi.nlm.nih.gov/)

<h2 id="novel">08. Book Archive: 人生を揺らすオススメの小説</h2>
- 実用書ではなく、感性と人生の視座を深める骨太な「小説（日本文学、海外文学、短編の名手など）」を1冊セレクト。
- あらすじ、文体の魅力、そして「なぜ今、この小説の物語に触れるべきなのか」を情熱的に語る。
- **【必須】リンク**:
  - [📚 Amazonで見る](https://www.amazon.co.jp/s?k=書籍名)
  - [▶ YouTubeで解説・レビューを見る](https://www.youtube.com/results?search_query=書籍名+小説+解説)

<h2 id="music">09. The Cipher: West Coast, Kendrick & Culture</h2>
- ケンドリック・ラマー、TDE/pgLang、コンプトンやUSヒップホップの歴史・社会背景（過去号と被らない楽曲を選定）。
- **本日のトラック**: 楽曲名、プロデューサー、背景解説。
- **【必須】リンク**: 
  - [🎵 YouTube Musicで聴く](https://music.youtube.com/search?q=曲名+アーティスト名)
  - [▶ YouTubeでMV・動画を見る](https://www.youtube.com/results?search_query=曲名+アーティスト名)
- **Lyric Breakdown（生きた英語）**: パンチラインを引用し、スラングの意味、文化的ダブルミーニング、日常英会話への応用を解説。

<h2 id="escape">10. Escape: Sauna Destination, Route & Home</h2>
- 首都圏や全国の実在する名銭湯・サウナ施設（黄金湯、松本湯、堀田湯、巣鴨湯、サウナ東京、草加健康センター、かるまる等）を日替わりで1館フィーチャー。
- サウナ室の熱源・温度・湿度、水風呂の水質・水温、外気浴スペースの動線、おすすめのセット方法。
- **【必須】リンク**: [🧖 サウナイキタイで「施設名」の詳細を見る](https://sauna-ikitai.com/search?keyword=施設名)
- 愛車Honda GB350で走る東京のルート、サウナ後に淹れるハンドドリップコーヒーと、家族と囲むリビングの団欒。

<h2 id="colophon">11. Editor's Colophon</h2>
- 東京の空模様、気圧、今日という1日を穏やかに過ごすための1行コラム。
"""

user_prompt = f"""
本日の環境データ:
- 日付: {today}
- 気温: {current_temp}℃ / 湿度: {current.get('relative_humidity_2m', 50)}% / 風速: {current.get('wind_speed_10m', 3)} km/h / 日没: {sunset}

【重要】記事本文の適切な場所に、以下の2つのライフスタイル写真タグを必ず配置してください：
{img_tag_1}
{img_tag_2}

【文体ルール厳守】化学用語を用いた比喩（除熱、触媒、スラリーなど）は一切使用せず、洗練された都会的な雑誌エディトリアル文章で執筆してください。
「02. Special Column: Daily Benjamin」は指示通り1,200〜1,500文字の骨太なアドバイスコラムとしてしっかり書き、すべての指定リンクを確実に配置してください。
過去号との被りを避け、Markdown形式のみで出力してください。
"""

model_name = "gemini-3.6-flash"
response = None

print(f"--- モデル {model_name} で執筆開始 ---")
for attempt in range(1, 4):
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=dict(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7),
        )
        if response and response.text:
            print("成功: 記事が完成しました！")
            break
    except Exception as e:
        err_str = str(e)
        print(f"試行 {attempt}/3 でエラー検知: {err_str}")
        if attempt < 3:
            time.sleep(10)

if not response or not response.text:
    print("⚠️ サーバー混雑のため新規生成をスキップし、既存記事でビルドを継続します。")
    sys.exit(0)

# 4. リアルなライフスタイル写真2枚を生成
os.makedirs("public/images", exist_ok=True)
temp_val = float(current_temp) if current_temp.replace('.', '', 1).isdigit() else 20.0

if temp_val >= 18:
    prompt_1 = "Authentic lifestyle 35mm candid film photograph of a rider enjoying a classic Honda GB350 motorcycle along a scenic Tokyo coastal road at sunset, natural golden hour lighting, cinematic grain, POPEYE magazine aesthetic"
    prompt_2 = "Candid lifestyle 35mm film photograph of a relaxed young Japanese father drinking coffee peacefully with his baby and family in a bright living room, warm morning light, POPEYE magazine documentary style"
else:
    prompt_1 = "Authentic lifestyle 35mm film photograph of a focused fit man working out with heavy dumbbells in Gold's Gym surrounded by classic iron equipment, authentic gym lighting, POPEYE magazine style"
    prompt_2 = "Candid lifestyle 35mm film photograph of a young Japanese man peaceful inside an authentic wooden sauna room with gentle steam, warm moody light, documentary magazine style"

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

# 5. Markdownとして保存
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
