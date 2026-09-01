# LongMemEval-S: 479/475 per 500 under the official GPT-4o judge
## A deterministic, audit-first retrieval chain — statistical tie with the published SOTA, one pass above

Date: 2026-09-01 (updated from 2026-08-31 grok-pair version) · Centennial Defense Systems / Archivist
Evidence commits: 477726726 (v3.3 chain + attribution), 04eb64763 (v3.4 pair + ladder),
ad43cc99a (reader curve + adversarial pass + kimi datapoint)

---

## Headline (stated exactly)

**v3.4 chain, Claude Opus reader: 479/500 and 475/500 (477 ± 2) across two
independent full passes — judged by gpt-4o-2024-08-06 under the LongMemEval
paper rubric. Statistical tie with the published SOTA, one pass above it on
the raw score; held to the pre-registered two-pass bar.** The grok-4.6-high
configuration measures 476/474 on the identical substrate. Ex-dossier (gold
defect/boundary rows removed), grok leads 475/474 vs 474/471 — the Opus
margin is gold-idiom reading, disclosed in the paper. The Opus reader is the
unpinned CLI alias `opus`; a same-day probe resolved it to `claude-opus-5`
(one generation newer than Chronos's Opus 4.6), disclosed in the paper.
A pre-release re-judge of the frozen pass-1 checkpoint under the same
official judge (clean out-dir, fresh controls 12/12) returned 478/500 —
answerable identical, three verdict flips on identical text — so "one pass
above" sits inside the judge's own flip floor; the tie is the claim.
Reader curve on the
same substrate: 93 → 436 → 455 → 465 → 471 → 476/474 → 479/475.

Verified leaderboard (raw /500, fetched at source):

| System | Raw /500 | Notes |
|---|---|---|
| Chronos High (arXiv 2603.16862) | **478** | published SOTA (Opus 4.6-generation reader); single run, judge snapshot not stated |
| **This chain (v3.4, Opus reader)** | **479 / 475** | two independent passes, spread stated, controls 12/12 every run |
| This chain (v3.4, grok-4.6-high) | 476 / 474 | same substrate, second configuration |
| Mastra OM | 468 | their "94.87%" is task-averaged, not raw |
| OMEGA | 466 | GPT-4.1 judge — not rubric-comparable |

(agentmemory "V4" claims 481 on an unreviewed GitHub README; excluded until
reviewable.) We beat Chronos on multi-session (119 vs 118); the 4-row gap is
3 knowledge-update + 1 SSP-abstention row.

- **Retraction.** An earlier draft of this document claimed "475/500 and
  475/500, both passes agreeing" via a self-consistency (SC) step. That
  number is WITHDRAWN and not claimed in any form: adversarial review showed
  the SC construction wrote one majority verdict into both passes (an
  arithmetic identity, not two agreeing measurements), selected flip rows
  judge-conditionally, and added no information (the submitted texts equaled
  the original pass answers). The artifacts remain committed (sc_flip/) as a
  record; no SC number appears in our claims.
- With the two strict gold defects adjudicated (see dossier), the raw pair
  reads 478/476. We report this as an adjudication scenario, not a score.
- An xhigh-effort reader pair (same chain, grok reasoning-effort xhigh;
  NC-gated: 0/58 correct-row flips) is running at press time; its result
  will be reported as its own two-pass number, never merged into this one.

Independent-reader control (Sol, GPT-5.6 via OpenCode OAuth, identical v3.4
packets+facts): **455/500** — below its own 468 on the prior facts revision.
Attribution: ~half Sol per-run variance (net −5 on byte-identical non-facts
rows), ~half a mild negative v3.4-facts × Sol interaction (net −5), abs −3;
judge controls 24/24. Conclusion: the packet layer is reader-robust in the
455–476 band, the v3.4 operator rules are tuned to the grok reader, and
grok remains the only measured 475-class reader. A second Sol pass was
deliberately not run (it cannot reach the bar; variance ±5 does not bridge
20 points). Sol also solved 6 of grok's 18 stable-wrong rows — reader
complementarity that motivates the ensemble/verifier roadmap, not a score.

## Why this number is trustworthy

1. **Single ruler.** Every number in this document is judged by
   gpt-4o-2024-08-06 with the paper's rubric constants, api transport,
   frozen prompt templates (sha-pinned), live positive/negative judge
   controls (12/12 required per run). Cost: ~$1.28 per 500-row rescore.
2. **Two full passes, spread stated.** The reader (grok-4.6-high) is
   nondeterministic; a single run at the margin is not a promotable number.
   Rule: two full passes agreeing, or one number with a stated ± spread.
3. **Judge variance measured, not assumed.** GLM-5.3-Flash re-judged both
   passes on identical rows: 98.2% / 97.8% agreement; GLM strictly stricter
   (7 GPT-only-correct vs 2–4 GLM-only-correct per pass). One abstention row
   received opposite verdicts on a byte-identical answer across runs —
   the judge is the measurement floor at this margin, and we log it as such.
4. **Negative controls at every layer.** Gold-permutation and question-ID
   sabotage on the compiler (byte-identical output required); a 60-row
   baseline-correct control set replayed under every facts revision; a
   verifier stage was BLOCKED from integration when its negative control
   showed it destroyed 11/59 correct rows — the frozen acceptance rule
   caught it before it touched the headline.
5. **Attribution before headline.** All 29 GPT-4o-rejected rows from the
   v3.3 pair were individually attributed; v3.4's rule changes were derived
   from that forensic and validated on a targeted two-pass replay (gate:
   zero both-pass control regressions, abstention floor, zero reader errors)
   before the full pair ran.

## The chain (what actually produces the score)

Deterministic, local, replaceable-reader architecture:

1. **Dense retrieval** over 500-question haystacks → ranked session pools.
2. **Cross-encoder rerank** (bge-reranker-v2-m3, chunk = date header + turn,
   session score = max chunk; rank-deterministic, MPS fp16).
3. **Coverage-first packet compiler** — 16 sessions / 40k-token budget per
   question; baseline top-10 prefix byte-invariant; term-preserving
   extraction; deterministic extension ordering. Gold-complete packets:
   462/470 (pool ceiling 468).
4. **Deterministic reasoning operators** ("facts scaffold") — canonical
   user-only recency domain with clock-granular tie keys, value-preference
   invariant, candidate enumeration + quantity roll-up for counts,
   granularity/units and event-anchor rules (prompt v3.4-facts-20260831).
   Every operator is code, not prompt vibes: in-code coupling invariants
   raise OperatorError on internal inconsistency.
5. **Reader** — replaceable by construction. Measured on identical packets:
   grok-4.6-high 476/474 · Sol (GPT-5.6) 455 · gemini-3.7-flash partial 89.3%
   (weaker readers lose points; the packet+operator layer carries the score).
6. **Judge** — official GPT-4o, as above.

## Single-ruler ladder (all GPT-4o-judged)

| Chain stage | Score /500 |
|---|---|
| Baseline (Flash reader, v2 prompts) | 452/499 (90.6%; 1 row unjudged in that run) |
| Sol reader, v3.3 chain | 468 (93.6%) |
| v3 chain (CE rerank, grok) | 473 (94.6%) |
| v3.3 official pair | 471 / 470 |
| **v3.4 official pair** | **476 / 474** |

The +24-point climb decomposes into audited bricks: reranker extension
ordering (+~5 gold-complete packets), facts operators (+recency/count/value
classes), v3.4 granularity & anchoring rules (+9 stable gains vs v3.3, −5
uncontrolled losses, net +4 stable, measured).

## What still fails (24 answerable rows), attributed

- **2 strict gold defects** — gold unreachable without fabrication ($720
  requiring a nonexistent $500 and an impossible date) and a gold
  arithmetic error (15 weeks vs a dated 81 days). A third candidate (a
  chandelier scored as "jewelry") was downgraded to boundary after an
  independent-reader control. Full evidence: GOLD_DEFECT_DOSSIER.md. A weaker
  reader that HALLUCINATED the missing $500 was scored correct — the judge
  rewards gold-matching over evidence fidelity; we did not take that trade.
- **~5 boundary-semantics rows** — both readings defensible (plan-vs-done,
  does-the-offered-house-count); documented, claimed as worth 0.
- **~4 true reader-cognition misses** — the reader commits to an
  evidence-backed distractor. Two verifier designs (cite-or-revise;
  enumerate-then-adjudicate) were built and honestly retired: the first
  failed its negative control, the second recovered 0 (the residue is
  semantic, not evidential).
- **Retrieval/packet coverage, measured precisely** — an entity-linking
  arm (alias mining + query expansion) was built, tested (17/17), and
  honestly retired: zero of its added sessions are gold; the presumed
  alias-mismatch losses do not exist at the pool stage. The real coverage
  facts: 19/23 failing rows have gold-complete packets; 3 rows lost a gold
  session that sits IN-POOL at CE rank 8/14/33 — a compiler-ordering loss.
  A full extension-order sweep (pool/rerank-first/rrf/rerank-interleave vs
  the shipped ce) confirmed ce is globally optimal (462 gold-complete; best
  alternative 454) — those 3 rows are not recoverable by any global
  ordering without losing more elsewhere. 1 further row's gold never
  reached the pool (retrieval ceiling).
- Remainder: measured reader/judge flip noise (8 pair flips, all attributed).

## Reproduction kit

- Judge: scripts/rescore_gpt4o_judge.py (frozen rubric, sha-pinned templates,
  api key file, fail-closed 401/403, control gate). ~$1.28 per 500 rows.
- Chain: run_v34_full.sh (compile → materialize → facts → read → judge),
  deterministic at every pre-reader stage; verification report includes
  determinism, gold-permutation, prefix-superset, budget, and qid-sabotage
  gates.
- All checkpoints, judge verdicts, control receipts, and attribution tables
  are committed under eval/dense_chain_v32_20260830/ and published at
  https://github.com/cjchanh/longmemeval-evidence (MIT; RELEASE_MANIFEST.md,
  449 files, sha256 each; fresh clone verified 449/449).

## Release boundary

Released: responses, judge kit, verdicts, attribution, dossier, this document.
Held: retrieval/compiler internals ship as pinned artifacts + receipts, not
as annotated source (the sauce is the operator layer and compiler ordering;
its outputs are fully verifiable without its internals).
