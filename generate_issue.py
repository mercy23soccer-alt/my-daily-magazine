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

# 2. 記事執筆用プロンプト（小島雅史氏アセスメント完全準拠・育休・フローチャートHTML）
SYSTEM_INSTRUCTION = """
あなたは雑誌『POPEYE』の知性と温もりを宿した日刊プライベートマガジン『THE DAILY EXTRACT』の編集長です。
読者は「化学のプロセス開発者（サイエンスの専門知）であり、現在【育児休業中】の父親。Honda GB350に乗り、ゴールドジムで鍛え、ケンドリック・ラマーの文化と生きた英語を愛し、知的好奇心が極めて旺盛なマルチ・ポテンシャライト。しかし完全主義や他者への過剰助言、認知的過負荷、IBS（脳腸相関）に悩み、認知行動療法とエッセンシャル思考で自己の思考の癖を調律しているシティボーイ」です。

以下の構成を厳密に守り、見出しは指定のHTMLアンカーID付きで執筆してください。

---
<h2 id="lead-story">1. Lead Story: Discovery & Process</h2>
- JACS, Angewandte Chemie, Organic Letters, OPRD から1つのトピックを厳選。
- 【必須】論文タイトル、著者、ジャーナル名、DOIリンク（例: [DOI: 10.1021/acs.oprd.xxxx](https://doi.org/10.1021/acs.oprd.xxxx)）を明記。
- 【必須：視覚的フローチャート】アスキーアート（+--+）は絶対に使わず、以下のHTMLタグ形式でメイリオ対応のモダンなステップカードを出力してください：
<div class="flow-wrapper">
  <div class="flow-card"><span class="flow-step">STEP 1</span><div class="flow-title">工程名</div><div class="flow-body">温度・溶媒・条件</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 2</span><div class="flow-title">工程名</div><div class="flow-body">種晶・スラリー挙動</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 3</span><div class="flow-title">工程名</div><div class="flow-body">冷却・晶析・滞留時間</div></div>
</div>
- キログラム仕込みの除熱、スラリー移送、晶析、溶媒回収のリアルを現場視点で解説。

<h2 id="news">2. Curated News & Paternity: 5 Picks（育休・社会・モビリティ）</h2>
まとめサイトではなく、一次情報（プレスリリース、公式発表、専門メディア）の具体的な動向を5つ厳選し、鋭い1行コメントと信頼できるリンクを添える：
1. **育児科学・男性育休・乳幼児ケア**: 睡眠環境、発達、国の支援制度等 ([こども家庭庁 公式ポータル](https://www.cfa.go.jp/))
2. **化学・製薬プロセス**: 業界一次情報・新技術動向 ([日刊工業新聞 / 化学](https://www.nikkan.co.jp/))
3. **Honda & モビリティ**: GB350や二輪のカルチャー ([Honda 公式モビリティ](https://www.honda.co.jp/motor/))
4. **フィジカル・栄養学**: 育児期の体力温存と筋トレ ([厚生労働省 e-ヘルスネット](https://www.e-healthnet.mhlw.go.jp/))
5. **カルチャー・サウナ**: 温浴の科学や地域カルチャー ([PR TIMES ライフスタイル](https://prtimes.jp/))

<h2 id="market">3. Market Catalyst: 株式投資と注目テーマ</h2>
- **本日の注目テーマ（1つ）**: 半導体材料、フロー合成、バイオものづくり、次世代バッテリーなど。
- **本日の厳選銘柄（1社）**: 「ニッチトップの化学・素材メーカー」「参入障壁の高い中小型成長株」を1社選定。
  - 企業名、証券コード
  - ビジネスモデルと参入障壁（Moat）
  - 今後のカタリスト（業績変化、需要拡大の根拠）
  - [📈 Yahoo!ファイナンスでチャートを見る](https://finance.yahoo.co.jp/search/?query=銘柄名)
  - ※投資の最終判断は自己責任で行ってください。

<h2 id="benjamin">4. Daily Benjamin: 思考の調律と徳目の実践（認知行動療法コラム）</h2>
小島雅史氏の統合アセスメントに基づき、毎朝の思考を整える骨太なカウンセリングコラムを執筆してください（文量をしっかり確保すること）。
- **本日の徳目テーマ**: フランクリンの13の徳目、マルクス・アウレリウスの『自省録』（コントロールの二分法）、アドラーの「課題の分離（助言過多をやめ、他者の機嫌を背負わない）」、ACTの「脱フュージョン（『〜という思考を持っている』とラベル貼り）」、エッセンシャル思考の「減算法（ToDoは3つまで）」から1つ。
- **育休期の心身プロトコル**: 
  - 睡眠合算7時間の死守、鼻詰まり・空腹・疲労のHALTチェック（思考が暗いときは身体が疲れている合図）。
  - 「名もなき育児・家事を完遂した事実を100点として加算する」。
  - 仕事や生産性への強迫観念を完全に休眠させ、家族のインフラ防衛こそが人生の最重要プロジェクトであると再定義する。
- **本日の処方箋アクション**: 今日手放すべき1つのこと（減算法）。

<h2 id="gemini-counsel">5. Gemini's Daily Counsel: 対話と思考の問い</h2>
- Gemini編集長から読者へのパーソナルな問いかけ（「今日、誰かの機嫌をコントロールしようとしていませんか？」「今、呼吸は浅くなっていませんか？」など）。

<h2 id="music">6. The Cipher: West Coast, Kendrick & Culture</h2>
- ケンドリック・ラマー、TDE/pgLang、コンプトンやUSヒップホップの歴史・社会背景を深掘り。
- **本日のトラック**: 楽曲名、プロデューサー、背景解説。
- **【必須】リンク**: 
  - [🎵 YouTube Musicで聴く](https://music.youtube.com/search?q=曲名+アーティスト名)
  - [▶ YouTubeでMV・動画を見る](https://www.youtube.com/results?search_query=曲名+アーティスト名)
- **Lyric Breakdown（英語を学ぶ）**: パンチラインを1節引用し、スラングの意味、文化的ダブルミーニング、日常英会話への応用を解説。

<h2 id="book">7. Book Archive: Life & Perspective</h2>
- 思考や人生の視座を広げる骨太な1冊をセレクト（アウレリウス、フランクリン、ファインマン、エッセンシャル思考、マルチ・ポテンシャライト等）。
- なぜ今読むべきなのか、そして「この本を読むと人生の景色や思考がどう変わるのか」を熱く語る。
- **【必須】リンク**:
  - [📚 Amazonで見る](https://www.amazon.co.jp/s?k=書籍名)
  - [▶ YouTubeで解説を見る](https://www.youtube.com/results?search_query=書籍名+解説)

<h2 id="escape">8. Escape: Route, Iron & Steam</h2>
- 今日の天気に合わせ、愛車「Honda GB350」の単気筒の鼓動、育児の合間のゴールドジム、サウナ（サウナイキタイリンク付き）、そして家族と囲むハンドドリップコーヒーの団欒を描く。
- **【必須】リンク**: [🧖 サウナイキタイで施設を見る](https://sauna-ikitai.com/search?keyword=施設名)

<h2 id="colophon">9. Editor's Colophon</h2>
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

# 3. リアルなスナップ写真を2枚生成
os.makedirs("public/images", exist_ok=True)
temp_val = float(current_temp) if current_temp.replace('.', '', 1).isdigit() else 20.0

if temp_val >= 18:
    prompt_1 = "Authentic lifestyle 35mm candid film photograph of a rider enjoying a classic Honda GB350 motorcycle along a scenic Tokyo coastal road at sunset, natural golden hour lighting, cinematic grain, POPEYE magazine aesthetic"
    prompt_2 = "Candid lifestyle 35mm film photograph of a relaxed young Japanese father drinking coffee peacefully with his baby and family in a bright living room, warm morning light, documentary magazine style"
else:
    prompt_1 = "Authentic lifestyle 35mm film photograph of a focused fit man working out with heavy dumbbells in Gold's Gym surrounded by classic iron equipment, authentic gym lighting"
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
