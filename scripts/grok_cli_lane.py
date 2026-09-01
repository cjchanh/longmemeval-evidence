#!/usr/bin/env python3
"""Grok CLI (Grok Build subscription) transport for the LME chain.

Single-turn headless mode: `grok --prompt-file <f>` prints the response to
stdout and exits. Used as the fallback vote lane for the self-consistency
pass when the Cursor lane is exhausted — same grok-4.6 model family,
different serving; every vote records its transport.

Fail-closed like the other lanes: transport errors raise, never return
error-shaped text as an answer.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

MODEL = os.environ.get("LME_GROK_CLI_MODEL", "grok-4.6")
EFFORT = os.environ.get("LME_GROK_CLI_EFFORT", "")  # xhigh|high|medium|low; "" = CLI default

_TIMEOUT_BASE_S = 240
_TIMEOUT_CHARS_PER_SECOND = 400
_TIMEOUT_MIN_S = 600  # xhigh paging over 40k-token packets needs headroom
_TIMEOUT_MAX_S = 900

# ^-anchored transport-failure banners (an answer MENTIONING quota is fine)
_LANE_DOWN = re.compile(
    r"^(?:Error|error):|rate.?limit|quota|unauthorized|credit|log ?in required",
    re.I,
)


class GrokCliLaneError(RuntimeError):
    pass


# CLI chrome that must never leak into a captured answer (fail, don't strip)
_CHROME = re.compile(r"^\s*(?:>\s|\[(?:boot|session)\]|ox-alpha ·)")


def effective_timeout_s(prompt: str, timeout_s: int | None) -> int:
    if isinstance(timeout_s, int):
        return timeout_s
    scaled = _TIMEOUT_BASE_S + len(prompt) // _TIMEOUT_CHARS_PER_SECOND
    return max(_TIMEOUT_MIN_S, min(_TIMEOUT_MAX_S, scaled))


def _scratch_workspace() -> Path:
    root = Path(tempfile.gettempdir()) / "lme_grok_cli_lane"
    root.mkdir(parents=True, exist_ok=True)
    ws = root / f"ws_{os.getpid()}"
    ws.mkdir(exist_ok=True)
    return ws


def grok_cli_generate(prompt: str, *, timeout_s: int | None = None,
                      max_attempts: int = 3, backoff_s: float = 2.0,
                      model: str = MODEL) -> str:
    """One read-only single-turn completion via the Grok CLI."""
    effective = effective_timeout_s(prompt, timeout_s)
    ws = _scratch_workspace()
    last = ""
    for attempt in range(1, max_attempts + 1):
        pf = ws / f"prompt_{os.getpid()}_{attempt}.txt"
        pf.write_text(prompt)
        try:
            # Pass the prompt as argv (-p): the CLI still offloads large
            # payloads, but the agent completes the read+answer within the
            # turn budget (verified rc=0 on a 137k-char packet at max-turns
            # 2). --prompt-file paging burned unbounded turns ("Max turns
            # reached" at 1 AND 4); argv is the working shape. Fallback to
            # --prompt-file only past ARG_MAX safety (800k chars).
            if len(prompt) <= 800_000:
                src = ["-p", prompt]
            else:
                src = ["--prompt-file", str(pf)]
            # max-turns 8: paging depth scales with packet length — 11/25
            # probe rows fit in 4 turns, the longest packets did not.
            cmd = ["grok", *src, "-m", model,
                   "--disable-web-search", "--no-plan", "--no-subagents",
                   "--max-turns", "8", "--cwd", str(ws)]
            if EFFORT:
                cmd += ["--reasoning-effort", EFFORT]
            proc = subprocess.run(
                cmd, capture_output=True, timeout=effective, cwd=str(ws))
            out = proc.stdout.decode("utf-8", errors="replace").strip()
            err = proc.stderr.decode("utf-8", errors="replace").strip()
            if (_LANE_DOWN.search(err)
                    or (proc.returncode != 0 and _LANE_DOWN.search(out))
                    or (out and _LANE_DOWN.match(out))):
                raise GrokCliLaneError(
                    f"grok cli lane down: {(err or out)[:160]!r}")
            if proc.returncode == 0 and out:
                return out
            last = f"rc={proc.returncode} out={out[:120]!r} err={err[:120]!r}"
        except subprocess.TimeoutExpired:
            last = f"timeout after {effective}s"
        finally:
            pf.unlink(missing_ok=True)
        time.sleep(backoff_s * attempt)
    raise GrokCliLaneError(f"grok cli lane exhausted {max_attempts}: {last}")


if __name__ == "__main__":
    import sys
    print(grok_cli_generate(sys.stdin.read()))
