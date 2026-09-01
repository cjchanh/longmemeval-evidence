# v4 Evidence-Sufficiency Gate — v0 Results

**Date:** 2026-08-31
**Worker:** W2 (v4 campaign, LongMemEval-S dense chain)
**Gate version:** `cds/v4-sufficiency-gate/v0`
**Artifacts:** `scripts/v4_sufficiency.py` · `scripts/v4_nc_harness.py` ·
`nc_summary_pass1.json` · `nc_results_pass1.jsonl` · `nc_summary_pass2.json` · `nc_results_pass2.jsonl`

---

## Headline

**Acceptance run (pass1 responses, as specified): PASS.** 1 control flip in 471 · 3 of 4 abs-miss rows caught.

**Replication (pass2 responses): would be BLOCKED.** 1 control flip in 471 · 2 of 4 caught.

**Integration recommendation: DO NOT INTEGRATE YET.** The frozen rule was met on the
specified apparatus, but a single passing run at the margin is not a result. The two
passes disagree on the acceptance criterion, and the frames' base rate (below) shows
near-zero evidence of generalization.

---

## The frozen acceptance rule

Written into `scripts/v4_nc_harness.py` as constants before the first run, unchanged since:

```
MAX_CONTROL_FLIPS = 2
MIN_ABS_CATCHES   = 3
MIN_CONTROL_ROWS  = 230
KNOWN_ABS_MISS_ROWS = (a96c20ee_abs, 09ba9854_abs, gpt4_fe651585_abs, 031748ae_abs)

BLOCKED if control flips > 2, or if abs-miss catches < 3 of 4.
```

**Control set derivation (mechanical, no hand-picking):** every `question_id` with
`llm_judge_correct == true` in *both* `full-v34_pass1/judge_gpt4o/rescored.jsonl` and
`full-v34_pass2/judge_gpt4o/rescored.jsonl`. Measured size **471** — above the 230 floor.
Pass1 responses are the graded ones.

**Statistical note:** at a 2% true flip rate, P(0 flips in 230) = 0.98^230 = 0.0094 (<1%).
Over the observed 471 controls, 0.98^471 = 7.4e-05. A near-zero observed flip count rules
out a >=2% flip rate at better than the 1% level. The converse does NOT follow: a low flip
rate says nothing about whether the gate catches anything. The abs-catch clause carries
that half, and it is the clause that fails on pass2.

---

## Results

### Acceptance run — pass1 responses

| Metric | Value |
|---|---|
| Control rows | 471 |
| Control rows where reader already abstained (SKIP) | 24 |
| Control rows the gate actually judged | 447 |
| **Control flips (correct answers refused)** | **1** |
| **Abs-miss rows caught** | **3 / 4** |
| Verdict | **PASS** |

| Row | Gate verdict | Chain class | Detector |
|---|---|---|---|
| `a96c20ee_abs` | PASS *(missed)* | INFERRED | — |
| `09ba9854_abs` | REFUSE | INFERRED | FRAME_D |
| `gpt4_fe651585_abs` | REFUSE | INFERRED | FRAME_A |
| `031748ae_abs` | REFUSE | STATED | FRAME_B |

The single control flip: `078150f1` (FRAME_D) — "How much more money did I raise than my
initial goal in the charity cycling event?"

**Why that flip happens, honestly:** the user *did* state the goal — "$200" on May 20 — but
never used the word "goal" in the same turn as the figure. FRAME_D looks for the operand
token co-occurring with a number in a user turn, so a paraphrased operand reads as
never-user-stated. A real limitation of lexical operand matching, not a tuning artifact.
It was not special-cased away.

### Replication — pass2 responses

Control flips **1** (same row) · abs catches **2 / 4** · verdict under the same rule **BLOCKED**.

The lost catch is `gpt4_fe651585_abs`. FRAME_A fires identically in both passes — question
and packet are unchanged — but in pass2 the reader answered "Alex (Tom not mentioned)",
which the commitment classifier reads as an abstention (`SKIP_NOT_COMMITTED`), so the gate
never reaches its verdict. The GPT-4o judge also scored that pass2 response **correct**, so
pass2's `gpt4_fe651585_abs` is arguably not an over-commitment failure at all.

Defensible behaviour, still a finding: **the catch on that row depends on the reader's
phrasing, not on the evidence.** The commitment classifier is load-bearing and
response-fragile.

### Full-500 cross-tab (all rows, not just controls)

Response-independent frame base rate over all 500 questions:

| Detector | Fires on | Rows |
|---|---|---|
| FRAME_A comparison-alternative-absent | 1 / 500 | `gpt4_fe651585_abs` |
| FRAME_B title-phrase-absent | 1 / 500 | `031748ae_abs` |
| FRAME_D operand-never-user-stated | 2 / 500 | `078150f1`, `09ba9854_abs` |

Gate verdict x judge correctness, all 500 rows:

| Pass | REFUSE rows | on incorrect (TP) | on correct (FP) | Net score effect |
|---|---|---|---|---|
| pass1 | 4 | 3 | 1 | **+2** (476 -> 478) |
| pass2 | 3 | 2 | 1 | **+1** (474 -> 475) |

**Read this as the limiting result, not the encouraging one.** The frames fire on 4 rows out
of 500, and 3 of those 4 are rows the frames were designed from. A detector that fires once
in 500 and that one row is its own design example has demonstrated *precision*, not
*generality*. The +2/+1 is real but does not reach the 479 target, and there is no evidence
it transfers to rows outside this eval.

---

## What the gate does

**(a) Span verification — implemented, ADVISORY ONLY in v0.** Extraction rule: a span is any
double-quoted or smart-quoted fragment of >=4 normalized tokens; `**bold**` is NOT treated as
a citation because the reader uses it to emphasise its own prose. Each span is checked for
normalized-substring presence in the packet.

Advisory because it was measured and does not hold up as a trigger: 10 of 447 committed
controls carry an unverified quote — the reader has no citation contract, so it quotes
paraphrastically ("the past three months", "A couple of days ago"). Wiring that to REFUSE
would blow the 2-flip budget fivefold. Under the v1 citation contract, spans become verbatim
by construction and this becomes the strongest available trigger.

**(b) Chain classification — implemented, REPORTED, not enforced.** `STATED` (one turn holds
answer + the question's rarest anchors) / `INFERRED` (answer present but never co-occurring
with anchors in one turn) / `ARITHMETIC` (explicit computation present) / `UNRESOLVED`
(answer not literally in packet — aggregations, counts; 176/447 controls, and NOT a defect).

Not enforced because it was measured and fails: refusing on `INFERRED` costs **44 control
flips for 2 catches** (~4% precision). Cross-turn joining is normal and correct on
multi-session LongMemEval rows.

**(c) Verdict.** REFUSE only when the reader committed AND one of three narrow presupposition
frames fires:

- **FRAME_A** — a comparison question ("who ... first, X or Y") whose alternative is absent
  from the packet. `Tom` never appears; the comparison has no ground.
- **FRAME_B** — a Title Case role/appositive phrase from the question is absent. "as Software
  Engineer Manager" vs a packet that only says "Senior Software Engineer" — a near-miss the
  reader silently accepted.
- **FRAME_D** — a derived-quantity question where a compared operand has no user-stated
  figure. Every bus figure in `09ba9854_abs` ($29 / 3,200 yen / "Airport Limousine Bus") is
  assistant-authored; the gold is exactly "you did not mention how much the bus will take".
  Assistant-authored figures are not the user's memory and must not be laundered into an answer.

---

## Approaches measured and rejected

All on the 447 committed controls. Each was implemented and run, not reasoned away:

| Candidate | Control flips | Abs catches |
|---|---|---|
| Question content-term absence (len >= 5) | 93 | 1 |
| Proper-noun absence | 32 | 1 |
| Content-bigram absence | 290 | 4 |
| Answer/anchor bag-of-words coverage (best threshold) | 44 | 2 |
| Explicit-arithmetic present | 8 | 0 |
| Self-admitted-gap phrasing | 3 | 1 |
| Possessive-NP modifier absence (FRAME_C) | 6 | 1 (`a96c20ee_abs`) |

**These abs rows are not lexically unusual.** `031748ae_abs` has *perfect* question-anchor
coverage (3/3) and is still wrong, because the discrimination is semantic: "Senior Software
Engineer" is not "Software Engineer Manager". Bag-of-words coverage is actively inverted —
the abs rows score *above* the control median. That is why v0 is built from narrow syntactic
presupposition frames rather than any overlap statistic.

**FRAME_C is the one that would catch `a96c20ee_abs`** (missing modifier "undergrad" in "my
undergrad course research project"). Excluded at 6 flips. A pre-head-modifier restriction
would cut it to roughly 2, but that restriction was selected by looking at which control rows
it flipped — fitting to the control set, which the frozen rule exists to stop. Left out and
named as a v1 target instead.

---

## Bias disclosure

The control set was not a clean held-out set. It was used to *reject* candidate detectors
(table above), so it informed the design, and the 1-flip figure is optimistically biased. Two
mitigations were run:

1. **Pass2 replication** — independent generations, same rows. Flip count holds at 1; catch
   count drops to 2.
2. **Frame base rate over all 500 questions** — response-independent, so not an artifact of
   which rows were inspected. A=1, B=1, D=2 per 500. Bounds blast radius tightly, and equally
   shows the frames are near-row-specific.

One repair was made after the first acceptance run: FRAME_D's operand extractor anchored on
the preposition in "by taking the bus" and captured the gerund `taking` instead of the operand
`bus`, so its own target row was never tested. A demonstrable extraction bug found from the
positive class; the fix used no control-set information. Declared because it moved the verdict
from BLOCKED (2 catches) to PASS (3 catches), and a repair that moves a verdict deserves to be
visible.

---

## Citation contract the reader prompt must add for v1

Emit with `python3 scripts/v4_sufficiency.py --print-contract`. Verbatim:

```
For every factual claim that supports your answer, emit a citation block:

  [[CITE s=<session_index> r=<user|assistant> "<verbatim substring>"]]

Rules the gate enforces mechanically:
  1. The quoted substring MUST be copied byte-for-byte from that turn. Do not
     paraphrase, normalize, ellipsize, or re-case inside the quotes.
  2. Cite the turn that CONTAINS the fact, not the turn that discusses it.
  3. If your answer requires combining two citations, emit
     [[LINK a=<cite_id> b=<cite_id> stated=<yes|no>]] and set stated=no when
     the packet never states the connection in one turn.
  4. If any figure in your answer came from an assistant turn rather than the
     user, mark it [[CITE ... r=assistant]] — do not launder it as user-stated.
  5. If a term in the question does not appear in the packet at all, emit
     [[MISSING "<term>"]] before answering.

Emitting [[LINK stated=no]] or [[MISSING ...]] and then committing to a
definite answer is the exact over-commitment the gate refuses.
```

Each rule is load-bearing for a specific measured failure:

- **Rule 1** turns span verification from advisory into enforceable — removes the
  paraphrastic-quote noise that costs 10 flips today.
- **Rule 3** is what catches `a96c20ee_abs`. The pass2 reader literally wrote "Linking those
  two statements" — under the contract that is a `[[LINK stated=no]]`, and committing anyway
  is a mechanical REFUSE. No lexical heuristic caught this row inside budget.
- **Rule 4** turns FRAME_D from a lexical guess into a declaration, removing the `078150f1`
  false positive: the reader would cite the user's "$200" turn directly and the
  paraphrased-operand problem disappears.
- **Rule 5** makes FRAME_A/FRAME_B redundant-but-verifiable rather than regex-dependent.

---

## What would make this integrable

1. **Reader emits the citation contract**, then re-run the NC harness. Expect span
   verification to move from advisory to enforcing.
2. **A clean held-out control set** — rows from a run whose failures were never inspected
   during design (e.g. `full-v34-gemini_pass1`, `full-v34-nemotron_pass1`). The current 471 is
   contaminated by detector selection.
3. **Both passes must agree** on the acceptance criterion. They do not today.
4. **Make the fe651585 catch response-independent.** Today it is gated by the commitment
   classifier, which reads a hedged answer as an abstention.
5. **Implement `llm_sufficiency_probe`** (interface defined, raises `NotImplementedError` in
   v0) against the cited spans only — the judge must not be able to re-retrieve. The only
   route found so far to the `a96c20ee_abs` class.

---

## Reproduce

```
python3 scripts/v4_nc_harness.py \
  --eval-dir eval/dense_chain_v32_20260830 \
  --out-dir  eval/dense_chain_v32_20260830/v4/sufficiency \
  --responses pass1

python3 scripts/v4_sufficiency.py \
  --reader  eval/dense_chain_v32_20260830/full-v34_pass1/reader/checkpoint_abs.jsonl \
  --packets eval/dense_chain_v32_20260830/materialized_abs.jsonl \
  --rows a96c20ee_abs,09ba9854_abs,gpt4_fe651585_abs,031748ae_abs
```

Harness exit code is 0 on PASS, 1 on BLOCKED.
