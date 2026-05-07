"""Direct call into the tool function — bypasses MCP transport.

    uv run python _smoketest.py            # editor-absent (Grok picks)
    uv run python _smoketest.py 'matter…'  # editor-driven
"""
from __future__ import annotations

import json
import sys

from advocate.grok_article import write_article

matter = sys.argv[1] if len(sys.argv) > 1 else None
print(json.dumps(write_article(matter=matter, length="short"), indent=2))
