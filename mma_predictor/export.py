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
from .analysis import upcoming_flags
from .bios import division_label, write_bio
from .sources.events import link_names
from .skills import CATEGORIES, SUB_LABELS

SNAPSHOT_FIELDS = (
    "elo", "fights", "wins", "losses", "age", "minutes", "stat_minutes",
    "slpm", "sapm", "str_acc", "str_def", "kd_per15", "kd_absorbed_per15",
    "td_per15", "td_acc", "td_def", "sub_per15", "ctrl_share", "ctrl_against_share",
    "win_methods", "loss_methods", "finish_rate", "ko_loss_rate", "sub_loss_rate",
    "recent_ko_losses", "late_win_rate", "five_round_fights", "form", "streak",
    "layoff_days", "sos", "quality_win_elo", "striking", "wrestling", "grappling",
    "ko_losses", "kd_absorbed", "sig_absorbed", "pedigree", "rd", "proven",
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
    upcoming: Optional[Dict[str, Any]] = None,
    aliases: Optional[Dict[str, str]] = None,
    rankings: Optional[List[Dict[str, str]]] = None,
    insights: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    model = model or WinModel()
    as_of = as_of or history.default_date()
    known_wc = {n: b.weight_class for n, b in history.bios.items() if b.weight_class}
    fighters: List[Dict[str, Any]] = []
    picked: List[Tuple[FighterSnapshot, Dict[str, Any]]] = []
    # Fighters on upcoming cards or in the official rankings are always exported.
    dataset_names = set(history.names())
    card_names = [str(b[k]) for e in (upcoming or {}).get("events", []) for b in e.get("bouts", []) for k in ("a", "b")]
    ranked_names = [r["name"] for r in (rankings or [])]
    linked = link_names(set(card_names) | set(ranked_names), dataset_names, aliases)
    must = set(linked.values())
    for name in history.names():
        s = history.snapshot(name, as_of)
        researched = name in history.scouting.backgrounds and s.fights >= 1
        inactive = s.layoff_days is None or s.layoff_days > active_years * 365
        if name not in must and not researched and (s.fights < min_fights or inactive):
            continue
        row = snapshot_json(s)
        wc, inferred = infer_weight_class(history, name, as_of, known_wc)
        row.update(weight_class=wc, weight_class_inferred=inferred, gender=s.bio.gender,
                   division=division_label(wc, s.bio.gender),
                   weight_class_source="inferred" if inferred else (s.bio.weight_class_source or ("sherdog" if wc else "")),
                   nationality=s.bio.nationality, team=s.bio.team, height_cm=s.bio.height_cm,
                   complete=s.bio.complete)
        bg = history.scouting.backgrounds.get(name)
        if bg:
            row["background"] = {"summary": bg.summary, "credentials": [dataclasses.asdict(c) for c in bg.credentials]}
        row["notes"] = [
            {"date": n.date.isoformat(), "fighter": n.fighter, "opponent": n.opponent, "category": n.category,
             "rating": n.rating, "note": n.note, "source": n.source}
            for n in history.scouting.notes if name in (n.fighter, n.opponent)
        ]
        row["history"] = [
            {"date": a.fight.date.isoformat(), "opponent": a.opponent, "result": {True: "W", False: "L", None: "D"}[a.result],
             "method": a.method.value, "round": a.fight.end_round, "time": f"{a.fight.end_seconds // 60}:{a.fight.end_seconds % 60:02d}",
             "event": a.fight.event, "opp_rating": round(a.opp_elo)}
            for a in reversed(s.all_appearances[-40:])
        ]
        picked.append((s, row))
    # Bios compare each fighter with the others in their division.
    divisions: Dict[str, List[FighterSnapshot]] = {}
    for s, row in picked:
        divisions.setdefault(row["division"], []).append(s)
    for s, row in picked:
        peers = divisions.get(row["division"], []) if row["division"] else []
        row["bio"] = write_bio(s, peers, row["division"], history.scouting.backgrounds.get(s.name))
        fighters.append(row)
    fighters.sort(key=lambda f: -f["elo"])
    # Official UFC rank(s), for comparing our order with the UFC's.
    by_name = {f["name"]: f for f in fighters}
    for r in rankings or []:
        target = linked.get(r["name"])
        if target in by_name:
            by_name[target].setdefault("official", {})[r["system"]] = {"rank": r["rank"], "division": r["division"]}
    cards = []
    for e in (upcoming or {}).get("events", []):
        bouts = []
        for b in e.get("bouts", []):
            a_id = linked.get(str(b["a"])) if linked.get(str(b["a"])) in by_name else None
            b_id = linked.get(str(b["b"])) if linked.get(str(b["b"])) in by_name else None
            row = dict(b, a_id=a_id, b_id=b_id)
            if a_id and b_id:
                # Which historical matchup patterns this bout fits ("a"/"b" = who has the edge).
                row["patterns"] = [{"key": k, "side": "a" if s > 0 else "b", "detail": d}
                                   for k, s, d in upcoming_flags(history, a_id, b_id, int(b.get("rounds") or 3), as_of)]
            bouts.append(row)
        cards.append(dict(e, bouts=bouts))
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
        "calibration_scale": model.scale,
        "prior_weights": PRIOR_WEIGHTS,
        "rating_categories": {k: list(v) for k, v in CATEGORIES.items()},
        "rating_labels": SUB_LABELS,
        "category_weights": history.skills.config.category_weights,
        "insights": insights,
        "upcoming": {"fetched": (upcoming or {}).get("fetched"), "source": (upcoming or {}).get("source"), "events": cards},
        "fighters": fighters,
    }


def write(data: Dict[str, Any], path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, separators=(",", ":")))
