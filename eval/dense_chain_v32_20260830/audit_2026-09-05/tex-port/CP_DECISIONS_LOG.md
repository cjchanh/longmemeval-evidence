# CP decisions log — `.tex` / `.md` author rulings applied (2026-09-06)

Resolves CP-1 .. CP-10 from `TEX_PORT_PLAN.md` §4, which `PORT_LOG.md` §4
deliberately left for the author. Every entry below records the ruling as
given, the exact before/after text, and the file + line it landed on.

**Write scope honoured:** `paper/…​.tex`, `paper/…​.md`, `paper/…​.pdf`
(rebuilt), `arxiv_upload/…​.tex` (re-synced byte-identical), and this file.
Nothing else was touched — no dossier, no `SOTA_WRITEUP.md`, no `README.md`,
no manifest, no scripts, no tests.

**Headline integrity:** `479/475` is unchanged — 6 occurrences in the `.tex`
and 6 in the `.md`, identical before and after. A token-level multiset diff of
every number in both files before vs after shows exactly four intended deltas
and nothing else: `.tex` loses `17/17` (CP-5) and gains two `4.6` tokens
(CP-1); `.md` loses one `2` (the `(2 rows)` heading count, CP-10) and gains the
`§3.5` / `6d550036` / `75f70248` tokens of the restored Chronos sentence
(CP-6). No number was invented, changed, or re-derived.

Pre-edit hashes — `.tex` / `arxiv_upload` `.tex`
`de5982f560e1415ebed14e6d668f01e1370d55d5d070122906977e0ad61b0661`,
`.md` `a42a5f2616580c67f374716c14e25fc2f7bcbb1ce08b8fb2496fea203e2d21f6`.

---

## CP-1 — never "prior"; always name the reader pair

**Ruling.** Never "prior"; always name the reader pair explicitly. Use
"grok pair" (or "grok-4.6-high pair" on first use in a section) and
"Opus headline pair". Rationale on the record: an unlabelled pair reference is
exactly how grok's 116/133 ended up inside an Opus sentence.

The plan named four `.tex` sites. All four were found and fixed; a **fifth**
site — the abstract — failed the "does this hit name its reader?" check the
ruling asks for at the end, and was fixed on the same rule (flagged as a
deviation below).

### CP-1a — §4.2, `.tex` line 174

- **Before:** `We re-judged both passes` / `of our prior configuration with a second judge on identical rows: agreement 98.2\%/97.8\%…`
- **After:** `We re-judged both passes` / `of the grok-4.6-high pair with a second judge on identical rows: agreement 98.2\%/97.8\%…`
- §4 is a fresh section, so this is the long form.
- **Referent confirmed, not assumed:** `FINAL_VERIFICATION.md` line 304 —
  *"GLM-vs-GPT-4o 98.2%/97.8% **on the grok pair** with gpt_only 7/7 and
  glm_only 2/4"*. The `.md`'s parallel sentence ("both official passes") and
  the §5.2 ablation row ("official pair, grok high") agree.

### CP-1b — §5.1 paragraph label, `.tex` line 260

- **Before:** `Prior-configuration detail: answerable 450/470 and 447/470;`
- **After:** `Raw grok-pair detail: answerable 450/470 and 447/470;`
- Adopts the phrasing the corrected `.md` already carries at its line 262
  (`Raw grok-pair detail (the pair the self-consistency rule was frozen over):`).

### CP-1c — §5.1 adjudication figure, `.tex` line 262

- **Before:** `adjudication scenario (\S6.3) the prior pair reads 477/475 (476+1 / 474+1, the single strict defect)`
- **After:** `adjudication scenario (\S6.3) the grok pair reads 477/475 (476+1 / 474+1, the single strict defect)`
- The number was already correct (the parent's CP-1 numeric half); only the
  label moved. `.md` line 271 reads `that grok pair reads 477/475` — the two
  documents now name the same pair.

### CP-1d — §6 intro, `.tex` line 361

- **Before:** `Of 470 answerable questions, 24 fail in at least one prior-configuration pass.`
- **After:** `Of 470 answerable questions, 24 fail in at least one pass of the grok-4.6-high pair.`
- §6 is a fresh section, so the long form again.
- **Note, not a change:** `FINAL_VERIFICATION.md` F5 (lines 131–145) already
  records that no configuration yields exactly 24 — grok-pair union is 25,
  Opus-pair union 22, all-four-pass union 35. Naming the pair makes that open
  finding more visible; the `24` itself was **not** touched, because changing a
  headline-adjacent count is not one of the rulings and would be inventing a
  number. F5 stays open.

### CP-1e — Abstract, `.tex` line 32 / `.md` line 21 *(fifth site — deviation, see below)*

- **Before (`.tex`):** `measurement is the result: the pair's entire` / `spread traced to eight verdict-flip rows;`
- **After (`.tex`):** `measurement is the result: the Opus headline pair's entire` / `spread traced to eight verdict-flip rows;`
- **Before (`.md`):** `measurement is the result: the pair's` / `entire spread traces to eight verdict-flip rows;`
- **After (`.md`):** `measurement is the result: the Opus headline pair's` / `entire spread traces to eight verdict-flip rows;`
- **Why this hit fails the check.** The nearest antecedent is the *grok*
  configuration ("A second, grok-4.6 reader configuration measured 476/474",
  `.tex` line 27), while the intended referent is the headline pair — the exact
  failure mode the ruling's rationale names. Both pairs happen to have eight
  flip rows, so the sentence was not false, only unattributable.
- **Referent confirmed:** `FINAL_VERIFICATION.md` line 300 — *"Opus 8 flips =
  6 lost (2 abstentions) + 2 gained"* (PASS), i.e. 479 → 475 is exactly that
  spread. §5.1 states the same.
- The `.md` got the identical one-phrase change so the two documents keep
  saying the same thing in the abstract.

### CP-1 — post-edit verification sweep (as the ruling requires)

`grep -n 'prior pair\|prior configuration\|prior-configuration'` over the
`.tex` → **no hits**. Three `prior` tokens survive, none a pair reference:

| line | text | why it stays |
|---|---|---|
| 133 | `tie-break by prior turn` | rerank determinism, not a reader pair |
| 243 | `one row no prior reader had ever solved` | earlier *readers*, not a pair |
| 333 | `versus its prior-contract 468` | Sol's v3.3 contract score |

Every one of the 24 `pair` hits in the `.tex` was then checked individually for
whether it names its reader. All pass:

- **Named outright** — L32 `Opus headline pair`, L161 `The headline pair uses
  the Claude Opus reader`, L174 `grok-4.6-high pair`, L224/225 `The Opus pair…
  the grok pair's 471`, L240 `the Opus pair`, L260/262 `Raw grok-pair… the grok
  pair`, L361 `the grok-4.6-high pair`, L427 `(grok pair: …)`, L428 `The xhigh
  pair`, L478 `the headline pair`.
- **Pinned by an adjacent number or subject in the same sentence** — L55 and
  L504 (`measures 479/475 … the pair a statistical tie`), L187 (`its full pair`
  ← "the reader-tier upgrade"), L221 (`the ex-dossier pair`), L235/L242 (inside
  the Opus paragraph), L246/L248 (inside the xhigh paragraph), L326 (`under
  strict abstention the pair reads 476/472` — the sentence subject is *"Three
  of **Opus's** abstention credits"*).
- **Table-defined label** — L190 and L286 use `raw pair`, defined by the §5.1
  table row `v3.4, grok-4.6 high (raw pair)` (L210) and the §5.1.1 `Raw p1 /
  Raw p2` columns totalling 476/474; L308/309 use `official pair` /
  `official pair, grok high`. `raw pair` is left standing deliberately: it is
  the vocabulary the operator-corrected `.md` itself uses (`Raw grok-pair
  detail`, `the raw pair's 8 flip rows`), and none of these hits attaches a
  score to an unnamed reader.

---

## CP-2 — §4.3 closing sentence: keep both facts, in that order

**Ruling.** The `.md` fact (the frozen rule blocked the rejected verifier) and
the `.tex` fact (the reader-tier upgrade passed the same control) are
complementary, not alternatives — the pairing shows the gate is *discriminating*
rather than merely restrictive. One sentence carrying both, blocked-verifier
first; `.md` and `.tex` must agree.

**`.tex` line 184** (§4.3)

- **Before:**
  ```
  flipped 11 of 59 correct drafts to wrong (\S6.2). The reader-tier upgrade in
  this report passed the same control with zero flips before its full pair was
  launched.
  ```
- **After:**
  ```
  flipped 11 of 59 correct drafts to wrong (\S6.2). The frozen acceptance rule
  --- zero control flips --- blocked it from ever touching the headline, while
  the reader-tier upgrade in this report passed that same control with zero
  flips before its full pair was launched.
  ```

**`.md` line 184** (§4.3) — same sentence, same order:

- **Before:** `The frozen acceptance rule — zero control flips — blocked it from ever touching the headline.`
- **After:** `The frozen acceptance rule — zero control flips — blocked it from ever touching the headline, while the reader-tier upgrade in this report passed that same control with zero flips before its full pair was launched.`

Both source phrasings are carried verbatim; the only added words are the
`, while` hinge and `that` in "that same control". `its full pair` keeps its
antecedent ("the reader-tier upgrade in this report"), so it is not a bare
pair reference under CP-1.

---

## CP-3 — already resolved upstream; re-verified

**Ruling (parent):** `.md` §4.4 now carries the `.tex`'s "built, then
withdrawn" text. **Verified, no edit made.** `.md` lines 192–199 carry
*"**The resulting number was WITHDRAWN from any claim.** Internal review showed
the construction wrote one derived verdict into *both* passes — an identity,
not two agreeing measurements — and that its flip-row selection was
judge-conditioned…"*, matching `.tex` lines 188–195.

*Residual noticed, not acted on (outside the rulings):* the `.md` §4.4 **heading**
still reads `Self-consistency on measured flip rows (frozen rule)` while the
`.tex` reads `Self-consistency tie-break (built, then withdrawn)` — the `.md`
heading now under-states its own body. The `.md` §4.4 body also repeats itself
across lines 188–190 ("the entire spread came from them" / "The raw pair's
spread came from eight verdict-flip rows"). Reported, not fixed.

---

## CP-4 — §5.3 tex-only analytical content: KEEP

**Ruling.** Keep; do not overwrite; do not port into the `.md`. Record as a
deliberate asymmetry.

**No edit made.** `.tex` §5.3 (lines 331–357) retains, with no `.md`
counterpart: the serving-artifact control (`28\%` vs `15\%` across packet-size
buckets vs `90/86\%` for V4 Pro), the DeepSeek `407/470` answerable breakdown,
and the full reader-capability curve
(`93 → 436 → 455 → 465 → 471 → 476`).

**Recorded as a deliberate asymmetry:** the `.tex` is the richer document in
§5.3 by author decision. Any future full-paragraph sync from `.md` into `.tex`
must skip §5.3, or it will silently delete measured analysis. `FINAL_VERIFICATION.md`
lines 386–393 already classifies these as presence/absence asymmetries with
**no contradicting value** between the documents.

---

## CP-5 — the tex-only "(17/17)" entity-linking figure: **CUT** (not sourceable)

**Ruling.** Source it or cut it. Keep it only if a released artifact supports
17/17, adding the artifact path in the sentence; otherwise delete the figure and
keep the surrounding claim without a number. Do not guess.

**Outcome: CUT.** No released artifact supports it.

**`.tex` line 407** (§6.4)

- **Before:** `An entity-linking retrieval arm (alias mining + query expansion) was built,` / `tested (17/17), and retired when measurement showed zero of its added` / `sessions were gold …`
- **After:** `An entity-linking retrieval arm (alias mining + query expansion) was built,` / `tested, and retired when measurement showed zero of its added` / `sessions were gold …`

The claim survives without a number, and the `.tex` now matches the `.md`'s
own wording (`was built, tested, and retired`) — so this cut also removes a
`.tex`/`.md` divergence rather than creating one.

**Evidence actually searched (all of it, and what it says):**

1. `eval/dense_chain_v32_20260830/entity_link_expansion_summary.json`
   (released, `RELEASE_MANIFEST.md` line 54) — the arm's own summary:
   `n_questions 470`, `n_with_expansion_terms 55`, `n_with_added_sessions 22`,
   `total_added_sessions 40`, `n_with_mined_aliases 465`. **No 17 of any
   kind.**
2. `eval/dense_chain_v32_20260830/entity_link_expansion.jsonl`
   (released, `RELEASE_MANIFEST.md` line 53) — all 470 records re-counted
   directly: `mined_aliases` 465, `activated_surface_forms` 60,
   `expansion_terms` 55, `added_sessions` 22, `added_session_scores` 22,
   40 added sessions total. **No count of 17 appears on any field.**
3. Repo-wide `grep` for `17/17` — three hits only: this paper's own §6.4
   (the claim under audit), `SOTA_WRITEUP.md` line 162 (the same unsourced
   claim, out of write scope — see the child-work note), and
   `judge_agreement_matrix_opus_glm53.json` line 7,
   `"controls": "pass1 pos 17/17 neg 20/20; pass2 pos 17/17 neg 20/20"` —
   which is **judge-control counts for the Opus↔GLM agreement matrix, an
   unrelated measurement**. Adopting it would have been exactly the number
   migration CP-1 exists to prevent.
4. `scripts/` and `tests/` — no entity-linking module and no entity-linking
   test suite ship in the release, so there is no 17-case test to point at.
5. `PARENT_ANALYSIS.md` / a `v4` directory — searched for; **no such files
   exist** anywhere in this repo.

Conclusion: `(17/17)` cannot be derived from released bytes, so per the ruling
it is gone rather than guessed at.

---

## CP-6 — Chronos gold-defect corroboration stays inline in §6.3

**Ruling.** Leave it inline in the `.tex` §6.3 — it is independent
corroboration of one of our dossier rows and reads stronger next to the claim.
Make the `.md` match: restore it inline in `.md` §6.3, keeping the References
entry.

**`.tex`:** no change. Lines 396–399 already carry it inline:
*"The Chronos authors independently document a defect on question
`6d550036` (their §3.5, alongside a judge-variability example on `75f70248`),
consistent with our dossier."*

**`.md` line 414** (§6.3, appended to the closing "Six further rows" bullet, the
same position it occupies in the `.tex`)

- **Before:** `  intended referent was answerable by premise repair.`
- **After:** `  intended referent was answerable by premise repair. The Chronos authors` / `  independently document a defect on question ` `` `6d550036` `` ` (their §3.5,` / `  alongside a judge-variability example on ` `` `75f70248` `` `), consistent with our` / `  dossier.`

**`.md` References entry kept** — lines 534–539 still carry the same fact as a
parenthetical on the Chronos citation, per the ruling ("keeping the References
entry"). The fact is now in both places in the `.md` and inline in the `.tex`;
it is not lost in either document.

---

## CP-7 — already resolved upstream; re-verified

**Ruling (parent):** the `.md` gained the 5 missing references and the `.tex`
gained the BAAI reranker entry; both lists now cover the same works.

**Verified, no edit made.** Author-token sets extracted from both References
sections are **identical**: `BAAI, Barnes, Chen, Cho, Cormack, Dodge,
Maharana, Nogueira, Packer, Sen, Wang, Wu, Zheng` — 7 bullets each,
`.tex` lines 510–528, `.md` lines 531–554.

---

## CP-8 — §6.2 closing: published negative result first, future work second

**Ruling.** Take the `.tex`'s sentence, then append the `.md`'s
forward-looking clause as a second short sentence.

**`.tex` lines 377–378** (§6.2)

- **Before:** `Both failures are published; they map the limit of prompting-side repair.`
- **After:** `Both failures are published; they map the limit of prompting-side repair.` / `They motivate an evidence-testimony layer as future work.`

**`.md` lines 390–392** (§6.2) — brought to the same two sentences:

- **Before:** `Both failures map the limit of prompting-side repair and motivate an evidence-testimony layer as future work.`
- **After:** `Both failures are published; they map the limit of prompting-side repair. They motivate an evidence-testimony layer as future work.`

---

## CP-9 — already resolved upstream; re-verified

**Ruling (parent):** no table or figure changes.

**Verified, no edit made.** The `.tex` still holds exactly three `tabular`
environments and no figure: §5.1 `{lcc}` (line 205), §5.1.1 `{lccccc}`
(line 268), §5.2 `{lc}` (line 301). No `\includegraphics`, no
`\begin{figure}`, and no markdown image in the `.md`. Nothing in this port
touched a table cell.

---

## CP-10 — §6.4 heading: take the tex heading in both files

**Ruling.** Take the `.tex` heading in both files — drop the wrong count
rather than fixing it. (The `.md`'s own `(2 rows)` disagreed with its 4-row
body: 1 pool-miss + 3 ordering.)

**`.tex`:** no change; line 403 already reads
`\textbf{6.4 Retrieval ceiling and coverage, measured precisely.}`

**`.md` line 419**

- **Before:** `### 6.4 Retrieval ceiling (2 rows) and flip noise`
- **After:** `### 6.4 Retrieval ceiling and coverage, measured precisely`

The wrong count is dropped rather than re-derived, exactly as ruled — the
`.md` §6.4 body (1 pool-miss + 3 ordering) is untouched.

---

## Build

Run twice from `eval/dense_chain_v32_20260830/paper/`:

```
pdflatex -interaction=nonstopmode longmemeval_auditable_memory_paper.tex   # exit 0
pdflatex -interaction=nonstopmode longmemeval_auditable_memory_paper.tex   # exit 0
```

- Both passes **exit 0**. `Output written on
  longmemeval_auditable_memory_paper.pdf (9 pages, 233121 bytes)`.
- **Zero** `!` errors, **zero** `Overfull \hbox`, **zero** `Underfull \hbox`
  in the log. Page count unchanged from the pre-decision build (9).
- `.aux`, `.log`, `.out` removed after the build; the log was kept out of tree
  in the session scratchpad.
- Rendered checks against the PDF text layer (all present): `the Opus headline
  pair's entire spread traced to eight verdict-flip rows`; `of the
  grok-4.6-high pair with a second judge`; `Raw grok-pair detail`; `the grok
  pair reads 477/475`; `24 fail in at least one pass of the grok-4.6-high
  pair`; `blocked it from ever touching the headline`; `They motivate an
  evidence-testimony layer`; `tested, and retired`; `consistent with our
  dossier`. Absent as intended: any `17/17`, any `prior-config…`.

## Byte-identity — `arxiv_upload` vs the paper `.tex`

```
$ cmp arxiv_upload/longmemeval_auditable_memory_paper.tex \
      eval/dense_chain_v32_20260830/paper/longmemeval_auditable_memory_paper.tex
(no output, exit 0)

$ shasum -a 256 <both>
fec0232bc6bd7171a55556dd0a304dc6d37414ef0635046d9b0d873c5cbb3ea3  arxiv_upload/…
fec0232bc6bd7171a55556dd0a304dc6d37414ef0635046d9b0d873c5cbb3ea3  eval/…/paper/…
```

Post-edit `.md` `53cbfdcacae516e465d754257d48c889fe634045b652fda8a29097555c7076cd`;
`.pdf` `0e6c1e82cd4887e8429f5b80f93bf4712d4b419c1d230ae300cbfb853368408d`.

## Deviations from the rulings as written

1. **CP-1 gained a fifth site (the abstract, CP-1e).** The ruling named four
   and then required verifying that *no* unlabelled pair reference survives
   anywhere in the `.tex`. The abstract's `the pair's entire spread` failed
   that check — its nearest antecedent is the grok configuration while its
   referent is the Opus pair — so it was fixed on the ruling's own rule, and
   the `.md` was kept in step. Flagged rather than done silently because it is
   outside the four sites the ruling enumerated.
2. **CP-6's `.md` restoration is placed inside the last §6.3 bullet**, not as a
   standalone paragraph. The `.md` §6.3 body is a bullet list, so this is the
   position that matches the `.tex`'s inline placement; a loose paragraph after
   the list would have read as a different section.
3. **Nothing else deviated.** CP-4, CP-9 and the `.tex` halves of CP-6 and
   CP-10 required no edit, as ruled.

## Adjacent findings — recorded, not acted on (outside write scope)

- `SOTA_WRITEUP.md` line 162 still carries `tested (17/17)` for the same
  entity-linking arm. CP-5 cut it from the `.tex` as unsourceable; the same
  figure is still published there.
- `FINAL_VERIFICATION.md` F5 (`24` reconciles to no configuration; grok-pair
  union is 25) is now attached to an explicitly named pair in the `.tex` §6
  intro, which makes the discrepancy sharper. Still open.
- `.md` §4.4's heading (`frozen rule`) under-states its own withdrawn-SC body,
  and lines 188–190 repeat the same fact twice.
- `.md` §6.4's closing sentence still points at `§4.4` for flip noise, a
  section that is now about a withdrawn construction.
- `FINAL_VERIFICATION.md` §7 item 1: the `.md` §5.1.1 still says "where both
  strict gold defects live" against its own 1-strict count. The `.tex` has no
  equivalent sentence and is clean.
