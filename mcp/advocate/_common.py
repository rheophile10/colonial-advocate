"""Shared MCP instance + helpers.

The Grok API key is read from the sibling project's .env at startup —
the user keeps secrets in `../ccfr-site/.env` rather than duplicating
them per project. If that file is moved, set GROK_API_KEY in the
environment instead and it takes precedence.
"""
from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CCFR_ENV_PATH = PROJECT_ROOT.parent / "ccfr-site" / ".env"

mcp = FastMCP("colonial-advocate")


def _read_env_file(path: Path) -> dict[str, str]:
    vals: dict[str, str] = {}
    if not path.exists():
        return vals
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def get_grok_api_key() -> str:
    """Resolve the Grok key — env var first, then ../ccfr-site/.env."""
    if (k := os.environ.get("GROK_API_KEY")):
        return k
    vals = _read_env_file(CCFR_ENV_PATH)
    if (k := vals.get("GROK_API_KEY")):
        return k
    raise RuntimeError(
        f"GROK_API_KEY not found in environment or {CCFR_ENV_PATH}"
    )
