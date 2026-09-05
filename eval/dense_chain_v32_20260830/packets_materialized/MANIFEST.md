# Materialized packets (headline pair)

Reader-format packet text consumed by both headline Opus passes, plus the
v3.4 evidence scaffolds. Pass 1 and pass 2 used byte-identical files.

These rows are a pure rendering of the public LongMemEval-S dataset
(`xiaowu0162/longmemeval-cleaned`, MIT; sha256
`d6f21ea9d60a0d56f34a05b609c79c88a451d2ae03597821ea3d5a9678c3a442`, pinned
in `eval/dense_chain_v32_20260830/materialize_summary.json`). Shipping the
text is licence-clean. The dataset JSON itself is not in this repository.

The 500 materialized rows are the concatenation of the 470 answerable rows
hashed in `eval/dense_chain_v32_20260830/materialize_summary.json`
(`876ef9d2f95d57ae5d014476315b69fa7dc323f631ba9fae0558fd5c3c3f9a6c`) and the
30 abstention rows hashed in
`eval/dense_chain_v32_20260830/materialize_abs_summary.json`
(`cbb42353030f52bfe252a3e4051cc790251ec67f807e02b46d0dd25ced6ca11b`).

## Files

Uncompressed sha256 is `sha256` of the gunzipped bytes (`gunzip -c FILE | shasum -a 256`).

| file | rows | uncompressed sha256 |
|---|---:|---|
| `materialized_all.jsonl.gz` | 500 | `a8bfd9d239f51330c6872609c346ab60a0659194a2d04998a179440753eb13c1` |
| `facts_all.jsonl.gz` | 257 | `076108c465937537b126a85bdc0ab0a43e42cb15bcd034cf267311d44f6a5739` |

## Verify the rendering

From the repository root, set `$LONGMEMEVAL_S_JSON` to the public dataset JSON:

```
python3 scripts/materialize_packets.py --data "$LONGMEMEVAL_S_JSON" --verify eval/dense_chain_v32_20260830/packets_materialized/materialized_all.jsonl.gz
```

Expected: `rows=500 identical=500 mismatched=0` (exit 0). This does not
re-run retrieval, rerank, or the compiler.

## Re-run the reader and re-score

```
gunzip -c eval/dense_chain_v32_20260830/packets_materialized/materialized_all.jsonl.gz > /tmp/materialized_all.jsonl
gunzip -c eval/dense_chain_v32_20260830/packets_materialized/facts_all.jsonl.gz > /tmp/facts_all.jsonl
python3 scripts/run_lme_qa_flash_packets.py --data "$LONGMEMEVAL_S_JSON" --materialized /tmp/materialized_all.jsonl --facts /tmp/facts_all.jsonl --out-dir /tmp/lme_reader_rerun
python3 scripts/rescore_gpt4o_judge.py --answerable /tmp/lme_reader_rerun/checkpoint_answerable.jsonl --abs /tmp/lme_reader_rerun/checkpoint_abs.jsonl --out-dir /tmp/lme_reader_rerun_judge
```
