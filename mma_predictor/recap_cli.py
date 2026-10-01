"""Card review helper for the Sunday routine.

    python -m mma_predictor recap-brief            # the latest recapped card
    python -m mma_predictor recap-brief --event "UFC 332"

Prints the card's recap (from app/data.json) and the document id the page uses for it:
the owner's notes live in recap_notes/<id>, Claude's review goes to recap_reviews/<id>.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def page_slug(s: str) -> str:
    """The page's slug(): lowercase, NFKD, non [a-z0-9] runs -> '-', trimmed, 120 chars (must match index.html)."""
    s = unicodedata.normalize("NFKD", str(s).lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:120] or "x"


def recap_id(ev: dict) -> str:
    return page_slug(f"{ev['date']} {ev['event']}")


def bout_key(b: dict) -> str:
    return page_slug(f"{b['a']}--{b['b']}")


def cmd_recap_brief(args) -> int:
    recaps = json.loads((ROOT / "app" / "data.json").read_text()).get("recaps") or {}
    events = recaps.get("events") or []
    ev = next((e for e in events if args.event.lower() in e["event"].lower()), None) if args.event else (events[0] if events else None)
    if not ev:
        print("No recapped card found.")
        return 1
    out = {"id": recap_id(ev), "event": ev["event"], "date": ev["date"], "summary": ev["summary"], "season": recaps.get("season"),
           "bouts": [dict(b, key=bout_key(b)) for b in ev["bouts"]]}
    print(json.dumps(out, indent=1))
    return 0


def register(sub) -> None:
    p = sub.add_parser("recap-brief", help="a card's recap and its page ids, for writing the review")
    p.add_argument("--event", default="")
    p.set_defaults(func=cmd_recap_brief)
