#!/usr/bin/env python3
"""Claude CLI (operator's Claude subscription) transport for the LME chain.

Single-turn headless mode: `claude -p <prompt> --model <model>
--output-format text --tools ""` prints the model's answer to stdout and
exits. `--tools ""` disables all agentic tools (Bash/Read/Edit/etc.) so the
reader is a pure text-completion call — it never touches the filesystem or
runs commands, matching the read-only contract of every other reader lane.
The call also runs from a per-process scratch cwd (never this repo), so it
never inherits this repo's CLAUDE.md/settings context and cannot pollute the
prompt with local project state.

Verified against the installed CLI (2.1.252) before writing this module:
  - `claude -p <prompt> --model <model> --output-format text` prints the
    clean answer to stdout; ALL chrome (untrusted-workspace notices,
    permission-rule warnings) goes to stderr, never stdout.
  - `--tools ""` disables tool access and produces zero stderr chrome from a
    scratch cwd — the production shape used here.
  - A 128,295-char real packet prompt (LME question_id 08f4fc43, v3.4-facts
    packet) round-tripped via argv in ~20s, rc=0, correct answer.
  - There is no CLI flag to read the prompt from a file (`@path` is treated
    as literal prompt text the agent may try to interpret, not a
    file-read directive). Piping the prompt on stdin to `claude -p` with no
    positional prompt argument DOES work (probed with a literal pipe) — used
    as the >800k-char fallback instead of a temp file.
  - A bogus `--model` value returns rc=1, stdout carries a
    "issue with the selected model ... may not exist" sentence, and stderr
    carries a structured `[claude-code:unrecognized_model]` tag — the tag is
    matched by _LANE_DOWN.
  - A bogus flag returns rc=1 with `error: unknown option '...'` on stderr,
    matched by _LANE_DOWN's `^error:` anchor.

Fail-closed like the other lanes: transport errors raise, never return
error-shaped text as an answer. Any non-zero return code is refused
regardless of banner match — the banner regex only labels *why*, it is
never required to trigger the refusal.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

MODEL = os.environ.get("LME_CLAUDE_CLI_MODEL", "opus")

_TIMEOUT_BASE_S = 240
_TIMEOUT_CHARS_PER_SECOND = 400
_TIMEOUT_MIN_S = 300
_TIMEOUT_MAX_S = 900

# argv ARG_MAX safety line (mirrors grok_cli_lane's 800k cutoff); above this
# the prompt goes over stdin instead (verified working — see module docstring).
_ARGV_PROMPT_MAX_CHARS = 800_000

# ^-anchored transport-failure banners (an answer MENTIONING quota is fine).
# Not the sole fail-closed mechanism: `claude_cli_generate` only ever returns
# `out` when returncode == 0 AND out is non-empty, so any error exit already
# refuses regardless of whether it matches this regex.
_LANE_DOWN = re.compile(
    r"^(?:Error|error):|rate.?limit|quota|unauthorized|usage limit|"
    r"credit balance|log ?in required|not authenticated|"
    r"authentication failed|invalid api key|unrecognized_model|"
    r"issue with the selected model|please (?:run|log ?in)",
    re.I,
)

# CLI chrome that must never leak into a captured answer (fail, don't strip).
# Observed only on stderr in the production shape (--tools "" + scratch cwd
# emits zero stderr chrome); kept as a defensive stdout guard in case a
# future CLI version prints workspace-trust noise to stdout.
_CHROME = re.compile(
    r"^\s*(?:Ignoring \d+ permissions|Permission (?:deny|allow) rule|"
    r"this workspace has not been trusted)",
    re.I,
)


class ClaudeCliLaneError(RuntimeError):
    pass


def effective_timeout_s(prompt: str, timeout_s: int | None) -> int:
    if isinstance(timeout_s, int):
        return timeout_s
    scaled = _TIMEOUT_BASE_S + len(prompt) // _TIMEOUT_CHARS_PER_SECOND
    return max(_TIMEOUT_MIN_S, min(_TIMEOUT_MAX_S, scaled))


def _scratch_workspace() -> Path:
    root = Path(tempfile.gettempdir()) / "lme_claude_cli_lane"
    root.mkdir(parents=True, exist_ok=True)
    ws = root / f"ws_{os.getpid()}"
    ws.mkdir(exist_ok=True)
    return ws


def _resolve_claude_binary() -> str:
    binary = shutil.which("claude")
    if not binary:
        raise ClaudeCliLaneError(
            "claude cli not found on PATH — install/login the Claude CLI "
            "before selecting the claude-cli reader lane"
        )
    return binary


def claude_cli_generate(prompt: str, *, timeout_s: int | None = None,
                        max_attempts: int = 3, backoff_s: float = 2.0,
                        model: str = MODEL) -> str:
    """One read-only single-turn completion via the Claude CLI.

    `--tools ""` keeps this a pure text-completion call (no Bash/Read/Edit);
    the scratch cwd keeps it isolated from this repo's own CLAUDE.md.
    """
    if not prompt:
        raise ClaudeCliLaneError("claude cli lane: empty prompt")
    binary = _resolve_claude_binary()
    effective = effective_timeout_s(prompt, timeout_s)
    ws = _scratch_workspace()
    last = ""
    last_signature = None
    for attempt in range(1, max_attempts + 1):
        try:
            cmd = [binary, "-p"]
            stdin_bytes: bytes | None = None
            if len(prompt) <= _ARGV_PROMPT_MAX_CHARS:
                cmd += [prompt]
            else:
                # Verified fallback: `claude -p` with no positional prompt
                # reads the prompt from stdin.
                stdin_bytes = prompt.encode("utf-8")
            cmd += ["--model", model, "--output-format", "text",
                    "--tools", ""]
            proc = subprocess.run(
                cmd, input=stdin_bytes, capture_output=True,
                timeout=effective, cwd=str(ws))
            out = proc.stdout.decode("utf-8", errors="replace").strip()
            err = proc.stderr.decode("utf-8", errors="replace").strip()
            if (_LANE_DOWN.search(err)
                    or (proc.returncode != 0 and _LANE_DOWN.search(out))
                    or (out and _LANE_DOWN.match(out))):
                raise ClaudeCliLaneError(
                    f"claude cli lane down: {(err or out)[:160]!r}")
            if proc.returncode == 0 and out and not _CHROME.match(out):
                return out
            last = f"rc={proc.returncode} out={out[:120]!r} err={err[:120]!r}"
        except subprocess.TimeoutExpired:
            last = f"timeout after {effective}s"
        signature = last
        if signature == last_signature:
            # Identical failure twice: stop early rather than burn the
            # remaining attempt budget on a deterministic repeat.
            break
        last_signature = signature
        if attempt < max_attempts:
            time.sleep(backoff_s * attempt)
    raise ClaudeCliLaneError(f"claude cli lane exhausted: {last}")


if __name__ == "__main__":
    import sys
    print(claude_cli_generate(sys.stdin.read()))
