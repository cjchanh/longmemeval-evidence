#!/usr/bin/env bash
# v3.4 targeted replay: 123 answerable (60 baseline-correct controls + 44
# ledger targets + 29 GPT-4o-rejected rows) + 30 abs. Reader Cursor
# grok-4.6-high; judge GPT-4o-2024-08-06 (the deciding ruler; GLM retired
# per operator 2026-08-31). Usage: run_v34_replay.sh pass1|pass2
set -u
LABEL="$1"
V=eval/dense_chain_v32_20260830
P="$V/replay-v34_$LABEL"; mkdir -p "$P"
DATA="${LONGMEMEVAL_S_JSON:-$HOME/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json}"
date -u +"%Y-%m-%dT%H:%M:%SZ start v34 $LABEL" >> "$V/timeline.log"
LME_READER_LANE=cursor-grok LME_READER_MODEL=cursor-grok-4.6-high \
python3 scripts/run_lme_qa_flash_packets.py --data "$DATA" \
  --materialized "$V/replay_materialized_v34.jsonl" \
  --out-dir "$P/reader" --workers 6 --facts "$V/replay_facts_v34.jsonl" > "$P/reader.log" 2>&1
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
date -u +"%Y-%m-%dT%H:%M:%SZ v34 $LABEL judged" >> "$V/timeline.log"
python3 - "$P" "$V" <<'PY'
import json, sys
p, v = sys.argv[1], sys.argv[2]
rows = {json.loads(l)["question_id"]: json.loads(l)["llm_judge_correct"] for l in open(p + "/judge_gpt4o/rescored.jsonl")}
plan = json.load(open(v + "/replay_plan_v34.json"))
ab = [q for q in rows if q.endswith("_abs")]; ans = [q for q in rows if not q.endswith("_abs")]
print(f"V34 {p.split('_')[-1]}: answerable {sum(rows[q] for q in ans)}/{len(ans)} | abs {sum(rows[q] for q in ab)}/{len(ab)}")
ctl = [q for q in plan["controls_n60"] if q in rows]
print(f"controls {sum(rows[q] for q in ctl)}/{len(ctl)} regressions: {[q for q in ctl if not rows[q]]}")
rej = [q for q in plan["gpt4o_rejected"] if q in rows]
print(f"gpt4o-rejected recovered: {sum(rows[q] for q in rej)}/{len(rej)}")
PY
