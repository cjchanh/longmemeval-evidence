#!/usr/bin/env python3
"""Reader lane selector for the LME packet reader.

The architecture's reader is a replaceable synthesis stage; this module is
the single seam that picks the transport + model, so the reader script
never hard-codes a provider. Selection is by environment so every run_meta
records exactly what answered:

    LME_READER_LANE = flash (default) | cursor-grok

flash       -> scripts/oc_flash_lane (GLM-5.3-Flash; LME_FLASH_MODEL picks transport)
cursor-grok -> scripts/cursor_grok_lane (Grok 4.6 via Cursor Ultra; LME_READER_MODEL)

Exports: LANE, MODEL, TRANSPORT, generate, LaneError. Unknown lane fails loudly.
"""
from __future__ import annotations

import os

LANE = os.environ.get("LME_READER_LANE", "flash")

if LANE == "flash":
    from oc_flash_lane import (  # noqa: F401
        MODEL,
        FlashLaneError as LaneError,
        _CONTAMINATION,
        flash_generate as generate,
    )
    TRANSPORT = "opencode run --pure (stdin), ThreadPoolExecutor"
elif LANE == "cursor-grok":
    from cursor_grok_lane import (  # noqa: F401
        MODEL,
        CursorLaneError as LaneError,
        _CHROME as _CONTAMINATION,
        grok_generate as generate,
    )
    TRANSPORT = "cursor-agent -p --mode ask (stdin, empty workspace), ThreadPoolExecutor"
elif LANE == "sol":
    from openai_sol_lane import (  # noqa: F401
        MODEL,
        SolLaneError as LaneError,
        _CHROME_LINE as _CONTAMINATION,
        sol_generate as generate,
    )
    TRANSPORT = "opencode run --pure openai oauth (stdin), ThreadPoolExecutor"
elif LANE == "grok-cli":
    from grok_cli_lane import (  # noqa: F401
        MODEL,
        EFFORT,
        GrokCliLaneError as LaneError,
        _CHROME as _CONTAMINATION,
        grok_cli_generate as generate,
    )
    TRANSPORT = f"grok --prompt-file (single-turn, effort={EFFORT or 'default'}), ThreadPoolExecutor"
elif LANE == "claude-cli":
    from claude_cli_lane import (  # noqa: F401
        MODEL,
        ClaudeCliLaneError as LaneError,
        _CHROME as _CONTAMINATION,
        claude_cli_generate as generate,
    )
    TRANSPORT = "claude -p --tools '' (single-turn, scratch cwd), ThreadPoolExecutor"
else:
    raise RuntimeError(
        f"LME_READER_LANE={LANE!r} unknown; expected 'flash', 'cursor-grok', "
        "'sol', 'grok-cli', or 'claude-cli'"
    )
