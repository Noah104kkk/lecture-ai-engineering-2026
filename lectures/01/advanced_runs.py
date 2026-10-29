# 第1回 宿題（発展）
# 応答時間とトークン数を、モデル・質問の種類ごとに比べる
# 実行: PYTHONPATH=. uv run python lectures/01/advanced_runs.py
#
# 自分のキーのプロジェクトは課金ありなので、出力は2048トークンまでにして、
# 概算の料金が30円をこえたら止める

import time

from google import genai
from google.genai import types

from app.config import get_api_key

questions = {
    "短い事実": "日本の首都はどこですか？",
    "説明": "LoRAとは何ですか？",
    "コード": "Pythonでリストから重複を取り除く関数を書いてください。",
    "講座固有": "AIE2026の講座の宿題にある「3レベル」とは何ですか？",
}
# 1Mトークンあたりの値段（ドル）。入力, 出力（thinkingを含む）
price = {
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.6-flash": (0.75, 3.75),
    "gemini-3.8-flash": (0.75, 3.75),
}
YEN = 155
LIMIT_YEN = 30

client = genai.Client(api_key=get_api_key())
config = types.GenerateContentConfig(max_output_tokens=2048)
rows = []
total_yen = 0

for kind, q in questions.items():
    for m in price:
        for i in range(2):
            if total_yen > LIMIT_YEN:
                break
            start = time.time()
            first = None
            text = ""
            usage = None
            try:
                for chunk in client.models.generate_content_stream(model=m, contents=q, config=config):
                    if first is None:
                        first = time.time() - start
                    text += chunk.text or ""
                    if chunk.usage_metadata:
                        usage = chunk.usage_metadata
            except Exception as e:
                rows.append(f"| {kind} | {m} | {i + 1} | エラー: {str(e)[:60]} | | | | | |")
                print(m, kind, "error", e)
                time.sleep(5)
                continue
            total = time.time() - start
            first = first or total
            inp = (usage and usage.prompt_token_count) or 0
            out = (usage and usage.candidates_token_count) or 0
            think = (usage and usage.thoughts_token_count) or 0
            yen = (inp * price[m][0] + (out + think) * price[m][1]) / 1_000_000 * YEN
            total_yen += yen
            rows.append(f"| {kind} | {m} | {i + 1} | {first:.1f} | {total:.1f} | {inp} | {out} | {think} | {yen:.2f} | {len(text)} |")
            print(m, kind, i + 1, f"{total:.1f}s", out, think, f"{total_yen:.1f}円")
            time.sleep(5)

head = [
    "# 第1回 宿題（発展）実行ログ",
    "",
    f"出力上限 2048トークン、temperatureは既定。料金は1ドル{YEN}円で計算した概算。",
    "",
    "| 質問 | モデル | 回 | 最初の文字まで(秒) | 全体(秒) | 入力 | 出力 | thinking | 料金(円) | 文字数 |",
    "|---|---|---|---|---|---|---|---|---|---|",
]
with open("lectures/01/advanced_results.md", "w", encoding="utf-8") as f:
    f.write("\n".join(head + rows) + f"\n\n合計 約{total_yen:.1f}円\n")
print(f"合計 約{total_yen:.1f}円")
