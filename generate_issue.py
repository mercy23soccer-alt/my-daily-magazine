import base64
import glob
import io
import os
import random
import re
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
import requests
from PIL import Image
from google import genai

# 日本時間（JST）の厳格取得
JST = timezone(timedelta(hours=9))
now_jst = datetime.now(JST)
today = now_jst.strftime("%Y-%m-%d")

SECTION_ID_MAP = {
    "01": "lead-story",
    "02": "benjamin",
    "03": "niche-stock",
    "04": "news",
    "05": "baby",
    "06": "comedy",
    "07": "curiosity",
    "08": "workout",
    "09": "bike",
    "10": "sauna",
    "11": "evidence",
    "12": "novel",
    "13": "music",
    "14": "colophon",
}


def migrate_legacy_issues():
    """src/content/issues/ に残っている過去記事 (2026-10-06〜2026-10-13等) を
    src/content/posts/ に自動移行し、フロントマターと見出しIDを補完する。"""
    legacy_dir = "src/content/issues"
    target_dir = "src/content/posts"
    if not os.path.isdir(legacy_dir):
        return

    os.makedirs(target_dir, exist_ok=True)
    legacy_files = sorted(glob.glob(os.path.join(legacy_dir, "*.md")))
    if not legacy_files:
        return

    for src_path in legacy_files:
        filename = os.path.basename(src_path)
        date_str = filename.replace(".md", "")
        dst_path = os.path.join(target_dir, filename)

        if not os.path.exists(dst_path):
            with open(src_path, "r", encoding="utf-8") as f:
                raw = f.read()

            # フロントマターを分離して posts 用のメタデータを付与
            body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", raw, flags=re.DOTALL).strip()
            # 冒頭の重複タイトル行を整理
            body = re.sub(
                r"^(\*{0,2}『?ZAZZY.*?\n|\*?[Ii]ssue.*?\n|# ZAZZY.*?\n|---\s*\n)+",
                "",
                body,
            ).strip()

            # Markdown の `## 01. ...` 見出しを `<h2 id="...">` に変換
            def replace_h2(match):
                num = match.group(1)
                title_rest = match.group(2).strip()
                sec_id = SECTION_ID_MAP.get(num, f"sec-{num}")
                return f'<h2 id="{sec_id}">{num}. {title_rest}</h2>'

            body = re.sub(
                r"^##\s+(\d{2})\.\s*(.+)$",
                replace_h2,
                body,
                flags=re.MULTILINE,
            )

            frontmatter = f"""---
title: "Issue - {date_str}"
date: "{date_str}"
temp: "20.0°C"
sunset: "17:12"
wind: "3.5 km/h"
bike: "Honda GB350"
---

"""
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(frontmatter + body + "\n")
            print(f"✅ 旧ディレクトリから記事を移行しました: {src_path} -> {dst_path}")

        os.remove(src_path)

    # 空になった src/content/issues ディレクトリを削除
    if not os.listdir(legacy_dir):
        shutil.rmtree(legacy_dir, ignore_errors=True)
        print("✅ 旧ディレクトリ src/content/issues を整理しました。")


# 0. まず src/content/issues のバックナンバーを src/content/posts へ移行
migrate_legacy_issues()

api_key = os.environ.get("GEMINI_API_KEY")
client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Gemini初期化スキップ: {e}")

# 1. 天気の取得（失敗時もデフォルト値で安全に継続）
current_temp = "20"
sunset = "17:30"
current_wind = "3"
try:
    weather_res = requests.get(
        "https://api.open-meteo.com/v1/forecast?latitude=35.68&longitude=139.76&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m&daily=sunset&timezone=Asia%2FTokyo",
        timeout=15,
    ).json()
    current = weather_res.get("current", {})
    daily = weather_res.get("daily", {})
    current_temp = str(current.get("temperature_2m", "20"))
    sunset = daily.get("sunset", ["17:30"])[0].split("T")[-1]
    current_wind = str(current.get("wind_speed_10m", "3"))
except Exception as e:
    print(f"天気API取得スキップ（デフォルト値を使用）: {e}")

# 2. 【過去45日分】全記事から重複禁止トピックを自動抽出（入力トークン最適化）
past_posts = sorted(glob.glob("src/content/posts/*.md"), reverse=True)[:45]
past_used_topics = []

for p in past_posts:
    try:
        with open(p, "r", encoding="utf-8") as f:
            c = f.read()
            date_label = os.path.basename(p).replace(".md", "")
            items = []
            for line in c.splitlines():
                line_str = line.strip()
                if line_str.startswith("#") or line_str.startswith("<h2") or line_str.startswith("<h3"):
                    clean_h = re.sub(r"<[^>]+>|[#*]", "", line_str).strip()
                    if clean_h and not any(
                        k in clean_h
                        for k in [
                            "Chemical Literature",
                            "Lead Story",
                            "Special Column",
                            "Daily Benjamin",
                            "Niche Stock",
                            "Curated News",
                            "Baby & Paternity",
                            "The Comedy Underground",
                            "Curiosity Expedition",
                            "Iron & Form",
                            "Moto Chronicle",
                            "Sauna Spec",
                            "Evidence Wellness",
                            "Book Archive",
                            "Soundtrack",
                            "Editor's Colophon",
                        ]
                    ):
                        items.append(clean_h)
                elif any(
                    k in line_str
                    for k in ["ネタ", "芸人", "銘柄", "コード", "サウナ", "バイク", "小説", "曲", "DOI:", "STEP"]
                ):
                    bolds = re.findall(r"\*\*(.*?)\*\*", line_str)
                    if bolds:
                        items.extend(bolds[:2])
                    else:
                        clean_l = re.sub(r"<[^>]+>|\[.*?\]\(.*?\)|\*", "", line_str).strip()
                        if 3 < len(clean_l) < 45:
                            items.append(clean_l)

            seen = set()
            unique_items = [x for x in items if not (x in seen or seen.add(x))]
            if unique_items:
                past_used_topics.append(f"【{date_label}号】: " + " / ".join(unique_items[:6]))
    except Exception:
        pass

past_context = "\n".join(past_used_topics) if past_used_topics else "（過去90日間の記録なし）"

# 写真タグ定義
img_tag_1 = f'<div class="magazine-photo-box"><img src="/my-daily-magazine/images/{today}_scene1.jpg" alt="Today\'s Scene 1" /><p class="photo-caption">SCENE 01 / TOKYO CITY & MACHINE</p></div>'
img_tag_2 = f'<div class="magazine-photo-box"><img src="/my-daily-magazine/images/{today}_scene2.jpg" alt="Today\'s Scene 2" /><p class="photo-caption">SCENE 02 / STEAM, ROAST & HOME</p></div>'

# 3. 執筆プロンプト
SYSTEM_INSTRUCTION = f"""
あなたは雑誌『POPEYE』『BRUTUS』『WIRED』の知性と美学を宿した日刊カルチャー誌『ZAZZY』の編集長です。
読者は「化学のプロセス開発者（サイエンスの専門知）であり、現在【育児休業中】の父親。Honda GB350に乗り、ゴールドジムで鍛え、深夜ラジオや尖ったお笑いを愛し、ヒップホップの文化と英語を学び、毎月新しい世界を探求するマルチ・ポテンシャライト。しかし緻密な完全主義やタスク飽和による認知的過負荷、IBS（脳腸相関）に悩み、心理学・東西哲学・知恵の体系で自己の思考と心持ちを調律しているシティボーイ・小島雅史氏」です。

【最重要：過去90日間に取り上げたトピック・固有名詞一覧】
以下の過去90日間に登場した「芸人、ネタ、論文、銘柄、書籍、サウナ施設、バイク車種、音楽、心理学・哲学テーマ」は絶対に重複・再使用しないでください：
{past_context}

【最重要執筆ルール】
1. **出力前セルフチェック**: あなたは出力を行う前に、以下の全14セクションがすべて揃っており、上記の過去90日間の記録と一切被りがないかを内部で厳密に確認してください。
2. **お笑いリサーチの広域化**: 特定の芸人に固執することは固く禁じます。ベテラン演芸・落語・漫談、90〜00年代の実力派、各賞レース（M-1, KOC, R-1, THE W, ABCお笑いGP, ツギクル芸人GP）ファイナリスト、下北沢・神保町などの劇場インディーズ、**大学お笑いサークル（早稲田寄席研、慶応O-keis、明治木曜会、東大落研等）出身の気鋭若手、アマチュアや地方発の異才**まで、時代とジャンルを広くリサーチし、過去90日間に登場していない3組・3ネタを厳選してください。各ネタの解説直後に個別YouTubeリンクを明記すること。
3. **思考調律・哲学の多角的深化**: 「脱フュージョン」「減算法」「HALT」などの決まり文句の固定化を完全禁止します。心理学（ACT、ロゴセラピー、アドラー、セルフコンパッション、ポジティブ心理学等）、西洋哲学（ストア派、エピクロス、スピノザ、モンテーニュ、実存主義、プラグマティズム等）、仏教（禅の放下着・喫茶去、唯識、中道、空、縁起等）、儒教・東洋思想（中庸、知足、無為自然等）から、過去90日間で取り上げていない思想体系を日替わりで主軸に据え、育休期の父親がどのような心持ちで今日を過ごすべきかを骨太な文学的エッセイで語ってください。
4. **化学用語の比喩禁止**: 「除熱」「触媒」「スラリー」「晶析」などの理系用語を、心理や日常の比喩として使うことは一切禁止。
5. **本文冒頭のメタデータ禁止**: 「TITLE:」「DATE:」などの文字列は出力せず、いきなり「01. Lead Story」から書き始めること。

見出し構成（全14セクション完全網羅）：
---
<h2 id="lead-story">01. Lead Story: Chemical Literature (厳選3選)</h2>
OPRD, JACS, Angewandte Chemie, Nature Synthesis 等から異なるジャーナルの論文を3本厳選（過去90日間と被らないこと）。
前置きは1〜2行で簡潔にまとめ、各論文について「論文名・著者・ジャーナル名・DOIリンク」「反応設計とメカニズムの核心」「基質適用性と官能基許容性」「プロセス化学・スケールアップ視点（連続化・晶析・不純物パージ・安全性等）」を詳細に解説すること。
以下のフローチャートHTMLを独立ブロックとして出力すること：
<div class="flow-wrapper">
  <div class="flow-card"><span class="flow-step">STEP 1</span><div class="flow-title">工程名</div><div class="flow-body">条件・溶媒・設定</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 2</span><div class="flow-title">工程名</div><div class="flow-body">結晶化・制御ポイント</div></div>
  <div class="flow-arrow">➔</div>
  <div class="flow-card"><span class="flow-step">STEP 3</span><div class="flow-title">工程名</div><div class="flow-body">分離・精製・収率</div></div>
</div>

<h2 id="benjamin">02. Special Column: Daily Benjamin — 思考の調律と東西哲学の実践</h2>
【1,200〜1,500文字の骨太本格エッセイ】
過去90日間のテーマと被らない心理学・哲学（例：ストア派の自制、スピノザの能動、禅の放下着、セルフ・コンパッションの友愛、老荘の無為自然、モンテーニュの随想等）を1つ深く掘り下げる。
育休中の認知的焦燥やタスク過多、IBS（脳腸相関）に向き合い、家庭の生活インフラを支え抜く尊さを確信し、内なる心理的安全性を高めて穏やかに一日を過ごすための精神的処方箋を論理的かつ温かく説く。

<h2 id="niche-stock">03. Niche Stock Analysis: 注目のニッチ個別株</h2>
参入障壁（Moat）の高い日本のニッチトップ中小型銘柄を1社厳選（過去90日間と被らないこと）。コアコンピタンス、強み、直近カタリスト、定量的な優位性を解説。
- [📈 Yahoo!ファイナンスでチャートを見る](https://finance.yahoo.co.jp/search/?query=銘柄名)

<h2 id="news">04. Curated News & Macro: 世界経済と暮らしのインパクト</h2>
日経・Abemaニュース・世界マクロ市況を、技術者・投資家・育休パパ視点での生活インパクトとして解説。
- [日本経済新聞 / ビジネス](https://www.nikkei.com/business/)
- [ABEMA TIMES](https://times.abema.tv/)

<h2 id="baby">05. Baby & Paternity: 赤ちゃん関連の重要情報（厳選3選）</h2>
睡眠・栄養・脳発達・感覚遊び・夫婦のメンタルヘルスなど幅広いエビデンスから過去号と被らない3点解説：
1. **知見1** ([こども家庭庁](https://www.cfa.go.jp/))
2. **知見2** ([日本小児科学会](https://www.jpeds.or.jp/))
3. **知見3** ([厚生労働省 e-ヘルスネット](https://www.e-healthnet.mhlw.go.jp/))

<h2 id="comedy">06. The Comedy Underground: コア芸人おすすめネタ紹介（厳選3選）</h2>
ベテランから気鋭の若手、大学お笑い出身、アマチュアまで幅広くリサーチし、過去90日間で一度も紹介されていない3組・3ネタを紹介。
各ネタの解説文の直後に、それぞれ個別のYouTubeリンクを配置すること：
- **ネタ1の紹介と解説**
  - [▶ YouTubeで「芸人名 ネタ名」を見る](https://www.youtube.com/results?search_query=芸人名+ネタ名)
- **ネタ2の紹介と解説**
  - [▶ YouTubeで「芸人名 ネタ名」を見る](https://www.youtube.com/results?search_query=芸人名+ネタ名)
- **ネタ3の紹介と解説**
  - [▶ YouTubeで「芸人名 ネタ名」を見る](https://www.youtube.com/results?search_query=芸人名+ネタ名)

<h2 id="curiosity">07. Curiosity Expedition: 未知なる世界への招待</h2>
普段の関心から外れた未開拓領域（現代アート、塊根植物、時計機構、建築、発酵、民族音楽等）の深掘り。

<h2 id="workout">08. Iron & Form: 筋トレと身体操作のサイエンス</h2>
解剖学・力学に基づくフォーム改善とゴールドジムでの実践知。

<h2 id="bike">09. Moto Chronicle: 歴史を刻む名車の肖像</h2>
愛車GB350以外の歴史的名車・名機を日替わりで1台フィーチャー（過去90日間と絶対に被らないこと）。
エンジン形式の鼓動感、吸排気設計、時代背景、開発者の思想を熱量高く描写。

<h2 id="sauna">10. Sauna Spec & Destination: 究極の温冷巡礼</h2>
実在する名サウナ施設を1館厳選（過去90日間と被らないこと）。スペックに徹底フォーカスして解説（サウナ室温度・熱源、水風呂水温・水質・深さ、外気浴動線）。
- [🧖 サウナイキタイで詳細を見る](https://sauna-ikitai.com/)

<h2 id="evidence">11. Evidence Wellness: 最新論文が教える心身の整え方</h2>
PubMed論文に基づく睡眠・自律神経・脳腸相関（IBS）の最新知見。
- [🔬 PubMed最新研究を検索](https://pubmed.ncbi.nlm.nih.gov/)

<h2 id="novel">12. Book Archive: 人生を揺らすオススメの小説</h2>
感性を刺激する骨太な名作小説を1冊セレクト（過去90日間と被らないこと）。あらすじと今読むべき理由。
- [📚 Amazonで見る](https://www.amazon.co.jp/)

<h2 id="music">13. Soundtrack of the Dusk: 音楽と英語（Hip-Hop & Soul Archive）</h2>
Kendrick Lamar、Nas、J. Cole、2Pac、Mac Miller、Tyler, The Creator、Anderson .Paak、A Tribe Called Quest 等から過去90日間と被らない名曲を1曲。
時代背景、ビートの美学、**「Lyric Breakdown（生きた英語）」**としてのスラング・ダブルミーニング解説。
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
全14セクションが揃っており、過去記事のトピックと重複が一切ないことを点検してからMarkdown形式で出力してください。
また、14セクションすべてを出力した一番最後に、本日の記事内容に合った雑誌POPEYE風35mmフィルム写真用の英語プロンプト（1文）を以下の2行の形式で添えてください（1つ目は紹介したバイクや都市の機械美、2つ目はサウナ・珈琲・住まいのシーン）：
PROMPT1: <英語プロンプト1>
PROMPT2: <英語プロンプト2>
"""


def generate_text_with_gemini(prompt_str, sys_inst=None, thinking_level="low"):
    """最新の Interactions API (gemini-3.8-flash / gemini-4-argon) を優先使用し、
    万が一古い SDK 環境の場合もフォールバックで対応するヘルパー。"""
    if not client:
        return None

    for model_name in ["gemini-3.8-flash", "gemini-4-argon"]:
        try:
            kwargs = {
                "model": model_name,
                "input": prompt_str,
                "generation_config": {
                    "thinking_level": thinking_level,
                    "max_output_tokens": 32768,
                },
            }
            if sys_inst:
                kwargs["system_instruction"] = sys_inst

            interaction = client.interactions.create(**kwargs)
            if interaction and interaction.output_text:
                return interaction.output_text
        except Exception as e:
            print(f"⚠️ Interactions API ({model_name}) スキップ: {str(e)[:120]}")

    return None


response_text = None

if client:
    print("--- Gemini Interactions API (省エネ・1回統合モード) で執筆を試行中 ---")
    text_out = generate_text_with_gemini(
        user_prompt, sys_inst=SYSTEM_INSTRUCTION, thinking_level="low"
    )
    if text_out and len(text_out) > 1400:
        print("✅ 成功: Gemini APIでフルボリューム記事が完成しました！")
        response_text = text_out

if not response_text:
    print("--- バックアップAIエンジンで執筆中 ---")
    try:
        combined_prompt = f"{SYSTEM_INSTRUCTION}\n\n---\n{user_prompt}"
        payload = {
            "messages": [{"role": "user", "content": combined_prompt}],
            "model": "openai",
            "seed": int(time.time()),
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

# 記事末尾から PROMPT1 / PROMPT2 を抽出し、本文からは除去する（API呼び出し1回化）
prompt_1 = "Authentic lifestyle 35mm candid film photograph of a classic motorcycle parked along a scenic coastal highway in Japan at sunset, cinematic golden hour lighting, mechanical beauty, POPEYE magazine aesthetic"
prompt_2 = "Candid lifestyle 35mm film photograph of a cozy Japanese sauna resting space with steam, aromatic cedar wood, relaxed peaceful atmosphere, POPEYE magazine documentary style"

m1 = re.search(r"^PROMPT1:\s*(.+)$", response_text, flags=re.MULTILINE)
m2 = re.search(r"^PROMPT2:\s*(.+)$", response_text, flags=re.MULTILINE)
if m1:
    prompt_1 = (
        m1.group(1).strip()
        + ", authentic 35mm film photography, cinematic grain, POPEYE magazine style"
    )
if m2:
    prompt_2 = (
        m2.group(1).strip()
        + ", authentic 35mm film photography, natural lighting, candid documentary style"
    )

clean_text = re.sub(
    r"^PROMPT[12]:.*?\n?", "", response_text, flags=re.MULTILINE
).strip()
clean_text = re.sub(
    r"^(title:.*?\n|TITLE:.*?\n|date:.*?\n|DATE:.*?\n|temp:.*?\n|TEMP:.*?\n|sunset:.*?\n|SUNSET:.*?\n|wind:.*?\n|WIND:.*?\n|bike:.*?\n|BIKE:.*?\n)+",
    "",
    clean_text,
    flags=re.MULTILINE | re.IGNORECASE,
).strip()

# 万が一 Markdown の `## 01. ...` 形式で出力された場合も `<h2 id="...">` に自動正規化
def normalize_h2(match):
    num = match.group(1)
    title_rest = match.group(2).strip()
    sec_id = SECTION_ID_MAP.get(num, f"sec-{num}")
    return f'<h2 id="{sec_id}">{num}. {title_rest}</h2>'


clean_text = re.sub(
    r"^##\s+(\d{2})\.\s*(.+)$",
    normalize_h2,
    clean_text,
    flags=re.MULTILINE,
)

if '<div class="flow-wrapper">' in clean_text:
    parts = clean_text.split('<div class="flow-wrapper">')
    reconstructed = parts[0]
    for p in parts[1:]:
        if "</div>" not in p or p.find("</div>") > 1000:
            p = p.replace("\n\n", "</div>\n\n", 1)
        reconstructed += '<div class="flow-wrapper">' + p
    clean_text = reconstructed

# 4. 画像の生成完了確認（2枚揃ってから記事出力へ進む）
os.makedirs("public/images", exist_ok=True)

scenes = [
    (prompt_1, f"public/images/{today}_scene1.jpg"),
    (prompt_2, f"public/images/{today}_scene2.jpg"),
]


def generate_and_save_photo(prompt_text, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # A. Pollinations AI (Flux 無料エンジン・最大3回リトライ、60秒タイムアウト)
    clean_prompt = quote(prompt_text)
    for attempt in range(1, 4):
        try:
            seed_val = int(time.time()) + random.randint(1000, 99999)
            url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1200&height=675&nologo=true&seed={seed_val}"
            print(f"画像生成試行中 ({attempt}/3): {file_path}")
            r = requests.get(url, timeout=60)
            if r.status_code == 200 and len(r.content) > 5000:
                with open(file_path, "wb") as f:
                    f.write(r.content)
                img = Image.open(file_path)
                img.verify()
                print(
                    f"✅ フォトエンジンで生成完了: {file_path} ({os.path.getsize(file_path)} bytes)"
                )
                return True
        except Exception as ex:
            print(f"⚠️ 画像生成リトライ中 ({attempt}/3): {ex}")
            time.sleep(5)

    # C. 高品質フォールバック写真の保存（欠落の完全防止）
    try:
        r = requests.get("https://picsum.photos/1200/675", timeout=30)
        if r.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(r.content)
            print(f"⚠️ バックアップ写真で保存完了: {file_path}")
            return True
    except Exception as e:
        print(f"フォールバック失敗: {e}")

    return False


print("=== 画像生成プロセス開始 ===")
for idx, (p_text, s_path) in enumerate(scenes):
    success = generate_and_save_photo(p_text, s_path)
    if not success or not os.path.exists(s_path) or os.path.getsize(s_path) < 1000:
        dummy = Image.new("RGB", (1200, 675), color=(25, 35, 45))
        dummy.save(s_path, "JPEG")
        print(f"⚠️ プレースホルダー画像を配置: {s_path}")
    if idx < len(scenes) - 1:
        print("2枚目の画像生成まで 6秒 待機します...")
        time.sleep(6)

# 2枚とも完全に揃っていることを検証
assert os.path.exists(scenes[0][1]) and os.path.getsize(scenes[0][1]) > 500, "Scene 1 is missing!"
assert os.path.exists(scenes[1][1]) and os.path.getsize(scenes[1][1]) > 500, "Scene 2 is missing!"
print("✅ すべての画像（SCENE 01 / SCENE 02）がディスクに生成完了しました。")

# 5. 画像生成が完了した後に、Markdown記事を保存して出力完了
os.makedirs("src/content/posts", exist_ok=True)
frontmatter_block = f"""---
title: "Issue - {today}"
date: "{today}"
temp: "{current_temp}°C"
sunset: "{sunset}"
wind: "{current_wind} km/h"
bike: "Honda GB350"
---

"""

file_path = f"src/content/posts/{today}.md"
with open(file_path, "w", encoding="utf-8") as f:
    f.write(frontmatter_block + clean_text + "\n")

print(f"Successfully published issue: {file_path}")
