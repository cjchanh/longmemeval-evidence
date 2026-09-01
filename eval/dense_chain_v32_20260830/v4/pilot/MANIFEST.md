# v4 Pilot Set — MANIFEST

Frozen pilot row set for the v4 component pilot. Generated deterministically by `scripts/v4_pilot_set.py` (seed=20260831) from the grok-pair GPT-4o judge rescores: `full-v34_pass1/judge_gpt4o/rescored.jsonl` / `full-v34_pass2/judge_gpt4o/rescored.jsonl`.

## How each row qualified

**TARGET** (n=27) — union of:
- `stable_wrong`: wrong in BOTH full-v34_pass1 AND full-v34_pass2 (grok-pair stable-wrong, all types incl. abstention; 21 rows before exclusions — matches `v4/PARENT_ANALYSIS.md`'s "21 pair-stable-wrong rows"; the campaign-root `stable_wrong_v34.json` is the answerable-only subset, 18 rows).
- `flip`: `llm_judge_correct` differs between pass1 and pass2 (8 rows; matches `v34_full_pair_attribution.json` flips list).
- `abs_miss`: the 4 named pass1 abstention misses (`a96c20ee_abs`, `09ba9854_abs`, `gpt4_fe651585_abs`, `031748ae_abs`), unioned with any additional abstention rows wrong in pass2 (none beyond the named 4 in this data).
- The two strict gold-defect rows (`gpt4_731e37d7`, `370a8ff4`) are members of `stable_wrong` but are pulled OUT of TARGET and re-categorized `claim_excluded` (see below) — they never decide a TARGET verdict.

**CONTROL** (n=60)
- Deterministic seeded (seed=20260831) sample of rows correct in BOTH passes, excluding every TARGET and `claim_excluded` row, stratified by `question_type` proportional to the eligible pool's per-type counts (largest-remainder allocation to hit exactly 60), sampled with a single `random.Random(20260831)` walking types in sorted order over sorted candidate lists per type — reproducible byte-for-byte.
- Pool includes both answerable and abstention rows correct in both passes (the `question_type` field already carries the underlying LongMemEval type for abstention rows, e.g. `gpt4_fe651585_abs` -> `temporal-reasoning`); this is a documented interpretation, not a stated constraint — flag for review if the intent was answerable-only controls.

**claim_excluded** (n=2)
- `gpt4_731e37d7`, `370a8ff4` — the two strict (A+B) gold-defect rows per `GOLD_DEFECT_DOSSIER.md` §Strict defects. Listed for visibility (they are genuinely wrong-in-both-passes rows) but flagged `claim_excluded`: they must never decide a pilot verdict in either direction.

## Count table by category and type

| question_type | target | control | claim_excluded |
|---|---|---|---|
| knowledge-update | 3 | 9 | 0 |
| multi-session | 16 | 15 | 1 |
| single-session-assistant | 0 | 7 | 0 |
| single-session-preference | 2 | 4 | 0 |
| single-session-user | 1 | 9 | 0 |
| temporal-reasoning | 5 | 16 | 1 |
| **total** | **27** | **60** | **2** |

## Freeze seal

- Algorithm: `sha256`
- Input: sorted(target_final + control_final + claim_excluded) qid list, newline-joined
- Hash: `4c9feeac5a522d17f1aeba41ba75a016dcd4f3e819abe696ec74df681fe6ad2f`
- Total listed rows: 89 (target 27 + control 60 + claim_excluded 2)

## Pre-registered pilot acceptance rule

> v4 components are promoted to a full pair only if pilot shows net >= +4 on TARGET rows with <= 1 CONTROL regression.

Determinism: re-running `scripts/v4_pilot_set.py` against unchanged input files reproduces this manifest and `PILOT_SET.json` byte-identically (fixed seed, all row lists sorted before hashing or sampling).
