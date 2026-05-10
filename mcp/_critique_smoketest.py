"""Direct call into critique_article — bypasses MCP transport.

Reads a published article from articles.json by index (newest first
when idx=0) and prints the structured critique.

    uv run python _critique_smoketest.py            # critiques the lead piece
    uv run python _critique_smoketest.py 1          # second-most-recent
    uv run python _critique_smoketest.py 0 --fast   # skip fact-check
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from advocate.critique import critique_article

ARTICLES = Path(__file__).resolve().parent.parent / "web" / "public" / "articles.json"

idx = int(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else 0
fast = "--fast" in sys.argv

articles = json.loads(ARTICLES.read_text())
a = articles[idx]
print(f"Critiquing: {a['headline']}\n", file=sys.stderr)

result = critique_article(
    headline=a["headline"],
    deck=a.get("deck", ""),
    body=a["body"],
    fact_check=not fast,
)
print(json.dumps(result, indent=2, ensure_ascii=False))
