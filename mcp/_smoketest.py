"""Direct call into the tool function — bypasses the MCP transport.
Run: uv run python _smoketest.py
"""
from advocate.grok_article import write_article

matter = (
    "the federal government's backroom comfort with grocery oligopolies "
    "(Loblaws, Sobeys, Metro) while Canadian families pay record food prices "
    "and the Competition Bureau's report sits unactioned"
)
print(write_article(matter=matter, length="short"))
