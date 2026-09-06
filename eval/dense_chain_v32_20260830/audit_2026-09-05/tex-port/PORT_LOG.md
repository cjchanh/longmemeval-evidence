# TeX port log — `.md` → `.tex` (2026-09-06)

Ports the 2026-09-05 `gpt4_731e37d7` reclassification (`../rewrite/REWRITE_LOG.md`)
into the LaTeX source, plus the still-valid mechanical instructions from
`TEX_PORT_PLAN.md`. Zero model/provider/network calls. No git write commands.
`RELEASE_MANIFEST*` not regenerated (a later step owns that).

Write scope, exactly five:

| File | sha256 before | sha256 after |
|---|---|---|
| `eval/dense_chain_v32_20260830/paper/longmemeval_auditable_memory_paper.tex` | `f4e19301…7158f5b` | `6e36e289…8f5c48a9e` |
| `eval/dense_chain_v32_20260830/paper/longmemeval_auditable_memory_paper.pdf` | `b58cdea6…3771fe7aee4d88` | `376ffc35…81af9481d2c28f` |
| `eval/dense_chain_v32_20260830/paper/ARXIV_SUBMISSION.md` | `38493a5a…180372fbe6b6` | `357a92cb…f53ec36d57198` |
| `arxiv_upload/longmemeval_auditable_memory_paper.tex` | `f4e19301…7158f5b` | `6e36e289…8f5c48a9e` |
| `…/audit_2026-09-05/tex-port/PORT_LOG.md` | (new) | this file |

Untouched: the paper `.md`, `GOLD_DEFECT_DOSSIER.md`, `SOTA_WRITEUP.md`,
`README.md`, `RELEASE_MANIFEST*`, `ANCHORS.md`, `scripts/`, `tests/`, every
judge/reader directory. `git status` after the port shows no new modified file
outside the scope above; no `.aux`/`.log`/`.out` build artifacts were left in
the repo.

**Headline integrity.** `479/475` is unchanged everywhere. Post-port
occurrences in the tex: title (L14), abstract (L22, as 479/500 + 475/500),
§1 (L53), §5.1 table (L208), §5.1.1 total row, §5.3 (L326), §6.3 (L387),
§7 correction bullet (L439), §9 (L496). No headline number was edited.

---

## 1. Facts the port was checked against

Re-derived from the released bytes before editing (not taken from the plan):

- Headline raw pair **479/500 and 475/500** (Opus), unchanged.
- Splits: Opus p1 452/470 + 27/30 = 479; Opus p2 450/470 + 25/30 = 475.
  grok p1 450/470 + 26/30 = 476; grok p2 447/470 + 27/30 = 474. The tex's
  §5.1 "Prior-configuration detail" splits (450/447, 26/27) are the **grok**
  pair's and were already correctly labelled as the prior configuration —
  the tex never carried the md's "Headline-pair detail" mislabel.
- `370a8ff4` judged False in all four passes ⇒ adjudication is **+1 per pass**:
  grok pair **477/475**, Opus pair **480/476**. Both pairs are named at every
  occurrence; they are never merged.
- `gpt4_731e37d7` is **Class D (boundary semantics)**. No reader fabricated:
  the `$500` is user-stated (`answer_826d51da_2`, 2023/02/26 13:37). Opus
  counted it ($720, judged correct both passes); grok excluded it ($220,
  judged wrong both passes) on window grounds.
- Strict defects (A+B) = **1**, not 2.
- Judge provenance: the tex cites exactly one judge directory —
  `full-v34-opus_pass1/judge_gpt4o_repro_20260901/` (§8, the 478 same-day
  repro). It never cites the authoritative pass-1 dir, so there was **nothing
  to redirect to `judge_gpt4o_v2`**. No edit made; recorded so the next pass
  does not go looking.

---

## 2. Edits, before → after

Old line numbers are from the pre-edit 461-line tex; new line numbers from the
finished 532-line tex.

### E1 — Title (PI-1) · L14 → L14

BEFORE
```
\title{\textbf{Auditable Long-Term Memory: A Deterministic Retrieval\\Chain at 95.4$\pm$0.4\% on LongMemEval-S}}
```
AFTER
```
\title{\textbf{Auditable Long-Term Memory: A Deterministic\\Retrieval Chain Scoring 479/475 of 500 on\\LongMemEval-S Under the Official Judge}}
```

Deviation from the plan, deliberate. The plan's replacement keeps a single
`\\` after "Retrieval". Measured at `\LARGE\bfseries` against
`\textwidth = 469.755pt`, that break gives segments of **495.52pt** and
**641.69pt** — both over-wide, so LaTeX would silently re-wrap them into an
unbalanced block. Two `\\` at measured points give **411.87 / 362.94 /
355.92pt**, all inside `\textwidth`. Same convention (`\\` inside
`\title{\textbf{…}}`), no new packages, no wording change. Rendered title
verified in the PDF as three balanced lines.

### E2 — Abstract strict-defect count (REWRITE_LOG §4.1) · L38–39 → L38–39

BEFORE `--- including two strict gold-answer / defects, an improvement stage…`
AFTER  `--- including a strict gold-answer / defect, an improvement stage…`

### E3 — §1 (PI-16) · L53–59 → L53–60
Restores "across two independent full passes", "(478)", and "(what counts as a
reportable number)"; applied verbatim from the plan.

### E4 — §2 haystack (PI-8) · L86–87 → L87–90
Adds `\texttt{\_abs}` notation, "$\sim$40--60 sessions with timestamps",
"several sessions"; verbatim from the plan.

### E5 — §3.3 controls (PI-9) · L135–139 → L138–144
Adds "(invariant R1)" and the per-control explanations; verbatim.

### E6 — §3.4 scaffolds (PI-10) · L143–146 → L148–153
"For 240 of 470 questions" → "For questions whose type benefits from
mechanical reasoning (240 of 470)"; adds the value-preference gloss; verbatim.

### E7 — §3.5 reader (PI-2) · L152–154 → L159–163
Names the Opus/CLI headline reader and the two secondary readers; verbatim.

### E8 — §4.1 (PI-11) · L158–159 → L167–169
"small margin" → "one-point margin"; "before the deciding experiments" →
"two days before the deciding experiment"; verbatim.

### E9 — §5.1 table, two ex-dossier rows (PI-6a) · after L200 → L211–212

AFTER (added)
```
v3.4, Claude Opus reader --- ex-dossier (8 dossier rows removed, \S6.3) & 474/492 & 471/492\\
v3.4, grok-4.6 high --- ex-dossier (same 8 rows removed) & 475/492 & 474/492\\
```

Deviation, typesetting-driven and measured. The plan's row-1 label
("…ex-dossier (8 gold-defect/boundary rows removed, \S6.3)") makes the
`tabular{lcc}` **530.00pt** wide against `\textwidth = 469.755pt`; the first
build confirmed `Overfull \hbox (60.2451pt too wide)`. Options measured:
`\small` → 487.17pt (still over), `\footnotesize` → 453.41pt (fits but shrinks
the headline table), shortened label at full size → **459.25pt (fits)**. Chose
the shortened label so the headline table keeps its normal size. The dropped
descriptor "gold-defect/boundary" is fully recoverable in place: the cell
still points at `\S6.3` ("Gold-answer defects (1 strict, 7 boundary)") and
§5.2's footnote spells out "all eight gold-defect/boundary rows removed from
both readers". The grok row and the `474/492 · 471/492 · 475/492 · 474/492`
figures are the plan's/md's verbatim.

### E10 — §5.1 ex-dossier lead paragraph (PI-6b) · after L203 → L217–222
Inserted verbatim from the plan (identical to md L222–226).

### E11 — §5.1 gold-defect passage (REWRITE_LOG §4.2; audit-flagged L215–220) · L215–221 → L233–241

BEFORE
```
``one above'' is a judge roll). The two gold-defect rows from the dossier (\S6.3) sit inside this
pair as well: one is scored correct via the fabrication the dossier
documents (the reader supplies the \$500 no session contains), one is lost
to fidelity (the evidence-faithful answer contradicts defective gold) ---
net zero per pass. Under adjudication the pair reads 478/474
(ex-fabrication) to 480/476 (restored); the tie with the published state
of the art holds in every stance.
```
AFTER
```
``one above'' is a judge roll). The two rows \S6.3 documents individually
--- the \$720 workshop row and the 15-weeks row --- sit inside this pair as
well: one is scored correct because this reader counts a user-stated \$500
fee whose event is dated outside the question's four-month window (a
boundary row, not a fabrication --- \S6.3), one is lost to fidelity (the
evidence-faithful answer contradicts defective gold) --- net zero per pass.
Adjudicating the single strict defect raises the Opus pair to 480/476
(479+1 / 475+1); the tie with the published state of the art holds in every
stance.
```

Verified per audit-flagged line before editing: **L215** (calls both rows
"gold-defect") contradicted; **L216–217** ("the fabrication the dossier
documents", "the \$500 no session contains") contradicted — the fee is
user-stated; **L219–220** ("478/474 (ex-fabrication) to 480/476 (restored)")
contradicted — the ex-fabrication branch presumed a fabrication that does not
exist, and 480/476 is now the single figure. "net zero per pass" was kept:
still arithmetically true for this pair (one row +1, one row −1); only its
reason changed.

### E12 — §5.1 grok-pair adjudication figure (REWRITE_LOG §4.4; audit-flagged L241) · L241–242 → L261–262

BEFORE `adjudication scenario (\S6.3) the prior pair reads 478/476; we report that as a / scenario, never as a score.`
AFTER  `adjudication scenario (\S6.3) the prior pair reads 477/475 (476+1 / 474+1, the / single strict defect); we report that as a scenario, never as a score.`

`478/476` presumed 2 strict defects on the grok pair (476+2 / 474+2). With one
strict defect the grok pair is 477/475. The paragraph **label**
("Prior-configuration detail") is CP-1 and was left alone — only the
contradicted number moved.

### E13 — §5.2 ablation ladder, missing row (PI-12) · after L281 → L302
Adds `+ v3.3 operators (official pair) & 471 / 470\\`; verbatim from the plan
and from md L317.

### E14 — §6.1 (PI-13) · L337–338 → L358–360
Adds "Two verifier designs failed to fix this honestly (\S6.2)."; verbatim.

### E15 — §6.2 adjudicator clause (PI-14) · L346 → L368–370
Adds ": on the residue rows the adjudicator reaches defensible-but-not-gold
readings." The §6.2 **closing sentence** was left as published (CP-8).

### E16 — §6.3 (REWRITE_LOG §4.6 + surviving PI-15 clauses; audit-flagged L349, L352, L355, L356) · L349–358 → L373–393

BEFORE
```
\textbf{6.3 Gold-answer defects (2 strict, 6 boundary).} Documented row-by-row
in the released dossier. Strict A: gold requires a \$500 expense that appears
nowhere in the evidence, plus an event dated after the question date attended
in the past tense; a weaker reader that \emph{hallucinated} the missing \$500
was scored correct by the official judge. The grok reader's evidence-faithful
\$220 scores 0 in both passes; we keep the 0. The headline Opus reader, by
contrast, supplies the \$500 and is scored correct on both passes --- the
disclosed fabrication point inside 479/475 (\S5.1). Strict B: gold says ``15 weeks''
between two user-dated events 81 days apart. Six further rows are
boundary-semantic and claimed as worth nothing. The Chronos authors
```
AFTER
```
\textbf{6.3 Gold-answer defects (1 strict, 7 boundary).} Documented row-by-row
in the released dossier. Strict B: gold says ``15 weeks'' between two
user-dated events that are 81 days (11 weeks 4 days) apart; wrong in all four
passes of both reader configurations. Boundary --- the \$720 workshop row
(published as strict; reclassified after re-auditing the released packet):
gold requires a \$500 workshop fee, and the user states it (session
\texttt{answer\_826d51da\_2}, 2023/02/26 13:37, ``I paid \$500 to attend''),
so nothing has to be invented to reach gold. What is disputed is window
membership: both dated mentions place the workshop on March 15--16, after the
2023/02/26 question date, attended in the past tense. The grok reader excludes
the fee and answers \$220 $\to$ 0 in both passes; the headline Opus reader
includes it and answers \$720 $\to$ correct in both passes; a weaker
gemini-3.7-flash probe likewise included it and was scored correct. The judge
rewards including the out-of-window item because gold includes it --- the
disclosed window-inclusion point inside 479/475 (\S5.1), not a fabrication
point. Six further rows are boundary-semantic (defensible readings on both
sides); we claim nothing for them. One earlier strict candidate was
\emph{downgraded} to boundary after an independent-reader control showed the
intended referent was answerable by premise repair. The Chronos authors
```

Per audit-flagged line: **L349** "(2 strict, 6 boundary)" contradicted;
**L350–351** "a \$500 expense that appears nowhere in the evidence"
contradicted (flagged only implicitly by the audit; verified and fixed —
the past-tense/after-the-question-date half is preserved as the window
dispute); **L352** "\emph{hallucinated} the missing \$500" contradicted;
**L355** "supplies the \$500" — the Opus verdict itself is root-verified and
retained, but reframed as "includes it and answers \$720 $\to$ correct in both
passes" because "supplies" asserts invention; **L356** "the disclosed
fabrication point" contradicted → "the disclosed window-inclusion point".
Structure preserved: §6.3 remains one running paragraph, not an `itemize`.
The Chronos-defect sentence was left in place (CP-6). Strict B moved first,
matching the corrected md's ordering.

### E17 — §6.4 (PI-17) · L366–368 → L399–402
Adds "(alias mining + query expansion)" and "--- the presumed alias-mismatch
losses do not exist in this benchmark"; keeps the tex-only "(17/17)" per the
plan (see CP-5). The md's §6.4 **heading** was not ported (CP-10).

### E18 — §7 new first bullet (PI-7) · after L371 → L406–417
"No held-out evaluation" bullet inserted verbatim from the plan.

### E19 — §7 new final bullet (REWRITE_LOG §4.7) · before L387 → L433–443
Correction-provenance bullet, ported from md L455–464 with the md's
`$`/`§` converted to `\$`/`\S`:

```
\item \textbf{A claim in our own released dossier was wrong and is corrected
here.} The dossier originally classed the \$720 workshop row as
gold-unreachable without fabrication, on the claim that no \$500 workshop fee
appeared in the evidence; a mechanical re-audit of this release's own
published packets found that fee stated by the user, so the row is a boundary
row (\S6.3), the strict-defect count is 1 rather than 2, and the adjudication
figures in \S5.1 were recomputed. No verdict changed and the headline 479/475
is unaffected --- only the classification of a row that was already scored as
measured. The error and its correction are recorded in the dossier rather
than removed from it.
```

### E20 — §8 pinned-comparator lead (PI-3) · after L389 → L446–454
Inserted verbatim from the plan.

### E21 — §8 manifest sentence (PI-4) · L392 → L457
`verifies 449/449 manifest hashes` → `verifies every \texttt{RELEASE\_MANIFEST.md} row`.

### E22 — §8 held/released packets (PI-5) · L404–406 → L470–477
Materialized packets moved from "held" to "released"; verbatim from the plan.

### E23 — `ARXIV_SUBMISSION.md`, four edits

| Line | Before | After |
|---|---|---|
| 5 | `**Title:** … Retrieval Chain at 95.4±0.4% on LongMemEval-S` | `**Title:** … Retrieval Chain Scoring 479/475 of 500 on LongMemEval-S Under the Official Judge` |
| 12 | `Technical report, v1.2, 8 pages.` | `Technical report, v1.2, 9 pages.` |
| 16 | `216 words; arXiv limit 1920 characters — this is 1470 characters` | `216 words; arXiv limit 1920 characters — this is 1467 characters` |
| 18 | `…including two strict gold-answer defects, an improvement stage…` | `…including a strict gold-answer defect, an improvement stage…` |

Counts recomputed on the finished abstract text: **216 words, 1467
characters** (arXiv limit 1920). Line 12's page count was stale after the
rebuild (8 → 9) and is corrected. Nothing was sent anywhere.

---

## 3. PI-1..PI-17 disposition

| Item | Status | Note |
|---|---|---|
| PI-1 Title | **Applied, adapted** | Plan's single `\\` measures 495.52 / 641.69pt vs `\textwidth` 469.76pt; used two measured breaks (411.87 / 362.94 / 355.92pt). Wording identical to the md title. |
| PI-2 §3.5 | Applied verbatim | |
| PI-3 §8 lead | Applied verbatim | |
| PI-4 §8 manifest | Applied verbatim | |
| PI-5 §8 held/released | Applied verbatim | |
| PI-6 §5.1 table + para | **Applied, adapted** | Row-1 label shortened; `Overfull \hbox 60.25pt` measured and removed. Paragraph verbatim. |
| PI-7 §7 bullet | Applied verbatim | |
| PI-8 §2 | Applied verbatim | |
| PI-9 §3.3 | Applied verbatim | |
| PI-10 §3.4 | Applied verbatim | |
| PI-11 §4.1 | Applied verbatim | |
| PI-12 §5.2 row | Applied verbatim | |
| PI-13 §6.1 | Applied verbatim | |
| PI-14 §6.2 | Applied verbatim | Adjudicator clause only; closing sentence is CP-8. |
| PI-15 §6.3 | **Superseded in part** | Its replacement text preserves "2 strict, 6 boundary", "the judge rewards gold-matching over evidence fidelity", and "the disclosed fabrication point inside 479/475" — all contradicted by the corrected md. Surviving clauses were folded into E16: "(11 weeks 4 days)", "we claim nothing for them", and the downgraded-strict-candidate sentence. The Strict-A / "hallucinated" characterization is dropped, not reworded. |
| PI-16 §1 | Applied verbatim | |
| PI-17 §6.4 | Applied verbatim | |

REWRITE_LOG items with **no tex counterpart** (no edit made, recorded here):

- **§4.3** (md's "Headline-pair detail:" → "Raw grok-pair detail…"). The tex
  reads "Prior-configuration detail:" and its 450/447 + 26/27 splits are the
  grok pair's, so the tex never carried the md's mislabel. Renaming the label
  is CP-1 and was left to the author.
- **§4.5** (md §6 partition "(2 strict, 6" → "(1 strict, 7"). The tex has no
  partition sentence at all — its §6 intro is one line ("Of 470 answerable
  questions, 24 fail in at least one prior-configuration pass."). The plan
  noted the missing partition content but assigned it no PI number, so it is
  neither a mechanical port nor a CP item. Recorded as an open gap.

---

## 4. CP-1..CP-10 — left for the author, not acted on

1. **CP-1 — "prior configuration" vs "headline pair"** (4 sites: §4.2 L174,
   the §5.1 paragraph label L259, §5.1 L261, §6 intro L355). Decide whether
   the grok-pair paragraph stays as its own paragraph beside an added
   headline-pair one, or is replaced wholesale. *Note:* the contradicted
   **number** at L261 was corrected (478/476 → 477/475) because the task
   named that line; the **label** is untouched.
2. **CP-2 — §4.3 closing sentence.** tex: "The reader-tier upgrade in this
   report passed the same control with zero flips before its full pair was
   launched." md: "The frozen acceptance rule — zero control flips — blocked
   it from ever touching the headline." Two different facts about two
   different things; author must say which is current, or whether both belong.
3. **CP-3 — §4.4 tells a different story in each document.** tex §4.4 is
   "built, then withdrawn"; md §4.4 narrates SC applied to the grok pair as
   informative, and puts the withdrawal in §5.1 instead. The corrected md's
   §5.1 grok paragraph now carries the withdrawal *and* the 477/475 figure, so
   this is more entangled than when the plan was written, not less.
4. **CP-4 — §5.3 is richer in the tex** (28% vs 15% packet-size buckets,
   90/86% for V4 Pro, DeepSeek 407/470 answerable, reader curve
   93 → 436 → 455 → 465 → 471 → 476). None of it appears in the md. Do not
   let a future full-paragraph sync delete it.
5. **CP-5 — §6.4 "(17/17)"** is tex-only; the md gives no equivalent figure.
   Preserved by PI-17; the md's silence is not corroboration. Confirm the
   count.
6. **CP-6 — §6.3 Chronos-defect sentence placement.** Left inline in the tex
   §6.3 (md keeps the same fact as a References annotation). Either placement
   is defensible; the fact is not lost in the shuffle.
7. **CP-7 — the md's References list is missing 5 of the 8 works its own §1.1
   cites** (MemGPT, LoCoMo, Nogueira & Cho, BGE-M3, RRF, Wang, Zheng, Dodge).
   The tex list is complete. **Not ported — the tex References are left
   intact.** The gap is in the md and needs repair there.
8. **CP-8 — §6.2 closing sentence.** tex: "Both failures are published; they
   map the limit of prompting-side repair." md: "…motivate an
   evidence-testimony layer as future work." Author's rhetorical choice.
9. **CP-9 — no table changed column count; no figures exist** in either
   document. Re-confirmed after this port: §5.1 is still `lcc`, §5.1.1 still
   `lccccc`, §5.2 still `lc`; every change was a row.
10. **CP-10 — §6.4 heading.** md's "Retrieval ceiling (2 rows) and flip
    noise" is inconsistent with its own body (1 pool-miss + 3 ordering = 4
    rows). Not ported; the tex heading stands.

---

## 5. Build

Run from `eval/dense_chain_v32_20260830/paper/`, twice, as specified:

```
pdflatex -interaction=nonstopmode longmemeval_auditable_memory_paper.tex   # exit 0
pdflatex -interaction=nonstopmode longmemeval_auditable_memory_paper.tex   # exit 0
```

- **First build** (before the E9 typesetting fix): exit 0 / exit 0, 9 pages,
  one warning — `Overfull \hbox (60.2451pt too wide) in paragraph at lines
  204--215` (the §5.1 table). Fixed by E9, not left standing.
- **Final build:** exit 0 and exit 0, **9 pages**, `232,363` bytes.
  **Zero** `!` errors, **zero** `Overfull \hbox`, **zero** `Underfull \hbox`.
- PDF was 8 pages before the port; the added §5.1 rows/paragraph, §7 bullets,
  §8 paragraph and §6.3 expansion push it to 9.
- `.aux`, `.log`, `.out` were removed after the build; the log is kept out of
  tree at the session scratchpad.
- Rendered checks in the PDF text layer: title on three balanced lines;
  "a strict gold-answer defect"; "8 dossier rows removed, §6.3"; "raises the
  Opus pair to 480/476 (479+1 / 475+1)"; "the prior pair reads 477/475 (476+1
  / 474+1, the single strict defect)"; "6.3 Gold-answer defects (1 strict, 7
  boundary)"; "the disclosed window-inclusion point inside 479/475"; the
  "No held-out evaluation" and "corrected here" bullets.

---

## 6. Byte-identity proof — `arxiv_upload` vs the paper `.tex`

```
$ diff arxiv_upload/longmemeval_auditable_memory_paper.tex \
       eval/dense_chain_v32_20260830/paper/longmemeval_auditable_memory_paper.tex
(no output)

$ cmp  arxiv_upload/longmemeval_auditable_memory_paper.tex \
       eval/dense_chain_v32_20260830/paper/longmemeval_auditable_memory_paper.tex
(no output)

$ shasum -a 256 arxiv_upload/longmemeval_auditable_memory_paper.tex \
                eval/dense_chain_v32_20260830/paper/longmemeval_auditable_memory_paper.tex
6e36e28913ba8d124179cf310ae2342b67f510e305000b93a4723308f5c48a9e  arxiv_upload/…
6e36e28913ba8d124179cf310ae2342b67f510e305000b93a4723308f5c48a9e  eval/…/paper/…
```

The two files were also byte-identical **before** the port
(`f4e1930144c2b013…`), so the sync is a re-establishment, not a first
alignment.

---

## 7. What the plan and the rewrite both missed

1. **The corrected `.md` still carries a 2-strict claim.** §5.1.1, md L300:
   "multi-session aggregation (**where both strict gold defects live**)".
   Contradicted by the md's own §6.3 heading ("1 strict, 7 boundary") and §7
   correction bullet. The plan classed that whole sentence as md-only Tier C,
   so it was never diffed for content; the rewrite's edit list never reached
   it. **The tex has no equivalent sentence, so the tex is clean** — and this
   is a positive reason not to port that sentence later. Fix belongs in the
   `.md`, which is out of this write scope.
2. **PI-1's title does not fit the page.** Measured, not guessed: 495.52pt and
   641.69pt against 469.76pt. The plan flagged it as "compile check" only.
3. **PI-6's table row does not fit the page.** 530.00pt against 469.76pt;
   confirmed as a real `Overfull \hbox 60.2451pt` on the first build. The plan
   asserted "no new LaTeX packages, no new environments" was sufficient for
   mechanical portability, which held — but width was never measured.
4. **§6 intro has no partition sentence in the tex**, so REWRITE_LOG §4.5 has
   nothing to correct there. The plan noticed the missing content but gave it
   no PI number and no CP number, leaving it in a gap between the two lists.
5. **`ARXIV_SUBMISSION.md` line 12's "8 pages" was stale** the moment the PDF
   was rebuilt. The task named lines 5 and 18; the page count and the
   character count on line 16 were consequential and are corrected too.
6. **No pass-1 judge-provenance citation exists in the tex** to point at
   `judge_gpt4o_v2`. The only judge directory the tex names is the §8 repro
   dir, which is correct as written.
