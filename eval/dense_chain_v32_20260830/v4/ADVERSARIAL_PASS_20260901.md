# Adversarial pass — campaign claims (2026-09-01)

Method: independent re-derivation from raw artifacts only (fresh code, no
campaign analysis scripts, no summary JSONs trusted). Every number below was
recounted from rescored.jsonl / checkpoints / receipts.

## CONFIRMED (attacks failed — numbers re-derive exactly)

- **All ten curve totals**: 479/475 (Opus), 476/474 (grok), 471 (GLM-5.3),
  436 (DSv4Pro), 455 (Sol), 93 (Nemotron), 460/465 (xhigh). 500 rows each,
  0 duplicate ids, 0 empty verdicts (one exception, W-2 below).
- **Substrate byte-identity across ALL 11 runs**: materialized_all sha
  a8bfd9d239f5, facts_all sha 076108c46593 — every reader got the identical
  chain. The curve is same-substrate by construction, now proven by hash.
- **Cross-judge study**: 493/500 and 493/500 agree (98.6/98.6%), gpt_only
  7/5, glm_only 0/2 — re-derived with independent code.
- **Both-pass-stable floors**: Opus 473, grok 471 — exact.
- **Judge controls**: 1.00 positive / 1.00 negative in every control receipt
  across all runs; Opus pair 24/24 both passes.
- **Staleness quarantine**: opus pass1 v1 vs v2 differ on 190 rows; v2 (479)
  is the quoted judge, v1 (289) quarantined. Correct.
- **GLM-5.3 datapoint apparatus**: substrate sha identity, 0/257 facts-hash
  mismatches, 0 missing Answer lines, response lengths ≥ Opus (no
  truncation), miss attribution 11 hard / 14 specific / 4 mixed.

## WEAKENED (real findings, ranked)

- **W-1 — the Opus headline contains a fabrication-toward-defective-gold
  point on BOTH passes.** gpt4_731e37d7 (dossier Class A: gold $720 requires
  a $500 no packet evidence contains; evidence-faithful answer is $220):
  Opus answered **$720 on both passes** and was scored correct — the exact
  hazard the dossier's own control datum documents (gemini scored CORRECT
  for the same fabrication). Offsetting: 370a8ff4 (Class B, gold 15 weeks,
  evidence-faithful 11): Opus answered 11 on both passes and lost the point.
  Net zero per pass. Adjudicated band: ex-fabrication 478/474 (pair 476);
  restored 480/476 (pair 478); raw 479/475 (pair 477).
  **The TIE claim is robust across all three stances (476/477/478 vs 478).
  "Pass 1 exceeds the published SOTA outright" is NOT — under ex-fabrication
  it is 478 = exact tie.** The paper discloses §6.3 adjudication for the
  grok pair only; the Opus headline section carries no defect-row
  disclosure. Fix: one sentence mirroring the grok disclosure.
- **W-2 — xhigh_pass1 contains one silent-False empty-raw verdict**
  (gpt4_fe651585_abs, recorded False on an empty verdict channel) inside the
  quoted 460 — the same artifact class repaired in the GLM judge study.
  Route is closed, but the number is quoted in the paper's table; under
  repair it could read 461. Fix: re-judge that row or footnote it.
- **W-3 — "verified published state of the art" overstates the Chronos
  basis.** Chronos High 478 (arXiv 2603.16862) is source-verified (located,
  per-type decomposed: we beat it on multi-session 119 vs 118) but not
  apparatus-verified — their harness/judge, not ours. The 2026 reproduction
  literature (published-vs-observed gaps) applies to everyone. Fix: say
  "published," not "verified," or footnote the distinction.

## OPEN (not closable from artifacts)

- Chronos apparatus parity (would require reproducing their system).
- SSP judge header sentence is reconstructed, not survey-verbatim (stated in
  every receipt; 30 rows; bounded).

## Statistical framing check

477±2 is the observed pass spread, not a CI. Binomial SE per pass ≈ 4.9,
pair-mean SE ≈ 3.5 — the true interval is WIDER than stated, which makes the
tie claim more robust, not less. No change needed.

## RESOLUTION (2026-09-01, same day — all three fixes landed)

- **W-1 FIXED**: paper headline section now carries the Opus defect-row
  disclosure (tex+md): "exceeds ... on the raw score" replaces "outright";
  adjudicated band 478/474–480/476 stated; tie-holds-in-every-stance sentence
  added, mirroring the §6.3 grok disclosure.
- **W-2 FIXED — and the number moved**: diagnosis showed the empty verdict was
  READER-RESUME STALENESS, not a judge artifact — the reader rewrote
  gpt4_fe651585_abs 11 minutes AFTER the judge scored it on an empty response
  (attempts: 0). Exactly one row affected (the other 499 verdicts pre-date
  their reader rows). Surgical v2 re-judge (judge_gpt4o_v2: 499 frozen
  verdicts carried, fresh controls 12/12 + 12/12, official
  gpt-4o-2024-08-06, resolved snapshot exact): fresh verdict True.
  **xhigh_pass1: 460 → 461/500** (ans 434/470, abs 27/30). Paper updated
  everywhere: table 461/465, regression −15/−9, losses 19 (4 flips + 15
  over-skepticism), Wilson 461 [89.5%, 94.2%], staleness-repair note added.
  The xhigh regression conclusion is UNCHANGED (still a measured regression).
- **W-3 FIXED**: abstract "verified published state of the art" → "published
  state of the art" (tex+md); the §4 "verified at source" qualifier kept
  (it is the accurate statement of what was done).

PDF rebuilt. All edits in tex+md+pdf triple.
