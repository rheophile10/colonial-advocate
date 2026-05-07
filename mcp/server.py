"""colonial-mcp server.

Importing `advocate` registers every `@mcp.tool()` against the shared
FastMCP instance, then `main()` runs it.

Run with:
    uv run --directory mcp python server.py
"""
from __future__ import annotations

from advocate import mcp  # noqa: F401  — import side-effect registers tools


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
