# v4 parent-thread analysis — 2026-08-31

## Per-type reader matrix (pass-averaged, GPT-4o judge)
| type | grok-high | xhigh | sol | dsv4 |
|---|---|---|---|---|
| abstention | .883 | .867 | .767 | **.967** |
| knowledge-update | **.979** | .965 | .931 | .972 |
| multi-session | **.893** | .864 | .868 | .793 |
| single-session-assistant | **1.000** | .982 | .982 | .982 |
| single-session-preference | **.967** | .833 | .800 | .500 |
| single-session-user | **.984** | .945 | .969 | .938 |
| temporal-reasoning | **.961** | .961 | .937 | .874 |

grok-high is best on ALL six answerable types. "Type-routed 479/500" exists ONLY by
routing abstention rows to dsv4 — which requires knowing rows are abstention rows
(the `_abs` id-suffix) = the id-stem oracle trap. ⛔ NOT a legitimate score.

## Ceilings (11 runs, updated 2026-09-01 after kimi + xhigh-v2)
- Oracle union: 495/500 (5 never-right rows: 0a995998, 370a8ff4, gpt4_15e38248,
  gpt4_2f8be40d, gpt4_e061b84f — includes both strict gold defects' 370a8ff4
  plus two boundary rows; the old 491/9 figure predates kimi + xhigh-v2).
- 14 of Opus's 19 pair-stable-wrong rows solved by ≥1 other reader we ran.
- Flat 4-reader majority: 457 — voting is anti-productive; adjudication required.
- ⚠ Fable 5.1 read-only review (2026-09-01): ex-dossier, grok LEADS Opus
  475/474 vs 474/471 — Opus's net margin is gold-idiom reading on dossier
  rows. Tie is the ceiling at the top of the curve; the measurable frontier
  is the weak-reader end (DSv4 436 / local readers) where levers are 3σ
  visible. Review memory: dense-chain-opus-tie-readonly-review-2026-09-01.md.

## Refusal-consensus abstention rules — MEASURED CLOSED (do not retry)
Rule "abstain iff <readers> all refused", scored over both grok passes:
naive dsv4-only: 476→456 / 474→452. Intersections (ds∧xh1, ds∧xh1∧xh2, ds∧sol,
ds∧sol∧xh1, xh1∧xh2): every variant nets −2 to −4 on BOTH passes; gains ≤1 abs row,
losses always include ec81a493 / ba358f49 / 37f165cf (rows every weak reader refuses
but grok answers correctly). Cross-reader refusal consensus cannot buy abstention
points on this benchmark. The abs lever must be evidence-span sufficiency (W2),
not consensus.

## Standing win path
selector convergence (W1) · sufficiency gate + NC-230 (W2) · dual-read adjudication
upside on 12 recoverable rows (W3) · frozen pilot (W4) · reader-tier $ as insurance.
Promotion: pilot net ≥ +4 target rows, ≤1 control regression → fresh pre-registered pair.

## v3.5 in-text anchors A/B — VERDICT: NULL (not promoted), one red flag (2026-08-31)
119-row live A/B (54 treatment / 65 control, grok-cli high, GPT-4o judge) vs pass1 baseline:
treatment +1, control −2 (noise floor ±2–3). Row-level: the +1 decomposes entirely into noise
and a hazard — gpt4_731e37d7 "gain" = reader now matches DEFECTIVE gold $720 by including the
$500 the dossier proved absent from evidence (dual-year Caution anchors likely shifted an event
into the lookback window; fabrication-toward-gold, claim-excluded row); ba358f49 "loss" = judge
flip on byte-similar refusals; gpt4_7abb270c "gain" = same 6 museums reordered, judge noise.
Single-session-day finding class: no genuine gain. ⛔ v3.5 stays built+committed but UNPROMOTED;
its Caution-row dual-reading can push a reader INTO defective-gold fabrication — paper-worthy
evidence-fidelity datum. Artifacts: v4/anchors/ab_v35/.

## Arm A citation-contract pilot — DO NOT PROMOTE (2026-08-31)
Frozen rule: net ≥+4 TARGET, ≤1 CONTROL regression. Measured: TARGET +2 (6 gained/4 lost),
CONTROL regressions 6. Gate fired REFUSE 24 (LINK_STATED_NO 21) — over-refusal eats correct
answers, same shape as refusal-consensus. Contract MARKUP succeeded (86/89 rows emitted
[[CITE]] blocks) — retained as instrumentation; gate v1 killed. ⛔ do not re-run unchanged.

## Opus reader lane — pass1 apparatus failure + resume (2026-08-31/09-01)
First pass1 invocation hit the Claude session usage limit at row ~306 (194 rows errored,
100% back-half, banner "You've hit your session limit"; fail-closed lane recorded errors,
never fake answers). Completed-row hit rate 289/306 = 94.4%. 289/500 headline is an
APPARATUS artifact, not a capability verdict (novel-system rule: first FAIL provisional).
Resume relaunched on limit rollover.

## OPUS READER PASS1 — 479/500 (95.8%), ONE ABOVE CHRONOS 478 (2026-09-01)
Fresh-judge verdict on the clean 500-row artifact (reader 500/500, 0 errors after
usage-limit resume): answerable 452/470, abs 27/30. ⚠ NOT A CLAIM — single pass;
pass2 running with auto-resume loop; claim requires the pair per the pre-registered
two-pass rule. Incident recorded: the judge's resume-by-qid (done_ids) silently kept
stale verdicts for the 194 resumed rows — first "289/500 resumed" verdict was judge
staleness, caught by timeline reconstruction; fresh judge in judge_gpt4o_v2 is
authoritative. ⛔ Lesson: after a reader resume changes answers, the judge MUST run
in a clean out-dir (resume-by-qid cannot see changed rows).

## GLM-5.3 cross-judge study (Opus pair) — 98.6/98.6% agreement, GLM stricter (2026-09-01)
Judge-variance study, NOT rubric-comparable — official 479/475 never changes.
glm-5.3:cloud re-judged both frozen Opus checkpoints (identical frozen official
rubric templates; controls pos 17/17 neg 20/20 both passes). pass1 493/500 agree
(gpt_only 7, glm_only 0); pass2 493/500 (gpt_only 5, glm_only 2). GLM-5.3 is the
stricter judge both passes; systematic gpt_only = 2133c1b5_abs, c8090214_abs,
f685340e_abs (all abstention-class). Disagreement concentrates in abstention
(5+4 of 30) — all other types ≥98.3%, temporal + SSA 100% both passes. Mirrors the
glm-5.2-on-grok study (98.2/97.8, judge_agreement_matrix.json): the ~98%
cross-judge agreement band reproduces on a second judge generation and reader pair.
For context only (NOT a benchmark number): glm-5.3 scores the same responses
472/472. ⚠ Apparatus incident + repair: first pass recorded 29 empty-raw verdicts
(glm-5.3 thinking exceeded num_predict:512 → done_reason=length → empty response
channel → silent False); 11+14 disagreed with official = artifact-flavored.
Repair: num_predict 4096, empty/unparseable verdicts retry fail-closed, first-word
extraction (tests test_extract_verdict_*). 29 rows re-judged, 0 empty since.
Pre-repair 96.6/96.6 — do not quote. Matrix: judge_agreement_matrix_opus_glm53.json.

## GLM-5.3 READER datapoint — 471/500 (94.2%), curve only, NOT a headline (2026-09-01)
Single pass on the identical v3.4 substrate (materialized+facts concat, same as
dsv4pro_pass1; 243 v2 + 257 v3.4-facts rows) via the flash lane on Ollama MAX
(opencode ollama-cloud/glm-5.3; bare "glm-5.3:cloud" does not resolve on opencode —
err_b5e3cd53 — the provider-prefixed rail id is the resolvable form of the same
model+sub). Reader audit clean: 500/500, 0 errors/empty/contaminated/missing.
Official judge gpt-4o-2024-08-06 (api, resolved snapshot exact), controls 12/12 +
12/12. Answerable 445/470, abs 26/30. Per-type: SSU 1.000, KU .972, TR .969,
SSA .982, MS .893, SSP .833. Reader curve now 93 → 436 → 455 → 471 → 476/474 →
479/475: GLM-5.3 slots between Sol and grok-high — within a few points of the top
tier, tens above the mid tier. Two-pass rule applies before any promotion.

## Adversarial pass — all claims re-derived, 3 fixes landed (2026-09-01)
Independent re-derivation from raw artifacts (fresh code, no summary JSONs):
all ten curve totals exact, substrate byte-identity by hash across ALL 11
runs, cross-judge 98.6/98.6 re-derived, floors 473/471 exact, controls 1.00/1.00
everywhere, staleness quarantine correct. Findings + fixes: (W-1) the Opus
headline contains the dossier's Class-A fabrication point on both passes
(731e37d7 $720) net-zero against the Class-B fidelity loss (370a8ff4) —
adjudicated band 478/474–480/476, tie robust in every stance, "outright"
softened to "on the raw score" + disclosure sentence added (tex+md). (W-2)
xhigh_pass1's one empty verdict was READER-RESUME STALENESS (reader rewrote
fe651585_abs 11 min after the judge scored it empty; 1 row only) — surgical
v2 re-judge, fresh controls 12/12, verdict True → **xhigh_pass1 460→461**;
paper updated (table, −15/−9, 19 losses, Wilson [89.5,94.2], repair note);
regression conclusion unchanged. (W-3) abstract "verified published" →
"published". Receipt: v4/ADVERSARIAL_PASS_20260901.md.

## KIMI K3 READER datapoint — 465/500 (93.0%), curve only, NOT a headline (2026-09-01)
Single pass, identical v3.4 substrate, flash lane on Ollama MAX
(opencode ollama-cloud/kimi-k3). Reader audit clean after one resume (2 rows
chrome-contaminated by the opencode cue-plugin "OUT: 0 (...)" banner —
trailing text defeats the OUT regex's $ anchor; lane failed closed, resume
retried both, clean 500/500). Official judge gpt-4o-2024-08-06, controls
12/12 + 12/12, 0 empty verdicts. Answerable 444/470, abs 21/30 (abstention is
Kimi's weak spot; SSA .911 also soft). Misses: 35 = 12 hard + 20 kimi-specific
+ 3 mixed. The long-context-specialist family lands BETWEEN Sol (455) and
GLM-5.3 (471): long-context specialization does not transfer to
memory-benchmark dominance on this substrate — the "long context is not long
memory" datum, measured with receipts. Curve: 93 → 436 → 455 → 465 → 471 →
476/474 → 479/475. Two-pass rule applies before any promotion.
