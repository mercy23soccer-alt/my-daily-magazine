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
ウェブマガジン『ZAZZY | Paternity, Culture & Mind』の本日号を作成してください。

以下の14セクションを必ず含めてMarkdown形式で執筆してください：
## 01. LEAD STORY: CHEMICAL LITERATURE (厳選3選)
- 連続生産技術、フロー合成、遷移金属触媒等の最新プロセス化学論文3選（著者・ジャーナル、DOI、反応設計とメカニズム、基質許容性、プロセス化学・スケールアップ視点）

## 02. SPECIAL COLUMN: DAILY BENJAMIN — 思考の調律と東西哲学の実践
- 育児休業、ヴィクトール・フランクル等の態度価値、日常の尊厳に関する深いエッセイ

## 03. NICHE STOCK ANALYSIS: 注目のニッチ個別株
- 精密化学・半導体材料等の高参入障壁を持つ優良企業1社（事業内容、参入障壁Moat、カタリスト）

## 04. CURATED NEWS & MACRO: 世界経済と暮らしのインパクト
- 先端サプライチェーン、育児インフラ、マクロ為替動向

## 05. BABY & PATERNITY: 赤ちゃん関連の重要情報（厳選3選）
- 離乳食、共同注意、睡眠科学などの小児エビデンス3選

## 06. THE COMEDY UNDERGROUND: コア芸人おすすめネタ紹介（厳選3選）
- 個性派・実力派芸人のネタ解説

## 07. CURIOSITY EXPEDITION: 未知なる世界への招待
- 規矩術、伝統工芸、精密幾何学などの構造美コラム

## 08. IRON & FORM: 筋トレと身体操作のサイエンス
- ベンチプレス等の解剖学・力学に基づくフォーム解説

## 09. MOTO CHRONICLE: 歴史を刻む名車の肖像
- 空冷・メカニズムの美しい名車バイクの肖像

## 10. SAUNA SPEC & DESTINATION: 究極の温冷巡礼
- 実在の名サウナ施設（サウナ室温度、水風呂水温、ととのい動線）

## 11. EVIDENCE WELLNESS: 最新論文が教える心身の整え方
- 迷走神経、腸内環境等の医学論文解説と日常実践法

## 12. BOOK ARCHIVE: 人生を揺らすオススメの小説
- 人生の深みを味わう小説・純文学の推薦

## 13. SOUNDTRACK OF THE DUSK: 音楽と英語（HIP-HOP & SOUL ARCHIVE）
- 名曲紹介とリリックの英語表現・ダブルミーニング解説

## 14. EDITOR'S COLOPHON: 編集後記
- 夕暮れの情景、気温、読者への静かなメッセージ
"""

    # 低コストかつ高速な最新モデルを指定（max_output_tokens で無駄な長文課金を抑制）
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
