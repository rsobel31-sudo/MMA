"""Fight Matrix (fightmatrix.com): computer rankings and point-in-time ratings.

Fight Matrix has no strike or takedown statistics. What it adds:

- Three independent rating systems per bout: a standard Elo (K-170), a
  modified Elo and Glicko-1. Every bout on a fighter's profile lists both
  fighters' ratings *before and after* that bout, so the ratings at any past
  date are known without look-ahead.
- Profile metrics: Combat Age (career mileage on a "dog years" scale),
  Quality Performance %, the 540-day opponent metric, 'Big League' record,
  UFC octagon time, and current divisional rankings.
- A link to the fighter's Sherdog page, so fighters match our Sherdog data
  exactly rather than by name.

robots.txt allows all crawling; keep the delay polite anyway.
"""

from __future__ import annotations

import html as htmllib
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote

BASE = "https://www.fightmatrix.com"
SYSTEMS = ("elo_k170", "elo_mod", "glicko")
RANK_PAGES = {
    "M": ["heavyweight-265-lbs", "light-heavyweight-185-205-lbs", "middleweight", "welterweight", "lightweight",
          "featherweight", "bantamweight", "flyweight"],
    "F": ["womens-featheweight", "womens-bantamweight", "womens-flyweight", "womens-strawweight"],
}


@dataclass
class FMBout:
    date: date
    opponent: str
    opponent_url: str
    result: str  # W / L / D / NC
    method: str
    end_round: Optional[int]
    event: str
    rank: str  # fighter's rank going in, e.g. "#4 LW" ('' if unranked)
    opp_rank: str
    # (before, after) for the fighter and the opponent, per rating system.
    ratings: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    opp_ratings: Dict[str, Tuple[int, int]] = field(default_factory=dict)


@dataclass
class FMProfile:
    name: str
    url: str
    sherdog_url: str = ""
    stats: Dict[str, str] = field(default_factory=dict)  # label -> value as shown
    rankings: List[str] = field(default_factory=list)  # e.g. "#1 Lightweight"
    bouts: List[FMBout] = field(default_factory=list)

    def number(self, label: str) -> Optional[float]:
        """A numeric profile stat ('66.7%' -> 0.667, '.727' -> 0.727, '45' -> 45)."""
        v = self.stats.get(label, "").strip()
        m = re.match(r"^(-?\d*\.?\d+)(%?)$", v)
        if not m:
            return None
        x = float(m.group(1))
        return x / 100.0 if m.group(2) else x


def _text(s: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def profile_url(name: str, fm_id: str) -> str:
    return f"{BASE}/fighter-profile/{name.replace(' ', '%20')}/{fm_id}/"


def parse_profile(page: str, url: str) -> FMProfile:
    h1 = re.search(r'<h1 class="entry-title"[^>]*>(.*?)</h1>', page, re.S)
    name = _text(h1.group(1)) if h1 else unquote(url.rstrip("/").split("/")[-2])
    prof = FMProfile(name=name, url=url)
    sd = re.search(r"href='(https?://www\.sherdog\.com/fighter/[^' ]+)", page)
    if sd:
        prof.sherdog_url = sd.group(1).replace("http://", "https://").strip()
    # "Label: <strong>value</strong>" pairs in the header tables.
    head = page[: page.find("Complete Professional MMA Fight History")] if "Complete Professional" in page else page
    for label, value in re.findall(r">\s*([A-Z0-9'][A-Za-z0-9 '.%]+?):\s*(?:&nbsp;)?\s*<strong>(.*?)</strong>", head, re.S):
        prof.stats.setdefault(_text(label), _text(value))
    for label, value in re.findall(r"class='sherLink'>([^<]+?):</a>\s*<strong>(.*?)</strong>", head, re.S):
        prof.stats.setdefault(_text(label), _text(value))
    prof.rankings = [_text(x) for x in re.findall(r"class='redLink'[^>]*>(#\d+[^<]+)</a>", head)]

    # One chunk per bout, starting at its tooltip (both fighters' ratings);
    # result, opponent, method, event and date follow.
    hist = page[page.find("Complete Professional MMA Fight History"):] if "Complete Professional" in page else page
    for chunk in re.split(r"<tr onmouseover=\"LoadCustomData\('stat','", hist)[1:]:
        tip = _text(chunk.split("');", 1)[0]).split("|")
        if len(tip) < 18:
            continue
        nums = [int(x) if x.strip().lstrip("-").isdigit() else None for x in tip[6:18]]
        ratings, opp = {}, {}
        for k, sysname in enumerate(SYSTEMS):
            a0, a1, b0, b1 = nums[4 * k: 4 * k + 4]
            if None not in (a0, a1):
                ratings[sysname] = (a0, a1)
            if None not in (b0, b1):
                opp[sysname] = (b0, b1)
        res = re.search(r"<b style='color: black'>([A-Z]+)</b>", chunk)
        opp_a = re.search(r"href='(/fighter-profile/[^']+)'[^>]*>(.*?)</a>", chunk)
        cells = [c for c in re.findall(r"<td class=\"tdRank[^\"]*\"[^>]*>(.*?)</td>", chunk, re.S)
                 if "/event/" not in c and "/fighter-profile/" not in c and "<b style=" not in c]
        method_cell = _text(cells[-1]) if cells else ""
        rnd = re.search(r"Round (\d+)", method_cell)
        ev = re.search(r"<a href='/event/[^']*'[^>]*>(.*?)</a>", chunk, re.S)
        when = re.search(r"<em>\w+day, (\w+) (\d+)\w\w (\d{4})</em>", chunk)
        if not (res and opp_a and when):
            continue
        d = datetime.strptime(f"{when.group(1)} {when.group(2)} {when.group(3)}", "%B %d %Y").date()
        prof.bouts.append(FMBout(
            date=d, opponent=_text(opp_a.group(2)), opponent_url=BASE + opp_a.group(1), result=res.group(1),
            method=re.sub(r"\s*Round \d+\s*$", "", method_cell).strip(), end_round=int(rnd.group(1)) if rnd else None,
            event=_text(ev.group(1)) if ev else "", rank=tip[2].strip(), opp_rank=tip[3].strip(),
            ratings=ratings, opp_ratings=opp))
    return prof


def parse_rankings(page: str) -> List[Tuple[int, str, str, int]]:
    """(rank, name, profile URL, rating points) from a divisional ranking page."""
    out = []
    for m in re.finditer(r'class="tdRank(?:Alt)?">(\d+)</td>.*?href="(/fighter-profile/[^"]+)"[^>]*>\s*<strong>(.*?)</strong>'
                         r'.*?<div class="tdBar"[^>]*>(\d+)</div>', page, re.S):
        out.append((int(m.group(1)), _text(m.group(3)), BASE + m.group(2), int(m.group(4))))
    return out


def rankings_url(slug: str, page: int = 1) -> str:
    return f"{BASE}/mma-ranks/{slug}/" + (f"?PageNum={page}" if page > 1 else "")
