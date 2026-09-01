#!/usr/bin/env python3
"""Build the LongMemEval-S evidence-release manifest (sha256 per released file).

Why: the paper's §8 release gate promises a public evidence repository. This
script freezes the released/held boundary as a checkable list so the public
copy can be verified file-by-file against the tagged commit. Deterministic:
same tree -> byte-identical manifest body. Read-only over the tree; writes
ONLY the manifest path given by --out.

Released = every git-tracked file under the campaign eval dir (reader outputs,
judge verdicts, control receipts, agreement matrices, dossier, paper, reports)
plus the judge kit, its tests, the rubric source, and the reader-lane scripts.
Held = retrieval/compiler/scaffold internals and the materialized packets
(benchmark haystack text; regenerable; never committed).
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

EVAL_DIR = "eval/dense_chain_v32_20260830"
RELEASED_EXTRA = [
    "scripts/rescore_gpt4o_judge.py",       # official-judge harness (frozen templates, sha-pinned)
    "scripts/oc_flash_lane.py",             # imported by the judge harness (chrome-strip helpers)
    "scripts/rescore_llm_judge.py",         # base judge script (SSP header reconstruction source; test_rescore_gpt4o_judge vendored check)
    "scripts/analyze_judge_agreement.py",   # cross-judge agreement matrix
    "scripts/reader_lane.py",               # reader lane dispatcher
    "scripts/claude_cli_lane.py",           # Opus reader lane (claude -p)
    "scripts/grok_cli_lane.py",             # grok-cli reader lane (xhigh)
    "scripts/run_lme_qa_flash_packets.py",  # reader runner over frozen packets
    "scripts/build_release_manifest.py",    # this file
    "scripts/export_release.py",            # exporter: copies manifest rows to a standalone tree, re-hashes
    "tests/test_rescore_gpt4o_judge.py",    # template sha pin + verdict extraction tests
    "tests/test_claude_cli_lane.py",
    "benchmarks/longmemeval-judge-gate/GROUND_TRUTH_SURVEY.md",  # rubric source (verbatim transcription)
]
HELD = [
    "scripts/dense_chain_reasoning_operators.py (deterministic scaffold operators, v3.4 contract)",
    "scripts/build_coverage_preserving_packets.py (coverage-first packet compiler)",
    "scripts/rerank_pool_cross_encoder.py, scripts/reranker_service*.py (cross-encoder rerank stage)",
    "scripts/compile_retrieval_eval.py (dense retrieval stage)",
    f"{EVAL_DIR}/**/materialized*.jsonl, facts_all.jsonl (packets + scaffolds: benchmark haystack text; regenerable; never committed)",
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked(prefix: str) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z", prefix], capture_output=True, check=True).stdout
    return sorted(x for x in out.decode().split("\0") if x)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"{EVAL_DIR}/RELEASE_MANIFEST.md")
    a = ap.parse_args(argv)
    head = subprocess.run(["git", "rev-parse", "--short=9", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    default_out = f"{EVAL_DIR}/RELEASE_MANIFEST.md"
    missing = [s for s in RELEASED_EXTRA if not Path(s).exists()]
    if missing:
        print(f"FAIL: released file missing: {missing}", file=sys.stderr)
        return 1
    files = [f for f in tracked(EVAL_DIR) if f != default_out] + RELEASED_EXTRA
    rows = [(f, Path(f).stat().st_size, sha256(Path(f))) for f in files]
    total = sum(r[1] for r in rows)
    lines = [
        "# LongMemEval-S evidence release — manifest",
        "",
        f"Generated at HEAD `{head}`; the release commit is the one that contains this file. "
        f"Regenerate with `python3 scripts/build_release_manifest.py`. "
        f"Files: {len(rows)} · {total / 1e6:.1f} MB.",
        "",
        "A public copy of this release is verified when every row below matches "
        "`sha256sum` of the corresponding file. The materialized packets are not part "
        "of the release (see Held); every judge-side claim in the paper is re-derivable "
        "from the released reader checkpoints plus `scripts/rescore_gpt4o_judge.py` alone.",
        "",
        "## Held (not released as source)",
        "",
        *[f"- {h}" for h in HELD],
        "",
        "## Released",
        "",
        "| file | bytes | sha256 |",
        "|---|---:|---|",
        *[f"| `{f}` | {n} | `{h}` |" for f, n, h in rows],
        "",
    ]
    Path(a.out).write_text("\n".join(lines))
    print(f"wrote {a.out}: {len(rows)} files, {total / 1e6:.1f} MB, tree {head}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
