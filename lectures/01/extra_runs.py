# 第1回 宿題（発展）の追加
# 説明の質問で1回目だけ極端に遅かったので、3〜5回目を追加で測る
# 実行: PYTHONPATH=. uv run python lectures/01/extra_runs.py

import time

from google import genai
from google.genai import types

from app.config import get_api_key

q = "LoRAとは何ですか？"
price = {"gemini-3.5-flash-lite": (0.30, 2.50), "gemini-3.6-flash": (0.75, 3.75)}
YEN = 155

client = genai.Client(api_key=get_api_key())
config = types.GenerateContentConfig(max_output_tokens=2048)
rows = []
total_yen = 0

for m in price:
    for i in range(3, 6):
        start = time.time()
        first = None
        usage = None
        for chunk in client.models.generate_content_stream(model=m, contents=q, config=config):
            if first is None:
                first = time.time() - start
            if chunk.usage_metadata:
                usage = chunk.usage_metadata
        total = time.time() - start
        out = usage.candidates_token_count or 0
        think = usage.thoughts_token_count or 0
        yen = (usage.prompt_token_count * price[m][0] + (out + think) * price[m][1]) / 1_000_000 * YEN
        total_yen += yen
        rows.append(f"| 説明 | {m} | {i} | {first:.1f} | {total:.1f} | {out} | {think} | {yen:.2f} |")
        print(m, i, f"{total:.1f}s", f"{total_yen:.1f}円")
        time.sleep(5)

head = [
    "# 第1回 宿題（発展）追加の計測",
    "",
    "advanced_results.md の「説明」の質問で1回目が極端に遅かったので、3〜5回目を追加した。",
    "",
    "| 質問 | モデル | 回 | 最初の文字まで(秒) | 全体(秒) | 出力 | thinking | 料金(円) |",
    "|---|---|---|---|---|---|---|---|",
]
with open("lectures/01/extra_results.md", "w", encoding="utf-8") as f:
    f.write("\n".join(head + rows) + f"\n\n合計 約{total_yen:.1f}円\n")
