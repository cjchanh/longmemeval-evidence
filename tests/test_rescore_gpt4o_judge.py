"""Tests for scripts/rescore_gpt4o_judge.py.

No model calls: judge_once / check_model_available are always mocked via
monkeypatch on subprocess.run. Covers: frozen prompt constants (sha pin),
row schema, control gating (fail-closed on low pass rate), and transport
retry/contamination behavior.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.error
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import rescore_gpt4o_judge as m  # noqa: E402


# ---------------------------------------------------------------------------
# Frozen prompt constants — sha pin
# ---------------------------------------------------------------------------

def test_prompt_template_version_is_frozen_tag():
    assert m.PROMPT_TEMPLATE_VERSION == "longmemeval-official-judge-v1"


def test_prompt_templates_sha256_matches_frozen_text():
    """If anyone edits BASE_TEMPLATE/TEMPORAL_ADDITION/KU_ADDITION/SSP_TEMPLATE/
    ABS_TEMPLATE, this test fails — the sha pin is the tripwire for a silent
    rubric drift, not decoration."""
    recomputed = m.hashlib.sha256(
        "\x00".join([
            m.BASE_TEMPLATE, m.TEMPORAL_ADDITION, m.KU_ADDITION,
            m.SSP_TEMPLATE, m.ABS_TEMPLATE,
        ]).encode("utf-8")
    ).hexdigest()
    assert recomputed == m.PROMPT_TEMPLATES_SHA256
    # and the module constant itself is a real sha256 hex digest
    assert len(m.PROMPT_TEMPLATES_SHA256) == 64
    int(m.PROMPT_TEMPLATES_SHA256, 16)  # raises if not hex


def test_prompt_templates_match_rescore_llm_judge_verbatim():
    """These are frozen as an independent copy (see module docstring) but must
    stay byte-identical to the base script's official-rubric templates unless
    a deliberate, version-bumped edit happens."""
    base_scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
    base_path = base_scripts_dir / "rescore_llm_judge.py"
    if not base_path.exists():
        pytest.skip("rescore_llm_judge.py not vendored alongside this build "
                    "(scratchpad smoke build) — verified against the real "
                    "worktree at authoring time")
    sys.path.insert(0, str(base_scripts_dir))
    import rescore_llm_judge as base  # noqa: E402
    assert m.BASE_TEMPLATE == base.BASE_TEMPLATE
    assert m.TEMPORAL_ADDITION == base.TEMPORAL_ADDITION
    assert m.KU_ADDITION == base.KU_ADDITION
    assert m.SSP_TEMPLATE == base.SSP_TEMPLATE
    assert m.ABS_TEMPLATE == base.ABS_TEMPLATE


# ---------------------------------------------------------------------------
# build_prompt() — per-type rubric selection
# ---------------------------------------------------------------------------

def test_build_prompt_abstention_uses_abs_template():
    p = m.build_prompt("single-session-user", "q", "explanation", "resp",
                       abstention=True)
    assert p == m.ABS_TEMPLATE.format(question="q", answer="explanation",
                                      response="resp")


def test_build_prompt_ssp_uses_ssp_template():
    p = m.build_prompt("single-session-preference", "q", "rubric", "resp",
                       abstention=False)
    assert p == m.SSP_TEMPLATE.format(question="q", answer="rubric",
                                      response="resp")


def test_build_prompt_temporal_appends_addition():
    p = m.build_prompt("temporal-reasoning", "q", "g", "r", abstention=False)
    assert m.TEMPORAL_ADDITION in p
    assert m.KU_ADDITION not in p


def test_build_prompt_knowledge_update_appends_addition():
    p = m.build_prompt("knowledge-update", "q", "g", "r", abstention=False)
    assert m.KU_ADDITION in p
    assert m.TEMPORAL_ADDITION not in p


def test_build_prompt_default_type_plain_base():
    p = m.build_prompt("multi-session", "q", "g", "r", abstention=False)
    assert p == m.BASE_TEMPLATE.format(question="q", answer="g", response="r")
    assert m.TEMPORAL_ADDITION not in p
    assert m.KU_ADDITION not in p


# ---------------------------------------------------------------------------
# Row schema
# ---------------------------------------------------------------------------

REQUIRED_ROW_KEYS = {
    "question_id", "question_type", "abstention", "llm_judge_correct",
    "llm_judge_raw", "attempts", "scored_at", "transport", "model",
    "resolved_snapshot",
}


def test_rescore_row_schema_has_required_keys(monkeypatch):
    monkeypatch.setattr(m, "judge_once", lambda *a, **k: (True, "yes", 1, None))
    row = {"question_id": "q1", "question_type": "single-session-user",
          "question": "What?", "gold": "gold answer", "response": "an answer"}
    record = m.rescore_row(row, abstention=False, model="openai/gpt-4o",
                           timeout_s=10, max_attempts=1, backoff_s=0.0)
    assert REQUIRED_ROW_KEYS.issubset(record.keys())
    assert record["question_id"] == "q1"
    assert record["question_type"] == "single-session-user"
    assert record["abstention"] is False
    assert record["llm_judge_correct"] is True
    assert record["llm_judge_raw"] == "yes"
    assert record["attempts"] == 1
    assert record["transport"] == "opencode"  # default when unspecified
    assert record["resolved_snapshot"] is None
    # scored_at is a real ISO8601 UTC timestamp
    import datetime
    datetime.datetime.fromisoformat(record["scored_at"])


def test_rescore_row_records_api_transport_and_resolved_snapshot(monkeypatch):
    monkeypatch.setattr(
        m, "judge_once",
        lambda *a, **k: (True, "yes", 1, "gpt-4o-2024-08-06"))
    row = {"question_id": "q1", "question_type": "multi-session",
          "question": "What?", "gold": "gold answer", "response": "an answer"}
    record = m.rescore_row(row, abstention=False, model="gpt-4o-2024-08-06",
                           timeout_s=10, max_attempts=1, backoff_s=0.0,
                           transport="api")
    assert record["transport"] == "api"
    assert record["model"] == "gpt-4o-2024-08-06"
    assert record["resolved_snapshot"] == "gpt-4o-2024-08-06"


def test_rescore_row_empty_response_scored_false_without_calling_judge(monkeypatch):
    called = []
    monkeypatch.setattr(m, "judge_once",
                        lambda *a, **k: called.append(1) or (True, "yes", 1, None))
    row = {"question_id": "q2", "question_type": "multi-session",
          "question": "What?", "gold": "gold", "response": ""}
    record = m.rescore_row(row, abstention=False, model="openai/gpt-4o",
                           timeout_s=10, max_attempts=1, backoff_s=0.0)
    assert record["llm_judge_correct"] is False
    assert record["llm_judge_raw"] == ""
    assert record["attempts"] == 0
    assert not called  # judge never invoked for an empty response


def test_rescore_row_abstention_flag_recorded(monkeypatch):
    monkeypatch.setattr(m, "judge_once", lambda *a, **k: (False, "no", 2, None))
    row = {"question_id": "q3", "question_type": "single-session-user",
          "question": "What?", "gold": "the info is missing", "response": "I don't know"}
    record = m.rescore_row(row, abstention=True, model="openai/gpt-4o",
                           timeout_s=10, max_attempts=1, backoff_s=0.0)
    assert record["abstention"] is True
    assert record["attempts"] == 2


# ---------------------------------------------------------------------------
# Control gating — fail-closed
# ---------------------------------------------------------------------------

def _rows_for_controls(n=6):
    rows = []
    for i in range(n):
        rows.append({
            "question_id": f"q{i}",
            "question_type": "multi-session",
            "question": f"question {i}?",
            "gold": f"gold-{i}",
            "response": f"response-{i}",
        })
    return rows


def test_run_controls_all_pass(tmp_path, monkeypatch):
    def fake_judge_once(model, prompt, timeout_s, max_attempts, backoff_s, **kw):
        # A correct judge says yes iff the answer and response fields match
        # verbatim (positive control uses gold as the response; negative uses
        # a different row's response). Extract both fields deterministically.
        answer = re.search(r"Correct Answer: (.*?)\n\n", prompt).group(1)
        response = re.search(r"Model Response: (.*?)\n\n", prompt).group(1)
        match = answer == response
        return (match, "yes" if match else "no", 1, None)
    monkeypatch.setattr(m, "judge_once", fake_judge_once)
    rows = _rows_for_controls(6)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    result = m.run_controls(rows, "openai/gpt-4o", n=6, timeout_s=10,
                            max_attempts=1, backoff_s=0.0, out_dir=out_dir)
    assert result["positive_rate"] == 1.0
    assert result["negative_rate"] == 1.0
    assert (out_dir / "control_receipt.json").exists()
    receipt = json.loads((out_dir / "control_receipt.json").read_text())
    assert receipt["threshold"] == 0.9
    assert receipt["ssp_excluded_from_positive_arm"] is True


def test_run_controls_ssp_excluded_from_positive_arm(monkeypatch, tmp_path):
    calls = {"n": 0}

    def fake_judge_once(model, prompt, timeout_s, max_attempts, backoff_s, **kw):
        calls["n"] += 1
        return (False, "no", 1, None)

    monkeypatch.setattr(m, "judge_once", fake_judge_once)
    rows = [{
        "question_id": "ssp1", "question_type": "single-session-preference",
        "question": "q", "gold": "rubric text", "response": "some response",
    }, {
        "question_id": "other1", "question_type": "multi-session",
        "question": "q2", "gold": "gold2", "response": "resp2",
    }]
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    result = m.run_controls(rows, "openai/gpt-4o", n=2, timeout_s=10,
                            max_attempts=1, backoff_s=0.0, out_dir=out_dir)
    # SSP row contributes 0 to n_positive_eligible; only 'other1' does.
    assert result["n_positive_eligible"] == 1
    ssp_record = next(r for r in result["records"] if r["question_id"] == "ssp1")
    assert ssp_record["positive_pass"] is None


def test_main_aborts_on_control_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "check_model_available", lambda model, **k: None)
    monkeypatch.setattr(m, "judge_once", lambda *a, **k: (False, "no", 1, None))
    ans_path = tmp_path / "answerable.jsonl"
    abs_path = tmp_path / "abs.jsonl"
    rows = _rows_for_controls(6)
    ans_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    abs_path.write_text("")
    out_dir = tmp_path / "out"
    rc = m.main([
        "--answerable", str(ans_path), "--abs", str(abs_path),
        "--out-dir", str(out_dir), "--control-n", "6",
    ])
    assert rc == 2
    assert (out_dir / "control_receipt.json").exists()
    assert not (out_dir / "rescored.jsonl").exists()


def test_main_skip_controls_without_prior_receipt_refuses(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "check_model_available", lambda model, **k: None)
    ans_path = tmp_path / "answerable.jsonl"
    abs_path = tmp_path / "abs.jsonl"
    ans_path.write_text("")
    abs_path.write_text("")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    rc = m.main([
        "--answerable", str(ans_path), "--abs", str(abs_path),
        "--out-dir", str(out_dir), "--skip-controls",
    ])
    assert rc == 2


def test_main_end_to_end_with_mocked_judge(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "check_model_available", lambda model, **k: None)

    def fake_judge_once(model, prompt, timeout_s, max_attempts, backoff_s, **kw):
        # Discriminate positive vs negative controls like a real judge would
        # (answer==response -> yes), and say "yes" for the abstention row
        # below (whose response correctly states the info is unavailable).
        answer_m = re.search(r"(?:Correct Answer|Explanation): (.*?)\n\n", prompt)
        response_m = re.search(r"Model Response: (.*?)\n\n", prompt)
        if answer_m and response_m:
            match = answer_m.group(1) == response_m.group(1)
            return (match, "yes" if match else "no", 1, None)
        return (True, "yes", 1, None)

    monkeypatch.setattr(m, "judge_once", fake_judge_once)
    # Perfect-reader rows (response == gold) so the real scoring pass reads
    # back llm_judge_accuracy == 1.0 under the discriminating fake judge
    # above; the control phase still discriminates correctly (negative arm
    # substitutes a DIFFERENT row's response, which has a different gold).
    ans_rows = [{
        "question_id": f"q{i}", "question_type": "multi-session",
        "question": f"question {i}?", "gold": f"gold-{i}",
        "response": f"gold-{i}",
    } for i in range(6)]
    abs_rows = [{
        "question_id": "abs0", "question_type": "single-session-user",
        "question": "q", "gold": "info missing", "response": "info missing",
    }]
    ans_path = tmp_path / "answerable.jsonl"
    abs_path = tmp_path / "abs.jsonl"
    ans_path.write_text("\n".join(json.dumps(r) for r in ans_rows) + "\n")
    abs_path.write_text("\n".join(json.dumps(r) for r in abs_rows) + "\n")
    out_dir = tmp_path / "out"
    rc = m.main([
        "--answerable", str(ans_path), "--abs", str(abs_path),
        "--out-dir", str(out_dir), "--control-n", "6",
    ])
    assert rc == 0
    summary = json.loads((out_dir / "rescore_summary.json").read_text())
    # Neither --model nor --transport given -> new default: api transport,
    # dated gpt-4o snapshot (see module docstring default-resolution rule).
    assert summary["judge_model"] == "gpt-4o-2024-08-06"
    assert summary["transport"] == "api"
    assert summary["prompt_template_version"] == m.PROMPT_TEMPLATE_VERSION
    assert summary["prompt_templates_sha256"] == m.PROMPT_TEMPLATES_SHA256
    assert summary["n_answerable"] == 6
    assert summary["llm_judge_accuracy"] == 1.0
    assert summary["abstention"]["n"] == 1
    scored = [json.loads(l) for l in
             (out_dir / "rescored.jsonl").read_text().splitlines()]
    assert len(scored) == 7
    for row in scored:
        assert REQUIRED_ROW_KEYS.issubset(row.keys())


# ---------------------------------------------------------------------------
# Transport — retry / chrome-strip / contamination (no real subprocess calls)
# ---------------------------------------------------------------------------

class _FakeCompleted:
    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_judge_once_parses_plain_yes(monkeypatch):
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: _FakeCompleted(0, b"yes"))
    verdict, raw, attempts, resolved = m.judge_once("openai/gpt-4o", "prompt", 10, 3, 0.0)
    assert verdict is True
    assert raw == "yes"
    assert attempts == 1


def test_judge_once_parses_plain_no(monkeypatch):
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: _FakeCompleted(0, b"no"))
    verdict, raw, attempts, resolved = m.judge_once("openai/gpt-4o", "prompt", 10, 3, 0.0)
    assert verdict is False


def test_judge_once_strips_ansi_and_chrome(monkeypatch):
    # Realistic opencode banner: "> <lane> · <model>" on its own ANSI-colored
    # line (observed live, e.g. "> ox-alpha \xc2\xb7 gpt-5.4-mini"), real
    # verdict on the next line. The chrome line is dropped ENTIRELY (line-
    # level filter, matching oc_flash_lane semantics) — a bare "> " line with
    # nothing after the single space does NOT match _CHROME_LINE once
    # stripped (no trailing char left for \s) and is correctly caught instead
    # by the _CONTAMINATION safety net (see the fail-closed test below).
    contaminated = "\x1b[36m> ox-alpha · gpt-4o\x1b[0m\nyes".encode("utf-8")
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: _FakeCompleted(0, contaminated))
    verdict, raw, attempts, resolved = m.judge_once("openai/gpt-4o", "prompt", 10, 3, 0.0)
    assert verdict is True
    assert raw == "yes"


def test_judge_once_bare_gt_line_caught_by_contamination_safety_net(monkeypatch):
    """A bare "> " chrome line (space, then nothing) does not match
    _CHROME_LINE once .strip()'d (no trailing char left for \\s to match),
    so it survives line-level filtering — the _CONTAMINATION check on the
    reassembled text is the safety net that still rejects it rather than
    silently handing a chrome-prefixed blob to the caller as if it were a
    clean verdict."""
    raw = "\x1b[32m> \x1b[0m\nyes".encode("utf-8")
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: _FakeCompleted(0, raw))
    with pytest.raises(m.JudgeContamination):
        m.judge_once("openai/gpt-4o", "prompt", 10, 3, 0.0)


def test_judge_once_retries_on_nonzero_exit_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def fake_run(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            return _FakeCompleted(1, b"", b"boom")
        return _FakeCompleted(0, b"yes")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    verdict, raw, attempts, resolved = m.judge_once("openai/gpt-4o", "prompt", 10, 3, 0.0)
    assert verdict is True
    assert attempts == 2
    assert calls["n"] == 2


def test_judge_once_retries_on_timeout(monkeypatch):
    calls = {"n": 0}

    def fake_run(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise subprocess.TimeoutExpired(cmd="opencode", timeout=10)
        return _FakeCompleted(0, b"no")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    verdict, raw, attempts, resolved = m.judge_once("openai/gpt-4o", "prompt", 10, 3, 0.0)
    assert verdict is False
    assert attempts == 2


def test_judge_once_exhausts_retries_and_raises(monkeypatch):
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: _FakeCompleted(1, b"", b"dead"))
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    with pytest.raises(m.JudgeTransportError):
        m.judge_once("openai/gpt-4o", "prompt", 10, 3, 0.0)


def test_judge_once_fails_closed_on_contamination_no_retry(monkeypatch):
    """Chrome that merges with real content on the SAME line (the exact
    2026-08-28 failure class oc_flash_lane's _CONTAMINATION guards against —
    20/500 rows began "OUT: 0" immediately followed by the real answer) is
    not a full chrome LINE (so _CHROME_LINE's end-anchored pattern does not
    drop it), and must be rejected rather than silently judged."""
    calls = {"n": 0}

    def fake_run(*a, **k):
        calls["n"] += 1
        return _FakeCompleted(0, b"OUT: 0 the answer is yes")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(m.JudgeContamination):
        m.judge_once("openai/gpt-4o", "prompt", 10, 3, 0.0)
    assert calls["n"] == 1  # contamination is NOT retried


# ---------------------------------------------------------------------------
# check_model_available — fail closed on absent model, no real network call
# ---------------------------------------------------------------------------

def test_check_model_available_passes_when_listed(monkeypatch):
    def fake_run(*a, **k):
        return type("R", (), {"returncode": 0,
                              "stdout": "openai/gpt-4o\nopencode/gpt-5\n",
                              "stderr": ""})()

    monkeypatch.setattr(subprocess, "run", fake_run)
    m.check_model_available("openai/gpt-4o")  # must not raise


def test_check_model_available_fails_closed_when_absent(monkeypatch):
    def fake_run(*a, **k):
        return type("R", (), {"returncode": 0,
                              "stdout": "openai/gpt-5.4\nopencode/gpt-5\n",
                              "stderr": ""})()

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(m.JudgeTransportError, match="not available"):
        m.check_model_available("openai/gpt-4o")


def test_check_model_available_fails_closed_on_nonzero_exit(monkeypatch):
    def fake_run(*a, **k):
        return type("R", (), {"returncode": 1, "stdout": "",
                              "stderr": "opencode: command failed"})()

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(m.JudgeTransportError):
        m.check_model_available("openai/gpt-4o")


# ---------------------------------------------------------------------------
# summary_caveats
# ---------------------------------------------------------------------------

def test_summary_caveats_flags_non_gpt4o_model():
    caveats = m.summary_caveats("openai/gpt-5.6-sol")
    assert any("not gpt-4o" in c for c in caveats)


def test_summary_caveats_gpt4o_model_notes_snapshot_caution():
    caveats = m.summary_caveats("openai/gpt-4o")
    assert any("gpt-4o-2024-08-06" in c for c in caveats)
    assert not any("not gpt-4o" in c for c in caveats)


# ---------------------------------------------------------------------------
# API transport — key file handling, 401 fail-closed, retry, snapshot
# recording. urllib.request.urlopen is ALWAYS mocked; no real network calls.
# ---------------------------------------------------------------------------

class _FakeHTTPResponse:
    """Context-manager stand-in for the object urllib.request.urlopen()
    yields."""
    def __init__(self, body: bytes):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _api_body(content="yes", model="gpt-4o-2024-08-06"):
    return json.dumps({
        "model": model,
        "choices": [{"message": {"content": content}}],
    }).encode("utf-8")


def test_read_api_key_reads_and_strips_file(tmp_path):
    key_file = tmp_path / "api_key"
    key_file.write_text("  sk-fake-test-key-not-real  \n")
    assert m.read_api_key(key_file) == "sk-fake-test-key-not-real"


def test_read_api_key_fails_closed_on_missing_file(tmp_path):
    with pytest.raises(m.ApiKeyError):
        m.read_api_key(tmp_path / "does-not-exist")


def test_read_api_key_fails_closed_on_empty_file(tmp_path):
    key_file = tmp_path / "api_key"
    key_file.write_text("   \n")
    with pytest.raises(m.ApiKeyError):
        m.read_api_key(key_file)


def test_api_judge_once_success_records_resolved_snapshot_and_auth_header(
        tmp_path, monkeypatch):
    key_file = tmp_path / "api_key"
    key_file.write_text("sk-fake-test-key-not-real")
    captured_requests = []

    def fake_urlopen(request, timeout=None):
        captured_requests.append(request)
        return _FakeHTTPResponse(_api_body("yes", "gpt-4o-2024-08-06"))

    monkeypatch.setattr(m.urllib.request, "urlopen", fake_urlopen)
    verdict, raw, attempts, resolved = m.api_judge_once(
        "gpt-4o-2024-08-06", "prompt text", 10, 3, 0.0, key_file)
    assert verdict is True
    assert raw == "yes"
    assert attempts == 1
    assert resolved == "gpt-4o-2024-08-06"
    assert len(captured_requests) == 1
    sent = captured_requests[0]
    assert sent.get_header("Authorization") == "Bearer sk-fake-test-key-not-real"
    assert sent.full_url == m.OPENAI_CHAT_COMPLETIONS_URL


def test_api_judge_once_parses_plain_no(tmp_path, monkeypatch):
    key_file = tmp_path / "api_key"
    key_file.write_text("sk-fake-test-key-not-real")
    monkeypatch.setattr(m.urllib.request, "urlopen",
                        lambda *a, **k: _FakeHTTPResponse(_api_body("no")))
    verdict, raw, attempts, resolved = m.api_judge_once(
        "gpt-4o-2024-08-06", "prompt", 10, 3, 0.0, key_file)
    assert verdict is False


def test_api_judge_once_fails_closed_on_401_no_retry(tmp_path, monkeypatch):
    key_file = tmp_path / "api_key"
    key_file.write_text("sk-fake-test-key-not-real")
    calls = {"n": 0}

    def fake_urlopen(request, timeout=None):
        calls["n"] += 1
        raise urllib.error.HTTPError(
            m.OPENAI_CHAT_COMPLETIONS_URL, 401, "Unauthorized", {}, None)

    monkeypatch.setattr(m.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(m.ApiAuthError) as excinfo:
        m.api_judge_once("gpt-4o-2024-08-06", "prompt", 10, 3, 0.0, key_file)
    assert calls["n"] == 1  # 401 is NOT retried
    # the key value never appears in the raised error message
    assert "sk-fake-test-key-not-real" not in str(excinfo.value)


def test_api_judge_once_fails_closed_on_403_no_retry(tmp_path, monkeypatch):
    key_file = tmp_path / "api_key"
    key_file.write_text("sk-fake-test-key-not-real")
    calls = {"n": 0}

    def fake_urlopen(request, timeout=None):
        calls["n"] += 1
        raise urllib.error.HTTPError(
            m.OPENAI_CHAT_COMPLETIONS_URL, 403, "Forbidden", {}, None)

    monkeypatch.setattr(m.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(m.ApiAuthError):
        m.api_judge_once("gpt-4o-2024-08-06", "prompt", 10, 3, 0.0, key_file)
    assert calls["n"] == 1


def test_api_judge_once_retries_on_429_then_succeeds(tmp_path, monkeypatch):
    key_file = tmp_path / "api_key"
    key_file.write_text("sk-fake-test-key-not-real")
    calls = {"n": 0}

    def fake_urlopen(request, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(
                m.OPENAI_CHAT_COMPLETIONS_URL, 429, "Too Many Requests", {}, None)
        return _FakeHTTPResponse(_api_body("yes"))

    monkeypatch.setattr(m.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    verdict, raw, attempts, resolved = m.api_judge_once(
        "gpt-4o-2024-08-06", "prompt", 10, 3, 0.0, key_file)
    assert verdict is True
    assert attempts == 2
    assert calls["n"] == 2


def test_api_judge_once_retries_on_5xx_then_succeeds(tmp_path, monkeypatch):
    key_file = tmp_path / "api_key"
    key_file.write_text("sk-fake-test-key-not-real")
    calls = {"n": 0}

    def fake_urlopen(request, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(
                m.OPENAI_CHAT_COMPLETIONS_URL, 503, "Service Unavailable", {}, None)
        return _FakeHTTPResponse(_api_body("no"))

    monkeypatch.setattr(m.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    verdict, raw, attempts, resolved = m.api_judge_once(
        "gpt-4o-2024-08-06", "prompt", 10, 3, 0.0, key_file)
    assert attempts == 2


def test_api_judge_once_retries_on_network_error(tmp_path, monkeypatch):
    key_file = tmp_path / "api_key"
    key_file.write_text("sk-fake-test-key-not-real")
    calls = {"n": 0}

    def fake_urlopen(request, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.URLError("connection refused")
        return _FakeHTTPResponse(_api_body("yes"))

    monkeypatch.setattr(m.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    verdict, raw, attempts, resolved = m.api_judge_once(
        "gpt-4o-2024-08-06", "prompt", 10, 3, 0.0, key_file)
    assert verdict is True
    assert attempts == 2


def test_api_judge_once_exhausts_retries_and_raises(tmp_path, monkeypatch):
    key_file = tmp_path / "api_key"
    key_file.write_text("sk-fake-test-key-not-real")

    def fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(
            m.OPENAI_CHAT_COMPLETIONS_URL, 500, "Internal Server Error", {}, None)

    monkeypatch.setattr(m.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    with pytest.raises(m.JudgeTransportError):
        m.api_judge_once("gpt-4o-2024-08-06", "prompt", 10, 3, 0.0, key_file)


def test_api_judge_once_fails_closed_on_malformed_response(tmp_path, monkeypatch):
    key_file = tmp_path / "api_key"
    key_file.write_text("sk-fake-test-key-not-real")
    malformed = json.dumps({"model": "gpt-4o-2024-08-06"}).encode("utf-8")
    monkeypatch.setattr(m.urllib.request, "urlopen",
                        lambda *a, **k: _FakeHTTPResponse(malformed))
    with pytest.raises(m.JudgeTransportError):
        m.api_judge_once("gpt-4o-2024-08-06", "prompt", 10, 3, 0.0, key_file)


def test_api_judge_once_fails_closed_on_missing_key_file(tmp_path):
    with pytest.raises(m.ApiKeyError):
        m.api_judge_once("gpt-4o-2024-08-06", "prompt", 10, 3, 0.0,
                         tmp_path / "no-such-key-file")


def test_judge_once_dispatches_to_api_transport(tmp_path, monkeypatch):
    key_file = tmp_path / "api_key"
    key_file.write_text("sk-fake-test-key-not-real")
    monkeypatch.setattr(m.urllib.request, "urlopen",
                        lambda *a, **k: _FakeHTTPResponse(_api_body("yes")))
    verdict, raw, attempts, resolved = m.judge_once(
        "gpt-4o-2024-08-06", "prompt", 10, 3, 0.0,
        transport="api", api_key_file=key_file)
    assert verdict is True
    assert resolved == "gpt-4o-2024-08-06"


def test_judge_once_rejects_unknown_transport():
    with pytest.raises(ValueError):
        m.judge_once("m", "p", 10, 1, 0.0, transport="carrier-pigeon")


# ---------------------------------------------------------------------------
# check_model_available — api transport variant
# ---------------------------------------------------------------------------

def test_check_model_available_api_passes_when_listed(tmp_path, monkeypatch):
    key_file = tmp_path / "api_key"
    key_file.write_text("sk-fake-test-key-not-real")
    body = json.dumps({"data": [{"id": "gpt-4o-2024-08-06"}, {"id": "gpt-4o"}]}).encode()
    monkeypatch.setattr(m.urllib.request, "urlopen",
                        lambda *a, **k: _FakeHTTPResponse(body))
    m.check_model_available("gpt-4o-2024-08-06", transport="api",
                            api_key_file=key_file)  # must not raise


def test_check_model_available_api_fails_closed_when_absent(tmp_path, monkeypatch):
    key_file = tmp_path / "api_key"
    key_file.write_text("sk-fake-test-key-not-real")
    body = json.dumps({"data": [{"id": "gpt-5.4"}]}).encode()
    monkeypatch.setattr(m.urllib.request, "urlopen",
                        lambda *a, **k: _FakeHTTPResponse(body))
    with pytest.raises(m.JudgeTransportError, match="not available"):
        m.check_model_available("gpt-4o-2024-08-06", transport="api",
                                api_key_file=key_file)


def test_check_model_available_api_fails_closed_on_401(tmp_path, monkeypatch):
    key_file = tmp_path / "api_key"
    key_file.write_text("sk-fake-test-key-not-real")

    def fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(m.OPENAI_MODELS_URL, 401, "Unauthorized", {}, None)

    monkeypatch.setattr(m.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(m.ApiAuthError):
        m.check_model_available("gpt-4o-2024-08-06", transport="api",
                                api_key_file=key_file)


# ---------------------------------------------------------------------------
# --transport / --model default-resolution precedence (main())
# ---------------------------------------------------------------------------

def _run_main_minimal(tmp_path, extra_args, monkeypatch, judge_return=None):
    monkeypatch.setattr(m, "check_model_available", lambda model, **k: None)
    monkeypatch.setattr(
        m, "judge_once",
        lambda *a, **k: judge_return or (True, "yes", 1, None))
    # Two rows: run_controls' negative arm needs a DIFFERENT row to borrow a
    # response from.
    rows = [
        {"question_id": "q0", "question_type": "multi-session",
         "question": "q0", "gold": "g0", "response": "g0"},
        {"question_id": "q1", "question_type": "multi-session",
         "question": "q1", "gold": "g1", "response": "g1"},
    ]
    ans_path = tmp_path / "answerable.jsonl"
    abs_path = tmp_path / "abs.jsonl"
    ans_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    abs_path.write_text("")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    # These tests are about --transport/--model default-resolution, not
    # control-arm discrimination — pre-seed a passing control receipt and
    # skip the control phase so a non-discriminating fake judge_once doesn't
    # spuriously fail the (unrelated) control gate.
    (out_dir / "control_receipt.json").write_text(json.dumps({
        "n": 1, "positive_rate": 1.0, "negative_rate": 1.0,
    }))
    rc = m.main([
        "--answerable", str(ans_path), "--abs", str(abs_path),
        "--out-dir", str(out_dir), "--skip-controls",
    ] + extra_args)
    assert rc == 0
    return json.loads((out_dir / "rescore_summary.json").read_text())


def test_default_resolution_neither_given_is_api_dated_snapshot(tmp_path, monkeypatch):
    summary = _run_main_minimal(tmp_path, [], monkeypatch)
    assert summary["transport"] == "api"
    assert summary["judge_model"] == "gpt-4o-2024-08-06"


def test_default_resolution_model_with_slash_infers_opencode(tmp_path, monkeypatch):
    summary = _run_main_minimal(
        tmp_path, ["--model", "openai/gpt-5.6-sol"], monkeypatch)
    assert summary["transport"] == "opencode"
    assert summary["judge_model"] == "openai/gpt-5.6-sol"


def test_default_resolution_model_without_slash_infers_api(tmp_path, monkeypatch):
    summary = _run_main_minimal(
        tmp_path, ["--model", "gpt-4o-2024-11-20"], monkeypatch)
    assert summary["transport"] == "api"
    assert summary["judge_model"] == "gpt-4o-2024-11-20"


def test_explicit_transport_overrides_model_slash_inference(tmp_path, monkeypatch):
    # A "/"-bearing model would normally infer opencode; an explicit
    # --transport api wins.
    summary = _run_main_minimal(
        tmp_path, ["--model", "openai/gpt-4o", "--transport", "api"],
        monkeypatch)
    assert summary["transport"] == "api"
    assert summary["judge_model"] == "openai/gpt-4o"


def test_row_and_summary_record_resolved_snapshot(tmp_path, monkeypatch):
    summary = _run_main_minimal(
        tmp_path, ["--model", "gpt-4o-2024-08-06"], monkeypatch,
        judge_return=(True, "yes", 1, "gpt-4o-2024-08-06"))
    assert summary["resolved_snapshots"] == ["gpt-4o-2024-08-06"]


# ---------------------------------------------------------------------------
# CLI surface — no inline key-value flag exists, only a file-path flag
# ---------------------------------------------------------------------------

def test_no_inline_api_key_cli_flag_exists(capsys):
    with pytest.raises(SystemExit):
        m.main(["--help"])
    help_text = capsys.readouterr().out
    assert "--api-key-file" in help_text
    assert "--api-key " not in help_text
    assert "--api-key\n" not in help_text
