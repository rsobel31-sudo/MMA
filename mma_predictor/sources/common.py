"""Shared crawling and conversion logic for record-site importers."""

from __future__ import annotations

import csv
import hashlib
import re
import time
import urllib.error
import urllib.request
import urllib.robotparser
from collections import deque
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from ..data import Method, fight_csv_header, normalise_name, parse_date, parse_method

USER_AGENT = "mma-predictor/0.1 (personal research; respects robots.txt)"


@dataclass
class CareerBout:
    """One bout as listed on a fighter's record page (their perspective)."""

    date: date
    opponent: str
    opponent_url: Optional[str]
    result: str  # "win" | "loss" | "draw" | "nc"
    method: Method
    round: int
    time: str
    event: str = ""
    method_detail: str = ""
    scheduled_rounds: Optional[int] = None
    title_fight: bool = False


@dataclass
class FighterPage:
    url: str
    name: str
    dob: Optional[date] = None
    height_cm: Optional[float] = None
    reach_cm: Optional[float] = None
    stance: Optional[str] = None
    nickname: str = ""
    weight_class: str = ""
    nationality: str = ""
    team: str = ""
    bouts: List[CareerBout] = field(default_factory=list)


class Fetcher:
    """Polite HTTP GET: robots.txt, per-host delay, on-disk cache."""

    def __init__(self, cache_dir: Path, delay: float = 3.0, user_agent: str = USER_AGENT, respect_robots: bool = True) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.user_agent = user_agent
        self.respect_robots = respect_robots
        self._robots: Dict[str, urllib.robotparser.RobotFileParser] = {}
        self._last: Dict[str, float] = {}

    def _cache_path(self, url: str) -> Path:
        return self.cache_dir / (hashlib.sha1(url.encode()).hexdigest() + ".html")

    def allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        host = urlparse(url)
        base = f"{host.scheme}://{host.netloc}"
        if base not in self._robots:
            rp = urllib.robotparser.RobotFileParser(base + "/robots.txt")
            try:
                rp.read()
            except (urllib.error.URLError, OSError):
                rp = None  # type: ignore[assignment]
            self._robots[base] = rp  # type: ignore[assignment]
        rp = self._robots[base]
        return True if rp is None else rp.can_fetch(self.user_agent, url)

    def get(self, url: str) -> str:
        path = self._cache_path(url)
        if path.exists():
            return path.read_text(encoding="utf-8")
        if not self.allowed(url):
            raise PermissionError(f"robots.txt disallows {url}")
        host = urlparse(url).netloc
        wait = self.delay - (time.monotonic() - self._last.get(host, 0.0))
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent, "Accept-Language": "en"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="replace")
        self._last[host] = time.monotonic()
        path.write_text(html, encoding="utf-8")
        return html


# ------------------------------------------------------------------ parsing helpers
_DATE_PATTERNS = [
    (re.compile(r"\b(\d{4})[.\-/](\d{2})[.\-/](\d{2})\b"), lambda m: date(int(m[1]), int(m[2]), int(m[3]))),
    (re.compile(r"\b([A-Z][a-z]{2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})\b"), lambda m: parse_date(f"{m[1]} {int(m[2]):02d}, {m[3]}")),
    (re.compile(r"\b(\d{4})\s+([A-Z][a-z]{2})\s+(\d{1,2})\b"), lambda m: parse_date(f"{m[2]} {int(m[3]):02d}, {m[1]}")),
    (re.compile(r"\b([A-Z][a-z]+\.?)\s+(\d{1,2}),?\s+(\d{4})\b"), lambda m: parse_date(f"{m[1].rstrip('.')[:3]} {int(m[2]):02d}, {m[3]}")),
]


def find_date(text: str) -> Optional[date]:
    for rx, conv in _DATE_PATTERNS:
        for m in rx.finditer(text):
            try:
                return conv(m)
            except ValueError:
                continue
    return None


def normalise_result(raw: str) -> Optional[str]:
    s = raw.strip().lower()
    if s in ("w", "win", "won"):
        return "win"
    if s in ("l", "loss", "lost"):
        return "loss"
    if s in ("d", "draw"):
        return "draw"
    if s in ("nc", "no contest", "n/c"):
        return "nc"
    return None


def method_from_text(raw: str) -> Method:
    s = raw.strip()
    upper = s.upper()
    if re.search(r"\bTKO\b|\bKO\b|KO/TKO|DOCTOR|CORNER|RETIREMENT", upper):
        return Method.KO
    if "SUBMISSION" in upper or re.search(r"\bSUB\b", upper):
        return Method.SUB
    return parse_method(s)


_CM = re.compile(r"(\d{2,3}(?:\.\d+)?)\s*cm", re.I)
_FEET = re.compile(r"(\d)\s*'\s*(\d{1,2}(?:\.\d+)?)\s*\"?")
_INCHES = re.compile(r"(\d{2,3}(?:\.\d+)?)\s*(?:\"|in\b|inches)", re.I)


def length_cm(text: str) -> Optional[float]:
    m = _CM.search(text)
    if m:
        return float(m[1])
    m = _FEET.search(text)
    if m:
        return round((int(m[1]) * 12 + float(m[2])) * 2.54, 1)
    m = _INCHES.search(text)
    if m:
        return round(float(m[1]) * 2.54, 1)
    return None


# ------------------------------------------------------------------ crawl
ParseFn = Callable[[str, str], FighterPage]


def crawl(
    seeds: Iterable[str],
    fetcher: Fetcher,
    parse: ParseFn,
    depth: int = 1,
    max_fighters: int = 500,
    log: Callable[[str], None] = print,
) -> List[FighterPage]:
    """Breadth-first crawl from seed fighter URLs through their opponents."""
    queue = deque((url, 0) for url in seeds)
    seen: Set[str] = set()
    pages: List[FighterPage] = []
    while queue and len(pages) < max_fighters:
        url, d = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        try:
            page = parse(fetcher.get(url), url)
        except (urllib.error.URLError, OSError, PermissionError, ValueError) as exc:
            log(f"  skip {url}: {exc}")
            continue
        pages.append(page)
        log(f"  [{len(pages)}] {page.name}: {len(page.bouts)} bouts")
        if d < depth:
            for b in page.bouts:
                if b.opponent_url and b.opponent_url not in seen:
                    queue.append((urljoin(url, b.opponent_url), d + 1))
    return pages


# ------------------------------------------------------------------ conversion
def pages_to_rows(pages: List[FighterPage], source: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Merge per-fighter records into de-duplicated fighter and fight rows.

    A bout appears on both fighters' pages when both were crawled; it's keyed
    on (date, both names) so it's only written once.
    """
    fighters: Dict[str, Dict[str, str]] = {}
    url_to_name: Dict[str, str] = {}
    for p in pages:
        url_to_name[p.url] = p.name
        fighters[p.name] = {
            "name": p.name,
            "dob": p.dob.isoformat() if p.dob else "",
            "height_cm": f"{p.height_cm:.1f}" if p.height_cm else "",
            "reach_cm": f"{p.reach_cm:.1f}" if p.reach_cm else "",
            "stance": p.stance or "",
            "weight_class": p.weight_class,
            "nationality": p.nationality,
            "team": p.team,
            "prior_wins": "0",
            "prior_losses": "0",
            "source": source,
            "url": p.url,
        }
    fights: Dict[tuple, Dict[str, str]] = {}
    for p in pages:
        for b in p.bouts:
            opp = url_to_name.get(b.opponent_url or "", b.opponent)
            fighters.setdefault(opp, {"name": opp, "dob": "", "height_cm": "", "reach_cm": "", "stance": "",
                                      "prior_wins": "0", "prior_losses": "0", "source": source, "url": b.opponent_url or ""})
            key = (b.date, frozenset((normalise_name(p.name), normalise_name(opp))))
            if key in fights:
                continue
            if b.result == "win":
                winner = p.name
            elif b.result == "loss":
                winner = opp
            else:
                winner = b.result
            method = Method.DRAW if b.result == "draw" else Method.NC if b.result == "nc" else b.method
            fights[key] = {
                "date": b.date.isoformat(),
                "event": b.event,
                "weight_class": "",
                "fighter_a": p.name,
                "fighter_b": opp,
                "winner": winner,
                "method": method.value,
                "round": str(b.round),
                "time": b.time,
                "scheduled_rounds": str(infer_scheduled_rounds(b, p.name, opp)),
                "title_fight": "1" if b.title_fight else "0",
            }
    return list(fighters.values()), sorted(fights.values(), key=lambda r: r["date"])


def infer_scheduled_rounds(b: CareerBout, name: str, opponent: str) -> int:
    """Record sites rarely state the scheduled length, so infer it.

    Past round 3 means five rounds. Title fights are five. UFC main events
    (the event is named after both fighters, "X vs. Y") have been five rounds
    since late 2011.
    """
    if b.scheduled_rounds:
        return b.scheduled_rounds
    if b.round > 3 or b.title_fight:
        return 5
    event = b.event.lower()
    surnames = [n.split()[-1].lower() for n in (name, opponent) if n.split()]
    if event.startswith("ufc") and b.date.year >= 2012 and all(s in event for s in surnames):
        return 5
    return 3


FIGHTER_HEADER = ["name", "dob", "height_cm", "reach_cm", "stance", "weight_class", "nationality", "team",
                  "prior_wins", "prior_losses", "source", "url"]


def write_dataset(out_dir: Path, fighters: List[Dict[str, str]], fights: List[Dict[str, str]]) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "fighters.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIGHTER_HEADER, extrasaction="ignore")
        w.writeheader()
        w.writerows(fighters)
    with open(out_dir / "fights.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fight_csv_header(), extrasaction="ignore")
        w.writeheader()
        w.writerows(fights)
