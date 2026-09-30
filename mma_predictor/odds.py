"""Betting lines from BestFightOdds, linked to our verified bouts.

Each BestFightOdds bout is matched to a bout in our data (same two fighters
within a day, names matched regardless of order, accents or spelling). A
match means the bout is confirmed by an independent source and its lines can
be used:

- the closing line (the market's final word) is a benchmark for the model
  and fills ``a_odds``/``b_odds`` in the dataset;
- the opening line and the movement between them show where money went.

Lines are checked before use: both sides present, a bookmaker margin between
0% and 20%, and (where both fighters' pages list the bout) the two pages
agreeing on the lines. Upcoming bouts carry the current line.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .data import Fight, Method
from .sources.bestfightodds import closing, fair_pair, implied
from .verify import BoutMatch, load_jsonl, match_bouts


@dataclass
class MarketLine:
    """Both fighters' lines for one bout, oriented to (fighter_a, fighter_b) of our data."""

    date: date
    event: str
    a_open: Optional[int]
    b_open: Optional[int]
    a_close: Optional[int]
    b_close: Optional[int]
    movement_a: List[float] = field(default_factory=list)  # A's average decimal odds over time
    pages: int = 1  # how many fighter pages listed it (2 = both sides, cross-checked)

    @property
    def p_open(self) -> Optional[float]:
        return fair_pair(self.a_open, self.b_open)

    @property
    def p_close(self) -> Optional[float]:
        return fair_pair(self.a_close, self.b_close)

    @property
    def move(self) -> Optional[float]:
        """Change in A's fair win probability from open to close (+ = money came in on A)."""
        if self.p_open is None or self.p_close is None:
            return None
        return self.p_close - self.p_open

    @property
    def margin(self) -> Optional[float]:
        pa, pb = implied(self.a_close), implied(self.b_close)
        return None if pa is None or pb is None else pa + pb - 1.0


def _sane(a: Optional[int], b: Optional[int]) -> bool:
    pa, pb = implied(a), implied(b)
    return pa is not None and pb is not None and -0.005 <= pa + pb - 1.0 <= 0.20


def load_lines(path: Path) -> List[Tuple[Fight, dict]]:
    """Unique BestFightOdds bouts as (Fight, record); both fighters' copies are compared."""
    by_key: Dict[tuple, dict] = {}
    conflicts = 0
    for page in load_jsonl(Path(path)):
        for b in page.get("bouts", []):
            urls = tuple(sorted((b["fighter_url"], b["opponent_url"])))
            key = (b["date"], urls)
            flip = b["fighter_url"] != urls[0]
            fl, ol = b["fighter_line"], b["opponent_line"]
            first, second = (ol, fl) if flip else (fl, ol)
            rec = {"date": b["date"], "event": b["event"], "a": b["opponent"] if flip else b["fighter"],
                   "b": b["fighter"] if flip else b["opponent"], "a_line": first, "b_line": second,
                   "movement": {"b" if flip else "a": b.get("movement", [])}, "pages": 1}
            old = by_key.get(key)
            if old is None:
                by_key[key] = rec
            else:
                if (old["a_line"], old["b_line"]) != (rec["a_line"], rec["b_line"]):
                    conflicts += 1
                    old["conflict"] = True
                old["pages"] = 2
                for side, series in rec["movement"].items():
                    old["movement"].setdefault(side, series)
    out = []
    for rec in by_key.values():
        f = Fight(date.fromisoformat(rec["date"]), rec["a"], rec["b"], None, Method.NC, 1, 0, event=rec["event"])
        out.append((f, rec))
    return out


def link(fights: Iterable[Fight], lines: List[Tuple[Fight, dict]]) -> Tuple[Dict[int, MarketLine], Dict[str, int]]:
    """{id(our Fight): MarketLine} for matched bouts with sane lines, plus a report."""
    fights = list(fights)
    report = {"odds bouts": len(lines), "matched": 0, "unmatched": 0, "bad lines": 0, "pages disagree": 0, "both pages": 0}
    out: Dict[int, MarketLine] = {}
    for m, (_, rec) in zip(match_bouts(fights, [f for f, _ in lines]), lines):
        if m.base is None:
            report["unmatched"] += 1
            continue
        if rec.get("conflict"):
            report["pages disagree"] += 1
            continue
        la, lb = (rec["b_line"], rec["a_line"]) if m.swapped else (rec["a_line"], rec["b_line"])
        mv = movement_for(rec["movement"], "b" if m.swapped else "a")
        ml = MarketLine(m.base.date, rec["event"], la["open"], lb["open"], closing_line(la), closing_line(lb), mv, rec["pages"])
        if not _sane(ml.a_close, ml.b_close):
            report["bad lines"] += 1
            continue
        report["matched"] += 1
        report["both pages"] += rec["pages"] == 2
        out[id(m.base)] = ml
    return out, report


def movement_for(movement: Dict[str, List[float]], side: str) -> List[float]:
    """Decimal-odds series for ``side``; converted from the other side's series if that's all there is."""
    if movement.get(side):
        return list(movement[side])
    other = movement.get("b" if side == "a" else "a") or []
    return [x / (x - 1.0) for x in other if x > 1.0]  # the opposite side at the same (margin-free) price


def closing_line(line: dict) -> Optional[int]:
    from .sources.bestfightodds import Line

    return closing(Line(line.get("open"), line.get("close_lo"), line.get("close_hi")))


def logit(p: float) -> float:
    p = min(1 - 1e-6, max(1e-6, p))
    return math.log(p / (1 - p))


def upcoming_lines(path: Path, as_of: date) -> List[dict]:
    """Current lines for bouts on or after ``as_of`` (BestFightOdds lists scheduled bouts too)."""
    out = []
    for f, rec in load_lines(Path(path)):
        if f.date >= as_of and not rec.get("conflict"):
            out.append({"date": f.date, "a": rec["a"], "b": rec["b"], "a_line": rec["a_line"], "b_line": rec["b_line"],
                        "movement": rec["movement"]})
    return out


def line_for(upcoming: List[dict], a: str, b: str, when: Optional[date], days: int = 4) -> Optional[dict]:
    """The market for a scheduled bout, oriented to (a, b): opening and current lines, and A's movement."""
    from .verify import name_score

    for u in upcoming:
        if when and abs((u["date"] - when).days) > days:
            continue
        for flip, (x, y) in ((False, (u["a"], u["b"])), (True, (u["b"], u["a"]))):
            s1, s2 = name_score(a, x), name_score(b, y)
            if min(s1, s2) >= 1 and max(s1, s2) == 2:
                la, lb = (u["b_line"], u["a_line"]) if flip else (u["a_line"], u["b_line"])
                return {"a_open": la.get("open"), "b_open": lb.get("open"), "a_now": closing_line(la), "b_now": closing_line(lb),
                        "movement_a": [round(v, 4) for v in movement_for(u["movement"], "b" if flip else "a")]}
    return None
