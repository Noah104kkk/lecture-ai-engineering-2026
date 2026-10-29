# 第1回 宿題（基礎）
# 同じ質問を3回ずつ、モデルを変えて実行する
# 実行: PYTHONPATH=. uv run python lectures/01/basic_runs.py

import time

from google import genai

from app.config import get_api_key

questions = ["LoRAとは何ですか？", "AIE2026の講座の宿題にある「3レベル」とは何ですか？"]
models = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]

client = genai.Client(api_key=get_api_key())
out = []

for q in questions:
    out.append(f"## {q}\n")
    for m in models:
        for i in range(3):
            start = time.time()
            try:
                res = client.models.generate_content(model=m, contents=q)
                t = time.time() - start
                u = res.usage_metadata
                out.append(f"### {m} {i + 1}回目 ({t:.1f}秒 / 入力{u.prompt_token_count} 出力{u.candidates_token_count})\n")
                out.append(res.text + "\n")
            except Exception as e:
                out.append(f"### {m} {i + 1}回目 エラー\n")
                out.append(str(e) + "\n")
            print(m, i + 1)
            time.sleep(15)  # 3.8-flashは1分5回までなので間をあける

with open("lectures/01/basic_results.md", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
