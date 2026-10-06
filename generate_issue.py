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
日付: {today}
洗練された日刊ウェブマガジン『Zazzy』の本日の特集記事を作成してください。
【条件】
- テクノロジー、カルチャー、ライフスタイルから関心トピック2〜3件
- 知的で引き締まった文章構成
- 各見出しはMarkdown（## や ###）を使用
"""
    config = types.GenerateContentConfig(
        temperature=0.7,
        max_output_tokens=1500,
        system_instruction="あなたは洗練されたカルチャー＆ライフスタイルWebマガジン『Zazzy』の編集長です。要点を簡潔かつ魅力的にまとめてください。"
    )
    # 最新の推奨軽量モデル gemini-3.8-flash を指定
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
    
    print(f"Generating issue for {today_str}...")
    article_body = generate_issue()

    content = f"""---
title: "Daily Issue - {today_str}"
date: "{today_str}"
description: "Daily curated magazine issue."
---

{article_body}
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Successfully created: {file_path}")

if __name__ == "__main__":
    main()
