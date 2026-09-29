"""Manual adjustments: your own MMA knowledge layered on top of the data.

Stored as JSON so the web interface and the Python tools share them:

    {
      "fighters": {
        "Fighter Name": {
          "elo": 40,                         # rating nudge (camp change, injury...)
          "overrides": {"td_def": 0.80},     # replace any snapshot attribute
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

# Snapshot attributes that can be overridden (numeric only).
EDITABLE = (
    "slpm", "sapm", "str_acc", "str_def", "kd_per15", "kd_absorbed_per15",
    "td_per15", "td_acc", "td_def", "sub_per15", "ctrl_share", "ctrl_against_share",
    "finish_rate", "ko_loss_rate", "sub_loss_rate", "recent_ko_losses", "late_win_rate",
    "form", "streak", "layoff_days", "sos", "age", "reach_cm",
)


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
            MatchupAdjustment(m["a"], m["b"], float(m.get("logit", 0) or 0), m.get("note", "") or "")
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
        changes: Dict[str, Any] = {"elo": s.elo + adj.elo}
        bio = s.bio
        for k, v in adj.overrides.items():
            if k == "reach_cm":
                bio = dataclasses.replace(bio, reach_cm=v)
            elif k in ("recent_ko_losses", "streak", "layoff_days"):
                changes[k] = int(round(v))
            else:
                changes[k] = v
        return dataclasses.replace(s, bio=bio, **changes)

    def matchup_logit(self, a: str, b: str) -> float:
        total = 0.0
        for m in self.matchups:
            if (m.a, m.b) == (a, b):
                total += m.logit
            elif (m.a, m.b) == (b, a):
                total -= m.logit
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
