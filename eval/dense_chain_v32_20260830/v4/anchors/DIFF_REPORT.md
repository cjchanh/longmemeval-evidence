# v3.5 in-text date anchors — v3.4 → v3.5 facts diff

**Wave-2, W5.** Ports the highest-value wave-1 finding (`v4/selector/REPORT.md`,
"THE FINDING WORTH ACTING ON") into the v3.4 facts scaffold as a version-gated
v3.5 contract.

## Verdict first

The change is **additive, bounded, and attributable**. 54 of 257 facts rows
change; every changed row activates the date/duration operator, every changed
row names the provenance of every anchor it adds, and **not one v3.4 line is
rewritten or removed anywhere** — v3.5 output contains the complete v3.4 output
as an ordered subsequence on all 54 rows.

Two things in here are NOT clean and are reported as findings, not footnotes:

1. **34 of 111 emitted anchors resolve after the question date, and 29 of those
   sit in past-tense prose** — i.e. the disclosed year-resolution heuristic is
   probably picking the wrong year on roughly a quarter of the anchors it
   emits. Handled by emitting both readings and committing to neither (below),
   not by silently flipping them. This is a real accuracy limit of the anchor
   block, measured on this corpus, and it is the main reason to run a live
   measurement before promoting v3.5.
2. **The frozen pilot set cannot measure this change.** `v4/pilot/PILOT_SET.json`
   overlaps the changed rows on exactly **1 of 27 target rows** and 4 of 60
   control rows. Its acceptance rule ("net >= +4 on TARGET rows with <= 1
   CONTROL regression") is unreachable by construction — max attainable net is
   +1. A live pilot on that frozen set would be an under-powered instrument, and
   a null result from it would say nothing about v3.5. See §7.

## 1. What changed in the code

`scripts/dense_chain_reasoning_operators.py`, one file.

- `CONTRACT_V34 = "v3.4-facts"` / `CONTRACT_V35 = "v3.5-facts"`,
  `SUPPORTED_CONTRACTS`. An unrecognised contract raises `OperatorError` —
  fail-closed, never a silent downgrade to the older surface.
- `build_facts(...)` — **signature unchanged**, still exactly
  `{question, question_date, sessions}`, still emitting v3.4. The gold-blindness
  signature pin in `tests/test_dense_chain_reasoning_operators.py` was left
  untouched and still passes. The frozen entrypoint cannot be *handed* a
  contract, so no caller reaches a newer surface by accident.
- `build_facts_contract(..., contract=CONTRACT_V34)` — the new versioned
  entrypoint. Four inputs: the three frozen ones plus the version selector. No
  gold, no answer, no judge.
- `intext_date_anchors()`, `IntextAnchor`, `_resolve_intext_year()`,
  `_clip_span()`, `_intext_anchor_lines()` — the extraction, adapted from
  `scripts/v4_selector.py`'s measured logic.
- `_date_duration_lines()` gained `contract` + `truncated`. Under v3.5 the
  in-text block is **appended after** the header-derived lines; the v3.4 lines
  keep their exact text and position.

Extraction is gold-blind: fixed regexes over packet text only, fixed year
resolution, fixed chronological order, fixed caps (`MAX_INTEXT_ANCHORS = 12`,
`MAX_INTEXT_SPAN_CHARS = 200`). Scoped to **matched USER lines** only.

### Two defects found by the new tests, during this work

- **Year fallback picked `base_year - 1` on an undated session.** With no
  session date every candidate year had distance 0, so the tie-break chose the
  earliest. A session whose `date:` header failed to parse would have silently
  dated every statement in it a year early. Fixed: with nothing to be near, the
  fixed base year 2023 is the only candidate. Latent on this corpus — the
  artifact hashes are unchanged by the fix — but real.
- **Provenance quote could omit the date it claimed.** The first clip took the
  leading 200 characters of the source line, which on `08f4fc43` cut the
  sentence off *before* "January 2nd": a resolved date shown next to a quote not
  containing it. Fixed: the window is centred on the surface, with the cut side
  marked. Pinned by `test_quoted_span_always_contains_the_surface_it_resolved`.

## 2. Regeneration — commands and hashes

Driver: `eval/dense_chain_v32_20260830/v4/anchors/gen_facts_v35.py`. It lives in
this directory rather than in `scripts/` because the wave-2 write scope permits
exactly one shared-file edit (`dense_chain_reasoning_operators.py`); adding a
`--contract` flag to `scripts/run_dense_chain_failure_closure.py` would have
been a second one. It reuses that runner's loaders and hashing verbatim and
emits the **identical row schema** — `facts_v35.jsonl` is a drop-in substitute
for `facts_v34.jsonl` anywhere the reader lane takes `--facts`. Anchor
provenance goes to a separate sidecar so it cannot perturb the served artifact.

```
python3 eval/dense_chain_v32_20260830/v4/anchors/gen_facts_v35.py \
  --materialized eval/dense_chain_v32_20260830/materialized.jsonl \
  --data /Users/cj/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json \
  --out eval/dense_chain_v32_20260830/v4/anchors/facts_v35.jsonl \
  --anchors-out eval/dense_chain_v32_20260830/v4/anchors/anchors_v35.jsonl \
  --contract v3.5-facts

python3 eval/dense_chain_v32_20260830/v4/anchors/gen_facts_v35.py \
  --materialized eval/dense_chain_v32_20260830/materialized_abs.jsonl \
  --data /Users/cj/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json \
  --out eval/dense_chain_v32_20260830/v4/anchors/facts_abs_v35.jsonl \
  --anchors-out eval/dense_chain_v32_20260830/v4/anchors/anchors_abs_v35.jsonl \
  --contract v3.5-facts
```

| artifact | rows | sha256 |
|---|---:|---|
| `facts_v35.jsonl` | 240 | `8ebeedc8252662a50c82667a6a8bfde8b090394f1b91ed7ca58ac10adcbe4b90` |
| `facts_abs_v35.jsonl` | 17 | `71964ff81198898c72629e7c3aab15d38315d64c61cbeb99d8eff76a8195e8b2` |
| `anchors_v35.jsonl` | 240 | `92f58265c65087d451296c0460dbf44bcd6ff45bbdfd43c5ab748e29241068f0` |
| `anchors_abs_v35.jsonl` | 17 | `45021101cc49326893ab34c2c000de4bcaa31c0d5557689e44d140abfaf0dda1` |

Both `materialized_sha256` values recorded in the summaries match the frozen
v3.4 summaries, so the two contracts read identical inputs.

### v3.4 byte-identity (the regression gate)

The same driver at `--contract v3.4-facts` reproduces the frozen artifacts
exactly, through the edited module:

| artifact | expected sha256 | result |
|---|---|---|
| `facts_v34.jsonl` (240 rows) | `259adccb072909cebbba8d80ce5f7ea9238a33cac18d29df416cf893eb89dae8` | **MATCH** (`cmp` identical) |
| `facts_abs_v34.jsonl` (17 rows) | `d1e6f833c71bd5c7c2d056baf49eb27687b6827651ae77282c66789e1a149722` | **MATCH** (`cmp` identical) |

Also pinned as a test:
`tests/test_v35_date_anchors.py::test_v34_output_is_byte_identical_at_corpus_scale`
recomputes all 257 rows through `build_facts` and asserts both hashes.

### Determinism

Two independent full v3.5 runs produced byte-identical `facts_v35.jsonl`
(`cmp` clean). Unit-level determinism is pinned by
`TestDeterminism::test_two_runs_are_byte_identical`.

## 3. Rows changed — counts

| arm | rows | changed | rows where in-text dates were FOUND | rows where anchors were EMITTED |
|---|---:|---:|---:|---:|
| answerable | 240 | 51 | 85 | 51 |
| abs | 17 | 3 | 4 | 3 |
| **total** | **257** | **54** | **89** | **54** |

**54 changed ≤ 80 (acceptance met).**

Concentration checks, all computed mechanically in `diff_v34_v35.json`:

| check | result |
|---|---|
| changed rows activating `date_duration` | 54 / 54 |
| changed rows where every added anchor line names its provenance | 54 / 54 |
| changed rows with any v3.4 line removed or rewritten | **0 / 54** |
| rows with in-text dates that did **not** change | 35 — all 35 lack `date_duration`; the block is operator-scoped |
| added lines per changed row | 3 – 12 |
| anchors emitted per changed row | 1 – 8 (111 total) |

By selector class (class labels are derived from question text by the v4
selector — **not** from gold):

| selector class | changed |
|---|---:|
| date_interval | 33 |
| count_enumeration | 8 |
| passthrough | 6 |
| count_quantity | 4 |
| recency_value | 2 |
| date_anchor | 1 |

By question type: temporal-reasoning 39, multi-session 14, single-session-user 1.

**Concentration verdict: yes.** 34/54 are the two explicit date classes
(date_interval + date_anchor) and 39/54 are `temporal-reasoning` questions. The
remaining 20 are neighbours by construction, not leakage: the block fires on the
`date_duration` operator, and that operator activates on "order / earliest /
latest / when did / N days ago" phrasing which the selector may classify as a
count or recency question. Example: `ba358f49` ("How many years will I be when
my friend Rachel gets married?") is `count_enumeration` to the selector and an
elapsed-time question in fact.

### The wave-1 class

Recomputed independently from the packets (gold-blind: a session-day count):

| population | rows |
|---|---:|
| facts rows activating `date_duration` | 119 |
| … of those, packets with exactly ONE distinct session day | 32 |
| … of those, now served by an in-text anchor | **22** |
| … of those, still unserved (no parseable date anywhere in the prose) | 10 |
| `date_duration` rows with ≥2 session days that also gained anchors | 32 of 87 |

The 10 still-unserved single-session-day rows: `157a136e`, `2e6d26dc`,
`58ef2f1c`, `6cb6f249`, `81507db6`, `982b5123`, `c8090214_abs`,
`gpt4_372c3eed`, `gpt4_372c3eed_abs`, `gpt4_5dcc0aab`. These packets contain no
extractable date in either the headers or the prose; v3.5 does not reach them
and does not pretend to.

### "Zero changes on rows that already had multi-anchor coverage"

**Not met as literally stated — 32 multi-session-day rows changed — and that is
the design, justified here rather than waived.** A packet with several session
days already had a usable header chronology, so it was never blind; but the
in-text anchors on those rows date the *events* while the headers date the
*typing*, and those are different facts. Two things bound the risk:

- The change is **purely additive on every one of the 32** (0 removed lines,
  verified above). Nothing the reader relied on under v3.4 moved.
- Most are small: 23 of the 32 add a single anchor (3–4 lines).

The alternative — gating the block on `n_session_days == 1` — would have been a
selection rule tuned to the failure population rather than to the defect, and
the defect ("the operator cannot see dates in prose") is not conditional on
session-day count. If the live measurement shows control regressions on
multi-day rows, that gate is the obvious first knob.

## 4. Before / after — three single-session-day rows

### `08f4fc43` — date_interval, temporal-reasoning, 1 session day (the acceptance row)

> How many days had passed between the Sunday mass at St. Mary's Church and the Ash Wednesday service at the cathedral?

16 sessions, every header `2023/02/20`. Note what v3.4 does and does not do: the
prose **is** displayed in the matched-lines block, so the reader can read the
words "January 2nd". What v3.4 cannot do is **parse** them — no resolved date,
no anchor, no interval. The computed-evidence block offers a one-day chronology
for a two-date question and leaves the arithmetic entirely to the reader.

**v3.4 — date/duration lines of the computed-evidence block**

```
  * Distinct matched-user-line dates (earliest to latest): 2023/02/20 (Mon) 14:36
  * Offset from question date (2023/02/20 (Mon) 21:26): 2023/02/20 (Mon) 14:36 = +0 days
```

**v3.5 — same block**

```
  * Distinct matched-user-line dates (earliest to latest): 2023/02/20 (Mon) 14:36
  * Offset from question date (2023/02/20 (Mon) 21:26): 2023/02/20 (Mon) 14:36 = +0 days
  * In-text date anchors (dates stated INSIDE the user's own matched lines, which the session date headers above cannot see; a stated month/day carries no year, so the year shown is the reading nearest the session the statement was written in — a back-reference more than ~6 months old can resolve to the wrong year, so check the quoted sentence before using one):
    - 2023/01/02 from "January 2nd" — session #4 answer_6ea1541e_1 (2023/02/20 (Mon) 16:20) line 1: … mation on organizations that focus on serving the homeless? By the way, I recently attended the Sunday mass at St. Mary's Church on January 2nd, and the sermon on forgiveness really resonated with me.
    - 2023/02/01 (+30 days from previous) from "February 1st" — session #2 answer_6ea1541e_2 (2023/02/20 (Mon) 04:43) line 1: … e impact during my time there. By the way, I just came from the Ash Wednesday service at the cathedral on February 1st, and it really made me reflect on the importance of giving back to the community.
  * In-text anchor span (earliest to latest): 30 days (2023/01/02 to 2023/02/01)
  * In-text anchor offsets from question date (2023/02/20 (Mon) 21:26): 2023/01/02 = -49 days; 2023/02/01 = -19 days
```

Both required anchors present, both with provenance.

### `2a1811e2` — date_interval, temporal-reasoning, 1 session day

> How many days had passed between the Hindu festival of Holi and the Sunday mass at St. Mary's Church?

**v3.4**

```
  * Distinct matched-user-line dates (earliest to latest): 2023/03/26 (Sun) 12:48
  * Offset from question date (2023/03/26 (Sun) 12:05): 2023/03/26 (Sun) 12:48 = +0 days
```

**v3.5**

```
  * Distinct matched-user-line dates (earliest to latest): 2023/03/26 (Sun) 12:48
  * Offset from question date (2023/03/26 (Sun) 12:05): 2023/03/26 (Sun) 12:48 = +0 days
  * In-text date anchors (…):
    - 2023/02/26 from "February 26th" — session #1 answer_1cc3cd0c_1 (2023/03/26 (Sun) 12:48) line 1: … e information on Hindu festivals. I just attended the Holi celebration at my local temple on February 26th and had a blast throwing colors and learning about its significance. Can you tell me more abo …
    - 2023/03/19 (+21 days from previous) from "March 19th" — session #2 answer_1cc3cd0c_2 (2023/03/26 (Sun) 01:51) line 1: … ies that have been successful in the past. By the way, I just got back from Sunday mass at St. Mary's Church on March 19th, where Father John's sermon really inspired me to give back to the community.
  * In-text anchor span (earliest to latest): 21 days (2023/02/26 to 2023/03/19)
  * In-text anchor offsets from question date (2023/03/26 (Sun) 12:05): 2023/02/26 = -28 days; 2023/03/19 = -7 days
```

### `ba358f49` — count_enumeration (selector) / elapsed-time in fact, 1 session day

> How many years will I be when my friend Rachel gets married?

Included because it is the **worst** case, not the best: both anchors trip the
after-question-date guard and both quoted sentences are past-tense ("a
particularly vivid dream I **had** on February 15th"), so the resolved 2023
years are very likely wrong and the 31-day span computed from them is very
likely meaningless. This is what the caution machinery is for — the reader is
handed the alternative reading and the sentence that decides it.

**v3.4**

```
  * Distinct matched-user-line dates (earliest to latest): 2022/09/01 (Thu) 03:06
  * Offset from question date (2022/09/01 (Thu) 23:52): 2022/09/01 (Thu) 03:06 = +0 days
```

**v3.5**

```
  * In-text date anchors (…):
    - 2023/01/15 from "January 15th" — session #16 f6859b48_2 (2022/09/01 (Thu) 12:29) line 1: … . By the way, I just finished listening to a true crime podcast that my sister recommended to me on January 15th, and it got me thinking about how important it is to take risks and pursue my passions. [resolves 136 days AFTER the question date; if this statement is retrospective the intended date is 2022/01/15 — the quoted sentence's tense decides]
    - 2023/02/15 (+31 days from previous) from "February 15th" — session #13 385683f0_2 (2022/09/01 (Thu) 02:52) line 1: … e juices flowing. By the way, I've been keeping a journal and recently wrote about a particularly vivid dream I had on February 15th - it was so real that it took me a while to shake off the emotions. [resolves 167 days AFTER the question date; if this statement is retrospective the intended date is 2022/02/15 — the quoted sentence's tense decides]
  * Caution: 2 of 2 in-text anchors resolve after the question date. If those statements are retrospective, the year is one too high and every interval below that uses them is wrong by 365 days — re-read the quoted sentence before using one.
  * In-text anchor span (earliest to latest): 31 days (2023/01/15 to 2023/02/15)
  * In-text anchor offsets from question date (2022/09/01 (Thu) 23:52): 2023/01/15 = +136 days; 2023/02/15 = +167 days
```

## 5. Disclosed limits

**L1 — year resolution is a heuristic (carried from selector L7).** A stated
month/day has no year. The rule is "the reading nearest the session the
statement was written in": deterministic, gold-blind, and wrong for any
back-reference more than ~6 months old. The block discloses this in its own
header text.

**L2 — the heuristic has no tense signal, and it costs.** 34 of 111 emitted
anchors resolve **after** the question date; classifying the quoted sentence by
verb tense, 29 of those 34 are past-tense prose (likely wrong year), 3 are
explicitly forward-looking ("I'm training for a sprint triathlon on November
1st" — correctly future), 2 ambiguous. So roughly **26% of emitted anchors
probably carry the wrong year.** Silently flipping them to the prior year would
break the 3 genuinely-future ones just as silently, and no gold-blind signal
separates the two. The block therefore does what the count operator does with an
ambiguous count and the recency operator does with a tied timestamp: **emits
both readings and commits to neither**, beside the sentence whose tense decides
it. 21 of 54 changed rows carry the resulting `Caution:` line. This is a
disclosure, not a fix — if the live measurement shows these rows regressing, the
next move is to suppress the anchor rather than to guess the year.

**L3 — "may" is both a month and a modal.** The month regex accepts bare `may
<digits>`. Audited on this corpus: all 6 "May"-sourced anchors carry ordinal
suffixes ("May 15th", "May 10th", "May 28th") and are genuine dates. Zero false
positives observed here; the ambiguity remains latent for other corpora.

**L4 — numeric `m/d` extraction is deliberately permissive.** Out-of-range
readings self-reject, which disqualifies "1/72 scale", "50/50", "24/7" and
"15/16" without any content rule (pinned as negative controls). 10 of 111
anchors came from this form.

**L5 — anchors are capped at 12 per row.** No row on this corpus hit the cap
(max observed 8), so the truncation path is exercised only by unit test.

**L6 — no live reader measurement.** Everything above is a property of the
emitted text. Whether the reader *uses* the anchors is unmeasured. See §7.

## 6. Gold usage

**No gold in generation.** `gen_facts_v35.py` reads question text, question
date, and session blobs. The `selector_class` labels used above are derived from
question text by the v4 selector, not from gold.

**SCORING-ONLY note (not an input to anything):** of the 32 changed rows in the
two date classes that carry a numeric gold value, **12** have a gold value equal
to some pairwise gap between the emitted in-text anchors. That is a coverage
upper-bound on those rows and nothing more — it does not say the reader will
pick that pair, and it was computed after generation from
`v4/selector/replay_rows.jsonl`.

## 7. Is a live pilot on `v4/pilot/PILOT_SET.json` ready to run?

**No — the frozen pilot is the wrong instrument for this change, and running it
would produce an uninterpretable null.**

Pilot set (freeze seal `4c9feeac…`): 27 target, 60 control, 2 claim-excluded.
Overlap with the 54 v3.5-changed rows:

| pilot category | rows | changed under v3.5 | ids |
|---|---:|---:|---|
| target | 27 | **1** | `gpt4_7abb270c` |
| control | 60 | 4 | `60bf93ed_abs`, `bbf86515`, `e831120c`, `f0853d11` |

Its acceptance rule is "net >= +4 on TARGET rows with <= 1 CONTROL regression".
With one changed target row the **maximum attainable net is +1**, so v3.5 fails
that rule for arithmetic reasons regardless of quality. Meanwhile the only
non-zero-variance contribution is on the control side, where v3.5 can lose but
cannot win. The pilot set was frozen against a different intervention.

**What to run instead** — a date-class A/B on the rows the change actually
touches, with the unchanged rows as the control:

- **Treatment arm:** the 54 changed rows, `--facts facts_v35.jsonl` (+
  `facts_abs_v35.jsonl`) vs. the same rows under `facts_v34.jsonl`.
- **Control arm:** the 65 `date_duration` rows that did **not** change (119 − 54).
  Their facts_text is byte-identical across contracts, so any delta there is
  reader/judge noise and calibrates the treatment delta.
- **Pre-registered split:** report the 22 single-session-day rows separately
  from the 32 multi-session-day rows. They are different bets — the first is the
  finding, the second is a design choice — and pooling them hides which one paid.
- **Pre-registered subgroup:** the 21 rows carrying a `Caution:` line. If v3.5
  regresses, L2 is the first place to look, and this subgroup isolates it.

Everything needed for that run exists: `facts_v35.jsonl` is a drop-in `--facts`
sidecar with the frozen row schema. The reader dispatch itself is an operator
call — no live reader or judge was run in this wave.

### Prerequisite before ANY live run — recorded, not fixed (out of write scope)

**`scripts/run_lme_qa_flash_packets.py:65` hard-pins
`PROMPT_VERSION_V3_FACTS = "v3.4-facts-20260831"`.** It is stamped onto every
facts row's receipt and is pinned by five assertions in
`tests/test_run_lme_qa_flash_packets.py` (lines 138, 325, 383, 434, 443). Serve
`facts_v35.jsonl` through that runner as-is and **every row will be labelled
v3.4 while carrying v3.5 text** — the receipts would misattribute the scaffold,
which is exactly the failure mode the contract gating was built to prevent. The
constant is claim-lock-adjacent, so it needs an owner decision (bump vs. add a
v3.5 constant vs. pass the contract through), not a drive-by edit. This wave's
write scope was one shared file and it was not this one.

**`scripts/v4_pilot_run.py` (untracked, another wave-2 worker, mtime 16:42
during this run) already names
`eval/dense_chain_v32_20260830/v4/anchors/facts_v35.jsonl` in its usage
example.** The path matches this artifact exactly, so nothing needs to move. Its
own `--contract` flag is a **prompt** contract (`v4-citation`), a different axis
from the facts contract added here — the two names collide conceptually and
should not be conflated when the run is configured. Not touched: single-writer.

## 8. Files

| path | role |
|---|---|
| `scripts/dense_chain_reasoning_operators.py` | the one shared-file edit |
| `tests/test_v35_date_anchors.py` | 43 tests: byte-identity regression, extraction, year resolution, negative controls, caps, provenance coupling, determinism, acceptance row |
| `eval/dense_chain_v32_20260830/v4/anchors/gen_facts_v35.py` | generation driver (both contracts) |
| `eval/dense_chain_v32_20260830/v4/anchors/diff_v34_v35.py` | diff + additive-check tool |
| `eval/dense_chain_v32_20260830/v4/anchors/facts_v35.jsonl` | 240 rows, v3.5, drop-in `--facts` |
| `eval/dense_chain_v32_20260830/v4/anchors/facts_abs_v35.jsonl` | 17 rows, v3.5, abs arm |
| `eval/dense_chain_v32_20260830/v4/anchors/anchors_v35.jsonl` | per-row anchor provenance sidecar |
| `eval/dense_chain_v32_20260830/v4/anchors/anchors_abs_v35.jsonl` | same, abs arm |
| `eval/dense_chain_v32_20260830/v4/anchors/diff_v34_v35.json` | machine-readable diff audit |

Test result: `179 passed` across `tests/test_v35_date_anchors.py` (43) and
`tests/test_dense_chain_reasoning_operators.py` (136, unchanged and untouched).

## 9. Full changed-row list (54)

`sd` = distinct session days in the packet · `anch` = in-text anchors emitted ·
`+ln` = lines added · `caution` = carries the after-question-date caution line.

| question_id | arm | selector class | question type | sd | anch | +ln | caution |
|---|---|---|---|---:|---:|---:|---|
| `60bf93ed_abs` | abs | date_interval | multi-session | 1 | 3 | 7 | yes |
| `982b5123_abs` | abs | date_anchor | temporal-reasoning | 1 | 4 | 7 | no |
| `edced276_abs` | abs | count_quantity | multi-session | 7 | 1 | 3 | no |
| `08f4fc43` | answerable | date_interval | temporal-reasoning | 1 | 2 | 5 | no |
| `0bb5a684` | answerable | date_interval | temporal-reasoning | 1 | 4 | 8 | yes |
| `0bc8ad92` | answerable | date_interval | temporal-reasoning | 7 | 1 | 3 | no |
| `0bc8ad93` | answerable | passthrough | temporal-reasoning | 8 | 1 | 4 | yes |
| `0db4c65d` | answerable | date_interval | temporal-reasoning | 13 | 1 | 3 | no |
| `0ea62687` | answerable | count_enumeration | multi-session | 7 | 1 | 3 | no |
| `10d9b85a` | answerable | count_enumeration | multi-session | 1 | 2 | 5 | no |
| `2a1811e2` | answerable | date_interval | temporal-reasoning | 1 | 2 | 5 | no |
| `2c63a862` | answerable | date_interval | temporal-reasoning | 1 | 3 | 6 | no |
| `2ce6a0f2` | answerable | count_quantity | multi-session | 1 | 4 | 7 | no |
| `311778f1` | answerable | count_quantity | single-session-user | 7 | 2 | 5 | no |
| `4dfccbf7` | answerable | date_interval | temporal-reasoning | 13 | 2 | 5 | no |
| `4dfccbf8` | answerable | passthrough | temporal-reasoning | 10 | 1 | 3 | no |
| `5a7937c8` | answerable | count_enumeration | multi-session | 1 | 4 | 7 | no |
| `60159905` | answerable | count_enumeration | multi-session | 9 | 1 | 3 | no |
| `60bf93ed` | answerable | date_interval | multi-session | 1 | 4 | 8 | yes |
| `6613b389` | answerable | date_interval | temporal-reasoning | 1 | 2 | 6 | yes |
| `8077ef71` | answerable | date_interval | temporal-reasoning | 3 | 1 | 4 | yes |
| `8c18457d` | answerable | date_interval | temporal-reasoning | 1 | 2 | 5 | no |
| `9a707b81` | answerable | date_interval | temporal-reasoning | 10 | 1 | 3 | no |
| `a08a253f` | answerable | count_enumeration | multi-session | 10 | 2 | 6 | yes |
| `a3045048` | answerable | date_interval | temporal-reasoning | 1 | 4 | 7 | no |
| `af082822` | answerable | date_interval | temporal-reasoning | 5 | 1 | 4 | yes |
| `b3c15d39` | answerable | date_interval | multi-session | 1 | 2 | 5 | no |
| `b5ef892d` | answerable | count_enumeration | multi-session | 1 | 1 | 4 | yes |
| `ba358f49` | answerable | count_enumeration | multi-session | 1 | 2 | 6 | yes |
| `bbf86515` | answerable | date_interval | temporal-reasoning | 1 | 4 | 8 | yes |
| `bcbe585f` | answerable | date_interval | temporal-reasoning | 5 | 2 | 5 | no |
| `c8090214` | answerable | date_interval | temporal-reasoning | 1 | 1 | 4 | yes |
| `dcfa8644` | answerable | date_interval | temporal-reasoning | 1 | 8 | 12 | yes |
| `e831120c` | answerable | date_interval | multi-session | 8 | 1 | 3 | no |
| `f0853d11` | answerable | date_interval | temporal-reasoning | 1 | 2 | 5 | no |
| `gpt4_1e4a8aeb` | answerable | date_interval | temporal-reasoning | 6 | 2 | 6 | yes |
| `gpt4_21adecb5` | answerable | date_interval | temporal-reasoning | 12 | 1 | 3 | no |
| `gpt4_4cd9eba1` | answerable | count_quantity | temporal-reasoning | 1 | 4 | 8 | yes |
| `gpt4_4fc4f797` | answerable | date_interval | temporal-reasoning | 13 | 2 | 5 | no |
| `gpt4_61e13b3c` | answerable | date_interval | temporal-reasoning | 13 | 1 | 3 | no |
| `gpt4_731e37d7` | answerable | count_enumeration | multi-session | 1 | 3 | 7 | yes |
| `gpt4_7a0daae1` | answerable | date_interval | temporal-reasoning | 4 | 1 | 3 | no |
| `gpt4_7abb270c` | answerable | recency_value | temporal-reasoning | 13 | 1 | 3 | no |
| `gpt4_7bc6cf22` | answerable | date_interval | temporal-reasoning | 3 | 1 | 3 | no |
| `gpt4_8279ba03` | answerable | passthrough | temporal-reasoning | 11 | 1 | 3 | no |
| `gpt4_8e165409` | answerable | date_interval | temporal-reasoning | 7 | 1 | 3 | no |
| `gpt4_af6db32f` | answerable | date_interval | temporal-reasoning | 13 | 1 | 4 | yes |
| `gpt4_b0863698` | answerable | date_interval | temporal-reasoning | 13 | 1 | 3 | no |
| `gpt4_b5700ca0` | answerable | passthrough | temporal-reasoning | 10 | 4 | 8 | yes |
| `gpt4_e061b84g` | answerable | passthrough | temporal-reasoning | 6 | 1 | 4 | yes |
| `gpt4_e072b769` | answerable | date_interval | temporal-reasoning | 6 | 1 | 3 | no |
| `gpt4_f420262c` | answerable | recency_value | temporal-reasoning | 14 | 2 | 6 | yes |
| `gpt4_f49edff3` | answerable | passthrough | temporal-reasoning | 8 | 3 | 7 | yes |
| `gpt4_fa19884c` | answerable | date_interval | temporal-reasoning | 9 | 1 | 3 | no |
