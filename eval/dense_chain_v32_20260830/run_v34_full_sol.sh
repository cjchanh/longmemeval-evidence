#!/usr/bin/env bash
# v3.4 full pass on the Sol reader lane (opencode OAuth, quota-metered).
# Same packets + v3.4 facts as the official grok pair; judge GPT-4o api.
# Purpose: independent-reader SOTA attempt (Sol read 468 on v3.3-era facts).
# Usage: run_v34_full_sol.sh pass1|pass2
set -u
LABEL="$1"
V=eval/dense_chain_v32_20260830
P="$V/full-v34-sol_$LABEL"; mkdir -p "$P"
DATA=/Users/cj/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json
cat "$V/materialized.jsonl" "$V/materialized_abs.jsonl" > "$P/materialized_all.jsonl"
cat "$V/facts_v34.jsonl" "$V/facts_abs_v34.jsonl" > "$P/facts_all.jsonl"
date -u +"%Y-%m-%dT%H:%M:%SZ start v34-sol $LABEL" >> "$V/timeline.log"
LME_READER_LANE=sol \
python3 scripts/run_lme_qa_flash_packets.py --data "$DATA" \
  --materialized "$P/materialized_all.jsonl" \
  --out-dir "$P/reader" --workers "${LME_WORKERS:-4}" --facts "$P/facts_all.jsonl" > "$P/reader.log" 2>&1
echo "READER_EXIT=$?"
[ -f "$P/reader/checkpoint_abs.jsonl" ] || : > "$P/reader/checkpoint_abs.jsonl"
python3 - "$P" <<'PY'
import json, sys
m = json.load(open(sys.argv[1] + "/reader/run_meta.json"))
print("reader_model", m["reader_model"], "| rows", m["n_rows_total"], "| versions", m.get("prompt_versions"), "| audit clean", m["audit"]["clean"])
PY
python3 scripts/rescore_gpt4o_judge.py \
  --answerable "$P/reader/checkpoint_answerable.jsonl" \
  --abs "$P/reader/checkpoint_abs.jsonl" \
  --out-dir "$P/judge_gpt4o" --transport api --model gpt-4o-2024-08-06 \
  --api-key-file ~/.config/openai/api_key --control-n 12 \
  --spec eval/dense_chain_v32_20260830/gpt4o_judge_dispatch_spec.md > "$P/judge.log" 2>&1
echo "JUDGE_EXIT=$?"
date -u +"%Y-%m-%dT%H:%M:%SZ v34-sol $LABEL judged" >> "$V/timeline.log"
python3 - "$P" <<'PY'
import json, sys
rows = {json.loads(l)["question_id"]: json.loads(l)["llm_judge_correct"] for l in open(sys.argv[1] + "/judge_gpt4o/rescored.jsonl")}
ab = [q for q in rows if q.endswith("_abs")]; an = [q for q in rows if not q.endswith("_abs")]
na = sum(rows[q] for q in an); nb = sum(rows[q] for q in ab)
print(f"SOL V34 FULL {sys.argv[1].split('_')[-1]}: answerable {na}/{len(an)} | abs {nb}/{len(ab)} | TOTAL {na+nb}/{len(rows)} = {(na+nb)/max(len(rows),1)*100:.1f}%  (bar 475; grok pair 476/474)")
PY
