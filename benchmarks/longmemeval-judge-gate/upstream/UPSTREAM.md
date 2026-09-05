# Upstream LongMemEval judge

Vendored byte-for-byte from the official LongMemEval evaluator. This file
is the pin a stranger uses to check the copy in this tree.

- repository: `xiaowu0162/LongMemEval`
- path: `src/evaluation/evaluate_qa.py`
- fetch_date: 2026-09-05
- sha256: `ecce9c4c79dc89d99534ac17b383a5cbb5b9f0c69ee98adaf0684742e3d95251`
- licence: MIT (same as the LongMemEval dataset)

## Known deviation between the harness templates and upstream

`tests/test_upstream_judge_pin.py` compares every rubric template in
`scripts/rescore_gpt4o_judge.py` with the vendored upstream source after mapping
the harness's named placeholders (`{question}`, `{answer}`, `{response}`) onto
upstream's positional `{}`. Four templates and both additions are identical.
`BASE_TEMPLATE` differs by exactly one byte: upstream's first line ends with a
trailing space before the newline; the harness's does not. The harness is NOT
edited to match, because every released verdict was produced with the harness
text and its SHA-256 pin (`9c9d67fab129…`) covers that text. The test records the
exact diff and fails if any other byte moves. "Verbatim" in the harness docstring
and paper therefore means: identical rubric text modulo that one trailing space
and the placeholder style.
