"""Tests the agent loop with a fake LLM: no API key, no cost, same result every run."""

from types import SimpleNamespace

import pytest

from src.agent import check_posting, run_tool


def test_unknown_tool_is_an_error_not_a_crash():
    assert "error" in run_tool("delete_everything", {})


class FakeClient:
    """Pretends to be the LLM: first asks for check_email_domain, then says DONE, then explains."""

    def __init__(self):
        self.calls = 0
        self.messages = SimpleNamespace(create=self.create)

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            block = SimpleNamespace(type="tool_use", id="t1", name="check_email_domain",
                                    input={"email": "hr@gmail.com", "company_domain": "acme.com"})
            return SimpleNamespace(stop_reason="tool_use", content=[block])
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="DONE")])


def test_full_pipeline_with_fake_llm(tmp_path, monkeypatch):
    monkeypatch.setattr("src.agent.LOG_FILE", tmp_path / "log.jsonl")
    out = check_posting("Earn $500 weekly from home, send bank details to hr@gmail.com", client=FakeClient())
    assert out["evidence"]["check_email_domain"]["free_webmail"] is True
    assert out["trace"][0]["tool"] == "check_email_domain"
    assert (tmp_path / "log.jsonl").exists()


def test_real_run_without_model_id_fails_clearly(monkeypatch):
    # No model name lives in the code, so a real run must stop with a clear message instead.
    monkeypatch.setattr("src.agent.MODEL", None)
    with pytest.raises(RuntimeError, match="JOB_TRUST_MODEL"):
        check_posting("any posting")
