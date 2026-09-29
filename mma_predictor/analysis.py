"""What actually decides fights, and where the model is wrong about it.

Two views of past UFC bouts, both built from point-in-time data (only what
was known before each fight):

1. Regression. Logistic regression of the result on every matchup feature,
   standardised so effects are comparable ("one standard deviation more of
   this factor shifts the log-odds by b"), with standard errors from the
   Fisher information and two-sided p-values.

2. Matchup patterns. Readable situations (clear wrestling edge, big age gap,
   coming off a KO loss, long layoff...). For each: how often the fighter
   with the edge won, against how often the model, predicting *before* the
   fight in the walk-forward backtest, expected them to. A positive gap means
   the model underrates that edge; a negative gap means it overrates it.
   z = (wins - expected wins) / sqrt(sum p(1-p)) says whether the gap is
   more than noise.

Scheduled bouts are then flagged with the patterns they match.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .data import Fight, Method
from .features import FEATURE_LABELS, FEATURES, BoutContext, wear_index
from .history import FightHistory, FighterSnapshot
from .model import sigmoid

Side = int  # +1: fighter A has the trait, -1: fighter B, 0: neither


def _ufc_bouts(s: FighterSnapshot) -> int:
    return sum(1 for a in s.all_appearances if a.fight.event.lower().startswith("ufc"))


def _last_was_ko_loss(s: FighterSnapshot) -> bool:
    scored = [a for a in s.all_appearances if a.result is not None]
    return bool(scored) and scored[-1].result is False and scored[-1].method is Method.KO


def _sign(v: float, threshold: float) -> Side:
    return 1 if v >= threshold else -1 if v <= -threshold else 0


def _pair(cond_a: bool, cond_b: bool) -> Side:
    """Trait on exactly one side."""
    return 1 if cond_a and not cond_b else -1 if cond_b and not cond_a else 0


@dataclass(frozen=True)
class Pattern:
    key: str
    label: str
    side_label: str  # who "the side" is
    test: Callable[[FighterSnapshot, FighterSnapshot, Dict[str, float], BoutContext], Side]
    # Plain-English specifics for one bout: (fighter with the edge, opponent) -> text.
    detail: Optional[Callable[[FighterSnapshot, FighterSnapshot], str]] = None
    # Depends on a fighter's full record (layoff, streak, last result...), so it
    # only fires when both fighters' own pages are in the data.
    needs_full_record: bool = False


def _both_complete(a: FighterSnapshot, b: FighterSnapshot) -> bool:
    return a.bio.complete and b.bio.complete


def _last_fight(s: FighterSnapshot) -> str:
    return s.all_appearances[-1].fight.date.strftime("%b %Y") if s.all_appearances else "?"


def _last_opponent(s: FighterSnapshot) -> str:
    return s.all_appearances[-1].opponent if s.all_appearances else "?"


def _grappler(s: FighterSnapshot) -> bool:
    return s.grappling - s.striking >= 80


def _striker(s: FighterSnapshot) -> bool:
    return s.striking - s.grappling >= 80


def _pedigree(s: FighterSnapshot) -> float:
    return max(s.pedigree.values()) if s.pedigree else 0.0


PATTERNS: List[Pattern] = [
    Pattern("rating_gap", "Ranking favourite by 150+", "higher-ranked fighter",
            lambda a, b, x, c: _sign(a.proven - b.proven, 150),
            lambda w, l: f"{w.name} ranks {w.proven - l.proven:.0f} points above {l.name}"),
    Pattern("close_ratings", "Near-even ratings (within 40)", "fighter the model picks",
            lambda a, b, x, c: (1 if a.proven >= b.proven else -1) if abs(a.proven - b.proven) < 40 else 0,
            lambda w, l: f"{w.name} and {l.name} are within {abs(w.proven - l.proven):.0f} rating points"),
    Pattern("wrestling_edge", "Clear wrestling edge", "better wrestler",
            lambda a, b, x, c: _sign(x["wrestling_rating"], 0.25),
            lambda w, l: f"{w.name} has the clear wrestling edge over {l.name}"),
    Pattern("striking_edge", "Clear striking edge", "better striker",
            lambda a, b, x, c: _sign(x["striking_rating"], 0.25),
            lambda w, l: f"{w.name} has the clear striking edge over {l.name}"),
    Pattern("grappling_edge", "Clear grappling edge", "better grappler",
            lambda a, b, x, c: _sign(x["grappling_rating"], 0.25),
            lambda w, l: f"{w.name} has the clear grappling edge over {l.name}"),
    Pattern("grappler_vs_striker", "Grappler vs striker", "grappler",
            lambda a, b, x, c: _pair(_grappler(a) and _striker(b), _grappler(b) and _striker(a)),
            lambda w, l: f"{w.name} (grappler) vs {l.name} (striker)"),
    Pattern("power_vs_chin", "Power vs a compromised chin", "puncher",
            lambda a, b, x, c: _sign(x["power_vs_chin"], 0.4),
            lambda w, l: f"{w.name}'s power against {l.name}'s chin ({l.ko_losses} KO/TKO losses on record)"),
    Pattern("off_ko_loss", "Opponent coming off a KO/TKO loss", "fighter whose opponent was just knocked out",
            lambda a, b, x, c: _pair(_last_was_ko_loss(b), _last_was_ko_loss(a)),
            lambda w, l: f"{l.name} was knocked out last time ({_last_opponent(l)}, {_last_fight(l)})", True),
    Pattern("age_gap", "Age gap 6+ years, older fighter 34+", "younger fighter",
            lambda a, b, x, c: (_sign((b.age or 0) - (a.age or 0), 6)
                                if a.age and b.age and max(a.age, b.age) >= 34 else 0),
            lambda w, l: f"{l.name} is {l.age:.0f}, {l.age - w.age:.0f} years older than {w.name}"),
    Pattern("wear_gap", "Much fresher (wear and tear)", "fresher fighter",
            lambda a, b, x, c: _sign(wear_index(b) - wear_index(a), 2.0),
            lambda w, l: f"{l.name} carries far more wear ({wear_index(l):.1f} vs {wear_index(w):.1f})", True),
    Pattern("layoff", "Opponent out 18+ months", "active fighter",
            lambda a, b, x, c: _pair((b.layoff_days or 0) >= 540 and (a.layoff_days or 0) <= 365,
                                     (a.layoff_days or 0) >= 540 and (b.layoff_days or 0) <= 365),
            lambda w, l: f"{l.name} has been out {(l.layoff_days or 0) // 30} months (last fight {_last_fight(l)}); {w.name} fought {_last_fight(w)}", True),
    Pattern("streak_vs_skid", "Win streak 3+ vs losing record lately", "fighter on the streak",
            lambda a, b, x, c: _pair(a.streak >= 3 and b.streak <= 0, b.streak >= 3 and a.streak <= 0),
            lambda w, l: f"{w.name} has won {w.streak} straight; {l.name} " + (f"has lost {-l.streak} straight" if l.streak < 0 else "lost last time"), True),
    Pattern("ufc_newcomer", "UFC veteran vs newcomer", "UFC veteran (5+ UFC bouts)",
            lambda a, b, x, c: _pair(_ufc_bouts(a) >= 5 and _ufc_bouts(b) <= 1, _ufc_bouts(b) >= 5 and _ufc_bouts(a) <= 1),
            lambda w, l: f"{w.name} has {_ufc_bouts(w)} UFC bouts; {l.name} has {_ufc_bouts(l)}", True),
    Pattern("reach", "Reach advantage 10 cm+", "longer fighter",
            lambda a, b, x, c: (_sign(a.bio.reach_cm - b.bio.reach_cm, 10) if a.bio.reach_cm and b.bio.reach_cm else 0),
            lambda w, l: f"{w.name} has {w.bio.reach_cm - l.bio.reach_cm:.0f} cm more reach than {l.name}"),
    Pattern("southpaw", "Southpaw vs orthodox", "southpaw",
            lambda a, b, x, c: _sign(x["stance"], 1),
            lambda w, l: f"{w.name} is a southpaw facing orthodox {l.name}"),
    Pattern("cardio_5r", "Five rounds with a cardio edge", "better late-round fighter",
            lambda a, b, x, c: _sign(x["cardio"], 0.4) if c.scheduled_rounds >= 5 else 0,
            lambda w, l: f"Five rounds: {w.name} wins {w.late_win_rate:.0%} of fights that go past round 2, {l.name} {l.late_win_rate:.0%}"),
    Pattern("pedigree", "Elite pedigree vs none", "fighter with the pedigree",
            lambda a, b, x, c: _pair(_pedigree(a) >= 60 and _pedigree(b) < 10, _pedigree(b) >= 60 and _pedigree(a) < 10),
            lambda w, l: f"{w.name} has an elite pre-MMA pedigree; {l.name} has none on record"),
]
PATTERN_BY_KEY = {p.key: p for p in PATTERNS}


def match_patterns(a: FighterSnapshot, b: FighterSnapshot, x: Dict[str, float], ctx: BoutContext) -> List[Tuple[str, Side]]:
    out = []
    complete = _both_complete(a, b)
    for p in PATTERNS:
        if p.needs_full_record and not complete:
            continue
        side = p.test(a, b, x, ctx)
        if side:
            out.append((p.key, side))
    return out


def describe(key: str, side: Side, a: FighterSnapshot, b: FighterSnapshot) -> str:
    pat = PATTERN_BY_KEY[key]
    w, l = (a, b) if side > 0 else (b, a)
    if pat.detail is None:
        return f"{w.name}: {pat.label.lower()}"
    try:
        return pat.detail(w, l)
    except (TypeError, ValueError):
        return f"{w.name}: {pat.label.lower()}"


# ----------------------------------------------------------------- statistics
def _wilson(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def _p_value(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2))


def pattern_table(history: FightHistory, predictions: Sequence[Tuple[Fight, float, dict]]) -> List[Dict[str, object]]:
    """Actual vs model-expected win rate for the side with each trait."""
    acc: Dict[str, Dict[str, object]] = {p.key: {"n": 0, "wins": 0, "expected": 0.0, "var": 0.0, "examples": []} for p in PATTERNS}
    for f, p_a, x in predictions:
        if not f.is_scored:
            continue
        sa, sb = history.snapshot(f.fighter_a, f.date), history.snapshot(f.fighter_b, f.date)
        a_won = f.winner == f.fighter_a
        for key, side in match_patterns(sa, sb, x, BoutContext(f.scheduled_rounds, f.title_fight)):
            row = acc[key]
            p = p_a if side > 0 else 1 - p_a
            won = a_won if side > 0 else not a_won
            row["n"] += 1
            row["wins"] += int(won)
            row["expected"] += p
            row["var"] += p * (1 - p)
            ex = row["examples"]
            ex.append({"date": f.date.isoformat(), "side": f.fighter_a if side > 0 else f.fighter_b,
                       "opponent": f.fighter_b if side > 0 else f.fighter_a, "won": won, "p": round(p, 3), "event": f.event})
    out = []
    for pat in PATTERNS:
        row = acc[pat.key]
        n = int(row["n"])
        if n == 0:
            out.append({"key": pat.key, "label": pat.label, "side": pat.side_label, "n": 0})
            continue
        wins, expected, var = int(row["wins"]), float(row["expected"]), float(row["var"])
        z = (wins - expected) / math.sqrt(var) if var > 0 else 0.0
        lo, hi = _wilson(wins, n)
        verdict = "not enough bouts"
        if n >= 20:
            if z >= 2:
                verdict = "model underrates"
            elif z <= -2:
                verdict = "model overrates"
            elif abs(z) >= 1.5:
                verdict = "leaning " + ("underrated" if z > 0 else "overrated")
            else:
                verdict = "well calibrated"
        out.append({
            "key": pat.key, "label": pat.label, "side": pat.side_label, "n": n,
            "win_rate": wins / n, "expected": expected / n, "gap": (wins - expected) / n,
            "ci": [lo, hi], "z": z, "p": _p_value(z), "verdict": verdict,
            "examples": sorted(row["examples"], key=lambda e: e["date"], reverse=True)[:8],
        })
    return out


# ------------------------------------------------------------------ regression
def _solve(A: List[List[float]], b: List[float]) -> List[float]:
    """Gauss-Jordan with partial pivoting (small dense systems)."""
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[piv] = M[piv], M[c]
        if abs(M[c][c]) < 1e-12:
            continue
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                for k in range(c, n + 1):
                    M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] if abs(M[i][i]) > 1e-12 else 0.0 for i in range(n)]


def _inverse(A: List[List[float]]) -> List[List[float]]:
    n = len(A)
    cols = [_solve(A, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)]
    return [[cols[j][i] for j in range(n)] for i in range(n)]


def regression(X: Sequence[Dict[str, float]], y: Sequence[int], ridge: float = 1e-3, iterations: int = 25) -> List[Dict[str, object]]:
    """Standardised logistic regression (no intercept: features are antisymmetric)."""
    names = [k for k in FEATURES if any(abs(x.get(k, 0.0)) > 1e-12 for x in X)]
    n = len(X)
    sd = {k: math.sqrt(sum(x.get(k, 0.0) ** 2 for x in X) / n) or 1.0 for k in names}
    rows = [[x.get(k, 0.0) / sd[k] for k in names] for x in X]
    m = len(names)
    w = [0.0] * m
    H = [[0.0] * m for _ in range(m)]
    for _ in range(iterations):
        g = [-ridge * wi for wi in w]
        H = [[ridge if i == j else 0.0 for j in range(m)] for i in range(m)]
        for r, label in zip(rows, y):
            p = sigmoid(sum(wi * xi for wi, xi in zip(w, r)))
            err = label - p
            v = p * (1 - p)
            for i in range(m):
                g[i] += err * r[i]
                vi = v * r[i]
                for j in range(i, m):
                    H[i][j] += vi * r[j]
        for i in range(m):
            for j in range(i):
                H[i][j] = H[j][i]
        step = _solve(H, g)
        w = [wi + si for wi, si in zip(w, step)]
        if max(abs(s) for s in step) < 1e-7:
            break
    cov = _inverse(H)
    out = []
    for i, k in enumerate(names):
        se = math.sqrt(max(cov[i][i], 1e-12))
        z = w[i] / se
        out.append({"feature": k, "label": FEATURE_LABELS.get(k, k), "coef_per_sd": w[i], "se": se, "z": z,
                    "p": _p_value(z), "odds_ratio_per_sd": math.exp(w[i]), "sd": sd[k]})
    return sorted(out, key=lambda r: -abs(float(r["z"])))


def calibration_bands(predictions: Sequence[Tuple[Fight, float, dict]], width: float = 0.05) -> List[Dict[str, float]]:
    """Out-of-sample hit rate of the favourite, by how confident the model was."""
    bands: Dict[int, List[int]] = {}
    for f, p, _ in predictions:
        if not f.is_scored:
            continue
        fav = max(p, 1 - p)
        idx = min(int((fav - 0.5) / width), int(0.5 / width) - 1)
        hit = int((p >= 0.5) == (f.winner == f.fighter_a))
        bands.setdefault(idx, [0, 0])
        bands[idx][0] += 1
        bands[idx][1] += hit
    out = []
    for idx in sorted(bands):
        n, hits = bands[idx]
        lo, hi = _wilson(hits, n)
        out.append({"from": 0.5 + idx * width, "to": 0.5 + (idx + 1) * width, "n": n, "hit_rate": hits / n, "ci": [lo, hi]})
    return out


def insights(history: FightHistory, predictions, X_all, y_all) -> Dict[str, object]:
    return {
        "regression": regression(X_all, y_all),
        "patterns": pattern_table(history, predictions),
        "calibration": calibration_bands(predictions),
        "n_bouts": len(predictions),
        "n_regression": len(X_all),
    }


def upcoming_flags(history: FightHistory, a: str, b: str, rounds: int, when=None) -> List[Tuple[str, Side, str]]:
    from .features import matchup_features

    sa, sb = history.snapshot(a, when), history.snapshot(b, when)
    ctx = BoutContext(rounds)
    return [(k, s, describe(k, s, sa, sb)) for k, s in match_patterns(sa, sb, matchup_features(sa, sb, ctx), ctx)]
