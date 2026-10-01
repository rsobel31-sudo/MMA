"""Backtest of the prospect score on past Fight Matrix snapshots (see scripts/backtest_prospects.py).

For each snapshot date: the ranked fighters who were prospects by our rules on that date,
the score's inputs rebuilt as of that date from their Fight Matrix histories, and what
happened in the next four years. "Made it" = won a bout in a major promotion (UFC, PFL,
Bellator, ONE, ACA, RIZIN; not the Contender Series or Road to UFC) within four years.
"""

from __future__ import annotations

import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from . import prospects as PR

COMPONENTS = ("rating", "winning", "finishing", "youth", "activity")
CURRENT = {"rating": 0.50, "winning": 0.15, "finishing": 0.10, "youth": 0.10, "activity": 0.05}
WINDOW_DAYS = 4 * 365


def _d(s) -> Optional[date]:
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def snapshot_pool(rows: List[dict], profiles: Dict[str, dict], cutoff: date) -> List[dict]:
    """Prospects on `cutoff` with their score inputs (as of then) and outcomes (after)."""
    pool = []
    for r in rows:
        prof = profiles.get(r["url"])
        if not prof:
            continue
        bouts = [dict(b, d=_d(b["date"])) for b in prof.get("bouts", []) if _d(b.get("date"))]
        before = [b for b in bouts if b["d"] < cutoff]
        after = [b for b in bouts if cutoff <= b["d"] < cutoff + timedelta(days=WINDOW_DAYS)]
        age = PR.age_on(prof.get("stats", {}).get("Birth Date") or None, cutoff)
        if not before or age is None or age >= PR.MAX_AGE or len(before) >= PR.MAX_FIGHTS:
            continue
        if any(PR.is_major(b["event"]) for b in before):
            continue
        last = max(b["d"] for b in before)
        if (cutoff - last).days > 730:
            continue
        w = sum(b["result"] == "W" for b in before)
        l_ = sum(b["result"] == "L" for b in before)
        d_ = sum(b["result"] == "D" for b in before)
        wins = [b for b in before if b["result"] == "W"]
        fin = sum(1 for b in wins if not str(b.get("method", "")).upper().startswith("DEC")) / len(wins) if wins else 0.0
        n = w + l_ + d_
        pool.append({
            "name": r["name"], "url": r["url"], "division": r["division"], "fm_rank": r["rank"], "rating": r["points"],
            "age": round(age, 1), "wins": w, "losses": l_, "draws": d_, "finish_rate": fin,
            "days_since": (cutoff - last).days, "n": n,
            "made_it": any(b["result"] == "W" and PR.is_major(b["event"]) for b in after),
            "reached": any(PR.is_major(b["event"]) for b in after),
        })
    _components(pool)
    return pool


def _components(pool: List[dict]) -> None:
    """The live score's components (prospects.score_pool), buzz left out: there's no buzz history."""
    by_div: Dict[str, List[dict]] = {}
    for p in pool:
        by_div.setdefault(p["division"], []).append(p)
    for ps in by_div.values():
        ratings = sorted(p["rating"] for p in ps)
        for p in ps:
            pct = 0.5 if len(ratings) < 2 else sum(x < p["rating"] for x in ratings) / (len(ratings) - 1)
            win = (p["wins"] + 1) / (p["n"] + 2) + (0.08 if p["losses"] == 0 and p["wins"] >= 5 else 0)
            p["c"] = {"rating": pct, "winning": min(1.0, win), "finishing": p["finish_rate"],
                      "youth": max(0.0, min(1.0, (PR.MAX_AGE - p["age"]) / 7)), "activity": 1.0 if p["days_since"] <= 365 else 0.4}


def score(p: dict, weights: Dict[str, float]) -> float:
    return sum(weights[k] * p["c"][k] for k in COMPONENTS)


def auc(pool: List[dict], key, target: str = "made_it") -> float:
    """Chance a random fighter who made it outscores a random one who didn't."""
    pos = [key(p) for p in pool if p[target]]
    neg = [key(p) for p in pool if not p[target]]
    if not pos or not neg:
        return float("nan")
    wins = sum((a > b) + 0.5 * (a == b) for a in pos for b in neg)
    return wins / (len(pos) * len(neg))


def top_rate(pool: List[dict], key, k: int, target: str = "made_it") -> float:
    top = sorted(pool, key=key, reverse=True)[:k]
    return sum(p[target] for p in top) / len(top) if top else float("nan")


def fit_logistic(pool: List[dict], l2: float = 1.0, iterations: int = 50) -> Dict[str, float]:
    """Logistic regression of made_it on the components (Newton, light L2 so a small sample can't run away)."""
    X = [[1.0] + [p["c"][k] for k in COMPONENTS] for p in pool]
    y = [1.0 if p["made_it"] else 0.0 for p in pool]
    k = len(X[0])
    w = [0.0] * k
    for _ in range(iterations):
        g = [l2 * w[i] * (i > 0) for i in range(k)]
        H = [[(l2 if i == j and i > 0 else 0.0) + (1e-9 if i == j else 0.0) for j in range(k)] for i in range(k)]
        for x, t in zip(X, y):
            q = 1 / (1 + math.exp(-sum(a * b for a, b in zip(w, x))))
            for i in range(k):
                g[i] += (q - t) * x[i]
                for j in range(k):
                    H[i][j] += q * (1 - q) * x[i] * x[j]
        A = [row[:] + [g[i]] for i, row in enumerate(H)]
        for c in range(k):
            piv = max(range(c, k), key=lambda r: abs(A[r][c]))
            A[c], A[piv] = A[piv], A[c]
            for r in range(k):
                if r != c:
                    f = A[r][c] / A[c][c]
                    A[r] = [a - f * b for a, b in zip(A[r], A[c])]
        w = [wi - A[i][k] / A[i][i] for i, wi in enumerate(w)]
    return {"intercept": w[0], **{c: w[i + 1] for i, c in enumerate(COMPONENTS)}}


def as_mix(coef: Dict[str, float], total: float = 0.90) -> Dict[str, float]:
    """Logistic coefficients -> score weights: the positive ones, rescaled to `total` (buzz keeps the rest)."""
    pos = {k: max(0.0, coef[k]) for k in COMPONENTS}
    s = sum(pos.values()) or 1.0
    return {k: round(total * v / s, 3) for k, v in pos.items()}


def run(out_dir: Path) -> Dict[str, object]:
    profiles = {}
    for src in (Path("data/fightmatrix/profiles.jsonl"), out_dir / "profiles.jsonl"):
        if src.exists():
            for line in src.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    profiles[r["url"]] = r
    pools = {}
    for snap in sorted(out_dir.glob("snapshot_*.jsonl")):
        when = date.fromisoformat(snap.stem.split("_")[1])
        rows = [json.loads(l) for l in snap.read_text(encoding="utf-8").splitlines() if l.strip()]
        pools[when.isoformat()] = snapshot_pool(rows, profiles, when)
    (fit_on, fit_pool), (test_on, test_pool) = sorted(pools.items())[:2]
    cur = {k: v / 0.9 for k, v in CURRENT.items()}  # same ranking as the live score without buzz
    coef = fit_logistic(fit_pool)
    mix = as_mix(coef)
    fitted = {k: v / 0.9 for k, v in mix.items()}
    report = {"window_years": WINDOW_DAYS // 365, "target": "won a bout in a major promotion within the window"}
    for when, pool in pools.items():
        report[when] = {
            "prospects": len(pool), "made_it": sum(p["made_it"] for p in pool), "reached": sum(p["reached"] for p in pool),
            "base_rate": round(sum(p["made_it"] for p in pool) / len(pool), 3) if pool else None,
            "auc_current": round(auc(pool, lambda p: score(p, cur)), 3),
            "auc_fitted": round(auc(pool, lambda p: score(p, fitted)), 3),
            "auc_by_component": {k: round(auc(pool, lambda p, k=k: p["c"][k]), 3) for k in COMPONENTS},
            "top50_current": round(top_rate(pool, lambda p: score(p, cur), 50), 3),
            "top50_fitted": round(top_rate(pool, lambda p: score(p, fitted), 50), 3),
        }
    report["fitted_on"], report["tested_on"] = fit_on, test_on
    report["coefficients"] = {k: round(v, 3) for k, v in coef.items()}
    report["current_mix"], report["fitted_mix"] = CURRENT, mix
    # Refit on both snapshots for the weights we'd actually use, if the test says the fit is better.
    report["final_mix"] = as_mix(fit_logistic(fit_pool + test_pool))
    (out_dir / "report.json").write_text(json.dumps(report, indent=1))
    return report
