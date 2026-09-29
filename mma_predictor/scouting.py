"""Scouting knowledge the stats can't see: fighter backgrounds and fight commentary.

Backgrounds (``data/scouting/backgrounds.json``)
------------------------------------------------
Martial-arts pedigree becomes a *prior* on the matching sub-ratings. A 2011
IBJJF world champion starts with elite submission offence and defence even if
he rarely finishes people in MMA, because grapplers often win by control and
don't need the tap. The boost fades slowly as MMA evidence accumulates:

    effective = evidence_rating + boost * K / (K + bouts)      K = 10

so after ten bouts half the pedigree still counts. When a fighter has several
credentials, each sub-rating takes the largest boost, not the sum.

    {"Gilbert Burns": {
        "summary": "Brazilian jiu-jitsu world champion turned MMA fighter.",
        "credentials": [
          {"discipline": "bjj", "level": "elite",
           "detail": "2011 IBJJF World Champion (black belt)", "source": "https://..."}
        ]}}

Fight commentary (``data/scouting/fight_notes.json``)
------------------------------------------------------
A judgment of how a fighter did in one domain of one bout, relative to the
opponent: -2 (dominated) .. 0 (even) .. +2 (dominant). It's evidence like a
stat, and it's judged against expectation, so "held even on the mat with an
elite grappler" raises a fighter's grappling while the same line against a
weak grappler barely moves it.

    [{"date": "2020-03-14", "fighter": "Gilbert Burns", "opponent": "Demian Maia",
      "category": "grappling", "rating": 1, "skills": ["sub_def", "scramble"],
      "note": "...", "source": "https://..."}]
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .data import normalise_name, parse_date

# Rating points for each credential level (before discipline weights).
LEVELS: Dict[str, float] = {
    "elite": 200.0,          # Olympic / world champion, ADCC champion, NCAA D1 champion
    "international": 140.0,  # world/ADCC medallist, NCAA D1 All-American, major pro kickboxing title
    "national": 90.0,        # national champion, NCAA D1 qualifier, pro kickboxing/boxing record
    "experienced": 50.0,     # black belt, collegiate/high-school wrestling, amateur boxing
}

# Which sub-ratings each discipline informs, and how strongly.
DISCIPLINES: Dict[str, Dict[str, float]] = {
    "bjj": {"sub_off": 1.0, "sub_def": 1.0, "scramble": 0.6, "control": 0.4},
    "grappling": {"sub_off": 0.9, "sub_def": 0.9, "scramble": 0.6, "control": 0.5},
    "wrestling": {"td_off": 1.0, "td_def": 1.0, "control": 0.8, "scramble": 0.7, "gnp": 0.3},
    "judo": {"td_off": 0.8, "td_def": 0.8, "control": 0.6, "sub_off": 0.3},
    "sambo": {"td_off": 0.8, "td_def": 0.8, "control": 0.6, "sub_off": 0.5, "sub_def": 0.4},
    "boxing": {"strike_off": 1.0, "strike_def": 0.8, "power": 0.5},
    "kickboxing": {"strike_off": 1.0, "strike_def": 0.7, "power": 0.5},
    "muay_thai": {"strike_off": 1.0, "strike_def": 0.6, "power": 0.5},
    "karate": {"strike_off": 0.8, "strike_def": 0.8},
    "taekwondo": {"strike_off": 0.8, "strike_def": 0.6},
}

CATEGORY_NAMES = ("striking", "wrestling", "grappling")


@dataclass
class Credential:
    discipline: str
    level: str
    detail: str = ""
    source: str = ""


@dataclass
class Background:
    name: str
    summary: str = ""
    credentials: List[Credential] = field(default_factory=list)

    def boosts(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for c in self.credentials:
            base = LEVELS.get(c.level, 0.0)
            for key, weight in DISCIPLINES.get(c.discipline, {}).items():
                out[key] = max(out.get(key, 0.0), base * weight)
        return out


@dataclass(frozen=True)
class FightNote:
    date: date
    fighter: str
    opponent: str
    category: str  # striking | wrestling | grappling
    rating: float  # -2 .. +2, relative to the opponent
    skills: Tuple[str, ...] = ()  # optional: limit to these sub-ratings
    note: str = ""
    source: str = ""


def load_backgrounds(path: Optional[Path]) -> Dict[str, Background]:
    if path is None or not Path(path).exists():
        return {}
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {}
    for name, v in raw.items():
        creds = []
        for c in v.get("credentials", []):
            if c.get("discipline") not in DISCIPLINES or c.get("level") not in LEVELS:
                raise ValueError(f"{path}: {name}: unknown discipline/level {c.get('discipline')!r}/{c.get('level')!r}")
            creds.append(Credential(c["discipline"], c["level"], c.get("detail", ""), c.get("source", "")))
        out[name] = Background(name, v.get("summary", ""), creds)
    return out


def load_notes(path: Optional[Path]) -> List[FightNote]:
    if path is None or not Path(path).exists():
        return []
    notes = []
    for i, n in enumerate(json.loads(Path(path).read_text(encoding="utf-8"))):
        if n.get("category") not in CATEGORY_NAMES:
            raise ValueError(f"{path}[{i}]: category must be one of {CATEGORY_NAMES}")
        rating = float(n["rating"])
        if not -2 <= rating <= 2:
            raise ValueError(f"{path}[{i}]: rating must be between -2 and 2")
        notes.append(FightNote(parse_date(n["date"]), n["fighter"], n["opponent"], n["category"], rating,
                               tuple(n.get("skills") or ()), n.get("note", ""), n.get("source", "")))
    return notes


def notes_key(when: date, a: str, b: str) -> Tuple[date, frozenset]:
    return when, frozenset((normalise_name(a), normalise_name(b)))


@dataclass
class Scouting:
    backgrounds: Dict[str, Background] = field(default_factory=dict)
    notes: List[FightNote] = field(default_factory=list)

    @classmethod
    def load(cls, directory: Optional[Path]) -> "Scouting":
        if directory is None:
            return cls()
        d = Path(directory)
        return cls(load_backgrounds(d / "backgrounds.json"), load_notes(d / "fight_notes.json"))

    def boosts(self) -> Dict[str, Dict[str, float]]:
        return {name: b.boosts() for name, b in self.backgrounds.items()}
