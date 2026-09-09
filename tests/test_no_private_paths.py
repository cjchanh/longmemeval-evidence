"""The reproducibility surface of the release must not carry the author's home path.

Frozen evidence artifacts (facts_*.json, judge.log, ...) are hashed receipts of what ran
and are allowed to keep the logged command lines; runners, scripts, tests and docs are not.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRIVATE = "/Users/" + "cj"  # split so this file does not match itself

SCANNED_GLOBS = (
    "README.md",
    "docs/**/*.md",
    "scripts/**/*.py",
    "scripts/**/*.sh",
    "tests/**/*.py",
    "eval/**/run_*.sh",
    "eval/**/*.md",
)


def _files():
    for pattern in SCANNED_GLOBS:
        for path in ROOT.glob(pattern):
            if path.is_file() and path != pathlib.Path(__file__).resolve():
                yield path


def test_reproducibility_surface_has_no_private_home_path():
    hits = []
    for path in _files():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if PRIVATE in line and "MACHINE_DATASET" not in line:
                hits.append(f"{path.relative_to(ROOT)}:{lineno}")
    assert hits == [], "private home path in reproducibility surface: " + ", ".join(hits)
