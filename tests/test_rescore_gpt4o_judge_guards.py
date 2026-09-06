"""Tests for the artifact guards in scripts/rescore_gpt4o_judge.py.

No model calls: judge_once / check_model_available are always mocked via
monkeypatch, exactly as in test_rescore_gpt4o_judge.py.

The guards are refusals only. Each test asserts BOTH halves of that contract:
the refusal fires on the shape it exists for, and it does not fire on a clean
run — a guard that blocks a legitimate pass is as much a defect as one that
lets the incident through. The last section replays the guard against the
actual released judge_gpt4o/ artifact whose 194 never-judged rows are the
reason these guards exist.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import rescore_gpt4o_judge as m  # noqa: E402

RELEASED_PARTIAL = (
    REPO / "eval/dense_chain_v32_20260830/full-v34-opus_pass1"
    / "judge_gpt4o/rescored.jsonl"
)
AUTHORITATIVE_DIRS = (
    "eval/dense_chain_v32_20260830/full-v34-opus_pass1/judge_gpt4o_v2",
    "eval/dense_chain_v32_20260830/full-v34-opus_pass1/judge_gpt4o_repro_20260901",
    "eval/dense_chain_v32_20260830/full-v34-opus_pass2/judge_gpt4o",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _judged_row(qid: str, *, correct: bool = True, attempts: int = 1) -> dict:
    return {
        "question_id": qid, "question_type": "multi-session",
        "abstention": False, "llm_judge_correct": correct,
        "llm_judge_raw": "yes" if correct else "no", "attempts": attempts,
        "scored_at": "2026-09-01T00:00:00+00:00", "model": "gpt-4o-2024-08-06",
        "transport": "api", "resolved_snapshot": "gpt-4o-2024-08-06",
        "prompt_version": m.PROMPT_TEMPLATE_VERSION,
    }


def _unjudged_row(qid: str) -> dict:
    """The incident shape: attempts 0, empty raw, null snapshot, scored false."""
    row = _judged_row(qid, correct=False, attempts=0)
    row.update({"llm_judge_raw": "", "resolved_snapshot": None})
    return row


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def _reader_rows(n: int = 4) -> list[dict]:
    return [{
        "question_id": f"q{i}", "question_type": "multi-session",
        "question": f"question {i}?", "gold": f"gold-{i}",
        "response": f"gold-{i}", "error": None,
    } for i in range(n)]


def _discriminating_judge(model, prompt, timeout_s, max_attempts, backoff_s,
                          **kw):
    answer = re.search(r"(?:Correct Answer|Explanation): (.*?)\n\n", prompt)
    response = re.search(r"Model Response: (.*?)\n\n", prompt)
    if answer and response:
        match = answer.group(1) == response.group(1)
        return (match, "yes" if match else "no", 1, None)
    return (True, "yes", 1, None)


def _run_main(tmp_path, monkeypatch, *, ans_rows, abs_rows=(), extra=(),
              judge=_discriminating_judge, out_dir=None):
    monkeypatch.setattr(m, "check_model_available", lambda model, **k: None)
    monkeypatch.setattr(m, "judge_once", judge)
    ans_path = _write_jsonl(tmp_path / "answerable.jsonl", list(ans_rows))
    abs_path = _write_jsonl(tmp_path / "abs.jsonl", list(abs_rows))
    out_dir = out_dir or (tmp_path / "out")
    return m.main([
        "--answerable", str(ans_path), "--abs", str(abs_path),
        "--out-dir", str(out_dir), "--control-n", "4",
    ] + list(extra)), out_dir


# ---------------------------------------------------------------------------
# unjudged_rows() — the shared predicate
# ---------------------------------------------------------------------------

def test_unjudged_rows_selects_attempts_zero_only():
    rows = [_judged_row("a"), _unjudged_row("b"), _judged_row("c", attempts=3)]
    assert [r["question_id"] for r in m.unjudged_rows(rows)] == ["b"]


def test_unjudged_rows_treats_missing_attempts_key_as_unjudged():
    row = _judged_row("a")
    del row["attempts"]
    assert m.unjudged_rows([row]) == [row]


# ---------------------------------------------------------------------------
# Guard (a) — refuse to resume into an out-dir holding never-judged rows
# ---------------------------------------------------------------------------

def test_guard_resume_refuses_checkpoint_with_unjudged_rows(tmp_path):
    ckpt = _write_jsonl(tmp_path / "rescored.jsonl",
                        [_judged_row("a"), _unjudged_row("b"),
                         _unjudged_row("c")])
    with pytest.raises(m.ArtifactGuardError) as exc:
        m.guard_resume_checkpoint(ckpt)
    msg = str(exc.value)
    assert "REFUSING TO RESUME" in msg
    assert "2 of 3" in msg               # names the count, not just the shape
    assert "attempts=0" in msg
    assert "--allow-unjudged-resume" in msg


def test_guard_resume_allows_fully_judged_checkpoint(tmp_path):
    ckpt = _write_jsonl(tmp_path / "rescored.jsonl",
                        [_judged_row("a"), _judged_row("b")])
    m.guard_resume_checkpoint(ckpt)  # must not raise


def test_guard_resume_allows_absent_checkpoint(tmp_path):
    m.guard_resume_checkpoint(tmp_path / "nope.jsonl")  # must not raise


def test_guard_resume_override_warns_instead_of_raising(tmp_path, capsys):
    ckpt = _write_jsonl(tmp_path / "rescored.jsonl", [_unjudged_row("b")])
    m.guard_resume_checkpoint(ckpt, allow_unjudged_resume=True)
    out = capsys.readouterr().out
    assert "WARNING (--allow-unjudged-resume)" in out


def test_main_refuses_resume_into_partial_out_dir_without_judging(
        tmp_path, monkeypatch):
    calls = []

    def counting_judge(*a, **k):
        calls.append(1)
        return (True, "yes", 1, None)

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _write_jsonl(out_dir / "rescored.jsonl",
                 [_judged_row("q0"), _unjudged_row("q1")])
    receipt = out_dir / "control_receipt.json"
    receipt.write_text('{"sentinel": true}')
    rc, _ = _run_main(tmp_path, monkeypatch, ans_rows=_reader_rows(4),
                      judge=counting_judge, out_dir=out_dir)
    assert rc == 2
    assert not calls, "refusal must cost zero judge invocations"
    # and the pre-existing receipt is untouched by the refused run
    assert json.loads(receipt.read_text()) == {"sentinel": True}


def test_main_allows_resume_into_fully_judged_out_dir(tmp_path, monkeypatch):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _write_jsonl(out_dir / "rescored.jsonl", [_judged_row("q0")])
    rc, out_dir = _run_main(tmp_path, monkeypatch, ans_rows=_reader_rows(4),
                            out_dir=out_dir)
    assert rc == 0
    scored = [json.loads(l) for l in
              (out_dir / "rescored.jsonl").read_text().splitlines()]
    assert len(scored) == 4  # q0 resumed (skipped), q1..q3 judged


# ---------------------------------------------------------------------------
# Guard (b) — refuse a reader checkpoint carrying empty/errored responses
# ---------------------------------------------------------------------------

def test_guard_reader_checkpoint_refuses_empty_responses_and_names_count(
        tmp_path):
    rows = _reader_rows(3)
    rows[0]["response"] = ""
    rows[1]["response"] = "   "
    with pytest.raises(m.ArtifactGuardError) as exc:
        m.guard_reader_checkpoint(tmp_path / "checkpoint_answerable.jsonl",
                                  rows)
    msg = str(exc.value)
    assert "REFUSING TO JUDGE" in msg
    assert "empty=2" in msg and "of 3" in msg
    assert "errors=0" in msg
    assert "--allow-empty-responses" in msg


def test_guard_reader_checkpoint_refuses_errored_rows(tmp_path):
    rows = _reader_rows(2)
    rows[0]["error"] = "timeout"
    with pytest.raises(m.ArtifactGuardError) as exc:
        m.guard_reader_checkpoint(tmp_path / "ckpt.jsonl", rows)
    assert "errors=1" in str(exc.value)


def test_guard_reader_checkpoint_allows_complete_checkpoint(tmp_path):
    m.guard_reader_checkpoint(tmp_path / "ckpt.jsonl", _reader_rows(3))


def test_guard_reader_checkpoint_allows_empty_file(tmp_path):
    m.guard_reader_checkpoint(tmp_path / "ckpt.jsonl", [])


def test_guard_reader_checkpoint_override_warns_instead_of_raising(
        tmp_path, capsys):
    rows = _reader_rows(2)
    rows[0]["response"] = ""
    m.guard_reader_checkpoint(tmp_path / "ckpt.jsonl", rows,
                              allow_empty_responses=True)
    assert "WARNING (--allow-empty-responses)" in capsys.readouterr().out


def test_main_refuses_incomplete_reader_checkpoint_without_judging(
        tmp_path, monkeypatch):
    calls = []

    def counting_judge(*a, **k):
        calls.append(1)
        return (True, "yes", 1, None)

    rows = _reader_rows(4)
    rows[0]["response"] = ""
    rc, out_dir = _run_main(tmp_path, monkeypatch, ans_rows=rows,
                            judge=counting_judge)
    assert rc == 2
    assert not calls
    assert not (out_dir / "rescored.jsonl").exists()
    assert not (out_dir / "control_receipt.json").exists()


def test_main_override_lets_incomplete_checkpoint_through(
        tmp_path, monkeypatch):
    rows = _reader_rows(4)
    rows[0]["response"] = ""
    rc, out_dir = _run_main(tmp_path, monkeypatch, ans_rows=rows,
                            extra=["--allow-empty-responses"])
    assert rc == 0
    scored = [json.loads(l) for l in
              (out_dir / "rescored.jsonl").read_text().splitlines()]
    # the override preserves the pre-guard behavior exactly: the empty row is
    # still recorded false with attempts 0 and no judge call
    empty_row = next(r for r in scored if r["question_id"] == "q0")
    assert empty_row["attempts"] == 0
    assert empty_row["llm_judge_correct"] is False


# ---------------------------------------------------------------------------
# Guard (c-1) — control receipt overwrite
# ---------------------------------------------------------------------------

def test_guard_control_receipt_allows_absent_receipt(tmp_path):
    m.guard_control_receipt_overwrite(tmp_path / "control_receipt.json",
                                      ["a", "b"])


def test_guard_control_receipt_allows_identical_row_set(tmp_path):
    path = tmp_path / "control_receipt.json"
    path.write_text(json.dumps({"records": [{"question_id": "b"},
                                            {"question_id": "a"}]}))
    m.guard_control_receipt_overwrite(path, ["a", "b"])  # order-insensitive


def test_guard_control_receipt_refuses_different_row_set(tmp_path):
    path = tmp_path / "control_receipt.json"
    path.write_text(json.dumps({"records": [{"question_id": "a"},
                                            {"question_id": "b"}]}))
    with pytest.raises(m.ArtifactGuardError) as exc:
        m.guard_control_receipt_overwrite(path, ["a", "b", "c"])
    msg = str(exc.value)
    assert "REFUSING TO OVERWRITE" in msg
    assert "describes a row-set of 2" in msg and "controls 3" in msg
    assert "--allow-receipt-overwrite" in msg


def test_guard_control_receipt_refuses_legacy_receipt_without_row_ids(tmp_path):
    """Unknown row-set is not the same as identical — fail closed."""
    path = tmp_path / "control_receipt.json"
    path.write_text(json.dumps({"n": 12, "positive_rate": 1.0}))
    with pytest.raises(m.ArtifactGuardError) as exc:
        m.guard_control_receipt_overwrite(path, ["a"])
    assert "records no per-row question_ids" in str(exc.value)


def test_guard_control_receipt_refuses_unreadable_receipt(tmp_path):
    path = tmp_path / "control_receipt.json"
    path.write_text("{not json")
    with pytest.raises(m.ArtifactGuardError):
        m.guard_control_receipt_overwrite(path, ["a"])


def test_guard_control_receipt_override_warns_instead_of_raising(
        tmp_path, capsys):
    path = tmp_path / "control_receipt.json"
    path.write_text(json.dumps({"records": [{"question_id": "a"}]}))
    m.guard_control_receipt_overwrite(path, ["z"],
                                      allow_receipt_overwrite=True)
    assert "WARNING (--allow-receipt-overwrite)" in capsys.readouterr().out


def test_run_controls_refuses_before_spending_a_judge_call(
        tmp_path, monkeypatch):
    calls = []

    def counting_judge(*a, **k):
        calls.append(1)
        return (True, "yes", 1, None)

    monkeypatch.setattr(m, "judge_once", counting_judge)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    stale = out_dir / "control_receipt.json"
    stale.write_text(json.dumps({"records": [{"question_id": "other"}]}))
    with pytest.raises(m.ArtifactGuardError):
        m.run_controls(_reader_rows(4), "gpt-4o-2024-08-06", n=4, timeout_s=10,
                       max_attempts=1, backoff_s=0.0, out_dir=out_dir)
    assert not calls
    # the shipped receipt is still the one that describes the shipped verdicts
    assert json.loads(stale.read_text())["records"][0]["question_id"] == "other"


def test_run_controls_writes_receipt_when_none_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "judge_once", _discriminating_judge)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    result = m.run_controls(_reader_rows(4), "gpt-4o-2024-08-06", n=4,
                            timeout_s=10, max_attempts=1, backoff_s=0.0,
                            out_dir=out_dir)
    assert result["positive_rate"] == 1.0
    assert (out_dir / "control_receipt.json").exists()


# ---------------------------------------------------------------------------
# Guard (c-2) — rescore summary overwrite
# ---------------------------------------------------------------------------

def test_summary_row_ids_sha256_is_row_set_sensitive_and_order_insensitive():
    a = [_judged_row("x"), _judged_row("y")]
    b = [_judged_row("y"), _judged_row("x")]
    c = [_judged_row("x"), _judged_row("z")]
    assert m.summary_row_ids_sha256(a) == m.summary_row_ids_sha256(b)
    assert m.summary_row_ids_sha256(a) != m.summary_row_ids_sha256(c)
    assert len(m.summary_row_ids_sha256(a)) == 64
    int(m.summary_row_ids_sha256(a), 16)


def test_summary_row_ids_sha256_distinguishes_abstention_arm():
    row = _judged_row("x")
    abst = dict(row, abstention=True)
    assert m.summary_row_ids_sha256([row]) != m.summary_row_ids_sha256([abst])


def test_guard_summary_allows_absent_and_identical(tmp_path):
    path = tmp_path / "rescore_summary.json"
    m.guard_summary_overwrite(path, "a" * 64)
    path.write_text(json.dumps({"row_ids_sha256": "a" * 64}))
    m.guard_summary_overwrite(path, "a" * 64)


def test_guard_summary_refuses_different_row_set(tmp_path):
    path = tmp_path / "rescore_summary.json"
    path.write_text(json.dumps({"row_ids_sha256": "a" * 64}))
    with pytest.raises(m.ArtifactGuardError) as exc:
        m.guard_summary_overwrite(path, "b" * 64)
    msg = str(exc.value)
    assert "REFUSING TO OVERWRITE" in msg
    assert "--allow-receipt-overwrite" in msg


def test_guard_summary_refuses_legacy_summary_without_fingerprint(tmp_path):
    path = tmp_path / "rescore_summary.json"
    path.write_text(json.dumps({"schema": "cds/lme-qa-gpt4o-judge-rescore/v1",
                                "n_answerable": 470}))
    with pytest.raises(m.ArtifactGuardError) as exc:
        m.guard_summary_overwrite(path, "b" * 64)
    assert "carries no row_ids_sha256" in str(exc.value)


def test_guard_summary_override_warns_instead_of_raising(tmp_path, capsys):
    path = tmp_path / "rescore_summary.json"
    path.write_text(json.dumps({"row_ids_sha256": "a" * 64}))
    m.guard_summary_overwrite(path, "b" * 64, allow_receipt_overwrite=True)
    assert "WARNING (--allow-receipt-overwrite)" in capsys.readouterr().out


def test_main_summary_records_row_set_fingerprint(tmp_path, monkeypatch):
    rc, out_dir = _run_main(tmp_path, monkeypatch, ans_rows=_reader_rows(4))
    assert rc == 0
    summary = json.loads((out_dir / "rescore_summary.json").read_text())
    scored = [json.loads(l) for l in
              (out_dir / "rescored.jsonl").read_text().splitlines()]
    assert summary["n_rows"] == len(scored) == 4
    assert summary["row_ids_sha256"] == m.summary_row_ids_sha256(scored)


# ---------------------------------------------------------------------------
# Guards do not change scoring
# ---------------------------------------------------------------------------

def test_clean_run_still_scores_normally_under_the_guards(
        tmp_path, monkeypatch):
    rc, out_dir = _run_main(tmp_path, monkeypatch, ans_rows=_reader_rows(4),
                            abs_rows=[{
                                "question_id": "abs0",
                                "question_type": "single-session-user",
                                "question": "q", "gold": "info missing",
                                "response": "info missing", "error": None,
                            }])
    assert rc == 0
    summary = json.loads((out_dir / "rescore_summary.json").read_text())
    assert summary["n_answerable"] == 4
    assert summary["llm_judge_accuracy"] == 1.0
    assert summary["abstention"]["n"] == 1
    scored = [json.loads(l) for l in
              (out_dir / "rescored.jsonl").read_text().splitlines()]
    assert all(r["attempts"] >= 1 for r in scored)


# ---------------------------------------------------------------------------
# Regression — the released partial artifact this guard exists for
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not RELEASED_PARTIAL.exists(),
                    reason="released judge_gpt4o artifact not in this tree")
def test_released_partial_artifact_has_the_incident_signature():
    rows = m.load_rows(RELEASED_PARTIAL)
    stale = m.unjudged_rows(rows)
    assert len(rows) == 500
    assert len(stale) == 194
    # every never-judged row was written as a NEGATIVE verdict, with no raw
    # judge text and no resolved snapshot: absence stored as a verdict
    assert all(r["llm_judge_correct"] is False for r in stale)
    assert all(r["llm_judge_raw"] == "" for r in stale)
    assert all(r["resolved_snapshot"] is None for r in stale)
    # the directory total that must never be read as a score
    assert sum(1 for r in rows if r["llm_judge_correct"]) == 289


@pytest.mark.skipif(not RELEASED_PARTIAL.exists(),
                    reason="released judge_gpt4o artifact not in this tree")
def test_guard_a_detects_the_released_partial_artifact():
    with pytest.raises(m.ArtifactGuardError) as exc:
        m.guard_resume_checkpoint(RELEASED_PARTIAL)
    msg = str(exc.value)
    assert "194 of 500" in msg
    assert "knowledge-update=78" in msg
    assert "single-session-assistant=56" in msg


@pytest.mark.skipif(not RELEASED_PARTIAL.exists(),
                    reason="released judge_gpt4o artifact not in this tree")
@pytest.mark.parametrize("rel", AUTHORITATIVE_DIRS)
def test_guard_a_does_not_fire_on_the_authoritative_judge_dirs(rel):
    """The refusal must be specific to the partial artifact — the pass-1
    authority (judge_gpt4o_v2), the independent re-judge, and pass 2 all
    resume cleanly."""
    ckpt = REPO / rel / "rescored.jsonl"
    if not ckpt.exists():
        pytest.skip(f"{rel} not in this tree")
    rows = m.load_rows(ckpt)
    assert len(rows) == 500
    assert m.unjudged_rows(rows) == []
    m.guard_resume_checkpoint(ckpt)  # must not raise
