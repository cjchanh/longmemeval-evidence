#!/usr/bin/env python3
"""Build the LongMemEval-S evidence-release manifest (sha256 per released file).

Why: the paper's §8 release gate promises a public evidence repository. This
script freezes the released/held boundary as a checkable list so the public
copy can be verified file-by-file against the tagged commit. Deterministic:
same tree -> byte-identical manifest body. Read-only over the tree; writes
ONLY the manifest path given by --out and its sibling RELEASE_MANIFEST.root
(sha256 of that body). --check regenerates in memory and compares.

Released = every git-tracked file under the campaign eval dir (reader outputs,
judge verdicts, control receipts, agreement matrices, dossier, paper, reports)
plus the judge kit, its tests, the rubric source, the reader-lane scripts,
and the headline materialized packets/scaffolds under packets_materialized/.
Held = retrieval/compiler/rerank/scaffold-operator sources. Per-run
materialized*.jsonl / facts_all.jsonl files elsewhere under the eval dir are
also released as tracked artifacts; they are not the headline pair and are
not byte-identical to packets_materialized/*.gz.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

EVAL_DIR = "eval/dense_chain_v32_20260830"
DEFAULT_OUT = f"{EVAL_DIR}/RELEASE_MANIFEST.md"
ANCHORS = f"{EVAL_DIR}/ANCHORS.md"
README = "README.md"
README_ROOT_RE = re.compile(
    r"Manifest root \(sha256 of `RELEASE_MANIFEST\.md`\):\s*`([0-9a-f]{64})`"
)
RELEASED_EXTRA = [
    "scripts/rescore_gpt4o_judge.py",       # official-judge harness (frozen templates, sha-pinned)
    "scripts/oc_flash_lane.py",             # imported by the judge harness (chrome-strip helpers)
    "scripts/rescore_llm_judge.py",         # base judge script (SSP header reconstruction source; test_rescore_gpt4o_judge vendored check)
    "scripts/analyze_judge_agreement.py",   # cross-judge agreement matrix
    "scripts/reader_lane.py",               # reader lane dispatcher
    "scripts/claude_cli_lane.py",           # Opus reader lane (claude -p)
    "scripts/grok_cli_lane.py",             # grok-cli reader lane (xhigh)
    "scripts/run_lme_qa_flash_packets.py",  # reader runner over frozen packets
    "scripts/materialize_packets.py",       # public rematerializer (dataset + packets -> released text)
    "scripts/build_release_manifest.py",    # this file
    "scripts/export_release.py",            # exporter: copies manifest rows to a standalone tree, re-hashes
    "scripts/verify_release_manifest_signature.sh",
    "tests/test_rescore_gpt4o_judge.py",    # template sha pin + verdict extraction tests
    "tests/test_claude_cli_lane.py",
    "tests/test_packets_materialized.py",   # rematerializer + released gzip pins
    "tests/test_upstream_judge_pin.py",
    "tests/test_release_manifest_check.py",
    "benchmarks/longmemeval-judge-gate/GROUND_TRUTH_SURVEY.md",  # rubric source (verbatim transcription)
    "benchmarks/longmemeval-judge-gate/upstream/evaluate_qa.py",
    "benchmarks/longmemeval-judge-gate/upstream/UPSTREAM.md",
    ".github/workflows/release-manifest.yml",
]
PACKETS_MATERIALIZED_MANIFEST = f"{EVAL_DIR}/packets_materialized/MANIFEST.md"
HELD = [
    "scripts/dense_chain_reasoning_operators.py (deterministic scaffold operators, v3.4 contract)",
    "scripts/build_coverage_preserving_packets.py (coverage-first packet compiler)",
    "scripts/rerank_pool_cross_encoder.py, scripts/reranker_service*.py (cross-encoder rerank stage)",
    "scripts/compile_retrieval_eval.py (dense retrieval stage)",
]
ROW_RE = re.compile(r"^\| `([^`]+)` \| (\d+) \| `([0-9a-f]{64})` \|$")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked(prefix: str) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z", prefix],
            capture_output=True,
            check=False,
        )
    except OSError:
        proc = None
    if proc is not None and proc.returncode == 0:
        return sorted(x for x in proc.stdout.decode().split("\0") if x)
    root = Path(prefix)
    if not root.is_dir():
        return []
    return sorted(p.as_posix() for p in root.rglob("*") if p.is_file())


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def collect_files(out_path: str) -> list[str]:
    required = [*RELEASED_EXTRA, PACKETS_MATERIALIZED_MANIFEST, ANCHORS]
    missing = [s for s in required if not Path(s).exists()]
    if missing:
        raise SystemExit(f"FAIL: released file missing: {missing}")
    skip = {
        DEFAULT_OUT,
        str(Path(DEFAULT_OUT).with_suffix(".root")),
        Path(out_path).as_posix(),
        Path(out_path).with_suffix(".root").as_posix(),
    }
    eval_files = [f for f in tracked(EVAL_DIR) if f not in skip]
    for extra in (PACKETS_MATERIALIZED_MANIFEST, ANCHORS):
        if extra not in eval_files:
            eval_files.append(extra)
    eval_files.sort()
    return _dedupe(eval_files + RELEASED_EXTRA)


def build_body(files: list[str]) -> tuple[str, list[tuple[str, int, str]]]:
    rows = [(f, Path(f).stat().st_size, sha256(Path(f))) for f in files]
    total = sum(r[1] for r in rows)
    lines = [
        "# LongMemEval-S evidence release — manifest",
        "",
        "Generated by `python3 scripts/build_release_manifest.py`. "
        "The release commit is the one that contains this file. "
        f"Files: {len(rows)} · {total / 1e6:.1f} MB.",
        "",
        "A public copy of this release is verified when every row below matches "
        "`sha256sum` of the corresponding file. The headline pair's materialized "
        "packets and scaffolds are released under `packets_materialized/` (gzip). "
        "The compiler, rerank, retrieval and operator sources remain held (see Held). "
        "Other tracked materialized*.jsonl and facts_all.jsonl files under the eval "
        "dir are per-run artifacts (not the headline pair; not byte-identical to the "
        "released gzip). Every "
        "judge-side claim in the paper is re-derivable from the released reader "
        "checkpoints plus `scripts/rescore_gpt4o_judge.py` alone. Packet text is "
        "re-verified as a pure rendering of the public dataset via "
        "`scripts/materialize_packets.py --verify`.",
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
    return "\n".join(lines), rows


def parse_rows(text: str) -> dict[str, tuple[int, str]]:
    out: dict[str, tuple[int, str]] = {}
    for line in text.splitlines():
        match = ROW_RE.match(line)
        if match:
            out[match.group(1)] = (int(match.group(2)), match.group(3))
    return out


def root_digest(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def check(out_path: Path, body: str, rows: list[tuple[str, int, str]]) -> int:
    root_path = out_path.with_suffix(".root")
    digest = root_digest(body)
    mismatches: list[str] = []
    if not out_path.is_file():
        mismatches.append(out_path.as_posix())
    else:
        committed = out_path.read_text()
        committed_rows = parse_rows(committed)
        gen_rows = {f: (n, h) for f, n, h in rows}
        for f, meta in gen_rows.items():
            if f not in committed_rows or committed_rows[f] != meta:
                mismatches.append(f)
        for f in committed_rows:
            if f not in gen_rows:
                mismatches.append(f)
        if committed != body and not mismatches:
            mismatches.append(out_path.as_posix())
    if not root_path.is_file():
        mismatches.append(root_path.as_posix())
    elif root_path.read_text().strip() != digest:
        mismatches.append(root_path.as_posix())
    readme = Path(README)
    if not readme.is_file():
        mismatches.append(README)
    else:
        pin = README_ROOT_RE.search(readme.read_text())
        if pin is None or pin.group(1) != digest:
            mismatches.append(README)
    named = _dedupe(mismatches)
    if named:
        print("FAIL: mismatching rows:\n  " + "\n  ".join(named), file=sys.stderr)
        return 1
    print(f"OK: {len(rows)} files, manifest_root_sha256 {digest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument(
        "--check",
        action="store_true",
        help="regenerate in memory; exit 1 if the committed manifest or root differs",
    )
    a = ap.parse_args(argv)
    files = collect_files(a.out)
    body, rows = build_body(files)
    total = sum(r[1] for r in rows)
    digest = root_digest(body)
    out_path = Path(a.out)
    if a.check:
        return check(out_path, body, rows)
    out_path.write_text(body)
    out_path.with_suffix(".root").write_text(digest + "\n")
    print(f"wrote {a.out}: {len(rows)} files, {total / 1e6:.1f} MB")
    print(f"manifest_root_sha256 {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
