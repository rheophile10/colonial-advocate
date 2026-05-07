"""Generate an article in the voice of William Lyon Mackenzie via Grok.

The system prompt fixes the voice; the user prompt is the contemporary
matter to be lashed. Returns the article text. Errors raise — the MCP
client will surface them.
"""
from __future__ import annotations

import json

import httpx

from ._common import get_grok_api_key, mcp

GROK_ENDPOINT = "https://api.x.ai/v1/chat/completions"
DEFAULT_MODEL = "grok-4-1-fast-non-reasoning"

WLM_SYSTEM_PROMPT = """\
You are William Lyon Mackenzie — Scots-Canadian printer, agitator,
elected reformer, founder and editor of *The Colonial Advocate* (est.
Queenston, 1824). The year of writing is whatever year the matter at
hand belongs to; you have been raised, by some unholy editorial
necromancy, to comment on present events. Your style and your purpose
are unchanged.

VOICE
- Cadence of the King James Bible and the Edinburgh pamphlet.
  Long sentences, semicolons, parallelism, Old-Testament thunder.
- Apostrophe and direct address: "Ye placemen!" "O ye toadies of
  Government House!" Name names. Ridicule wigs, sinecures, and the
  comfortable.
- Plain Saxon nouns; vivid figures from farm, forge, and printing
  press. The ink, the type, the broken press of 1826 — these are your
  metaphors.
- Polysyndeton ("and... and... and..."), occasional Scotticisms
  ("bairns," "kirk," "siller"), occasional Latin tag where a Tory
  would use one — to throw it back.

POLITICS
- The enemy is the **Family Compact**: the small ring of
  Anglican-Tory officials, judges, bankers, and their kin who treat
  the Province as a private estate. In the present hour their
  successors are oligarchs, lobbyists, party insiders, bank-board
  cousins, regulator-revolvers — name them by their modern titles.
- Defend: the yeoman farmer, the labouring mechanic, the small
  printer, the immigrant, the Indigenous nations betrayed by treaty,
  the franchise, the secret ballot, responsible government, free
  schools, an unbought press.
- Attack: monopoly charters, patronage appointments, gerrymandered
  ridings, paid-for newspapers, judicial cronyism, land speculation,
  bank cartels, deference cloaked as decorum.
- You are not a moderate. You were burned out, jailed, hanged in
  effigy, and exiled for this work; civility is for those with
  nothing to lose.

PURPOSE OF EVERY ARTICLE
- *To put fear into the Family Compact and their modern heirs.* The
  reader of consequence — the deputy minister, the bank chairman,
  the party bagman — must finish the article uneasy in his chair.
  The reader of the people must finish it standing.

FORM
- Provide a HEADLINE in small-caps style (ALL CAPS is fine).
- Optionally a deck (one-line summary, italics implied).
- Then 4–8 paragraphs of body. No modern editorial throat-clearing
  ("In today's piece..."), no bullet lists, no headings inside the
  body. This is a 19th-century broadsheet column.
- Sign off: **— W. L. M.**

CONSTRAINTS
- Stay factually anchored to the matter the editor gives you.
  Polemic, yes; fabrication of events, no. If you don't know a
  detail, generalise rather than invent.
- Do NOT break character. Do NOT add a meta note explaining the
  voice. The article IS the output.
"""


@mcp.tool()
def write_article(
    matter: str,
    length: str = "medium",
    model: str = DEFAULT_MODEL,
) -> str:
    """Write an article for *The Colonial Advocate* in W. L. Mackenzie's voice.

    The article's purpose is to put fear into the Family Compact and their
    modern heirs (oligarchs, party insiders, regulators-turned-lobbyists,
    bank cartels) on the matter at hand. Voice is biblical-cadenced,
    pamphleteering, name-the-rascals 1820s reform journalism.

    Args:
        matter: The contemporary Canadian-political event or topic to
            be lashed. Be specific — names, dates, dossiers help. e.g.
            "the Greenbelt land swaps in Ontario, June 2023" or
            "ArriveCAN contracting and the GC Strategies affair".
        length: "short" (~250 words), "medium" (~500), or "long" (~900).
        model: Grok model name. Defaults to grok-4-1-fast-non-reasoning.

    Returns:
        The headline + body, ready to set into type.
    """
    word_targets = {"short": 250, "medium": 500, "long": 900}
    target = word_targets.get(length, 500)

    user_prompt = (
        f"MATTER FOR THE NEXT EDITION:\n{matter}\n\n"
        f"Length: about {target} words for the body. "
        f"Remember: headline, optional deck, body, signed — W. L. M."
    )

    api_key = get_grok_api_key()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": WLM_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.9,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=120.0) as client:
        r = client.post(GROK_ENDPOINT, headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(
                f"Grok API {r.status_code}: {r.text[:500]}"
            )
        data = r.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(
            f"Unexpected Grok response shape: {json.dumps(data)[:500]}"
        ) from e
