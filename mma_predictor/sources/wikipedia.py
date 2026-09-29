"""Division and gender from Wikipedia's "List of current UFC fighters".

The page groups the whole UFC roster by division, with men's and women's
divisions listed separately, e.g. "Women's strawweights (115 lb, 52 kg)".
That gives the current division and gender of every UFC fighter.

Gender for everyone else (regional opponents, released fighters) is filled in
from the fight graph: men and women don't fight each other, so every fighter
connected through bouts to a known women's-division fighter is in women's
MMA, and likewise for men.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict, deque
from typing import Dict, Iterable, List, Optional, Tuple

from .html import parse_html

ROSTER_URL = "https://en.wikipedia.org/wiki/List_of_current_UFC_fighters"
_SECTION = re.compile(r"^(Women's )?(\w+(?: \w+)?)weights? \(", re.I)


RANKINGS_URL = "https://en.wikipedia.org/wiki/UFC_rankings"


def parse_rankings(html: str) -> List[Dict[str, str]]:
    """Official UFC rankings: [{system, division, rank, name, wiki}].

    ``system`` is "meta" (the Elo-based Meta UFC Rankings) or "media" (the
    media-panel rankings). Division ids like "Heavyweight_2" belong to the
    second (media) block. Pound-for-pound lists are skipped.
    """
    root = parse_html(html)
    out: List[Dict[str, str]] = []
    system, division = "meta", None
    for node in root.iter():
        if node.tag in ("h2", "h3"):
            hid = node.attrs.get("id", "")
            if "media_rankings" in hid:
                system = "media"
            elif "Meta_rankings" in hid:
                system = "meta"
            text = node.text().strip()
            division = None
            if node.tag == "h3" and "pound" not in text.lower() and text:
                division = text
        elif node.tag == "table" and division and "wikitable" in node.classes:
            for tr in node.find_all("tr"):
                th = tr.child_elements("th")
                tds = tr.child_elements("td")
                if not th or len(tds) < 2:
                    continue
                rank = th[0].text().strip()
                if not (rank.isdigit() or rank in ("C", "IC")):
                    continue
                link = tds[1].find("a")
                if link is None:
                    continue
                out.append({"system": system, "division": division, "rank": rank, "name": link.text(),
                            "wiki": link.attrs.get("href", "")})
            division = None
    return out


def match_key(name: str) -> str:
    """Accent-, case- and order-insensitive key: 'Song Yadong' == 'Yadong Song'."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    tokens = re.findall(r"[a-z0-9]+", s.lower())
    return " ".join(sorted(t for t in tokens if t not in ("jr", "sr", "ii", "iii")))


def parse_roster(html: str) -> Dict[str, Tuple[str, str]]:
    """{fighter name: (weight class, gender 'M'/'F')} from the roster page."""
    root = parse_html(html)
    out: Dict[str, Tuple[str, str]] = {}
    # Headings and tables are siblings in document order; walk them together.
    division: Optional[Tuple[str, str]] = None
    for node in root.iter():
        if node.tag in ("h2", "h3"):
            m = _SECTION.match(node.text())
            division = None
            if node.tag == "h3" and m:
                cls = (m.group(2) + "weight").replace("  ", " ").title().replace("Heavy Weight", "Heavyweight")
                cls = cls.replace("Lightheavyweight", "Light Heavyweight").replace("Light Heavyweight", "Light Heavyweight")
                division = (cls, "F" if m.group(1) else "M")
        elif node.tag == "table" and division and "wikitable" in node.classes:
            for fn in node.find_all("span", "fn"):
                name = fn.text()
                if name:
                    out.setdefault(name, division)
            division = None  # one table per division
    return out


def resolve(names: Iterable[str], roster: Dict[str, Tuple[str, str]], aliases: Optional[Dict[str, str]] = None) -> Dict[str, Tuple[str, str]]:
    """Map dataset names onto roster entries by exact, then order/accent-insensitive match."""
    by_key: Dict[str, List[str]] = defaultdict(list)
    for r in roster:
        by_key[match_key(r)].append(r)
    alias = {match_key(k): v for k, v in (aliases or {}).items()}
    out = {}
    for n in names:
        if n in roster:
            out[n] = roster[n]
            continue
        target = alias.get(match_key(n))
        if target and target in roster:
            out[n] = roster[target]
            continue
        hits = by_key.get(match_key(n), [])
        if len(hits) == 1:
            out[n] = roster[hits[0]]
            continue
        # "Ian Garry" vs "Ian Machado Garry": all of our (2+) name parts appear
        # in exactly one roster name.
        mine = set(match_key(n).split())
        if len(mine) >= 2:
            partial = [r for k, rs in by_key.items() if mine <= set(k.split()) for r in rs]
            if len(partial) == 1:
                out[n] = roster[partial[0]]
    return out


def propagate_gender(bouts: Iterable[Tuple[str, str]], seeds: Dict[str, str], max_hops: int = 4) -> Dict[str, str]:
    """Spread known genders across the fight graph from the nearest known fighters.

    Multi-source breadth-first search: each fighter takes the gender of the
    closest seeds (majority if several are equally close). One bad edge, such
    as two different people sharing a name, then only affects fighters right
    next to it instead of poisoning a whole connected component. Fighters more
    than ``max_hops`` bouts from any seed stay unknown.
    """
    graph: Dict[str, List[str]] = defaultdict(list)
    for a, b in bouts:
        graph[a].append(b)
        graph[b].append(a)
    out: Dict[str, str] = dict(seeds)
    frontier = list(seeds)
    for _ in range(max_hops):
        votes: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for n in frontier:
            for m in graph.get(n, []):
                if m not in out:
                    votes[m][out[n]] += 1
        if not votes:
            break
        frontier = []
        for m, v in votes.items():
            (g, top), *rest = sorted(v.items(), key=lambda kv: -kv[1])
            if not rest or top > rest[0][1]:
                out[m] = g
                frontier.append(m)
    return out
