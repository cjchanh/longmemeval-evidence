# LongMemEval-S evidence release — Archivist dense chain (479/475 per 500)

Judge-side evidence for a LongMemEval-S measurement: 479/475 of 500 under
the official GPT-4o judge. Clone this repo; `python3 -m pytest -q tests/`
is the install check. Re-derive the headline from released verdicts with
the snippet under Verify. This tree does not release the retrieval, rerank,
packet-compiler, or scaffold-operator sources.

The headline score is not independently reproducible. Packets and the
judge harness are; the method is not. Every component that moves the
score was tuned against the same 500 LongMemEval-S questions; no
held-out split is reported.

Comparator numbers (Chronos High 478, Mastra 468 raw, OMEGA 466 raw) are
author-reported. Chronos PDF sha256 `a6a75d611a381ba8e244c77601c21ad4567e39e2e97426c85999a0cea21ae738`
and Mastra page sha256 `cd0bf092daa9a2956bf8983c8425ea812290ef6c005b00eb6fa60ba7e0f2a073`
are pinned under `eval/dense_chain_v32_20260830/comparators/`; OMEGA has no
source in this release.

Paper: *Auditable Long-Term Memory: A Deterministic Retrieval Chain
Measured at 479/475 of 500 on LongMemEval-S Under the Official Judge*
(Chanhnourack, Centennial Defense Systems, technical report v1.3,
2026-09-08). Source, Markdown, and PDF are in
`eval/dense_chain_v32_20260830/paper/`.

This tree matches the rows in
`eval/dense_chain_v32_20260830/RELEASE_MANIFEST.md` (see that file's header
for the file count; one SHA-256 per row).

## What is here

- `eval/dense_chain_v32_20260830/full-v34-opus_pass{1,2}/` — the headline
  Opus reader pair: reader checkpoints (`reader/checkpoint_*.jsonl`,
  `run_meta.json`), official GPT-4o judge verdicts (`judge_gpt4o_v2/` for
  pass 1, `judge_gpt4o/` for pass 2), control records, GLM-5.3 cross-judge
  verdicts, and the pre-release re-judge `judge_gpt4o_repro_20260901/`
  (478/500, three verdict flips on identical text — see paper §8).
  ⚠ `full-v34-opus_pass1/judge_gpt4o/` is a **partial artifact, not a judge
  result**: 194 of its 500 rows were never judged (`attempts: 0`) and are
  written `false`, so it totals 289/500. It is retained for the record and
  labelled by `SUPERSEDED.md` beside it. Pass-1 verdicts come from
  `judge_gpt4o_v2/`.
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
sources. See the manifest's *Held* section.

## Packets

The headline pair's compiled packet text is released under
`eval/dense_chain_v32_20260830/packets_materialized/`. See
`eval/dense_chain_v32_20260830/packets_materialized/MANIFEST.md`.

## Verify

Manifest root (sha256 of `RELEASE_MANIFEST.md`):
`9f95007916ba647015bb0ac76876f79ff0ab0ea71941caf1e0b510f19b6e9c2b`
(`eval/dense_chain_v32_20260830/RELEASE_MANIFEST.root`). Anchors:
`eval/dense_chain_v32_20260830/ANCHORS.md`.

Upstream judge pin: `benchmarks/longmemeval-judge-gate/upstream/evaluate_qa.py`
sha256 `ecce9c4c79dc89d99534ac17b383a5cbb5b9f0c69ee98adaf0684742e3d95251`
(`xiaowu0162/LongMemEval` `src/evaluation/evaluate_qa.py`, 2026-09-05, MIT;
see `benchmarks/longmemeval-judge-gate/upstream/UPSTREAM.md`). Harness rubric
templates are pinned at `9c9d67fab129…`.

Third-party:

```
python3 scripts/build_release_manifest.py --check
python3 -m pytest -q tests
bash scripts/verify_release_manifest_signature.sh
shasum -a 256 benchmarks/longmemeval-judge-gate/upstream/evaluate_qa.py
```

`--check` exits 1 and names mismatching rows if any released file drifted.
The signature wrapper prints `UNSIGNED` and exits 2 until a maintainer
offline key writes `RELEASE_MANIFEST.root.sig`.
Logged commands in frozen evidence artifacts record the author's local
dataset path; they are hashed receipts of what ran, not an install
requirement.

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
checkpoints carry question and gold text from the benchmark. Rendered
packet text (`session_blobs` under `packets_materialized/`) is released;
the raw dataset JSON is not. Runner scripts read `$LONGMEMEVAL_S_JSON`
(default `$HOME/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json`).

## License

MIT (see `LICENSE`) for the code and evidence in this release. The benchmark-derived question and gold text is MIT under the dataset's own license.
