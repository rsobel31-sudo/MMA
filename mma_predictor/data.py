"""Core data types and CSV loading.

Two tables drive everything:

* ``fighters.csv`` -- static biographical data (one row per fighter).
* ``fights.csv``   -- one row per bout with the result and per-corner stats.

Career statistics are *never* stored directly. They are derived from the fight
table as of a given date, which is what makes honest backtesting possible: a
prediction for a fight only ever sees bouts that happened before it.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ROUND_SECONDS = 300


class Method(str, Enum):
    KO = "KO/TKO"
    SUB = "SUB"
    DEC = "DEC"
    SPLIT_DEC = "S-DEC"
    DQ = "DQ"
    DRAW = "DRAW"
    NC = "NC"

    @property
    def is_finish(self) -> bool:
        return self in (Method.KO, Method.SUB)

    @property
    def is_decision(self) -> bool:
        return self in (Method.DEC, Method.SPLIT_DEC)

    @property
    def bucket(self) -> str:
        """Collapse to the three outcome buckets used for method prediction."""
        if self is Method.KO:
            return "KO/TKO"
        if self is Method.SUB:
            return "SUB"
        return "DEC"


METHOD_BUCKETS = ("KO/TKO", "SUB", "DEC")


def parse_method(raw: str) -> Method:
    """Normalise the many spellings found in public fight data."""
    s = (raw or "").strip().upper()
    if not s:
        raise ValueError("empty method")
    if s.startswith("NC") or "NO CONTEST" in s or "OVERTURNED" in s:
        return Method.NC
    if "DRAW" in s:
        return Method.DRAW
    if s.startswith("DQ") or "DISQUAL" in s:
        return Method.DQ
    if "KO" in s or "DOCTOR" in s or "CORNER" in s or "RETIRE" in s:
        return Method.KO
    if s.startswith("SUB") or "SUBMISSION" in s:
        return Method.SUB
    if "DEC" in s:
        if "SPLIT" in s or s.startswith("S-") or "MAJORITY" in s or s.startswith("M-"):
            return Method.SPLIT_DEC
        return Method.DEC
    raise ValueError(f"unrecognised method: {raw!r}")


def parse_date(raw: str) -> date:
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unrecognised date: {raw!r}")


def parse_clock(raw: str) -> int:
    """'4:32' -> 272 seconds. Bare numbers are treated as seconds."""
    raw = (raw or "").strip()
    if not raw:
        return ROUND_SECONDS
    try:
        if ":" in raw:
            m, s = raw.split(":", 1)
            return int(m) * 60 + int(s)
        return int(float(raw))
    except ValueError:
        return ROUND_SECONDS // 2  # unknown ("N/A"): assume mid-round


def american_to_prob(odds: float) -> float:
    """Convert American moneyline odds to raw implied probability (with vig)."""
    if odds < 0:
        return -odds / (-odds + 100.0)
    return 100.0 / (odds + 100.0)


def devig(odds_a: float, odds_b: float) -> Tuple[float, float]:
    pa, pb = american_to_prob(odds_a), american_to_prob(odds_b)
    total = pa + pb
    return pa / total, pb / total


@dataclass(frozen=True)
class FighterBio:
    name: str
    dob: Optional[date] = None
    height_cm: Optional[float] = None
    reach_cm: Optional[float] = None
    stance: Optional[str] = None
    # Record accumulated outside the fight table (e.g. regional circuit).
    prior_wins: int = 0
    prior_losses: int = 0

    def age_on(self, when: date) -> Optional[float]:
        if self.dob is None:
            return None
        return (when - self.dob).days / 365.25


@dataclass(frozen=True)
class CornerStats:
    """Stats one fighter produced in one bout."""

    sig_landed: int = 0
    sig_attempted: int = 0
    td_landed: int = 0
    td_attempted: int = 0
    sub_attempts: int = 0
    knockdowns: int = 0
    ctrl_seconds: int = 0
    ground_landed: Optional[int] = None  # significant strikes landed on the ground


@dataclass(frozen=True)
class Fight:
    date: date
    fighter_a: str
    fighter_b: str
    winner: Optional[str]  # None for draws / no contests
    method: Method
    end_round: int
    end_seconds: int  # clock time elapsed in the final round
    scheduled_rounds: int = 3
    weight_class: str = ""
    title_fight: bool = False
    event: str = ""
    stats_a: Optional[CornerStats] = None
    stats_b: Optional[CornerStats] = None
    odds_a: Optional[float] = None
    odds_b: Optional[float] = None

    @property
    def duration_seconds(self) -> int:
        return (self.end_round - 1) * ROUND_SECONDS + self.end_seconds

    @property
    def is_scored(self) -> bool:
        """True when the bout has a winner (usable as a training label)."""
        return self.winner is not None and self.method not in (Method.DRAW, Method.NC)

    def involves(self, name: str) -> bool:
        return name in (self.fighter_a, self.fighter_b)

    def opponent_of(self, name: str) -> str:
        return self.fighter_b if name == self.fighter_a else self.fighter_a

    def stats_for(self, name: str) -> Tuple[Optional[CornerStats], Optional[CornerStats]]:
        """(own stats, opponent stats) from ``name``'s perspective."""
        if name == self.fighter_a:
            return self.stats_a, self.stats_b
        return self.stats_b, self.stats_a


def _opt_float(v: Optional[str]) -> Optional[float]:
    if v is None or str(v).strip() in ("", "NA", "N/A", "--", "None"):
        return None
    return float(v)


def _opt_int(v: Optional[str], default: int = 0) -> int:
    f = _opt_float(v)
    return default if f is None else int(f)


def _truthy(v: Optional[str]) -> bool:
    return str(v or "").strip().lower() in ("1", "true", "yes", "y", "t")


STAT_FIELDS = (
    "sig_landed",
    "sig_attempted",
    "td_landed",
    "td_attempted",
    "sub_attempts",
    "knockdowns",
    "ctrl_seconds",
    "ground_landed",
)


def _corner(row: Dict[str, str], prefix: str) -> Optional[CornerStats]:
    if all(_opt_float(row.get(f"{prefix}_{f}")) is None for f in STAT_FIELDS):
        return None
    values = {f: _opt_int(row.get(f"{prefix}_{f}")) for f in STAT_FIELDS}
    ground = _opt_float(row.get(f"{prefix}_ground_landed"))
    values["ground_landed"] = None if ground is None else int(ground)  # absent != zero
    return CornerStats(**values)


def load_fighters(path: Path) -> Dict[str, FighterBio]:
    fighters: Dict[str, FighterBio] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            name = row["name"].strip()
            dob = row.get("dob", "").strip()
            fighters[name] = FighterBio(
                name=name,
                dob=parse_date(dob) if dob else None,
                height_cm=_opt_float(row.get("height_cm")),
                reach_cm=_opt_float(row.get("reach_cm")),
                stance=(row.get("stance") or "").strip().title() or None,
                prior_wins=_opt_int(row.get("prior_wins")),
                prior_losses=_opt_int(row.get("prior_losses")),
            )
    return fighters


def load_fights(path: Path) -> List[Fight]:
    fights: List[Fight] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for line_no, row in enumerate(csv.DictReader(fh), start=2):
            try:
                fights.append(_parse_fight_row(row))
            except (KeyError, ValueError) as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
    fights.sort(key=lambda f: f.date)
    return fights


def _parse_fight_row(row: Dict[str, str]) -> Fight:
    a, b = row["fighter_a"].strip(), row["fighter_b"].strip()
    method = parse_method(row["method"])
    raw_winner = (row.get("winner") or "").strip()
    winner: Optional[str]
    if method in (Method.DRAW, Method.NC) or raw_winner.lower() in ("", "draw", "nc"):
        winner = None
    elif raw_winner in (a, b):
        winner = raw_winner
    else:
        raise ValueError(f"winner {raw_winner!r} is neither {a!r} nor {b!r}")
    return Fight(
        date=parse_date(row["date"]),
        fighter_a=a,
        fighter_b=b,
        winner=winner,
        method=method,
        end_round=_opt_int(row.get("round"), 1),
        end_seconds=parse_clock(row.get("time", "")),
        scheduled_rounds=_opt_int(row.get("scheduled_rounds"), 3),
        weight_class=(row.get("weight_class") or "").strip(),
        title_fight=_truthy(row.get("title_fight")),
        event=(row.get("event") or "").strip(),
        stats_a=_corner(row, "a"),
        stats_b=_corner(row, "b"),
        odds_a=_opt_float(row.get("a_odds")),
        odds_b=_opt_float(row.get("b_odds")),
    )


@dataclass(frozen=True)
class Matchup:
    """An upcoming (or hypothetical) bout to predict."""

    fighter_a: str
    fighter_b: str
    date: Optional[date] = None
    scheduled_rounds: int = 3
    title_fight: bool = False
    odds_a: Optional[float] = None
    odds_b: Optional[float] = None


def load_card(path: Path) -> List[Matchup]:
    card: List[Matchup] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            d = (row.get("date") or "").strip()
            card.append(
                Matchup(
                    fighter_a=row["fighter_a"].strip(),
                    fighter_b=row["fighter_b"].strip(),
                    date=parse_date(d) if d else None,
                    scheduled_rounds=_opt_int(row.get("scheduled_rounds"), 3),
                    title_fight=_truthy(row.get("title_fight")),
                    odds_a=_opt_float(row.get("a_odds")),
                    odds_b=_opt_float(row.get("b_odds")),
                )
            )
    return card


def load_dataset(directory: Path) -> Tuple[Dict[str, FighterBio], List[Fight]]:
    directory = Path(directory)
    return load_fighters(directory / "fighters.csv"), load_fights(directory / "fights.csv")


def fight_csv_header() -> List[str]:
    base = [
        "date",
        "event",
        "weight_class",
        "fighter_a",
        "fighter_b",
        "winner",
        "method",
        "round",
        "time",
        "scheduled_rounds",
        "title_fight",
    ]
    stats = [f"{p}_{f}" for p in ("a", "b") for f in STAT_FIELDS]
    return base + stats + ["a_odds", "b_odds"]


def iter_names(fights: Iterable[Fight]) -> List[str]:
    seen: Dict[str, None] = {}
    for f in fights:
        seen.setdefault(f.fighter_a)
        seen.setdefault(f.fighter_b)
    return list(seen)


_WS = re.compile(r"\s+")


def normalise_name(name: str) -> str:
    return _WS.sub(" ", name).strip().lower()
