#!/usr/bin/env bash
# FULL 470+30 on GPT-5.6 Sol (opencode OpenAI OAuth), f3value facts, 16 workers.
# Operator-authorized 2026-08-30 ("launch the full one... could pass on fast")
# within the expiring ChatGPT-plan quota window. GLM judge afterwards (unaffected
# by the reset). NOT closure evidence under the lock — pro-reader arm.
set -u
V=eval/dense_chain_v32_20260830
P="$V/full_sol"; mkdir -p "$P"
DATA="${LONGMEMEVAL_S_JSON:-$HOME/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json}"
cat "$V/materialized.jsonl" "$V/materialized_abs.jsonl" > "$P/materialized_all.jsonl"
cat "$V/facts_f3value.jsonl" "$V/facts_abs_f3value.jsonl" > "$P/facts_all.jsonl"
date -u +"%Y-%m-%dT%H:%M:%SZ start full_sol" >> "$V/timeline.log"
LME_READER_LANE=sol LME_READER_MODEL=openai/gpt-5.6-sol \
python3 scripts/run_lme_qa_flash_packets.py --data "$DATA" --materialized "$P/materialized_all.jsonl" \
  --out-dir "$P/reader" --workers 16 --facts "$P/facts_all.jsonl" > "$P/reader.log" 2>&1
echo "READER_EXIT=$?"
[ -f "$P/reader/checkpoint_abs.jsonl" ] || : > "$P/reader/checkpoint_abs.jsonl"
python3 - "$P" <<'PY'
import json, sys
m = json.load(open(sys.argv[1] + "/reader/run_meta.json"))
print("reader_model", m["reader_model"], "| lane", m.get("reader_lane"), "| rows", m["n_rows_total"], "| audit", m["audit"])
PY
export LME_FLASH_MODEL=opencode-go/glm-5.3-flash
python3 scripts/rescore_llm_judge_flash.py --answerable "$P/reader/checkpoint_answerable.jsonl" \
  --abs "$P/reader/checkpoint_abs.jsonl" --out-dir "$P/judge" --control-n 12 > "$P/judge.log" 2>&1
echo "JUDGE_EXIT=$?"
date -u +"%Y-%m-%dT%H:%M:%SZ full_sol judged" >> "$V/timeline.log"
python3 - "$P" "$V" <<'PY'
import json, sys
p, v = sys.argv[1], sys.argv[2]
rows = {json.loads(l)["question_id"]: json.loads(l) for l in open(p + "/judge/rescored.jsonl")}
base = {json.loads(l)["question_id"]: json.loads(l)["llm_judge_correct"] for l in open("eval/judge_glm_full500_20260828/dense/rescored.jsonl")}
ab = [q for q in rows if q.endswith("_abs")]; ans = [q for q in rows if not q.endswith("_abs")]
n = sum(rows[q]["llm_judge_correct"] for q in ans); a = sum(rows[q]["llm_judge_correct"] for q in ab)
print(f"FULL SOL: answerable {n}/{len(ans)} | abs {a}/{len(ab)} | 500-basis {n+a}/{len(ans)+len(ab)}")
plan = json.load(open(v + "/replay_plan_v32.json"))
ctl = [q for q in plan["controls_n60"] if q in rows]
print(f"controls {sum(rows[q]['llm_judge_correct'] for q in ctl)}/{len(ctl)} | lost vs baseline: {[q for q in ans if base.get(q) and not rows[q]['llm_judge_correct']][:20]}")
PY
