#!/usr/bin/env python3
"""Cross-judge agreement matrix: GLM-5.3 study judge vs official GPT-4o.

Judge-variance study, NOT rubric-comparable: the official GPT-4o verdicts
are the benchmark ruler and NEVER change; this tool only measures how often
a second judge (glm-5.3:cloud, same frozen rubric templates) renders the
same verdict on the same frozen responses. Output format mirrors the
judge_agreement_matrix.json era (grok pair, glm-5.2 judge, 98.2/97.8%).

Usage:
  python3 scripts/analyze_judge_agreement.py \
      --official eval/.../judge_gpt4o_v2/rescored.jsonl \
      --study   eval/.../judge_glm53/rescored.jsonl \
      --out     eval/.../judge_agreement_glm53.json \
      --study-label "opus_pass1 glm-5.3:cloud vs gpt-4o-2024-08-06"
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def load_verdicts(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            qid = row["question_id"]
            if qid in out:
                raise SystemExit(f"{path}: duplicate question_id {qid!r}")
            out[qid] = row
    return out


def analyze(official: dict[str, dict], study: dict[str, dict],
            label: str) -> dict:
    ids = sorted(set(official) & set(study))
    only_official = sorted(set(official) - set(study))
    only_study = sorted(set(study) - set(official))
    gpt_only: list[str] = []
    glm_only: list[str] = []
    agree_n = 0
    per_type: dict[str, dict] = defaultdict(
        lambda: {"n": 0, "agree": 0, "gpt_only": 0, "glm_only": 0})
    for qid in ids:
        o = bool(official[qid]["llm_judge_correct"])
        s = bool(study[qid]["llm_judge_correct"])
        row = official[qid]
        is_abs = bool(row.get("abstention")) or qid.endswith("_abs")
        bucket = per_type["abstention" if is_abs
                          else str(row.get("question_type") or "?")]
        bucket["n"] += 1
        if o == s:
            agree_n += 1
            bucket["agree"] += 1
        elif o and not s:
            gpt_only.append(qid)      # GPT-4o yes, study judge no
            bucket["gpt_only"] += 1
        else:
            glm_only.append(qid)      # study judge yes, GPT-4o no
            bucket["glm_only"] += 1
    n = len(ids)
    stricter = ("glm-5.3 stricter (more gpt_only than glm_only)"
                if len(gpt_only) > len(glm_only)
                else "gpt-4o stricter (more glm_only than gpt_only)"
                if len(glm_only) > len(gpt_only)
                else "equally strict (symmetric disagreement)")
    return {
        "label": label,
        "n": n,
        "agree": agree_n,
        "pct": round(100.0 * agree_n / max(1, n), 1),
        "gpt_only": len(gpt_only),
        "glm_only": len(glm_only),
        "gpt_only_ids": gpt_only,
        "glm_only_ids": glm_only,
        "stricter": stricter,
        "per_type_disagreement": {
            t: {"n": b["n"], "agree": b["agree"],
                "gpt_only": b["gpt_only"], "glm_only": b["glm_only"],
                "pct": round(100.0 * b["agree"] / max(1, b["n"]), 1)}
            for t, b in sorted(per_type.items())
        },
        "join_gaps": {"only_in_official": only_official,
                      "only_in_study": only_study},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--official", required=True,
                    help="official GPT-4o judge rescored.jsonl (the ruler)")
    ap.add_argument("--study", required=True,
                    help="study judge rescored.jsonl (e.g. glm-5.3:cloud)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--study-label", required=True)
    args = ap.parse_args()

    official = load_verdicts(Path(args.official))
    study = load_verdicts(Path(args.study))
    result = analyze(official, study, args.study_label)
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    result["official_source"] = args.official
    result["study_source"] = args.study
    result["study_class"] = ("judge-variance study, NOT rubric-comparable — "
                             "the official GPT-4o number never changes")
    Path(args.out).write_text(json.dumps(result, indent=1))
    print(json.dumps({k: result[k] for k in
                      ("label", "n", "agree", "pct", "gpt_only",
                       "glm_only", "stricter")}, indent=1))
    print("per_type:", json.dumps(result["per_type_disagreement"], indent=1))
    if result["join_gaps"]["only_in_official"] or \
            result["join_gaps"]["only_in_study"]:
        print("WARNING: join gaps present — see join_gaps", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
