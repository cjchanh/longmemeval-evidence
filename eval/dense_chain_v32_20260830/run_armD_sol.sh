#!/usr/bin/env bash
# ARM D — GPT-5.6 Sol reader (opencode OpenAI OAuth) on the v3.2 replay set
# (60 baseline-correct controls + 44 targets + 30 abs), f3value facts,
# GLM judge on opencode-go. Operator-directed: pro-level reader datapoint
# before the quota reset. NOT closure evidence under the lock.
set -u
V=eval/dense_chain_v32_20260830
P="$V/armD_sol"; mkdir -p "$P"
DATA="${LONGMEMEVAL_S_JSON:-$HOME/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json}"
date -u +"%Y-%m-%dT%H:%M:%SZ start armD" >> "$V/timeline.log"
LME_READER_LANE=sol LME_READER_MODEL=openai/gpt-5.6-sol \
python3 scripts/run_lme_qa_flash_packets.py --data "$DATA" --materialized "$V/replay_materialized.jsonl" \
  --out-dir "$P/reader" --workers 6 --facts "$V/replay_facts_f3value.jsonl" > "$P/reader.log" 2>&1
echo "READER_EXIT=$?"
[ -f "$P/reader/checkpoint_abs.jsonl" ] || : > "$P/reader/checkpoint_abs.jsonl"
python3 - "$P" <<'PY'
import json, sys
m = json.load(open(sys.argv[1] + "/reader/run_meta.json"))
print("reader_model", m["reader_model"], "| lane", m.get("reader_lane"), "| rows", m["n_rows_total"], "| audit clean", m["audit"]["clean"])
PY
export LME_FLASH_MODEL=opencode-go/glm-5.3-flash
python3 scripts/rescore_llm_judge_flash.py --answerable "$P/reader/checkpoint_answerable.jsonl" \
  --abs "$P/reader/checkpoint_abs.jsonl" --out-dir "$P/judge" --control-n 12 > "$P/judge.log" 2>&1
echo "JUDGE_EXIT=$?"
python3 - "$P" "$V" <<'PY'
import json, sys
p, v = sys.argv[1], sys.argv[2]
rows = {json.loads(l)["question_id"]: json.loads(l) for l in open(p + "/judge/rescored.jsonl")}
plan = json.load(open(v + "/replay_plan_v32.json"))
ab = [q for q in rows if q.endswith("_abs")]; ans = [q for q in rows if not q.endswith("_abs")]
print(f"ARM D (Sol): answerable {sum(rows[q]['llm_judge_correct'] for q in ans)}/{len(ans)} | abs {sum(rows[q]['llm_judge_correct'] for q in ab)}/{len(ab)}")
ctl = [q for q in plan["controls_n60"] if q in rows]
print(f"controls {sum(rows[q]['llm_judge_correct'] for q in ctl)}/{len(ctl)} | 44 targets {sum(rows[q]['llm_judge_correct'] for q in plan['targets_44'] if q in rows)}/44")
PY
date -u +"%Y-%m-%dT%H:%M:%SZ armD done" >> "$V/timeline.log"
