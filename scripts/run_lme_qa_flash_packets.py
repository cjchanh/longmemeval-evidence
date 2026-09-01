#!/usr/bin/env python3
"""LME QA flash reader that consumes materialized session_blobs.

Sidecar equivalent of ``scripts/run_lme_qa_flash.py``. Packet membership
and body text come ONLY from a reader-materialize JSONL (the exact
compiled packet text, including ``kept_chars`` truncation). Dataset rows
are joined solely for question text/date/type/gold in the prompt and
checkpoint output. Never rehydrates haystack sessions from ranked IDs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from run_lme_qa_cloud_v2 import (  # noqa: E402
    ANSWER_SUFFIX,
    build_reader_prompt_v2,
    load_jsonl,
)
from reader_lane import (  # noqa: E402
    LANE as READER_LANE,
    MODEL,
    TRANSPORT as READER_TRANSPORT,
    LaneError as FlashLaneError,
    _CONTAMINATION,
    generate as flash_generate,
)

PROMPT_VERSION_V2 = "v2-20260827"
# v3.1 (2026-08-30): sentence (b) gained an explicit not-in-sessions clause —
# the v3 "never hedge" contract stripped abstention from the Answer line
# (abs 24/30 vs baseline 25/30; three losses were known-unanswerable).
# v3.2 (2026-08-30, brick_2b): sentence (d) gained a same-timestamp clause.
# The v3 form ("the later user statement governs") forced an ordering the
# evidence index cannot support when two contradictory user statements carry
# the identical timestamp — one of the four SCAFFOLD_MISLED losses in the −9
# forensic. The index now refuses to order such a pair; the prompt now says
# what to do when it refuses. Sentence (b) is unchanged, verbatim.
# v3.3 (2026-08-30, F-1 from the second auditor): the v3.2 clause fired on
# ANY shared timestamp, but the reworked F3 now ORDERS same-session,
# same-minute statements and emits [LATEST] for them. The prompt was telling
# the reader to abandon recency on rows where the index had just resolved
# recency. The clause is now conditioned on the index's own explicit tie
# notice — the only case where the index really cannot order.
# v3.4 (2026-08-31, GPT-4o official-judge rejection attribution,
# gpt4o_rejection_attribution.md): three new generic sentences appended,
# every v3.3 sentence kept verbatim. (e) GRANULARITY/UNITS fixes
# `15745da0` ("three months" vs "3 months and 9 days" — a stated-granularity
# duration re-expressed at day granularity). (f) COMBINED TOTAL fixes
# `37f165cf` ("856" vs "440 and 416" — parts emitted instead of the single
# combined figure the question asked for). (g) EVENT ANCHOR fixes the
# `9a707b81` anchor class (question anchored "how many days ago ... when I
# made the cake" to the question date instead of the cake's own date).
PROMPT_VERSION_V3_FACTS = "v3.4-facts-20260831"

# Facts-row-only instruction sentences (brick_2 P2, sentences a-d, frozen in
# docs/archivist_dense_chain_failure_closure_v2_claim_lock.json; e-g added
# 2026-08-31 per gpt4o_rejection_attribution.md). Typed once here — never in
# run_lme_qa_cloud_v2.py, which stays untouched.
_FACTS_SENTENCES = (
    "The DETERMINISTIC EVIDENCE INDEX above was computed mechanically from "
    "the retrieved sessions; use it to locate, count, and date, and verify "
    "each pointer against the session text.",
    "Commit to exactly one value on the Answer line; never list "
    "alternatives or hedge. If the retrieved sessions do not contain the "
    "information the question needs, the Answer line must say so "
    "explicitly instead of guessing a value.",
    "If the question asks how many more or fewer, answer the difference.",
    "When the user states a fact and later states a different value for "
    "the same fact, the later user statement governs, regardless of any "
    "assistant estimate; only when the evidence index explicitly reports "
    "that statements share the latest timestamp and cannot be ordered "
    "should you reason from their content instead of recency.",
    "State the answer at the same granularity and in the same units the "
    "user stated it; do not convert a stated duration or amount into a "
    "more precise computed figure unless the question asks for the "
    "computation.",
    "When the question asks for one combined figure across multiple "
    "stated numbers, give the single combined total, not the parts.",
    "When the question measures time to an event named in the question "
    "(e.g. 'when I made the cake'), measure to that event's date, not to "
    "the question date.",
)


# ---------------------------------------------------------------------------
# v4 citation contract (2026-08-31, W6). OFF BY DEFAULT.
#
# When enabled (``--prompt-contract v4-citation`` or
# ``LME_PROMPT_CONTRACT=v4-citation``) the reader prompt gains the five-rule
# citation contract owned by scripts/v4_sufficiency.py
# (``READER_CITATION_CONTRACT_V1``). The text is IMPORTED, never retyped, so
# the prompt and the gate can never drift apart; the import is lazy so a
# contract-off run has no dependency on that module at all.
#
# Placement: after the instruction block, BEFORE ANSWER_SUFFIX. The suffix
# ("End with a single line: Answer: <short answer>") must stay last — every
# downstream consumer (judge, dual-read, sufficiency) locates the answer by
# the final ``Answer:`` line.
#
# Flag off => the prompt is byte-identical to the current v2 / v3.4-facts
# prompt (regression-tested in tests/test_v4_contract_prompt.py).
# ---------------------------------------------------------------------------
PROMPT_CONTRACT_ENV = "LME_PROMPT_CONTRACT"
PROMPT_CONTRACT_V4_CITATION = "v4-citation"
PROMPT_CONTRACT_VERSION_V4 = "v4-citation-20260831"
CITATION_CONTRACT_HEADER = (
    "CITATION CONTRACT — a post-reader gate checks the following "
    "mechanically; an answer whose citations fail these checks is refused:"
)


def _citation_contract_text() -> str:
    """The v1 contract, imported from its owner. Fails loudly, never
    substitutes a local copy: a silently divergent contract would make the
    gate reject correct answers for the wrong reason."""
    try:
        from v4_sufficiency import READER_CITATION_CONTRACT_V1
    except Exception as exc:  # noqa: BLE001 - surfaced, not swallowed
        raise SystemExit(
            f"prompt contract {PROMPT_CONTRACT_V4_CITATION!r} requested but "
            f"scripts/v4_sufficiency.py could not be imported: {exc}"
        ) from exc
    text = READER_CITATION_CONTRACT_V1.strip("\n")
    if not text:
        raise SystemExit(
            "READER_CITATION_CONTRACT_V1 is empty; refusing to append an "
            "empty contract block"
        )
    return text


def citation_contract_block() -> str:
    """The exact text spliced into the prompt when the contract is on."""
    return f"\n\n{CITATION_CONTRACT_HEADER}\n\n{_citation_contract_text()}"


def resolve_contract(cli_value: str | None = None) -> str:
    """CLI flag wins over env; empty/'off'/'none' means disabled.

    Unknown values fail closed rather than degrading to 'no contract' —
    a typo must not silently produce an uncontracted arm that later gets
    reported as a contract arm.
    """
    raw = cli_value if cli_value is not None else os.environ.get(
        PROMPT_CONTRACT_ENV, ""
    )
    raw = (raw or "").strip()
    if raw in ("", "off", "none"):
        return ""
    if raw != PROMPT_CONTRACT_V4_CITATION:
        raise SystemExit(
            f"unknown prompt contract {raw!r}; expected "
            f"{PROMPT_CONTRACT_V4_CITATION!r} or empty"
        )
    return raw


def apply_contract(prompt: str, contract: str) -> str:
    """Splice the contract block in front of ANSWER_SUFFIX.

    ``contract=''`` returns the prompt unchanged (byte-identity guarantee).
    """
    if not contract:
        return prompt
    if contract != PROMPT_CONTRACT_V4_CITATION:
        raise SystemExit(f"unknown prompt contract {contract!r}")
    if not prompt.endswith(ANSWER_SUFFIX):
        raise SystemExit(
            "prompt does not end with ANSWER_SUFFIX; refusing to splice the "
            "citation contract into an unknown shape"
        )
    head = prompt[: -len(ANSWER_SUFFIX)]
    return f"{head}{citation_contract_block()}{ANSWER_SUFFIX}"


def prompt_version_for(*, has_facts: bool, contract: str = "") -> str:
    """Per-row prompt_version string. Contract arms carry a suffix so a
    checkpoint can never be mistaken for an uncontracted one."""
    facts_version = os.environ.get("LME_FACTS_VERSION") or PROMPT_VERSION_V3_FACTS
    base = facts_version if has_facts else PROMPT_VERSION_V2
    return f"{base}+{PROMPT_CONTRACT_VERSION_V4}" if contract else base


def _extract_v2_instructions() -> str:
    """Slice the v2 instruction sentences out of build_reader_prompt_v2's
    own output — never retyped, so there is zero drift risk against the P1
    byte-identical requirement. Fails loudly if v2's prompt shape ever
    changes underneath this module."""
    probe_q, probe_blob = "PROBE_Q", "PROBE_BLOB"
    probe = build_reader_prompt_v2(probe_q, [probe_blob], question_date="")
    prefix = f"Question: {probe_q}\n\nRetrieved sessions:\n{probe_blob}\n\n"
    if not probe.startswith(prefix) or not probe.endswith(ANSWER_SUFFIX):
        raise SystemExit(
            "build_reader_prompt_v2 shape changed; v2-instruction "
            "extraction in run_lme_qa_flash_packets.py is stale"
        )
    return probe[len(prefix): -len(ANSWER_SUFFIX)]


_V2_INSTRUCTIONS = _extract_v2_instructions()


def extract_blobs(row: dict) -> list[str]:
    """Return materialized blobs. Never looks at haystack sessions."""
    blobs = row.get("session_blobs")
    if not isinstance(blobs, list):
        raise SystemExit(
            f"{row.get('question_id')}: session_blobs must be a list"
        )
    out: list[str] = []
    for i, blob in enumerate(blobs):
        if not isinstance(blob, str):
            raise SystemExit(
                f"{row.get('question_id')}: session_blobs[{i}] is not a str"
            )
        out.append(blob)
    return out


def load_materialized(path: Path) -> dict[str, dict]:
    rows = load_jsonl(path)
    if not rows:
        raise SystemExit(f"{path}: no materialized rows")
    out: dict[str, dict] = {}
    for i, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise SystemExit(f"{path}:{i}: row is not an object")
        qid = row.get("question_id")
        if not isinstance(qid, str) or not qid:
            raise SystemExit(f"{path}:{i}: missing question_id")
        if qid in out:
            raise SystemExit(f"{path}:{i}: duplicate question_id {qid!r}")
        extract_blobs(row)
        out[qid] = row
    return out


def build_todo(
    data: list[dict], materialized: dict[str, dict], done: set[str]
) -> list[tuple]:
    """Jobs for every materialized question still pending.

    Blobs come from the materialized row only.
    """
    todo: list[tuple] = []
    for item in data:
        qid = str(item.get("question_id") or "")
        if not qid or qid in done or qid not in materialized:
            continue
        blobs = extract_blobs(materialized[qid])
        todo.append((item, qid, blobs))
    return todo


def build_prompt(
    item: dict,
    blobs: list[str],
    facts_text: str = "",
    contract: str = "",
) -> str:
    """Prompt from dataset question fields + materialized blobs.

    No facts_text (P1): byte-identical to build_reader_prompt_v2's own
    output — the v2 reader prompt, untouched.

    With facts_text (P2, failure-closure campaign 2026-08-29): the
    deterministic evidence scaffold (produced by
    scripts/dense_chain_reasoning_operators.py from the same blobs; it
    never carries gold or judge data) is placed BEFORE the instruction
    block, and the instruction block keeps every v2 sentence verbatim plus
    four facts-only sentences (prompt_version v3-facts-20260830):

      {dated}Question: ...\\n\\nRetrieved sessions:\\n{body}\\n\\n
      {facts_text}\\n\\n
      {v2 instructions} {sentences a-d}{ANSWER_SUFFIX}

    With contract='v4-citation' (v4 pilot, 2026-08-31): the five-rule
    citation contract is spliced in immediately before ANSWER_SUFFIX, on
    either shape above. contract='' leaves both shapes byte-identical.
    """
    base = build_reader_prompt_v2(
        str(item.get("question") or ""),
        blobs,
        question_date=str(item.get("question_date") or ""),
    )
    if not facts_text:
        return apply_contract(base, contract)
    if not isinstance(facts_text, str) or not facts_text.strip():
        raise SystemExit("facts_text must be a non-empty str when given")

    suffix = _V2_INSTRUCTIONS + ANSWER_SUFFIX
    if not base.endswith(suffix):
        raise SystemExit(
            "base prompt does not end with the expected v2 instruction "
            "suffix; refusing to splice facts_text into an unknown shape"
        )
    prefix = base[: -len(suffix)]  # ends "...Retrieved sessions:\n{body}\n\n"
    instructions = (
        _V2_INSTRUCTIONS + " " + " ".join(_FACTS_SENTENCES) + ANSWER_SUFFIX
    )
    return apply_contract(f"{prefix}{facts_text}\n\n{instructions}", contract)


def build_checkpoint_row(
    item: dict,
    qid: str,
    blobs: list[str],
    response: str,
    err: str,
    *,
    has_facts: bool = False,
    contract: str = "",
) -> dict:
    """Checkpoint schema identical to run_lme_qa_flash.py, plus P3's
    per-row prompt_version: facts rows record 'v3.1-facts-20260830', every
    other row keeps the frozen 'v2-20260827'.

    Gold is joined from the dataset item for scoring output only.
    """
    return {
        "question_id": qid,
        "question_type": str(item.get("question_type") or ""),
        "question": str(item.get("question") or ""),
        "gold": str(item.get("answer") or ""),
        "response": response,
        "error": err,
        "prompt_version": prompt_version_for(
            has_facts=has_facts, contract=contract
        ),
        "reader_model": MODEL,
        "n_context_sessions": len(blobs),
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }


def _require_dataset_join(
    data: list[dict], materialized: dict[str, dict]
) -> None:
    data_ids = {
        str(item.get("question_id") or "")
        for item in data
        if item.get("question_id")
    }
    missing = sorted(set(materialized) - data_ids)
    if missing:
        preview = ", ".join(missing[:8])
        raise SystemExit(
            f"materialized packets missing dataset join "
            f"({len(missing)}): {preview}"
        )


def load_facts(path: Path | None) -> dict[str, str]:
    """Load the optional deterministic-facts sidecar (question_id ->
    facts_text). Rows must be objects with a non-empty question_id and a
    non-empty facts_text string. Duplicate ids fail loudly."""
    if path is None:
        return {}
    out: dict[str, str] = {}
    with path.open() as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{lineno}: not JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise SystemExit(f"{path}:{lineno}: row is not an object")
            qid = row.get("question_id")
            facts = row.get("facts_text")
            if not isinstance(qid, str) or not qid:
                raise SystemExit(f"{path}:{lineno}: missing question_id")
            if not isinstance(facts, str) or not facts.strip():
                raise SystemExit(
                    f"{path}:{lineno}: facts_text must be a non-empty str"
                )
            if qid in out:
                raise SystemExit(f"{path}:{lineno}: duplicate question_id {qid!r}")
            out[qid] = facts
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--materialized", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument(
        "--facts",
        default=None,
        help=(
            "optional JSONL sidecar of deterministic evidence scaffolds "
            "(question_id, facts_text) appended to the reader prompt; "
            "produced by scripts/dense_chain_reasoning_operators.py"
        ),
    )
    ap.add_argument(
        "--prompt-contract",
        default=None,
        help=(
            f"{PROMPT_CONTRACT_V4_CITATION!r} appends the five-rule citation "
            f"contract (scripts/v4_sufficiency.READER_CITATION_CONTRACT_V1) "
            f"before the Answer line. Default: ${PROMPT_CONTRACT_ENV} or off; "
            "off produces byte-identical prompts to the current chain."
        ),
    )
    args = ap.parse_args()
    contract = resolve_contract(args.prompt_contract)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(Path(args.data).read_text())
    if not isinstance(data, list):
        raise SystemExit(f"{args.data}: dataset is not a list")
    materialized = load_materialized(Path(args.materialized))
    _require_dataset_join(data, materialized)
    facts = load_facts(Path(args.facts) if args.facts else None)
    unknown_facts = sorted(set(facts) - set(materialized))
    if unknown_facts:
        raise SystemExit(
            f"--facts rows without a materialized packet "
            f"({len(unknown_facts)}): {', '.join(unknown_facts[:8])}"
        )

    ans_path = out_dir / "checkpoint_answerable.jsonl"
    abs_path = out_dir / "checkpoint_abs.jsonl"
    done: set[str] = set()
    for p in (ans_path, abs_path):
        if p.exists():
            done |= {
                r["question_id"] for r in load_jsonl(p) if not r.get("error")
            }
    for p in (ans_path, abs_path):
        if p.exists():
            rows = [r for r in load_jsonl(p) if not r.get("error")]
            p.write_text("".join(json.dumps(r) + "\n" for r in rows))

    todo = build_todo(data, materialized, done)

    lock = threading.Lock()
    n_done = 0
    t0 = time.time()

    def work(job: tuple) -> None:
        item, qid, blobs = job
        prompt = build_prompt(item, blobs, facts.get(qid, ""), contract)
        try:
            response, err = flash_generate(prompt), ""
        except FlashLaneError as exc:
            response, err = "", str(exc)
        row = build_checkpoint_row(
            item,
            qid,
            blobs,
            response,
            err,
            has_facts=qid in facts,
            contract=contract,
        )
        if qid in facts:
            row["facts_sha256"] = hashlib.sha256(
                facts[qid].encode("utf-8")
            ).hexdigest()
        target = abs_path if qid.endswith("_abs") else ans_path
        nonlocal n_done
        with lock:
            with target.open("a") as fh:
                fh.write(json.dumps(row) + "\n")
            n_done += 1
            if n_done % 25 == 0:
                print(
                    f"{n_done}/{len(todo)} ({time.time() - t0:.0f}s)",
                    flush=True,
                )

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(as_completed([ex.submit(work, j) for j in todo]))

    all_rows: list[dict] = []
    for p in (ans_path, abs_path):
        if p.exists():
            all_rows.extend(load_jsonl(p))
    err_ids = [r["question_id"] for r in all_rows if r.get("error")]
    empty_ids = [
        r["question_id"]
        for r in all_rows
        if not (r.get("response") or "").strip()
    ]
    contaminated = [
        r["question_id"]
        for r in all_rows
        if _CONTAMINATION.match((r.get("response") or ""))
    ]
    expected_ids = {
        str(i.get("question_id"))
        for i in data
        if str(i.get("question_id")) in materialized
    }
    missing_ids = sorted(expected_ids - {r["question_id"] for r in all_rows})
    # Prefix match, not equality: contract arms carry a
    # "+v4-citation-<date>" suffix on the same base version, and a facts row
    # is a facts row whether or not the citation contract was on.
    n_rows_v3 = sum(
        1
        for r in all_rows
        if str(r.get("prompt_version") or "").startswith(PROMPT_VERSION_V3_FACTS)
    )
    n_rows_v2 = sum(
        1
        for r in all_rows
        if str(r.get("prompt_version") or "").startswith(PROMPT_VERSION_V2)
    )
    version_histogram: dict[str, int] = {}
    for r in all_rows:
        key = str(r.get("prompt_version") or "")
        version_histogram[key] = version_histogram.get(key, 0) + 1

    meta = {
        "schema": "cds/lme-qa-flash-packets/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reader_model": MODEL,
        "reader_lane": READER_LANE,
        "transport": READER_TRANSPORT,
        "prompt_version": "v2-20260827 (identical to cloud v2 chain)",
        "materialized_source": args.materialized,
        "facts_source": args.facts,
        "n_rows_with_facts": sum(
            1 for r in all_rows if r.get("facts_sha256")
        ),
        # P3: prompt_version per row class, plus n_rows_v3 (facts rows).
        "prompt_versions": {
            PROMPT_VERSION_V2: n_rows_v2,
            PROMPT_VERSION_V3_FACTS: n_rows_v3,
        },
        "prompt_version_histogram": version_histogram,
        "prompt_contract": contract or None,
        "prompt_contract_version": (
            PROMPT_CONTRACT_VERSION_V4 if contract else None
        ),
        "prompt_contract_sha256": (
            hashlib.sha256(
                citation_contract_block().encode("utf-8")
            ).hexdigest()
            if contract
            else None
        ),
        "n_rows_v3": n_rows_v3,
        "n_rows_total": len(all_rows),
        "n_completed_this_invocation": n_done,
        "n_expected": len(expected_ids),
        "audit": {
            "error_rows": err_ids,
            "empty_response_rows": empty_ids,
            "wrapper_contaminated_rows": contaminated,
            "missing_rows": missing_ids,
            "clean": not (
                err_ids or empty_ids or contaminated or missing_ids
            ),
        },
    }
    (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta, indent=1))
    if not meta["audit"]["clean"]:
        print(
            "ARTIFACT INVALID — not fit for judging. "
            f"errors={len(err_ids)} empty={len(empty_ids)} "
            f"contaminated={len(contaminated)} missing={len(missing_ids)}",
            flush=True,
        )
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
