#!/usr/bin/env bash
# Reader-robustness datapoint: Kimi K3 (Moonshot long-context specialist,
# Ollama MAX rail via opencode) reads the SAME v3.4 packets + facts; judge
# GPT-4o-2024-08-06. ONE pass = curve datapoint only, NEVER a headline
# (two-pass rule before any promotion).
#
# Why Kimi: the one reader family a memory benchmark most should measure that
# this curve hadn't — either outcome is a finding (joins the top tier =>
# ceiling confirmed harder; lands mid => "long context != long memory"
# measured on this substrate).
#
# Law honored: judge runs ONLY after reader audit is clean, in a CLEAN
# out-dir (no prior verdicts) — judge resume-by-qid can never see stale
# verdicts from changed reader answers.
# Usage: run_kimi_full.sh pass1
set -u
LABEL="${1:-pass1}"
V=eval/dense_chain_v32_20260830
P="$V/full-v34-kimi_$LABEL"; mkdir -p "$P"
DATA=/Users/cj/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json
cat "$V/materialized.jsonl" "$V/materialized_abs.jsonl" > "$P/materialized_all.jsonl"
cat "$V/facts_v34.jsonl" "$V/facts_abs_v34.jsonl" > "$P/facts_all.jsonl"
date -u +"%Y-%m-%dT%H:%M:%SZ start kimi $LABEL" >> "$V/timeline.log"
LME_READER_LANE=flash LME_FLASH_MODEL=ollama-cloud/kimi-k3 LME_FLASH_MODEL_UNPINNED=1 \
python3 scripts/run_lme_qa_flash_packets.py --data "$DATA" \
  --materialized "$P/materialized_all.jsonl" \
  --out-dir "$P/reader" --workers "${LME_WORKERS:-6}" --facts "$P/facts_all.jsonl" > "$P/reader.log" 2>&1
READER_EXIT=$?
echo "READER_EXIT=$READER_EXIT"
[ -f "$P/reader/checkpoint_abs.jsonl" ] || : > "$P/reader/checkpoint_abs.jsonl"
python3 - "$P" <<'PY'
import json, sys
m = json.load(open(sys.argv[1] + "/reader/run_meta.json"))
print("reader_model", m["reader_model"], "| rows", m["n_rows_total"],
      "| versions", m.get("prompt_versions"), "| audit clean", m["audit"]["clean"])
sys.exit(0 if m["audit"]["clean"] else 3)
PY
AUDIT_EXIT=$?
if [ "$READER_EXIT" -ne 0 ] || [ "$AUDIT_EXIT" -ne 0 ]; then
  echo "READER NOT CLEAN (reader_exit=$READER_EXIT audit_exit=$AUDIT_EXIT) — refusing to judge; resume reader first, judge only after clean."
  date -u +"%Y-%m-%dT%H:%M:%SZ kimi $LABEL reader NOT clean — judge withheld" >> "$V/timeline.log"
  exit 3
fi
python3 scripts/rescore_gpt4o_judge.py \
  --answerable "$P/reader/checkpoint_answerable.jsonl" \
  --abs "$P/reader/checkpoint_abs.jsonl" \
  --out-dir "$P/judge_gpt4o" --transport api --model gpt-4o-2024-08-06 \
  --api-key-file ~/.config/openai/api_key --control-n 12 \
  --spec eval/dense_chain_v32_20260830/gpt4o_judge_dispatch_spec.md > "$P/judge.log" 2>&1
echo "JUDGE_EXIT=$?"
date -u +"%Y-%m-%dT%H:%M:%SZ kimi $LABEL judged" >> "$V/timeline.log"
python3 - "$P" <<'PY'
import json, sys
rows = {json.loads(l)["question_id"]: json.loads(l)["llm_judge_correct"]
        for l in open(sys.argv[1] + "/judge_gpt4o/rescored.jsonl")}
ab = [q for q in rows if q.endswith("_abs")]
an = [q for q in rows if not q.endswith("_abs")]
na = sum(rows[q] for q in an); nb = sum(rows[q] for q in ab)
print(f"KIMI FULL: answerable {na}/{len(an)} | abs {nb}/{len(ab)} | "
      f"TOTAL {na+nb}/{len(rows)} = {(na+nb)/max(len(rows),1)*100:.1f}%  "
      "(single pass — curve datapoint, NOT a headline; opus pair 479/475, "
      "grok 476/474, glm-5.3 471)")
PY
