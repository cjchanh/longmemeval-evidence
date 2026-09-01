# LongMemEval-S evidence release — Archivist dense chain (479/475 per 500)

Evidence for *Auditable Long-Term Memory: A Deterministic Retrieval Chain at
95.4±0.4% on LongMemEval-S* (Chanhnourack, Centennial Defense Systems,
technical report v1.2, 2026-09-01). Paper source, Markdown, and PDF are in
`eval/dense_chain_v32_20260830/paper/`.

This tree is an exact export of the rows in
`eval/dense_chain_v32_20260830/RELEASE_MANIFEST.md`: 447 files, one SHA-256
each. Nothing here was edited after export.

## What is here

- `eval/dense_chain_v32_20260830/full-v34-opus_pass{1,2}/` — the headline
  Opus reader pair: reader checkpoints (`reader/checkpoint_*.jsonl`,
  `run_meta.json`), official GPT-4o judge verdicts (`judge_gpt4o_v2/` for
  pass 1, `judge_gpt4o/` for pass 2), control receipts, GLM-5.3 cross-judge
  verdicts, and the pre-release re-judge `judge_gpt4o_repro_20260901/`
  (478/500, three verdict flips on identical text — see paper §8).
- `full-v34_pass{1,2}/` (grok-4.6-high pair, 476/474), `full-v34-xhigh_pass{1,2}/`,
  `full-v34-{glm53,kimi,sol,dsv4pro,nemotron,gemini}_pass1/` — every run in
  the reader curve, same layout.
- `GOLD_DEFECT_DOSSIER.md`, `judge_agreement_matrix*.json`, `SOTA_WRITEUP.md`,
  `v4/PARENT_ANALYSIS.md`, `v4/ADVERSARIAL_PASS_20260901.md` — attribution,
  cross-judge study, adversarial pass.
- `scripts/rescore_gpt4o_judge.py` (+ `oc_flash_lane.py`) — the official-judge
  harness: frozen LongMemEval rubric templates, SHA-256 pinned
  (`9c9d67fab129…`), live positive/negative controls, fail-closed transport.
  `benchmarks/longmemeval-judge-gate/GROUND_TRUTH_SURVEY.md` is the rubric source.
- `scripts/{reader_lane,claude_cli_lane,grok_cli_lane,run_lme_qa_flash_packets}.py`
  — reader lanes and the reader runner over frozen packets.
- `tests/` — template-pin and verdict-extraction tests for the judge kit.

## What is held

Retrieval, cross-encoder rerank, packet-compiler, and scaffold-operator
sources, and the materialized packets (benchmark haystack text). See the
manifest's *Held* section and paper §8.

## Verify

Every file against the manifest:

```
python3 - <<'EOF'
import re, hashlib
rows = [m.groups() for m in (re.match(r"^\| `([^`]+)` \| (\d+) \| `([0-9a-f]{64})` \|$", l)
        for l in open("eval/dense_chain_v32_20260830/RELEASE_MANIFEST.md")) if m]
bad = [r for r, _, h in rows if hashlib.sha256(open(r, "rb").read()).hexdigest() != h]
print(len(rows), "rows;", len(bad), "mismatches")
EOF
```

Re-derive the headline from the released verdicts (no API key needed):

```
python3 - <<'EOF'
import json
E = "eval/dense_chain_v32_20260830"
for name, p in [("Opus pass1", f"{E}/full-v34-opus_pass1/judge_gpt4o_v2/rescored.jsonl"),
                ("Opus pass2", f"{E}/full-v34-opus_pass2/judge_gpt4o/rescored.jsonl"),
                ("Opus pass1 re-judge", f"{E}/full-v34-opus_pass1/judge_gpt4o_repro_20260901/rescored.jsonl"),
                ("grok pass1", f"{E}/full-v34_pass1/judge_gpt4o/rescored.jsonl"),
                ("grok pass2", f"{E}/full-v34_pass2/judge_gpt4o/rescored.jsonl")]:
    v = [json.loads(l)["llm_judge_correct"] for l in open(p)]
    print(f"{name}: {sum(v)}/{len(v)}")
EOF
```

Expected: 479, 475, 478, 476, 474.

Re-judge a checkpoint under the official judge (≈ $1.28, OpenAI API key in
`~/.config/openai/api_key`, mode 0600; the harness never accepts a key inline):

```
python3 scripts/rescore_gpt4o_judge.py \
  --answerable eval/dense_chain_v32_20260830/full-v34-opus_pass1/reader/checkpoint_answerable.jsonl \
  --abs        eval/dense_chain_v32_20260830/full-v34-opus_pass1/reader/checkpoint_abs.jsonl \
  --out-dir    /tmp/opus_pass1_rejudge --control-n 12
```

The judge is nondeterministic at the margin: the paper reports 479 and a
same-day re-judge returned 478 with 497/500 verdicts agreeing. Expect a
result in that band, with controls 12/12 and 12/12.

Tests: `python3 -m pytest -q tests/`.

## Dataset

LongMemEval-S, `xiaowu0162/longmemeval-cleaned` (Hugging Face, MIT). Reader
checkpoints carry question and gold text from the benchmark; the haystack
sessions are not redistributed here.

## License

MIT (see `LICENSE`) for the code and receipts in this release. The benchmark-derived question and gold text is MIT under the dataset's own license.
