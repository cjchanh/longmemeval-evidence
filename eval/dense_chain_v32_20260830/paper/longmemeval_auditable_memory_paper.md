# Auditable Long-Term Memory: A Deterministic Retrieval Chain Scoring 479/475 of 500 on LongMemEval-S Under the Official Judge

**Christopher J. Chanhnourack** — Centennial Defense Systems (Archivist)
*Technical report, September 1, 2026 — v1.2*

---

## Abstract

We report **479/500 and 475/500 across two independent full passes on
LongMemEval-S** (Claude Opus reader; CLI alias resolving to `claude-opus-5`, §5.3) under the benchmark's official
GPT-4o judge, against a published state of the art of 478/500
(95.60%, Chronos High, PwC, arXiv 2603.16862) — one pass above it, one
below, a statistical tie whose spread sits inside the instrument's
measured noise band. A second, grok-4.6 reader configuration measured
476/474 on the identical substrate. The system is
a deterministic retrieval chain — dense retrieval, cross-encoder
reranking, a coverage-first packet compiler, and mechanically extracted
reasoning scaffolds, all deterministic code validated by negative
controls — with a replaceable LLM reader confined to the final answering
step. At margins of a few questions, measurement is the result: the Opus headline pair's
entire spread traces to eight verdict-flip rows; cross-judge agreement
is 98%, we observed official-judge verdict flips on byte-identical
answers, and a maximum-reasoning-effort reader variant scored *lower*
(461/465) — with 4 of its 19 per-pass losses being the same answer text
judged oppositely. We release every reader
output, judge verdict, and control receipt, plus an error dossier that
attributes all remaining failures — including a strict gold-answer
defect, an improvement stage rejected by our own negative control, and
the routes that did not work. A full re-score under the official judge
costs about $1.28.

## 1. Introduction

Long-context memory benchmarks are typically reported as single numbers
from single runs, judged by an LLM, with no disclosure of run-to-run or
judge variance. At the top of a leaderboard, where entries are separated
by a handful of questions out of 500, this practice makes the ranking
partially an artifact of measurement noise.

This report makes two claims:

1. **A capability claim.** A deterministic, auditable retrieval chain —
   in which the language model is confined to a replaceable reader role —
   measures 479/475 per 500 on LongMemEval-S across two independent full
   passes — pass 1 above the published state of the art (478), the pair a
   statistical tie with it, with overlapping confidence intervals and
   per-run variance comparable to the gap.
2. **A methodology claim.** The apparatus that produced the number is the
   more important contribution: every stage below the reader is
   deterministic code validated by negative controls; the promotion rule
   (what counts as a reportable number) was frozen before the deciding
   run; measurement noise from both the reader and the judge is quantified
   and disclosed rather than absorbed into the headline.

The system under test is the retrieval core of Archivist, a local-first
conversational memory product. Nothing in the chain is benchmark-specific
except the evaluation harness itself.

### 1.1 Related work

Agentic memory systems (MemGPT, Packer et al., 2023; and production
systems such as Mem0 and Zep) focus on memory *stores* and management
policies; our contribution is orthogonal — determinism below the reader,
with the store fixed. Long-term memory benchmarks include LongMemEval
(Wu et al., 2024), used here, and LoCoMo (Maharana et al., 2024); we
evaluate one benchmark and claim no cross-benchmark generality (§7).
The retrieval stack follows the retrieve-and-rerank tradition (cross-
encoder reranking: Nogueira & Cho, 2019; BGE-M3 family: Chen et al.,
2024); reciprocal rank fusion (Cormack et al., 2009) is among the
extension-ordering baselines swept in §3.3. On measurement: a self-consistency
step (Wang et al., 2023) was built and later withdrawn when internal
review showed its two-pass framing was a derived identity (§4.4); our judge-variance study operationalizes known LLM-as-judge
agreement concerns (Zheng et al., 2023); and the two-pass reporting rule
answers the single-run reporting critique of Dodge et al. (2019).

## 2. Benchmark and evaluation protocol

**LongMemEval-S** (Wu et al., 2024) contains 500 questions over long
multi-session chat histories: 470 answerable questions across six types
(single-session-user, single-session-assistant, single-session-preference,
multi-session, temporal-reasoning, knowledge-update) and 30 abstention
questions
(`_abs`) whose correct behavior is to decline to answer. Each question
carries a haystack of ~40–60 sessions with timestamps; evidence for a
question may be spread across several sessions recorded weeks apart.

**Judge.** We use the benchmark's official protocol: GPT-4o
(`gpt-4o-2024-08-06`) with the paper's rubric templates. One header
sentence of the single-session-preference template was reconstructed from
the benchmark's published rubric text; the templates as used are SHA-256
pinned (`9c9d67fab129…`) and released verbatim, so the reconstruction is
auditable rather than asserted. Every scoring run executes 12 live positive and 12 live
negative control verdicts against a 0.9 pass threshold (preference rows
are excluded from the positive control arm because their rubric is the
reconstructed one); every run in this report returned 12/12 and 12/12.
The harness records the resolved model snapshot per verdict and fails
closed on authentication errors. A full 500-row re-score costs ≈ $1.28.

**Comparison point (verified at source, 2026-08-31).** The published
raw-score state of the art is **Chronos High: 478/500 (95.60%)** (PwC,
arXiv 2603.16862, Mar 2026; generator Claude Opus 4.6, LongMemEval judge
protocol, per-category table published — their Table 2 and Appendix A
Table 4). Two widely-quoted higher
percentages are not raw-comparable: Mastra OM's "94.87%" is a
category-unweighted average — their own per-category counts sum to
**468/500 raw** (generator gpt-5-mini) — and OMEGA's "95.4%" is likewise
task-averaged with raw 466/500, judged by GPT-4.1 rather than the
canonical judge. One higher claim (481/500, "agentmemory V4") exists in
an unreviewed personal repository; we note it without treating it as the
published bar. Reader/generator tier varies freely across all published
entries (GPT-4o through Opus 4.6; our headline reader resolves to Opus 5, §5.3); we follow the field convention of
reporting our strongest configuration alongside the full reader ladder.

## 3. System architecture

The chain has five stages. Stages 1–4 are deterministic: byte-identical
outputs across runs are enforced by verification gates, not assumed
(verified on the pinned environment; hardware and library versions are
recorded in the release).

**3.1 Dense retrieval.** Per-question dense embedding retrieval over the
haystack produces a ranked candidate pool (local inference; pool ceiling:
468/470 questions have all gold sessions somewhere in the pool).

**3.2 Cross-encoder reranking.** A cross-encoder
(`BAAI/bge-reranker-v2-m3`) scores each candidate session against the
question. Sessions are chunked (date header + turn); the session score is
the maximum chunk score. Scoring is rank-deterministic (fp16, fixed batch
size, tie-break by prior rank).

**3.3 Coverage-first packet compilation.** For each question a reading
packet is compiled under a hard budget (16 sessions / 40k proxy tokens):
the dense baseline top-10 is preserved as a byte-identical prefix
(invariant R1), remaining slots are filled in cross-encoder order with
term-preserving extractive compression, and budget overruns drop the
lowest-ranked extension first. The compiler is validated by determinism
(two compiles byte-identical), a gold-permutation negative control
(shuffled gold answers must not change output), a question-ID sabotage
control (renamed IDs must not change output), and budget accounting.
Packets are gold-complete for 462/470 questions. A post-hoc sweep of all
five extension-ordering policies confirmed the shipped ordering is
globally optimal (462 vs 454 for the best alternative).

**3.4 Deterministic reasoning scaffolds ("facts").** For questions whose
type benefits from mechanical reasoning (240 of 470), the chain emits a
deterministic evidence index computed from the packet: session chronology,
a canonical user-statement recency domain with clock-granular tie keys, a
value-preference invariant (statements carrying candidate values outrank
bare recency), candidate enumeration with quantity roll-up for counting
questions, and granularity/unit and event-anchor rules (contract
`v3.4-facts-20260831`). Scaffolds are code with in-code coupling
invariants that raise on internal inconsistency.
The scaffold is gold-blind and question-ID-independent by construction.

**3.5 Replaceable reader.** The packet, scaffold, and question go to an
LLM reader. The reader is deliberately replaceable; we measure the chain
under three readers (§5.3). The headline pair uses the Claude Opus
reader over the CLI lane (§5.1); `grok-4.6-high` and GLM-5.3 are the
secondary readers (§5.3).

## 4. Measurement methodology

**4.1 Two-pass rule (pre-registered).** A nondeterministic reader means a
single full run at a one-point margin is not a reportable number. Our
promotion rule, adopted two days before the deciding experiment: a
headline requires *two full passes agreeing, or one number with a stated
± spread from measured flip variance*.

**4.2 Judge variance is measured, not assumed.** We re-judged both
official passes with a second judge (GLM-5.3-Flash) on identical rows:
agreement 98.2% / 97.8%; the second judge was strictly harsher (7 rows
per pass where only GPT-4o accepts, vs 2–4 where only GLM accepts). We
also observed the official judge returning opposite verdicts on a
byte-identical answer across runs. At a one-point margin, the judge is
the measurement floor; we log such rows rather than resolve them by
re-rolling.

**4.3 Negative controls at the improvement layer.** Every proposed
improvement runs against a 60-row control set of baseline-correct
questions before integration. This rule has teeth: a verifier stage
(cite-or-revise) that recovered 3 previously-wrong rows was **rejected**
because the control replay showed it flipped 11 of 59 correct drafts to
wrong (§6.2). The frozen acceptance rule — zero control flips — blocked
it from ever touching the headline, while the reader-tier upgrade in this
report passed that same control with zero flips before its full pair was
launched.

**4.4 Self-consistency tie-break (built, then withdrawn).** The raw
grok pair measured 476/474, and its entire spread came from eight rows
that flipped verdicts between passes (reader or judge nondeterminism).
A tie-break
rule frozen before any additional read (`SC_RULE.json`) gave each flip row
three more reads with a five-vote majority. **The resulting number was
WITHDRAWN from any claim.** Internal review showed the construction wrote
one derived verdict into *both* passes — an identity, not two agreeing
measurements — and that its flip-row selection was judge-conditioned rather
than gold-blind as the rule had asserted. The artifacts remain released as
a record of what was built; **no self-consistency number is claimed
anywhere in this report**, and none should be quoted from the released
artifacts either.

**4.5 What we did not do.** No per-question prompt tuning against gold;
no judge re-rolling; no selective reporting (the failed routes are in
§6); no counting of the gold-defect adjudication in any headline number.

## 5. Results

### 5.1 Headline

| Configuration | Pass 1 | Pass 2 |
|---|---|---|
| **v3.4, Claude Opus reader (CLI lane)** | **479/500** | **475/500** |
| v3.4, grok-4.6 high (raw pair) | 476/500 | 474/500 |
| v3.4, grok-4.6 xhigh (agentic transport) | 461/500 | 465/500 |
| v3.4, Claude Opus reader — ex-dossier (8 gold-defect/boundary rows removed, §6.3) | 474/492 | 471/492 |
| v3.4, grok-4.6 high — ex-dossier (same 8 rows removed) | 475/492 | 474/492 |

Ex-dossier, grok leads Opus 475/474 to 474/471: the Opus margin on the full
set is carried by gold-idiom reading on dossier rows (§5.2, §6.3), not by
evidence reading on ordinary rows. Both are reported because the headline is
the official-judge score and the ex-dossier pair is what the evidence
supports.

The Opus pair is the headline: pass 1 exceeds the published SOTA (478)
on the raw score; the pair's both-pass-stable floor is 473 (vs. the grok pair's
471); pass 1 is perfect on three of six answerable types
(single-session assistant, user, and preference). Its spread (8 flip
rows: 6 lost — including 2 abstentions and 2 rows our dossier already
lists as flip-prone — 2 gained) matches the flip-noise structure
measured on every other pair in this report. Under the pre-registered
two-pass rule this is a **statistical tie with the published SOTA, one
pass above it**, not a clean beat: we state 477±2 and decline the
stronger claim our own bar forbids (a pre-release re-judge of pass 1 under
the same official judge returned 478 — three verdict flips on identical
text, §8 — so even "one above" is a judge roll). The two rows §6.3
documents individually — the $720 workshop row and the 15-weeks row — sit
inside this pair as well: one is scored correct because this reader counts a
user-stated $500 fee whose event is dated outside the question's four-month
window (a boundary row, not a fabrication — §6.3), one is lost to fidelity
(the evidence-faithful answer contradicts defective gold) — net zero per pass. Adjudicating the single
strict defect raises the Opus pair to 480/476 (479+1 / 475+1); the tie with
the published state of the art holds in every stance. Judge controls 24/24 in both
passes. A 25-row probe preceded the pair (11/25 stable-wrong recovered,
including one row no prior reader had ever solved).

The xhigh variant is a measured regression (−15/−9), reported in full.
Its gate evidence had looked favorable — a 25-row probe on the high
pair's wrong set recovered 9, and a 60-row negative control on
baseline-correct rows showed zero flips — but the full pair exposed the
gates' limits: only 4 probe recoveries held, and the true correct-row
flip rate (~3.4%) was small enough that a 60-row control had a ~13%
chance of showing zero flips. Row-level attribution of pass 1's 19
losses: 4 are judge flips on answer text identical to the high run's,
and 15 are a consistent over-skepticism signature — wrong abstentions on
answerable rows, over-filtered counts, hedged golds. More reasoning
effort made the reader second-guess correct evidence. (One v1 loss was
a staleness artifact, not a reader loss: the reader resumed one row
eleven minutes after the judge had scored it on an empty response; a
surgical v2 re-judge under fresh 12/12 controls restored it, 460 → 461.)

Raw grok-pair detail (the pair the self-consistency rule was frozen over):
answerable 450/470 and 447/470; abstention
26/30 (pass 1) and 27/30 (pass 2). A self-consistency tie-break over the
raw pair's 8 flip rows was constructed under a frozen rule and later
WITHDRAWN from any claim: internal review showed it wrote one derived
verdict into both passes (an identity, not two agreeing measurements)
and its flip-row selection was judge-conditioned. Its artifacts remain
released; no SC number is claimed. Judge controls passed in every scoring run
(scaled to run size; 24/24 on full passes). Under
the gold-defect adjudication scenario (§6.3) that grok pair reads 477/475
(476+1 / 474+1, the single strict defect); we
report that as a scenario, never as the score.

### 5.1.1 Per-question-type breakdown (official GPT-4o judge)

| Question type | n | Raw pass 1 | Raw pass 2 | xhigh p1 / p2 | Opus p1 / p2 |
|---|---|---|---|---|---|
| single-session-assistant | 56 | 56 (100.0%) | 56 (100.0%) | 55 / 55 | 56 / 56 |
| single-session-user | 64 | 63 (98.4%) | 63 (98.4%) | 61 / 60 | 64 / 64 |
| knowledge-update | 72 | 70 (97.2%) | 71 (98.6%) | 69 / 70 | 69 / 70 |
| single-session-preference | 30 | 29 (96.7%) | 29 (96.7%) | 25 / 25 | 30 / 28 |
| temporal-reasoning | 127 | 122 (96.1%) | 122 (96.1%) | 121 / 123 | 123 / 123 |
| multi-session | 121 | 110 (90.9%) | 106 (87.6%) | 103 / 106 | 110 / 109 |
| abstention | 30 | 26 (86.7%) | 27 (90.0%) | 26 / 26 | 27 / 25 |
| **Total** | **500** | **476** | **474** | 461 / 465 | **479 / 475** |

Five of six answerable types are pass-stable to within one question; the
raw pair's entire answerable spread is one type (multi-session,
110 → 106, partially offset by knowledge-update 70 → 71). On the abstention-folded basis of Chronos's per-category table
(n: KU 78, MS 133, SSA 56, SSP 30, SSU 70, TR 133 — their Appendix A),
our pass-1 deficit is −3 knowledge-update (75/78 vs. their 78/78), offset
by +2 multi-session (120/133 vs. 118/133), +1 single-session-user (70/70
vs. 69/70) and +1 temporal-reasoning (128/133 vs. 127/133), with
assistant and preference level — net **+1**, which is 479 vs. their 478.
Pass 2 carries the same −3 knowledge-update, ties on multi-session
(118/133), and loses −2 on preference (28/30) — net **−3**, which is 475
vs. 478. So we exceed them on multi-session in pass 1 and match it in
pass 2; the pass-to-pass difference is preference, not multi-session. The residual
concentrates where the benchmark itself is hardest to score:
multi-session aggregation (which holds the reclassified boundary row of
§6.3; the one surviving strict gold defect is temporal-reasoning) and
abstention (where we measured official-judge verdict flips on identical
answers).

*Note on the gemini partial (§5.3): its 189 scored rows cover
single-session-user 64/64 (100%), multi-session 73/83 (88.0%), and
single-session-preference 21/30 (70.0%) only — a type-ordered prefix,
not a sample — and contain no temporal-reasoning, knowledge-update, or
single-session-assistant rows.*

### 5.2 Ablation ladder (single ruler: official GPT-4o judge)

| Stage | Score /500 |
|---|---|
| Dense retrieval + flat reading (Flash reader, v2 prompts) | 452/499 (90.6%)¹ |
| + chain, v3.3 operators, Sol reader | 468 |
| + cross-encoder rerank (v3, grok reader) | 473 |
| + v3.3 operators (official pair) | 471 / 470 |
| + v3.4 operators (official pair, grok high) | 476 / 474 |
| + reader xhigh + agentic transport | 461 / 465 (regression) |
| **+ reader tier: Claude Opus, same substrate** | **479 / 475** |

Ex-dossier (all eight gold-defect/boundary rows removed from both readers):
grok leads 475/474 vs. Opus 474/471 — Opus's net margin over grok is carried
by gold-idiom reading on dossier rows, not by evidence reading on ordinary
rows. The Opus reader is the CLI alias `opus` (claude-cli lane,
subscription), not a pinned snapshot: no run artifact records the run-time
resolution, and a same-day probe (2026-09-01, Claude Code CLI 2.1.258; the
runs used 2.1.252) resolved `opus` to `claude-opus-5` — one model generation
newer than the Chronos comparator's Opus 4.6. The grok and GLM readers are
named models. Three of Opus's abstention credits (`2133c1b5_abs`, `c8090214_abs`,
`f685340e_abs`) are premise-repair-then-answer responses the official judge
accepts and the GLM cross-judge rejects; under strict abstention the pair
reads 476/472 — still a tie.

Every rescore in the ladder used the identical frozen judge harness.
¹ One row of the legacy baseline run failed its reader lane and was never
re-read; it is counted as scored-out-of-499 rather than imputed.

### 5.3 Reader robustness

On identical packets and scaffolds: **Claude Opus 479/475**;
grok-4.6-high 476/474;
GPT-5.6 (Sol) 455 — measured decomposition versus its prior-contract 468:
−5 from per-run reader variance on byte-identical non-scaffold rows, −5
from a negative v3.4-scaffold × Sol interaction, −3 on abstention; judge
controls 24/24. DeepSeek V4 Pro 436/500 (29/30 abstention — the best
measured). Nemotron-3.5-Lightning-30B floor probe: 93/500 on identical
gold-complete packets — the chain does not rescue a reader below a
capability threshold. (Controlled for serving artifacts: correctness
barely varies with packet size, and a question-first re-prompt of a
failed row was still ignored in favor of distractor content — the
collapse is model-side, not provider truncation.) A gemini-3.7-flash run reached a 189-row partial before
its lane was retired; the partial is a prefix of a type-ordered file, not
a random sample, so we report it as a bounded signal on the types it
covers rather than a score (§5.1.1 note below). A GLM-5.3 run on the
identical substrate scores 471/500 (445/470 answerable, 26/30 abstention;
official GPT-4o judge, controls 12/12) — a single-pass curve datapoint per
the two-pass rule, not a headline. A Kimi K3 run (the long-context-specialist
family) scores 465/500 (444/470 answerable, 21/30 abstention; same judge,
controls 12/12) — long-context specialization does not transfer to
memory-benchmark dominance on this substrate. The packet and
scaffold layers carry most of the score; reader choice moves it by a few
points. The v3.4 scaffold contract is tuned to the grok reader; we state
this rather than hide it.

## 6. Error analysis: every remaining failure, attributed

Of 470 answerable questions, 25 fail in at least one pass of the
grok-4.6-high pair (pass 1: 20, pass 2: 23; 18 wrong in both). The
buckets below — reader-cognition, gold-defect (1 strict, 7 boundary),
retrieval/ordering (1 pool-miss, 3 ordering), and flip-noise — attribute
those failures; their counts are approximate and do not form an exact
partition of the union, since a flip row can change bucket between
passes. (§6.2's "12 winnable" rows are a cross-cutting subset spanning
these buckets, not a fifth bucket.) Post-attribution:

### 6.1 Reader-cognition residue (~4 rows)
The packet contains the correct evidence; the reader commits to an
evidence-backed distractor. Two verifier designs failed to fix this
honestly (§6.2). The residue is question-boundary semantics (e.g., does
a stated *plan* update a location? does the offered property count as
"viewed"?), not evidence selection.

### 6.2 The verifier that our own control rejected
A cite-or-revise verifier recovered 3/12 winnable wrong rows — and the
mandatory negative control showed it revised 19/59 baseline-correct
drafts, flipping 11 to wrong while repairing none. It was blocked from
integration by the pre-committed acceptance rule. A second design
(draft-blind candidate enumeration + rule-based adjudication) recovered
0/9: on the residue rows the adjudicator reaches defensible-but-not-gold
readings. Both failures are published; they map the limit of
prompting-side repair. They motivate an evidence-testimony layer as
future work.

### 6.3 Gold-answer defects (1 strict, 7 boundary)
Documented row-by-row in the released dossier:
- **Strict B** — gold says "15 weeks" between two user-dated events that
  are 81 days (11 weeks 4 days) apart. Wrong in all four passes of both
  reader configurations.
- **Boundary — the $720 workshop row** (published as strict; reclassified
  after re-auditing the released packet). Gold requires a $500 workshop fee,
  and the user states it: session `answer_826d51da_2`, 2023/02/26 13:37,
  "I paid $500 to attend". Nothing has to be invented to reach gold. What is
  disputed is window membership: both dated mentions place the workshop on
  March 15-16, after the 2023/02/26 question date, attended in the past
  tense. The grok reader excludes the fee and answers $220 → 0 in both
  passes; the headline Opus reader includes it and answers $720 → correct in
  both passes; a weaker gemini-3.7-flash probe likewise included it and was
  scored correct. The judge rewards including the out-of-window item because
  gold includes it — the disclosed window-inclusion point inside 479/475
  (§5.1), not a fabrication point.
- Six further rows are boundary-semantic (defensible readings on both
  sides); we claim nothing for them. One earlier strict candidate was
  *downgraded* to boundary after an independent-reader control showed the
  intended referent was answerable by premise repair. The Chronos authors
  independently document a defect on question `6d550036` (their §3.5,
  alongside a judge-variability example on `75f70248`), consistent with our
  dossier.

### 6.4 Retrieval ceiling and coverage, measured precisely
One row's gold never reaches the candidate pool; three rows lost an
in-pool gold session to packet budget ordering (an ordering sweep showed
no global setting recovers them without losing more). An entity-linking
retrieval arm (alias mining + query expansion) was built, tested, and
retired when measurement showed zero of its added sessions were gold —
the presumed alias-mismatch losses do not exist in this benchmark. The
remaining failures are the eight measured flip-noise rows — reader or
judge nondeterminism on the same substrate, quantified in §5.1 and not
repaired by any construction in this report.

## 7. Limitations

- **No held-out evaluation.** Every component that moves the score — the
  v3.2→v3.4 operator ladder, the extension-ordering sweeps, the packet
  budgets, and the 60-row negative-control set — was developed against the
  same 500 LongMemEval-S questions the headline is measured on, and the
  gold-defect dossier records per-row inspection of gold answers during
  development. Nothing in this report is a test-set number in the held-out
  sense. At a one-to-four-question margin over the published state of the
  art this is the dominant threat to validity; the mitigations we do have
  (deterministic stages with negative controls, two independent full passes,
  every verdict released) bound variance, not overfitting. A held-out run on
  a disjoint question set is the right next measurement and has not been
  done.
- **Margins at this level are not claims of statistical superiority.**
  Wilson 95% intervals: our 479 [93.7%, 97.2%] and 475 [92.7%, 96.6%]
  (grok pair: 476 [93.0%, 96.8%], 474 [92.5%, 96.4%]) vs Chronos's 478
  [93.4%, 97.1%] — overlapping almost entirely. (The xhigh pair sits
  lower: 461 [89.5%, 94.2%], 465 [90.4%, 94.9%].) The intervals of nearby entries
  overlap substantially, and a paired test (McNemar) is not computable
  because no comparison entry publishes per-question verdicts. We claim
  exactly what we measure — two independent full passes under the
  official judge — and our contribution to the comparison is that our
  number is reproduced with variance disclosed; comparison entries are
  single runs.
- **The judge is the floor.** ~2% verdict variance between judges, and
  observed flips on identical answers, bound what any entry at this
  margin can honestly claim.
- **Scaffold-reader coupling.** The v3.4 scaffold is tuned to one reader
  family; portability of the exact number across readers is a few points
  (§5.3), though the chain's ranking of readers is stable.
- **One benchmark.** LongMemEval-S measures a specific memory regime;
  we make no cross-benchmark generality claim.
- **A claim in our own released dossier was wrong and is corrected here.**
  The dossier originally classed the $720 workshop row as gold-unreachable
  without fabrication, on the claim that no $500 workshop fee appeared in the
  evidence; a mechanical re-audit of this release's own published packets
  found that fee stated by the user, so the row is a boundary row (§6.3),
  the strict-defect count is 1 rather than 2, and the adjudication figures in
  §5.1 were recomputed. No verdict changed and the headline 479/475 is
  unaffected — only the classification of a row that was already scored as
  measured. The error and its correction are recorded in the dossier rather
  than removed from it.

## 8. Reproducibility

**The Chronos and Mastra comparator sources are pinned in the release; OMEGA is not.** The Chronos paper (arXiv
2603.16862, PDF and abstract page) and the Mastra Observational Memory page
that supply the 478/500 and 94.87% / 468 raw comparator figures are stored
with SHA-256 digests and a fetch timestamp under
`eval/dense_chain_v32_20260830/comparators/` (see its `MANIFEST.md`), so the
comparison rows in §5.1 can be checked against bytes the release carries.
The OMEGA figure quoted in §5.1 has no pinned source yet; that gap is
recorded in the same manifest.

Released with this report at
<https://github.com/cjchanh/longmemeval-evidence> (MIT). A fresh clone
verifies every `RELEASE_MANIFEST.md` row and re-derives every headline count from
the released verdicts without an API key. The evidence commits in the
footer anchor to the source tree the release was exported from. The
release holds all reader outputs,
all judge verdicts and control receipts for every run in the ladder, the judge harness (frozen rubric, SHA-pinned
templates, fail-closed transport), the SC rule and per-vote records, the
attribution tables, the gold-defect dossier, and the run scripts.
Re-scoring any run under the official judge costs ≈ $1.28 and requires
only an OpenAI API key. The released/held boundary is frozen in
`RELEASE_MANIFEST.md` (one sha256 per released file, regenerated
deterministically by `scripts/build_release_manifest.py`): released are
all reader checkpoints, judge verdicts, control receipts, agreement
matrices, the dossier, the judge harness with its tests and rubric
source, and the reader-lane scripts; held are the retrieval, rerank,
packet-compiler and scaffold-operator sources. The materialized packets and
the v3.4 scaffolds the headline pair consumed are released under
`eval/dense_chain_v32_20260830/packets_materialized/` (gzip; sha256 in its
`MANIFEST.md`), and `scripts/materialize_packets.py` re-derives every packet
byte-for-byte from the released allocation and the MIT benchmark data, so
stage 5 (reader) and the judge are re-runnable by a third party on the exact
text we read. The held stages ship as pinned artifacts with
verification receipts (determinism, gold-permutation,
question-ID-sabotage, budget gates); every judge-side claim is
re-derivable from the released checkpoints and harness alone. The
benchmark data is MIT-licensed (`xiaowu0162/longmemeval-cleaned`), so the
released checkpoints may carry question and gold text.
Judge-side reproduction, run before release: the frozen pass-1 reader
checkpoint was re-judged the same day in a clean output directory with the
identical harness (`gpt-4o-2024-08-06`, resolved snapshot exact, fresh
controls 12/12 and 12/12). Result **478/500**: 497 of 500 verdicts agree
with the quoted 479; answerable is identical (452/470); the three flips are
on byte-identical answer text (`7024f17c` and `031748ae_abs` lost,
`a2f3aa27` gained). The official judge's own flip floor (§4.2) is therefore
measured within a single judge on the headline pass, and "one pass above"
is inside that floor; the tie is the claim. Receipts:
`full-v34-opus_pass1/judge_gpt4o_repro_20260901/`.

## 9. Conclusion

A deterministic, negatively-controlled retrieval chain with the LLM
confined to a replaceable reader measures 479/475 per 500 on
LongMemEval-S — one pass above the published state of the art, the pair
a statistical tie inside the instrument's noise band — under a
measurement discipline that makes
the number defensible at a margin where measurement is usually the
weakest link.
The apparatus generalizes: freeze the promotion rule before the deciding
run, control every improvement against what it might break, measure the
judge, and publish the failures with the successes.

## References

- Wu, D., et al. *LongMemEval: Benchmarking Chat Assistants on Long-Term
  Interactive Memory.* ICLR 2025, arXiv:2410.10813. (benchmark, rubric,
  and judge protocol)
- Sen, S., Lumer, E., Gulati, A., Subbiah, V. K. *Chronos: Temporal-Aware
  Conversational Agents with Structured Event Retrieval for Long-Term
  Memory.* arXiv:2603.16862, Mar 2026. (published SOTA comparator,
  478/500; also independently documents a gold defect on question
  6d550036 consistent with our dossier — their §3.5, which also
  gives a judge-variability example on 75f70248)
- Barnes, T. *Observational Memory: 95% on LongMemEval.* Mastra Research,
  Feb 2026. mastra.ai/research/observational-memory (accessed 2026-08-31;
  task-averaged 94.87%, raw 468/500)
- Packer, C., et al. *MemGPT: Towards LLMs as Operating Systems.* 2023.
  Maharana, A., et al. *LoCoMo.* 2024. (prior long-term-memory systems and
  benchmark, §1.1)
- Nogueira, R., Cho, K. *Passage Re-ranking with BERT.* 2019.
  Chen, J., et al. *BGE M3-Embedding.* 2024.
  Cormack, G., et al. *Reciprocal Rank Fusion.* SIGIR 2009. (retrieval
  components of the chain, §1.1)
- Wang, X., et al. *Self-Consistency Improves Chain of Thought Reasoning.*
  ICLR 2023. Zheng, L., et al. *Judging LLM-as-a-Judge.* NeurIPS 2023.
  Dodge, J., et al. *Show Your Work.* EMNLP 2019. (self-consistency, judge
  variability, and reporting-discipline precedents, §1.1)
- BAAI. *bge-reranker-v2-m3.* (cross-encoder reranker)

---

*Correspondence: Christopher J. Chanhnourack, Centennial Defense Systems.*
*Evidence release: <https://github.com/cjchanh/longmemeval-evidence>.
Source-tree evidence commits:
477726726 · 04eb64763 · ad71321ea · ba805e575 · 08e5784bb · ad43cc99a · 9b0711c39.*
