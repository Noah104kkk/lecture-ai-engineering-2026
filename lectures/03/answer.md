# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  - 第1回の `app.ask` は「AIE2026という講座の情報にはアクセスできません」と断ったうえで、一般的な「レベル1〜3（初級・中級・上級）」を推測で並べた（入力21トークン・出力310トークン）
  - エージェントは `search_glossary('3レベル')` で用語集を引き、「基礎（講義内容の確認）・実装（自分でコードを書く）・発展（調査や試行）の3段階で、どれか1つに取り組めば完了」と用語集どおりに答え、最後に「関連回：第1回」を付けた
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - 「3レベル」の質問：`search_glossary({'query': '3レベル'})` の1回
  - 「LoRAとQLoRAの違いは？」：`search_glossary({'query': 'LoRA'})` と `search_glossary({'query': 'QLoRA'})` の2回。docstring の「query には調べたい用語を1つだけ入れる」どおり、用語を分けて検索していた
  - 「第2回の内容から確認問題を1問出して」：`make_quiz({'lecture': 2})` の1回
- 1つの質問での LLM 呼び出し回数（`requests`）：
  - どの質問も `requests=2`（1回目でツール呼び出しを決め、2回目でツールの結果を見て回答を作る）。LoRA/QLoRA は2つのツール呼び出しを1回目でまとめて出していたので、呼び出しが2つでも `requests` は2のまま
- 追加したツールと、docstring に書いた説明：
  - `make_quiz(lecture: int)`：用語集から指定した回の用語を1つ選び、`{"question": "「○○」の意味は？", "answer": 定義}` を返す。用語がない回（第0回など）には、問題を作れる回の一覧を返す
  - docstring：「『第2回の確認問題を出して』『第3回の復習クイズがほしい』のように、確認問題・クイズ・復習の問題を求められたときに使う。返り値の answer は、利用者が答えるまで見せないこと」
  - 実行すると、モデルは答えを伏せて問題だけを出した（「『教師ありファインチューニング（SFT）』の意味は？」）

## 宿題

- 取り組んだレベル：実装
- やったこと：
  - `app/tools.py` に `save_learning_log(title, content)` を作った。`learning_log/` に `日時_題名.md` で保存する。題名のうちファイル名に使えない文字（`/` など）は `_` に置き換え、同じ秒に同じ題名で保存しても `-2` を付けて上書きしないようにした。題名か本文が空なら保存しない
  - `app/agent.py` で `agent.tool_plain(tools.save_learning_log, requires_approval=True)` と登録し、`output_type=[str, DeferredToolRequests]` にした。`INSTRUCTIONS` に「学習の記録を保存してと頼まれたときだけ save_learning_log を使う」を足した
  - CLI に `run_with_approval()` を足した。結果が `DeferredToolRequests` なら、`approvals` の呼び出しごとに引数（題名と本文）を表示して `[y/N]` で聞き、`y` なら `True`、それ以外なら `ToolDenied("利用者が実行を断りました。保存はしていません。")` を `DeferredToolResults` に入れて、`message_history=result.all_messages()` と一緒にもう一度 `run_sync` する。承認待ちが続く限りくり返す
  - テスト `tests/test_lec03_homework.py` を足した（APIキー不要。TestModel で、承認前は保存されないこと・`y` で保存されること・`n` で保存されないこと、`make_quiz` の返り値と第0回の扱い、上書きしないこと）。`uv run pytest -q` は最初 22 passed。その後、第5回の `tests/test_mcp_server.py` だけが手元の Windows で MCP サーバーの起動中の `MemoryError` で落ちるようになったが、変更前のコードでも同じように落ちたので、今回の変更とは関係ないと判断した（残り21件は通る）
- 結果：
  - 最初の版は、保存を頼んでもツールが呼ばれなかった。「LoRAとQLoRAの違いを調べて、学習ログに保存して」に対して、`search_glossary` だけ呼んで「この内容で保存してよろしいでしょうか？『はい』とお知らせください」とチャットで聞き返して終わった（trace に `save_learning_log` が出ない）
  - 原因は、自分で docstring に書いた「保存の前に、利用者の確認（承認）を求める」だと考えた。確認するのはプログラム（`requires_approval`）なのに、モデルは「自分がチャットで確認を取れ」という指示として読んでいた
  - docstring を「保存してよいかの確認はこのツールを呼んだあとにプログラムが利用者へ行うので、チャットで確認を取り直さず、頼まれたらそのまま呼ぶこと」に変えると、同じ質問で `save_learning_log({'title': 'LoRAとQLoRAの違い', 'content': '# LoRAとQLoRAの違い ...'})` が呼ばれ、`[承認待ち]` で止まった
  - `y`：`[tool return] save_learning_log -> 保存しました: learning_log/2026-11-07_211612_LoRAとQLoRAの違い.md`。回答も「learning_log/ フォルダに保存しました」
  - `n`：`[tool return] save_learning_log -> 利用者が実行を断りました。保存はしていません。`。ファイルは作られず、回答も「今回は保存が実行されませんでした。保存をご希望の場合は、再度お申し付けください」と断られたことを踏まえていた
  - 保存を頼んでいない質問（「PEFTとは？」）では `save_learning_log` は呼ばれなかった
- 気づき・疑問：
