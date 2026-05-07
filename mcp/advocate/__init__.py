"""colonial-mcp tool registry.

Importing this package registers every tool on the shared `mcp` instance.
"""
from __future__ import annotations

from ._common import mcp
from . import grok_article  # noqa: F401  — registers the tool decorator

__all__ = ["mcp"]
