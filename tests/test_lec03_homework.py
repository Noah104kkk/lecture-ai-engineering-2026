"""第3回 演習（make_quiz）と宿題・実装（save_learning_log と承認）のテスト。LLMもAPIキーも使わない。"""

import json

import pytest
from pydantic_ai import DeferredToolRequests
from pydantic_ai.models.test import TestModel

from app import agent as agent_module
from app import tools


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    """保存先を一時フォルダに差し替え、本物の learning_log/ を汚さない。"""
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path / "learning_log")
    return tmp_path / "learning_log"


def test_make_quiz_returns_question_and_answer_of_the_lecture():
    quiz = json.loads(tools.make_quiz(2))
    lecture2 = {e["definition"] for e in tools.load_glossary() if e["lecture"] == 2}
    assert quiz["question"].endswith("の意味は？")
    assert quiz["answer"] in lecture2


def test_make_quiz_reports_missing_lecture():
    assert "ありません" in tools.make_quiz(0)


def test_save_learning_log_writes_file_without_overwriting(log_dir):
    first = tools.save_learning_log("LoRA/QLoRA の違い", "本文")
    second = tools.save_learning_log("LoRA/QLoRA の違い", "本文2")
    files = sorted(log_dir.glob("*.md"))
    assert "保存しました" in first and "保存しました" in second
    assert len(files) == 2  # 同じ秒・同じ題名でも上書きしない
    assert "/" not in files[0].name.split("_", 2)[2]  # 題名の「/」はファイル名に残さない


def test_save_learning_log_rejects_empty(log_dir):
    assert "保存しませんでした" in tools.save_learning_log(" ", "本文")
    assert not log_dir.exists()


def _run(answer, log_dir):
    model = TestModel(call_tools=["save_learning_log"])
    asked = []

    def fake_input(prompt):
        asked.append(prompt)
        return answer

    result = agent_module.run_with_approval(agent_module.agent, "今日の学びを保存して", model, ask=fake_input)
    return result, asked


def test_approval_pauses_before_saving(log_dir):
    model = TestModel(call_tools=["save_learning_log"])
    result = agent_module.agent.run_sync("今日の学びを保存して", model=model)
    assert isinstance(result.output, DeferredToolRequests)  # 承認待ちで止まる
    assert result.output.approvals[0].tool_name == "save_learning_log"
    assert not log_dir.exists()  # まだ保存されていない


def test_approved_call_saves(log_dir):
    result, asked = _run("y", log_dir)
    assert len(asked) == 1
    assert len(list(log_dir.glob("*.md"))) == 1
    assert isinstance(result.output, str)


def test_denied_call_does_not_save(log_dir):
    result, asked = _run("n", log_dir)
    assert len(asked) == 1
    assert not log_dir.exists()
    assert isinstance(result.output, str)
