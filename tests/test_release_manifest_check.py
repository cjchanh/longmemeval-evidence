"""CLI tests for scripts/build_release_manifest.py --check and the signature wrapper."""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "build_release_manifest.py"
SIG_SCRIPT = REPO / "scripts" / "verify_release_manifest_signature.sh"
EVAL = REPO / "eval" / "dense_chain_v32_20260830"
MANIFEST = EVAL / "RELEASE_MANIFEST.md"
ROOT = EVAL / "RELEASE_MANIFEST.root"
PROBE = REPO / "benchmarks/longmemeval-judge-gate/GROUND_TRUTH_SURVEY.md"
PROBE_REL = "benchmarks/longmemeval-judge-gate/GROUND_TRUTH_SURVEY.md"
WORKFLOW = REPO / ".github" / "workflows" / "release-manifest.yml"

sys.path.insert(0, str(REPO / "scripts"))
import build_release_manifest as brm  # noqa: E402


def _run_check() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )


def test_check_passes_on_current_tree():
    result = _run_check()
    assert result.returncode == 0, result.stderr
    assert "manifest_root_sha256" in result.stdout


def test_root_file_is_sha256_of_manifest_body():
    body = MANIFEST.read_bytes()
    assert ROOT.read_text().strip() == hashlib.sha256(body).hexdigest()


def test_check_does_not_write():
    before_m = MANIFEST.read_bytes()
    before_r = ROOT.read_bytes()
    result = _run_check()
    assert result.returncode == 0, result.stderr
    assert MANIFEST.read_bytes() == before_m
    assert ROOT.read_bytes() == before_r


def test_check_exits_1_when_released_file_modified(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(REPO)
    live = PROBE.read_bytes()
    probe = tmp_path / "GROUND_TRUTH_SURVEY.md"
    probe.write_bytes(live + b"\n# check-probe\n")
    orig = brm.sha256

    def sha256(p: Path) -> str:
        if Path(p).as_posix() == PROBE_REL:
            return orig(probe)
        return orig(p)

    monkeypatch.setattr(brm, "sha256", sha256)
    rc = brm.main(["--check"])
    captured = capsys.readouterr()
    named = captured.out + captured.err
    assert rc == 1
    assert "GROUND_TRUTH_SURVEY.md" in named
    assert PROBE.read_bytes() == live


def test_signature_script_returns_2_with_no_sig():
    assert not (EVAL / "RELEASE_MANIFEST.root.sig").exists()
    result = subprocess.run(
        ["bash", str(SIG_SCRIPT)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert result.stdout.strip() == "UNSIGNED"


README = REPO / "README.md"
PACKETS_MANIFEST = EVAL / "packets_materialized" / "MANIFEST.md"
ANCHORS = EVAL / "ANCHORS.md"
PIN_TEST = REPO / "tests" / "test_upstream_judge_pin.py"
MACHINE_DATASET = "/Users/" + "cj" + "/.archivist/eval/longmemeval-s/longmemeval_s_cleaned.json"  # split so no tracked file carries the literal
STALE_S8 = "Paper §8 still lists materialized packets as held"
WAIVER = '"answer no.\\n\\n", "answer no. \\n\\n"'


def test_readme_does_not_claim_paper_s8_still_holds_packets():
    text = README.read_text()
    assert STALE_S8 not in text
    assert "still lists materialized packets as held" not in text


def test_upstream_pin_test_does_not_waive_base_template_space():
    src = PIN_TEST.read_text()
    assert WAIVER not in src
    assert 'replace(\n        "answer no.\\n\\n"' not in src


def test_pin_tests_compare_composed_ku_to_upstream_decoded_2():
    src = PIN_TEST.read_text()
    assert "decoded[2]" in src
    assert "KU_ADDITION" in src
    assert "decoded[1]" in src
    assert "TEMPORAL_ADDITION" in src
    assert "part in src" not in src


def test_packets_manifest_verify_uses_placeholder_dataset_path():
    text = PACKETS_MANIFEST.read_text()
    assert MACHINE_DATASET not in text
    assert "$LONGMEMEVAL_S_JSON" in text
    assert MACHINE_DATASET not in README.read_text()
    assert "pinned path" not in text


def test_anchors_publish_location_is_a_url():
    text = ANCHORS.read_text()
    assert "https://github.com/cjchanh/longmemeval-evidence" in text
    assert "the company receipts page" not in text
    assert "no named tag" in text


def test_readme_root_hash_matches_root_file():
    pin = ROOT.read_text().strip()
    assert pin in README.read_text()
    assert len(pin) == 64


def test_check_exits_1_when_readme_root_pin_stale(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(REPO)
    live = README.read_text()
    pin = ROOT.read_text().strip()
    stale_path = tmp_path / "README.md"
    stale = live.replace(pin, "0" * 64, 1)
    assert stale != live
    stale_path.write_text(stale)
    monkeypatch.setattr(brm, "README", str(stale_path))
    rc = brm.main(["--check"])
    captured = capsys.readouterr()
    named = captured.out + captured.err
    assert rc == 1
    assert "README.md" in named
    assert README.read_text() == live


def test_check_tests_do_not_write_live_release_files():
    src = Path(__file__).read_text().split(
        "def test_check_tests_do_not_write_live_release_files"
    )[0]
    assert "PROBE.write_bytes(" not in src
    assert "PROBE.write_text(" not in src
    assert "README.write_text(" not in src


def test_workflow_pins_actions_to_commit_shas():
    text = WORKFLOW.read_text()
    assert re.search(r"actions/checkout@[0-9a-f]{40}", text)
    assert re.search(r"actions/setup-python@[0-9a-f]{40}", text)
    assert "actions/checkout@v4\n" not in text
    assert "actions/setup-python@v5\n" not in text


def test_tracked_falls_back_when_git_ls_files_exits_nonzero(tmp_path, monkeypatch):
    prefix = tmp_path / "eval_prefix"
    (prefix / "nested").mkdir(parents=True)
    (prefix / "nested" / "a.txt").write_text("x")
    monkeypatch.chdir(tmp_path)

    def fake_run(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args")
        return subprocess.CompletedProcess(cmd, 128, stdout=b"", stderr=b"fatal")

    monkeypatch.setattr(brm.subprocess, "run", fake_run)
    assert brm.tracked("eval_prefix") == ["eval_prefix/nested/a.txt"]


def test_tracked_falls_back_when_git_missing(tmp_path, monkeypatch):
    prefix = tmp_path / "eval_prefix"
    (prefix / "nested").mkdir(parents=True)
    (prefix / "nested" / "a.txt").write_text("x")
    monkeypatch.chdir(tmp_path)

    def boom(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(brm.subprocess, "run", boom)
    assert brm.tracked("eval_prefix") == ["eval_prefix/nested/a.txt"]
