#!/usr/bin/env python3
"""v4_pilot_set.py -- Deterministic frozen pilot row set + fixture manifest (W4).

Derives the v4 pilot TARGET / CONTROL / claim-excluded row sets from the
dense_chain_v32_20260830 grok-pair (full-v34_pass1 / full-v34_pass2) GPT-4o
judge rescores, and writes:

  eval/dense_chain_v32_20260830/v4/pilot/PILOT_SET.json
  eval/dense_chain_v32_20260830/v4/pilot/MANIFEST.md

Determinism: all row lists are built from sorted() inputs; the only random
component (the CONTROL sample) uses a single seeded random.Random(SEED) drawn
in a fixed type order over sorted candidate pools, so two runs on the same
input files produce byte-identical output files.

Usage:
    python3 scripts/v4_pilot_set.py [--root eval/dense_chain_v32_20260830]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

SEED = 20260831
N_CONTROL = 60

PASS1_DIR = "full-v34_pass1"
PASS2_DIR = "full-v34_pass2"
RESCORED_REL = "judge_gpt4o/rescored.jsonl"

ABS_NAMED_TARGET = [
    "a96c20ee_abs",
    "09ba9854_abs",
    "gpt4_fe651585_abs",
    "031748ae_abs",
]

GOLD_DEFECT_ROWS = ["gpt4_731e37d7", "370a8ff4"]  # GOLD_DEFECT_DOSSIER.md strict A+B


def load_rescored(path: Path) -> dict:
    rows = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            rows[r["question_id"]] = r
    return rows


def largest_remainder_allocation(counts: Counter, total: int) -> dict:
    """Proportional integer allocation of `total` across counts' keys,
    largest-remainder method. Deterministic given sorted key order."""
    grand = sum(counts.values())
    raw = {k: (v * total / grand) for k, v in counts.items()}
    floors = {k: int(v) for k, v in raw.items()}
    allocated = sum(floors.values())
    remainder = total - allocated
    # Break ties deterministically: sort by (fractional part desc, key asc)
    fracs = sorted(
        counts.keys(),
        key=lambda k: (-(raw[k] - floors[k]), k),
    )
    for k in fracs[:remainder]:
        floors[k] += 1
    return floors


def sha256_of_qids(qids: list) -> str:
    payload = "\n".join(sorted(qids)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build(root: Path) -> dict:
    p1_path = root / PASS1_DIR / RESCORED_REL
    p2_path = root / PASS2_DIR / RESCORED_REL
    p1 = load_rescored(p1_path)
    p2 = load_rescored(p2_path)

    if set(p1.keys()) != set(p2.keys()):
        sym = set(p1.keys()) ^ set(p2.keys())
        raise SystemExit(f"FATAL: pass1/pass2 question_id sets differ: {sorted(sym)[:10]} ...")

    all_qids = sorted(p1.keys())

    # --- component (a)(i): grok-pair stable-wrong -- wrong in BOTH passes,
    # over ALL rows (answerable + abstention). Matches PARENT_ANALYSIS.md's
    # "21 pair-stable-wrong rows"; the historical stable_wrong_v34.json at
    # the campaign root is the answerable-only subset (18 rows) of this set.
    stable_wrong = sorted(
        q for q in all_qids
        if not p1[q]["llm_judge_correct"] and not p2[q]["llm_judge_correct"]
    )

    # --- component (a)(ii): pair flip rows -- verdict differs pass1 vs pass2
    flips = sorted(
        q for q in all_qids
        if p1[q]["llm_judge_correct"] != p2[q]["llm_judge_correct"]
    )

    # --- component (a)(iii): the 4 named abs-miss rows from pass1, unioned
    # with any additional abstention rows wrong in pass2.
    abs_wrong_p2 = sorted(
        q for q in all_qids if p2[q]["abstention"] and not p2[q]["llm_judge_correct"]
    )
    abs_union = sorted(set(ABS_NAMED_TARGET) | set(abs_wrong_p2))
    missing_named = [q for q in ABS_NAMED_TARGET if q not in p1]
    if missing_named:
        raise SystemExit(f"FATAL: named abs-miss rows not found in pass1: {missing_named}")

    target_raw = sorted(set(stable_wrong) | set(flips) | set(abs_union))

    missing_gold = [q for q in GOLD_DEFECT_ROWS if q not in target_raw]
    if missing_gold:
        raise SystemExit(
            f"FATAL: expected strict gold-defect rows not present in target_raw: {missing_gold}"
        )

    target_final = sorted(set(target_raw) - set(GOLD_DEFECT_ROWS))
    claim_excluded = sorted(GOLD_DEFECT_ROWS)

    # --- CONTROL: correct in both passes, excluding TARGET + claim_excluded,
    # stratified by question_type proportional to type counts, seed=20260831.
    reserved = set(target_final) | set(claim_excluded)
    control_pool = sorted(
        q for q in all_qids
        if p1[q]["llm_judge_correct"] and p2[q]["llm_judge_correct"] and q not in reserved
    )
    pool_by_type: dict[str, list] = {}
    for q in control_pool:
        pool_by_type.setdefault(p1[q]["question_type"], []).append(q)
    for t in pool_by_type:
        pool_by_type[t] = sorted(pool_by_type[t])

    type_counts = Counter({t: len(v) for t, v in pool_by_type.items()})
    allocation = largest_remainder_allocation(type_counts, N_CONTROL)

    rng = random.Random(SEED)
    control_final: list[str] = []
    control_by_type: dict[str, list] = {}
    for t in sorted(allocation.keys()):
        k = allocation[t]
        candidates = pool_by_type[t]
        picked = sorted(rng.sample(candidates, k))
        control_by_type[t] = picked
        control_final.extend(picked)
    control_final = sorted(control_final)

    if len(control_final) != N_CONTROL:
        raise SystemExit(
            f"FATAL: control sample size {len(control_final)} != {N_CONTROL}"
        )
    if set(control_final) & reserved:
        raise SystemExit("FATAL: control/target overlap detected")

    # --- Row metadata
    def row_meta(qid: str, category: str) -> dict:
        r1, r2 = p1[qid], p2[qid]
        meta = {
            "question_id": qid,
            "question_type": r1["question_type"],
            "abstention": bool(r1["abstention"]),
            "category": category,
            "pass1_correct": bool(r1["llm_judge_correct"]),
            "pass2_correct": bool(r2["llm_judge_correct"]),
        }
        if category == "target":
            reasons = []
            if qid in stable_wrong:
                reasons.append("stable_wrong")
            if qid in flips:
                reasons.append("flip")
            if qid in ABS_NAMED_TARGET or qid in abs_wrong_p2:
                reasons.append("abs_miss")
            meta["target_reason"] = sorted(reasons)
        if category == "claim_excluded":
            meta["exclusion_reason"] = "strict_gold_defect (GOLD_DEFECT_DOSSIER.md A+B)"
        return meta

    rows = []
    for qid in target_final:
        rows.append(row_meta(qid, "target"))
    for qid in control_final:
        rows.append(row_meta(qid, "control"))
    for qid in claim_excluded:
        rows.append(row_meta(qid, "claim_excluded"))
    rows.sort(key=lambda r: (r["category"], r["question_id"]))

    all_listed_qids = sorted(target_final + control_final + claim_excluded)
    freeze_sha256 = sha256_of_qids(all_listed_qids)

    per_type_counts: dict[str, dict] = {}
    for r in rows:
        t = r["question_type"]
        per_type_counts.setdefault(t, {"target": 0, "control": 0, "claim_excluded": 0})
        per_type_counts[t][r["category"]] += 1
    per_type_counts = {k: per_type_counts[k] for k in sorted(per_type_counts)}

    pilot_set = {
        "schema": "cds/v4-pilot-set/v1",
        "seed": SEED,
        "n_control_target": N_CONTROL,
        "source": {
            "root": str(root),
            "pass1": f"{PASS1_DIR}/{RESCORED_REL}",
            "pass2": f"{PASS2_DIR}/{RESCORED_REL}",
            "reader": "cursor-grok-4.6-high",
            "judge": "gpt-4o-2024-08-06 (api)",
        },
        "counts": {
            "target": len(target_final),
            "control": len(control_final),
            "claim_excluded": len(claim_excluded),
            "total_listed": len(all_listed_qids),
            "per_type": per_type_counts,
        },
        "control_allocation": {k: allocation[k] for k in sorted(allocation)},
        "acceptance_rule": (
            "v4 components are promoted to a full pair only if pilot shows net "
            ">= +4 on TARGET rows with <= 1 CONTROL regression."
        ),
        "freeze_seal": {
            "algorithm": "sha256",
            "input": "sorted(target_final + control_final + claim_excluded) qid list, newline-joined",
            "hash": freeze_sha256,
        },
        "rows": rows,
    }
    return pilot_set


def render_manifest(pilot_set: dict) -> str:
    c = pilot_set["counts"]
    lines = []
    lines.append("# v4 Pilot Set — MANIFEST")
    lines.append("")
    lines.append(
        f"Frozen pilot row set for the v4 component pilot. Generated deterministically "
        f"by `scripts/v4_pilot_set.py` (seed={pilot_set['seed']}) from the grok-pair "
        f"GPT-4o judge rescores: `{pilot_set['source']['pass1']}` / `{pilot_set['source']['pass2']}`."
    )
    lines.append("")
    lines.append("## How each row qualified")
    lines.append("")
    lines.append("**TARGET** (n=%d) — union of:" % c["target"])
    lines.append(
        "- `stable_wrong`: wrong in BOTH full-v34_pass1 AND full-v34_pass2 "
        "(grok-pair stable-wrong, all types incl. abstention; 21 rows before exclusions — "
        "matches `v4/PARENT_ANALYSIS.md`'s \"21 pair-stable-wrong rows\"; the campaign-root "
        "`stable_wrong_v34.json` is the answerable-only subset, 18 rows)."
    )
    lines.append(
        "- `flip`: `llm_judge_correct` differs between pass1 and pass2 (8 rows; matches "
        "`v34_full_pair_attribution.json` flips list)."
    )
    lines.append(
        "- `abs_miss`: the 4 named pass1 abstention misses "
        "(`a96c20ee_abs`, `09ba9854_abs`, `gpt4_fe651585_abs`, `031748ae_abs`), unioned with "
        "any additional abstention rows wrong in pass2 (none beyond the named 4 in this data)."
    )
    lines.append(
        "- The two strict gold-defect rows (`gpt4_731e37d7`, `370a8ff4`) are members of "
        "`stable_wrong` but are pulled OUT of TARGET and re-categorized `claim_excluded` "
        "(see below) — they never decide a TARGET verdict."
    )
    lines.append("")
    lines.append("**CONTROL** (n=%d)" % c["control"])
    lines.append(
        "- Deterministic seeded (seed=20260831) sample of rows correct in BOTH passes, "
        "excluding every TARGET and `claim_excluded` row, stratified by `question_type` "
        "proportional to the eligible pool's per-type counts (largest-remainder allocation "
        "to hit exactly 60), sampled with a single `random.Random(20260831)` walking types "
        "in sorted order over sorted candidate lists per type — reproducible byte-for-byte."
    )
    lines.append(
        "- Pool includes both answerable and abstention rows correct in both passes "
        "(the `question_type` field already carries the underlying LongMemEval type for "
        "abstention rows, e.g. `gpt4_fe651585_abs` -> `temporal-reasoning`); this is a "
        "documented interpretation, not a stated constraint — flag for review if the "
        "intent was answerable-only controls."
    )
    lines.append("")
    lines.append("**claim_excluded** (n=%d)" % c["claim_excluded"])
    lines.append(
        "- `gpt4_731e37d7`, `370a8ff4` — the two strict (A+B) gold-defect rows per "
        "`GOLD_DEFECT_DOSSIER.md` §Strict defects. Listed for visibility (they are "
        "genuinely wrong-in-both-passes rows) but flagged `claim_excluded`: they must "
        "never decide a pilot verdict in either direction."
    )
    lines.append("")
    lines.append("## Count table by category and type")
    lines.append("")
    lines.append("| question_type | target | control | claim_excluded |")
    lines.append("|---|---|---|---|")
    for t, d in c["per_type"].items():
        lines.append(f"| {t} | {d['target']} | {d['control']} | {d['claim_excluded']} |")
    lines.append(
        f"| **total** | **{c['target']}** | **{c['control']}** | **{c['claim_excluded']}** |"
    )
    lines.append("")
    lines.append("## Freeze seal")
    lines.append("")
    lines.append(f"- Algorithm: `{pilot_set['freeze_seal']['algorithm']}`")
    lines.append(f"- Input: {pilot_set['freeze_seal']['input']}")
    lines.append(f"- Hash: `{pilot_set['freeze_seal']['hash']}`")
    lines.append(
        f"- Total listed rows: {c['total_listed']} (target {c['target']} + control {c['control']} "
        f"+ claim_excluded {c['claim_excluded']})"
    )
    lines.append("")
    lines.append("## Pre-registered pilot acceptance rule")
    lines.append("")
    lines.append(f"> {pilot_set['acceptance_rule']}")
    lines.append("")
    lines.append(
        "Determinism: re-running `scripts/v4_pilot_set.py` against unchanged input files "
        "reproduces this manifest and `PILOT_SET.json` byte-identically (fixed seed, all "
        "row lists sorted before hashing or sampling)."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parent.parent),
        help="dense_chain_v32_20260830 campaign root (default: parent of scripts/)",
    )
    args = ap.parse_args()
    root = Path(args.root).resolve()

    pilot_set = build(root)

    out_dir = root / "v4" / "pilot"
    out_dir.mkdir(parents=True, exist_ok=True)

    pilot_set_path = out_dir / "PILOT_SET.json"
    manifest_path = out_dir / "MANIFEST.md"

    pilot_set_path.write_text(json.dumps(pilot_set, indent=1, sort_keys=False) + "\n")
    manifest_path.write_text(render_manifest(pilot_set))

    c = pilot_set["counts"]
    print(f"target={c['target']} control={c['control']} claim_excluded={c['claim_excluded']}")
    print(f"freeze_hash={pilot_set['freeze_seal']['hash']}")
    print(f"wrote {pilot_set_path}")
    print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
