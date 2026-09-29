"""Export fighter snapshots + model for the web interface (``app/``).

The page re-implements the feature, method and pattern logic in
JavaScript (``app/engine.js``) so it can recompute instantly as you edit.
``tests/test_engine_parity.py`` checks the two implementations agree.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import date
from pathlib import Path
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from .features import FEATURE_LABELS, FEATURES
from .history import DEFAULT_PRIORS, FightHistory, FighterSnapshot
from .model import PRIOR_WEIGHTS, WinModel
from .skills import CATEGORIES, SUB_LABELS

SNAPSHOT_FIELDS = (
    "elo", "fights", "wins", "losses", "age", "minutes", "stat_minutes",
    "slpm", "sapm", "str_acc", "str_def", "kd_per15", "kd_absorbed_per15",
    "td_per15", "td_acc", "td_def", "sub_per15", "ctrl_share", "ctrl_against_share",
    "win_methods", "loss_methods", "finish_rate", "ko_loss_rate", "sub_loss_rate",
    "recent_ko_losses", "late_win_rate", "five_round_fights", "form", "streak",
    "layoff_days", "sos", "quality_win_elo", "striking", "wrestling", "grappling",
    "ko_losses", "kd_absorbed", "sig_absorbed", "pedigree",
)


def _round(v: Any) -> Any:
    if isinstance(v, float):
        return round(v, 5)
    if isinstance(v, dict):
        return {k: _round(x) for k, x in v.items()}
    return v


def snapshot_json(s: FighterSnapshot) -> Dict[str, Any]:
    out = {k: _round(getattr(s, k)) for k in SNAPSHOT_FIELDS}
    # Sub-ratings flattened as r_<key>, the same names adjustments use.
    out.update({"r_" + k: _round(v) for k, v in s.ratings.items()})
    out.update(
        name=s.name,
        prior_wins=s.bio.prior_wins,
        prior_losses=s.bio.prior_losses,
        reach_cm=s.bio.reach_cm,
        height_cm=s.bio.height_cm,
        stance=s.bio.stance,
        dob=s.bio.dob.isoformat() if s.bio.dob else None,
        recent=[
            {
                "date": a.fight.date.isoformat(),
                "opponent": a.opponent,
                "result": {True: "W", False: "L", None: "D"}[a.result],
                "method": a.method.value,
                "round": a.fight.end_round,
                "event": a.fight.event,
            }
            for a in reversed(s.recent)
        ],
    )
    return out


def infer_weight_class(history: FightHistory, name: str, as_of: date, known: Dict[str, str]) -> Tuple[str, bool]:
    """A fighter's listed class, or else the most common class among recent opponents."""
    if name in known:
        return known[name], False
    votes: Counter = Counter()
    apps = history.appearances_before(name, as_of)
    for i, app in enumerate(reversed(apps[-6:])):
        if app.opponent in known:
            votes[known[app.opponent]] += 1.0 / (1 + i)  # recent opponents count more
    if not votes:
        return "", False
    return votes.most_common(1)[0][0], True


def export(
    history: FightHistory,
    model: Optional[WinModel] = None,
    min_fights: int = 2,
    active_years: float = 4.0,
    as_of: Optional[date] = None,
    backtest: Optional[Dict[str, Any]] = None,
    source: str = "",
) -> Dict[str, Any]:
    model = model or WinModel()
    as_of = as_of or history.default_date()
    known_wc = {n: b.weight_class for n, b in history.bios.items() if b.weight_class}
    fighters: List[Dict[str, Any]] = []
    for name in history.names():
        s = history.snapshot(name, as_of)
        researched = name in history.scouting.backgrounds and s.fights >= 1
        inactive = s.layoff_days is None or s.layoff_days > active_years * 365
        if not researched and (s.fights < min_fights or inactive):
            continue
        row = snapshot_json(s)
        wc, inferred = infer_weight_class(history, name, as_of, known_wc)
        row.update(weight_class=wc, weight_class_inferred=inferred,
                   nationality=s.bio.nationality, team=s.bio.team)
        bg = history.scouting.backgrounds.get(name)
        if bg:
            row["background"] = {"summary": bg.summary, "credentials": [dataclasses.asdict(c) for c in bg.credentials]}
        row["notes"] = [
            {"date": n.date.isoformat(), "fighter": n.fighter, "opponent": n.opponent, "category": n.category,
             "rating": n.rating, "note": n.note, "source": n.source}
            for n in history.scouting.notes if name in (n.fighter, n.opponent)
        ]
        fighters.append(row)
    fighters.sort(key=lambda f: -f["elo"])
    return {
        "meta": {
            "as_of": as_of.isoformat(),
            "last_fight": history.last_date().isoformat(),
            "bouts": len(history.fights),
            "fighters_total": len(history.bios),
            "fighters_exported": len(fighters),
            "trained_on": model.trained_on,
            "source": source,
            "backtest": backtest,
        },
        "priors": dataclasses.asdict(DEFAULT_PRIORS),
        "features": FEATURES,
        "feature_labels": FEATURE_LABELS,
        "weights": model.weights,
        "prior_weights": PRIOR_WEIGHTS,
        "rating_categories": {k: list(v) for k, v in CATEGORIES.items()},
        "rating_labels": SUB_LABELS,
        "category_weights": history.skills.config.category_weights,
        "fighters": fighters,
    }


def write(data: Dict[str, Any], path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, separators=(",", ":")))
