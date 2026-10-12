"""One row per scored UFC bout since 2016 for the model reviews (review.py): the walk-forward (out-of-sample)
win chance, the method model's chance of a decision, the closing line, and both fighters' traits before the bout.

    python -m mma_predictor review-data      # about 10-15 minutes; writes .cache/review/bouts.jsonl
"""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".cache" / "review" / "bouts.jsonl"
SINCE = date(2016, 1, 1)
TRAITS = ("elo", "fights", "wins", "losses", "age", "slpm", "sapm", "str_acc", "str_def", "kd_per15", "td_per15", "td_acc",
          "td_def", "sub_per15", "ctrl_share", "finish_rate", "ko_loss_rate", "sub_loss_rate", "recent_ko_losses",
          "late_win_rate", "form", "streak", "layoff_days", "sos", "striking", "wrestling", "grappling", "proven", "rd",
          "ko_losses")


def american_to_p(odds) -> Optional[float]:
    try:
        o = float(odds)
    except (TypeError, ValueError):
        return None
    if o == 0:
        return None
    return 100 / (o + 100) if o > 0 else -o / (-o + 100)


def no_vig(a, b) -> Optional[float]:
    pa, pb = american_to_p(a), american_to_p(b)
    return pa / (pa + pb) if pa and pb else None


def _snap(s, bio) -> Dict[str, object]:
    out = {k: getattr(s, k) for k in TRAITS}
    out["reach_cm"] = getattr(bio, "reach_cm", None) if bio else None
    out["height_cm"] = getattr(bio, "height_cm", None) if bio else None
    out["stance"] = getattr(bio, "stance", None) if bio else None
    for k, v in list(out.items()):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            out[k] = None
    return out


def build(data: str = "data/verified", app_data: str = "app/data.json", log=print) -> List[dict]:
    from types import SimpleNamespace

    from . import picks as P
    from .backtest import walk_forward
    from .cli import _history
    from .data import Method
    from .features import BoutContext
    from .methods import method_distribution
    from .model import sigmoid
    from .picks_cli import _model
    from .predictor import FightPredictor

    h = _history(SimpleNamespace(data=data, scouting=None))
    log("walk-forward backtest (out-of-sample win chances)...")
    res = walk_forward(h, event_prefix="UFC")
    scale = json.loads(Path(app_data).read_text()).get("calibration_scale", 1.0)
    model, _ = _model(Path(app_data))
    pr = FightPredictor(h, model)
    timing = P.Timing.from_fights([f for f in h.fights if f.date < SINCE])
    odds = {}
    import csv
    with open(Path(data) / "fights.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("a_odds") and r.get("b_odds"):
                odds[(r["date"], r["fighter_a"], r["fighter_b"])] = no_vig(r["a_odds"], r["b_odds"])
    rows = []
    for f, p, x in res.predictions:
        if f.date < SINCE or not f.is_scored or f.winner is None:
            continue
        try:
            sa, sb, _x = pr.features(f.fighter_a, f.fighter_b, f.date, BoutContext(f.scheduled_rounds, f.title_fight))
        except KeyError:
            continue
        pa = sigmoid(scale * math.log(p / (1 - p)))
        pdec = P.model_prob(("distance", True), pa, method_distribution(sa, sb, f.scheduled_rounds),
                            method_distribution(sb, sa, f.scheduled_rounds), f.scheduled_rounds, timing)
        key = (f.date.isoformat(), f.fighter_a, f.fighter_b)
        mk = odds.get(key)
        if mk is None and (key[0], f.fighter_b, f.fighter_a) in odds:
            v = odds[(key[0], f.fighter_b, f.fighter_a)]
            mk = None if v is None else 1 - v
        rows.append({
            "date": f.date.isoformat(), "event": f.event, "a": f.fighter_a, "b": f.fighter_b,
            "wc": f.weight_class, "rounds": f.scheduled_rounds, "title": bool(f.title_fight),
            "y": int(f.winner == f.fighter_a), "method": f.method.value, "round": f.end_round,
            "dec": int(f.method not in (Method.KO, Method.SUB)),
            "pa": round(pa, 4), "pdec_raw": round(pdec, 4), "market": None if mk is None else round(mk, 4),
            "sa": _snap(sa, h.bios.get(f.fighter_a)), "sb": _snap(sb, h.bios.get(f.fighter_b)),
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r, default=str) + "\n" for r in rows))
    log(f"{len(rows)} bouts ({sum(r['market'] is not None for r in rows)} with a closing line) -> {OUT}")
    return rows


def load() -> List[dict]:
    return [json.loads(l) for l in OUT.read_text().splitlines() if l.strip()]


def cmd_review_data(args) -> int:
    build(args.data, args.app_data)
    return 0


def register(sub) -> None:
    p = sub.add_parser("review-data", help="per-bout dataset for the model reviews (walk-forward chances, lines, traits)")
    p.add_argument("--data", default="data/verified")
    p.add_argument("--app-data", default="app/data.json")
    p.set_defaults(func=cmd_review_data)
