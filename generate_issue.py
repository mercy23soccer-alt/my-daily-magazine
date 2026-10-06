import os
import sys
from datetime import datetime
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("Error: GEMINI_API_KEY is not set.")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

def generate_issue():
    today = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""
本日の日付: {today}
ウェブマガジン『ZAZZY | Paternity, Culture & Mind』の本日号（Markdown形式）を作成してください。

以下の各セクション見出しと構成を厳格に含めてください：
## 01. LEAD STORY: CHEMICAL LITERATURE (厳選3選)
- 連続フロー合成、遷移金属触媒、プロセス化学の最新論文3報（著者、ジャーナル、反応機構、プロセス化学視点）

## 02. SPECIAL COLUMN: DAILY BENJAMIN — 思考の調律と東西哲学の実践
- 育児休業、態度価値、日常の尊厳に関する深い哲学的エッセイ

## 03. NICHE STOCK ANALYSIS: 注目のニッチ個別株
- 精密化学・半導体材料等の高参入障壁を持つニッチ優良企業1社（事業内容、Moat、カタリスト）

## 04. CURATED NEWS & MACRO: 世界経済と暮らしのインパクト
- 先端サプライチェーン、育児と家計、為替動向の3大トピック

## 05. BABY & PATERNITY: 赤ちゃん関連の重要情報（厳選3選）
- 乳児の発達、睡眠科学、育児のエビデンス情報3点

## 06. THE COMEDY UNDERGROUND: コア芸人おすすめネタ紹介（厳選3選）
- 知的・個性派芸人のネタ解説3選

## 07. CURIOSITY EXPEDITION: 未知なる世界への招待
- 伝統技術や構造美（例: 規矩術、精密工学など）の知的好奇心コラム

## 08. IRON & FORM: 筋トレと身体操作のサイエンス
- ベンチプレス等の解剖学的・力学的フォーム解説

## 09. MOTO CHRONICLE: 歴史を刻む名車の肖像
- 名車バイク（空冷・造形美）のメカニズムと魅力

## 10. SAUNA SPEC & DESTINATION: 究極の温冷巡礼
- 実在の名サウナ施設詳細スペック（サウナ室温度、水風呂、ととのい動線）

## 11. EVIDENCE WELLNESS: 最新論文が教える心身の整え方
- 自律神経、腸内環境等の医学・生化学論文解説

## 12. BOOK ARCHIVE: 人生を揺らすオススメの小説
- 人生の深みを味わう純文学・小説の推薦

## 13. SOUNDTRACK OF THE DUSK: 音楽と英語（HIP-HOP & SOUL ARCHIVE）
- 名曲の紹介とリリックの英語表現・ダブルミーニング解説

## 14. EDITOR'S COLOPHON: 編集後記
- 本日の気候・夕暮れの情景と読者へのメッセージ

※知的で洗練された語彙を用い、読み応えのある文量で記述してください。
"""

    # 404エラーを解消し、API利用料を最安クラスに抑える最新モデル
    config = types.GenerateContentConfig(
        temperature=0.7,
        max_output_tokens=6000,
        system_instruction=(
            "あなたは洗練された日刊ウェブマガジン『ZAZZY』の編集長です。"
            "プロセス化学、哲学、カルチャー、育児、身体論に精通した知的で品格のある文章を出力してください。"
        )
    )

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=config,
    )
    return response.text

def main():
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = "src/content/issues"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{today_str}.md")
    
    print(f"Generating full ZAZZY issue for {today_str}...")
    article_body = generate_issue()

    content = f"""---
title: "ZAZZY - {today_str}"
date: "{today_str}"
description: "A Magazine for Paternity, Culture & The City."
---

{article_body}
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Successfully created: {file_path}")

if __name__ == "__main__":
    main()
