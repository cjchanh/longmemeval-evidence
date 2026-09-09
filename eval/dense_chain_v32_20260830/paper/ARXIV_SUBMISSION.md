# arXiv submission draft — not submitted

Prepared 2026-09-01; revised 2026-09-08 for v1.3. Nothing here has been sent anywhere.

**Title:** Auditable Long-Term Memory: A Deterministic Retrieval Chain Measured at 479/475 of 500 on LongMemEval-S Under the Official Judge

**Authors:** Christopher J. Chanhnourack (Centennial Defense Systems)

**Primary category:** cs.CL (Computation and Language)
**Cross-list:** cs.IR (Information Retrieval); cs.AI

**Comments field:** Technical report, v1.3, 10 pages. Evidence repository (reader outputs, judge verdicts, control records, judge harness): https://github.com/cjchanh/longmemeval-evidence (MIT). Re-scoring any run under the official judge costs about $1.28.

**License:** operator's choice at submission (arXiv default non-exclusive license is sufficient for a technical report).

**Abstract (synced from the live tex, 268 words; arXiv limit 1920 characters — this is 1821 characters):**

We report 479/500 and 475/500 across two independent full passes on LongMemEval-S (Claude Opus reader via an unpinned CLI alias; a same-day probe resolved it to claude-opus-5, §5.3) under the benchmark's official GPT-4o judge, against a published state of the art of 478/500 (95.60%, Chronos High, PwC, arXiv 2603.16862) — one pass above it, one below: indistinguishable from it within the instrument's measured noise band. A second, grok-4.6 reader configuration measured 476/474 on the identical substrate. Ex-dossier (eight gold-defect/boundary rows removed), grok leads Opus 475/474 vs. 474/471. The system is a deterministic retrieval chain — dense retrieval, cross-encoder reranking, a coverage-first packet compiler, and mechanically extracted reasoning scaffolds, all deterministic code validated by negative controls — with a replaceable LLM reader confined to the final answering step. At margins of a few questions, measurement is the result: the Opus headline pair's entire spread traced to eight verdict-flip rows; cross-judge agreement is 98%; we observed official-judge verdict flips on byte-identical answers; and a maximum-reasoning-effort reader variant scored lower (461/465), with 4 of its 19 per-pass losses being the same answer text judged oppositely. We release every reader output, judge verdict, and control receipt, plus an error dossier that attributes all remaining failures — including a strict gold-answer defect, an improvement stage rejected by our own negative control, and the routes that did not work. The headline score is not independently reproducible: packets and the judge are; the method is not. Every component that moves the score was tuned against the same 500 LongMemEval-S questions; no held-out split is reported. A full re-score under the official judge costs about $1.28.

## Before submitting

- cs.CL endorsement: granted 2026-09-04 (arXiv help, "You now can submit to cs.CL").
- The evidence-repository URL is in §8 and the footer (v1.2, public, fresh-clone verified). Tag the source-tree release commit.
- Upload the tex source (arXiv compiles it; the paper uses standard packages: geometry, booktabs, microtype, parskip, titlesec, xcolor, hyperref, helvet — all on arXiv's TeX Live).
- Ancillary files are optional; the evidence repository is the canonical artifact.
