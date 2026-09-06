# Judge-harness remediation — 2026-09-05/06

The worker that made these changes was killed by a session rate limit before it
could write its own log or run its tests. **The root session ran the tests it never
reached and verified the diff; this log is the root's record, and says so.**

## What changed

### 1. `full-v34-opus_pass1/judge_gpt4o/SUPERSEDED.md` (new, released tree)

Labels that directory a partial artifact rather than a judge result. Root-verified
facts it states:

| Directory | Rows | Correct | `attempts: 0` | Status |
|---|---|---|---|---|
| `judge_gpt4o_v2/` | 500 | 479 | 0 | authoritative pass 1 |
| `judge_gpt4o_repro_20260901/` | 500 | 478 | 0 | independent re-judge (paper §8) |
| `full-v34-opus_pass2/judge_gpt4o/` | 500 | 475 | 0 | authoritative pass 2 |
| `full-v34-opus_pass1/judge_gpt4o/` | 500 | 289 | **194** | partial — superseded |

Independently reproduced by the root:

```
never-judged rows: 194   (attempts:0, empty llm_judge_raw, resolved_snapshot:null,
                          all 194 written llm_judge_correct:false)
of those, judge_gpt4o_v2 scores correct: 190
289 + 190 = 479
```

The 194 `false` values are absence of a measurement stored in the field a real
verdict uses. On the 306 rows this directory did judge it agrees with `_v2`
**306/306** — the ruler was never wrong, the coverage was missing.

### 2. `scripts/rescore_gpt4o_judge.py` — four fail-closed guards (+260 / −8)

| Function | Refuses |
|---|---|
| `guard_resume_checkpoint` | resuming into an out-dir that already holds `attempts: 0` rows; names the affected question types; opt-out `--allow-unjudged-resume` warns loudly instead of silently proceeding |
| `guard_reader_checkpoint` | judging a reader checkpoint containing empty responses (the incident's own log read `ARTIFACT INVALID — not fit for judging. errors=194 empty=194`) |
| `guard_control_receipt_overwrite` | overwriting a control receipt whose sampled row-ids differ from this invocation's — this is how a green 12/12 came to sit on top of a run whose log says `positive 11/11` |
| `guard_summary_overwrite` | overwriting a summary whose scored row-set (`summary_row_ids_sha256`) differs from this invocation's |

The 8 deleted lines are refactors only — an import, a signature, a call, a moved
variable, and the summary write replaced by its guarded form. **No judging logic,
prompt, rubric, or scoring behaviour was changed.**

### 3. `tests/test_rescore_gpt4o_judge_guards.py` (new)

Includes a regression test that reads the actual released `judge_gpt4o/rescored.jsonl`
and asserts the 194 / `attempts:0` / all-false signature is caught by the resume guard.

## Test results — run by the root, not by the authoring worker

```
tests/test_rescore_gpt4o_judge_guards.py   36 passed
tests/ (full suite)                       152 passed, 2 failed
```

The two failures are `test_release_manifest_check.py::test_check_passes_on_current_tree`
and `::test_check_does_not_write`. Cause, confirmed: the three corrected `.md` files
plus `scripts/rescore_gpt4o_judge.py` no longer match `RELEASE_MANIFEST.md`. That is
the manifest check working correctly against a deliberately deferred step — **not a
regression.** `README.md` also appears in the mismatch list because it pins the
manifest root hash, which changes when the manifest is regenerated; the regeneration
resolves both together.

## Deliberately NOT done here

- **Manifest regeneration** — one step at the end, after all content edits land.
- **README clause** naming the superseded directory. Needs the manifest pass.
- **Paper §5.1 mislabelled numbers** — handled by the paper rewrite, not here.
- **`.tex` / `.pdf` / `ARXIV_SUBMISSION.md`** — the tex port owns those.
- **Removing any released file** — operator decision. Nothing was deleted; the
  defective directory is labelled in place, not withdrawn, so a third party can still
  see what happened.
- **`full-v34-xhigh_pass1/judge_gpt4o`** carries the same stub signature on 1 row and
  is already documented in paper §5.1 ("460 → 461"). Left alone.
