"""Tapology fighter-page parser.

Tapology fighter pages (``https://www.tapology.com/fightcenter/fighters/<slug>``)
list each professional bout as a card element carrying a result attribute
(``data-result`` in older markup, ``data-status`` in newer markup) with the
opponent link, date, method, round and time inside it. Tapology's layout has
changed several times, so rather than binding to exact class names this
parser finds bout containers by those attributes and extracts fields by
pattern, which survives cosmetic redesigns.

Amateur bouts (``data-division="am"`` or inside an ``amResults`` section) are
skipped.
"""

from __future__ import annotations

import re
from typing import List, Optional

from .common import CareerBout, FighterPage, find_date, length_cm, method_from_text, normalise_result
from .html import Node, parse_html

BASE = "https://www.tapology.com"
_RESULT_ATTRS = ("data-result", "data-status")
_ROUND = re.compile(r"\bR(?:ound)?\s*(\d)\b", re.I)
_TIME = re.compile(r"\b(\d{1,2}:\d{2})\b")
_METHOD = re.compile(
    r"(KO/TKO|TKO|KO|Submission|Sub|(?:Unanimous|Split|Majority)?\s*Decision|Decision|Disqualification|DQ|No Contest|Draw)",
    re.I,
)


def fighter_url(slug: str) -> str:
    return slug if slug.startswith("http") else f"{BASE}/fightcenter/fighters/{slug.strip('/')}"


def parse_fighter(html: str, url: str) -> FighterPage:
    root = parse_html(html)
    page = FighterPage(url=url, name=_name(root))
    _bio(root, page)
    seen = set()
    for node in root.find_all(pred=_is_bout):
        if _is_amateur(node):
            continue
        bout = _parse_bout(node)
        if bout is None:
            continue
        key = (bout.date, bout.opponent)
        if key in seen:
            continue
        seen.add(key)
        page.bouts.append(bout)
    return page


def _name(root: Node) -> str:
    for pred in (
        lambda n: n.tag == "div" and "fighterUpcomingHeader" in n.classes,
        lambda n: n.tag == "h1",
    ):
        node = root.find(pred=pred)
        if node:
            h = node.find("h1") or node
            text = re.sub(r'"[^"]*"', "", h.text()).strip()
            if text:
                return " ".join(text.split())
    title = root.find("title")
    if title:
        return title.text().split("|")[0].split("(")[0].strip()
    raise ValueError("no fighter name found (not a Tapology fighter page?)")


def _bio(root: Node, page: FighterPage) -> None:
    text = root.text()
    m = re.search(r"Date of Birth:?", text)
    if m:
        page.dob = find_date(text[m.end() : m.end() + 40])
    m = re.search(r"Height:?\s*([^|]{1,40})", text)
    if m:
        page.height_cm = length_cm(m.group(1))
    m = re.search(r"Reach:?\s*([^|]{1,40})", text)
    if m:
        page.reach_cm = length_cm(m.group(1))
    m = re.search(r"\b(Orthodox|Southpaw|Switch)\b", text)
    if m:
        page.stance = m.group(1).title()


def _is_bout(n: Node) -> bool:
    return any(normalise_result(n.attrs.get(a, "")) for a in _RESULT_ATTRS) and n.find(
        "a", pred=lambda a: "/fightcenter/fighters/" in a.attrs.get("href", "")
    ) is not None


def _is_amateur(n: Node) -> bool:
    cur: Optional[Node] = n
    while cur is not None:
        div = cur.attrs.get("data-division", "").lower()
        if div.startswith("am"):
            return True
        if div == "pro":
            return False
        if "amResults" in cur.attrs.get("id", "") or "amateur" in cur.attrs.get("id", "").lower():
            return True
        cur = cur.parent
    return False


def _parse_bout(n: Node) -> Optional[CareerBout]:
    result = next(filter(None, (normalise_result(n.attrs.get(a, "")) for a in _RESULT_ATTRS)))
    link = n.find("a", pred=lambda a: "/fightcenter/fighters/" in a.attrs.get("href", ""))
    assert link is not None
    opponent = link.text()
    href = link.attrs["href"]
    text = n.text(" | ")
    when = find_date(text)
    if when is None or not opponent:
        return None
    mm = _METHOD.search(text)
    try:
        method = method_from_text(mm.group(1)) if mm else method_from_text("Decision")
    except ValueError:
        return None
    rnd = _ROUND.search(text)
    tm = _TIME.search(text)
    ev = n.find("a", pred=lambda a: "/fightcenter/events/" in a.attrs.get("href", ""))
    event = ev.text() if ev else ""
    scheduled = re.search(r"(\d)\s*x\s*5", text)
    return CareerBout(
        date=when,
        opponent=opponent,
        opponent_url=BASE + href if href.startswith("/") else href,
        result=result,
        method=method,
        round=int(rnd.group(1)) if rnd else 1,
        time=tm.group(1) if tm else "",
        event=event,
        method_detail=mm.group(1) if mm else "",
        scheduled_rounds=int(scheduled.group(1)) if scheduled else None,
        title_fight=bool(re.search(r"\btitle\b", text, re.I)),
    )
