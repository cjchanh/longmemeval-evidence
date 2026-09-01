#!/usr/bin/env bash
# Waits for v33 pass 2 judging, evaluates the frozen gates mechanically, and
# ONLY on PASS launches both full passes concurrently (6 workers each).
# Gates (lock v3, operator-directed): zero controls wrong in BOTH passes;
# abstention >= 25/30 in both passes; zero reader errors either pass.
set -u
V=eval/dense_chain_v32_20260830
until [ "$(wc -l < $V/replay-v33_pass2/judge/rescored.jsonl 2>/dev/null | tr -d ' ')" = "134" ]; do sleep 60; done
sleep 10
python3 - "$V" <<'PY'
import json, sys
v = sys.argv[1]
plan = json.load(open(v + "/replay_plan_v32.json"))
def load(label):
    return {json.loads(l)["question_id"]: json.loads(l) for l in open(v + f"/replay-v33_{label}/judge/rescored.jsonl")}
p1, p2 = load("pass1"), load("pass2")
def readers_clean(label):
    for f in ("checkpoint_answerable.jsonl", "checkpoint_abs.jsonl"):
        for l in open(v + f"/replay-v33_{label}/reader/" + f):
            if json.loads(l).get("error"):
                return False
    return True
ctl = plan["controls_n60"]
reg = [q for q in ctl if not p1[q]["llm_judge_correct"] and not p2[q]["llm_judge_correct"]]
abs1 = sum(1 for q in p1 if q.endswith("_abs") and p1[q]["llm_judge_correct"])
abs2 = sum(1 for q in p2 if q.endswith("_abs") and p2[q]["llm_judge_correct"])
ans2 = sum(1 for q in p2 if not q.endswith("_abs") and p2[q]["llm_judge_correct"])
tgt2 = sum(1 for q in plan["targets_44"] if p2[q]["llm_judge_correct"])
ctl2 = sum(1 for q in ctl if p2[q]["llm_judge_correct"])
print(f"PASS2: ans {ans2}/104 ctl {ctl2}/60 tgt {tgt2}/44 abs {abs2}/30")
print(f"GATES: control_regressions_both={reg} abs=({abs1},{abs2}) readers_clean=({readers_clean('pass1')},{readers_clean('pass2')})")
ok = not reg and abs1 >= 25 and abs2 >= 25 and readers_clean("pass1") and readers_clean("pass2")
print("GATES_VERDICT:", "PASS" if ok else "BLOCKED")
sys.exit(0 if ok else 7)
PY
if [ $? -ne 0 ]; then echo "GATES BLOCKED — NOT launching full passes"; exit 7; fi
echo "GATES PASS — launching full pass1 + pass2 concurrently (6 workers each)"
LME_WORKERS=6 nohup bash $V/run_v32_chain.sh full pass1 > $V/full_pass1.launch.log 2>&1 &
LME_WORKERS=6 nohup bash $V/run_v32_chain.sh full pass2 > $V/full_pass2.launch.log 2>&1 &
echo "launched: $(jobs -p | tr '\n' ' ')"
wait
echo "both full stages exited"
tail -6 $V/full_pass1.launch.log
tail -6 $V/full_pass2.launch.log
