#!/usr/bin/env python3
"""Rebuild the released materialized packets from public dataset + packet files.

Proves: each materialized row is a pure rendering of the public LongMemEval-S
dataset sessions listed (in order) by packets.jsonl / packets_abs.jsonl —
date line plus `{role}: {content}` turns, with `kept_chars` truncation or
`kept_line_indices` extraction applied. `content_sha256` is sha256 of the
blobs joined by blank lines. Accounting tokens are ceil(chars/4) over that
joined packet text.

Does not: re-run retrieval, rerank, or the packet compiler. Those remain held.
Never reads gold/answer fields.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable, TextIO

SCHEMA = "cds/dense-chain-coverage-materialized-packet/v1"
EXPECTED_RELEASE_ROWS = 500
EVAL_DIR = Path("eval/dense_chain_v32_20260830")
DEFAULT_PACKETS = [
    EVAL_DIR / "packets.jsonl",
    EVAL_DIR / "packets_abs.jsonl",
]
DATASET_KEEP = (
    "question_id",
    "haystack_session_ids",
    "haystack_sessions",
    "haystack_dates",
)


class MaterializeError(Exception):
    """Fail-closed rematerialization error."""


def session_blob(session: Any, date: Any) -> str:
    lines: list[str] = []
    if date:
        lines.append(f"date: {date}")
    if not isinstance(session, list):
        raise MaterializeError("haystack session is not a list of turns")
    for turn in session:
        if not isinstance(turn, dict):
            raise MaterializeError("haystack turn is not an object")
        content = str(turn.get("content") or "").strip()
        if not content:
            continue
        role = turn.get("role") or "unknown"
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def render_extraction(full_blob: str, kept_line_indices: Any) -> str:
    if not isinstance(kept_line_indices, list):
        raise MaterializeError("kept_line_indices must be a list")
    try:
        indices = [int(i) for i in kept_line_indices]
    except (TypeError, ValueError) as exc:
        raise MaterializeError("kept_line_indices must be integers") from exc
    if indices != sorted(indices):
        raise MaterializeError("kept_line_indices must be sorted")
    if len(set(indices)) != len(indices):
        raise MaterializeError("kept_line_indices must be unique")
    lines = full_blob.split("\n")
    n = len(lines)
    for i in indices:
        if i < 0 or i >= n:
            raise MaterializeError(f"kept_line_indices out of range: {i}")
    kept = set(indices)
    out: list[str] = []
    i = 0
    while i < n:
        if i in kept:
            out.append(lines[i])
            i += 1
            continue
        j = i
        while j < n and j not in kept:
            j += 1
        out.append(f"[... {j - i} lines elided ...]")
        i = j
    return "\n".join(out)


def _index_by_sid(records: Any, kind: str) -> dict[str, dict]:
    if not records:
        return {}
    if not isinstance(records, list):
        raise MaterializeError(f"{kind} must be a list")
    out: dict[str, dict] = {}
    for rec in records:
        if not isinstance(rec, dict):
            raise MaterializeError(f"{kind} entry is not an object")
        sid = rec.get("session_id")
        if not isinstance(sid, str) or not sid:
            raise MaterializeError(f"{kind} missing session_id")
        if sid in out:
            raise MaterializeError(f"duplicate {kind} session id {sid!r}")
        out[sid] = rec
    return out


def _resolve_session(item: dict, session_id: str, packet_date: Any) -> tuple[Any, Any]:
    ids = item["haystack_session_ids"]
    sessions = item["haystack_sessions"]
    dates = item["haystack_dates"]
    if not (isinstance(ids, list) and isinstance(sessions, list) and isinstance(dates, list)):
        raise MaterializeError(f"{item.get('question_id')}: haystack lists are malformed")
    if not (len(ids) == len(sessions) == len(dates)):
        raise MaterializeError(f"{item.get('question_id')}: haystack lists are misaligned")
    hits = [i for i, sid in enumerate(ids) if sid == session_id]
    if not hits:
        raise MaterializeError(f"unknown session id {session_id!r}")
    if len(hits) == 1:
        i = hits[0]
        return sessions[i], dates[i]
    matched = [i for i in hits if dates[i] == packet_date]
    if len(matched) == 1:
        i = matched[0]
        return sessions[i], dates[i]
    raise MaterializeError(
        f"duplicate session id {session_id!r} "
        f"(hits={len(hits)} date-matches={len(matched)})"
    )


def _require_int(rec: dict, key: str, kind: str) -> int:
    val = rec.get(key)
    if not isinstance(val, int) or isinstance(val, bool):
        raise MaterializeError(f"{kind} {key} must be an int")
    return val


def serialize_row(row: dict) -> str:
    return json.dumps(row, sort_keys=True)


def materialize_row(packet: dict, item: dict) -> dict:
    qid = packet.get("question_id")
    if not isinstance(qid, str) or not qid:
        raise MaterializeError("packet missing question_id")
    sessions = packet.get("sessions")
    if not isinstance(sessions, list) or not sessions:
        raise MaterializeError(f"{qid}: packet has no sessions")
    trunc_recs = packet.get("truncations") or []
    extr_recs = packet.get("extractions") or []
    trunc_by = _index_by_sid(trunc_recs, "truncation")
    extr_by = _index_by_sid(extr_recs, "extraction")
    overlap = set(trunc_by) & set(extr_by)
    if overlap:
        raise MaterializeError(
            f"{qid}: session carries both truncation and extraction: {sorted(overlap)}"
        )
    session_ids: list[str] = []
    seen_sids: set[str] = set()
    blobs: list[str] = []
    for sess in sessions:
        if not isinstance(sess, dict):
            raise MaterializeError(f"{qid}: session entry is not an object")
        sid = sess.get("session_id")
        if not isinstance(sid, str) or not sid:
            raise MaterializeError(f"{qid}: session missing session_id")
        if sid in seen_sids:
            raise MaterializeError(f"{qid}: duplicate session id {sid!r}")
        seen_sids.add(sid)
        haystack_sess, haystack_date = _resolve_session(item, sid, sess.get("date"))
        full = session_blob(haystack_sess, haystack_date)
        if sid in trunc_by:
            rec = trunc_by[sid]
            original = _require_int(rec, "original_chars", "truncation")
            kept = _require_int(rec, "kept_chars", "truncation")
            if len(full) != original:
                raise MaterializeError(
                    f"{qid}: {sid} original_chars {original} != {len(full)}"
                )
            blob = full[:kept]
            if len(blob) != kept:
                raise MaterializeError(
                    f"{qid}: {sid} kept_chars {kept} != {len(blob)}"
                )
        elif sid in extr_by:
            rec = extr_by[sid]
            original = _require_int(rec, "original_chars", "extraction")
            kept = _require_int(rec, "kept_chars", "extraction")
            blob = render_extraction(full, rec.get("kept_line_indices"))
            if len(full) != original:
                raise MaterializeError(
                    f"{qid}: {sid} original_chars {original} != {len(full)}"
                )
            if len(blob) != kept:
                raise MaterializeError(
                    f"{qid}: {sid} kept_chars {kept} != {len(blob)}"
                )
        else:
            blob = full
        session_ids.append(sid)
        blobs.append(blob)
    for sid in trunc_by:
        if sid not in seen_sids:
            raise MaterializeError(f"{qid}: truncation for session not in packet: {sid!r}")
    for sid in extr_by:
        if sid not in seen_sids:
            raise MaterializeError(f"{qid}: extraction for session not in packet: {sid!r}")
    joined = "\n\n".join(blobs)
    packet_chars = len(joined)
    tokens = math.ceil(packet_chars / 4)
    budget_src = packet.get("budget") or {}
    if not isinstance(budget_src, dict):
        raise MaterializeError(f"{qid}: budget is not an object")
    extractions_out = [
        {
            "extraction": rec["extraction"],
            "kept_chars": rec["kept_chars"],
            "original_chars": rec["original_chars"],
            "session_id": rec["session_id"],
        }
        for rec in extr_recs
    ]
    truncations_out = [
        {
            "kept_chars": rec["kept_chars"],
            "original_chars": rec["original_chars"],
            "session_id": rec["session_id"],
        }
        for rec in trunc_recs
    ]
    return {
        "accounting": {
            "n_extracted_sessions": len(extractions_out),
            "n_sessions": len(session_ids),
            "n_truncated_sessions": len(truncations_out),
            "packet_chars": packet_chars,
            "tokens": tokens,
        },
        "budget": {
            "max_sessions": budget_src.get("max_sessions"),
            "max_tokens": budget_src.get("max_tokens"),
        },
        "content_sha256": hashlib.sha256(joined.encode("utf-8")).hexdigest(),
        "extractions": extractions_out,
        "question_id": qid,
        "schema": SCHEMA,
        "session_blobs": blobs,
        "session_ids": session_ids,
        "truncations": truncations_out,
    }


def load_dataset(path: Path) -> dict[str, dict]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise MaterializeError(f"{path}: dataset is not a list")
    out: dict[str, dict] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise MaterializeError(f"{path}: dataset item is not an object")
        qid = item.get("question_id")
        if not isinstance(qid, str) or not qid:
            raise MaterializeError(f"{path}: dataset item missing question_id")
        if qid in out:
            raise MaterializeError(f"{path}: duplicate dataset question_id {qid!r}")
        try:
            out[qid] = {k: item[k] for k in DATASET_KEEP}
        except KeyError as exc:
            raise MaterializeError(f"{path}: {qid} missing {exc}") from exc
    return out


def load_packets(paths: Iterable[Path]) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for path in paths:
        with path.open(encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise MaterializeError(f"{path}:{lineno}: not JSON: {exc}") from exc
                if not isinstance(row, dict):
                    raise MaterializeError(f"{path}:{lineno}: row is not an object")
                qid = row.get("question_id")
                if not isinstance(qid, str) or not qid:
                    raise MaterializeError(f"{path}:{lineno}: missing question_id")
                if qid in seen:
                    raise MaterializeError(f"duplicate question_id {qid!r}")
                seen.add(qid)
                rows.append(row)
    return rows


def materialize_packets(packets: list[dict], dataset: dict[str, dict]) -> list[dict]:
    rows: list[dict] = []
    for packet in packets:
        qid = packet.get("question_id")
        item = dataset.get(qid) if isinstance(qid, str) else None
        if item is None:
            raise MaterializeError(f"packet without a dataset item: {qid!r}")
        rows.append(materialize_row(packet, item))
    return rows


def _open_text(path: Path) -> TextIO:
    if path.suffix == ".gz" or path.name.endswith(".jsonl.gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open(encoding="utf-8")


def load_verify_lines(path: Path) -> list[str]:
    with _open_text(path) as fh:
        lines = [line.rstrip("\n") for line in fh if line.strip()]
    return lines


def verify_rows(rebuilt: list[dict], verify_path: Path) -> tuple[int, int, int]:
    released_lines = load_verify_lines(verify_path)
    n = len(rebuilt)
    identical = 0
    mismatched = 0
    limit = max(n, len(released_lines))
    for i in range(limit):
        if i >= n or i >= len(released_lines):
            mismatched += 1
            continue
        rebuilt_line = serialize_row(rebuilt[i])
        released_line = released_lines[i]
        try:
            released_obj = json.loads(released_line)
        except json.JSONDecodeError:
            mismatched += 1
            continue
        if released_obj == rebuilt[i] and released_line == rebuilt_line:
            identical += 1
        else:
            mismatched += 1
    return n, identical, mismatched


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True, help="LongMemEval-S cleaned JSON")
    ap.add_argument(
        "--packets",
        action="append",
        default=None,
        help="packet JSONL (repeatable; default packets.jsonl then packets_abs.jsonl)",
    )
    ap.add_argument("--out", default=None, help="write rebuilt JSONL")
    ap.add_argument(
        "--verify",
        default=None,
        help="released .jsonl or .jsonl.gz to compare against",
    )
    args = ap.parse_args(argv)
    if not args.out and not args.verify:
        print("FAIL: need --out and/or --verify", file=sys.stderr)
        return 1
    packet_paths = [Path(p) for p in (args.packets or [str(p) for p in DEFAULT_PACKETS])]
    try:
        dataset = load_dataset(Path(args.data))
        packets = load_packets(packet_paths)
        rebuilt = materialize_packets(packets, dataset)
    except MaterializeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fh:
            for row in rebuilt:
                fh.write(serialize_row(row) + "\n")
    if args.verify:
        n, identical, mismatched = verify_rows(rebuilt, Path(args.verify))
        print(f"rows={n} identical={identical} mismatched={mismatched}")
        released_n = len(load_verify_lines(Path(args.verify)))
        if released_n == EXPECTED_RELEASE_ROWS and n != EXPECTED_RELEASE_ROWS:
            return 1
        if mismatched == 0 and n == released_n:
            return 0
        return 1
    print(f"rows={len(rebuilt)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
