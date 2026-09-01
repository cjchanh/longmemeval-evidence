#!/usr/bin/env python3
"""OpenCode glm-5.3-flash transport for the LME chain.

Ollama Cloud hit its weekly quota (429, account-wide) mid-campaign; the
OpenCode `ox-alpha` lane (opencode-go/glm-5.3-flash) is quota-independent.
This module pipes a prompt to `opencode run --pure -m opencode-go/glm-5.3-flash`
via stdin and returns the cleaned response text. Used by the flash reader run
and the flash judge pass so the chain stays self-consistent on one lane.
"""
from __future__ import annotations

import os
import re
import subprocess
import time

# Same model, transport-selectable: the ruler is GLM-5.3-Flash, not the
# provider. LME_FLASH_MODEL overrides the lane (e.g. ollama-cloud/glm-5.3-flash
# when the opencode-go workspace is unfunded); the value is recorded in every
# run_meta so the transport is never silent.
_DEFAULT_MODEL = "opencode-go/glm-5.3-flash"
MODEL = os.environ.get("LME_FLASH_MODEL", _DEFAULT_MODEL)
# The glm pin protected the GLM-5.3-Flash *judge* ruler from silent drift.
# GLM retired as judge 2026-08-31 (GPT-4o api is the ruler); the lane now
# also serves as a generic opencode READER transport. Non-glm models must be
# doubly explicit: env model + LME_FLASH_MODEL_UNPINNED=1, else fail closed.
if not MODEL.endswith("/glm-5.3-flash") and os.environ.get(
        "LME_FLASH_MODEL_UNPINNED") != "1":
    raise RuntimeError(
        f"LME_FLASH_MODEL={MODEL!r} is not a glm-5.3-flash lane; the ruler is "
        "pinned (set LME_FLASH_MODEL_UNPINNED=1 for an explicit reader-role "
        "override)"
    )
_ANSI = re.compile(r"\x1b\[[0-9;]*m")

# Wrapper chrome the opencode CLI writes onto stdout alongside the model's
# text. Missing one of these silently CONTAMINATES the captured answer: a
# 2026-08-28 audit found 20/500 flash reader rows whose response began
# "OUT: 0" because only the "> " banner was stripped. Strip what we know,
# then FAIL on anything that still looks like chrome rather than passing it
# downstream — silent stripping is how the first leak went unnoticed.
_CHROME_LINE = re.compile(r"^(?:>\s|OUT:\s*\d+\s*$|\[[a-z]+\]\s)")
_CONTAMINATION = re.compile(r"^\s*(?:OUT:\s*\d+|>\s|\[(?:boot|fleet)\])")


class FlashLaneError(RuntimeError):
    pass


class FlashLaneContamination(FlashLaneError):
    """Response still carries wrapper chrome after stripping — fail closed."""


# Flat timeout_s=240 was the root cause of a 2026-08-30 replay failure class:
# 38/44 dense-chain-closure packets sit near the 40k-proxy-token budget
# (~160k chars) and exhausted all 4 retry attempts at a flat 240s each —
# the timeout never grew with the packet, so near-budget packets were
# structurally unable to finish. Scale the timeout with prompt size instead
# of leaving it flat; an explicit caller-supplied timeout_s is still honored
# unchanged (rescore/AB callers that need a fixed short timeout).
_TIMEOUT_BASE_S = 240
_TIMEOUT_MIN_S = 240
_TIMEOUT_MAX_S = 720
_TIMEOUT_CHARS_PER_SECOND = 400


def effective_timeout_s(prompt: str, timeout_s: int | None) -> int:
    """Resolve the timeout to use for one flash_generate call.

    An explicit int timeout_s is honored unchanged. Otherwise the timeout
    scales with prompt length: base 240s + 1s per 400 chars, clamped to
    [240, 720]s.
    """
    if isinstance(timeout_s, int):
        return timeout_s
    scaled = _TIMEOUT_BASE_S + len(prompt) // _TIMEOUT_CHARS_PER_SECOND
    return max(_TIMEOUT_MIN_S, min(_TIMEOUT_MAX_S, scaled))


def flash_generate(prompt: str, *, timeout_s: int | None = None,
                   max_attempts: int = 4, backoff_s: float = 2.0,
                   model: str = MODEL) -> str:
    """One completion through the opencode lane. Retries transients."""
    effective = effective_timeout_s(prompt, timeout_s)
    last = ""
    for attempt in range(1, max_attempts + 1):
        try:
            proc = subprocess.run(
                ["opencode", "run", "--pure", "-m", model],
                input=prompt.encode("utf-8"),
                capture_output=True, timeout=effective)
            out = _ANSI.sub("", proc.stdout.decode("utf-8", errors="replace"))
            lines = [l for l in out.splitlines()
                     if not _CHROME_LINE.match(l.strip())]
            text = "\n".join(lines).strip()
            if proc.returncode == 0 and text:
                if _CONTAMINATION.match(text):
                    raise FlashLaneContamination(
                        f"wrapper chrome survived stripping: {text[:80]!r}")
                return text
            last = f"rc={proc.returncode} out={text[:120]!r} err={proc.stderr.decode(errors='replace')[:120]!r}"
        except subprocess.TimeoutExpired:
            last = f"timeout after {effective}s"
        time.sleep(backoff_s * attempt)
    raise FlashLaneError(f"flash lane exhausted {max_attempts}: {last}")
