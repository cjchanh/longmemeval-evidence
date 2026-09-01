#!/usr/bin/env python3
"""Diff the v3.4 and v3.5 facts artifacts and emit the audit JSON behind
DIFF_REPORT.md.

Gold-blindness: the row CLASS labels read here (``selector_class``) are derived
from question text by the v4 selector, not from gold. The gold fields present in
replay_rows.jsonl are read for exactly one thing, the SCORING-ONLY coverage note
at the bottom of the report, and that number is labelled as such and is not an
input to anything the scaffold emits.

Additive check: v3.5 is supposed to APPEND to the v3.4 text, never rewrite it.
This script verifies that mechanically per row (every v3.4 line survives, in
order) rather than asserting it in prose.
"""
from __future__ import annotations

import json
import sys
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVAL = HERE.parents[1]


def load(path: Path) -> dict[str, dict]:
    return {
        r["question_id"]: r
        for r in (json.loads(l) for l in path.read_text().splitlines() if l.strip())
    }


def line_delta(old: str, new: str) -> tuple[list[str], list[str]]:
    """(added lines, removed lines) between two facts_text blobs."""
    a, b = old.split("\n"), new.split("\n")
    added: list[str] = []
    removed: list[str] = []
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, a, b).get_opcodes():
        if tag in ("insert", "replace"):
            added.extend(b[j1:j2])
        if tag in ("delete", "replace"):
            removed.extend(a[i1:i2])
    return added, removed


def main() -> int:
    arms = {
        "answerable": (
            EVAL / "facts_v34.jsonl",
            HERE / "facts_v35.jsonl",
            HERE / "anchors_v35.jsonl",
        ),
        "abs": (
            EVAL / "facts_abs_v34.jsonl",
            HERE / "facts_abs_v35.jsonl",
            HERE / "anchors_abs_v35.jsonl",
        ),
    }
    classes = {
        r["question_id"]: r
        for r in (
            json.loads(l)
            for l in (EVAL / "v4" / "selector" / "replay_rows.jsonl")
            .read_text()
            .splitlines()
            if l.strip()
        )
    }

    report: dict = {"arms": {}, "changed": [], "unchanged_with_anchors": []}
    for arm, (v34p, v35p, anchp) in arms.items():
        v34, v35 = load(v34p), load(v35p)
        anch = load(anchp)
        assert set(v34) == set(v35), f"{arm}: row-id sets differ"
        changed = [q for q in sorted(v34) if v34[q]["facts_text"] != v35[q]["facts_text"]]
        report["arms"][arm] = {
            "n_rows": len(v34),
            "n_changed": len(changed),
            "n_rows_with_anchors_found": sum(
                1 for a in anch.values() if a["n_intext_anchors_found"]
            ),
            "n_rows_with_anchors_emitted": sum(
                1 for a in anch.values() if a["n_intext_anchors"]
            ),
        }
        for q in changed:
            added, removed = line_delta(v34[q]["facts_text"], v35[q]["facts_text"])
            a = anch.get(q, {})
            cls = classes.get(q, {})
            report["changed"].append(
                {
                    "arm": arm,
                    "question_id": q,
                    "selector_class": cls.get("selector_class"),
                    "question_type": cls.get("question_type"),
                    "activated": v35[q]["activated"],
                    "n_intext_anchors": a.get("n_intext_anchors"),
                    "n_intext_anchors_found": a.get("n_intext_anchors_found"),
                    "n_session_days": a.get("n_session_days"),
                    "n_added_lines": len(added),
                    "n_removed_lines": len(removed),
                    "removed_lines": removed,
                    "names_provenance": all(
                        ' from "' in ln for ln in added if ln.startswith("    - ")
                    )
                    and any(ln.startswith("    - ") for ln in added),
                    "anchor_dates": [x["date"] for x in a.get("anchors", [])],
                    "anchor_surfaces": [x["surface"] for x in a.get("anchors", [])],
                }
            )
        # rows that HAVE in-text anchors but did not change: expected whenever
        # date_duration never activated, since the block is scoped to that
        # operator. Recorded so the scoping is visible, not assumed.
        changed_set = set(changed)
        for q, a in sorted(anch.items()):
            if a["n_intext_anchors_found"] and q not in changed_set:
                report["unchanged_with_anchors"].append(
                    {
                        "arm": arm,
                        "question_id": q,
                        "activated": a["activated"],
                        "n_intext_anchors_found": a["n_intext_anchors_found"],
                        "date_duration_active": "date_duration" in a["activated"],
                    }
                )
    (HERE / "diff_v34_v35.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["arms"], indent=1))
    print("total changed:", len(report["changed"]))
    print("unchanged despite anchors:", len(report["unchanged_with_anchors"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
