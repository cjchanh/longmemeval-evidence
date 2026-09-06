# Dossier claim audit — GOLD_DEFECT_DOSSIER.md

Mechanical, deterministic, read-only. No model, provider, or network calls.
Regenerate: `python3 audit_claims.py`. Input hashes: `HASHES.json`.

## Bottom line

**65 falsifiable claims enumerated — 51 CONFIRMED, 7 CONTRADICTED, 2 UNTESTABLE, 5 interpretive (recorded, not scored).**

- **`gpt4_731e37d7` changes class: A → D (or E).** The dossier's load-bearing negative — "No $500 attached to any workshop exists anywhere in the evidence" — is false against the release's own published packet. The record contains a user turn reading *"I just attended a digital marketing workshop at the city convention center on March 15-16 … **I paid $500 to attend**, and it was worth it!"* (session `2023/02/26 (Sun) 13:37`, `user:` turn, one occurrence).
- Class A is defined in this dossier as *gold unreachable without fabrication (evidence lacks a required fact)*. The fact is present, so A does not apply. The surviving dispute is whether a workshop the source dates **March 15-16** falls inside a four-month window ending **2023/02/26** — that is Class D, *boundary semantics (both readings defensible)*. Applied literally, **Class E** (*resolved — current chain matches gold*) also fits: the release's headline Opus pair answers $720 and is scored **correct in both passes**.
- **`370a8ff4` keeps Class B unchanged.** Every arithmetic and packet claim on that row is confirmed byte-for-byte: one flu-recovery date (2023/01/19, user turn), one 10th-jog date (2023/04/10, user turn), 81 days = 11 weeks 4 days, 15 weeks would land on 2023-05-04.
- **Impact statement moves with it**: strict defects 2 → **1**; adjudicated pair 478/476 → **477/475**; boundary rows 6 → **7** if `gpt4_731e37d7` is re-classed D.
- Everything else holds. All six Class-D rows, both Class-E rows, the 476/474 pair result, the judge identity, the judge-agreement matrix, and the 88432d0a_abs exhibit check out against the bytes.
- One stale path: the Reproduction section points at `eval/dense_chain_v32_20260830/materialized.jsonl`, which does not exist in the release.

### Rows whose class changes

| qid | published class | audited class | driver |
|---|---|---|---|
| `gpt4_731e37d7` | A — gold unreachable without fabrication | **D — boundary semantics** (or **E — resolved**, since the headline Opus pair matches gold in both passes) | C11, C12, C17b |
| `370a8ff4` | B — gold arithmetic error | **B (unchanged)** | — |
| all six Class-D rows | D | **D (unchanged)** | — |
| `9a707b81`, `28dc39ac` | E | **E (unchanged)** | — |

Class definitions, quoted verbatim from the dossier and applied literally:

> - **A — gold unreachable without fabrication** (evidence lacks a required fact)
> - **B — gold arithmetic error**
> - **C — gold category error**
> - **D — boundary semantics** (both readings defensible; not claimed)
> - **E — resolved** (historical candidate; current chain matches gold)

## Reader-lane note (applies to every READER and JUDGE claim)

The dossier's header names `cursor-grok-4.6-high` and its Reproduction section names `full-v34_pass{1,2}` as "the official pair". That is the pair every READER/JUDGE claim below is scored against, and the 476/474 figure matches it exactly. It is **not** the release's headline pair: `packets_materialized/MANIFEST.md` calls `full-v34-opus_pass{1,2}` "both headline Opus passes". Where the two pairs disagree — most sharply on `gpt4_731e37d7` — both are reported.

## Claim table

| id | qid | type | status | claim |
|---|---|---|---|---|
| C1 | — | JUDGE | CONFIRMED | Judge: gpt-4o-2024-08-06 (paper rubric, api transport) |
| C2 | — | READER | CONFIRMED | Reader: cursor-grok-4.6-high |
| C3 | — | READER | UNTESTABLE | Chain: v3.4 (commit 04eb64763) |
| C4 | — | ARITHMETIC | CONFIRMED | Pair result these rows are scored inside: 476/474 per 500 |
| C5 | `gpt4_731e37d7` | PACKET_POSITIVE | CONFIRMED | gpt4_731e37d7 (multi-session) |
| C6 | `gpt4_731e37d7` | PACKET_POSITIVE | CONFIRMED | Q: "How much total money did I spend on attending workshops in the last four months?" |
| C7 | `gpt4_731e37d7` | PACKET_POSITIVE | CONFIRMED | Gold: **$720** |
| C8 | `gpt4_731e37d7` | ARITHMETIC | CONFIRMED | (= $200 + $20 + $500) |
| C9 | `gpt4_731e37d7` | PACKET_POSITIVE | CONFIRMED | $200 writing workshop (November) — user-stated, in window. |
| C10 | `gpt4_731e37d7` | PACKET_POSITIVE | CONFIRMED | $20 mindfulness workshop (Dec 12) — user-stated, in window. |
| C11 | `gpt4_731e37d7` | PACKET_NEGATIVE | **CONTRADICTED** | **No $500 attached to any workshop exists anywhere in the evidence.** |
| C12 | `gpt4_731e37d7` | PACKET_NEGATIVE | **CONTRADICTED** | Every "$500" occurrence is website cost-filter boilerplate ("under $100, $100-$500…") or an immigration-form fee in an unrelated session. |
| C13 | `gpt4_731e37d7` | PACKET_POSITIVE | **CONTRADICTED** | The only dated mention of the digital-marketing workshop is internally impossible: a session dated **2023/02/26** says "I just attended a digital m… |
| C14 | `gpt4_731e37d7` | ARITHMETIC | CONFIRMED | a past-tense attendance of a future date |
| C15 | `gpt4_731e37d7` | INTERPRETIVE | not scored | Evidence-faithful answer: $220. |
| C16 | `gpt4_731e37d7` | READER | CONFIRMED | Both official passes answered $220 → scored 0. |
| C17a | `gpt4_731e37d7` | READER | CONFIRMED | a weaker reader (gemini-3.7-flash probe) ... "$500 Digital Marketing Workshop (Recent)", summed $720, and was scored CORRECT |
| C17b | `gpt4_731e37d7` | PACKET_NEGATIVE | **CONTRADICTED** | HALLUCINATED a "$500 Digital Marketing Workshop (Recent)" |
| C18 | `gpt4_731e37d7` | INTERPRETIVE | not scored | Packet facts (exhaustive dollar-amount inventory performed) |
| C19 | `gpt4_731e37d7` | INTERPRETIVE | not scored | VERIFIED IN FULL |
| C20 | `370a8ff4` | PACKET_POSITIVE | CONFIRMED | 370a8ff4 (temporal-reasoning) |
| C21 | `370a8ff4` | PACKET_POSITIVE | CONFIRMED | Q: "How many weeks had passed since I recovered from the flu when I went on my 10th jog outdoors?" |
| C22 | `370a8ff4` | PACKET_POSITIVE | CONFIRMED | Gold: **15** |
| C23 | `370a8ff4` | PACKET_POSITIVE | CONFIRMED | recovered 2023/01/19 ("today") |
| C24 | `370a8ff4` | PACKET_POSITIVE | CONFIRMED | 10th outdoor jog 2023/04/10 ("today") |
| C25 | `370a8ff4` | READER | CONFIRMED | Packet dates (user-stated, both passes agree) |
| C26 | `370a8ff4` | ARITHMETIC | CONFIRMED | Elapsed: 81 days = **11 weeks 4 days** |
| C27 | `370a8ff4` | ARITHMETIC | CONFIRMED | 15 weeks = 105 days would place the jog on May 4 |
| C28 | `370a8ff4` | READER | CONFIRMED | Evidence-faithful answer: 11. Both passes: 11 → 0. |
| C29 | `370a8ff4` | ARITHMETIC | CONFIRMED | No reading of the two dated statements yields 15 weeks |
| C30 | — | INTERPRETIVE | not scored | (none surviving review — 71017277 was downgraded to Class D ...) |
| C31 | `71017277` | PACKET_POSITIVE | CONFIRMED | Q: "I received a piece of jewelry last Saturday from whom?" Gold: my aunt. |
| C32 | `71017277` | PACKET_POSITIVE | CONFIRMED | the aunt gave a **crystal chandelier** that Saturday |
| C33 | `71017277` | PACKET_NEGATIVE | CONFIRMED | no jewelry gift or giver exists in the sessions |
| C34 | `71017277` | READER | CONFIRMED | Grok (both passes) refused the false premise ("aunt gave a chandelier, not jewelry") → 0 |
| C35 | `71017277` | READER | CONFIRMED | The Sol reader answered ... with "your aunt" and was scored correct |
| C36 | `gpt4_7fce9456` | PACKET_POSITIVE | CONFIRMED | Gold: 4 (excludes the Brookside townhouse itself) |
| C37 | `gpt4_7fce9456` | READER | CONFIRMED | Grok: 5 |
| C38 | `gpt4_7fce9456` | PACKET_POSITIVE | CONFIRMED | viewing dated Feb 22, offer Feb 25 |
| C39 | `07741c45` | PACKET_POSITIVE | CONFIRMED | 07741c45 — plan vs completed action (knowledge-update) |
| C40 | `07741c45` | PACKET_POSITIVE | CONFIRMED | Gold: "in a shoe rack in my closet" |
| C41 | `07741c45` | PACKET_POSITIVE | CONFIRMED | Evidence: May 25 "storing them under the bed" |
| C42 | `07741c45` | PACKET_POSITIVE | CONFIRMED | May 29 "looking forward to" the shoe rack while organizing the closet that weekend |
| C43 | `07741c45` | READER | CONFIRMED | the reader (both passes) holds that a plan is not a location change |
| C44 | `gpt4_2f8be40d` | PACKET_POSITIVE | CONFIRMED | Gold: 3 (Rachel+Mike, Emily+Sarah, Jen+Tom) |
| C45 | `gpt4_2f8be40d` | READER | CONFIRMED | Grok: 4, adding the user's sister's wedding (maid of honor, past tense) |
| C46 | `gpt4_2f8be40d` | PACKET_NEGATIVE | CONFIRMED | Whether the sister's wedding falls in "this year" is not pinned by a date in the packet |
| C47 | `gpt4_4929293b` | PACKET_POSITIVE | CONFIRMED | Gold: "my cousin's wedding" |
| C48 | `gpt4_4929293b` | PACKET_NEGATIVE | CONFIRMED | The wedding is stated "recently" (as of June 15) but never dated |
| C49 | `gpt4_4929293b` | PACKET_POSITIVE | CONFIRMED | the niece's kindergarten graduation is pinned to June 10 with the question asked June 22 |
| C50 | `88432d0a` | PACKET_POSITIVE | CONFIRMED | Gold: 4 |
| C51 | `88432d0a` | READER | CONFIRMED | Grok both passes: 5 distinct completed bakes enumerated with restatements merged |
| C52 | `88432d0a` | JUDGE | CONFIRMED | (flip row, p1 correct/p2 wrong) |
| C53 | `9a707b81` | READER | CONFIRMED | current passes answer 21 days and are accepted (gold's own text allows 21 or 22) |
| C54 | `28dc39ac` | READER | CONFIRMED | current passes compute 140 = gold |
| C55 | — | JUDGE | **CONTRADICTED** | Strict defects (A+B): **2 rows**, wrong in BOTH official passes. |
| C56 | — | ARITHMETIC | **CONTRADICTED** | Under adjudicated gold the pair reads **478/476** instead of 476/474. |
| C57 | — | ARITHMETIC | CONFIRMED | Boundary rows (D): 6 rows |
| C58 | `88432d0a_abs` | JUDGE | CONFIRMED | byte-identical-answer verdict flips (88432d0a_abs "0") |
| C59 | — | JUDGE | CONFIRMED | judge-agreement matrix 98.2/97.8% GLM-vs-GPT-4o |
| C60 | — | INTERPRETIVE | not scored | the Class-A control datum where fabrication scored above fidelity |
| C61 | — | PACKET_POSITIVE | **CONTRADICTED** | Packets: eval/dense_chain_v32_20260830/materialized.jsonl |
| C62 | — | PACKET_POSITIVE | CONFIRMED | Official pair answers/verdicts: full-v34_pass{1,2}/{reader,judge_gpt4o}/ |
| C63 | — | PACKET_POSITIVE | CONFIRMED | Judge: scripts/rescore_gpt4o_judge.py, frozen paper rubric |
| C64 | — | ARITHMETIC | UNTESTABLE | ~$1.28/500 rows |

## Contradicted claims — evidence and minimal correction

### C11 — `gpt4_731e37d7`

**Claim (verbatim):** **No $500 attached to any workshop exists anywhere in the evidence.**

**Type:** PACKET_NEGATIVE

**Evidence:**

```json
{
 "total_$500_occurrences": 9,
 "paid_500_to_attend_occurrences": 1,
 "hits": [
  {
   "session_index": 8,
   "session_id": "answer_826d51da_2",
   "session_date": "date: 2023/02/26 (Sun) 13:37",
   "role": "user:",
   "offset": 363,
   "match": "I paid $500 to attend",
   "context": "erstanding the importance of tracking my online engagement. I paid $500 to attend, and it was worth it! | assistant: That's great to hear that "
  }
 ],
 "record_content_sha256": "5fb5690f4fc06ba5c819875ad3a37fbbf91bbff4f3a059e0c8b720446dc1cf06"
}
```

**Minimal correction:** Delete the sentence. The packet contains one user-stated workshop fee: session date: 2023/02/26 (Sun) 13:37, user turn — "I just attended a digital marketing workshop at the city convention center on March 15-16 ... I paid $500 to attend, and it was worth it!". The dispute is window membership, not existence.

**Class change:** A -> D (or E); Class A requires 'evidence lacks a required fact' and the fact is present

### C12 — `gpt4_731e37d7`

**Claim (verbatim):** Every "$500" occurrence is website cost-filter boilerplate ("under $100, $100-$500…") or an immigration-form fee in an unrelated session.

**Type:** PACKET_NEGATIVE

**Evidence:**

```json
{
 "total": 9,
 "cost_filter_boilerplate": 7,
 "immigration_form_fee": 1,
 "user_stated_workshop_fee": 1,
 "unclassified_by_dossier": [
  "erstanding the importance of tracking my online engagement. I paid $500 to attend, and it was worth it! | assistant: That's great to hear that "
 ]
}
```

**Minimal correction:** Replace with: of 9 '$500' occurrences, 7 are cost-filter boilerplate, 1 is an immigration-form fee, and 1 is the user-stated digital-marketing workshop fee.

### C13 — `gpt4_731e37d7`

**Claim (verbatim):** The only dated mention of the digital-marketing workshop is internally impossible: a session dated **2023/02/26** says "I just attended a digital marketing workshop … **on March 15-16**"

**Type:** PACKET_POSITIVE

**Evidence:**

```json
{
 "n_dated_mentions": 2,
 "mentions": [
  {
   "session_date": "date: 2023/02/26 (Sun) 11:52",
   "role": "user:",
   "context": "st photography. For instance, I recently attended a two-day digital marketing workshop at the city convention center on March 15-16. | assistant: That's great to hear that you're interested in "
  },
  {
   "session_date": "date: 2023/02/26 (Sun) 13:37",
   "role": "user:",
   "context": "s for social media analytics. By the way, I just attended a digital marketing workshop at the city convention center on March 15-16, and it was really helpful in understanding the importance "
  }
 ]
}
```

**Minimal correction:** 'The only dated mention' -> 'Both dated mentions'. Two user turns carry the March 15-16 date (sessions 2023/02/26 11:52 and 2023/02/26 13:37); the second is the one that also states the $500.

### C17b — `gpt4_731e37d7`

**Claim (verbatim):** HALLUCINATED a "$500 Digital Marketing Workshop (Recent)"

**Type:** PACKET_NEGATIVE

**Evidence:**

```json
{
 "why": "the $500 digital-marketing workshop fee is user-stated in the packet (see C11); citing it is retrieval, not fabrication. The gemini row's only defect is window membership."
}
```

**Minimal correction:** Drop 'HALLUCINATED'. The control datum shows two readers differing on whether the March 15-16 workshop is inside a four-month window ending 2023/02/26 — not fabrication vs fidelity.

### C55 — dossier-wide

**Claim (verbatim):** Strict defects (A+B): **2 rows**, wrong in BOTH official passes.

**Type:** JUDGE

**Evidence:**

```json
{
 "official_pair_verdicts": {
  "gpt4_731e37d7": [
   false,
   false
  ],
  "370a8ff4": [
   false,
   false
  ]
 },
 "both_wrong_in_official_pair": true,
 "why_contradicted": "the 'wrong in both passes' half is CONFIRMED for the grok pair, but the 'strict defects (A+B): 2 rows' half fails: gpt4_731e37d7 is not Class A (C11/C12), so only 1 strict defect survives.",
 "headline_pair_verdicts": {
  "gpt4_731e37d7": [
   true,
   true
  ],
  "370a8ff4": [
   false,
   false
  ]
 }
}
```

**Minimal correction:** 'Strict defects (B): 1 row, wrong in both official passes.'

### C56 — dossier-wide

**Claim (verbatim):** Under adjudicated gold the pair reads **478/476** instead of 476/474.

**Type:** ARITHMETIC

**Evidence:**

```json
{
 "arithmetic_given_2_defects": [
  478,
  476
 ],
 "arithmetic_given_1_defect": [
  477,
  475
 ],
 "why": "the arithmetic is right; the premise (2 strict defects) is not"
}
```

**Minimal correction:** 'Under adjudicated gold the pair reads 477/475 instead of 476/474.'

### C61 — dossier-wide

**Claim (verbatim):** Packets: eval/dense_chain_v32_20260830/materialized.jsonl

**Type:** PACKET_POSITIVE

**Evidence:**

```json
{
 "path_exists": false,
 "released_packets": "eval/dense_chain_v32_20260830/packets_materialized/materialized_all.jsonl.gz (500 rows)"
}
```

**Minimal correction:** Point at packets_materialized/materialized_all.jsonl.gz (+ facts_all.jsonl.gz, MANIFEST.md).

## Untestable

- **C3** — Chain: v3.4 (commit 04eb64763) — commit 04eb64763 is not an object in this release repository (git cat-file -t -> 'Not a valid object name'); it refers to a source repo not published here
- **C64** — ~$1.28/500 rows — no cost receipt is released; the figure is asserted identically in SOTA_WRITEUP.md:72,162 and the paper:31,98,468 but no artifact records token counts or billed spend

## Interpretive (recorded, not scored)

- **C15** — Evidence-faithful answer: $220.
- **C18** — Packet facts (exhaustive dollar-amount inventory performed)
- **C19** — VERIFIED IN FULL
- **C30** — (none surviving review — 71017277 was downgraded to Class D ...)
- **C60** — the Class-A control datum where fabrication scored above fidelity

## Downstream repetition of contradicted claims

| claim | file | line | text |
|---|---|---|---|
| C55 | `SOTA_WRITEUP.md` | 50 | - With the two strict gold defects adjudicated (see dossier), the raw pair |
| C56 | `SOTA_WRITEUP.md` | 51 | reads 478/476. We report this as an adjudication scenario, not a score. |
| C11/C17b | `SOTA_WRITEUP.md` | 132 | - **2 strict gold defects** — gold unreachable without fabrication ($720 |
| C55 | `SOTA_WRITEUP.md` | 132 | - **2 strict gold defects** — gold unreachable without fabrication ($720 |
| C11/C12 | `SOTA_WRITEUP.md` | 133 | requiring a nonexistent $500 and an impossible date) and a gold |
| C11/C12 | `SOTA_WRITEUP.md` | 137 | reader that HALLUCINATED the missing $500 was scored correct — the judge |
| C17b | `SOTA_WRITEUP.md` | 137 | reader that HALLUCINATED the missing $500 was scored correct — the judge |
| C55 | `paper/longmemeval_auditable_memory_paper.md` | 239 | text, §8 — so even "one above" is a judge roll). The two gold-defect rows from the |
| C11/C12 | `paper/longmemeval_auditable_memory_paper.md` | 241 | the fabrication the dossier documents (the reader supplies the $500 no |
| C11/C17b | `paper/longmemeval_auditable_memory_paper.md` | 241 | the fabrication the dossier documents (the reader supplies the $500 no |
| C11/C17b | `paper/longmemeval_auditable_memory_paper.md` | 244 | pair reads 478/474 (ex-fabrication) to 480/476 (restored); the tie with |
| C56 | `paper/longmemeval_auditable_memory_paper.md` | 244 | pair reads 478/474 (ex-fabrication) to 480/476 (restored); the tie with |
| C56 | `paper/longmemeval_auditable_memory_paper.md` | 272 | the gold-defect adjudication scenario (§6.3) the pair reads 477/477; we |
| C55 | `paper/longmemeval_auditable_memory_paper.md` | 366 | The partition: 4 reader-cognition + 8 gold-defect (2 strict, 6 |
| C55 | `paper/longmemeval_auditable_memory_paper.md` | 388 | ### 6.3 Gold-answer defects (2 strict, 6 boundary) |
| C11/C12 | `paper/longmemeval_auditable_memory_paper.md` | 390 | - **Strict A** — gold requires a $500 expense that appears nowhere in the |
| C11/C12 | `paper/longmemeval_auditable_memory_paper.md` | 392 | past tense. A weaker reader that *hallucinated* the missing $500 was |
| C17b | `paper/longmemeval_auditable_memory_paper.md` | 392 | past tense. A weaker reader that *hallucinated* the missing $500 was |
| C11/C17b | `paper/longmemeval_auditable_memory_paper.md` | 397 | fabrication point inside 479/475 (§5.1). |
| C55 | `paper/longmemeval_auditable_memory_paper.tex` | 215 | ``one above'' is a judge roll). The two gold-defect rows from the dossier (\S6.3) sit inside this |
| C11/C17b | `paper/longmemeval_auditable_memory_paper.tex` | 216 | pair as well: one is scored correct via the fabrication the dossier |
| C11/C12 | `paper/longmemeval_auditable_memory_paper.tex` | 217 | documents (the reader supplies the \$500 no session contains), one is lost |
| C56 | `paper/longmemeval_auditable_memory_paper.tex` | 219 | net zero per pass. Under adjudication the pair reads 478/474 |
| C11/C17b | `paper/longmemeval_auditable_memory_paper.tex` | 220 | (ex-fabrication) to 480/476 (restored); the tie with the published state |
| C56 | `paper/longmemeval_auditable_memory_paper.tex` | 220 | (ex-fabrication) to 480/476 (restored); the tie with the published state |
| C56 | `paper/longmemeval_auditable_memory_paper.tex` | 241 | adjudication scenario (\S6.3) the prior pair reads 478/476; we report that as a |
| C55 | `paper/longmemeval_auditable_memory_paper.tex` | 349 | \textbf{6.3 Gold-answer defects (2 strict, 6 boundary).} Documented row-by-row |
| C11/C12 | `paper/longmemeval_auditable_memory_paper.tex` | 352 | in the past tense; a weaker reader that \emph{hallucinated} the missing \$500 |
| C17b | `paper/longmemeval_auditable_memory_paper.tex` | 352 | in the past tense; a weaker reader that \emph{hallucinated} the missing \$500 |
| C11/C12 | `paper/longmemeval_auditable_memory_paper.tex` | 355 | contrast, supplies the \$500 and is scored correct on both passes --- the |
| C11/C17b | `paper/longmemeval_auditable_memory_paper.tex` | 356 | disclosed fabrication point inside 479/475 (\S5.1). Strict B: gold says ``15 weeks'' |
| C55 | `paper/ARXIV_SUBMISSION.md` | 18 | We report 479/500 and 475/500 across two independent full passes on LongMemEval-S (Claude Opus reader; CLI alias resolving to claude-opus-5, §5.3) under the benchmark's official GPT-4o judge |

