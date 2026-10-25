"""第1回 宿題（基礎）: 同じ質問を3回ずつ、モデルを変えて実行し、回答の違いを記録する。

使い方（Codespaces のターミナルで）:
    PYTHONPATH=. uv run python lectures/01/basic_runs.py

結果は lectures/01/basic_results.md に書き出す（APIキーは書き出さない）。
"""

import time
from pathlib import Path

from google import genai
from google.genai import errors

from app.config import api_error_message, get_api_key

QUESTIONS = [
    "LoRAとは何ですか？",  # 一般的な用語
    "AIE2026の講座の宿題にある「3レベル」とは何ですか？",  # 講座に固有のこと
]
MODELS = [
    ("gemini-3.5-flash-lite", 5),  # 毎分15回まで。間隔5秒
    ("gemini-3.8-flash", 15),  # 毎分5回まで。間隔15秒
]
RUNS = 3
OUT = Path(__file__).with_name("basic_results.md")


def main() -> None:
    client = genai.Client(api_key=get_api_key())
    lines = ["# 第1回 宿題（基礎）実行ログ", "", f"各質問を{RUNS}回ずつ、モデルを変えて実行した。temperatureは既定のまま。", ""]
    for question in QUESTIONS:
        lines += [f"## 質問: {question}", ""]
        for model, wait in MODELS:
            for i in range(1, RUNS + 1):
                start = time.perf_counter()
                try:
                    res = client.models.generate_content(model=model, contents=question)
                    elapsed = time.perf_counter() - start
                    u = res.usage_metadata
                    tokens = f"入力 {u.prompt_token_count} / 出力 {u.candidates_token_count}" if u else "不明"
                    body = (res.text or "（空の応答）").strip()
                except errors.APIError as e:
                    elapsed = time.perf_counter() - start
                    tokens = "-"
                    body = f"（エラー）{api_error_message(e.code, e.message)}"
                head = f"### {model} / {i}回目（{elapsed:.1f}秒、トークン {tokens}）"
                print(head)
                lines += [head, "", body, ""]
                time.sleep(wait)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n書き出し: {OUT}")


if __name__ == "__main__":
    main()
