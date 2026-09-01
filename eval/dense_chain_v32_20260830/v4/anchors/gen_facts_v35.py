#!/usr/bin/env python3
"""Regenerate the dense-chain facts scaffold at an explicit contract version.

Why this lives here and not in scripts/: the v4 wave-2 write scope is exactly
``scripts/dense_chain_reasoning_operators.py`` (the one shared-file edit),
``tests/test_v35_date_anchors.py``, and this directory. Adding a ``--contract``
flag to ``scripts/run_dense_chain_failure_closure.py`` would be a second
shared-file edit on a file another session may hold, so the driver is scoped
to the artifact directory it feeds instead. It reuses that runner's loaders and
hashing verbatim rather than reimplementing them, so a divergence between this
driver and the canonical facts stage is a divergence in shared code, not in a
private copy.

Row schema is IDENTICAL to the v3.4 facts rows, field for field, so
facts_v35.jsonl is a drop-in substitute for facts_v34.jsonl anywhere the
reader lane takes ``--facts``. Anchor provenance goes to a separate sidecar
(``--anchors-out``) precisely so it cannot perturb the served artifact.

The v3.4 byte-identity proof is this same driver run at ``--contract
v3.4-facts``: it must reproduce the frozen artifact's sha256 exactly. If the
gate below fails, the v3.5 delta is not attributable and the run is void.

Usage:
  python3 eval/dense_chain_v32_20260830/v4/anchors/gen_facts_v35.py \\
      --materialized eval/dense_chain_v32_20260830/materialized.jsonl \\
      --data /Users/cj/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json \\
      --out eval/dense_chain_v32_20260830/v4/anchors/facts_v35.jsonl \\
      --anchors-out eval/dense_chain_v32_20260830/v4/anchors/anchors_v35.jsonl \\
      --contract v3.5-facts \\
      --expect-v34-sha256 <frozen sha256 of the matching facts_v34 artifact>

GOLD IS NEVER AN INPUT: this driver reads question text, question date, and
session blobs. It never opens a gold field, and it never opens the judge.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "scripts"))

from dense_chain_reasoning_operators import (  # noqa: E402
    CONTRACT_V35,
    SUPPORTED_CONTRACTS,
    SessionInput,
    build_facts_contract,
    intext_date_anchors,
    match_lines,
    parse_date,
    question_terms,
)
from run_dense_chain_failure_closure import (  # noqa: E402
    ClosureError,
    _index,
    _load_jsonl,
    sha256_file,
    sha256_text,
)


def compute(
    *,
    materialized: dict[str, dict],
    dataset: dict[str, dict],
    contract: str,
) -> tuple[list[dict], list[dict]]:
    """(facts rows, anchor sidecar rows) for every materialized question whose
    operators activate. Same iteration order and same row schema as the
    canonical facts stage."""
    rows: list[dict] = []
    anchors: list[dict] = []
    for qid in sorted(materialized):
        m = materialized[qid]
        d = dataset.get(qid)
        if d is None:
            raise ClosureError(f"{qid}: no dataset row")
        ids_list = m.get("session_ids") or []
        blobs_list = m.get("session_blobs") or []
        if len(ids_list) != len(blobs_list):
            raise ClosureError(f"{qid}: session_ids/session_blobs misaligned")
        sessions = [
            SessionInput(sid, blob) for sid, blob in zip(ids_list, blobs_list)
        ]
        question = str(d.get("question") or "")
        question_date = str(d.get("question_date") or "")
        facts = build_facts_contract(
            question=question,
            question_date=question_date,
            sessions=sessions,
            contract=contract,
        )
        if not facts.activated:
            continue
        rows.append(
            {
                "question_id": qid,
                "facts_text": facts.text,
                "activated": list(facts.activated),
                "facts_sha256": sha256_text(facts.text),
                "n_matched_lines": facts.n_matched_lines,
                "n_dedup_lines": facts.n_dedup_lines,
            }
        )
        if contract != CONTRACT_V35:
            continue
        found = intext_date_anchors(match_lines(sessions, question_terms(question)))
        anchors.append(
            {
                "question_id": qid,
                "activated": list(facts.activated),
                # FOUND vs EMITTED are separate numbers on purpose. The block
                # is scoped to the date/duration operator, so a row can hold
                # in-text dates and correctly emit none. Recording only the
                # emitted count would make "no unexpected rows changed" a
                # tautology instead of a check.
                "n_intext_anchors_found": len(found),
                "n_intext_anchors": facts.n_intext_anchors,
                "n_session_days": _session_days(sessions),
                "anchors": [
                    {
                        "date": a.canonical,
                        "surface": a.surface,
                        "session_pos": a.session_pos,
                        "session_id": a.session_id,
                        "session_date": a.session_date,
                        "line_no": a.line_no,
                        "span": a.span,
                    }
                    for a in found
                ],
            }
        )
    return rows, anchors


def _session_days(sessions: list[SessionInput]) -> int:
    """Distinct parseable session-header DAYS in the packet. This is the
    quantity the wave-1 finding turned on: a packet with exactly one session
    day cannot express an interval from its headers, no matter how many
    sessions it holds."""
    return len({p[1] for p in (parse_date(s.blob) for s in sessions) if p})


def write_jsonl(path: Path, rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return sha256_file(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--materialized", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--anchors-out", default=None)
    ap.add_argument("--contract", default=CONTRACT_V35, choices=list(SUPPORTED_CONTRACTS))
    ap.add_argument(
        "--expect-sha256",
        default=None,
        help=(
            "fail closed unless the emitted artifact hashes to this value; "
            "used to prove the v3.4 reproduction is byte-identical"
        ),
    )
    args = ap.parse_args()

    materialized = _index(
        _load_jsonl(Path(args.materialized)), Path(args.materialized)
    )
    data = json.loads(Path(args.data).read_text())
    if not isinstance(data, list):
        raise ClosureError(f"{args.data}: dataset is not a list")
    dataset = _index(data, Path(args.data))

    rows, anchors = compute(
        materialized=materialized, dataset=dataset, contract=args.contract
    )
    out_path = Path(args.out)
    digest = write_jsonl(out_path, rows)
    anchors_digest = None
    if args.anchors_out and anchors:
        anchors_digest = write_jsonl(Path(args.anchors_out), anchors)

    summary = {
        "schema": "cds/dense-chain-closure-facts-summary/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "command": (
            "python3 eval/dense_chain_v32_20260830/v4/anchors/gen_facts_v35.py "
            f"--materialized {args.materialized} --data {args.data} "
            f"--out {args.out} --contract {args.contract}"
        ),
        "contract": args.contract,
        "materialized": args.materialized,
        "materialized_sha256": sha256_file(Path(args.materialized)),
        "n_materialized_rows": len(materialized),
        "n_rows_with_facts": len(rows),
        "n_activated_questions": len(rows),
        "sha256": digest,
        "anchors_out": args.anchors_out if anchors_digest else None,
        "anchors_sha256": anchors_digest,
        "n_rows_with_intext_anchors_found": sum(
            1 for a in anchors if a["n_intext_anchors_found"]
        ),
        "n_rows_with_intext_anchors_emitted": sum(
            1 for a in anchors if a["n_intext_anchors"]
        ),
        "activated_operator_counts": _counts(rows),
    }
    summary_path = out_path.parent / (out_path.stem + "_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=1))

    if args.expect_sha256 and digest != args.expect_sha256:
        print(
            f"SHA MISMATCH: expected {args.expect_sha256}, got {digest}",
            file=sys.stderr,
        )
        return 2
    return 0


def _counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        for op in r.get("activated") or []:
            counts[op] = counts.get(op, 0) + 1
    return dict(sorted(counts.items()))


if __name__ == "__main__":
    raise SystemExit(main())
