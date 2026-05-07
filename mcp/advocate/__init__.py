"""colonial-mcp tool registry.

Importing this package registers every tool on the shared `mcp` instance.
"""
from __future__ import annotations

from ._common import mcp
from . import grok_article, publish  # noqa: F401  — registers tool decorators

__all__ = ["mcp"]
