"""Pin the vendored upstream judge and check harness templates against it."""
from __future__ import annotations

import ast
import difflib
import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import rescore_gpt4o_judge as m  # noqa: E402

UPSTREAM_PY = REPO / "benchmarks/longmemeval-judge-gate/upstream/evaluate_qa.py"
UPSTREAM_MD = REPO / "benchmarks/longmemeval-judge-gate/upstream/UPSTREAM.md"
SHA_RE = re.compile(r"sha256:\s*`?([0-9a-f]{64})`?")
TEMPLATE_LIT_RE = re.compile(r"template = (\".*?\")")
HARNESS_CONSTANTS = (
    "BASE_TEMPLATE",
    "TEMPORAL_ADDITION",
    "KU_ADDITION",
    "SSP_TEMPLATE",
    "ABS_TEMPLATE",
)


def _positional(text: str) -> str:
    return (
        text.replace("{question}", "{}")
        .replace("{answer}", "{}")
        .replace("{response}", "{}")
    )


def _decoded_templates(src: str) -> list[str]:
    return [ast.literal_eval(lit) for lit in TEMPLATE_LIT_RE.findall(src)]


def _compose(base: str, addition: str) -> str:
    return base.replace(
        "answer, answer no.\n\n",
        "answer, answer no." + addition + "\n\n",
    )


def test_vendored_evaluate_qa_sha256_matches_upstream_md():
    digest = hashlib.sha256(UPSTREAM_PY.read_bytes()).hexdigest()
    pinned = SHA_RE.search(UPSTREAM_MD.read_text())
    assert pinned is not None
    assert digest == pinned.group(1)
    assert digest == "ecce9c4c79dc89d99534ac17b383a5cbb5b9f0c69ee98adaf0684742e3d95251"


def _unified_diff(name: str, got: str, want: str) -> str:
    return "".join(
        difflib.unified_diff(
            want.splitlines(keepends=True),
            got.splitlines(keepends=True),
            fromfile=f"upstream evaluate_qa.py {name}",
            tofile=f"harness {name}",
        )
    )


def _assert_template_equal(name: str, got: str, want: str) -> None:
    if got == want:
        return
    raise AssertionError(
        f"{name} differs from upstream; do not edit the harness\n"
        f"{_unified_diff(name, got, want)}"
    )


def test_harness_rubric_templates_appear_verbatim_in_upstream():
    src = UPSTREAM_PY.read_text()
    decoded = _decoded_templates(src)
    assert len(decoded) == 5
    assert m.TEMPORAL_ADDITION in src
    assert m.KU_ADDITION in src
    _assert_template_equal("SSP_TEMPLATE", _positional(m.SSP_TEMPLATE), decoded[3])
    _assert_template_equal("ABS_TEMPLATE", _positional(m.ABS_TEMPLATE), decoded[4])
    for name in HARNESS_CONSTANTS:
        assert getattr(m, name)


def test_base_template_byte_diff_reported_without_editing_harness():
    """r2: BASE_TEMPLATE is not byte-identical (upstream first line has a
    trailing space). Report that exact diff; do not edit the harness."""
    src = UPSTREAM_PY.read_text()
    want = _decoded_templates(src)[0]
    got = _positional(m.BASE_TEMPLATE)
    diff = _unified_diff("BASE_TEMPLATE", got, want)
    assert got != want
    assert diff
    got_lines = got.splitlines()
    want_lines = want.splitlines()
    assert got_lines[1:] == want_lines[1:]
    assert got_lines[0] != want_lines[0]
    assert got_lines[0] == want_lines[0].rstrip()
    assert m.PROMPT_TEMPLATES_SHA256.startswith("9c9d67fa")


def test_temporal_composed_prompt_trailing_space_diff_reported_without_editing_harness():
    """r3: composed TEMPORAL (BASE+TEMPORAL_ADDITION) differs from upstream
    decoded[1] by a trailing space before the blank line. Quote that diff;
    do not edit the harness."""
    src = UPSTREAM_PY.read_text()
    want = _decoded_templates(src)[1]
    got = _positional(_compose(m.BASE_TEMPLATE, m.TEMPORAL_ADDITION))
    diff = _unified_diff("TEMPORAL_COMPOSED", got, want)
    assert got != want
    assert diff
    assert len(got) == 769
    assert len(want) == 770
    got_lines = got.splitlines()
    want_lines = want.splitlines()
    assert got_lines[1:] == want_lines[1:]
    assert got_lines[0] != want_lines[0]
    assert got_lines[0] == want_lines[0].rstrip()
    assert m.PROMPT_TEMPLATES_SHA256.startswith("9c9d67fa")


def test_ku_composed_prompt_diff_reported_without_editing_harness():
    """r3: harness sends BASE+KU_ADDITION (687 chars, keeps equivalent/subset
    sentences) while upstream decoded[2] is a 448-char replacement. Quote
    that diff; do not edit the harness."""
    src = UPSTREAM_PY.read_text()
    want = _decoded_templates(src)[2]
    got = _positional(_compose(m.BASE_TEMPLATE, m.KU_ADDITION))
    diff = _unified_diff("KU_COMPOSED", got, want)
    assert got != want
    assert diff
    assert len(got) == 687
    assert len(want) == 448
    equivalent = "If the response is equivalent to the correct answer"
    subset = "only contains a subset of the information required by the answer"
    assert equivalent in got
    assert subset in got
    assert equivalent not in want
    assert subset not in want
    assert m.KU_ADDITION.strip() in want
    assert m.PROMPT_TEMPLATES_SHA256.startswith("9c9d67fa")
