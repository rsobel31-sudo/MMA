"""BestFightOdds (bestfightodds.com): betting lines and how they moved.

A fighter page lists every bout BestFightOdds tracked for them, with both
fighters' lines:

- the opening line,
- the closing range (worst and best price across the sportsbooks it follows),
- a sparkline of the average line over time (decimal odds), for the page's fighter.

Upcoming bouts appear too, with the current lines. BestFightOdds is itself an
aggregate of many sportsbooks, so its lines are a market consensus rather
than one book's opinion. robots.txt allows everything; keep the crawl polite.
"""

from __future__ import annotations

import html as htmllib
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional

BASE = "https://www.bestfightodds.com"


@dataclass
class Line:
    open: Optional[int]  # American odds
    close_lo: Optional[int]  # the two ends of the closing range as shown
    close_hi: Optional[int]


@dataclass
class OddsBout:
    date: date
    event: str
    event_url: str
    fighter: str
    fighter_url: str
    opponent: str
    opponent_url: str
    fighter_line: Line
    opponent_line: Line
    movement: List[float] = field(default_factory=list)  # fighter's average decimal odds over time


def _text(s: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def _american(raw: str) -> Optional[int]:
    raw = raw.strip()
    return int(raw) if re.fullmatch(r"[+-]?\d+", raw) else None


def _line(row: str) -> Line:
    vals = [_american(_text(m)) for m in re.findall(r'<td class="moneyline"[^>]*>(.*?)</td>', row, re.S)]
    vals += [None] * (3 - len(vals))
    return Line(*vals[:3])


def parse_fighter(page: str, url: str) -> List[OddsBout]:
    table = re.search(r'<table class="team-stats-table".*?</table>', page, re.S)
    if not table:
        return []
    rows = re.findall(r"<tr[^>]*>.*?</tr>", table.group(0), re.S)
    out: List[OddsBout] = []
    ev_name = ev_url = ""
    when: Optional[date] = None
    i = 0
    while i < len(rows):
        r = rows[i]
        if "event-header" in r:
            m = re.search(r'<a href="(/events/[^"]+)">(.*?)</a>\s*([A-Z][a-z]{2}) (\d+)\w\w (\d{4})', r, re.S)
            if m:
                ev_url, ev_name = BASE + m.group(1), _text(m.group(2))
                when = datetime.strptime(f"{m.group(3)} {m.group(4)} {m.group(5)}", "%b %d %Y").date()
            i += 1
            continue
        if 'class="main-row"' in r and i + 1 < len(rows) and when:
            me, them = rows[i], rows[i + 1]
            a = re.search(r'<th class="oppcell"><a href="(/fighters/[^"]+)">(.*?)</a>', me)
            b = re.search(r'<th class="oppcell"><a href="(/fighters/[^"]+)">(.*?)</a>', them)
            spark = re.search(r'data-sparkline="([^"]*)"', me)
            if a and b:
                out.append(OddsBout(
                    date=when, event=ev_name, event_url=ev_url,
                    fighter=_text(a.group(2)), fighter_url=BASE + a.group(1),
                    opponent=_text(b.group(2)), opponent_url=BASE + b.group(1),
                    fighter_line=_line(me), opponent_line=_line(them),
                    movement=[float(x) for x in spark.group(1).split(",") if x.strip()] if spark else [],
                ))
            i += 2
            continue
        i += 1
    return out


def search_url(name: str) -> str:
    return f"{BASE}/search?query={re.sub(r'[^A-Za-z0-9]+', '+', name).strip('+')}"


def search_results(page: str) -> List[tuple]:
    """(name, url) of fighters on a search results page, in the order shown."""
    return [(_text(n), BASE + u) for u, n in re.findall(r'href="(/fighters/[^"]+)"[^>]*>(.*?)</a>', page)]


# ------------------------------------------------------------------ odds maths
def implied(american: Optional[int]) -> Optional[float]:
    """Implied probability of American odds (vig included)."""
    if american is None or american == 0:
        return None
    return 100.0 / (american + 100.0) if american > 0 else -american / (-american + 100.0)


def fair_pair(a: Optional[int], b: Optional[int]) -> Optional[float]:
    """Fighter A's probability with the bookmaker margin removed (None if either side is missing)."""
    pa, pb = implied(a), implied(b)
    if pa is None or pb is None:
        return None
    return pa / (pa + pb)


def closing(line: Line) -> Optional[int]:
    """A single closing price: the middle of the closing range, in implied-probability terms."""
    ps = [implied(x) for x in (line.close_lo, line.close_hi) if x is not None]
    if not ps:
        return None
    p = sum(ps) / len(ps)
    return round(-100 * p / (1 - p)) if p >= 0.5 else round(100 * (1 - p) / p)
