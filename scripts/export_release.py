#!/usr/bin/env python3
"""Export the LongMemEval-S evidence release into a standalone directory.

Why: the paper's §8 promises a public evidence repository whose files match
RELEASE_MANIFEST.md byte-for-byte. Origin is private, so the release is a
separate tree. This script copies exactly the manifest's rows (no globbing,
no discovery) into --dest, preserving relative paths, then re-hashes every
copy against the manifest and fails closed on any mismatch or missing file.

Never touches the source tree. Refuses a non-empty --dest unless --force.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
from pathlib import Path

MANIFEST = Path("eval/dense_chain_v32_20260830/RELEASE_MANIFEST.md")
ROW = re.compile(r"^\| `([^`]+)` \| (\d+) \| `([0-9a-f]{64})` \|$")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_manifest(path: Path) -> list[tuple[str, int, str]]:
    rows = []
    for line in path.read_text().splitlines():
        m = ROW.match(line)
        if m:
            rows.append((m.group(1), int(m.group(2)), m.group(3)))
    if not rows:
        raise SystemExit(f"FAIL: no manifest rows parsed from {path}")
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    ap.add_argument("--manifest", default=str(MANIFEST))
    ap.add_argument("--force", action="store_true", help="allow a non-empty --dest")
    a = ap.parse_args(argv)
    dest = Path(a.dest).expanduser().resolve()
    if dest.exists() and any(dest.iterdir()) and not a.force:
        print(f"FAIL: {dest} is not empty (use --force to overwrite files in place)", file=sys.stderr)
        return 1
    rows = parse_manifest(Path(a.manifest))
    bad: list[str] = []
    for rel, size, digest in rows:
        src = Path(rel)
        if not src.is_file():
            bad.append(f"missing source: {rel}")
            continue
        if sha256(src) != digest:
            bad.append(f"source drifted from manifest: {rel}")
            continue
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, out)
        if out.stat().st_size != size or sha256(out) != digest:
            bad.append(f"copy mismatch: {rel}")
    # the manifest itself travels with the release (it is not one of its own rows)
    shutil.copyfile(a.manifest, dest / Path(a.manifest))
    if bad:
        print("FAIL:\n  " + "\n  ".join(bad), file=sys.stderr)
        return 1
    print(f"exported {len(rows)} files to {dest}; every copy re-hashed against the manifest: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
