#!/usr/bin/env bash
# v3.2 chain (brick 2b: full-line value display, user-line completeness gate,
# same-timestamp tie, irregular-verb matcher; prompt v3.2-facts). The matcher
# widens R3 extraction, so packets are RECOMPILED from the v3 CE-scored pools.
# Stages: prep (compile/materialize/facts/verify for 470 + 30 abs; control
#         sample; replay plan) | replay pass1|pass2 (60 ctrl + 44 + 30 abs)
#         | full pass1|pass2 (470 + 30 abs)
# Reader: Cursor grok-4.6-high. Judge: GLM-5.3-Flash (opencode-go).
set -u
STAGE="$1"; SUB="${2:-}"
V3=eval/dense_chain_reranker_v3_20260830
V=eval/dense_chain_v32_20260830
DATA=/Users/cj/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json
TOP10=eval/lme_product_dense_qa_20260827/retrieval_ranked_dense_c.jsonl
mkdir -p "$V"
case "$STAGE" in
prep)
  python3 scripts/build_coverage_preserving_packets.py --pools "$V3/pools_ce.jsonl" --baseline-top10 "$TOP10" --data "$DATA" \
    --out "$V/packets.jsonl" --budget-tokens 40000 --max-sessions 16 \
    --allocation union16-rerank-term-extractive --extension-order ce --extension-floor none > "$V/compile.log" 2>&1
  echo "COMPILE_EXIT=$?"
  python3 scripts/build_coverage_preserving_packets.py --pools "$V3/abs/pools_ce.jsonl" --baseline-top10 "$V3/abs/baseline_top10_abs_dedup.jsonl" --data "$DATA" \
    --out "$V/packets_abs.jsonl" --budget-tokens 40000 --max-sessions 16 \
    --allocation union16-rerank-term-extractive --extension-order ce --extension-floor none > "$V/compile_abs.log" 2>&1
  echo "COMPILE_ABS_EXIT=$?"
  python3 scripts/run_dense_chain_coverage_ab.py reader-materialize --packets "$V/packets.jsonl" --data "$DATA" \
    --out "$V/materialized.jsonl" --summary "$V/materialize_summary.json" > "$V/materialize.log" 2>&1
  echo "MATERIALIZE_EXIT=$?"
  python3 scripts/run_dense_chain_coverage_ab.py reader-materialize --packets "$V/packets_abs.jsonl" --data "$DATA" \
    --out "$V/materialized_abs.jsonl" --summary "$V/materialize_abs_summary.json" > "$V/materialize_abs.log" 2>&1
  echo "MATERIALIZE_ABS_EXIT=$?"
  python3 scripts/run_dense_chain_failure_closure.py facts --materialized "$V/materialized.jsonl" --out "$V/facts.jsonl" > "$V/facts.log" 2>&1
  echo "FACTS_EXIT=$?"
  python3 scripts/run_dense_chain_failure_closure.py facts --materialized "$V/materialized_abs.jsonl" --out "$V/facts_abs.jsonl" > "$V/facts_abs.log" 2>&1
  echo "FACTS_ABS_EXIT=$?"
  python3 scripts/run_dense_chain_failure_closure.py verify --pools "$V3/pools_ce.jsonl" --baseline-top10 "$TOP10" \
    --gold-shuffled-data /tmp/lme_gold_shuffled_closure.json \
    --allocation union16-rerank-term-extractive --extension-order ce --extension-floor none \
    --materialized "$V/materialized.jsonl" --materialized-attempt2 "$V3/materialized_prefix10.jsonl" \
    --facts "$V/facts.jsonl" --out "$V/verification_report.json" > "$V/verify.log" 2>&1
  echo "VERIFY_EXIT=$?"
  python3 - "$V" <<'PY'
import json, sys
d = json.load(open(sys.argv[1] + "/verification_report.json"))
print("VERIFY overall", d["overall"], "| det", d["packets"]["determinism"]["identical"], "| goldNC", d["packets"]["gold_permutation_nc"]["identical_to_run1"],
      "| prefix-superset regress", d["membership"]["regressions"], "grown", d["membership"]["n_grown"], "| budget viol", d["budget"]["n_violations"],
      "| facts", d["facts"]["n_rows"], "| qid sabotage", d["question_id_sabotage"]["identical_modulo_ids"])
PY
  python3 scripts/sample_baseline_correct_controls.py --judge eval/judge_glm_full500_20260828/dense/rescored.jsonl \
    --facts "$V/facts.jsonl" --exclude-plan "$V3/replay/replay_plan.json" -n 60 --out "$V/controls_n60.jsonl" | tail -3
  python3 - "$V" "$V3" <<'PY'
import json, sys
v, v3 = sys.argv[1], sys.argv[2]
ctl = [json.loads(l)["question_id"] for l in open(v + "/controls_n60.jsonl")]
tgt = json.load(open(v3 + "/replay/replay_plan.json"))["targets"]
ids = set(ctl) | set(tgt)
mat = {json.loads(l)["question_id"]: l for l in open(v + "/materialized.jsonl")}
fac = {json.loads(l)["question_id"]: l for l in open(v + "/facts.jsonl")}
with open(v + "/replay_materialized.jsonl", "w") as fh:
    for q in sorted(ids): fh.write(mat[q])
    for l in open(v + "/materialized_abs.jsonl"): fh.write(l)
with open(v + "/replay_facts.jsonl", "w") as fh:
    for q in sorted(ids):
        if q in fac: fh.write(fac[q])
    for l in open(v + "/facts_abs.jsonl"): fh.write(l)
json.dump({"controls_n60": ctl, "targets_44": tgt, "n_answerable": len(ids), "n_abs": 30}, open(v + "/replay_plan_v32.json", "w"), indent=1)
print("replay set: answerable", len(ids), "(60 ctrl + 44 targets, overlap", 60 + len(tgt) - len(ids), ") + 30 abs")
PY
  ;;
replay|replay-f3fix|replay-f3value|replay-v33|full)
  P="$V/${STAGE}_$SUB"; mkdir -p "$P"
  if [ "$STAGE" = replay ]; then MAT="$V/replay_materialized.jsonl"; FAC="$V/replay_facts.jsonl"
  elif [ "$STAGE" = replay-f3fix ] || [ "$STAGE" = replay-f3value ]; then MAT="$V/replay_materialized.jsonl"; FAC="$V/replay_facts_f3value.jsonl"
  elif [ "$STAGE" = replay-v33 ]; then MAT="$V/replay_materialized.jsonl"; FAC="$V/replay_facts_v33.jsonl"
  else cat "$V/materialized.jsonl" "$V/materialized_abs.jsonl" > "$P/materialized_all.jsonl"; cat "$V/facts.jsonl" "$V/facts_abs.jsonl" > "$P/facts_all.jsonl"; MAT="$P/materialized_all.jsonl"; FAC="$P/facts_all.jsonl"; fi
  date -u +"%Y-%m-%dT%H:%M:%SZ start $STAGE $SUB" >> "$V/timeline.log"
  LME_READER_LANE=cursor-grok LME_READER_MODEL=cursor-grok-4.6-high \
  python3 scripts/run_lme_qa_flash_packets.py --data "$DATA" --materialized "$MAT" --out-dir "$P/reader" --workers "${LME_WORKERS:-4}" --facts "$FAC" > "$P/reader.log" 2>&1
  echo "READER_EXIT=$?"
  [ -f "$P/reader/checkpoint_abs.jsonl" ] || : > "$P/reader/checkpoint_abs.jsonl"
  python3 - "$P" <<'PY'
import json, sys
m = json.load(open(sys.argv[1] + "/reader/run_meta.json"))
print("reader_model", m["reader_model"], "| rows", m["n_rows_total"], "| versions", m.get("prompt_versions"), "| audit clean", m["audit"]["clean"])
PY
  export LME_FLASH_MODEL=opencode-go/glm-5.3-flash
  python3 scripts/rescore_llm_judge_flash.py --answerable "$P/reader/checkpoint_answerable.jsonl" --abs "$P/reader/checkpoint_abs.jsonl" \
    --out-dir "$P/judge" --control-n 12 > "$P/judge.log" 2>&1
  echo "JUDGE_EXIT=$?"
  date -u +"%Y-%m-%dT%H:%M:%SZ judge done $STAGE $SUB" >> "$V/timeline.log"
  python3 - "$P" "$V" <<'PY'
import json, sys
p, v = sys.argv[1], sys.argv[2]
rows = {json.loads(l)["question_id"]: json.loads(l) for l in open(p + "/judge/rescored.jsonl")}
base = {json.loads(l)["question_id"]: json.loads(l)["llm_judge_correct"] for l in open("eval/judge_glm_full500_20260828/dense/rescored.jsonl")}
plan = json.load(open(v + "/replay_plan_v32.json"))
ab = [q for q in rows if q.endswith("_abs")]; ans = [q for q in rows if not q.endswith("_abs")]
print(f"answerable {sum(rows[q]['llm_judge_correct'] for q in ans)}/{len(ans)} | abs {sum(rows[q]['llm_judge_correct'] for q in ab)}/{len(ab)}")
ctl = [q for q in plan["controls_n60"] if q in rows]
print(f"baseline-correct controls: {sum(rows[q]['llm_judge_correct'] for q in ctl)}/{len(ctl)}  regressions: {[q for q in ctl if not rows[q]['llm_judge_correct']]}")
tgt = [q for q in plan["targets_44"] if q in rows]
print(f"44 targets: {sum(rows[q]['llm_judge_correct'] for q in tgt)}/{len(tgt)}")
if len(ans) >= 470:
    n = sum(rows[q]["llm_judge_correct"] for q in ans); a = sum(rows[q]["llm_judge_correct"] for q in ab)
    print(f"FULL: {n}/470 = {n/470:.4f}; 500-basis {n+a}/500 = {(n+a)/5:.2f}%  (v3 448 + 24..25)")
    print("lost vs baseline:", [q for q in ans if base.get(q) and not rows[q]["llm_judge_correct"]])
PY
  ;;
*) echo "unknown stage"; exit 2 ;;
esac
