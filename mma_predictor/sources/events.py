"""Upcoming UFC cards from Wikipedia.

"List of UFC events" has a Scheduled events table linking to each event's
article, and each article has a Fight card table:

    Weight class | Fighter A (c) | vs. | Fighter B | Method | Round | Time | Notes

with segment header rows ("Main card", "Preliminary card"). The first bout on
the card is the main event; it and any title fight are five rounds.
"""

from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional
from urllib.parse import urljoin

from ..data import parse_date
from .common import Fetcher
from .html import Node, parse_html
from .wikipedia import match_key

EVENTS_URL = "https://en.wikipedia.org/wiki/List_of_UFC_events"
_TITLE = re.compile(r"\((c|ic)\)", re.I)


def scheduled_events(html: str) -> List[Dict[str, str]]:
    root = parse_html(html)
    heading = root.find(pred=lambda n: n.attrs.get("id") == "Scheduled_events")
    tables = root.find_all("table", "wikitable")
    if heading is None or not tables:
        return []
    out = []
    for tr in tables[0].find_all("tr")[1:]:
        cells = tr.child_elements()
        if len(cells) < 2:
            continue
        link = cells[0].find("a")
        try:
            when = parse_date(cells[1].text())
        except ValueError:
            continue
        out.append({
            "name": cells[0].text(),
            "date": when.isoformat(),
            "venue": cells[2].text() if len(cells) > 2 else "",
            "location": re.sub(r"\s+,", ",", cells[3].text()) if len(cells) > 3 else "",
            "url": urljoin(EVENTS_URL, link.attrs["href"]) if link is not None else "",
        })
    return sorted(out, key=lambda e: e["date"])


def _clean(name: str) -> str:
    return re.sub(r"\s+", " ", _TITLE.sub("", name)).strip()


def parse_card(html: str) -> List[Dict[str, object]]:
    """Bouts in card order: weight class, fighters, segment, title, rounds."""
    root = parse_html(html)
    bouts: List[Dict[str, object]] = []
    for table in root.find_all("table", "toccolours"):
        segment = ""
        for tr in table.find_all("tr"):
            cells = tr.child_elements()
            if len(cells) == 1 or (cells and all(c.tag == "th" for c in cells) and len(cells) <= 2):
                label = tr.text().strip()
                if label and "weight class" not in label.lower():
                    segment = label.split("(")[0].strip()
                continue
            if len(cells) < 4 or cells[2].text().strip().lower() not in ("vs.", "vs", "def.", "def"):
                continue
            a_raw, b_raw = cells[1].text(), cells[3].text()
            title = bool(_TITLE.search(a_raw) or _TITLE.search(b_raw))
            bouts.append({
                "order": len(bouts),
                "segment": segment,
                "weight_class": cells[0].text().strip(),
                "a": _clean(a_raw),
                "b": _clean(b_raw),
                "title": title,
                "result": cells[4].text().strip() if len(cells) > 4 else "",
            })
    # Bouts announced but not yet slotted into the card are a bulleted list:
    # "Bantamweight bout: Malcolm Wellmaker vs. Otari Tanzilovi [6]".
    seen = {frozenset((match_key(str(b["a"])), match_key(str(b["b"])))) for b in bouts}
    announced: List[Node] = []
    inside = False
    for node in root.iter():
        if node.tag in ("h2", "h3"):
            inside = node.attrs.get("id") == "Announced_bouts"
        elif inside and node.tag == "li":
            announced.append(node)
    if announced:
        for li in announced:
            m = re.match(r"(.+?) bout:\s*(.+?)\s+vs\.?\s+(.+?)(?:\s*\[\s*\d+\s*\])*\s*$", li.text())
            if not m:
                continue
            a, b = _clean(m.group(2)), _clean(m.group(3))
            key = frozenset((match_key(a), match_key(b)))
            if key in seen:
                continue
            seen.add(key)
            bouts.append({"order": len(bouts), "segment": "Announced", "weight_class": m.group(1).strip(),
                          "a": a, "b": b, "title": bool(_TITLE.search(m.group(0))), "result": ""})
    for b in bouts:
        b["rounds"] = 5 if b["order"] == 0 or b["title"] else 3
        b["main_event"] = b["order"] == 0
    return bouts


def upcoming_cards(fetcher: Fetcher, limit: int = 8, log: Callable[[str], None] = print) -> List[Dict[str, object]]:
    events = scheduled_events(fetcher.get(EVENTS_URL))[:limit]
    for e in events:
        if not e["url"]:
            e["bouts"] = []
            continue
        try:
            e["bouts"] = parse_card(fetcher.get(e["url"]))
        except (OSError, ValueError) as exc:
            log(f"  {e['name']}: {exc}")
            e["bouts"] = []
        log(f"  {e['date']} {e['name']}: {len(e['bouts'])} bouts")
    return events


def link_names(names, dataset_names, aliases: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Map card names onto dataset names (aliases, then accent/order-insensitive, then unique partial)."""
    by_key: Dict[str, List[str]] = {}
    for n in dataset_names:
        by_key.setdefault(match_key(n), []).append(n)
    alias = {match_key(k): v for k, v in (aliases or {}).items() if not k.startswith("_")}
    out = {}
    for n in names:
        target = alias.get(match_key(n))
        if target and target in dataset_names:
            out[n] = target
            continue
        hits = by_key.get(match_key(n), [])
        if len(hits) == 1:
            out[n] = hits[0]
            continue
        mine = set(match_key(n).split())
        if len(mine) >= 2:
            # Both directions ("Ian Garry" in "Ian Machado Garry" and back), but only
            # with two distinct name parts, so "Francisco Francisco" can't match
            # every Francisco.
            partial = [d for k, ds in by_key.items()
                       if len(set(k.split())) >= 2 and (mine <= set(k.split()) or set(k.split()) <= mine) for d in ds]
            if len(set(partial)) == 1:
                out[n] = partial[0]
    return out
