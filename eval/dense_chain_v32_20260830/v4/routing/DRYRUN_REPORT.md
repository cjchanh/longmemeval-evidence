# v4 dual-read dry-run report

Primary: `grok-4.6-high` (full-v34_pass1) routed against the route table's measured per-type second reader, over all 500 rows. Sourced from existing reader checkpoints -- no live calls.

GOLD-BLIND: agreement/disagreement above was computed from normalized answer text only. Judge verdicts (`llm_judge_correct`) are used ONLY in this report, to bound the honest upside/risk of adjudication -- never in the routing or agreement path.

## Agreement
- Total scored rows: 500
- Agree: 287 (57.4%)
- Disagree: 213 (42.6%)

## Disagreement by type
| type | disagreements |
|---|---|
| knowledge-update | 34 |
| multi-session | 82 |
| single-session-assistant | 9 |
| single-session-preference | 29 |
| single-session-user | 31 |
| temporal-reasoning | 28 |

## Honest bound (judge verdicts, report-only -- never in the routing path)
Of the disagreements where both sides have a judge verdict:
- **Upside** (second correct, primary wrong): 8
- **Risk** (primary correct, second wrong): 20
- Both correct despite flagged disagreement (normalization slack / true paraphrase): 176
- Both wrong: 9

No disagreement touches a known gold-defect row.

Net if adjudication always picked the second reader on disagreement: -12 raw, -12 gold-defect-excluded. A real adjudication gate (sufficiency-based, not always-second) is required to realize the upside without eating the risk -- see scripts/v4_sufficiency.py (not present yet at time of this run).

### Upside rows (second right, primary wrong)
- 07741c45
- 15745da0
- 3a704032
- 618f13b2
- 7405e8b1
- dd2973ad
- gpt4_4929293b
- gpt4_7abb270c

### Risk rows (primary right, second wrong)
- 07741c44
- 0edc2aef
- 1a8a66a6
- 1c0ddc50
- 2318644b
- 35a27287
- 37f165cf
- 51a45a95
- 6456829e_abs
- 69fee5aa
- 778164c6
- 88432d0a
- 9ee3ecd6
- a82c026e
- ba358f49
- d6233ab6
- efc3f7c2
- gpt4_468eb063
- gpt4_ab202e7f
- gpt4_f420262c

