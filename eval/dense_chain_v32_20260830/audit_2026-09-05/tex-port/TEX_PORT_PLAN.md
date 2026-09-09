# TEX Port Plan — longmemeval_auditable_memory_paper (.md → .tex)

Read-only diff/plan artifact. Nothing in `paper/` or `arxiv_upload/` was modified to produce this.

## Bottom line

- **Content differences found (md vs tex, current state): 39** enumerated in `tex_port_plan.json`.
  - **7** are the KNOWN Sept 4–5 drift (commits `1dacbebc`, `7c12e127`, `e8b7078e`, `e601671d`) — PI-1..PI-7 below.
  - **10** are mechanically-portable PRE-EXISTING gaps (the tex was never a byte-faithful mirror of the md; these are omitted clauses/rows/numbers that predate the Sept-1 tex baseline commit `27904b9`) — PI-8..PI-17 below.
  - **10** require a human decision before porting — CP-1..CP-10 below. Two of these are not wording drift at all: §4.3 and §4.4 tell **different stories** in the two documents (not condensation — a different claim / different narrative), and the md's own References list is missing 5 works it cites inline (tex's is complete — do not overwrite it).
  - **12** are cosmetic-only (punctuation/tense/article, zero informational delta) — Tier C, listed compactly, not recommended as individual ports.
- **Mechanically portable: 17 of 39** (PI-1..PI-17). All are text substitutions in existing `\textbf{}`/paragraph/itemize/tabular structures — no new LaTeX packages, no new environments.
- **No table changed column count** (§5.1, §5.1.1, §5.2 tables all gained/need rows only, never columns). **No figures exist in either document.** Citations are handled as one structural flag (CP-7), not per-citation edits.
- **TeX toolchain: INSTALLED and verified.** TinyTeX `pdflatex` at `~/Library/TinyTeX/bin/universal-darwin/pdflatex` (also xelatex, lualatex, latexmk) plus Homebrew `tectonic` at `/opt/homebrew/bin/tectonic`. Test-compiled the current tex in an isolated scratch copy (not the repo) — clean 2-pass build, exit 0, 8-page PDF. **The PDF does not have to be recorded as stale** — see §5.

## 1. Commits that touched the md after the tex's baseline (2026-09-01 17:29:17, commit `27904b9`)

`git log --follow` on `eval/dense_chain_v32_20260830/paper/longmemeval_auditable_memory_paper.md`. The tex's own last touch was **also** `27904b9` (a 1-line manifest-count edit, 448→449 — confirmed via `git show --stat`), so `27904b9` is the true shared baseline for both files, not just the tex's mtime.

| Commit | Timestamp | Subject | md lines touched |
|---|---|---|---|
| `27904b9` | 2026-09-01 17:29:17 | paper/README: manifest count 449 (shared baseline — also touched tex) | 1 (448→449) |
| `1dacbebc` | 2026-09-04 21:01:02 | paper+tests: name the Opus pair as the headline reader in 3.5; make CLI-lane tests hermetic | §3.5 rewritten (headline was still credited to grok-4.6-high, contradicting abstract/§5.1) |
| `7c12e127` | 2026-09-04 21:28:26 | paper: point the reproducibility section at the pinned comparator sources | §8 new lead paragraph (+9 lines) naming `comparators/MANIFEST.md` |
| `e8b7078e` | 2026-09-04 21:40:54 | paper: the pinned-sources lead names what is and is not pinned | §8 lead sentence corrected (review fix on `7c12e127` — bold lead had read as a universal pin claim) |
| `e601671d` | 2026-09-05 09:50:07 | paper: raw-count title, ex-dossier rows in the 5.1 table, no-held-out Limitations bullet, section 8 released/held sentence | title; §5.1 table +2 rows +1 paragraph; §7 +1 bullet; §8 manifest-verify sentence + held/released paragraph |

Verified: diffing the md at `27904b9` against the current md reproduces **exactly** the union of these four commits' diffs — nothing else changed in the md since the shared baseline.

## 2. Structural comparison — every content difference, by section

Full detail (exact md/tex text, replacement text) is in the numbered instructions below and in `tex_port_plan.json`. Section-by-section presence map:

| § | md-only content | tex-only content | Numeric/claim conflict |
|---|---|---|---|
| Title | raw-count framing | percentage framing | — (KNOWN, PI-1) |
| Abstract | — | — | cosmetic only (Tier C) |
| 1 Intro | "(478)", "across two independent full passes", "(what counts as a reportable number)" | — | — (PI-16) |
| 1.1 Related work | "cross-encoder reranking:" label, minor connectives | — | — (Tier C) |
| 2 Benchmark | haystack size ("~40–60 sessions"), `_abs` notation, "several" | — | — (PI-8) |
| 3.1–3.2 | — | — | none |
| 3.3 | invariant R1 tag, control explanations (what each control tests) | — | — (PI-9) |
| 3.4 | "(240 of 470)" rationale, value-preference invariant explanation | — | — (PI-10) |
| 3.5 | headline-reader identity (Opus named, CLI lane, secondary readers named) | — | **YES — KNOWN** (PI-2) |
| 4.1 | "one-point margin", "two days before" | "small margin", generic "before the deciding experiments" | precision loss (PI-11) |
| 4.2 | "official passes", judge-disagreement-direction breakdown (7 vs 2–4) | **"our prior configuration"** | **terminology conflict — CP-1** |
| 4.3 | "blocked it from ever touching the headline" (re: rejected verifier) | **"the reader-tier upgrade in this report passed the same control"** (different claim) | **DIFFERENT CLAIM — CP-2** |
| 4.4 | detailed SC-on-grok-pair narrative, framed as informative, not "withdrawn" here | **"built, then withdrawn"** framing (matches md's §5.1 paragraph instead) | **DIFFERENT NARRATIVE — CP-3** |
| 4.5 | — | — | none |
| 5.1 table | 2 ex-dossier rows | — | **YES — KNOWN** (PI-6) |
| 5.1 para 1 (post-table) | ex-dossier lead paragraph | — | **YES — KNOWN** (PI-6) |
| 5.1 "headline-pair detail" | SC-withdrawal paragraph placed here; **477/477** | **"Prior-configuration detail"** heading; **prior pair reads 478/476** | **NUMERIC CONFLICT — CP-1** |
| 5.1.1 | delta numbers inline, closing "residual concentrates..." sentence, duplicate gemini-partial note | — | — (Tier C / minor) |
| 5.2 table | "+ v3.3 operators (official pair) 471/470" row | — | missing row (PI-12) |
| 5.2 footnote | "Every rescore...identical frozen judge harness" sentence | — | — (Tier C) |
| 5.3 | — | specific % figures (28/15%, 90/86%), 407/470 answerable, full reader-capability curve (93→436→455→465→471→476) | **tex is richer — CP-4, do not overwrite** |
| 6 intro | full partition breakdown (4+8+4+8=24) + "12 winnable" cross-cutting note | **"prior-configuration pass"** | terminology + missing content (CP-1 + PI note) |
| 6.1 | "Two verifier designs failed to fix this honestly (§6.2)" | — | — (PI-13) |
| 6.2 | "adjudicator reaches defensible-but-not-gold readings"; "future work" framing | "published" framing (different closing claim) | minor claim swap (PI-14, low-confidence on closing sentence) |
| 6.3 | "(11 weeks 4 days)", "downgraded to boundary" sentence, "judge rewards gold-matching..." clause; Chronos-defect note moved to References | Chronos-defect note **inline here** | relocation, not omission — **CP-6** |
| 6.4 | "(alias mining + query expansion)" | **"(17/17)"** test result; different heading text | asymmetric — merge both ways (PI-17, CP-5) |
| 7 Limitations | "No held-out evaluation" bullet; "(§5.3)" cross-ref in scaffold bullet; "LongMemEval-S measures a specific memory regime" clause | — | **bullet is KNOWN** (PI-7); rest is Tier C |
| 8 lead | pinned-comparator-sources paragraph | — | **YES — KNOWN** (PI-3) |
| 8 manifest line | "verifies every `RELEASE_MANIFEST.md` row" | "verifies 449/449 manifest hashes" | **YES — KNOWN** (PI-4) |
| 8 held/released | materialized packets now RELEASED, new path + script | materialized packets still listed as HELD | **YES — KNOWN, factual scope change** (PI-5) |
| 8 rest | "SC rule" naming | "tie-break rule" naming | terminology only, not a conflict |
| 9 Conclusion | — | — | cosmetic only |
| References | Wu/Chronos/Barnes annotations | 5 additional works (MemGPT, LoCoMo, Nogueira&Cho, BGE-M3, RRF, Wang, Zheng, Dodge) that md cites in §1.1 but drops from its own reference list | **md's list is INCOMPLETE — CP-7, do not port** |
| Footer | — | — | none, identical |

## 3. Port instructions (mechanically portable — PI-1 .. PI-17)

Each gives: tex location (section + anchor line from the current 461-line tex), current text, replacement text in the file's own LaTeX conventions (`---` for em-dash, `\%`, `\$`, `\S`, `\_`, `$\pm$`, `\emph{}`/`\textbf{}`, existing `tabular`/`itemize`). Line numbers are from a fresh read of `eval/dense_chain_v32_20260830/paper/longmemeval_auditable_memory_paper.tex` today.

---

### PI-1 — Title [KNOWN · e601671d · supersession risk LOW-MEDIUM]
**Location:** line 14, `\title{...}`
**Current:**
```
\title{\textbf{Auditable Long-Term Memory: A Deterministic Retrieval\\Chain at 95.4$\pm$0.4\% on LongMemEval-S}}
```
**Replacement:**
```
\title{\textbf{Auditable Long-Term Memory: A Deterministic Retrieval\\Chain Scoring 479/475 of 500 on LongMemEval-S Under the Official Judge}}
```
Note: longer title — worker should visually check the compiled title block doesn't overflow the line/page at 11pt (compile check, not a text-substitution risk).

### PI-2 — §3.5 Replaceable reader [KNOWN · 1dacbebc · supersession risk LOW]
**Location:** lines 152–154
**Current:**
```
\textbf{3.5 Replaceable reader.} The packet, scaffold, and question go to an
LLM reader, deliberately replaceable; we measure the chain under multiple
readers (\S5.3).
```
**Replacement:**
```
\textbf{3.5 Replaceable reader.} The packet, scaffold, and question go to an
LLM reader. The reader is deliberately replaceable; we measure the chain
under three readers (\S5.3). The headline pair uses the Claude Opus reader
over the CLI lane (\S5.1); \texttt{grok-4.6-high} and GLM-5.3 are the
secondary readers (\S5.3).
```

### PI-3 — §8 new lead paragraph [KNOWN · 7c12e127+e8b7078e · supersession risk LOW]
**Location:** insert immediately after line 389 (`\section{Reproducibility}`), before line 390 (`Released with this report at`)
**Current:** (paragraph does not exist)
**Insert:**
```
\textbf{The Chronos and Mastra comparator sources are pinned in the release;
OMEGA is not.} The Chronos paper (arXiv 2603.16862, PDF and abstract page)
and the Mastra Observational Memory page that supply the 478/500 and
94.87\%~/~468 raw comparator figures are stored with SHA-256 digests and a
fetch timestamp under \texttt{eval/dense\_chain\_v32\_20260830/comparators/}
(see its \texttt{MANIFEST.md}), so the comparison rows in \S5.1 can be
checked against bytes the release carries. The OMEGA figure quoted in \S5.1
has no pinned source yet; that gap is recorded in the same manifest.

```

### PI-4 — §8 manifest-verification sentence [KNOWN · e601671d · supersession risk LOW]
**Location:** line 392
**Current:**
```
verifies 449/449 manifest hashes and re-derives every headline count from the
```
**Replacement:**
```
verifies every \texttt{RELEASE\_MANIFEST.md} row and re-derives every headline count from the
```

### PI-5 — §8 held/released materialized-packets paragraph [KNOWN · e601671d · supersession risk LOW-MEDIUM, §8 named in the campaign step]
**Location:** lines 404–406
**Current:**
```
packet-compiler and scaffold-operator sources and the materialized packets
(benchmark haystack text). The held stages ship as pinned artifacts with
```
**Replacement:**
```
packet-compiler and scaffold-operator sources. The materialized packets and
the v3.4 scaffolds the headline pair consumed are released under
\texttt{eval/dense\_chain\_v32\_20260830/packets\_materialized/} (gzip; sha256
in its \texttt{MANIFEST.md}), and \texttt{scripts/materialize\_packets.py}
re-derives every packet byte-for-byte from the released allocation and the
MIT benchmark data, so stage 5 (reader) and the judge are re-runnable by a
third party on the exact text we read. The held stages ship as pinned
artifacts with
```

### PI-6 — §5.1 table rows + new paragraph [KNOWN · e601671d · supersession risk **HIGH** — §5.1 is named for the fabrication-passage correction pass]
**Location:** table body lines 198–201; new paragraph immediately after `\end{center}` (line 203) and before "The Opus pair is the headline" (line 205)
**Current table tail:**
```
v3.4, grok-4.6 xhigh (agentic transport) & 461/500 & 465/500\\
\bottomrule
```
**Replacement table tail:**
```
v3.4, grok-4.6 xhigh (agentic transport) & 461/500 & 465/500\\
v3.4, Claude Opus reader --- ex-dossier (8 gold-defect/boundary rows removed, \S6.3) & 474/492 & 471/492\\
v3.4, grok-4.6 high --- ex-dossier (same 8 rows removed) & 475/492 & 474/492\\
\bottomrule
```
**Insert after `\end{center}`:**
```
Ex-dossier, grok leads Opus 475/474 to 474/471: the Opus margin on the full
set is carried by gold-idiom reading on dossier rows (\S5.2, \S6.3), not by
evidence reading on ordinary rows. Both are reported because the headline is
the official-judge score and the ex-dossier pair is what the evidence
supports.

```
**DO NOT PORT YET recommended** — see §6 supersession note below; this is the single highest-risk-of-rework instruction in this plan.

### PI-7 — §7 Limitations, new first bullet [KNOWN · e601671d · supersession risk LOW]
**Location:** insert as new first `\item` right after line 371 (`\begin{itemize}`)
**Insert:**
```
\item \textbf{No held-out evaluation.} Every component that moves the score
--- the v3.2$\to$v3.4 operator ladder, the extension-ordering sweeps, the
packet budgets, and the 60-row negative-control set --- was developed
against the same 500 LongMemEval-S questions the headline is measured on,
and the gold-defect dossier records per-row inspection of gold answers
during development. Nothing in this report is a test-set number in the
held-out sense. At a one-to-four-question margin over the published state
of the art this is the dominant threat to validity; the mitigations we do
have (deterministic stages with negative controls, two independent full
passes, every verdict released) bound variance, not overfitting. A
held-out run on a disjoint question set is the right next measurement and
has not been done.
```

### PI-8 — §2 haystack-size sentence [PRE-EXISTING · supersession risk NONE]
**Location:** lines 85–87
**Current:**
```
questions whose correct behavior is to decline to answer. Evidence for a
question may be spread across sessions recorded weeks apart.
```
**Replacement:**
```
questions (\texttt{\_abs}) whose correct behavior is to decline to answer.
Each question carries a haystack of $\sim$40--60 sessions with timestamps;
evidence for a question may be spread across several sessions recorded
weeks apart.
```

### PI-9 — §3.3 control explanations + invariant tag [PRE-EXISTING · supersession risk NONE]
**Location:** lines 135–139
**Current:**
```
dense baseline top-10 is preserved as a byte-identical prefix, remaining slots
fill in cross-encoder order with term-preserving extractive compression, and
budget overruns drop the lowest-ranked extension first. Validated by
determinism, gold-permutation and question-ID-sabotage negative controls, and
budget accounting.
```
**Replacement:**
```
dense baseline top-10 is preserved as a byte-identical prefix (invariant R1),
remaining slots are filled in cross-encoder order with term-preserving
extractive compression, and budget overruns drop the lowest-ranked extension
first. The compiler is validated by determinism (two compiles
byte-identical), a gold-permutation negative control (shuffled gold answers
must not change output), a question-ID sabotage control (renamed IDs must
not change output), and budget accounting.
```

### PI-10 — §3.4 explanatory clauses [PRE-EXISTING · supersession risk NONE]
**Location:** lines 143–146
**Current:**
```
\textbf{3.4 Deterministic reasoning scaffolds (``facts'').} For 240 of 470
questions the chain emits a deterministic evidence index computed from the
packet: session chronology, a canonical user-statement recency domain with
clock-granular tie keys, a value-preference invariant, candidate enumeration
```
**Replacement:**
```
\textbf{3.4 Deterministic reasoning scaffolds (``facts'').} For questions
whose type benefits from mechanical reasoning (240 of 470), the chain emits
a deterministic evidence index computed from the packet: session chronology,
a canonical user-statement recency domain with clock-granular tie keys, a
value-preference invariant (statements carrying candidate values outrank
bare recency), candidate enumeration
```

### PI-11 — §4.1 numeric/timing specificity [PRE-EXISTING · supersession risk NONE]
**Location:** lines 157–159
**Current:**
```
single full run at a small margin is not a reportable number. Our promotion
rule, adopted before the deciding experiments: a headline requires two full
```
**Replacement:**
```
single full run at a one-point margin is not a reportable number. Our
promotion rule, adopted two days before the deciding experiment: a headline
requires two full
```

### PI-12 — §5.2 ablation table, missing row [PRE-EXISTING · supersession risk LOW]
**Location:** lines 281–282 (insert between the cross-encoder-rerank row and the v3.4-operators row)
**Current:**
```
+ cross-encoder rerank (v3, grok reader) & 473\\
+ v3.4 operators (official pair, grok high) & 476 / 474\\
```
**Replacement:**
```
+ cross-encoder rerank (v3, grok reader) & 473\\
+ v3.3 operators (official pair) & 471 / 470\\
+ v3.4 operators (official pair, grok high) & 476 / 474\\
```

### PI-13 — §6.1 "two verifier designs" sentence [PRE-EXISTING · supersession risk LOW]
**Location:** line 337–338
**Current:**
```
correct evidence; the reader commits to an evidence-backed distractor. The
residue is question-boundary semantics
```
**Replacement:**
```
correct evidence; the reader commits to an evidence-backed distractor. Two
verifier designs failed to fix this honestly (\S6.2). The residue is
question-boundary semantics
```

### PI-14 — §6.2 adjudicator clause [PRE-EXISTING · supersession risk LOW · closing sentence is optional, see CP-8]
**Location:** line 346
**Current:**
```
(draft-blind candidate enumeration + rule-based adjudication) recovered 0/9.
```
**Replacement:**
```
(draft-blind candidate enumeration + rule-based adjudication) recovered
0/9: on the residue rows the adjudicator reaches defensible-but-not-gold
readings.
```

### PI-15 — §6.3 restore three omitted clauses [PRE-EXISTING · supersession risk **HIGH** — §6.3 is named for the fabrication-passage correction pass]
**Location:** lines 351–357
**Current:**
```
was scored correct by the official judge. The grok reader's evidence-faithful
\$220 scores 0 in both passes; we keep the 0. The headline Opus reader, by
contrast, supplies the \$500 and is scored correct on both passes --- the
disclosed fabrication point inside 479/475 (\S5.1). Strict B: gold says ``15 weeks''
between two user-dated events 81 days apart. Six further rows are
boundary-semantic and claimed as worth nothing.
```
**Replacement:**
```
was scored correct by the official judge --- the judge rewards gold-matching
over evidence fidelity. The grok reader's evidence-faithful \$220 scores 0 in
both passes; we keep the 0. The headline Opus reader, by contrast, supplies
the \$500 and is scored correct on both passes --- the disclosed fabrication
point inside 479/475 (\S5.1). Strict B: gold says ``15 weeks'' between two
user-dated events that are 81 days (11 weeks 4 days) apart. Six further rows
are boundary-semantic (defensible readings on both sides); we claim nothing
for them. One earlier strict candidate was \emph{downgraded} to boundary
after an independent-reader control showed the intended referent was
answerable by premise repair.
```
**DO NOT PORT YET recommended** — this whole clause set is about gold-defect characterization, exactly what the named campaign step will rewrite.

### PI-16 — §1 restore "(478)" / "across two independent full passes" / rule-definition parenthetical [PRE-EXISTING · supersession risk NONE]
**Location:** lines 52–60
**Current:**
```
replaceable reader role --- measures 479/475 per 500 on LongMemEval-S, pass 1
above the published state of the art, the pair a statistical tie with it, with
overlapping confidence intervals and per-run variance comparable to the gap.
\textbf{A methodology claim}: the apparatus that produced the number is the more
important contribution. Every stage below the reader is deterministic code
validated by negative controls; the promotion rule was frozen before the
deciding run;
```
**Replacement:**
```
replaceable reader role --- measures 479/475 per 500 on LongMemEval-S across
two independent full passes --- pass 1 above the published state of the art
(478), the pair a statistical tie with it, with overlapping confidence
intervals and per-run variance comparable to the gap. \textbf{A methodology
claim}: the apparatus that produced the number is the more important
contribution: every stage below the reader is deterministic code validated
by negative controls; the promotion rule (what counts as a reportable
number) was frozen before the deciding run;
```

### PI-17 — §6.4 merge both directions [PRE-EXISTING · supersession risk LOW · see CP-5]
**Location:** lines 366–368
**Current:**
```
An entity-linking retrieval arm was built, tested (17/17), and retired
when measurement showed zero of its added sessions were gold. Remaining
failures are measured flip noise.
```
**Replacement:**
```
An entity-linking retrieval arm (alias mining + query expansion) was built,
tested (17/17), and retired when measurement showed zero of its added
sessions were gold --- the presumed alias-mismatch losses do not exist in
this benchmark. Remaining failures are measured flip noise.
```
Keeps tex's `(17/17)` figure (md has no equivalent number) and adds md's descriptive clause + closing sentence. See CP-5 — a human should confirm `(17/17)` is still the current test count.

## 4. Cannot be ported mechanically — human/worker decision needed (CP-1 .. CP-10)

### CP-1 — "Prior configuration" vs "headline pair", 4 occurrences, one is a bare numeric conflict
tex says **"our prior configuration"** (§4.2, line 164), **"Prior-configuration detail"** as a paragraph label (§5.1, line 239) with **"the prior pair reads 478/476"** (§5.1, line 241), and **"24 fail in at least one prior-configuration pass"** (§6, line 334). The md's parallel text uses "headline"/"official passes" framing throughout and, at the equivalent spot in §5.1, gives **477/477**, not 478/476. This reads as a leftover label from a draft where the grok pair (not Opus) was headline, never fully reconciled after `1dacbebc` made Opus the named headline. **Decision needed:** is tex's "prior configuration" paragraph (a) the grok pair's own adjudication detail, which should be kept and the Opus/headline detail added alongside it, or (b) simply stale and should be replaced wholesale with md's headline-pair paragraph (477/477)? A blind search-replace of "prior configuration" → "headline" is not safe until this is resolved, because option (a) requires keeping a second, separate paragraph rather than a 1:1 substitution.

### CP-2 — §4.3 closing sentence is a different claim, not a rewording
md: *"The frozen acceptance rule — zero control flips — blocked it from ever touching the headline"* (about the **rejected** cite-or-revise verifier). tex: *"The reader-tier upgrade in this report passed the same control with zero flips before its full pair was launched"* (about the **reader-tier upgrade**, i.e. adopting Opus). These are two different facts about two different things, not two phrasings of one fact. A human with authorial context must say which is current/true and whether both belong in the paragraph.

### CP-3 — §4.4 tells a different story in each document
md's §4.4 narrates a self-consistency (SC) rule applied to "the raw v3.4 pair" (476/474, i.e. the grok pair), with a specific 476→475 / 474→475 shift discussed as informative ("rebuts the selection-on-outcome objection") — no "withdrawn" language anywhere in md's §4.4 itself. The "withdrawn" framing that tex's §4.4 uses instead appears in **md's §5.1** ("Headline-pair detail" paragraph), word-for-word similar to tex's §4.4. **The content has moved sections between the two documents, and md's own §4.4 now says something tex never said (an informative SC application to a still-live pair) rather than what tex says (SC was built and withdrawn).** This directly touches the same self-consistency/gold-defect material the task names for a later fabrication-correction pass on §5.1. Recommend: do not port §4.4 until that correction lands, then re-diff.

### CP-4 — §5.3 has content only in tex; do not overwrite
tex carries specific percentages (28% vs 15% across packet-size buckets, 90/86% for DeepSeek V4 Pro), a DeepSeek 407/470-answerable breakdown, and a stated reader-capability curve (93 → 436 → 455 → 465 → 471 → 476) that **do not appear anywhere in the current md**. If a future tool tries a full-paragraph sync from md into tex here, it would delete real analytical content. No action needed now — flagging so nobody "fixes" this paragraph by replacing it wholesale.

### CP-5 — §6.4 entity-linking test count is tex-only, unconfirmed by md
tex states the entity-linking retrieval arm was "tested (17/17)"; md gives no equivalent figure (positive or negative). PI-17 above preserves it, but a human should confirm 17/17 is still accurate before or after that merge — the md's silence is not corroboration.

### CP-6 — §6.3 Chronos gold-defect corroboration sentence has moved to md's References
tex states inline in §6.3: *"The Chronos authors independently document a defect on question `6d550036`... consistent with our dossier."* In the current md this same fact instead appears as a parenthetical on the Chronos citation in **References**, and md's §6.3 body does not have it. If PI-15 (§6.3 restore) is executed as a literal md-match, this sentence would need to be **deleted from tex's §6.3**, not silently dropped — recommend instead: leave it where it already lives in tex (§6.3 body) and do not port the References annotation; either placement is defensible, but do not lose the fact in the shuffle.

### CP-7 — md's References list is missing 5 works it cites in §1.1; do not port References at all
md's References section lists only 4 entries (Wu/LongMemEval, Sen et al./Chronos, Barnes/Mastra, BAAI/reranker). It is missing entries for MemGPT (Packer), LoCoMo (Maharana), Nogueira & Cho, BGE-M3 (Chen), Reciprocal Rank Fusion (Cormack), Wang (self-consistency), Zheng (LLM-as-judge), and Dodge (Show Your Work) — all eight are cited by name in md's own §1.1. tex's References section has all of these. **This is not something to port — tex is the more complete/correct document here.** Recommend surfacing to the author separately that the md's References section itself needs repair; out of scope for this tex port.

### CP-8 — §6.2 closing sentence: optional, not a clean omission
md closes with "...motivate an evidence-testimony layer as future work"; tex closes with "Both failures are published; they map the limit of prompting-side repair." These are two different rhetorical choices, not one truncating the other. PI-14 above only restores the adjudicator clause; leave the closing sentence to author discretion.

### CP-9 — No table changed column count; no figures exist
Checked explicitly per the task's own examples of non-mechanical cases: §5.1 headline table (3 cols in both), §5.1.1 per-question-type table (6 cols in both, all cell values match exactly already), §5.2 ablation table (2 cols in both) — every table diff found is a **row** addition, which is mechanical (PI-6, PI-12). Neither document contains an `\includegraphics`, a markdown image, or a figure environment. Nothing in this category actually blocks mechanical porting; recorded here only because the task asked the question directly.

### CP-10 — Heading-text mismatch in §6.4 not recommended for porting
md's §6.4 heading is "Retrieval ceiling (2 rows) and flip noise"; tex's is "Retrieval ceiling and coverage, measured precisely." md's own heading count ("2 rows") appears inconsistent with its own body and the §6 partition sentence (1 pool-miss + 3 ordering = 4 rows, not 2). Recommend not porting the md heading verbatim until that internal md discrepancy is resolved by the author.

## 5. PDF rebuild

TeX toolchain **is installed**: TinyTeX provides `pdflatex`, `xelatex`, `lualatex`, `latexmk`, `kpsewhich` at `~/Library/TinyTeX/bin/universal-darwin/`; Homebrew also provides `tectonic` at `/opt/homebrew/bin/tectonic`. All are on `PATH`.

Verified by test-compiling the **current, unmodified** tex in an isolated scratch copy (`/private/tmp/claude-501/-Users-cj/ada35468-f339-4d59-8027-c1740c8e0180/scratchpad/texbuild/`, never inside the repo): two `pdflatex` passes, both exit 0, output `longmemeval_auditable_memory_paper.pdf`, 8 pages, 225,900 bytes. No missing-package errors; all packages the tex declares (geometry, booktabs, microtype, parskip, titlesec, xcolor, hyperref, helvet) resolved from TinyTeX's tree.

**Rebuild command** (run from `eval/dense_chain_v32_20260830/paper/`, two passes for the TOC/reference bookmarks in `hyperref`'s `.out`/`.aux` to settle):
```
pdflatex -interaction=nonstopmode longmemeval_auditable_memory_paper.tex
pdflatex -interaction=nonstopmode longmemeval_auditable_memory_paper.tex
```
or equivalently `latexmk -pdf longmemeval_auditable_memory_paper.tex`, or `tectonic longmemeval_auditable_memory_paper.tex`.

Caveat: the freshly-built PDF is **225,900 bytes**, not the repo's checked-in **91,363 bytes** — expected (different TeX engine build/date/font-embedding than whatever produced the shipped PDF originally), not a sign of a broken build. After the actual port lands, rebuilding will **not** reproduce the existing PDF byte-for-byte; it will produce a new, current PDF that should replace it.

## 6. Supersession note — re-run this plan after the §5.1/§6.3/§8 fabrication-passage edits

The task names a later campaign step that will correct fabrication passages in **§5.1, §6.3, §8** of the md. Instructions in this plan touching those sections carry a supersession-risk tag; summary:

- **HIGH risk (do not port until after that edit, then re-diff):** PI-6 (§5.1 ex-dossier table+paragraph), PI-15 (§6.3 three clauses), CP-1's §5.1 piece (`477/477` vs `478/476`), CP-3 (§4.4/§5.1 self-consistency narrative — thematically entangled even though §4.4 isn't named), CP-6 (§6.3 Chronos-defect placement).
- **LOW-MEDIUM risk (§8-adjacent but not about the fabrication claims themselves — probably safe, re-check after anyway):** PI-3, PI-4, PI-5, PI-1 (title uses raw counts that live in §5.1's table, so if the headline numbers themselves move, the title moves too).
- **NONE / LOW (unaffected sections):** PI-2, PI-7, PI-8, PI-9, PI-10, PI-11, PI-12, PI-13, PI-14, PI-16, PI-17, CP-2, CP-4, CP-5, CP-7, CP-8, CP-9, CP-10.

Practical recommendation: land the LOW/NONE-risk instructions now (PI-2, PI-7, PI-8 through PI-14, PI-16, PI-17 — 15 of 17), hold PI-1, PI-3, PI-4, PI-5, PI-6, PI-15 and CP-1/CP-3/CP-6 until the fabrication-passage correction lands in the md, then re-run this same diff process against the corrected md before porting those.
