# GROUND_TRUTH_SURVEY.md — LongMemEval-S / LoCoMo Ground Truth (Phase 1)

Phase 1 deliverable of spec `2618719`. Answers AC1–AC3: dataset identity
and license (re-verified, not restated from the spec's prose), the
canonical judge rubric, the chosen local-inference lane, and whether
LongMemEval-S segments its question set by ability/reasoning type.

## Epistemic grading key

- **[VERIFIED-LIVE]** — confirmed this session against a live primary source
  (fetched LICENSE/README/source, or a command run against this machine).
- **[RECALLED-UNVERIFIED]** — training-data recall only; not treated as ground truth.

## 1. Dataset identity & license (AC1)

### LongMemEval-S [VERIFIED-LIVE — 2026-07-09; re-confirmed 2026-07-10]

| Fact | Value | Exact source |
|---|---|---|
| Paper | Wu et al., ICLR 2025; arXiv:2410.10813 | https://arxiv.org/abs/2410.10813 |
| Code repo | `xiaowu0162/LongMemEval` | https://github.com/xiaowu0162/LongMemEval |
| Dataset (current official) | Hugging Face `xiaowu0162/longmemeval-cleaned` (replaces deprecated `xiaowu0162/longmemeval`) | https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned |
| Record-chase split | `longmemeval_s_cleaned` (~115k-token histories; paper's LongMemEval_S) | README.md data section |
| **License** | **MIT** | **Primary:** `https://raw.githubusercontent.com/xiaowu0162/LongMemEval/main/LICENSE` — full text begins `MIT License` / `Copyright (c) 2024 Di Wu`. **Corroborating:** GitHub repo license badge "MIT license"; HF card for original `xiaowu0162/longmemeval` lists `License: mit`. |

**License file opening lines (verbatim, MIT):**

```
MIT License

Copyright (c) 2024 Di Wu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

**SC-1 check:** LongMemEval-S **is** MIT-licensed. Premise holds; do not halt.

### LoCoMo [VERIFIED-LIVE — 2026-07-09; re-confirmed 2026-07-10]

| Fact | Value | Exact source |
|---|---|---|
| Paper | Maharana et al., ACL 2024 | ACL Anthology 2024.acl-long.747 |
| Code/data repo | `snap-research/locomo` | https://github.com/snap-research/locomo |
| **License** | **CC BY-NC 4.0 (non-commercial)** | **Primary:** `https://raw.githubusercontent.com/snap-research/locomo/main/LICENSE.txt` — title line `Attribution-NonCommercial 4.0 International` and body `Creative Commons Attribution-NonCommercial 4.0 International Public License`. **Corroborating:** ACL paper appendix states the dataset is released under the CC BY-NC 4.0 DEED. |

**Why LongMemEval-S, not LoCoMo, for a COMMERCIAL sovereign claim:**
LoCoMo's CC-BY-NC 4.0 license forbids commercial use of the licensed material
(LICENSE.txt §2(a)(1): rights granted "for NonCommercial purposes only").
A CDS commercial sovereign-record claim built on a non-commercial-licensed
dataset would itself be a licensing problem, independent of any technical
merit. **LongMemEval-S's MIT license carries no commercial-use restriction;
that is the load-bearing reason LongMemEval-S — not LoCoMo — is the
record-chase target for a commercial sovereign claim.**

## 2. Canonical judge rubric (AC2) [VERIFIED-LIVE — 2026-07-09]

**Exact source:**
`https://raw.githubusercontent.com/xiaowu0162/LongMemEval/main/src/evaluation/evaluate_qa.py`
function `get_anscheck_prompt(task, question, answer, response, abstention=False)`.

Canonical setup (same file + README): GPT-4o-class judge
(`gpt-4o-2024-08-06` in `model_zoo`), `temperature=0`, `max_tokens=10`,
binary label via `'yes' in eval_response.lower()`.

### Shared (non-abstention) types — `single-session-user`,
`single-session-assistant`, `multi-session` (verbatim template)

```
I will give you a question, a correct answer, and a response from a model.
Please answer yes if the response contains the correct answer. Otherwise,
answer no. If the response is equivalent to the correct answer or contains
all the intermediate steps to get the correct answer, you should also answer
yes. If the response only contains a subset of the information required by
the answer, answer no.

Question: {question}

Correct Answer: {answer}

Model Response: {response}

Is the model response correct? Answer yes or no only.
```

### `temporal-reasoning` (adds off-by-one day tolerance)

Same base as above, plus: *"In addition, do not penalize off-by-one errors
for the number of days. If the question asks for the number of
days/weeks/months, etc., and the model makes off-by-one errors (e.g.,
predicting 19 days when the answer is 18), the model's response is still
correct."*

### `knowledge-update`

*"If the response contains some previous information along with an updated
answer, the response should be considered as correct as long as the updated
answer is the required answer."*

### `single-session-preference` (rubric instead of gold answer string)

*"Please answer yes if the response satisfies the desired response. ... The
model does not need to reflect all the points in the rubric. The response is
correct as long as it recalls and utilizes the user's personal information
correctly."* — fields labeled Question / Rubric / Model Response.

### Abstention (`question_id` ends with `_abs`)

```
I will give you an unanswerable question, an explanation, and a response
from a model. Please answer yes if the model correctly identifies the
question as unanswerable. The model could say that the information is
incomplete, or some other information is given but the asked information
is not.

Question: {question}

Explanation: {answer}

Model Response: {response}

Does the model correctly identify the question as unanswerable? Answer yes or no only.
```

**Harness consequence:** the agreement seam (`compute_agreement`) consumes
already-scored binary verdicts and does not re-prompt a model.
`invoke_local_judge()` remains a separate CALL seam. It is intentionally
not part of the air-gapped `run` loop (AC8/AC9): live local scoring is an
optional future operator step after local-verdict files exist; the
repeatable scoring loop only reads disk verdict files.

## 3. Local-inference lane choice (AC2)

**[VERIFIED-LIVE — python urllib probe, 2026-07-09; re-probed 2026-07-10; no MoLA start/stop]**

| Lane | Endpoint | 2026-07-09 | 2026-07-10 re-probe |
|---|---|---|---|
| MLX | `http://127.0.0.1:8100/v1` | **unreachable** (`Connection refused`) | **unreachable** (`Connection refused`) |
| Ollama | `http://127.0.0.1:11434` | **HTTP 200** (`/api/tags`) | **HTTP 200** (`/api/tags`) |

**Chosen lane: Ollama (`:11434`).** One-line reason: Ollama is the only
product-guardrail-allowed local lane reachable this session; MLX `:8100`
is down and MoLA must not be started/stopped without operator order
(2026-03-28 kernel-panic guardrail).

**SC-2 check:** at least one of MLX/Ollama is reachable → do not halt.

**No MoLA start/stop occurred during this survey.** Only a read-only
Python `urlopen` probe against already-listening (or refused) ports.

## 4. Ability/reasoning-type segmentation (AC3) [VERIFIED-LIVE]

**Yes — LongMemEval segments by ability / question type.**

Official five core abilities (README + paper): Information Extraction,
Multi-Session Reasoning, Knowledge Updates, Temporal Reasoning, Abstention.

**`question_type` field values** (README dataset format +
`evaluate_qa.py` task keys):

| `question_type` | Notes |
|---|---|
| `single-session-user` | IE — user-side fact in one session |
| `single-session-assistant` | IE — assistant-side fact in one session |
| `single-session-preference` | Personalization / preference use |
| `multi-session` | Cross-session synthesis / comparison |
| `temporal-reasoning` | Explicit + implicit time |
| `knowledge-update` | Updated user state over time |
| `abstention` | Unanswerable / false-premise; encoded as `question_id` suffix `_abs` |

`compute_agreement()` does **not** hardcode this list — segmentation is
inferred from non-empty `ability_type` on **both** local and canonical
verdict files for every matched item. Corrected type names need no code
change.

## 5. AC3 vacuous case (mechanical)

If a slice has no `ability_type` on either side, `segmented=False`,
`per_type={}`, and the receipt writes the explicit marker `"not_segmented"`
(AC7). Proven by `test_unsegmented_fixture_produces_aggregate_only_result`
and `test_receipt_marks_not_segmented_explicitly`.

## Summary table

| Item | Status this session | Confidence |
|---|---|---|
| LongMemEval-S location + MIT license | Re-confirmed vs LICENSE + HF | **VERIFIED-LIVE** |
| LoCoMo location + CC-BY-NC 4.0 | Re-confirmed vs LICENSE.txt | **VERIFIED-LIVE** |
| MIT-vs-CC-BY-NC record-chase-target reason | Stated | **VERIFIED-LIVE** |
| Judge rubric (verbatim templates) | Transcribed from evaluate_qa.py | **VERIFIED-LIVE** |
| Local-inference lane (Ollama) | Chosen; only live lane | **VERIFIED-LIVE** |
| No MoLA start/stop | Confirmed | **VERIFIED-LIVE** |
| Type segmentation = yes + type names | Confirmed vs README/source | **VERIFIED-LIVE** |
| AC3 vacuous-case code path | Implemented + tested | **VERIFIED-LIVE** |

**Net: AC1/AC2/AC3 re-verification bars are MET for this session (2026-07-10).**

Live re-confirmations this session:
- LongMemEval LICENSE raw URL → MIT License / Copyright (c) 2024 Di Wu
- LoCoMo LICENSE.txt raw URL → CC BY-NC 4.0 (Attribution-NonCommercial 4.0 International)
- Lane probe: Ollama `:11434` HTTP 200; MLX `:8100` refused; no MoLA touch
- Fixture evidence runs: `sovereign_claim=ALLOWED` + `WITHHELD` receipts under
  `~/.governance/receipts/longmemeval-judge-gate/` (20260710T092236*)
- `gather-canonical` exit 4 with OPERATOR COMMIT message; missing
  `--canonical-verdicts` exit 2 with operator-authorization message
- pytest: 31/31 pass

Remaining operator-gated work is outside the pure agreement gate: download
the real LongMemEval-S slice, obtain canonical GPT-judge labels
(`gather-canonical` / OPERATOR COMMIT), and optionally score local-judge
labels via Ollama using the transcribed rubric.
