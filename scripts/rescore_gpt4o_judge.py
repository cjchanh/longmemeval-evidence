#!/usr/bin/env python3
"""Rescore frozen LME reader responses with the canonical GPT-4o judge lane.

Why: LongMemEval (Wu et al., ICLR 2025) reports its published numbers using
a GPT-4o-class LLM judge with per-type rubric prompts (evaluate_qa.py
get_anscheck_prompt). Archivist's public SOTA number needs a like-for-like
rescore against that exact ruler. This script supports TWO judge transports:

  --transport opencode  `opencode run --pure -m <model>` over stdin (the oc
                        lane retry/chrome-strip pattern, reused from
                        oc_flash_lane.py). Model carries a provider prefix,
                        e.g. openai/gpt-4o.
  --transport api       Direct HTTPS to https://api.openai.com/v1/chat/
                        completions via urllib. Model is a bare OpenAI model
                        id, e.g. gpt-4o-2024-08-06 (the dated snapshot is the
                        default for reproducibility; plain "gpt-4o" is
                        accepted but resolves server-side to whatever
                        snapshot OpenAI currently aliases it to — the
                        response's own "model" field, captured as
                        resolved_snapshot, records exactly which one ran).
                        The API key is read ONLY from a local file
                        (--api-key-file, default ~/.config/openai/api_key,
                        expected 0600) — never accepted as an inline CLI
                        value, never logged, never included in any receipt
                        or error message.

If --transport is not given, it is inferred from --model: a model with a
"/" (provider prefix) implies opencode; a bare model id implies api. If
NEITHER --transport nor --model is given, the default is
--transport api --model gpt-4o-2024-08-06.

2026-08-31: gpt-4o is unreachable on the opencode lane (see probe note
below) but IS reachable via a real, operator-supplied OpenAI API key
(egress resolution ~/.claude/resolutions/EGRESS_20260831_gpt4o_judge.json;
scope: api.openai.com only, LongMemEval public-benchmark judge calls).
The api transport is the one that actually reaches gpt-4o today.

2026-08-30 availability probe: `openai/gpt-4o` is NOT present in this
worktree's opencode lane (`opencode models` lists no gpt-4o variant; a direct
`opencode run --pure -m openai/gpt-4o` call returns the identical generic
"Unexpected server error" signature as a deliberately bogus model name, while
a real model on the same lane, e.g. openai/gpt-5.4-mini, succeeds). Available
openai/* models on this lane at probe time: gpt-5.3-codex-spark, gpt-5.4,
gpt-5.4-fast, gpt-5.4-mini, gpt-5.4-mini-fast, gpt-5.5, gpt-5.5-fast,
gpt-5.6-luna, gpt-5.6-luna-fast, gpt-5.6-sol, gpt-5.6-sol-fast, gpt-5.6-terra,
gpt-5.6-terra-fast. This script stays generic (--model is a CLI arg with no
hardcoded lane restriction) so it starts working the moment a gateway that
does serve gpt-4o (or the paper's exact gpt-4o-2024-08-06 snapshot) is
pointed at it — see check_model_available() below, which fails closed at
run time rather than silently judging on a substitute model.

Rubric source: benchmarks/longmemeval-judge-gate/GROUND_TRUTH_SURVEY.md §2
(verbatim transcription of LongMemEval evaluate_qa.py get_anscheck_prompt,
VERIFIED-LIVE 2026-07-09) — same source rescore_llm_judge.py uses. The
templates below are frozen, version-tagged, and sha256-pinned (see
PROMPT_TEMPLATE_VERSION / PROMPT_TEMPLATES_SHA256) so a silent edit to the
rubric text is caught by tests rather than drifting unnoticed. The
single-session-preference header sentence is elided in the survey; it is
reconstructed here (verbatim from rescore_llm_judge.py) and flagged in the
receipt, same as the base script.

Controls run FIRST and gate the full pass (fail-closed):
  positive: response := gold verbatim      -> judge must say yes
  negative: response := another row's resp -> judge must say no
Either control below threshold aborts with a control receipt and no verdict.

Usage:
  python3 scripts/rescore_gpt4o_judge.py \\
      --answerable eval/dense_chain_reranker_v3_20260830/full470/reader/checkpoint_answerable.jsonl \\
      --abs eval/dense_chain_reranker_v3_20260830/abs/reader/checkpoint_abs.jsonl \\
      --out-dir eval/gpt4o_judge_rescore_20260830 \\
      --model openai/gpt-4o
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

# Reuse the oc lane's retry/chrome-strip regexes rather than re-deriving them
# — same precedent as rescore_llm_judge_flash.py importing _CONTAMINATION
# from oc_flash_lane. These patterns are lane-generic (ANSI escapes and
# opencode wrapper chrome), not GLM-specific, so reuse here is exact, not
# approximate.
from oc_flash_lane import _ANSI, _CHROME_LINE, _CONTAMINATION  # noqa: E402

DEFAULT_MODEL = "openai/gpt-4o"              # opencode transport default
DEFAULT_API_MODEL = "gpt-4o-2024-08-06"      # api transport default (dated
                                              # snapshot, pinned for
                                              # reproducibility; "gpt-4o" is
                                              # accepted but floats)
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODELS_URL = "https://api.openai.com/v1/models"
DEFAULT_API_KEY_FILE = Path.home() / ".config" / "openai" / "api_key"

# ---------------------------------------------------------------------------
# Frozen rubric prompt templates — verbatim from rescore_llm_judge.py, which
# transcribed them from GROUND_TRUTH_SURVEY.md §2 (VERIFIED-LIVE 2026-07-09).
# Frozen here as a separate, independently sha256-pinned copy so this judge
# lane's prompts cannot silently drift if the base script's templates ever
# change for an unrelated reason. Bump PROMPT_TEMPLATE_VERSION and
# PROMPT_TEMPLATES_SHA256 together, deliberately, if the rubric text changes.
# ---------------------------------------------------------------------------
PROMPT_TEMPLATE_VERSION = "longmemeval-official-judge-v1"

BASE_TEMPLATE = (
    "I will give you a question, a correct answer, and a response from a model. "
    "Please answer yes if the response contains the correct answer. Otherwise, "
    "answer no. If the response is equivalent to the correct answer or contains "
    "all the intermediate steps to get the correct answer, you should also answer "
    "yes. If the response only contains a subset of the information required by "
    "the answer, answer no.\n\n"
    "Question: {question}\n\n"
    "Correct Answer: {answer}\n\n"
    "Model Response: {response}\n\n"
    "Is the model response correct? Answer yes or no only."
)

TEMPORAL_ADDITION = (
    " In addition, do not penalize off-by-one errors for the number of days. "
    "If the question asks for the number of days/weeks/months, etc., and the "
    "model makes off-by-one errors (e.g., predicting 19 days when the answer "
    "is 18), the model's response is still correct."
)

KU_ADDITION = (
    " If the response contains some previous information along with an updated "
    "answer, the response should be considered as correct as long as the "
    "updated answer is the required answer."
)

# Header sentence reconstructed (survey elides it); rubric semantics verbatim
# from the survey transcription.
SSP_TEMPLATE = (
    "I will give you a question, a rubric for desired personalized response, "
    "and a response from a model. "
    "Please answer yes if the response satisfies the desired response. "
    "Otherwise, answer no. The model does not need to reflect all the points "
    "in the rubric. The response is correct as long as it recalls and utilizes "
    "the user's personal information correctly.\n\n"
    "Question: {question}\n\n"
    "Rubric: {answer}\n\n"
    "Model Response: {response}\n\n"
    "Is the model response correct? Answer yes or no only."
)

ABS_TEMPLATE = (
    "I will give you an unanswerable question, an explanation, and a response "
    "from a model. Please answer yes if the model correctly identifies the "
    "question as unanswerable. The model could say that the information is "
    "incomplete, or some other information is given but the asked information "
    "is not.\n\n"
    "Question: {question}\n\n"
    "Explanation: {answer}\n\n"
    "Model Response: {response}\n\n"
    "Does the model correctly identify the question as unanswerable? "
    "Answer yes or no only."
)

_TEMPLATE_ORDER = (BASE_TEMPLATE, TEMPORAL_ADDITION, KU_ADDITION, SSP_TEMPLATE,
                   ABS_TEMPLATE)
PROMPT_TEMPLATES_SHA256 = hashlib.sha256(
    "\x00".join(_TEMPLATE_ORDER).encode("utf-8")).hexdigest()


def build_prompt(question_type: str, question: str, gold: str, response: str,
                 *, abstention: bool) -> str:
    """Build the exact judge prompt for one row. Mirrors rescore_llm_judge.py
    build_prompt() byte-for-byte (frozen templates above)."""
    if abstention:
        return ABS_TEMPLATE.format(question=question, answer=gold,
                                   response=response)
    if question_type == "single-session-preference":
        return SSP_TEMPLATE.format(question=question, answer=gold,
                                   response=response)
    base = BASE_TEMPLATE
    if question_type == "temporal-reasoning":
        base = base.replace(
            "answer, answer no.\n\n",
            "answer, answer no." + TEMPORAL_ADDITION + "\n\n")
    elif question_type == "knowledge-update":
        base = base.replace(
            "answer, answer no.\n\n",
            "answer, answer no." + KU_ADDITION + "\n\n")
    return base.format(question=question, answer=gold, response=response)


# ---------------------------------------------------------------------------
# Transport: opencode run --pure -m <model>, prompt over stdin, oc lane
# retry/chrome-strip pattern (reused regexes from oc_flash_lane).
# ---------------------------------------------------------------------------

class JudgeTransportError(RuntimeError):
    """Fail-closed judge transport error (exhausted retries, timeout, etc)."""


class JudgeContamination(JudgeTransportError):
    """Response still carries opencode wrapper chrome after stripping."""


class ApiKeyError(JudgeTransportError):
    """API key file missing, unreadable, or empty. Fails closed — never a
    silent empty-key request."""


class ApiAuthError(JudgeTransportError):
    """401/403 from the OpenAI API. Fails closed WITHOUT retry — a bad or
    revoked key does not heal itself with backoff, and retrying an auth
    failure against a live account is its own hazard."""


def read_api_key(path: Path) -> str:
    """Read the OpenAI API key from a local file. The key value NEVER
    travels through argv, an env var this script sets, a log line, or a
    receipt — this is the one place it is read into memory, and the caller
    threads the returned string only into the Authorization header of the
    single outbound request."""
    try:
        key = path.read_text().strip()
    except OSError as exc:
        raise ApiKeyError(f"could not read API key file {path}: {exc}") from exc
    if not key:
        raise ApiKeyError(f"API key file {path} is empty")
    return key


def opencode_judge_once(model: str, prompt: str, timeout_s: int,
                        max_attempts: int,
                        backoff_s: float) -> tuple[bool, str, int, None]:
    """One judge call over the opencode --pure stdin transport.

    Returns (verdict_is_yes, raw_text[:200], attempts_used, resolved_model).
    resolved_model is always None for this transport — opencode does not
    echo back a resolved snapshot id. Retries transients (non-zero exit,
    timeout, empty output) with linear backoff. Contamination (wrapper
    chrome surviving the strip) is NOT retried — it is a transport-contract
    violation, not a transient, so it fails closed immediately rather than
    silently accepting a chrome-laced verdict.
    """
    last = ""
    for attempt in range(1, max_attempts + 1):
        try:
            proc = subprocess.run(
                ["opencode", "run", "--pure", "-m", model],
                input=prompt.encode("utf-8"),
                capture_output=True, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            last = f"timeout after {timeout_s}s"
            time.sleep(backoff_s * attempt)
            continue
        out = _ANSI.sub("", proc.stdout.decode("utf-8", errors="replace"))
        lines = [ln for ln in out.splitlines()
                if not _CHROME_LINE.match(ln.strip())]
        text = "\n".join(lines).strip()
        if proc.returncode != 0 or not text:
            last = (f"rc={proc.returncode} out={text[:120]!r} "
                    f"err={proc.stderr.decode(errors='replace')[:120]!r}")
            time.sleep(backoff_s * attempt)
            continue
        if _CONTAMINATION.match(text):
            raise JudgeContamination(
                f"wrapper chrome survived stripping: {text[:80]!r}")
        return ("yes" in text.lower(), text[:200], attempt, None)
    raise JudgeTransportError(
        f"judge call failed after {max_attempts} attempts: {last}")


def api_judge_once(model: str, prompt: str, timeout_s: int, max_attempts: int,
                   backoff_s: float,
                   api_key_file: Path) -> tuple[bool, str, int, str | None]:
    """One judge call over direct HTTPS to the OpenAI chat/completions API.

    Returns (verdict_is_yes, raw_text[:200], attempts_used, resolved_model)
    where resolved_model is the "model" field OpenAI's own response body
    echoes back — the exact snapshot that served the request, which can
    differ from the requested model id if a floating alias (e.g. "gpt-4o")
    was requested.

    401/403 fails closed immediately, no retry (ApiAuthError). 429/5xx and
    network errors retry with linear backoff, same discipline as the
    opencode transport. The key is read fresh each call (read_api_key is a
    cheap local file read, not a bottleneck against network latency) and is
    placed ONLY in the Authorization header — never in a URL, never in the
    request body, never echoed into any error message this function raises.
    """
    api_key = read_api_key(api_key_file)
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 5,
    }).encode("utf-8")
    last = ""
    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(
            OPENAI_CHAT_COMPLETIONS_URL, data=payload, method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            status = exc.code
            if status in (401, 403):
                # Fail closed, no retry. Never echo headers or key material;
                # status + reason phrase only.
                raise ApiAuthError(
                    f"OpenAI API auth failed: HTTP {status} {exc.reason}. "
                    "Refusing to retry — verify/rotate the key file "
                    f"({api_key_file})."
                ) from None
            last = f"HTTP {status} {exc.reason}"
            time.sleep(backoff_s * attempt)
            continue
        except (urllib.error.URLError, TimeoutError, OSError,
                json.JSONDecodeError) as exc:
            last = f"{type(exc).__name__}: {exc}"
            time.sleep(backoff_s * attempt)
            continue
        try:
            text = str(body["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise JudgeTransportError(
                f"unexpected OpenAI API response shape: {exc}") from exc
        resolved_model = body.get("model")
        if not text:
            last = "empty content in response"
            time.sleep(backoff_s * attempt)
            continue
        return ("yes" in text.lower(), text[:200], attempt, resolved_model)
    raise JudgeTransportError(
        f"API judge call failed after {max_attempts} attempts: {last}")


def judge_once(model: str, prompt: str, timeout_s: int, max_attempts: int,
               backoff_s: float, *, transport: str = "opencode",
               api_key_file: Path | None = None
               ) -> tuple[bool, str, int, str | None]:
    """Transport dispatcher. Default transport is "opencode" (backward
    compatible with every existing call site and test); pass
    transport="api" for the direct-HTTPS OpenAI lane."""
    if transport == "api":
        return api_judge_once(model, prompt, timeout_s, max_attempts,
                              backoff_s, api_key_file or DEFAULT_API_KEY_FILE)
    if transport != "opencode":
        raise ValueError(f"unknown transport: {transport!r}")
    return opencode_judge_once(model, prompt, timeout_s, max_attempts,
                               backoff_s)


def check_model_available(model: str, *, transport: str = "opencode",
                          api_key_file: Path | None = None) -> None:
    """Fail closed if the requested model is not available on the selected
    transport's lane.

    A silent substitution (asking for gpt-4o, silently getting whatever the
    lane falls back to) would produce a number that LOOKS like a GPT-4o
    rescore and isn't.
    """
    if transport == "api":
        api_key = read_api_key(api_key_file or DEFAULT_API_KEY_FILE)
        request = urllib.request.Request(
            OPENAI_MODELS_URL, method="GET",
            headers={"Authorization": f"Bearer {api_key}"})
        try:
            with urllib.request.urlopen(request, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise ApiAuthError(
                    f"OpenAI API auth failed listing models: HTTP {exc.code} "
                    f"{exc.reason}. Verify/rotate the key file."
                ) from None
            raise JudgeTransportError(
                f"could not list OpenAI models: HTTP {exc.code} {exc.reason}"
            ) from None
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
            raise JudgeTransportError(
                f"could not list OpenAI models: {exc}") from exc
        available = {str(m.get("id")) for m in body.get("data", [])}
        if model not in available:
            raise JudgeTransportError(
                f"requested judge model {model!r} is not available via the "
                f"OpenAI API for this key. Refusing to silently substitute. "
                f"gpt-4o* models available: "
                f"{sorted(m for m in available if 'gpt-4o' in m)}")
        return
    try:
        proc = subprocess.run(["opencode", "models"], capture_output=True,
                              text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise JudgeTransportError(
            f"could not enumerate opencode models: {exc}") from exc
    if proc.returncode != 0:
        raise JudgeTransportError(
            f"opencode models exited {proc.returncode}: {proc.stderr[-300:]}")
    available = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    if model not in available:
        raise JudgeTransportError(
            f"requested judge model {model!r} is not available on this "
            f"opencode lane. Refusing to silently substitute. "
            f"openai/* models available: "
            f"{sorted(m for m in available if m.startswith('openai/'))}")


def load_rows(path: Path) -> list[dict]:
    rows = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ---------------------------------------------------------------------------
# Artifact guards — fail-closed refusals, never verdict changes.
#
# Origin: eval/dense_chain_v32_20260830/full-v34-opus_pass1/judge_gpt4o/, where
# 194 of 500 rows carry attempts=0 / llm_judge_raw="" / resolved_snapshot=null —
# the judge was never invoked on them — and every one of those 194 is stored as
# llm_judge_correct=false. A MISSING measurement was written into the same field
# a real "no" verdict uses, and the directory's total (289/500) then read as a
# score. Three mechanics combined to produce it, and each gets one guard here:
#
#   (a) resume keys on question_id EXISTENCE, not freshness, so a second
#       invocation into that out-dir skipped all 194 and judged zero rows;
#   (b) rescore_row() returns a false verdict with attempts=0 and no API call
#       for an empty reader response, and the reader checkpoint it ran against
#       had already been declared "ARTIFACT INVALID — not fit for judging.
#       errors=194 empty=194" by the reader's own run log;
#   (c) control_receipt.json and rescore_summary.json are written
#       unconditionally, so the receipt shipped beside those rows came from a
#       LATER invocation that judged nothing and describes a different row-set
#       than the run that produced the verdicts.
#
# These guards only ever REFUSE. They do not touch judging logic, prompts, the
# rubric, retry behavior, or any scoring path — a run that passes them scores
# byte-identically to a run before they existed. Each is overridable by an
# explicit flag so a deliberate operator workflow is not silently blocked.
# ---------------------------------------------------------------------------

class ArtifactGuardError(RuntimeError):
    """A pre-flight or receipt-write guard refused. Fails closed: the run
    produces no verdict and no receipt rather than an honest-looking one."""


def unjudged_rows(rows: list[dict]) -> list[dict]:
    """Rows the judge was never invoked on (attempts == 0).

    rescore_row() records attempts=0, llm_judge_raw="", resolved_snapshot=None
    when the reader response was empty. That row is an ABSENCE of measurement
    stored in the verdict column — not a "no" from the judge."""
    return [r for r in rows if not r.get("attempts")]


def guard_resume_checkpoint(ckpt_path: Path, *,
                            allow_unjudged_resume: bool = False) -> None:
    """(a) Refuse to resume into an out-dir holding never-judged rows.

    Resume skips any question_id already present in rescored.jsonl, so those
    rows would stay unjudged for every future invocation while the summary
    re-published their absences as verdicts. A clean --out-dir is required."""
    if not ckpt_path.exists():
        return
    rows = load_rows(ckpt_path)
    stale = unjudged_rows(rows)
    if not stale:
        return
    types = ", ".join(f"{t}={n}" for t, n in sorted(
        Counter(r.get("question_type", "") for r in stale).items()))
    msg = (
        f"REFUSING TO RESUME — {ckpt_path} already holds {len(stale)} of "
        f"{len(rows)} rows with attempts=0 (judge never invoked; "
        f"llm_judge_raw empty, resolved_snapshot null), all of them stored as "
        f"llm_judge_correct=false. Those are missing measurements, not "
        f"verdicts, and resume keys on question_id existence rather than "
        f"freshness — resuming here would judge zero of them and re-publish "
        f"the same partial artifact as a score. Unjudged by question type: "
        f"{types}. Use a clean --out-dir, or pass --allow-unjudged-resume to "
        f"override deliberately."
    )
    if allow_unjudged_resume:
        print("WARNING (--allow-unjudged-resume): " + msg, flush=True)
        return
    raise ArtifactGuardError(msg)


def guard_reader_checkpoint(path: Path, rows: list[dict], *,
                            allow_empty_responses: bool = False) -> None:
    """(b) Refuse to judge a reader checkpoint that carries empty responses.

    Mirrors the reader's own fail-closed line ("ARTIFACT INVALID — not fit for
    judging. errors=N empty=N"). An empty response is scored false with
    attempts=0 and no judge call, so judging such a checkpoint writes absences
    into the verdict column at exactly the rate the reader failed."""
    empty = [r for r in rows if not (r.get("response") or "").strip()]
    errored = [r for r in rows if r.get("error")]
    if not (empty or errored):
        return
    msg = (
        f"REFUSING TO JUDGE — reader checkpoint {path} is not fit for "
        f"judging: errors={len(errored)} empty={len(empty)} of {len(rows)} "
        f"rows. An empty reader response is recorded as "
        f"llm_judge_correct=false with attempts=0 and NO judge call, so this "
        f"pass would write {len(empty)} absences into the verdict column and "
        f"report them as a score. Re-run the reader until the checkpoint is "
        f"complete, or pass --allow-empty-responses to override deliberately."
    )
    if allow_empty_responses:
        print("WARNING (--allow-empty-responses): " + msg, flush=True)
        return
    raise ArtifactGuardError(msg)


def _control_receipt_row_ids(receipt: dict) -> list[str] | None:
    """Sorted question_ids a control receipt describes, or None if it does not
    record them (a legacy or hand-written receipt whose row-set is unknowable
    — which fails closed, because unknown is not the same as identical)."""
    records = receipt.get("records")
    if not isinstance(records, list):
        return None
    ids = [r.get("question_id") for r in records if isinstance(r, dict)]
    if not ids or any(i is None for i in ids):
        return None
    return sorted(ids)


def summary_row_ids_sha256(scored: list[dict]) -> str:
    """Fingerprint of the exact row-set a summary describes. Written into the
    summary so a later invocation can tell "same rows, rewritten" from
    "different rows, silently replacing the shipped receipt"."""
    payload = "\n".join(sorted(
        f"{r.get('question_id')}\t{int(bool(r.get('abstention')))}"
        for r in scored
    ))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_receipt(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def guard_control_receipt_overwrite(path: Path, sample_ids: list[str], *,
                                    allow_receipt_overwrite: bool = False
                                    ) -> None:
    """(c-1) Refuse to overwrite a control receipt describing other rows.

    Called BEFORE the control arms run, so a refusal costs no judge calls. The
    shipped incident receipt reads positive 12/12 over an artifact whose own
    run log says positive 11/11: a later invocation with a different control
    sample replaced the receipt of the run that actually produced the
    verdicts."""
    if not path.exists():
        return
    existing = _read_receipt(path)
    old_ids = _control_receipt_row_ids(existing) if existing else None
    new_ids = sorted(sample_ids)
    if old_ids == new_ids:
        return
    detail = ("it records no per-row question_ids, so its row-set cannot be "
              "shown to match" if old_ids is None
              else f"it describes a row-set of {len(old_ids)}, this "
                   f"invocation controls {len(new_ids)}")
    msg = (
        f"REFUSING TO OVERWRITE — {path} already exists and {detail}. A "
        f"control receipt is the evidence for the verdicts shipped beside it; "
        f"replacing it with a different invocation's row-set makes the "
        f"receipt describe a run that did not produce those verdicts. Use a "
        f"clean --out-dir, or pass --allow-receipt-overwrite to override "
        f"deliberately."
    )
    if allow_receipt_overwrite:
        print("WARNING (--allow-receipt-overwrite): " + msg, flush=True)
        return
    raise ArtifactGuardError(msg)


def guard_summary_overwrite(path: Path, row_ids_sha256: str, *,
                            allow_receipt_overwrite: bool = False) -> None:
    """(c-2) Refuse to overwrite a rescore summary describing other rows."""
    if not path.exists():
        return
    existing = _read_receipt(path)
    old = existing.get("row_ids_sha256") if existing else None
    if old == row_ids_sha256:
        return
    detail = ("carries no row_ids_sha256, so its row-set cannot be shown to "
              "match" if not old
              else f"describes row-set {old[:12]}…, this invocation scored "
                   f"{row_ids_sha256[:12]}…")
    msg = (
        f"REFUSING TO OVERWRITE — {path} already exists and {detail}. The "
        f"summary is the receipt for the rows in rescored.jsonl; replacing it "
        f"from an invocation over a different row-set is how a green receipt "
        f"comes to sit on top of a partial artifact. Use a clean --out-dir, "
        f"or pass --allow-receipt-overwrite to override deliberately."
    )
    if allow_receipt_overwrite:
        print("WARNING (--allow-receipt-overwrite): " + msg, flush=True)
        return
    raise ArtifactGuardError(msg)


def summary_caveats(model: str) -> list[str]:
    """Provenance-accurate caveats for whatever model actually ran."""
    caveats = [
        "Responses are frozen from the named input checkpoints. Retrieval and "
        "reader provenance remain governed by those checkpoints' run receipts; "
        "this script changes only the ruler.",
    ]
    if model != "openai/gpt-4o" and not model.startswith("openai/gpt-4o-"):
        caveats.insert(0, (
            f"Judge model is {model}, not gpt-4o (LongMemEval's canonical "
            "gpt-4o-2024-08-06 judge); cross-judge agreement with the "
            "canonical judge is NOT established by this run."
        ))
    else:
        caveats.insert(0, (
            f"Judge model is {model}. Exact snapshot parity with the "
            "LongMemEval paper's gpt-4o-2024-08-06 judge is not guaranteed "
            "unless the opencode gateway pins that exact snapshot — record "
            "the resolved snapshot from the provider if available."
        ))
    return caveats


def run_controls(rows: list[dict], model: str, n: int, timeout_s: int,
                 max_attempts: int, backoff_s: float, out_dir: Path, *,
                 transport: str = "opencode",
                 api_key_file: Path | None = None,
                 allow_receipt_overwrite: bool = False) -> dict:
    """Positive+negative judge controls, gating the full pass. Fail-closed:
    either arm below threshold aborts before any real row is judged."""
    rng = random.Random(20260830)
    eligible = [r for r in rows if r.get("response") and r.get("gold")]
    sample = rng.sample(eligible, min(n, len(eligible)))
    # Guard (c-1) runs here, before the first control call: a refusal must
    # cost no judge invocations, and the receipt must never be replaced by an
    # invocation controlling a different row-set.
    guard_control_receipt_overwrite(
        out_dir / "control_receipt.json",
        [r["question_id"] for r in sample],
        allow_receipt_overwrite=allow_receipt_overwrite)
    pos_total = pos_pass = neg_pass = 0
    records = []
    for row in sample:
        q, g, t = row["question"], row["gold"], row.get("question_type", "")
        # positive: gold verbatim as the response. INVALID for
        # single-session-preference — gold there is a rubric, and a rubric
        # pasted as a response does not satisfy itself; a correct judge says
        # no. Excluded from the positive arm (kept in the negative arm).
        pos_ok = None
        raw = ""
        if t != "single-session-preference":
            p = build_prompt(t, q, g, g, abstention=False)
            yes, raw, _, _ = judge_once(model, p, timeout_s, max_attempts,
                                        backoff_s, transport=transport,
                                        api_key_file=api_key_file)
            pos_ok = yes
            pos_total += 1
            pos_pass += int(pos_ok)
        # negative: a different row's response
        other = rng.choice([r for r in eligible
                            if r["question_id"] != row["question_id"]])
        p = build_prompt(t, q, g, other["response"], abstention=False)
        yes, raw_n, _, _ = judge_once(model, p, timeout_s, max_attempts,
                                      backoff_s, transport=transport,
                                      api_key_file=api_key_file)
        neg_ok = not yes
        neg_pass += int(neg_ok)
        records.append({"question_id": row["question_id"],
                        "question_type": t,
                        "positive_pass": pos_ok, "negative_pass": neg_ok,
                        "positive_raw": raw, "negative_raw": raw_n})
    result = {
        "n": len(sample),
        "n_positive_eligible": pos_total,
        "positive_pass": pos_pass,
        "negative_pass": neg_pass,
        "positive_rate": pos_pass / max(1, pos_total),
        "negative_rate": neg_pass / max(1, len(sample)),
        "threshold": 0.9,
        "ssp_excluded_from_positive_arm": True,
        "records": records,
    }
    (out_dir / "control_receipt.json").write_text(json.dumps(result, indent=1))
    return result


def rescore_row(row: dict, *, abstention: bool, model: str, timeout_s: int,
                max_attempts: int, backoff_s: float,
                transport: str = "opencode",
                api_key_file: Path | None = None) -> dict:
    response = row.get("response") or ""
    if not response:
        verdict, raw, attempts, resolved_snapshot = False, "", 0, None
    else:
        prompt = build_prompt(row.get("question_type", ""), row["question"],
                              row["gold"], response, abstention=abstention)
        verdict, raw, attempts, resolved_snapshot = judge_once(
            model, prompt, timeout_s, max_attempts, backoff_s,
            transport=transport, api_key_file=api_key_file)
    return {
        "question_id": row["question_id"],
        "question_type": row.get("question_type", ""),
        "abstention": abstention,
        "llm_judge_correct": verdict,
        "llm_judge_raw": raw,
        "attempts": attempts,
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "transport": transport,
        "resolved_snapshot": resolved_snapshot,
        "prompt_version": PROMPT_TEMPLATE_VERSION,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--answerable", required=True)
    ap.add_argument("--abs", dest="abs_path", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--model", default=None,
                    help="opencode transport: provider-prefixed id, e.g. "
                         "openai/gpt-4o. api transport: bare OpenAI model "
                         f"id, e.g. {DEFAULT_API_MODEL}. Default depends on "
                         "--transport (see module docstring).")
    ap.add_argument("--transport", choices=["opencode", "api"], default=None,
                    help="default: api if --model has no '/' provider "
                         "prefix (or if --model is also omitted), else "
                         "opencode.")
    ap.add_argument("--api-key-file", default=str(DEFAULT_API_KEY_FILE),
                    help="path to a file holding the OpenAI API key. The "
                         "key value is NEVER accepted as an inline CLI arg.")
    ap.add_argument("--timeout-s", type=int, default=300)
    ap.add_argument("--max-attempts", type=int, default=4)
    ap.add_argument("--backoff-s", type=float, default=1.0)
    ap.add_argument("--control-n", type=int, default=20)
    ap.add_argument("--spec",
                    help="dispatch-gate spec path for this egress run "
                         "(classification only; not read by this script).")
    ap.add_argument("--skip-controls", action="store_true",
                    help="resume mode only; controls must already have passed")
    ap.add_argument("--skip-availability-check", action="store_true",
                    help="test/CI hook only; do not use for a real rescore")
    # Artifact-guard overrides. Each guard fails closed by default; these
    # exist so a deliberate operator workflow is refusable-but-possible
    # rather than silently permitted. See the Artifact guards section above.
    ap.add_argument("--allow-unjudged-resume", action="store_true",
                    help="guard (a) override: resume into an out-dir whose "
                         "rescored.jsonl already holds attempts=0 rows the "
                         "judge was never invoked on. Those rows stay "
                         "unjudged.")
    ap.add_argument("--allow-empty-responses", action="store_true",
                    help="guard (b) override: judge a reader checkpoint that "
                         "contains empty/errored responses. Each empty "
                         "response is scored false with no judge call.")
    ap.add_argument("--allow-receipt-overwrite", action="store_true",
                    help="guard (c) override: replace an existing "
                         "control_receipt.json / rescore_summary.json that "
                         "describes a different row-set than this run.")
    args = ap.parse_args(argv)

    # Transport/model default resolution (see module docstring):
    #   both omitted            -> api / gpt-4o-2024-08-06
    #   --model given, no "/"   -> api (unless --transport overrides)
    #   --model given, has "/"  -> opencode (unless --transport overrides)
    if args.transport is None:
        args.transport = ("opencode" if args.model and "/" in args.model
                          else "api")
    if args.model is None:
        args.model = DEFAULT_API_MODEL if args.transport == "api" else DEFAULT_MODEL
    args.api_key_file = Path(args.api_key_file)

    if not args.skip_availability_check:
        check_model_available(args.model, transport=args.transport,
                              api_key_file=args.api_key_file)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ans_rows = load_rows(Path(args.answerable))
    abs_rows = load_rows(Path(args.abs_path))
    ckpt_path = out_dir / "rescored.jsonl"

    # Pre-flight artifact guards (a) and (b). They run before the control
    # phase so a refusal neither spends a judge call nor touches the receipt
    # already sitting in out_dir.
    try:
        guard_reader_checkpoint(
            Path(args.answerable), ans_rows,
            allow_empty_responses=args.allow_empty_responses)
        guard_reader_checkpoint(
            Path(args.abs_path), abs_rows,
            allow_empty_responses=args.allow_empty_responses)
        guard_resume_checkpoint(
            ckpt_path, allow_unjudged_resume=args.allow_unjudged_resume)
    except ArtifactGuardError as exc:
        print(str(exc), flush=True)
        return 2

    if not args.skip_controls:
        try:
            ctrl = run_controls(
                ans_rows, args.model, args.control_n,
                args.timeout_s, args.max_attempts, args.backoff_s,
                out_dir, transport=args.transport,
                api_key_file=args.api_key_file,
                allow_receipt_overwrite=args.allow_receipt_overwrite)
        except ArtifactGuardError as exc:
            print(str(exc), flush=True)
            return 2
        print(f"controls: positive {ctrl['positive_pass']}/"
              f"{ctrl['n_positive_eligible']} negative {ctrl['negative_pass']}/"
              f"{ctrl['n']}", flush=True)
        if (ctrl["positive_rate"] < 0.9) or (ctrl["negative_rate"] < 0.9):
            print("CONTROL FAILURE — aborting, no verdict. "
                  "See control_receipt.json", flush=True)
            return 2
    elif not (out_dir / "control_receipt.json").exists():
        print("--skip-controls without a prior control receipt — refusing.",
              flush=True)
        return 2

    done_ids = set()
    if ckpt_path.exists():
        for row in load_rows(ckpt_path):
            done_ids.add(row["question_id"])

    def rescore(rows: list[dict], *, abstention: bool) -> None:
        with ckpt_path.open("a") as fh:
            for i, row in enumerate(rows):
                if row["question_id"] in done_ids:
                    continue
                record = rescore_row(row, abstention=abstention,
                                     model=args.model,
                                     timeout_s=args.timeout_s,
                                     max_attempts=args.max_attempts,
                                     backoff_s=args.backoff_s,
                                     transport=args.transport,
                                     api_key_file=args.api_key_file)
                fh.write(json.dumps(record) + "\n")
                fh.flush()
                if (i + 1) % 25 == 0:
                    print(f"  {'abs' if abstention else 'ans'} {i+1}/{len(rows)}",
                          flush=True)

    rescore(ans_rows, abstention=False)
    rescore(abs_rows, abstention=True)

    scored = load_rows(ckpt_path)
    ans = [r for r in scored if not r["abstention"]]
    abst = [r for r in scored if r["abstention"]]
    per_type: dict[str, dict[str, int]] = defaultdict(lambda: {"n": 0, "llm": 0})
    for r in ans:
        b = per_type[r["question_type"]]
        b["n"] += 1
        b["llm"] += int(r["llm_judge_correct"])
    resolved_snapshots = sorted({
        r["resolved_snapshot"] for r in scored
        if r.get("resolved_snapshot")
    })
    summary = {
        "schema": "cds/lme-qa-gpt4o-judge-rescore/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "judge_model": args.model,
        "transport": args.transport,
        "resolved_snapshots": resolved_snapshots,
        "prompt_template_version": PROMPT_TEMPLATE_VERSION,
        "prompt_templates_sha256": PROMPT_TEMPLATES_SHA256,
        "rubric_source": ("benchmarks/longmemeval-judge-gate/"
                          "GROUND_TRUTH_SURVEY.md §2 (official templates; "
                          "SSP header sentence reconstructed)"),
        "inputs": {"answerable": args.answerable, "abs": args.abs_path},
        # Row-set fingerprint of exactly the rows this summary describes.
        # Guard (c-2) compares it against any summary already in out_dir so a
        # later invocation over different rows cannot silently replace the
        # receipt for the shipped verdicts.
        "row_ids_sha256": summary_row_ids_sha256(scored),
        "n_rows": len(scored),
        "n_answerable": len(ans),
        "llm_judge_accuracy": (sum(r["llm_judge_correct"] for r in ans)
                               / max(1, len(ans))),
        "per_type": {t: {"n": b["n"], "llm_acc": b["llm"] / max(1, b["n"])}
                     for t, b in sorted(per_type.items())},
        "abstention": {
            "n": len(abst),
            "llm_judge_refusal_recognized": sum(r["llm_judge_correct"]
                                                for r in abst),
        },
        "caveats": summary_caveats(args.model),
    }
    summary_path = out_dir / "rescore_summary.json"
    try:
        guard_summary_overwrite(
            summary_path, summary["row_ids_sha256"],
            allow_receipt_overwrite=args.allow_receipt_overwrite)
    except ArtifactGuardError as exc:
        print(str(exc), flush=True)
        return 2
    summary_path.write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: summary[k] for k in
                      ("judge_model", "transport", "resolved_snapshots",
                       "llm_judge_accuracy")}, indent=1))
    print("per_type:", json.dumps(summary["per_type"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
