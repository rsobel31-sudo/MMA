"""Sherdog fighter-page parser.

Sherdog fighter pages (``https://www.sherdog.com/fighter/<Name>-<id>``) list
professional bouts in a ``fight_history`` module as a table with columns
Result | Fighter | Event (+date) | Method (+referee) | Round | Time.
Amateur records live in a separate module and are skipped.

Site markup changes over time; if parsing breaks, update the selectors here
and the fixture in ``tests/fixtures``.
"""

from __future__ import annotations

import re
from datetime import date
from typing import List, Optional

from .common import CareerBout, Fetcher, FighterPage, find_date, length_cm, method_from_text, normalise_result
from .html import Node, parse_html

BASE = "https://www.sherdog.com"


def fighter_url(slug: str) -> str:
    """'Israel-Adesanya-56374' or a full URL -> full URL."""
    return slug if slug.startswith("http") else f"{BASE}/fighter/{slug.strip('/')}"


def parse_fighter(html: str, url: str) -> FighterPage:
    root = parse_html(html)
    name_node = root.find("span", "fn") or root.find(pred=lambda n: n.attrs.get("itemprop") == "name")
    if name_node is None:
        raise ValueError("no fighter name found (not a Sherdog fighter page?)")
    page = FighterPage(url=url, name=name_node.text())
    nick = root.find("span", "nickname")
    if nick:
        page.nickname = nick.text().strip('"')

    bd = root.find(pred=lambda n: n.attrs.get("itemprop") == "birthDate")
    if bd:
        page.dob = find_date(bd.attrs.get("content", "") or bd.text())
    h = root.find(pred=lambda n: n.attrs.get("itemprop") == "height")
    if h:
        # The cm figure usually sits next to the feet/inches figure.
        page.height_cm = length_cm((h.parent.text() if h.parent else "") or h.text())

    for module in root.find_all(pred=lambda n: "fight_history" in n.classes):
        heading = (module.find(pred=lambda n: n.tag in ("h2", "div") and "slanted_title" in n.classes) or module)
        if "amateur" in heading.text()[:80].lower():
            continue
        for table in module.find_all("table"):
            page.bouts.extend(_parse_table(table))
        if page.bouts:
            break  # first professional module is the record
    return page


def _parse_table(table: Node) -> List[CareerBout]:
    bouts: List[CareerBout] = []
    for tr in table.find_all("tr"):
        if "table_head" in tr.classes:
            continue
        tds = tr.child_elements("td")
        if len(tds) < 6:
            continue
        bout = _parse_row(tds)
        if bout:
            bouts.append(bout)
    return bouts


def _parse_row(tds: List[Node]) -> Optional[CareerBout]:
    result = normalise_result(tds[0].text())
    if result is None:
        return None  # header row or upcoming bout
    link = tds[1].find("a")
    opponent = (link.text() if link else tds[1].text()).strip()
    opp_url = link.attrs.get("href") if link else None
    event_link = tds[2].find("a")
    event = event_link.text() if event_link else ""
    when = find_date(tds[2].text())
    if when is None or not opponent:
        return None
    method_node = tds[3].find("b")
    method_text = method_node.text() if method_node else tds[3].text()
    try:
        method = method_from_text(method_text)
    except ValueError:
        return None
    rnd = re.search(r"\d+", tds[4].text())
    return CareerBout(
        date=when,
        opponent=opponent,
        opponent_url=(BASE + opp_url) if opp_url and opp_url.startswith("/") else opp_url,
        result=result,
        method=method,
        round=int(rnd.group()) if rnd else 1,
        time=tds[5].text().strip(),
        event=event,
        method_detail=method_text,
        title_fight="title" in event.lower(),
    )


UFC_ORG = BASE + "/organizations/Ultimate-Fighting-Championship-UFC-2"


def recent_event_fighters(fetcher: Fetcher, events: int = 40, org_url: str = UFC_ORG, log=print) -> List[str]:
    """Fighter URLs from an organisation's most recent completed events."""
    today = date.today()
    event_urls: List[str] = []
    page = 1
    while len(event_urls) < events and page <= 20:
        url = org_url if page == 1 else f"{org_url}/recent-events/{page}"
        root = parse_html(fetcher.get(url))
        found = 0
        for tr in root.find_all("tr"):
            link = tr.find("a", pred=lambda a: a.attrs.get("href", "").startswith("/events/"))
            when = find_date(tr.text()) if link else None
            if link is None or when is None or when >= today:
                continue  # upcoming events have no results yet
            href = BASE + link.attrs["href"]
            if href not in event_urls:
                event_urls.append(href)
                found += 1
        if not found:
            break
        page += 1
    fighters: List[str] = []
    for ev in event_urls[:events]:
        root = parse_html(fetcher.get(ev))
        for a in root.find_all("a", pred=lambda a: a.attrs.get("href", "").startswith("/fighter/")):
            href = BASE + a.attrs["href"]
            if href not in fighters:
                fighters.append(href)
        log(f"  event {ev.rsplit('/', 1)[-1]}: {len(fighters)} fighters so far")
    return fighters
