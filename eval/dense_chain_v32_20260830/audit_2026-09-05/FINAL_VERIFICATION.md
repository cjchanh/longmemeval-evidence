# FINAL VERIFICATION — corrected LongMemEval evidence release

Adversarial read-only pass on a frozen tree. Zero model/provider/network calls.
No git writes. One file written: this one.

- Repo: `/Users/cj/Workspace/active/longmemeval-evidence-release`
- HEAD at start and end: `0fc232b0c4b1ca18d1b937d2b562ff3aa1e1a1a6`
- Verifier model: `claude-opus-5[1m]`
- Date: 2026-09-06

**Verdict:** every ROOT-VERIFIED ANCHOR reproduces exactly — all six, no
exceptions. The $500 correction itself is sound and complete in the four
documents it targeted. What the campaign did **not** finish is (1) a stale
self-consistency section in the paper `.md` that the `.tex` already retired,
(2) a released JSON receipt still carrying the withdrawn `478/476`, (3) two
stale counts in `SOTA_WRITEUP.md`, and (4) a comparator sentence that is now
falsifiable against a source the campaign itself pinned into the release.

---

## Findings, most severe first

### F1 — MISSED / INCONSISTENT (severe)
**File:** `paper/longmemeval_auditable_memory_paper.md` §4.4, lines 190–212
(heading line 190: `**4.4 Self-consistency on measured flip rows (frozen rule).**`)

**Claim as written:** the self-consistency tie-break is presented as a live,
endorsed method with its results reported affirmatively — *"SC resolved four of
the eight rows to correct and four to wrong, moving the higher pass down —
pass 1 went 476 → 475 and pass 2 went 474 → 475. The frozen rule cost us the
best single number we had measured and converged the pair on the midpoint of
the raw spread, not its maximum — which is what a variance-collapse rule should
do and a score-maximizing rule would not."*

**What I found:** `476 → 475` / `474 → 475` **is** the withdrawn 475/475 pair.
`SOTA_WRITEUP.md` lines 42–49 state it *"is WITHDRAWN and not claimed in any
form"*. The `.tex` §4.4 (line 191, `\textbf{4.4 Self-consistency tie-break
(built, then withdrawn).}`) says *"The resulting number was WITHDRAWN from any
claim … no self-consistency number is claimed anywhere in this report."*
The `.md` therefore (a) contradicts the `.tex` head-on, (b) contradicts
**itself** — its own §5.1 line 267 says *"later WITHDRAWN from any claim …
no SC number is claimed"* — and (c) republishes the retracted figures in the
one place a reader looks for the method. Its §6.4 closer (line 445) compounds
this: *"the measured flip-noise rows addressed by §4.4"* presents SC as the
remedy, where the `.tex` says only *"Remaining failures are measured flip
noise."* Note the string search the campaign would naturally run (`475/475`,
`475/500 and 475/500`) does **not** hit this passage — the numbers appear as an
arrow transition, which is why it survived.

**Minimal correction:** port the `.tex` §4.4 verbatim into the `.md` (heading
included) and drop the `§4.4` reference from `.md` §6.4's last sentence, so the
`.md` matches the tex/PDF the release actually publishes.

---

### F2 — MISSED (high)
**File:** `eval/dense_chain_v32_20260830/v34_full_pair_attribution.json`, key
`gold_defect_note` (line 98 of the pretty-printed source)

**Claim:** *"5 documented gold-defect candidates unclaimed in this number; with
defensible gold corrections the pair would read ~478/476."*

**What I found:** this file is git-tracked and carries manifest row
`RELEASE_MANIFEST.md:361` (`2ff8900406e832…`), so it ships as released
evidence. `478/476` is exactly the adjudicated figure the campaign removed from
the dossier, `SOTA_WRITEUP.md`, the `.md`, and the `.tex`; the campaign's own
`audit_2026-09-05/DOSSIER_CLAIM_AUDIT.md` scores it **CONTRADICTED** (C56).
"5 documented gold-defect candidates" is also stale — the dossier now lists
1 strict (B) + 7 boundary (D). The correct adjudicated grok pair is **477/475**.

**Minimal correction:** either add a one-line `superseded_by` field pointing at
`GOLD_DEFECT_DOSSIER.md` §Correction record (the pattern already used for
`judge_gpt4o/SUPERSEDED.md`), or restate the note as `1 strict defect;
adjudicated 477/475`. Both change a released hash, so the manifest and
`RELEASE_MANIFEST.root` regenerate with it.

---

### F3 — DISAGREES (high) — the md/tex/PDF all say something the release's own
### pinned comparator refutes
**Files:** `.md` line 294–299; `.tex` lines 283–288; PDF p.5 — identical text.

**Claim:** *"our pass-1 gap is −3 knowledge-update and −1 preference, partially
offset by +2 multi-session (120/133 vs. their 118/133); pass 2 trails on
multi-session as well (116/133), so our multi-session score exceeds theirs in
pass 1 only."*

**What I found (from `comparators/chronos-arxiv-2603.16862.pdf`, Table 4, hash
verified `a6a75d61…`):** Chronos High = KU 100.00%(78/78), MS 88.72%(118/133),
SSA 100%(56/56), **SSP 100.00% (30/30)**, SSU 98.57%(69/70), TR 95.49%(127/133)
= 478. Our abstention-folded Opus pass 1 = KU 75/78, MS 120/133, SSA 56/56,
**SSP 30/30**, SSU 70/70, TR 128/133 = 479.

Three errors:
1. **"−1 preference" is impossible.** Both sides are 30/30 → delta 0. A −1 gap
   would require Chronos at 31/30.
2. **The offsets are undercounted.** True deltas: KU −3, MS +2, SSU +1, TR +1,
   SSA 0, SSP 0 → net **+1**, which is what 479 − 478 requires. As written the
   enumerated deltas sum to −2 and cannot reconcile with the headline.
3. **"pass 2 … (116/133)" is the wrong reader.** Opus pass 2 is **118/133** —
   identical to Chronos's 118/133, i.e. it **ties**, it does not trail. 116/133
   is the *grok* pass-2 value; a grok number is standing inside an Opus
   sentence.

**Minimal correction:** *"our pass-1 deltas are −3 knowledge-update, +2
multi-session (120/133 vs. their 118/133), +1 single-session-user and +1
temporal-reasoning — net +1; pass 2 matches their multi-session exactly
(118/133)."*

---

### F4 — MISSED (medium)
**File:** `SOTA_WRITEUP.md` line 179

**Claim:** *"RELEASE_MANIFEST.md, 449 files, sha256 each; fresh clone verified
449/449"*

**What I found:** the manifest header reads **466 files · 96.9 MB**, and
`build_release_manifest.py --check` confirms `OK: 466 files`. The campaign knew
this number was stale: it deleted the identical phrase from the `.tex`
(`- verifies 449/449 manifest hashes` → `verifies every RELEASE_MANIFEST.md
row`) and `README.md` already defers to the manifest header. Only
`SOTA_WRITEUP.md` still asserts 449.

**Minimal correction:** replace with *"RELEASE_MANIFEST.md, one sha256 per
released file; fresh clone verifies every row"* — the same phrasing the tex now
uses, so it cannot go stale again.

---

### F5 — MISSED / INCONSISTENT (medium)
**Files:** `SOTA_WRITEUP.md` line 132 (`## What still fails (24 answerable
rows), attributed`); `.md` line 369; `.tex` line 355 (`Of 470 answerable
questions, 24 fail in at least one … pass`).

**What I found:** no configuration yields 24. Failing answerable rows —
grok p1 20, grok p2 23, **grok-pair union 25**; Opus p1 18, Opus p2 20,
**Opus-pair union 22**; **all-four-pass union 35**. `SOTA_WRITEUP.md`'s own body
says *"19/23 failing rows have gold-complete packets"* — 23, not 24. The `.md`
partition sentence (`4 + 8 + 4 + 8 = 24`) was **edited by this campaign**
(`8 gold-defect (2 strict, 6 boundary)` → `(1 strict, 7 boundary)`) without
re-deriving the 24 it sums to.

**Minimal correction:** state 25 for the grok pair (`4 reader-cognition +
8 gold-defect + 4 retrieval/ordering + 9 flip-noise = 25`), or scope the
sentence to a single pass and use that pass's count.

---

### F6 — DISAGREES (medium)
**File:** `SOTA_WRITEUP.md` line 39–40

**Claim:** *"We beat Chronos on multi-session (119 vs 118); the 4-row gap is
3 knowledge-update + 1 SSP-abstention row."*

**What I found:** two defects.
- **119 is not a measurement.** Abstention-folded multi-session is Opus p1
  **120/133**, Opus p2 **118/133**; 119 is the unlabeled pair mean. It also
  disagrees with the paper, which states 120/133 for the same comparison (F3).
- **"1 SSP-abstention row" cannot exist.** LongMemEval-S has **zero**
  single-session-preference abstention rows (SSP: n=30 total, n=30 answerable;
  the 30 abstention rows are KU 6, MS 12, SSU 6, TR 6, SSA 0, SSP 0). And there
  is no 4-row gap: Opus p1 leads Chronos by +1 (479 vs 478).

**Minimal correction:** *"Opus pass 1 leads Chronos on multi-session (120/133
vs 118/133) and trails by 3 on knowledge-update (75/78 vs 78/78); net +1."*

---

### F7 — OVERCONFIDENT (low)
**Files:** `.md` line 240; `.tex` line 227; PDF p.4

**Claim:** *"Its 8 flip rows (6 lost — including 2 abstentions and **2
dossier-listed flip-prone rows** — 2 gained)"*

**What I found:** the Opus pair's 6 lost rows are `88432d0a`, `09d032c9`,
`57f827a0`, `37f165cf`, `60bf93ed_abs`, `031748ae_abs`. Exactly **one** —
`88432d0a` — appears in `GOLD_DEFECT_DOSSIER.md` (line 125, "flip row, p1
correct/p2 wrong"). The dossier's other flip exhibit, `88432d0a_abs`, is
**correct in both Opus passes** and so is not among the lost. Everything else
in the sentence checks out: 8 flips, 6 lost, 2 of them abstentions, 2 gained.

**Minimal correction:** "2 dossier-listed" → "1 dossier-listed".

---

### F8 — INCONSISTENT (low)
**Files:** `.md` line 305–309 (§5.1.1 note); `.tex` line 336–338

**Claim:** *"its 189 scored rows cover single-session-user 64/64, multi-session
73/83, and single-session-preference 21/30 only"*

**What I found:** those three are the **answerable** rows and sum to **177**,
not 189. The judged partial has 189 rows: 177 answerable (158 correct) plus 12
abstention rows (12/12 correct), which the enumeration omits. On the folded
basis the same file reads SSU 70/70, MS 79/89, SSP 21/30. `SOTA_WRITEUP.md`'s
"gemini-3.7-flash partial 89.3%" is the answerable-only rate (158/177 =
89.27%); the all-189 rate is 89.9%.

**Minimal correction:** *"189 scored rows — 177 answerable (SSU 64/64, MS
73/83, SSP 21/30) plus 12 abstention rows, all correct."*

---

### F9 — INCONSISTENT (low) — md-internal
**File:** `.md` line 435, heading `### 6.4 Retrieval ceiling (2 rows) and flip
noise`

Its own body and the §6 partition both say **4** rows (1 pool-miss + 3
compiler-ordering). The `.tex` heading carries no count and is not wrong.
**Correction:** drop "(2 rows)" or make it "(4 rows)".

---

### F10 — DISAGREES (low) — md vs tex, and md vs its own data
**File:** `.md` line 363–365 vs `.tex` line 348–350

`.md`: *"The packet and scaffold layers carry most of the score; reader choice
moves it by a few points."*
`.tex`: *"reader choice moves it by tens of points across tiers but only a few
points within a tier."*

The `.md` version is contradicted by the same paragraph's own range (Nemotron
93 → Opus 479). The `.tex` is correct. The `.md` also omits the reader-capability
curve `(93 → 436 → 455 → 465 → 471 → 476)` that the `.tex` carries.

---

### F11 — INCONSISTENT (low) — README cites the paper by its old title
**File:** `README.md` lines 3–5

*"Evidence for *Auditable Long-Term Memory: A Deterministic Retrieval Chain at
95.4±0.4% on LongMemEval-S*"* — this is the **pre-correction** title. The
campaign retitled the paper in the `.tex` (`\title{…Scoring 479/475 of 500 on
LongMemEval-S Under the Official Judge}`), in `ARXIV_SUBMISSION.md`, in the
`.md` H1 and in the rendered PDF, but README still names the retired title.
(The `95.4±0.4%` figure is itself fine: 479/500 = 95.8%, 475/500 = 95.0%.)
**Correction:** copy the current title into README.

---

### F12 — OVERCONFIDENT (nit)
**File:** `GOLD_DEFECT_DOSSIER.md` lines 64–67

*"Of the 9 '$500' occurrences in the record, **7** are website cost-filter
boilerplate ('under $100, $100-$500…'), **1** is an immigration-form fee … and
**1** is this user-stated workshop fee."*

The count of 9 and the 7/1/1 split are right, but one of the 7 is not a cost
filter — it is a suggested Google query string, *"writing conferences under
$500"*. Six are literal `$100-$500 / $500-$1000` filter ranges.
**Correction:** "7 are website cost-filter / search-suggestion boilerplate".

---

### F13 — UNTRACEABLE (disclosed, no action needed)
`SOTA_WRITEUP.md` line 36 and paper §5.1 quote OMEGA at 95.4% / raw 466 with a
GPT-4.1 judge. There is no pinned source and no reference entry. The release
already records this against itself in `comparators/MANIFEST.md` §"Not
snapshotted" — *"a release-integrity gap, recorded rather than papered over."*
Verified as disclosed, not as true. Same for the agentmemory "V4" 481 claim,
which both documents explicitly exclude as unreviewable.

---

## Cross-document reference lists (task item 3)

Not identical. The `.md` reference list carries **7 bullets / 12 works**; the
`.tex` carries **6 bullets / 11 works**. The delta is one entry:

| Entry | md | tex |
|---|---|---|
| BAAI, *bge-reranker-v2-m3* | present (line 553) | **absent** |

Wu · Sen (Chronos) · Barnes (Mastra) · Packer · Maharana · Nogueira & Cho ·
Chen · Cormack · Wang · Zheng · Dodge are in both. The campaign added the
Packer/Nogueira/Wang bullets to the `.md` this round but did not add BAAI to
the `.tex`. The `.md` also carries source URLs and per-entry annotations the
`.tex` drops; the `.tex` moves the Chronos `6d550036` / `75f70248` note into
§6.3 instead. **Correction:** add the BAAI entry to the `.tex` (it is the only
substantive gap; a `.tex` edit forces a PDF rebuild, which is an operator call).

Titles agree across `.md` H1, `.tex` `\title`, `ARXIV_SUBMISSION.md`, and the
rendered PDF. Only `README.md` disagrees (F11).

---

## Anchors re-derived (all six PASS)

| # | Anchor | Result |
|---|---|---|
| 1 | `materialized_all.jsonl.gz` / `gpt4_731e37d7`: exactly one `paid $500 to attend`, `user:` turn, session `answer_826d51da_2`, dated `2023/02/26 (Sun) 13:37` | **PASS** — blob index 8 = `answer_826d51da_2`, head `date: 2023/02/26 (Sun) 13:37`, single occurrence in a user turn; `content_sha256` = `5fb5690f4fc06ba5c819875ad3a37fbbf91bbff4f3a059e0c8b720446dc1cf06` as the dossier states |
| 2 | Opus p1 $720/True · Opus p2 $720/True · grok p1 $220/False · grok p2 $220/False; grok p2 text says the $500 is excluded | **PASS** — verbatim grok p2: *"the **$500** is excluded"*; gold `$720`; raws `Yes.` / `Yes.` / `No.` / `No` |
| 3 | Splits 452+27=479 · 450+25=475 · 450+26=476 · 447+27=474 | **PASS** — recounted row-by-row from `rescored.jsonl`, not from the summaries; both agree |
| 4 | `370a8ff4` False in all four passes; `question_type` = temporal-reasoning | **PASS** — gold `15`, all four readers answered 11 (81 days = 11w4d) |
| 5 | Adjudication: Opus 480/476, grok 477/475 | **PASS** — 479+1 / 475+1 and 476+1 / 474+1; `370a8ff4` is 0 in all four passes, so +1 per pass is exact |
| 6 | `judge_gpt4o/`: 194 `attempts:0`, empty raw, null snapshot, all written false; 306/306 agreement with `_v2`; `_v2` scores 190 of the 194 correct; 289+190=479 | **PASS** — every sub-claim, exactly |

Additional independent re-derivations, all PASS: both-pass-stable floors
(Opus 473, grok 471) · Opus 8 flips = 6 lost (2 abstentions) + 2 gained ·
re-judge 478/500 with flips `7024f17c`↓ `031748ae_abs`↓ `a2f3aa27`↑ and
answerable 452/470 identical · strict-abstention 476/472 via
`2133c1b5_abs`/`c8090214_abs`/`f685340e_abs` (GPT-4o accepts, GLM rejects, both
passes) · GLM-vs-GPT-4o 98.2%/97.8% on the grok pair with gpt_only 7/7 and
glm_only 2/4 · reader curve 93 · 436(407/470, abs 29/30) · 455 · 465(444/470,
21/30) · 471(445/470, 26/30) · 476 · xhigh 461/465 · Sol solved 6 of grok's 18
stable-wrong rows · ex-dossier 475/474 (grok) vs 474/471 (Opus) over the exact
8 dossier rows · all seven Class-D rows and both Class-E rows · packet
`facts` n=240 and the four compiler negative controls in
`verification_report.json` · every Wilson interval in §7 (479, 475, 476, 474,
478, 461, 465) · Mastra 468 raw and 94.87% task-average, re-derived from the
pinned HTML.

---

## Everything re-run

| Check | Command / method | Result |
|---|---|---|
| Manifest integrity | `python3 scripts/build_release_manifest.py --check` | **exit 0** — `OK: 466 files, manifest_root_sha256 da55ca5b…` |
| README pinned root | `shasum -a 256 RELEASE_MANIFEST.md` vs README:48 vs `RELEASE_MANIFEST.root` | **all three = `da55ca5b605e…2d6444`** |
| `SUPERSEDED.md` manifest row | grep `RELEASE_MANIFEST.md` | **present**, line 119, 3879 B, `748077f7…` — hash matches the file |
| Test suite | `python3 -m pytest -q tests/` | **154 passed** in 2.13s |
| Mutation — guard (a) `guard_resume_checkpoint` | scratch copy outside repo, early `return`, re-run | **3 failed** (incl. `test_guard_a_detects_the_released_partial_artifact`) |
| Mutation — guard (b) `guard_reader_checkpoint` | same | **4 failed** |
| Mutation — guard (c) receipt/summary overwrite | same | **8 failed** |
| Mutation restore | copy back, re-run | **36 passed**; repo file sha `8c33fd81…` unchanged throughout |
| `arxiv_upload` byte-identity | sha256 both `.tex` | **identical** — `6e36e28913ba8d124179cf310ae2342b67f510e305000b93a4723308f5c48a9e` |
| PDF ↔ tex | `pdfinfo` + `pdftotext -layout` + grep | **9 pages** (matches `ARXIV_SUBMISSION.md` "9 pages"); title matches `\title`; `1 strict, 7 boundary`, `480/476`, `477/475`, `479+1`, `476+1`, `answer_826d51da_2`, `"I paid $500 to attend"`, `2023/02/26 13:37`, `March 15--16`, `$220`, `not a fabrication`, `built, then withdrawn`, `no self-consistency number is claimed`, `475/492`, `474/492`, `strict-defect count is 1 rather than 2` all present |
| Abstract metadata | char/word count of `ARXIV_SUBMISSION.md` abstract | **1467 chars, 216 words** — exactly as stated |
| Harness diff | `git diff scripts/rescore_gpt4o_judge.py` | +260 / −8; see below |
| Packet gz integrity | `gunzip -c \| shasum -a 256` | `materialized_all` 500 rows `a8bfd9d2…`, `facts_all` 257 rows `076108c4…` — both match `packets_materialized/MANIFEST.md` |
| Comparator pins | `shasum -a 256` on all three | **all match** `comparators/MANIFEST.md` |
| Guard regression risk | empty/errored rows in the four released reader checkpoints | **0/1000** — README's documented re-judge command still passes guards (a)/(b) |

### Harness diff (task item 8) — clean
All 8 deleted lines are refactors, none behavioural:
`from collections import defaultdict` → `Counter, defaultdict`; the
`run_controls` signature line and its call site re-wrapped for a new
keyword-only `allow_receipt_overwrite`; `ckpt_path = out_dir / "rescored.jsonl"`
moved earlier so the pre-flight guard can see it; the
`rescore_summary.json` write wrapped in a guard.
Every added path terminates in a **refusal** (`raise ArtifactGuardError` →
caught → `print` → `return 2`) or, under an explicit `--allow-*` flag, a
**warning** that then proceeds unchanged. Judging logic, prompt templates,
rubric, retry/backoff, verdict extraction and the accuracy arithmetic are
untouched. The one non-refusal addition is two new keys in
`rescore_summary.json` (`row_ids_sha256`, `n_rows`) — a receipt-shape change,
not a scoring change. Worth knowing: guard (c-2) refuses by design when an
existing summary lacks `row_ids_sha256`, so re-running into a *legacy* out-dir
now fails closed and needs `--allow-receipt-overwrite`. That is the intended
semantics, and it does not affect a clean `--out-dir` run.

---

## Clean statements — checked, came up empty

- **Fabrication / hallucination framing.** `fabricat*` appears 9 times across
  `README.md`, `GOLD_DEFECT_DOSSIER.md`, `SOTA_WRITEUP.md`, the `.md`, the
  `.tex`, `ARXIV_SUBMISSION.md`, `SUPERSEDED.md`, `ANCHORS.md`,
  `packets_materialized/MANIFEST.md`. Every one is either the Class-A
  *definition* (dossier lines 18, 26 — a heading over an explicitly empty
  class), an explicit **negation** (*"this is retrieval, not fabrication"*;
  *"a boundary row, not a fabrication"*; *"not a fabrication point"*), or the
  **correction record** itself. `hallucinat*` appears exactly once, in the
  dossier's correction record, in scare quotes, describing the reading that was
  found wrong. Nothing asserts fabrication as fact. The same greps over the
  rendered PDF return the same three negation/correction hits and nothing else.
- **"two strict" / "2 strict" / "both strict".** Zero hits in every file
  checked, in the PDF, and repo-wide outside `audit_2026-09-05/`.
- **478/476, 478/474, 477/477.** Zero hits in the corrected document set and in
  the PDF. The only surviving `478/476` anywhere in the tracked tree is F2
  (`v34_full_pair_attribution.json`).
- **480/476 and 477/475 used without a pair label.** Zero. All four
  occurrences of `480/476` read *"the headline Opus pair reads 480/476"* /
  *"raises the Opus pair to 480/476"*; all four of `477/475` read *"the official
  grok pair"* / *"grok pair"* / *"that grok pair"* / *"the prior pair"* (the
  last defined two sentences earlier as the grok configuration). Each is also
  shown as `479+1 / 475+1` or `476+1 / 474+1`, so the derivation is on the page.
- **Class A still holding `gpt4_731e37d7`.** No. Class A reads *"(none
  surviving review — gpt4_731e37d7 was moved to Class D on 2026-09-05 …)"*, the
  row appears in full under Class D with "(downgraded from A)" in its heading,
  and the Correction record at the foot of the dossier states the original claim
  and the contradiction rather than deleting them. Class D holds exactly 7 rows,
  matching the impact statement.
- **Numeric drift between `.md` and `.tex`.** A token-level comparison of every
  number in both bodies found **no contradicting value**. The only asymmetries
  are presence/absence: the `.tex` alone carries `93`, `436`, `407/470`,
  `17/17`, `28%`, `15%`, `90/86%`; the `.md` alone carries `100%`, `88.0%`,
  `70.0%`, `90.6%` and its own section numbers. The five substantive prose
  divergences are F1, F10, and — non-contradictory — the `.tex`-only sentence
  in §4.3 (reader-tier upgrade passed the control with zero flips), the
  `.tex`-only reader curve, and the `.md`-only §6 partition sentence.
- **Per-question-type table.** Every one of the 35 cells in §5.1.1 reproduces
  from the released verdicts, and every column sums to its stated total
  (476, 474, 461/465, 479/475).
- **Guard tests are real.** Not tautological: removing any one guard turns the
  suite red, and all three restore to green.

---

## Freeze assertion

Tree state recorded before the first read and again after the last.

- `git status --short`: **15 lines, byte-identical at start and end** —
  8 modified + 1 added tracked paths, plus untracked `.lineage-state/`,
  `arxiv_upload/`, `eval/dense_chain_v32_20260830/audit_2026-09-05/`.
- `git rev-parse HEAD`: `0fc232b0c4b1ca18d1b937d2b562ff3aa1e1a1a6` at start and
  end.
- SHA-256 of all 19 verified files re-computed at the end: **all 19 unchanged**.
  `README.md 9197c7bb…` · `GOLD_DEFECT_DOSSIER.md 687a272f…` ·
  `SOTA_WRITEUP.md 8c71ce38…` · `RELEASE_MANIFEST.md da55ca5b…` ·
  `RELEASE_MANIFEST.root 0e637780…` · `ANCHORS.md e346a6bc…` ·
  `ARXIV_SUBMISSION.md 357a92cb…` · `paper.md ffbfdf38…` ·
  `paper.tex 6e36e289…` · `paper.pdf 376ffc35…` · `SUPERSEDED.md 748077f7…` ·
  `judge_gpt4o/rescored.jsonl 49b4df39…` · `materialized_all.jsonl.gz
  304b7be4…` · `packets_materialized/MANIFEST.md 067ab638…` ·
  `arxiv_upload/…tex 6e36e289…` · `rescore_gpt4o_judge.py 8c33fd81…` ·
  `build_release_manifest.py badf662c…` ·
  `test_rescore_gpt4o_judge_guards.py b5a72fe6…` ·
  `test_rescore_gpt4o_judge.py cdcb2a78…`

**Nothing moved during the pass.** All findings above are frozen-referent
against `0fc232b0`.

The mutation check ran entirely inside
`/private/tmp/claude-501/…/scratchpad/mut`, a copy made with
`rsync -a --exclude .git`; the repo copy of `rescore_gpt4o_judge.py` was never
opened for write and its hash is unchanged. Two tests
(`test_release_manifest_check.py`) fail *in that scratch copy only* because
`build_release_manifest.py` enumerates via `git ls-files` and the copy is not a
git repo, so the untracked `audit_2026-09-05/` tree gets pulled into the walk.
That is also the mechanism by which this directory stays outside the manifest —
confirmed, and the reason writing this file perturbs nothing.

Only file written: this one.
