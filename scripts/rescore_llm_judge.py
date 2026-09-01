#!/usr/bin/env python3
"""Rescore the stored n500 cloud-reader responses with an LLM judge running
the OFFICIAL LongMemEval rubric templates.

Why: the original run scored with ``official_judge`` = ``contains_gold``, a
deterministic substring/bag-of-words matcher. The published LongMemEval
numbers (Emergence Simple 82.4% etc.) were scored by a GPT-4o-class LLM
judge with per-type rubric prompts. Same responses, different ruler. This
script re-runs ONLY the judging step over the frozen responses — it does not
touch retrieval, the reader, archivist.db, or :4244.

Rubric source: benchmarks/longmemeval-judge-gate/GROUND_TRUTH_SURVEY.md §2
(verbatim transcription of LongMemEval evaluate_qa.py get_anscheck_prompt,
VERIFIED-LIVE 2026-07-09). The single-session-preference header sentence is
elided in the survey; it is reconstructed here and flagged in the receipt.

Controls run FIRST and gate the full pass (fail-closed):
  positive: response := gold verbatim      -> judge must say yes
  negative: response := another row's resp -> judge must say no
Either control below threshold aborts with a control receipt and no verdict.

Usage:
  python3 scripts/rescore_llm_judge.py \
      --answerable <checkpoint_answerable.jsonl> \
      --abs <checkpoint_abs.jsonl> \
      --out-dir eval/lme_qa_cloud_n500_rescore_20260827 \
      --model deepseek-v4-pro:cloud
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OLLAMA_GENERATE_URL = "http://127.0.0.1:11434/api/generate"

BASE_TEMPLATE = (
    "I will give you a question, a correct answer, and a response from a model. "
    "Please answer yes if the response contains the correct answer. Otherwise, "
    "answer no. If the response is equivalent to the correct answer or contains "
    "all the intermediate steps to get the correct answer, you should also answer "
    "yes. If the response only contains a subset of the information required by "
    "the answer, answer no.\n\n"
    "Question: {question}\n\n"
    "Correct Answer: {answer}\n\n"
    "Model Response: {response}\n\n"
    "Is the model response correct? Answer yes or no only."
)

TEMPORAL_ADDITION = (
    " In addition, do not penalize off-by-one errors for the number of days. "
    "If the question asks for the number of days/weeks/months, etc., and the "
    "model makes off-by-one errors (e.g., predicting 19 days when the answer "
    "is 18), the model's response is still correct."
)

KU_ADDITION = (
    " If the response contains some previous information along with an updated "
    "answer, the response should be considered as correct as long as the "
    "updated answer is the required answer."
)

# Header sentence reconstructed (survey elides it); rubric semantics verbatim
# from the survey transcription.
SSP_TEMPLATE = (
    "I will give you a question, a rubric for desired personalized response, "
    "and a response from a model. "
    "Please answer yes if the response satisfies the desired response. "
    "Otherwise, answer no. The model does not need to reflect all the points "
    "in the rubric. The response is correct as long as it recalls and utilizes "
    "the user's personal information correctly.\n\n"
    "Question: {question}\n\n"
    "Rubric: {answer}\n\n"
    "Model Response: {response}\n\n"
    "Is the model response correct? Answer yes or no only."
)

ABS_TEMPLATE = (
    "I will give you an unanswerable question, an explanation, and a response "
    "from a model. Please answer yes if the model correctly identifies the "
    "question as unanswerable. The model could say that the information is "
    "incomplete, or some other information is given but the asked information "
    "is not.\n\n"
    "Question: {question}\n\n"
    "Explanation: {answer}\n\n"
    "Model Response: {response}\n\n"
    "Does the model correctly identify the question as unanswerable? "
    "Answer yes or no only."
)


def build_prompt(question_type: str, question: str, gold: str, response: str,
                 *, abstention: bool) -> str:
    if abstention:
        return ABS_TEMPLATE.format(question=question, answer=gold,
                                   response=response)
    if question_type == "single-session-preference":
        return SSP_TEMPLATE.format(question=question, answer=gold,
                                   response=response)
    base = BASE_TEMPLATE
    if question_type == "temporal-reasoning":
        base = base.replace(
            "answer, answer no.\n\n",
            "answer, answer no." + TEMPORAL_ADDITION + "\n\n")
    elif question_type == "knowledge-update":
        base = base.replace(
            "answer, answer no.\n\n",
            "answer, answer no." + KU_ADDITION + "\n\n")
    return base.format(question=question, answer=gold, response=response)


def _judge_payload(model: str, prompt: str, *, think: bool,
                   num_predict: int) -> bytes:
    """Serialize one /api/generate judge request body.

    Split out so the transport shape is testable without a live Ollama.
    ``think`` and ``num_predict`` are TRANSPORT parameters, never rubric:
    the prompt templates in build_prompt are frozen and untouched by both.
    """
    return json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "num_predict": num_predict},
        "think": think,
    }).encode("utf-8")


def _extract_verdict(text: str) -> bool | None:
    """Verdict from the response channel's first word, or None if the model
    did not lead with yes/no.

    The rubric says 'Answer yes or no only.' A terse model emits exactly
    that and this equals the historical full-text containment check. A
    verbose model (glm-5.3:cloud with think:true) may append explanation
    prose AFTER the verdict — scanning the full text would false-positive
    on a 'No' explanation that mentions the word 'yes'. The verdict is the
    first word; markdown emphasis and trailing punctuation are stripped.
    """
    if not text.strip():
        return None
    first = text.strip().splitlines()[0].strip()
    first = first.replace("*", "").replace("_", "").replace("`", "").strip()
    words = first.split()
    if not words:
        return None
    word = words[0].strip(".,!?;:").lower()
    if word == "yes":
        return True
    if word == "no":
        return False
    return None


def judge_once(model: str, prompt: str, timeout_s: int, max_attempts: int,
               backoff_s: float, *, think: bool = False,
               num_predict: int = 10) -> tuple[bool, str, int]:
    payload = _judge_payload(model, prompt, think=think,
                             num_predict=num_predict)
    last_err = ""
    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(
            OLLAMA_GENERATE_URL, data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            text = str(body.get("response", "")).strip()
            # Fail-closed on the two silent-garbage shapes a thinking judge
            # produces when its reasoning eats the num_predict budget:
            #   empty response channel (done_reason=length) -> retry
            #   no leading yes/no                      -> retry
            # Both exhausted -> raise. Never record a silent False.
            verdict = _extract_verdict(text)
            if verdict is None:
                last_err = (f"no yes/no verdict in response channel "
                            f"(len={len(text)}): {text[:80]!r}")
                time.sleep(backoff_s * attempt)
                continue
            return (verdict, text, attempt)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError,
                json.JSONDecodeError) as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            time.sleep(backoff_s * attempt)
    raise RuntimeError(f"judge call failed after {max_attempts}: {last_err}")


def load_rows(path: Path) -> list[dict]:
    rows = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def summary_caveats(model: str) -> list[str]:
    """Return provenance-accurate caveats for any supported judge transport."""
    return [
        f"Judge model is {model}, not gpt-4o-2024-08-06; cross-judge "
        "agreement with the canonical judge is NOT established by this run.",
        "Responses are frozen from the named input checkpoints. Retrieval and "
        "reader provenance remain governed by those checkpoints' run receipts; "
        "this script changes only the ruler.",
    ]


def run_controls(rows: list[dict], model: str, n: int, timeout_s: int,
                 max_attempts: int, backoff_s: float, out_dir: Path, *,
                 think: bool = False, num_predict: int = 10) -> dict:
    rng = random.Random(20260827)
    eligible = [r for r in rows if r.get("response") and r.get("gold")]
    sample = rng.sample(eligible, min(n, len(eligible)))
    pos_total = pos_pass = neg_pass = 0
    records = []
    for row in sample:
        q, g, t = row["question"], row["gold"], row.get("question_type", "")
        # positive: gold verbatim as the response. INVALID for
        # single-session-preference — gold there is a rubric, and a rubric
        # pasted as a response does not satisfy itself; a correct judge says
        # no. Excluded from the positive arm (kept in the negative arm).
        pos_ok = None
        raw = ""
        if t != "single-session-preference":
            p = build_prompt(t, q, g, g, abstention=False)
            yes, raw, _ = judge_once(model, p, timeout_s, max_attempts,
                                     backoff_s, think=think,
                                     num_predict=num_predict)
            pos_ok = yes
            pos_total += 1
            pos_pass += int(pos_ok)
        # negative: a different row's response
        other = rng.choice([r for r in eligible
                            if r["question_id"] != row["question_id"]])
        p = build_prompt(t, q, g, other["response"], abstention=False)
        yes, raw_n, _ = judge_once(model, p, timeout_s, max_attempts,
                                   backoff_s, think=think,
                                   num_predict=num_predict)
        neg_ok = not yes
        neg_pass += int(neg_ok)
        records.append({"question_id": row["question_id"],
                        "question_type": t,
                        "positive_pass": pos_ok, "negative_pass": neg_ok,
                        "positive_raw": raw, "negative_raw": raw_n})
    result = {
        "n": len(sample),
        "n_positive_eligible": pos_total,
        "positive_pass": pos_pass,
        "negative_pass": neg_pass,
        "positive_rate": pos_pass / max(1, pos_total),
        "negative_rate": neg_pass / max(1, len(sample)),
        "threshold": 0.9,
        "ssp_excluded_from_positive_arm": True,
        "records": records,
    }
    (out_dir / "control_receipt.json").write_text(json.dumps(result, indent=1))
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--answerable", required=True)
    ap.add_argument("--abs", dest="abs_path", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--model", default="deepseek-v4-pro:cloud")
    ap.add_argument("--timeout-s", type=int, default=300)
    ap.add_argument("--max-attempts", type=int, default=4)
    ap.add_argument("--backoff-s", type=float, default=1.0)
    ap.add_argument("--control-n", type=int, default=20)
    ap.add_argument("--think", action="store_true",
                    help="pass think:true to Ollama so reasoning lands in "
                         "the separate thinking channel and the response "
                         "carries only the verdict. Required for "
                         "inline-narrating judge models (e.g. glm-5.3:cloud "
                         "emits '<think>...</think>yes' into the response "
                         "channel when think is false, which a small "
                         "num_predict truncates before the verdict).")
    ap.add_argument("--num-predict", type=int, default=10,
                    help="num_predict cap for one judge call. With --think "
                         "the cap must cover thinking + verdict (glm-5.3 "
                         "judge calls measure ~50 eval tokens; 512 is safe).")
    ap.add_argument("--skip-controls", action="store_true",
                    help="resume mode only; controls must already have passed")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ans_rows = load_rows(Path(args.answerable))
    abs_rows = load_rows(Path(args.abs_path))

    if not args.skip_controls:
        ctrl = run_controls(ans_rows, args.model, args.control_n,
                            args.timeout_s, args.max_attempts, args.backoff_s,
                            out_dir, think=args.think,
                            num_predict=args.num_predict)
        print(f"controls: positive {ctrl['positive_pass']}/{ctrl['n']} "
              f"negative {ctrl['negative_pass']}/{ctrl['n']}", flush=True)
        if (ctrl["positive_rate"] < 0.9) or (ctrl["negative_rate"] < 0.9):
            print("CONTROL FAILURE — aborting, no verdict. "
                  "See control_receipt.json", flush=True)
            return 2
    elif not (out_dir / "control_receipt.json").exists():
        print("--skip-controls without a prior control receipt — refusing.",
              flush=True)
        return 2

    ckpt_path = out_dir / "rescored.jsonl"
    done_ids = set()
    if ckpt_path.exists():
        for row in load_rows(ckpt_path):
            done_ids.add(row["question_id"])

    def rescore(rows: list[dict], *, abstention: bool) -> None:
        with ckpt_path.open("a") as fh:
            for i, row in enumerate(rows):
                if row["question_id"] in done_ids:
                    continue
                response = row.get("response") or ""
                if not response:
                    verdict, raw, attempts = False, "", 0
                else:
                    prompt = build_prompt(row.get("question_type", ""),
                                          row["question"], row["gold"],
                                          response, abstention=abstention)
                    verdict, raw, attempts = judge_once(
                        args.model, prompt, args.timeout_s,
                        args.max_attempts, args.backoff_s, think=args.think,
                        num_predict=args.num_predict)
                fh.write(json.dumps({
                    "question_id": row["question_id"],
                    "question_type": row.get("question_type", ""),
                    "abstention": abstention,
                    "string_judge_correct": bool(row.get("correct")),
                    "llm_judge_correct": verdict,
                    "llm_judge_raw": raw,
                    "attempts": attempts,
                    "scored_at": datetime.now(timezone.utc).isoformat(),
                }) + "\n")
                fh.flush()
                if (i + 1) % 25 == 0:
                    print(f"  {'abs' if abstention else 'ans'} {i+1}/{len(rows)}",
                          flush=True)

    rescore(ans_rows, abstention=False)
    rescore(abs_rows, abstention=True)

    # summarize
    scored = load_rows(ckpt_path)
    ans = [r for r in scored if not r["abstention"]]
    abst = [r for r in scored if r["abstention"]]
    per_type: dict[str, dict[str, int]] = defaultdict(lambda: {"n": 0,
                                                               "string": 0,
                                                               "llm": 0})
    flips_up = flips_down = 0
    for r in ans:
        b = per_type[r["question_type"]]
        b["n"] += 1
        b["string"] += int(r["string_judge_correct"])
        b["llm"] += int(r["llm_judge_correct"])
        if r["llm_judge_correct"] and not r["string_judge_correct"]:
            flips_up += 1
        if r["string_judge_correct"] and not r["llm_judge_correct"]:
            flips_down += 1
    summary = {
        "schema": "cds/lme-qa-llm-judge-rescore/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "judge_model": args.model,
        "judge_transport": {"endpoint": OLLAMA_GENERATE_URL,
                            "think": args.think,
                            "num_predict": args.num_predict},
        "rubric_source": ("benchmarks/longmemeval-judge-gate/"
                          "GROUND_TRUTH_SURVEY.md §2 (official templates; "
                          "SSP header sentence reconstructed)"),
        "inputs": {"answerable": args.answerable, "abs": args.abs_path},
        "n_answerable": len(ans),
        "string_judge_accuracy": (sum(r["string_judge_correct"] for r in ans)
                                  / max(1, len(ans))),
        "llm_judge_accuracy": (sum(r["llm_judge_correct"] for r in ans)
                               / max(1, len(ans))),
        "flips_string_wrong_llm_right": flips_up,
        "flips_string_right_llm_wrong": flips_down,
        "per_type": {t: {"n": b["n"],
                         "string_acc": b["string"] / max(1, b["n"]),
                         "llm_acc": b["llm"] / max(1, b["n"])}
                     for t, b in sorted(per_type.items())},
        "abstention": {
            "n": len(abst),
            "llm_judge_refusal_recognized": sum(r["llm_judge_correct"]
                                                for r in abst),
        },
        "caveats": summary_caveats(args.model),
    }
    (out_dir / "rescore_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: summary[k] for k in
                      ("string_judge_accuracy", "llm_judge_accuracy",
                       "flips_string_wrong_llm_right",
                       "flips_string_right_llm_wrong")}, indent=1))
    print("per_type:", json.dumps(summary["per_type"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
