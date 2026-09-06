# Rewrite log — correcting the `gpt4_731e37d7` misclassification

Date: 2026-09-05. Source of findings: `../DOSSIER_CLAIM_AUDIT.md` (65 claims,
7 contradicted) plus direct re-verification against the released bytes.
Zero model/provider/network calls. No git write commands.

Files edited (write scope, exactly three + this log):

1. `eval/dense_chain_v32_20260830/GOLD_DEFECT_DOSSIER.md`
2. `eval/dense_chain_v32_20260830/SOTA_WRITEUP.md`
3. `eval/dense_chain_v32_20260830/paper/longmemeval_auditable_memory_paper.md`

Untouched by design: the `.tex`, the `.pdf`, `ARXIV_SUBMISSION.md`, every other
worker's directory.

---

## 0. Facts re-verified before editing (not taken on trust)

All from the released packet and checkpoints, re-derived in this session:

| Fact | Source | Result |
|---|---|---|
| record identity | `packets_materialized/materialized_all.jsonl.gz`, `question_id == gpt4_731e37d7` | `content_sha256 = 5fb5690f4fc06ba5c819875ad3a37fbbf91bbff4f3a059e0c8b720446dc1cf06` (matches the audit) |
| `$500` occurrences | regex over the record's 16 session blobs | **9 total → 7 cost-filter boilerplate (session `answer_826d51da_4`, assistant turn) + 1 immigration L-1 fee (`sharegpt_Rwql31f_62`) + 1 user-stated workshop fee (`answer_826d51da_2`, `date: 2023/02/26 (Sun) 13:37`, user turn)** |
| user-stated fee text | same | "…I just attended a digital marketing workshop at the city convention center on March 15-16, and it was really helpful … **I paid $500 to attend**, and it was worth it!" |
| `March 15-16` mentions | same | **2**, both user turns: `answer_826d51da_3` @ `2023/02/26 (Sun) 11:52` and `answer_826d51da_2` @ `2023/02/26 (Sun) 13:37` |
| question date | `packets_materialized/facts_all.jsonl.gz` → `facts_text` | `2023/02/26 (Sun) 23:35` |
| reader answers | `*/reader/checkpoint_answerable.jsonl` | opus p1 `$720`, opus p2 `$720`, grok p1 `$220`, grok p2 `$220` (p2 text: "the **$500** is excluded") |
| judge verdicts (`llm_judge_correct`) | `*/judge_*/rescored.jsonl` | opus p1 True (gpt4o, gpt4o_v2, gpt4o_repro, glm53 all True), opus p2 True (gpt4o, glm53), grok p1 False, grok p2 False |
| `370a8ff4` | reader + judge | answered 11 weeks in all four passes; `llm_judge_correct = False` in all four |
| pass totals | `rescored.jsonl` row counts | opus p1 **479** (`judge_gpt4o_v2`), opus p2 **475**, grok p1 **476**, grok p2 **474** |
| ex-dossier | 8 dossier rows removed | opus 474/492 & 471/492; grok 475/492 & 474/492 — **unchanged by the reclassification** (same 8 rows, 1 strict + 7 boundary instead of 2 + 6) |

Conclusion: **no reader fabricated anything on this row.** Both readers saw the
user-stated `$500`. The only dispute is whether a March 15-16 workshop falls
inside a four-month window ending 2023/02/26. Class A ("evidence lacks a
required fact") therefore does not apply; Class D (boundary semantics) does.

---

## 1. Recomputed figures — the ONE adjudication scenario

**Scenario (single, stated identically everywhere):** adjudicate the one
surviving strict gold defect, `370a8ff4` (Class B — gold says 15 weeks between
two user-dated events 81 days = 11 weeks 4 days apart). `gpt4_731e37d7` is now
Class D and, per the dossier's own rule, boundary rows are worth 0 in any
headline — so it is *not* adjudicated in either direction and its as-scored
verdicts stand.

`370a8ff4` is scored 0 in all four passes, so adjudication adds exactly +1 per
pass:

```
grok pair (full-v34_pass{1,2}):        476 + 1 = 477 ;  474 + 1 = 475   →  477/475
Opus headline pair (full-v34-opus):    479 + 1 = 480 ;  475 + 1 = 476   →  480/476
```

The two pairs are labelled explicitly wherever the scenario is stated; they are
never merged into one number.

**What the three incompatible published statements were, and why each is gone:**

| Published | Where | Premise | Verdict |
|---|---|---|---|
| `478/476` | dossier:121, writeup:51 | 2 strict defects, grok pair (476+2 / 474+2) | arithmetic right, premise wrong → **477/475** |
| `478/474 (ex-fabrication) to 480/476 (restored)` | paper.md:244 | Opus's `$720` was a fabrication whose credit could be withdrawn | premise false (the `$500` is user-stated) → the ex-fabrication half is deleted; **480/476** is the one figure |
| `477/477` | paper.md:272 | the WITHDRAWN self-consistency pair 475/475 plus 2 strict defects | built on a withdrawn number *and* the wrong defect count → **477/475** (grok pair, 476+1 / 474+1) |

`480/476` is quoted twice in the paper (§5.1 body and §5.1's SC paragraph now
carries the grok pair's `477/475`); each occurrence names its pair.

---

## 2. GOLD_DEFECT_DOSSIER.md — edit by edit

### 2.1 Header — name the headline pair (new, lines 6–7)

The dossier's header names only the grok pair; every reader/judge claim in it
is scored against that pair, while the release headline is the Opus pair.

BEFORE (line 5, end of header block):
```
Pair result these rows are scored inside: 476/474 per 500 (475±1 vs Mastra 474).
```
AFTER:
```
Pair result these rows are scored inside: 476/474 per 500 (475±1 vs Mastra 474).
The release's headline pair is `full-v34-opus_pass{1,2}` (479/475); where the
two pairs differ on a row below, both verdicts are reported.
```

### 2.2 Class A body → pointer (was lines 24–44, now 26–30)

BEFORE:
```
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
```
AFTER:
```
## Class A — gold unreachable without fabrication

(none surviving review — gpt4_731e37d7 was moved to Class D on 2026-09-05
after a re-audit of the released packet found the $500 this dossier had said
was absent; see Class D and the Correction record below)
```
Matches the existing Class-C convention ("none surviving review — 71017277 was
downgraded…"), so the document's own voice is preserved.

### 2.3 New Class D entry (first in Class D, lines 52–88)

Written fresh; states the user-stated `$500` with session id and date, the
corrected 7/1/1 enumeration, *both* dated mentions, both readers' answers and
verdicts, and window membership as the real dispute. Full text is in the file;
the load-bearing corrections it carries:

- `$500` enumeration: **"Every occurrence is boilerplate or an immigration fee"**
  → **"of the 9 occurrences, 7 boilerplate + 1 immigration fee + 1 user-stated
  workshop fee"**.
- `"The only dated mention"` → **`"Both dated mentions"`** (2023/02/26 11:52 and
  13:37; the 13:37 turn is the one that also states the `$500`).
- The gemini control datum: `HALLUCINATED` → **"listed … It cited a real
  user-stated figure, so this is retrieval, not fabrication; its only defect is
  the same window question. The honest reading of the datum is narrower than
  this dossier first published: the judge rewards including an out-of-window
  item because gold includes it."**
- Both readers' verdicts stated explicitly (grok $220 → 0/0; Opus $720 →
  correct/correct).

### 2.4 Impact statement (lines 144–155)

BEFORE:
```
- Strict defects (A+B): **2 rows**, wrong in BOTH official passes.
  Under adjudicated gold the pair reads **478/476** instead of 476/474.
- Boundary rows (D): 6 rows where an alternative defensible gold exists
  (incl. 71017277, downgraded from strict after an independent-reader
  control); discussion items only, worth 0 in any headline.
- Judge-floor exhibits attached to this dossier: byte-identical-answer verdict
  flips (88432d0a_abs "0", judge-agreement matrix 98.2/97.8% GLM-vs-GPT-4o),
  and the Class-A control datum where fabrication scored above fidelity.
```
AFTER:
```
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
```

### 2.5 Reproduction — stale packet path (lines 160–162)

BEFORE:
```
- Packets: eval/dense_chain_v32_20260830/materialized.jsonl (regenerable via
  run_v34_full.sh prep inputs; concat files excluded from git deliberately)
```
AFTER:
```
- Packets: eval/dense_chain_v32_20260830/packets_materialized/materialized_all.jsonl.gz
  (500 rows, released; alongside facts_all.jsonl.gz and MANIFEST.md, and
  re-derivable byte-for-byte via scripts/materialize_packets.py)
```
The old parenthetical ("concat files excluded from git deliberately") was also
stale — the packets *are* released now (paper §8, `packets_materialized/MANIFEST.md`).

### 2.6 New "Correction record (2026-09-05)" section (end of file)

Four sentences, no self-congratulation, records the original claim, the packet
sha256 the re-audit ran against, the reclassification, and that the original
claim is kept rather than deleted.

---

## 3. SOTA_WRITEUP.md — edit by edit

### 3.1 Lines 50–51 → 50–53 (audit: C55, C56)

BEFORE:
```
- With the two strict gold defects adjudicated (see dossier), the raw pair
  reads 478/476. We report this as an adjudication scenario, not a score.
```
AFTER:
```
- With the one strict gold defect adjudicated (370a8ff4; see dossier), the
  grok pair reads 477/475 and the Opus pair 480/476 — +1 per pass, since that
  row is scored 0 in all four passes. We report this as an adjudication
  scenario, not a score.
```

### 3.2 Lines 132–140 → 134–152 (audit: C11, C12, C17b, C55)

BEFORE:
```
- **2 strict gold defects** — gold unreachable without fabrication ($720
  requiring a nonexistent $500 and an impossible date) and a gold
  arithmetic error (15 weeks vs a dated 81 days). A third candidate (a
  chandelier scored as "jewelry") was downgraded to boundary after an
  independent-reader control. Full evidence: GOLD_DEFECT_DOSSIER.md. A weaker
  reader that HALLUCINATED the missing $500 was scored correct — the judge
  rewards gold-matching over evidence fidelity; we did not take that trade.
- **~5 boundary-semantics rows** — both readings defensible (plan-vs-done,
  does-the-offered-house-count); documented, claimed as worth 0.
```
AFTER: a `**1 strict gold defect**` bullet naming the two downgrades, the
user-stated `$500` with session and date, the window question, and the
explicit reader split (grok $220 → 0/0; Opus $720 → correct/correct; gemini
probe likewise correct), closing "The judge scores window inclusion because
gold does; we report the split rather than claim either side." Boundary count
`~5` → `~6`.

Bucket arithmetic preserved: `2 + ~5` → `1 + ~6`; the section's stated total
(24 answerable rows) is unchanged.

**Beyond the audit:** the clause **"we did not take that trade"** was false as
published — the *headline* Opus pair takes exactly that trade on this row
(answers `$720`, scored correct in both passes). It is removed, not hedged.

---

## 4. paper/longmemeval_auditable_memory_paper.md — edit by edit

### 4.1 Abstract, line 28 (NOT in the audit's downstream list)

BEFORE: `attributes all remaining failures — including two strict gold-answer`
        `defects, an improvement stage rejected by our own negative control, and`
AFTER:  `attributes all remaining failures — including a strict gold-answer`
        `defect, an improvement stage rejected by our own negative control, and`

### 4.2 §5.1, lines 239–245 (audit: C11/C17b, C56)

BEFORE:
```
text, §8 — so even "one above" is a judge roll). The two gold-defect rows from the
dossier (§6.3) sit inside this pair as well: one is scored correct via
the fabrication the dossier documents (the reader supplies the $500 no
session contains), one is lost to fidelity (the evidence-faithful answer
contradicts defective gold) — net zero per pass. Under adjudication the
pair reads 478/474 (ex-fabrication) to 480/476 (restored); the tie with
the published state of the art holds in every stance.
```
AFTER:
```
text, §8 — so even "one above" is a judge roll). The two rows §6.3
documents individually — the $720 workshop row and the 15-weeks row — sit
inside this pair as well: one is scored correct because this reader counts a
user-stated $500 fee whose event is dated outside the question's four-month
window (a boundary row, not a fabrication — §6.3), one is lost to fidelity
(the evidence-faithful answer contradicts defective gold) — net zero per pass. Adjudicating the single
strict defect raises the Opus pair to 480/476 (479+1 / 475+1); the tie with
the published state of the art holds in every stance.
```
"net zero per pass" survives because it is still arithmetically true for this
pair (one row +1, one row −1); only its *reason* changed.

### 4.3 §5.1, line 264 — mislabelled pair (NOT in the audit's list)

BEFORE: `Headline-pair detail: answerable 450/470 and 447/470; abstention`
AFTER:  `Raw grok-pair detail (the pair the self-consistency rule was frozen over):`
        `answerable 450/470 and 447/470; abstention`

Reason: `450 + 26 = 476` and `447 + 27 = 474` — those splits are the **grok**
pair's, and the paragraph continues into the SC rule, which §4.4 states was
frozen over "the raw v3.4 pair measured 476/474". The Opus pair's own splits
are `452/470 + 27/30 = 479` and `450/470 + 25/30 = 475`. §5.1 line 228 says
"The Opus pair is the headline", so the label was a stale carry-over from the
grok-pair version of the document and contradicted the paper's own §5.1.1
table. Required by the brief's instruction to label each pair explicitly.

### 4.4 §5.1, line 272 (audit: C56)

BEFORE: `the gold-defect adjudication scenario (§6.3) the pair reads 477/477; we`
AFTER:  `the gold-defect adjudication scenario (§6.3) that grok pair reads 477/475`
        `(476+1 / 474+1, the single strict defect); we`

### 4.5 §6 partition, line 366 (audit: C55)

BEFORE: `The partition: 4 reader-cognition + 8 gold-defect (2 strict, 6`
AFTER:  `The partition: 4 reader-cognition + 8 gold-defect (1 strict, 7`

Total stays 8 gold-defect rows and 24 overall; only the strict/boundary split
moves.

### 4.6 §6.3 heading + bullets, lines 388–403 (audit: C11, C12, C17b, C55)

Heading `(2 strict, 6 boundary)` → `(1 strict, 7 boundary)`.

The `**Strict A**` bullet is deleted and replaced by a `**Boundary — the $720
workshop row**` bullet stating: gold's `$500` is user-stated (`answer_826d51da_2`,
2023/02/26 13:37, "I paid $500 to attend"); nothing has to be invented; the
dispute is window membership (both dated mentions say March 15-16, after the
2023/02/26 question date); grok excludes → $220 → 0/0; Opus includes → $720 →
correct/correct; the gemini probe likewise; and the closing correction —
**"the disclosed window-inclusion point inside 479/475 (§5.1), not a
fabrication point"** (was: "the disclosed fabrication point inside 479/475").
`Strict B` is moved first and gains "Wrong in all four passes of both reader
configurations" (verified). The trailing "Six further rows are
boundary-semantic" is correct as written: 6 summarised + the $720 row itemised
= the 7 boundary rows.

### 4.7 §7 Limitations — new final bullet (correction provenance)

Four sentences: what the dossier originally claimed, that a mechanical
re-audit of the release's own published packets found the fee, what changed
(boundary row, strict count 1 not 2, §5.1 figures recomputed), and that no
verdict changed so the headline 479/475 is unaffected — plus that the error is
recorded in the dossier rather than removed.

---

## 5. Headline integrity

`479/475` was not touched anywhere. Post-edit occurrences (all pre-existing):

```
SOTA_WRITEUP.md:1  # LongMemEval-S: 479/475 per 500 under the official GPT-4o judge
SOTA_WRITEUP.md:12 **v3.4 chain, Claude Opus reader: 479/500 and 475/500 (477 ± 2) across two
SOTA_WRITEUP.md:33 | **This chain (v3.4, Opus reader)** | **479 / 475** | two independent passes, …
paper.md:1   # Auditable Long-Term Memory: A Deterministic Retrieval Chain Scoring 479/475 of 500 …
paper.md:10  We report **479/500 and 475/500 across two independent full passes on
paper.md:289 | **Total** | **500** | **476** | **474** | 461 / 465 | **479 / 475** |
```
Plus two new *references* to it (dossier:6 naming the headline pair;
paper §7 stating the headline is unaffected) — neither changes the number.
The §5.1.1 per-type table, the §5.2 ladder, the ex-dossier rows
(474/492, 471/492, 475/492, 474/492) and the Wilson intervals are untouched
and re-verified as still correct under the new classification.

---

## 6. Operator decisions (NOT guessed; text left as published)

1. **Class D vs Class E for `gpt4_731e37d7`.** The audit notes Class E
   ("resolved — current chain matches gold") also fits literally, since the
   headline Opus pair matches gold in both passes. The brief directed D, and D
   is used. If the author prefers E, the dossier entry, the §6.3 bullet, the
   boundary counts (7 → 6) and the §6 partition would all need a second pass.
   **Decision: keep D, or move to E?**

2. **`.tex` / `.pdf` / `ARXIV_SUBMISSION.md` still carry the old claims.**
   Out of this write scope by instruction. `.tex` lines 215–220, 241, 349,
   352, 355–356 and `ARXIV_SUBMISSION.md:18` repeat C11/C17b/C55/C56 verbatim,
   and the compiled PDF embeds them. Until that port runs, the release is
   internally inconsistent between the `.md` and the `.tex`/`.pdf`.
   **Decision: who runs the tex/pdf port, and is the PDF re-rendered before
   any further distribution?**

3. **`C3` and `C64` remain untestable in-release.** Chain commit `04eb64763`
   is not an object in this repository (dossier:4, writeup:5), and the
   `~$1.28/500 rows` figure (dossier:162, writeup:74/163, paper §8) has no
   released cost receipt. Both are asserted, not falsifiable from the release.
   Neither is a contradicted claim, so nothing was changed.
   **Decision: pin the source commit / attach a cost receipt, or mark both as
   unverifiable-from-this-release?**

4. **Dossier header still reads `Date: 2026-08-31`** while the file now carries
   a 2026-09-05 correction record. Left as published to preserve provenance of
   the original document.
   **Decision: keep the original date with the dated correction record (current
   state), or restate as "2026-08-31, corrected 2026-09-05"?**
