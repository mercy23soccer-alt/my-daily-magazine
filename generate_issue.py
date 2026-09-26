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
    latest_past_file = past_posts[0]
    try:
        with open(latest_past_file, "r", encoding="utf-8") as f:
            past_content = f.read()
            past_context = f"\n【重要：前回号のトピック（これらと内容・銘柄・選曲・書籍・サウナ施設・紹介芸人・論文が絶対に重複しないこと）】\n{past_content[:1800]}\n"
    except Exception as e:
        print(f"過去記事の読み込みスキップ: {e}")

# 画像タグ定義（わけのわからない論文画像は廃止し、雑誌風スナップ写真2枚のみに厳選）
img_tag_1 = f'<div class="magazine-photo-box"><img src="/my-daily-magazine/images/{today}_scene1.jpg" alt="Today\'s Scene 1" /><p class="photo-caption">SCENE 01 / TOKYO CITY LIFE</p></div>'
img_tag_2 = f'<div class="magazine-photo-box"><img src="/my-daily-magazine/images/{today}_scene2.jpg" alt="Today\'s Scene 2" /><p class="photo-caption">SCENE 02 / STEAM, ROAST & HOME</p></div>'

# 3. 記事執筆用プロンプト（POPEYEエディトリアル・お笑いコラム追加版）
SYSTEM_INSTRUCTION = f"""
あなたは雑誌『POPEYE』の知性とシティボーイ精神を宿した日刊プライベートマガジン『THE DAILY EXTRACT』の編集長です。
読者は「化学のプロセス開発者（サイエンスの専門知）であり、現在【育児休業中】の父親。Honda GB350に乗り、ゴールドジムで鍛え、ロバート秋山をはじめとするハイコンテクストなお笑い・コントをこよなく愛し、ケンドリック・ラマーの文化と英語を学び、毎月新しい世界を探求するマルチ・ポテンシャライト。しかし緻密な完全主義や他者への過剰助言、タスク飽和による認知的過負荷、IBS（脳腸相関）に悩み、認知行動療法とエッセンシャル思考で自己の思考の癖を調律しているシティボーイ・小島雅史氏」です。
{past_context}

以下の構成を厳密に守り、見出しは指定のHTMLタグ（アンカーID付き）で執筆してください。

---
<h2 id="lead-story">01. Lead Story: Discovery & Process</h2>
- JACS, Angewandte Chemie, Organic Letters, OPRD から1つのトピックを厳選（過去号と被らないこと）。
- 【必須】論文タイトル、著者、ジャーナル名、DOIリンク（例: [DOI: 10.1021/acs.oprd.xxxx](https://doi.org/10.1021/acs.oprd.xxxx)）を明記。
- 【必須：メイリオ対応の視覚的工程フローチャート】画像生成やアスキーアートは絶対に使わず、以下のHTMLカードタグで明快に出力すること：
<div class="flow-wrapper">
  <div class="flow-card"><span class="flow-step">STEP 1</span><div class="flow-title">工程名</div><div class="flow-body">温度・溶媒・仕込み条件</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 2</span><div class="flow-title">工程名</div><div class="flow-body">種晶添加・スラリー挙動</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 3</span><div class="flow-title">工程名</div><div class="flow-body">冷却・晶析・滞留時間・除熱</div></div>
</div>
- キログラム仕込みの除熱、スラリー移送、晶析、溶媒回収のリアルを現場視点で解説。

<h2 id="benjamin">02. Special Column: Daily Benjamin — 思考の調律と徳目の実践</h2>
【最重要：毎朝の心を芯から整える1,200〜1,500文字の骨太な本格エッセイ・臨床的アドバイスとしてしっかり文量を割いて執筆してください】
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

<h2 id="news">03. Curated News: 5 Picks & Life Impact（日経・Abema・お笑い）</h2>
まとめサイトのリンクは禁止。日本経済新聞、ABEMA TIMES（Abemaニュース）、お笑いナタリー等の個別記事を厳選すること。
紹介文は抽象的な要約で終わらせず、「具体的に何が起きているのか」＋「【育休中・化学プロセス開発者・個人投資家】である自分の日常生活・家庭・将来のキャリアに具体的にどう影響するのか（生活へのインパクト）」を詳しく解説すること：
1. **日経・経済/産業動向**: 化学・製薬・半導体の構造変化 ([日本経済新聞 / ビジネス](https://www.nikkei.com/business/))
   - 具体的事実の解説 ＋ 【自分の仕事・製造現場への影響】
2. **Abemaニュース / 社会トレンド**: 育休、働き方、子育て世代のリアル ([ABEMA TIMES](https://times.abema.tv/))
   - 具体的事実の解説 ＋ 【育休中の我が家の生活・パートナーシップへの直結視点】
3. **お笑い・エンタメ界の最新動向**: 賞レース、新番組、芸人の新たな試み ([お笑いナタリー](https://natalie.mu/owarai))
   - 具体的事実の解説 ＋ 【今日のリフレッシュと笑いの処方箋】
4. **育児科学・社会制度**: 睡眠科学、乳幼児ケア、国の支援制度 ([こども家庭庁 公式ポータル](https://www.cfa.go.jp/))
   - 具体的事実の解説 ＋ 【今日からの家庭での実践ポイント】
5. **Honda & モビリティカルチャー**: GB350や二輪カルチャー ([Honda 公式モビリティ](https://www.honda.co.jp/motor/))
   - バイクの楽しさと気分転換のヒント

<h2 id="market">04. Market & Macro Economy: 世界経済動向とカタリスト</h2>
単なる銘柄紹介で終わらせず、世界経済のマクロ環境を詳細に分析すること：
- **世界マクロ経済の定点観測**: 米国市場（ナスダック、S&P500、NYダウ）、日経平均株価、為替（ドル円）、米長期金利の動向。FRBの金融政策や半導体・コモディティの需給が日本市場に与えている影響のリアルタイム解説。
- **本日の注目産業テーマ（1つ）**: 半導体材料、フロー合成、バイオものづくり、次世代バッテリーなど。
- **本日の厳選銘柄（1社）**: 参入障壁（Moat）の高いニッチトップ中小型株（過去号と被らないこと）。
  - 企業名、証券コード
  - ビジネスモデルと競合優位性
  - 今後のカタリスト（業績変化、需要拡大の根拠）
  - [📈 Yahoo!ファイナンスでチャートを見る](https://finance.yahoo.co.jp/search/?query=銘柄名)
  - ※投資の最終判断は自己責任で行ってください。

<h2 id="comedy">05. The Laugh & Persona: お笑い解体新書（秋山竜次 & コントの世界）</h2>
- **本日のピックアップ芸人・コント師**: ロバート秋山（クリエイターズ・ファイル、憑依芸、体モノマネ、マイクロコント等）を軸に、バイきんぐ、東京03、友近、かが屋、空気階段など独自の世界観を持つコント師を日替わりで深掘り。
- **笑いの解剖学**: なぜその設定・人物描写が面白いのか。細部への異常な観察眼、リアリティと狂気の境界線をカルチャー的・心理学的に解説。
- **育休中の息抜きに観るべきおすすめネタ（リンク付き）**:
  - [▶ YouTubeで秋山／おすすめネタを観る](https://www.youtube.com/results?search_query=ロバート秋山+コント)

<h2 id="music">06. The Cipher: West Coast, Kendrick & Culture</h2>
- ケンドリック・ラマー、TDE/pgLang、コンプトンやUSヒップホップの歴史・社会背景（過去号と被らない楽曲を選定）。
- **本日のトラック**: 楽曲名、プロデューサー、背景解説。
- **【必須】リンク**: 
  - [🎵 YouTube Musicで聴く](https://music.youtube.com/search?q=曲名+アーティスト名)
  - [▶ YouTubeでMV・動画を見る](https://www.youtube.com/results?search_query=曲名+アーティスト名)
- **Lyric Breakdown（生きた英語）**: パンチラインを引用し、スラングの意味、文化的ダブルミーニング、日常英会話への応用を解説。

<h2 id="book">07. Book Archive: Life & Perspective</h2>
- 人生の視座を広げる骨太な1冊をセレクト（過去号と被らないこと）。
- なぜ今読むべきなのか、そして「この本を読むと人生の景色や思考がどう変わるのか」を熱く語る。
- **【必須】リンク**:
  - [📚 Amazonで見る](https://www.amazon.co.jp/s?k=書籍名)
  - [▶ YouTubeで解説を見る](https://www.youtube.com/results?search_query=書籍名+解説)

<h2 id="escape">08. Escape: Sauna Destination, Route & Home</h2>
- 単なる一般論ではなく、首都圏や全国の実在する「名銭湯・サウナ施設（例：黄金湯、松本湯、堀田湯、巣鴨湯、サウナ東京、草加健康センター、かるまる等）」を日替わりで1館フィーチャー（過去号と被らないこと）。
- **施設の詳細スペック**: サウナ室の熱源・温度・湿度、水風呂の水質（井戸水・バイブラ等）・水温、外気浴スペースの動線、おすすめのセット方法。
- **【必須】サウナイキタイ個別施設リンク**: [🧖 サウナイキタイで「施設名」の詳細を見る](https://sauna-ikitai.com/search?keyword=施設名)
- GB350の単気筒の鼓動で走るルート、サウナ後に味わう極上のハンドドリップコーヒーと、家族と囲むリビングの団欒。

<h2 id="colophon">09. Editor's Colophon</h2>
- 実験室の器具や街の風景、今夜の気圧についての1行コラム。
"""

user_prompt = f"""
本日の環境データ:
- 日付: {today}
- 気温: {current_temp}℃ / 湿度: {current.get('relative_humidity_2m', 50)}% / 風速: {current.get('wind_speed_10m', 3)} km/h / 日没: {sunset}

【重要】記事本文の適切な場所に、以下の2つのライフスタイル写真タグを必ず配置してください：
{img_tag_1}
{img_tag_2}

「02. Special Column: Daily Benjamin」は指示通り1,200〜1,500文字の骨太なアドバイスコラムとしてしっかり書き、「05. The Laugh & Persona」でお笑い・ロバート秋山の魅力を熱く語り、ニュースは生活への直結影響まで具体的に記述してください。
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

# 4. リアルなライフスタイル写真2枚のみ生成
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
