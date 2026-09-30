"""Manual adjustments: your own MMA knowledge layered on top of the data.

Stored as JSON so the web interface and the Python tools share them:

    {
      "fighters": {
        "Fighter Name": {
          "elo": 40,                         # nudge every sub-rating (camp change, injury...)
          "overrides": {"td_def": 0.80,      # replace any snapshot attribute
                        "r_td_def": 1650,    # or a sub-rating (r_ + skills.SUB_RATINGS key)
                        "sig_diff5": 2.5},   # strike differential per 5 min (sets landed/absorbed)
          "note": "New wrestling coach; TD defence looked much better"
        }
      },
      "weights": {"wrestling_edge": 0.45},   # override model feature weights
      "matchups": [
        {"a": "Fighter A", "b": "Fighter B", "logit": 0.3, "note": "B had a bad weight cut"}
      ]
    }

A matchup ``logit`` shifts the log-odds toward ``a`` (0.4 is roughly +10
percentage points near a coin flip). Everything is optional.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .history import FighterSnapshot
from .intangibles import clean as clean_intangibles
from .intangibles import logit as intangibles_logit
from .skills import SUB_RATINGS, SkillConfig, category_rating, overall_rating

# Snapshot attributes that can be overridden (numeric only).
EDITABLE = (
    "slpm", "sapm", "sig_diff5", "str_acc", "str_def", "kd_per15", "kd_absorbed_per15",
    "td_per15", "td_acc", "td_def", "sub_per15", "ctrl_share", "ctrl_against_share",
    "finish_rate", "ko_loss_rate", "sub_loss_rate", "recent_ko_losses", "late_win_rate",
    "form", "streak", "layoff_days", "sos", "age", "reach_cm", "height_cm", "fight_weight",
    "ko_losses", "kd_absorbed", "sig_absorbed", "minutes", "ext_rating",
) + tuple("r_" + k for k in SUB_RATINGS)
INT_FIELDS = ("recent_ko_losses", "streak", "layoff_days", "ko_losses", "kd_absorbed", "sig_absorbed")
CATEGORY_WEIGHTS = SkillConfig().category_weights


@dataclass
class FighterAdjustment:
    elo: float = 0.0
    overrides: Dict[str, float] = field(default_factory=dict)
    note: str = ""


@dataclass
class MatchupAdjustment:
    a: str
    b: str
    logit: float = 0.0
    note: str = ""
    # Your 1-10 scores for this matchup: {"a": {quality: score}, "b": {...}} (intangibles.py).
    intangibles: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class Adjustments:
    fighters: Dict[str, FighterAdjustment] = field(default_factory=dict)
    weights: Dict[str, float] = field(default_factory=dict)
    matchups: List[MatchupAdjustment] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Adjustments":
        fighters = {
            name: FighterAdjustment(
                elo=float(v.get("elo", 0) or 0),
                overrides={k: float(x) for k, x in (v.get("overrides") or {}).items() if k in EDITABLE and x is not None},
                note=v.get("note", "") or "",
            )
            for name, v in (d.get("fighters") or {}).items()
        }
        matchups = [
            MatchupAdjustment(m["a"], m["b"], float(m.get("logit", 0) or 0), m.get("note", "") or "",
                              {side: clean_intangibles((m.get("intangibles") or {}).get(side)) for side in ("a", "b")})
            for m in d.get("matchups") or []
        ]
        return cls(fighters, {k: float(v) for k, v in (d.get("weights") or {}).items()}, matchups)

    @classmethod
    def load(cls, path: Optional[Path]) -> "Adjustments":
        if path is None or not Path(path).exists():
            return cls()
        return cls.from_dict(json.loads(Path(path).read_text()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighters": {n: dataclasses.asdict(f) for n, f in self.fighters.items()},
            "weights": dict(self.weights),
            "matchups": [dataclasses.asdict(m) for m in self.matchups],
        }

    def save(self, path: Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    # -------------------------------------------------------------- applying
    def apply(self, s: FighterSnapshot) -> FighterSnapshot:
        adj = self.fighters.get(s.name)
        if adj is None:
            return s
        changes: Dict[str, Any] = {}
        bio = s.bio
        # The Elo nudge shifts every sub-rating, so the overall moves by exactly that much.
        ratings = {k: v + adj.elo for k, v in s.ratings.items()}
        for k, v in adj.overrides.items():
            if k.startswith("r_"):
                if k[2:] in ratings:
                    ratings[k[2:]] = v
            elif k == "sig_diff5":
                continue  # applied below, after any landed/absorbed edits
            elif k in ("reach_cm", "height_cm"):
                bio = dataclasses.replace(bio, **{k: v})
            elif k in INT_FIELDS:
                changes[k] = int(round(v))
            else:
                changes[k] = v
        if "sig_diff5" in adj.overrides:
            # Keep the fighter's output (landed + absorbed) and set the gap between them.
            landed, absorbed = changes.get("slpm", s.slpm), changes.get("sapm", s.sapm)
            mid, half = (landed + absorbed) / 2.0, adj.overrides["sig_diff5"] / 10.0
            changes["slpm"], changes["sapm"] = max(0.1, mid + half), max(0.1, mid - half)
        if ratings:
            changes.update(
                ratings=ratings,
                striking=category_rating(ratings, "striking"),
                wrestling=category_rating(ratings, "wrestling"),
                grappling=category_rating(ratings, "grappling"),
                elo=overall_rating(ratings, CATEGORY_WEIGHTS),
            )
        else:
            changes["elo"] = s.elo + adj.elo
        changes["proven"] = s.proven + (changes["elo"] - s.elo)
        return dataclasses.replace(s, bio=bio, **changes)

    def matchup_logit(self, a: str, b: str) -> float:
        total = 0.0
        for m in self.matchups:
            if (m.a, m.b) == (a, b):
                total += m.logit
            elif (m.a, m.b) == (b, a):
                total -= m.logit
        return total

    def intangibles_logit(self, a: str, b: str) -> float:
        """Log-odds toward ``a`` from your 1-10 intangibles scores for this matchup (either order)."""
        total = 0.0
        for m in self.matchups:
            sc = m.intangibles or {}
            if (m.a, m.b) == (a, b):
                total += intangibles_logit(sc.get("a"), sc.get("b"))
            elif (m.a, m.b) == (b, a):
                total += intangibles_logit(sc.get("b"), sc.get("a"))
        return total

    def notes_for(self, a: str, b: str) -> List[str]:
        out = []
        for name in (a, b):
            adj = self.fighters.get(name)
            if adj and (adj.note or adj.elo or adj.overrides):
                bits = []
                if adj.elo:
                    bits.append(f"Elo {adj.elo:+.0f}")
                bits += [f"{k}={v:g}" for k, v in adj.overrides.items()]
                out.append(f"Your adjustment to {name}: {', '.join(bits) or 'note'}" + (f" - {adj.note}" if adj.note else ""))
        for m in self.matchups:
            if {m.a, m.b} == {a, b} and m.logit:
                out.append(f"Your matchup read: {m.logit:+.2f} log-odds toward {m.a}" + (f" - {m.note}" if m.note else ""))
        return out
