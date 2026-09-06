# SUPERSEDED — this directory is a partial artifact, not a judge result

**Do not read `rescored.jsonl` in this directory as a score.** 194 of its 500
rows were never judged. The judge was not invoked on them: they carry
`attempts: 0`, an empty `llm_judge_raw`, and `resolved_snapshot: null`, and all
194 are written as `llm_judge_correct: false`. Those `false` values are the
**absence of a measurement**, stored in the same field a real `no` verdict
uses. They are not verdicts.

The total this directory yields — 289 of 500 — is therefore **not a score** and
must not be cited as one, in aggregate or per type.

## Authoritative pass-1 verdicts

| Directory | Rows | Correct | `attempts: 0` rows | Status |
|---|---|---|---|---|
| `../judge_gpt4o_v2/` | 500 | 479 | 0 | **authoritative pass 1** |
| `../judge_gpt4o_repro_20260901/` | 500 | 478 | 0 | independent re-judge (paper §8) |
| `../../full-v34-opus_pass2/judge_gpt4o/` | 500 | 475 | 0 | authoritative pass 2 |
| `./` (this directory) | 500 | 289 | **194** | **partial — superseded** |

## The judge itself was never wrong

On the 306 rows this directory actually judged, it agrees with
`../judge_gpt4o_v2/` on **306 of 306**. The defect is missing coverage, not a
bad ruler. Of the 194 rows it never judged, `judge_gpt4o_v2` scores **190
correct** — the absences replaced 190 correct answers with `false`.

## Where the missing rows land

| Question type | Rows here | Never judged |
|---|---|---|
| knowledge-update | 78 | 78 (all) |
| single-session-assistant | 56 | 56 (all) |
| temporal-reasoning | 133 | 60 |
| multi-session | 133 | 0 |
| single-session-preference | 30 | 0 |
| single-session-user | 70 | 0 |

The two types this directory reports at **0.0 accuracy** — knowledge-update and
single-session-assistant — are exactly the two types where **every** row is
unjudged. `rescore_summary.json` in this directory reports those 0.0 figures;
they are artifacts of the missing measurement, not results.

## Reproduce the count yourself

One line, from the repository root:

```
jq -s '{total:length, unjudged:[.[]|select(.attempts==0)]|length, unjudged_all_false:([.[]|select(.attempts==0 and .llm_judge_correct==false)]|length)}' eval/dense_chain_v32_20260830/full-v34-opus_pass1/judge_gpt4o/rescored.jsonl
```

Expected output:

```
{
  "total": 500,
  "unjudged": 194,
  "unjudged_all_false": 194
}
```

The same line over `../judge_gpt4o_v2/rescored.jsonl`,
`../judge_gpt4o_repro_20260901/rescored.jsonl`, or
`../../full-v34-opus_pass2/judge_gpt4o/rescored.jsonl` returns `"unjudged": 0`.

## How it happened

`scripts/rescore_gpt4o_judge.py` scores an empty reader response `false` with
`attempts: 0` and no API call. This pass ran against a reader checkpoint whose
own run log (`../reader.log`) had already declared
`ARTIFACT INVALID — not fit for judging. errors=194 empty=194`. Resume then
keyed on `question_id` existence rather than freshness, so a later invocation
into this same directory skipped all 194 and judged nothing — while still
overwriting `control_receipt.json` and `rescore_summary.json`. That is why the
control receipt here reads a green `positive 12/12` while `../judge.log` line 1
— the invocation that actually produced these rows — reports
`controls: positive 11/11 negative 12/12`. The shipped receipt describes the
later, empty invocation (`../judge.log` line 55), not the run whose verdicts
sit beside it.

All three mechanics now fail closed in `scripts/rescore_gpt4o_judge.py`
(guards a, b, c). See
`../../audit_2026-09-05/judge-dirs/REMEDIATION_LOG.md`.

## Status of the files in this directory

Nothing here has been edited or removed. `rescored.jsonl`,
`rescore_summary.json`, and `control_receipt.json` are byte-unchanged from the
run that produced them, so the incident stays independently auditable. This
note labels them; it does not alter them.
