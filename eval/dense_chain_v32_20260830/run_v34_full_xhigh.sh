#!/usr/bin/env bash
# v3.4 full pass on grok-4.6 XHIGH via Grok CLI (Grok Build sub).
# Gate cleared 2026-08-31: xhigh NC 0 flips / 58 correct controls; probe
# recovered 9/25 wrong rows. Same packets+facts as the official pair;
# judge GPT-4o api. Usage: run_v34_full_xhigh.sh pass1|pass2
set -u
LABEL="$1"
V=eval/dense_chain_v32_20260830
P="$V/full-v34-xhigh_$LABEL"; mkdir -p "$P"
DATA=/Users/cj/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json
cat "$V/materialized.jsonl" "$V/materialized_abs.jsonl" > "$P/materialized_all.jsonl"
cat "$V/facts_v34.jsonl" "$V/facts_abs_v34.jsonl" > "$P/facts_all.jsonl"
date -u +"%Y-%m-%dT%H:%M:%SZ start v34-xhigh $LABEL" >> "$V/timeline.log"
LME_READER_LANE=grok-cli LME_GROK_CLI_EFFORT=xhigh \
python3 scripts/run_lme_qa_flash_packets.py --data "$DATA" \
  --materialized "$P/materialized_all.jsonl" \
  --out-dir "$P/reader" --workers "${LME_WORKERS:-3}" --facts "$P/facts_all.jsonl" > "$P/reader.log" 2>&1
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
date -u +"%Y-%m-%dT%H:%M:%SZ v34-xhigh $LABEL judged" >> "$V/timeline.log"
python3 - "$P" <<'PY'
import json, sys
rows = {json.loads(l)["question_id"]: json.loads(l)["llm_judge_correct"] for l in open(sys.argv[1] + "/judge_gpt4o/rescored.jsonl")}
ab = [q for q in rows if q.endswith("_abs")]; an = [q for q in rows if not q.endswith("_abs")]
na = sum(rows[q] for q in an); nb = sum(rows[q] for q in ab)
print(f"XHIGH FULL {sys.argv[1].split('_')[-1]}: answerable {na}/{len(an)} | abs {nb}/{len(ab)} | TOTAL {na+nb}/{len(rows)} = {(na+nb)/max(len(rows),1)*100:.1f}%  (Chronos 478; agentmemory claim 481)")
PY
