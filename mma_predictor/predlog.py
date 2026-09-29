"""Prediction log: record picks before fights happen, grade them after.

``data/predictions/log.json`` keeps one entry per scheduled bout. The first
prediction made for a bout is frozen (``first``) so the grade reflects what
the model said beforehand. ``latest`` is refreshed on every export so you can
see how the pick moved as new data arrived. Once the bout appears in the fight
data, it is graded: did the pick win, and what was the log-loss.
"""

from __future__ import annotations

import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .data import normalise_name
from .history import FightHistory


def _key(event_date: str, a: str, b: str) -> str:
    x, y = sorted((normalise_name(a), normalise_name(b)))
    return f"{event_date}|{x}|{y}"


def _find_result(history: FightHistory, a: str, b: str, when: date) -> Optional[Dict[str, Any]]:
    for app in reversed(history.appearances_before(a, when + timedelta(days=3))):
        f = app.fight
        if abs((f.date - when).days) <= 2 and app.opponent == b:
            return {"winner": f.winner, "method": f.method.value, "round": f.end_round, "date": f.date.isoformat()}
    return None


def update(path: Path, history: FightHistory, events: List[Dict[str, Any]], predict, model_info: Dict[str, Any]) -> Dict[str, Any]:
    """Add/refresh predictions for scheduled bouts and grade finished ones.

    ``predict(a, b, rounds)`` returns a dict with p_a, pick, method, method_p.
    """
    path = Path(path)
    log: Dict[str, Any] = json.loads(path.read_text()) if path.exists() else {"entries": {}}
    entries: Dict[str, Any] = log["entries"]
    today = date.today().isoformat()
    for e in events:
        for bt in e.get("bouts", []):
            a, b = bt.get("a_id"), bt.get("b_id")
            if not a or not b:
                continue
            k = _key(e["date"], a, b)
            pred = dict(predict(a, b, int(bt.get("rounds") or 3)), made=today, model=model_info)
            entry = entries.setdefault(k, {"event": e["name"], "date": e["date"], "a": a, "b": b,
                                           "weight_class": bt.get("weight_class"), "first": pred})
            if "result" not in entry:
                entry["latest"] = pred
    # Grade anything that has happened.
    for entry in entries.values():
        if "result" in entry:
            continue
        when = date.fromisoformat(entry["date"])
        if when > history.last_date():
            continue
        res = _find_result(history, entry["a"], entry["b"], when)
        if res is None:
            continue
        pa = entry["first"]["p_a"]
        if res["winner"] is None:
            entry["result"] = dict(res, graded=today, correct=None, log_loss=None)
            continue
        a_won = res["winner"] == entry["a"]
        p = min(1 - 1e-6, max(1e-6, pa if a_won else 1 - pa))
        entry["result"] = dict(res, graded=today, correct=(pa >= 0.5) == a_won, log_loss=-math.log(p))
    graded = [e for e in entries.values() if e.get("result", {}).get("correct") is not None]
    log["scorecard"] = {
        "graded": len(graded),
        "correct": sum(1 for e in graded if e["result"]["correct"]),
        "accuracy": (sum(1 for e in graded if e["result"]["correct"]) / len(graded)) if graded else None,
        "log_loss": (sum(e["result"]["log_loss"] for e in graded) / len(graded)) if graded else None,
        "pending": sum(1 for e in entries.values() if "result" not in e),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, indent=1))
    return log
