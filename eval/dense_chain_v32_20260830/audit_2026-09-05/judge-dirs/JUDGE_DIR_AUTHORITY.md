# Judge-directory authority — `full-v34-opus_pass{1,2}`

Read-only audit, 2026-09-05. No files outside this directory were modified.
Every input was verified byte-identical to `RELEASE_MANIFEST.md` before analysis
(34 opus-pair rows checked, 0 mismatches).

---

## Bottom line

**`full-v34-opus_pass1/judge_gpt4o_v2/` is authoritative for pass 1** (479/500).
**`full-v34-opus_pass2/judge_gpt4o/` is authoritative for pass 2** (475/500).
Together they are the paper's 479/475 headline, and they match the §5.1.1
per-type table row-for-row.

The other two pass-1 directories are:

- **`judge_gpt4o/` — a partial, invalid artifact. Not a judge result.**
  194 of its 500 rows were **never judged at all**: `attempts: 0`,
  `llm_judge_raw: ""`, `resolved_snapshot: null`, verdict recorded as `false`.
  The judge API was never called for them. It yields **289/500**.
- **`judge_gpt4o_repro_20260901/` — a legitimate independent re-judge**, run in a
  clean out-dir 16 h later on the same frozen checkpoint. It yields **478/500**
  and is exactly what paper §8 describes (497/500 verdict agreement with v2,
  three flips on byte-identical text). It is a *confirmation* artifact, not a
  competing headline.

**Could a third party tell?** *Only from the repo `README.md`.* One sentence there
names `judge_gpt4o_v2/` for pass 1 and `judge_gpt4o/` for pass 2, and a copy-paste
snippet prints the expected 479/475/478. Nothing anywhere — README, manifest, or
paper — says what pass 1's `judge_gpt4o/` **is**, that it is superseded, or that
it yields 289. `RELEASE_MANIFEST.md` mentions it only as three hash rows; it
carries **zero** prose about any judge directory. A third party who lists the
directory tree instead of reading the README faces a naming convention that
points the wrong way: the unsuffixed `judge_gpt4o/` reads as canonical and
`_v2/` as an experiment, when the truth is the reverse.

---

## 1. Side by side

| | **pass1/`judge_gpt4o`** | **pass1/`judge_gpt4o_v2`** | **pass1/`judge_gpt4o_repro_20260901`** | pass2/`judge_gpt4o` |
|---|---|---|---|---|
| rows | 500 | 500 | 500 | 500 |
| answerable / abstention | 470 / 30 | 470 / 30 | 470 / 30 | 470 / 30 |
| `llm_judge_correct` **true** | **289** | **479** | **478** | **475** |
| `llm_judge_correct` false | 211 | 21 | 22 | 25 |
| answerable correct | 273/470 = 0.58085 | 452/470 = 0.96170 | 452/470 = 0.96170 | 450/470 = 0.95745 |
| abstention recognized | 16/30 | 27/30 | 26/30 | 25/30 |
| **/500 total** | **289** | **479** | **478** | **475** |
| `scored_at` min | 2026-09-01T05:27:08.971787Z | 06:30:06.769469Z | 22:53:57.038585Z | 12:20:37.065653Z |
| `scored_at` max | 2026-09-01T05:30:48.725322Z | 06:35:20.185955Z | 22:59:02.813749Z | 12:26:55.205299Z |
| summary `generated_at` | **06:28:25.650474Z** (58 min after last row) | 06:35:20.186943Z | 22:59:02.815458Z | 12:26:55.209562Z |
| `model` | gpt-4o-2024-08-06 ×500 | ×500 | ×500 | ×500 |
| `transport` | api ×500 | ×500 | ×500 | ×500 |
| `resolved_snapshot` | **gpt-4o-2024-08-06 ×306, `null` ×194** | ×500 | ×500 | ×500 |
| `prompt_version` | longmemeval-official-judge-v1 ×500 | ×500 | ×500 | ×500 |
| `attempts` | **1 ×306, `0` ×194** | 1 ×500 | 1 ×500 | 1 ×500 |
| `llm_judge_raw` empty | **194** | 0 | 0 | 0 |
| controls (shipped receipt) | 12/12 pos, 12/12 neg | 12/12, 12/12 | 12/12, 12/12 | 12/12, 12/12 |
| controls in the log line that produced these verdicts | **`positive 11/11 negative 12/12`** | `12/12 12/12` | `12/12 12/12` | `12/12 12/12` |

Per-question-type, answerable only (correct / n):

| type | n | pass1 `judge_gpt4o` | pass1 `_v2` | pass1 `_repro` | pass2 `judge_gpt4o` |
|---|---:|---|---|---|---|
| knowledge-update | 72 | **0 (0.000)** | 69 (0.958) | 70 (0.972) | 70 (0.972) |
| multi-session | 121 | 110 (0.909) | 110 (0.909) | 109 (0.901) | 109 (0.901) |
| single-session-assistant | 56 | **0 (0.000)** | 56 (1.000) | 56 (1.000) | 56 (1.000) |
| single-session-preference | 30 | 30 (1.000) | 30 (1.000) | 30 (1.000) | 28 (0.933) |
| single-session-user | 64 | 64 (1.000) | 64 (1.000) | 64 (1.000) | 64 (1.000) |
| temporal-reasoning | 127 | **69 (0.543)** | 123 (0.969) | 123 (0.969) | 123 (0.969) |

---

## 2. Staleness test — hypothesis CONFIRMED, and stronger than a timestamp

Test as specified: a judge verdict whose `scored_at` precedes the reader row's
`scored_at` for the same `question_id` is stale by construction.

| directory | stale rows | stale rows that are `false` |
|---|---:|---:|
| pass1/`judge_gpt4o` | **194 / 500** | **194 / 194 (100%)** |
| pass1/`judge_gpt4o_v2` | 0 | — |
| pass1/`judge_gpt4o_repro_20260901` | 0 | — |
| pass2/`judge_gpt4o` | 0 | — |

The timestamp test and a second, independent test agree **exactly**: the set of
194 stale-by-timestamp rows is **set-identical** to the set of 194 rows carrying
`attempts: 0` + `llm_judge_raw: ""` + `resolved_snapshot: null`. Those fields say
the judge was never called. So these are not stale *verdicts* — they are
**non-verdicts recorded as `false`**.

Clean temporal separation, no overlap:

- reader `scored_at` for the 194 stale rows: **05:51:57.696Z → 06:28:04.240Z** — all *after* the judge finished.
- reader `scored_at` for the 306 real rows: **03:12:18.609Z → 04:30:34.008Z** — all *before* the judge started.
- judge real-call window: **05:27:08.972Z → 05:30:48.725Z**.

### Concentration in the 0.0 types — exact

| question_type | stale | total in dir | fraction |
|---|---:|---:|---|
| knowledge-update | 78 | 78 | **1.000** |
| single-session-assistant | 56 | 56 | **1.000** |
| temporal-reasoning | 60 | 133 | 0.451 |
| multi-session | 0 | 133 | 0.000 |
| single-session-preference | 0 | 30 | 0.000 |
| single-session-user | 0 | 70 | 0.000 |

The two types reading 0.0 are precisely the two types that are **100% stale**.
Temporal-reasoning is 45% stale and reads 0.543. Every type with zero stale rows
scores identically to `_v2`. The score is fully explained by the stale set.

### Positive control on the judge itself

On the **306 rows the judge actually judged**, `judge_gpt4o` and `judge_gpt4o_v2`
agree **306/306**. Across all 500 they agree 310/500. The judge was never wrong;
only the 194 never-judged rows differ. `judge_gpt4o/` is not "a different judge
result" — it is the same judge run against an incomplete input.

### Mechanism, from runtime code (`scripts/rescore_gpt4o_judge.py`)

1. **L514–516** — an empty reader response short-circuits with no API call:
   `verdict, raw, attempts, resolved_snapshot = False, "", 0, None`.
   That is the exact 194-row signature.
2. **L605–612** — resume builds `done_ids` from `question_id` **existence** in
   `rescored.jsonl`. Not freshness, not `attempts`, not the reader timestamp.
   A re-run into the same out-dir skips every row already present, however it
   was scored. (The "label ≠ state / enforcement keys existence, not fields"
   family.)
3. **L631–668** — the summary and `control_receipt.json` are recomputed and
   **overwritten on every invocation**, and `resolved_snapshots` filters out
   falsy values — so the 194 `null` snapshots are invisible in the summary. The
   summary structurally cannot show this defect.

### Corroborating log evidence

`full-v34-opus_pass1/reader.log`, last line:

```
ARTIFACT INVALID — not fit for judging. errors=194 empty=194 contaminated=0 missing=0
```

The reader lane itself declared the checkpoint unfit. The judge was fired against
it anyway.

### Reconstructed timeline (2026-09-01, UTC)

| time | event |
|---|---|
| ~02:15 → ~04:30 | reader invocation 1 writes 500 rows; 194 error/empty. `reader.log`: **ARTIFACT INVALID**. |
| 05:27:08 → 05:30:48 | judge invocation 1 → `judge_gpt4o/`. 306 real verdicts + **194 stubs**. `judge.log`: `controls: positive 11/11 negative 12/12`, acc 0.5809. |
| 05:51:57 → 06:28:04 | reader invocation 2 (resume) rewrites the 194 rows. `run_meta.json`: `n_completed_this_invocation: 194`, audit `clean: true`. |
| **06:28:25** | judge invocation 2 into the **same** out-dir. Resume skips all 500 — `judge.log`'s second block has **no `ans N/470` progress lines**. Controls re-run **12/12**; `control_receipt.json` and `rescore_summary.json` **overwritten**; the 194 stub verdicts **untouched**. Score still 0.5809. |
| 06:30:06 → 06:35:20 | **the fix** — judge into a **clean** out-dir → `judge_gpt4o_v2/` → **479/500**. |
| 12:20 → 12:27 | pass 2 judged clean → `judge_gpt4o/` → 475/500. |
| 22:53 → 22:59 | independent re-judge into a clean out-dir → `judge_gpt4o_repro_20260901/` → 478/500. |

Step 4 is the sharpest part of the defect: **the shipped `control_receipt.json`
in `judge_gpt4o/` (12/12, 12/12) does not describe the run that produced the
shipped verdicts** (which logged `positive 11/11`). A green control receipt sits
on top of 194 never-judged rows. Self-reported health is not evidence.

### Release-wide sweep

The stub signature (`attempts == 0` ∧ empty raw ∧ null snapshot) appears in
**exactly 2 of 29** judge directories in the release:

| directory | stubs | fix dir | documented? |
|---|---:|---|---|
| `full-v34-opus_pass1/judge_gpt4o/` | **194** | `judge_gpt4o_v2/` | **no** |
| `full-v34-xhigh_pass1/judge_gpt4o/` | 1 | `judge_gpt4o_v2/` | **yes — paper §5.1** |

Same defect class, same fix pattern, both shipped. Paper §5.1 documents the
one-row xhigh instance verbatim ("the reader resumed one row eleven minutes after
the judge had scored it on an empty response; a surgical v2 re-judge under fresh
12/12 controls restored it, 460 → 461"). The 194-row instance on the **headline**
pass is undocumented.

---

## 3. What number each directory yields

Paper accounting (§5.1.1): **answerable correct + abstention recognized, over 500.**

| directory | answerable | abstention | **/500** | matches |
|---|---|---|---|---|
| pass1/`judge_gpt4o` | 273/470 (0.58085) | 16/30 | **289/500 (57.80%)** | **nothing in the paper or README** |
| pass1/`judge_gpt4o_v2` | 452/470 (0.96170) | 27/30 | **479/500 (95.80%)** | **paper §5.1 + §5.1.1 headline pass 1** |
| pass1/`judge_gpt4o_repro_20260901` | 452/470 (0.96170) | 26/30 | **478/500 (95.60%)** | paper §8 pre-release re-judge |
| pass2/`judge_gpt4o` | 450/470 (0.95745) | 25/30 | **475/500 (95.00%)** | **paper §5.1 + §5.1.1 headline pass 2** |

`judge_gpt4o_v2` reproduces the paper's pass-1 number. Its per-type column is
identical to §5.1.1's "Opus p1" column at every row (SSA 56, SSU 64, KU 69,
SSP 30, TR 123, MS 110, abstention 27, total 479), and pass2/`judge_gpt4o`
matches "Opus p2" identically (56, 64, 70, 28, 123, 109, 25, total 475).

`_repro` vs `_v2`: 497/500 agreement, 3 flips — the exact three named in §8:

| qid | type | `_v2` | `_repro` |
|---|---|---|---|
| `7024f17c` | multi-session | True (`Yes.`) | False (`No`) |
| `031748ae_abs` | knowledge-update (abstention) | True (`Yes`) | False (`No`) |
| `a2f3aa27` | knowledge-update | False (`No`) | True (`Yes`) |

**Separate paper defect found in passing (not in scope, recorded):** §5.1's
sentence *"Headline-pair detail: answerable 450/470 and 447/470; abstention 26/30
(pass 1) and 27/30 (pass 2)"* does **not** describe the Opus headline pair
(452/470 + 27/30 = 479; 450/470 + 25/30 = 475). Those figures are the **grok raw
pair** — verified directly: `full-v34_pass1/judge_gpt4o` = 450/470 + 26/30 = 476,
`full-v34_pass2/judge_gpt4o` = 447/470 + 27/30 = 474. The grok pair's detail is
mislabelled as the headline pair's. §5.1.1's table is correct; only this prose
sentence is wrong. Owner: the paper/tex-port worker.

---

## 4. Authority verdict, on evidence

**Authoritative — pass 1: `full-v34-opus_pass1/judge_gpt4o_v2/` (479/500).**
Grounds: 500/500 rows genuinely judged (`attempts: 1`, snapshot resolved,
non-empty raw on every row); zero stale rows; controls 12/12 and 12/12 from the
same invocation that produced the verdicts; reproduces the paper's §5.1.1 pass-1
column exactly; independently corroborated at 497/500 by `_repro`; named by the
repo README.

**Authoritative — pass 2: `full-v34-opus_pass2/judge_gpt4o/` (475/500).**
Same grounds; no sibling directory competes.

**`full-v34-opus_pass1/judge_gpt4o/` is a superseded partial artifact (289/500).**
Not stale-in-the-ordinary-sense and not a judge disagreement: 194 of 500 rows
were never submitted to the judge, and the harness recorded the absence of a
verdict as `false`. Its `rescore_summary.json` and `control_receipt.json` come
from a later resume invocation that judged nothing, so the green controls beside
it describe a different run than the verdicts. Its accuracy figure (0.5809) has
no measurement meaning — it is 273 real verdicts diluted by 197 non-verdicts.

**`full-v34-opus_pass1/judge_gpt4o_repro_20260901/` is a valid, independent
re-judge (478/500)**, deliberately produced and explicitly cited in paper §8. It
belongs in the release. It is not a competing headline and should not be read as
one; it measures the official judge's own flip floor.

---

## 5. What the release should do

Smallest correct fix, in priority order. **Removal is explicitly not recommended
by this audit and is an operator decision, not an auditor's** — deleting a
released file changes `RELEASE_MANIFEST.md`, its root hash
`f8875b3bd9252a0be4dbd486ef3ab0097eab6d5c886898e8d424cc565b602b3d`, and the
published anchor in `ANCHORS.md`. Keeping the artifact and labelling it is also
the more auditable choice: a defect that is documented is evidence of process,
while a defect that is deleted is unverifiable.

1. **LABEL (in-directory, highest value).** Add a `SUPERSEDED.md` or `NOTE.md`
   inside `full-v34-opus_pass1/judge_gpt4o/` stating: this directory is a partial
   artifact; 194 of 500 rows were never judged (`attempts: 0`, empty
   `llm_judge_raw`, `null` `resolved_snapshot`) because the judge ran against a
   reader checkpoint that `reader.log` had already declared
   `ARTIFACT INVALID — errors=194 empty=194`; it yields 289/500 and is **not** a
   judge result; the authoritative pass-1 verdicts are in `judge_gpt4o_v2/`; the
   shipped control receipt here is from a later resume invocation that judged no
   rows. A reader who opens the directory should not have to reach the repo README
   to learn this.
2. **DOCUMENT (README).** The README currently names `judge_gpt4o_v2/` positively
   but never mentions that pass 1 also ships `judge_gpt4o/`. Add one clause naming
   it as superseded. Silence is what makes the naming convention hazardous.
3. **DOCUMENT (paper).** Paper §5.1 already documents the identical one-row defect
   on the xhigh pass. The 194-row instance on the headline pass deserves the same
   sentence, in §5.1 or §8. It strengthens the paper rather than weakening it: it
   is the same fail-closed reader audit catching a much larger instance.
4. **HARNESS GUARD (the durable fix).** Two one-line-class changes to
   `scripts/rescore_gpt4o_judge.py`: (a) refuse to resume into an out-dir whose
   `rescored.jsonl` contains any row with `attempts == 0`, since those rows are
   non-verdicts, not completed work; (b) refuse to judge a reader checkpoint whose
   `run_meta.json` audit is not `clean` (or whose rows contain empty responses)
   unless explicitly forced. Root cause is that resume keys on **existence**
   rather than freshness — the same class the release already hit once on xhigh.
5. **MANIFEST (optional).** `build_release_manifest.py` could emit a per-judge-dir
   integrity column (rows, `attempts == 0` count) so the manifest itself would
   have exposed this. Currently the manifest proves only that bytes did not drift,
   not that the bytes mean what their directory name implies.

**Operator decision required for:** any file removal, any edit to
`RELEASE_MANIFEST.md` or the root hash, and any push. Nothing in this audit was
written outside `audit_2026-09-05/judge-dirs/`.

---

## 6. What the release says today — verbatim

**Repo `README.md` — the only place that lets a third party pick correctly:**

> - `eval/dense_chain_v32_20260830/full-v34-opus_pass{1,2}/` — the headline
>   Opus reader pair: reader checkpoints (`reader/checkpoint_*.jsonl`,
>   `run_meta.json`), official GPT-4o judge verdicts (`judge_gpt4o_v2/` for
>   pass 1, `judge_gpt4o/` for pass 2), control receipts, GLM-5.3 cross-judge
>   verdicts, and the pre-release re-judge `judge_gpt4o_repro_20260901/`
>   (478/500, three verdict flips on identical text — see paper §8).

and the re-derivation snippet, which hard-codes the correct paths:

> ```
> for name, p in [("Opus pass1", f"{E}/full-v34-opus_pass1/judge_gpt4o_v2/rescored.jsonl"),
>                 ("Opus pass2", f"{E}/full-v34-opus_pass2/judge_gpt4o/rescored.jsonl"),
>                 ("Opus pass1 re-judge", f"{E}/full-v34-opus_pass1/judge_gpt4o_repro_20260901/rescored.jsonl"),
> ```
> Expected: 479, 475, 478, 476, 474.

This is correct and sufficient **if read**. It is also the whole of it. The README
never names `full-v34-opus_pass1/judge_gpt4o/`, never says it is superseded, and
never says it yields 289.

**`RELEASE_MANIFEST.md`:** contains **nothing** about any judge directory. The
string `judge_gpt4o` appears only inside manifest table rows
(`| path | bytes | sha256 |`) — 0 prose lines, verified by grep. The header
paragraph says only that "Every judge-side claim in the paper is re-derivable
from the released reader checkpoints plus `scripts/rescore_gpt4o_judge.py`
alone." True, and it points a third party at a *re-run*, not at a directory
choice. The manifest cannot help someone pick.

**`eval/dense_chain_v32_20260830/README.md`** (541 B): describes `full_sol/`
only. Nothing about the opus pair.

**`ANCHORS.md`:** manifest root and signing only. Nothing about judge directories.

**Paper:** §5.1.1's table matches `_v2` (pass 1) and pass2 `judge_gpt4o` exactly,
so the numbers are traceable to bytes; §8 names
`full-v34-opus_pass1/judge_gpt4o_repro_20260901/` explicitly. Neither section
names pass 1's `judge_gpt4o/`.

---

## 7. Integrity of this audit

All 34 `full-v34-opus_pass{1,2}` manifest rows re-hashed against
`RELEASE_MANIFEST.md`: **0 mismatches**. The files analysed here are the released
bytes. Input and output hashes are in `HASHES.json`; machine-readable findings in
`judge_dir_authority.json`.
