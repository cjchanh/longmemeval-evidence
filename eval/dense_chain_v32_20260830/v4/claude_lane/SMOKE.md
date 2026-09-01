# Claude CLI reader lane — live smoke (3 calls)

Date: 2026-08-31. Lane: `scripts/claude_cli_lane.py` via `reader_lane.py`
(`LME_READER_LANE=claude-cli`). Model: `opus` (env `LME_CLAUDE_CLI_MODEL`
default), resolves to the operator's installed Claude CLI 2.1.252 on the
Claude subscription (Opus 4.6-class — the measured tier-jump lever this
lane exists to unlock).

All three calls ran through the actual `claude_cli_generate()` production
code path (not raw subprocess) — no lane fixes were needed after the initial
build; the transport worked on first try (unlike the grok CLI lane, which
needed `--max-turns`/`-p` iteration — see `scripts/grok_cli_lane.py` header
comment for that history).

## (a) Trivial sanity call

- Command shape: `claude -p "Reply with exactly: SMOKE_A_PONG" --model opus --output-format text --tools "" ` (scratch cwd)
- Elapsed: **15.4s**
- rc: 0
- stdout tail (full output, 12 chars): `SMOKE_A_PONG`
- stderr: empty (production shape: `--tools ""` + scratch cwd emits zero chrome)

## (b) Packet-scale real row (question_id `08f4fc43`)

- Prompt built exactly as `scripts/run_lme_qa_flash_packets.py`'s
  `build_prompt()` builds it: dataset item from
  `/Users/cj/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json`
  (question_id `08f4fc43`) + `session_blobs` from
  `eval/dense_chain_v32_20260830/full-v34_pass1/materialized_all.jsonl` +
  `facts_text` from `eval/dense_chain_v32_20260830/full-v34_pass1/facts_all.jsonl`
  (the same facts_all.jsonl `run_v34_full.sh` builds by concatenating
  `facts_v34.jsonl` + `facts_abs_v34.jsonl` — `facts_v34.jsonl` alone does
  not contain answerable-set rows, so the joined file was used to
  reproduce the runner's real join).
- Prompt size: **128,295 chars** (~40k-token scale, argv transport — well
  under the 800,000-char argv/stdin threshold, no fallback needed).
- Elapsed: **17.8s**
- rc: 0
- Question: "How many days had passed between the Sunday mass at St. Mary's
  Church and the Ash Wednesday service at the cathedral?"
- Gold answer: "30 days. 31 days (including the last day) is also
  acceptable."
- Model output (full): "Based on the retrieved sessions:\n\n- Session #1
  (16:20): recently attended the Sunday mass at St. Mary's Church on
  **January 2nd**\n- Session #2 (04:43): \"I just came from the Ash
  Wednesday service at the cathedral on **February 1st**\"\n\n**Interval**\n\n-
  January 2 → February 1\n- January has 31 days: 31 − 2 = 29 days to
  January 31, plus 1 day to February 1 = **30 days**\n\nAnswer: 30 days"
  (tail shown; full answer correct against gold, right computation and
  citation of both source sessions).
- Verdict: **correct**, no truncation, no turn-limit issue, no argv-length
  issue. No transport fix was required for this row.

## (c) Deliberate-failure probe (bogus model name)

- Command shape: `claude -p "ping" --model bogus-model-xyz --output-format text --tools ""`
- Elapsed: **14.3s** (CLI boot + model-validation round trip; this is an
  immediate raise, not a retry loop — `_LANE_DOWN` matched on the first
  attempt so no backoff/retry was spent)
- rc: 1
- stdout: `There's an issue with the selected model (bogus-model-xyz). It
  may not exist or you may not have access to it. Run --model to pick a
  different model.`
- stderr: `[claude-code:unrecognized_model] {"model":"bogus-model-xyz","query_source":"sdk"}`
- `claude_cli_lane.py`'s `_LANE_DOWN` regex matched the
  `unrecognized_model` tag on stderr → `claude_cli_generate()` raised
  `ClaudeCliLaneError` immediately (no retry, since a lane-down banner is
  treated as immediately fatal, mirroring `grok_cli_lane.py`'s design) —
  **the error text was never returned as an answer.** Verified fail-closed.

## Transport notes (probed before writing the lane)

- `claude -p <prompt> --model <model> --output-format text` is the correct
  print-mode invocation; positional `prompt` argv, not a `-p <value>` flag
  value pair issue — `-p` is a boolean switch, the prompt is a separate
  positional arg.
- All CLI chrome (untrusted-workspace notice, permission-rule warnings)
  goes to **stderr only**; stdout is always the clean answer when rc=0.
  Confirmed by comparing captured stdout/stderr separately.
- `--tools ""` disables all agentic tools (Bash/Read/Edit/etc.), turning
  the call into a pure text completion — required so the reader lane never
  executes commands or touches the filesystem. Combined with a per-process
  scratch `cwd` (never this repo), this also eliminates the untrusted-
  workspace warning entirely (confirmed: zero stderr bytes in call (a) and
  (b)).
- There is no CLI flag to read the prompt from a file; `@path` in the
  prompt text is interpreted by the agent as an instruction to read that
  file, not a CLI-level file-read directive (probed and rejected as a
  transport). Piping the prompt on stdin to `claude -p` with no positional
  prompt argument **does** work (probed with a literal shell pipe before
  writing the lane) — used as the verified >800,000-char fallback instead
  of a temp file.
- Bogus model → rc=1, structured `[claude-code:unrecognized_model]` tag on
  stderr (see call (c)).
- Bogus flag → rc=1, `error: unknown option '...'` on stderr (probed
  separately, not part of the 3-call smoke budget; covered in
  `tests/test_claude_cli_lane.py`).

## Readiness verdict for a 25-row probe at 2-3 workers

**Ready.** All three smoke calls landed clean on the first attempt through
the production code path; no transport fix was needed (unlike the grok CLI
lane's `--max-turns` history). At ~16-18s/call for both a trivial prompt
and a real 128k-char packet, 25 rows at 2-3 workers is on the order of
6-7 minutes wall clock (25 rows / 2.5 avg workers × ~17s ≈ 170s, plus
scheduling overhead) — well inside a single bounded run. Recommend:

- `LME_READER_LANE=claude-cli LME_CLAUDE_CLI_MODEL=opus` for the probe.
- `--workers 2` to start (bump to 3 only after confirming no rate-limit
  banner fires under concurrent load — this smoke test only exercised
  serial calls; concurrent-worker rate-limit behavior against the CLI's
  own session/auth state is unverified and worth a first small batch
  before scaling to 3).
- Watch for `ClaudeCliLaneError` in the checkpoint error field — any
  `rate.?limit`/`quota` banner match under concurrency would surface there
  first.
