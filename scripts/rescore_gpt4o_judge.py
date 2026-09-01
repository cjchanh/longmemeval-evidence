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
from collections import defaultdict
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
                 api_key_file: Path | None = None) -> dict:
    """Positive+negative judge controls, gating the full pass. Fail-closed:
    either arm below threshold aborts before any real row is judged."""
    rng = random.Random(20260830)
    eligible = [r for r in rows if r.get("response") and r.get("gold")]
    sample = rng.sample(eligible, min(n, len(eligible)))
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

    if not args.skip_controls:
        ctrl = run_controls(ans_rows, args.model, args.control_n,
                            args.timeout_s, args.max_attempts, args.backoff_s,
                            out_dir, transport=args.transport,
                            api_key_file=args.api_key_file)
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

    ckpt_path = out_dir / "rescored.jsonl"
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
    (out_dir / "rescore_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: summary[k] for k in
                      ("judge_model", "transport", "resolved_snapshots",
                       "llm_judge_accuracy")}, indent=1))
    print("per_type:", json.dumps(summary["per_type"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
