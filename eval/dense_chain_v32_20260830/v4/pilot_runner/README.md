# v4 Pilot Runner — coordinator runbook

Runner: `scripts/v4_pilot_run.py` (`cds/v4-pilot-runner/v1`)
Frozen set: `eval/dense_chain_v32_20260830/v4/pilot/PILOT_SET.json`
(89 rows — 27 TARGET / 60 CONTROL / 2 claim_excluded, freeze hash
`4c9feeac5a522d17f1aeba41ba75a016dcd4f3e819abe696ec74df681fe6ad2f`)

The runner re-derives that hash on every start and halts if it does not
reproduce. An unfrozen set cannot decide a pre-registered rule.

---

## The frozen promotion rule (restated verbatim)

> v4 components are promoted to a full pair only if pilot shows net >= +4 on
> TARGET rows with <= 1 CONTROL regression.

The runner reads this string out of `PILOT_SET.json` and prints it verbatim
above its own verdict; it is never retyped in code. `claim_excluded` rows
(`gpt4_731e37d7`, `370a8ff4`) are scored for visibility and **excluded from
both numbers** in either direction.

Verdict values:

| Verdict | Meaning |
|---|---|
| `PROMOTE` | net ≥ +4 on TARGET **and** ≤ 1 CONTROL regression |
| `DO NOT PROMOTE` | every judged row accounted for, rule not met |
| `INDETERMINATE` (exit 4) | at least one TARGET/CONTROL row unjudged — a partial pilot cannot satisfy a pre-registered threshold |

---

## Arm A — v3.5 facts + citation contract, grok-cli high

Run from the repo root. The OpenAI key is read by the judge from the key
file; it never appears in argv, env, or any receipt.

```
python3 scripts/v4_pilot_run.py --live \
  --lane grok-cli --effort high --workers 3 \
  --contract v4-citation \
  --facts eval/dense_chain_v32_20260830/v4/anchors/facts_v35.jsonl \
  --facts eval/dense_chain_v32_20260830/v4/anchors/facts_abs_v35.jsonl \
  --materialized eval/dense_chain_v32_20260830/full-v34_pass1/materialized_all.jsonl \
  --data ~/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json \
  --baseline-key pass1_correct \
  --out-dir eval/dense_chain_v32_20260830/v4/pilot_runner/armA
```

What it does, in order: filter packets + facts to the 89 qids → reader run
(`scripts/run_lme_qa_flash_packets.py`, `LME_READER_LANE=grok-cli`,
`LME_GROK_CLI_EFFORT=high`, `--prompt-contract v4-citation`) → mechanical
sufficiency gate → GPT-4o judge over the final answers → score → verdict.

**Baseline is the same rows' `pass1_correct` verdicts already in
`PILOT_SET.json`** (grok-4.6-high, v3.4 facts, GPT-4o judge). Arm A changes
two things at once relative to that baseline — the v3.5 facts scaffold and
the citation contract. If the coordinator needs the contract's effect
isolated, run a third arm with `--facts` pointing at the v3.4 files
(`full-v34_pass1/facts_all.jsonl`) and everything else identical.

## Arm B (optional) — dual read + adjudication

Add to the arm A command:

```
  --dual-read --arm-b-lane cursor-grok
```

Adjudication rule, as implemented:

> On disagreement, prefer the answer whose citations byte-verify AND whose
> LINK markers are all stated=yes; if neither or both qualify, keep primary.

A response carrying **no** citation markup never qualifies — the rule prefers
demonstrated grounding, and vacuous truth is not demonstration. Consequence
measured in the dry run: without the contract arm, adjudication is inert
(54 disagreements, 0 second-reader wins). Arm B is only worth its cost on a
contract arm.

## Dry run (no live calls — run this first)

```
python3 scripts/v4_pilot_run.py --dry-run --dual-read \
  --facts eval/dense_chain_v32_20260830/v4/anchors/facts_v35.jsonl \
  --facts eval/dense_chain_v32_20260830/v4/anchors/facts_abs_v35.jsonl \
  --contract v4-citation --lane grok-cli --effort high \
  --out-dir eval/dense_chain_v32_20260830/v4/pilot_runner/dryrun
```

Reader responses come from `full-v34_pass1/reader/`; judge verdicts are
reused from `full-v34_pass1/judge_gpt4o/rescored.jsonl` **only** where the
final answer is byte-identical to the response that was judged. Anything the
gate or adjudicator changed is `PENDING_LIVE` and forces `INDETERMINATE`.

---

## Cost — rows × lanes

| Stage | Calls | Lane |
|---|---|---|
| Arm A reader | 89 | grok-cli (Grok Build subscription; quota, not per-call USD) |
| Arm B reader (optional) | 89 | second reader lane |
| Judge, arm A final answers | 89 | OpenAI API, `gpt-4o-2024-08-06` |
| Judge controls (integrity arm) | 24 (12 positive + 12 negative) | same |
| **Total with arm B** | **178 reader + 113 judge** | |
| **Total arm A only** | **89 reader + 113 judge** | |

Judge control count is `--judge-control-n` (default 12, matching the
`full-v34_pass1` control receipt). Wall clock: the 500-row v34 reader pass
took ~5,000 s at 3 workers, so 89 rows ≈ 15–20 min per reader arm; the judge
is a few minutes.

---

## What the gate does and does not enforce

Wired to REFUSE (mechanical, contract-markup-driven only):

| Reason | Fires when |
|---|---|
| `SPAN_NOT_VERBATIM` | a `[[CITE ... "span"]]` span is not a byte-exact substring of the packet |
| `LINK_STATED_NO` | `[[LINK ... stated=no]]` on a committed answer |
| `MISSING_TERM` | `[[MISSING "term"]]` on a committed answer |

A REFUSE rewrites the final `Answer:` line to an explicit abstention and
preserves the original under `response_pre_gate` in `gate_records.jsonl`.
An abstention is never refused — there is no over-commitment to catch.

Advisory only (recorded, never decides a row): `CITE_ROLE_MISMATCH` (contract
rule 4), and `NO_CITATIONS` on a committed answer — opt that one into REFUSE
with `--refuse-on-missing-citations` if the coordinator wants contract
compliance itself to be scored.

**Not wired:** the v0 lexical gate in `scripts/v4_sufficiency.py`
(`FRAME_A`/`FRAME_B`/`FRAME_D`). W2 blocked it from integration; the pilot
runner never imports those detectors and a test asserts they are unreachable.

## Gold discipline

Gold enters exactly one stage — the judge. The gate and the adjudicator take
`(question, response, blobs)` and nothing else (asserted by signature in
`tests/test_v4_contract_prompt.py`), and `strip_gold()` is applied to every
record crossing into them. `pass1_correct` / `pass2_correct` are prior judge
verdicts, not gold, and are read only when scoring.

## Artifacts written per run

```
<out-dir>/
  filtered/materialized_pilot.jsonl   89 packets
  filtered/facts_pilot.jsonl          merged + filtered facts scaffolds
  armA/reader/checkpoint_{answerable,abs}.jsonl, run_meta.json
  armB/reader/…                       (only with --dual-read)
  gate_records.jsonl                  per-row gate + adjudication record
  final/checkpoint_{answerable,abs}.jsonl   what the judge scored
  judge_gpt4o/{rescored.jsonl,rescore_summary.json,control_receipt.json}
  pilot_result.json                   the full receipt, including the verdict
```

## Known state at handoff (2026-08-31)

- `facts_v35.jsonl` + `facts_abs_v35.jsonl` cover **50 of the 89** pilot rows
  (240 + 17 rows overall). The other 39 run on the plain v2 prompt shape —
  the same 50/39 split as the v34 baseline, so the comparison stays like-for-like.
- The contract arm has **never been run live**. Dry-run measured
  `0/89 rows carried [[CITE]] blocks`, which is expected: the frozen
  checkpoints predate the contract. The gate's REFUSE paths are proven on
  synthetic markup in `tests/test_v4_contract_prompt.py`, not yet on reader output.
- A no-op dry run reproduces the baseline exactly (TARGET net +0, 0 CONTROL
  regressions) — the harness's identity path is verified.
