# Gold-Defect Dossier — LongMemEval-S dense-chain campaign

Date: 2026-08-31 · Judge: gpt-4o-2024-08-06 (paper rubric, api transport)
Reader: cursor-grok-4.6-high · Chain: v3.4 (commit 04eb64763)
Pair result these rows are scored inside: 476/474 per 500 (475±1 vs Mastra 474).

Method: every row below was answered wrong (or flip-unstable) in the official
pair. For each, the packet evidence was re-read manually; the claim "gold is
defective" is made ONLY where the evidence cannot produce gold, contradicts
gold, or gold requires an arithmetic/category error. Boundary rows — where a
reasonable annotator could defend either reading — are classed separately and
NOT claimed as defects. Two historical candidates that current runs answer
correctly are retained as resolved, for honesty about the moving list.

Severity classes:
- **A — gold unreachable without fabrication** (evidence lacks a required fact)
- **B — gold arithmetic error**
- **C — gold category error**
- **D — boundary semantics** (both readings defensible; not claimed)
- **E — resolved** (historical candidate; current chain matches gold)

---

## Class A — gold unreachable without fabrication

### gpt4_731e37d7 (multi-session) — VERIFIED IN FULL
Q: "How much total money did I spend on attending workshops in the last four months?"
Gold: **$720** (= $200 + $20 + $500)

Packet facts (exhaustive dollar-amount inventory performed):
- $200 writing workshop (November) — user-stated, in window.
- $20 mindfulness workshop (Dec 12) — user-stated, in window.
- **No $500 attached to any workshop exists anywhere in the evidence.** Every
  "$500" occurrence is website cost-filter boilerplate ("under $100, $100-$500…")
  or an immigration-form fee in an unrelated session.
- The only dated mention of the digital-marketing workshop is internally
  impossible: a session dated **2023/02/26** says "I just attended a digital
  marketing workshop … **on March 15-16**" — a past-tense attendance of a
  future date.

Evidence-faithful answer: $220. Both official passes answered $220 → scored 0.
Control datum: a weaker reader (gemini-3.7-flash probe) HALLUCINATED a
"$500 Digital Marketing Workshop (Recent)", summed $720, and was scored
CORRECT — the judge rewards fabrication that matches defective gold.

## Class B — gold arithmetic error

### 370a8ff4 (temporal-reasoning)
Q: "How many weeks had passed since I recovered from the flu when I went on my 10th jog outdoors?"
Gold: **15**

Packet dates (user-stated, both passes agree): recovered 2023/01/19 ("today"),
10th outdoor jog 2023/04/10 ("today"). Elapsed: 81 days = **11 weeks 4 days**.
No reading of the two dated statements yields 15 weeks (15 weeks = 105 days
would place the jog on May 4). Evidence-faithful answer: 11. Both passes: 11 → 0.

## Class C — gold category error

(none surviving review — 71017277 was downgraded to Class D after an
independent-reader control; see below)

---

## Class D — boundary semantics (NOT claimed as defects)

### 71017277 — premise-repair vs premise-refusal (downgraded from C)
Q: "I received a piece of jewelry last Saturday from whom?" Gold: my aunt.
Evidence: the aunt gave a **crystal chandelier** that Saturday; no jewelry
gift or giver exists in the sessions. Grok (both passes) refused the false
premise ("aunt gave a chandelier, not jewelry") → 0. The Sol reader answered
the question's intent — who gave me the thing — with "your aunt" and was
scored correct. Both stances are defensible: gold mislabels the object, but
the intended referent is unambiguous. Boundary, not a strict defect.

### gpt4_7fce9456 — does the offered property count as "viewed before the offer"?
Gold: 4 (excludes the Brookside townhouse itself). Grok: 5 (viewing dated
Feb 22, offer Feb 25 — literally "viewed before making an offer"). Both
readings defensible; gold's is the idiomatic one.

### 07741c45 — plan vs completed action (knowledge-update)
Gold: "in a shoe rack in my closet". Evidence: May 25 "storing them under the
bed"; May 29 "looking forward to" the shoe rack while organizing the closet
that weekend. Gold assumes the stated plan completed; the reader (both passes)
holds that a plan is not a location change. The benchmark's knowledge-update
convention evidently treats a dated intention as an update; that convention is
nowhere stated in the question. Defensible either way.

### gpt4_2f8be40d — wedding count window
Gold: 3 (Rachel+Mike, Emily+Sarah, Jen+Tom). Grok: 4, adding the user's
sister's wedding (maid of honor, past tense). Whether the sister's wedding
falls in "this year" is not pinned by a date in the packet; gold's exclusion
implies it does not. Unverifiable from the packet alone — boundary, possibly
a packet-coverage issue rather than gold or reader error.

### gpt4_4929293b — undated event vs dated event at "a week ago"
Gold: "my cousin's wedding". The wedding is stated "recently" (as of June 15)
but never dated; the niece's kindergarten graduation is pinned to June 10 with
the question asked June 22 — closer to "a week ago" than any dated event.
Gold is reachable only by treating "recently" as exactly one week. Boundary.

### 88432d0a — bake count window (flip row, p1 correct/p2 wrong)
Gold: 4. Grok both passes: 5 distinct completed bakes enumerated with
restatements merged. Without re-adjudicating each mention against the
two-week window this stays a boundary row; it is also judge-flip-prone
(scored differently across passes on near-identical enumerations).

---

## Class E — resolved historical candidates

- **9a707b81** ("how many days ago … baking class"): current passes answer
  21 days and are accepted (gold's own text allows 21 or 22). Off the list.
- **28dc39ac** ("hours playing games"): current passes compute 140 = gold.
  Off the list.

---

## Impact statement (conservative)

- Strict defects (A+B): **2 rows**, wrong in BOTH official passes.
  Under adjudicated gold the pair reads **478/476** instead of 476/474.
- Boundary rows (D): 6 rows where an alternative defensible gold exists
  (incl. 71017277, downgraded from strict after an independent-reader
  control); discussion items only, worth 0 in any headline.
- Judge-floor exhibits attached to this dossier: byte-identical-answer verdict
  flips (88432d0a_abs "0", judge-agreement matrix 98.2/97.8% GLM-vs-GPT-4o),
  and the Class-A control datum where fabrication scored above fidelity.

## Reproduction

Every claim above is checkable from committed artifacts:
- Packets: eval/dense_chain_v32_20260830/materialized.jsonl (regenerable via
  run_v34_full.sh prep inputs; concat files excluded from git deliberately)
- Official pair answers/verdicts: full-v34_pass{1,2}/{reader,judge_gpt4o}/
- Judge: scripts/rescore_gpt4o_judge.py, frozen paper rubric, ~$1.28/500 rows.
