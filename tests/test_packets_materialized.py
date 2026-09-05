"""Tests for the released materialized packets and scripts/materialize_packets.py.

(a) gzip pins in packets_materialized/MANIFEST.md — fails if a digest or
    row count in MANIFEST.md does not match the gunzipped file.
(b) content_sha256 — fails if a row's hash is not sha256 of blobs joined
    by blank lines.
(c) session_ids order — fails if a materialized row's session_ids differ
    from packets.jsonl / packets_abs.jsonl session order.
(d) materialize_packets.py --verify on the first 5 rows of each packet
    file — skipped when the pinned dataset path is absent; fails if the
    rebuilt serialized line is not byte-identical.
    (e) render_extraction — fails if unsorted/duplicate/out-of-range indices
    are accepted, or if elision markers are misplaced.
    README/manifest truth — fails if README hardcodes a stale export count,
    claims haystack text is unreleased, defers the packet boundary to paper
    §8, or if packets_materialized/MANIFEST.md is missing from
    RELEASE_MANIFEST.md, or if RELEASE_MANIFEST.md pins a generation HEAD.
    Per-run materialized/facts — fails if the manifest/script claims those
    tracked files are uncommitted byte-identical duplicates of the gzip.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import materialize_packets as m  # noqa: E402

EVAL = REPO / "eval" / "dense_chain_v32_20260830"
PACKETS_DIR = EVAL / "packets_materialized"
MANIFEST = PACKETS_DIR / "MANIFEST.md"
RELEASE_MANIFEST = EVAL / "RELEASE_MANIFEST.md"
README = REPO / "README.md"
MATERIALIZED_GZ = PACKETS_DIR / "materialized_all.jsonl.gz"
FACTS_GZ = PACKETS_DIR / "facts_all.jsonl.gz"
PACKETS = EVAL / "packets.jsonl"
PACKETS_ABS = EVAL / "packets_abs.jsonl"
PACKETS_MANIFEST_REL = "eval/dense_chain_v32_20260830/packets_materialized/MANIFEST.md"
DATASET = Path("/Users/cj/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json")
FILE_ROW_RE = re.compile(
    r"^\| `([^`]+)` \| (\d+) \| `([0-9a-f]{64})` \|$"
)


def parse_manifest_files(text: str) -> dict[str, tuple[int, str]]:
    out: dict[str, tuple[int, str]] = {}
    for line in text.splitlines():
        match = FILE_ROW_RE.match(line)
        if match:
            out[match.group(1)] = (int(match.group(2)), match.group(3))
    return out


def gunzip_bytes(path: Path) -> bytes:
    with gzip.open(path, "rb") as fh:
        return fh.read()


def load_jsonl_bytes(raw: bytes) -> list[dict]:
    rows = []
    for line in raw.decode("utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def md_section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.index(marker)
    rest = text[start + len(marker) :]
    nxt = rest.find("\n## ")
    return rest if nxt < 0 else rest[:nxt]


def load_packet_session_ids() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for path in (PACKETS, PACKETS_ABS):
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                out[row["question_id"]] = [s["session_id"] for s in row["sessions"]]
    return out


def test_packets_manifest_verify_uses_env_var_not_pinned_path():
    intro = md_section(MANIFEST.read_text(), "Verify the rendering")
    assert "pinned path" not in intro
    assert "$LONGMEMEVAL_S_JSON" in intro
    assert "public dataset JSON" in intro


def test_gz_sha256_and_row_counts_match_manifest():
    pins = parse_manifest_files(MANIFEST.read_text())
    assert "materialized_all.jsonl.gz" in pins
    assert "facts_all.jsonl.gz" in pins
    for name, path in (
        ("materialized_all.jsonl.gz", MATERIALIZED_GZ),
        ("facts_all.jsonl.gz", FACTS_GZ),
    ):
        expected_n, expected_sha = pins[name]
        raw = gunzip_bytes(path)
        got_sha = hashlib.sha256(raw).hexdigest()
        got_n = sum(1 for line in raw.decode("utf-8").splitlines() if line.strip())
        assert got_sha == expected_sha
        assert got_n == expected_n


def test_content_sha256_matches_joined_blobs():
    rows = load_jsonl_bytes(gunzip_bytes(MATERIALIZED_GZ))
    assert rows
    for row in rows:
        joined = "\n\n".join(row["session_blobs"])
        got = hashlib.sha256(joined.encode("utf-8")).hexdigest()
        assert got == row["content_sha256"], row["question_id"]


def test_session_ids_match_packet_order():
    packet_ids = load_packet_session_ids()
    rows = load_jsonl_bytes(gunzip_bytes(MATERIALIZED_GZ))
    assert len(rows) == len(packet_ids)
    for row in rows:
        qid = row["question_id"]
        assert row["session_ids"] == packet_ids[qid]


def test_verify_first_five_rows_roundtrip(tmp_path: Path):
    if not DATASET.is_file():
        pytest.skip(f"dataset not present: {DATASET}")
    pkt_lines = [l for l in PACKETS.read_text().splitlines() if l.strip()]
    abs_lines = [l for l in PACKETS_ABS.read_text().splitlines() if l.strip()]
    first_pkt = pkt_lines[:5]
    first_abs = abs_lines[:5]
    want_ids = [json.loads(l)["question_id"] for l in first_pkt + first_abs]
    released_by_qid: dict[str, str] = {}
    for line in gunzip_bytes(MATERIALIZED_GZ).decode("utf-8").splitlines():
        if line.strip():
            released_by_qid[json.loads(line)["question_id"]] = line
    missing = [qid for qid in want_ids if qid not in released_by_qid]
    assert not missing
    p5 = tmp_path / "packets5.jsonl"
    a5 = tmp_path / "packets_abs5.jsonl"
    v10 = tmp_path / "verify10.jsonl"
    p5.write_text("".join(l + "\n" for l in first_pkt))
    a5.write_text("".join(l + "\n" for l in first_abs))
    v10.write_text("".join(released_by_qid[qid] + "\n" for qid in want_ids))
    rc = m.main(
        [
            "--data",
            str(DATASET),
            "--packets",
            str(p5),
            "--packets",
            str(a5),
            "--verify",
            str(v10),
        ]
    )
    assert rc == 0


def test_readme_does_not_hardcode_stale_export_count():
    readme = README.read_text()
    preamble = readme.split("## ", 1)[0]
    assert "Nothing here was edited after export" not in readme
    manifest = RELEASE_MANIFEST.read_text()
    header_n = int(re.search(r"Files: (\d+)", manifest).group(1))
    table_n = len(parse_manifest_files(manifest))
    assert header_n == table_n
    for match in re.finditer(r"(\d+) files", preamble):
        assert int(match.group(1)) == header_n


def test_readme_dataset_section_matches_packets_release():
    dataset = md_section(README.read_text(), "Dataset")
    assert "the haystack sessions are not redistributed here" not in dataset
    assert "session_blobs" in dataset
    assert "packets_materialized" in dataset
    assert "raw dataset JSON is not" in dataset


def test_readme_held_does_not_defer_packet_boundary_to_paper():
    readme = README.read_text()
    held = md_section(readme, "What is held")
    packets = md_section(readme, "Packets")
    assert "paper §8" not in held
    assert "packets_materialized/MANIFEST.md" in packets
    assert "Paper §8 still lists materialized packets as held" not in packets
    assert "still lists materialized packets as held" not in readme


def test_packets_manifest_is_a_release_manifest_row():
    rows = parse_manifest_files(RELEASE_MANIFEST.read_text())
    assert PACKETS_MANIFEST_REL in rows
    path = REPO / PACKETS_MANIFEST_REL
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    assert rows[PACKETS_MANIFEST_REL][1] == got


def test_release_manifest_header_does_not_pin_git_head():
    header = RELEASE_MANIFEST.read_text().split("##", 1)[0]
    assert "Generated at HEAD" not in header
    assert re.search(r"HEAD `[0-9a-f]{7,}`", header) is None


UNCOMMITTED_DUP_RE = re.compile(r"not committed.{0,120}byte-identical", re.I | re.S)
PER_RUN_MATERIALIZED = (
    "eval/dense_chain_v32_20260830/sc_flip/materialized.jsonl"
)
PER_RUN_FACTS = "eval/dense_chain_v32_20260830/full_pass1/facts_all.jsonl"


def test_build_release_manifest_omits_uncommitted_duplicate_claim():
    """r3: script must not emit 'uncommitted because byte-identical'.
    Fails if that sentence returns in the generator source."""
    src = (SCRIPTS / "build_release_manifest.py").read_text()
    assert UNCOMMITTED_DUP_RE.search(src) is None


def test_release_manifest_does_not_claim_per_run_materialized_uncommitted():
    """r3: Released table lists per-run materialized/facts files that are
    tracked and not the headline gzip. Preamble must not call them
    uncommitted duplicates. Fails if the false sentence returns, if those
    rows vanish, or if a listed per-run file hashes to the uncompressed gzip.
    """
    manifest = RELEASE_MANIFEST.read_text()
    header = manifest.split("\n## ", 1)[0]
    assert UNCOMMITTED_DUP_RE.search(header) is None
    rows = parse_manifest_files(manifest)
    assert PER_RUN_MATERIALIZED in rows
    assert PER_RUN_FACTS in rows
    pins = parse_manifest_files(MANIFEST.read_text())
    headline_shas = {
        pins["materialized_all.jsonl.gz"][1],
        pins["facts_all.jsonl.gz"][1],
    }
    for rel in (PER_RUN_MATERIALIZED, PER_RUN_FACTS):
        got = hashlib.sha256((REPO / rel).read_bytes()).hexdigest()
        assert got not in headline_shas, rel


def test_render_extraction_rejects_unsorted():
    with pytest.raises(m.MaterializeError, match="sorted"):
        m.render_extraction("a\nb\nc", [1, 0])


def test_render_extraction_rejects_duplicate():
    with pytest.raises(m.MaterializeError, match="unique"):
        m.render_extraction("a\nb\nc", [1, 1])


def test_render_extraction_rejects_out_of_range():
    with pytest.raises(m.MaterializeError, match="out of range"):
        m.render_extraction("a\nb\nc", [3])
    with pytest.raises(m.MaterializeError, match="out of range"):
        m.render_extraction("a\nb\nc", [-1])


def test_render_extraction_marker_before_between_after():
    blob = "a\nb\nc\nd\ne"
    assert m.render_extraction(blob, [2, 3, 4]) == (
        "[... 2 lines elided ...]\nc\nd\ne"
    )
    assert m.render_extraction(blob, [0, 4]) == (
        "a\n[... 3 lines elided ...]\ne"
    )
    assert m.render_extraction(blob, [0, 1]) == (
        "a\nb\n[... 3 lines elided ...]"
    )
