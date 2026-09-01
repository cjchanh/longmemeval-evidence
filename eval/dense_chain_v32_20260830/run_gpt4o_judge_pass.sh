#!/usr/bin/env bash
# GPT-4o (official, gpt-4o-2024-08-06) judge over one full pass's frozen
# responses. Runs alongside the GLM judge; both columns reported.
# Usage: run_gpt4o_judge_pass.sh <pass_dir>   e.g. full_pass1
set -u
V=eval/dense_chain_v32_20260830
P="$V/$1"
python3 scripts/rescore_gpt4o_judge.py \
  --answerable "$P/reader/checkpoint_answerable.jsonl" \
  --abs "$P/reader/checkpoint_abs.jsonl" \
  --out-dir "$P/judge_gpt4o" --transport api --model gpt-4o-2024-08-06 \
  --api-key-file ~/.config/openai/api_key \
  --spec eval/dense_chain_v32_20260830/gpt4o_judge_dispatch_spec.md > "$P/judge_gpt4o.log" 2>&1
echo "GPT4O_JUDGE_EXIT=$?"
python3 - "$P" <<'PY'
import json, sys
p = sys.argv[1]
rows = {json.loads(l)["question_id"]: json.loads(l) for l in open(p + "/judge_gpt4o/rescored.jsonl")}
ab = [q for q in rows if q.endswith("_abs")]; ans = [q for q in rows if not q.endswith("_abs")]
n = sum(rows[q]["llm_judge_correct"] for q in ans); a = sum(rows[q]["llm_judge_correct"] for q in ab)
print(f"GPT-4o OFFICIAL: answerable {n}/{len(ans)} | abs {a}/{len(ab)} | 500-basis {n+a}/{len(ans)+len(ab)} = {(n+a)/(len(ans)+len(ab))*100:.2f}%")
PY
