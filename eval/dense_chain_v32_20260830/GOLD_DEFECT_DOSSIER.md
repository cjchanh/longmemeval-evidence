# Gold-Defect Dossier — LongMemEval-S dense-chain campaign

Date: 2026-08-31 · Judge: gpt-4o-2024-08-06 (paper rubric, api transport)
Reader: cursor-grok-4.6-high · Chain: v3.4 (commit 04eb64763)
Pair result these rows are scored inside: 476/474 per 500 (475±1 vs Mastra 474).
The release's headline pair is `full-v34-opus_pass{1,2}` (479/475); where the
two pairs differ on a row below, both verdicts are reported.

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

(none surviving review — gpt4_731e37d7 was moved to Class D on 2026-09-05
after a re-audit of the released packet found the $500 this dossier had said
was absent; see Class D and the Correction record below)

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

### gpt4_731e37d7 — is a March 15-16 workshop inside a four-month window ending Feb 26? (downgraded from A)
Q: "How much total money did I spend on attending workshops in the last four months?"
Gold: **$720** (= $200 + $20 + $500). Question date: 2023/02/26 (Sun) 23:35.

Packet facts (exhaustive dollar-amount inventory, re-verified against the
released packet record, content_sha256 `5fb5690f…1cf06`):
- $200 writing workshop (November) — user-stated, in window.
- $20 mindfulness workshop (Dec 12) — user-stated, in window.
- **$500 digital-marketing workshop — user-stated, in the packet.** Session
  `answer_826d51da_2`, date 2023/02/26 (Sun) 13:37, user turn: "I just
  attended a digital marketing workshop at the city convention center on
  March 15-16, and it was really helpful … **I paid $500 to attend**, and it
  was worth it!" Of the 9 "$500" occurrences in the record, **7** are website
  cost-filter boilerplate ("under $100, $100-$500…"), **1** is an
  immigration-form fee in an unrelated session, and **1** is this user-stated
  workshop fee.
- **Both** dated mentions of the digital-marketing workshop carry the same
  impossible date: user turns in sessions dated 2023/02/26 (Sun) 11:52 and
  2023/02/26 (Sun) 13:37 each place it "on March 15-16" — a past-tense
  attendance of a date after the question date. The 13:37 turn is the one
  that also states the $500.

Nothing has to be invented to reach gold; the dispute is window membership.
The two released readers split on it, and both stances are defensible:
- **grok-4.6-high (official pair)** excluded the fee as out-of-window — pass 2
  states it outright ("the **$500** is excluded") — answered **$220**, scored
  **0 in both passes**.
- **Claude Opus (headline pair)** counted it as recently attended, answered
  **$720**, scored **correct in both passes** (all three judge directories on
  pass 1 agree, as does GLM-5.3 on both passes).

Control datum: a weaker reader (gemini-3.7-flash probe) listed "$500 Digital
Marketing Workshop (Recent)", summed $720, and was scored CORRECT. It cited a
real user-stated figure, so this is retrieval, not fabrication; its only
defect is the same window question. The honest reading of the datum is
narrower than this dossier first published: the judge rewards **including an
out-of-window item** because gold includes it.

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

- Strict defects (B): **1 row** (370a8ff4), wrong in BOTH official passes —
  and in both headline Opus passes. Adjudicating it adds +1 to every pass:
  the official grok pair reads **477/475** instead of 476/474 (476+1 / 474+1),
  and the headline Opus pair reads **480/476** instead of 479/475 (479+1 /
  475+1). Reported as an adjudication scenario, never as a score.
- Boundary rows (D): 7 rows where an alternative defensible gold exists
  (incl. 71017277, downgraded from strict after an independent-reader
  control, and gpt4_731e37d7, downgraded from strict after the packet
  re-audit below); discussion items only, worth 0 in any headline.
- Judge-floor exhibits attached to this dossier: byte-identical-answer verdict
  flips (88432d0a_abs "0", judge-agreement matrix 98.2/97.8% GLM-vs-GPT-4o),
  and the gpt4_731e37d7 control datum where the judge rewarded including an
  out-of-window item because gold includes it.

## Reproduction

Every claim above is checkable from committed artifacts:
- Packets: eval/dense_chain_v32_20260830/packets_materialized/materialized_all.jsonl.gz
  (500 rows, released; alongside facts_all.jsonl.gz and MANIFEST.md, and
  re-derivable byte-for-byte via scripts/materialize_packets.py)
- Official pair answers/verdicts: full-v34_pass{1,2}/{reader,judge_gpt4o}/
- Judge: scripts/rescore_gpt4o_judge.py, frozen paper rubric, ~$1.28/500 rows.

## Correction record (2026-09-05)

The gpt4_731e37d7 entry above was originally published in Class A on the
claim that no $500 workshop fee existed anywhere in the evidence. A
mechanical re-audit of this release's own published packet
(`packets_materialized/materialized_all.jsonl.gz`, record content_sha256
`5fb5690f4fc06ba5c819875ad3a37fbbf91bbff4f3a059e0c8b720446dc1cf06`) found
that fee stated by the user in session `answer_826d51da_2`, which makes the
Class-A definition inapplicable and the "hallucination" reading of the
control datum wrong. The row was reclassified to D, the strict-defect count
dropped from 2 to 1, and the adjudication figures were recomputed above. The
original claim and the contradiction are recorded here rather than removed.
