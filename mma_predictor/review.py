"""Post-card model review: re-test the model's weak spots on every UFC bout so far and switch a setting only when
the out-of-sample test says the new one is better.

Three studies, all on .cache/review/bouts.jsonl (review_data.py: walk-forward win chances, the method model's
chance of a decision, closing lines, both fighters' traits before the bout):

1. Decision chance. The candidates are the current correction, a straight refit, a refit that weights recent
   years more (a trend), and a refit that also knows how lopsided the matchup is (matchmaking: mismatches end
   early). Each is fitted on the years before a test year and scored on that year (rolling origin, 2021 on).
   A new method replaces the current one only if it beats it pooled (by MIN_GAIN) and in at least half the
   test years; the chosen method is refitted on every bout after each card.
2. Veterans. Whether the model under- or over-rates fighters 35 and older against younger opponents; a shift
   on the win chance is adopted the same way (rolling origin, must beat no shift).
3. Underdogs. Who wins as an underdog more than the line says, by trait, with each pattern checked in three
   separate eras so one hot season doesn't count as a finding, plus the flat-stake return at the closing price.

4. Pre-fight claims vs the fights: the Sunday review's per-bout checks (fight_recaps.py) tallied by factor.

    python -m mma_predictor model-review            # writes data/analysis/review.json (+ a line in review_log.jsonl)
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "analysis" / "review.json"
LOG = ROOT / "data" / "analysis" / "review_log.jsonl"
CALIBRATION = ROOT / "data" / "ai_picks" / "calibration.json"
TEST_FROM = 2021
ERAS = (("2016-2019", 2016, 2019), ("2020-2022", 2020, 2022), ("2023-2026", 2023, 2026))
EPS = 1e-6
MIN_GAIN = 0.0005  # pooled log-loss gain a new setting needs (noise between candidates is about 0.0002)


def _logit(p: float) -> float:
    p = min(1 - EPS, max(EPS, p))
    return math.log(p / (1 - p))


def _sig(z: float) -> float:
    return 1 / (1 + math.exp(-z)) if z > -40 else 0.0


def _ll(p: float, y: int) -> float:
    p = min(1 - EPS, max(EPS, p))
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def logistic(X: Sequence[Sequence[float]], y: Sequence[int], w: Optional[Sequence[float]] = None,
             start: Optional[Sequence[float]] = None, l2: float = 1e-3, iterations: int = 50) -> List[float]:
    """Newton-fitted logistic regression (X rows include their own intercept column)."""
    k = len(X[0])
    beta = list(start) if start else [0.0] * k
    w = w or [1.0] * len(X)
    for _ in range(iterations):
        g = [l2 * b for b in beta]
        H = [[(l2 if i == j else 0.0) for j in range(k)] for i in range(k)]
        for xi, yi, wi in zip(X, y, w):
            q = _sig(sum(b * v for b, v in zip(beta, xi)))
            for i in range(k):
                g[i] += wi * (q - yi) * xi[i]
                for j in range(i, k):
                    H[i][j] += wi * q * (1 - q) * xi[i] * xi[j]
        for i in range(k):
            for j in range(i):
                H[i][j] = H[j][i]
        step = _solve(H, g)
        beta = [b - s for b, s in zip(beta, step)]
        if max(abs(s) for s in step) < 1e-8:
            break
    return beta


def _solve(A: List[List[float]], b: List[float]) -> List[float]:
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c and M[c][c]:
                f = M[r][c] / M[c][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] if M[i][i] else 0.0 for i in range(n)]


def _std_errors(X, y, beta) -> List[float]:
    k = len(beta)
    H = [[0.0] * k for _ in range(k)]
    for xi in X:
        q = _sig(sum(b * v for b, v in zip(beta, xi)))
        for i in range(k):
            for j in range(k):
                H[i][j] += q * (1 - q) * xi[i] * xi[j]
    out = []
    for i in range(k):
        e = [1.0 if j == i else 0.0 for j in range(k)]
        col = _solve([r[:] for r in H], e)
        out.append(math.sqrt(max(col[i], 0.0)))
    return out


def _year(r) -> int:
    return int(r["date"][:4])


def mismatch(r: dict, source: str = "market") -> float:
    """How lopsided the bout is: |logit| of the favourite's chance (closing line, else our model)."""
    p = r["market"] if source == "market" and r.get("market") is not None else r["pa"]
    return abs(_logit(p))


# ------------------------------------------------------------------ 1. decision chance
def _dec_candidates(current: Optional[Sequence[float]]):
    """name -> (fit(train_rows) -> params, predict(params, row) -> P(decision))."""
    def base_x(r):
        return [1.0, _logit(r["pdec_raw"])]

    def fit_plain(rows, weights=None):
        return logistic([base_x(r) for r in rows], [r["dec"] for r in rows], weights, start=[0.0, 1.0])

    def fit_recent(rows):
        last = max(_year(r) for r in rows)
        return fit_plain(rows, [0.5 ** ((last - _year(r)) / 2.0) for r in rows])  # two-year half-life

    def mx(source):
        def fit(rows):
            return logistic([base_x(r) + [mismatch(r, source)] for r in rows], [r["dec"] for r in rows], start=[0.0, 1.0, 0.0])

        def pred(b, r):
            return _sig(b[0] + b[1] * _logit(r["pdec_raw"]) + b[2] * mismatch(r, source))
        return fit, pred

    plain_pred = lambda b, r: _sig(b[0] + b[1] * _logit(r["pdec_raw"]))  # noqa: E731
    out = {
        "raw (no correction)": (lambda rows: None, lambda b, r: r["pdec_raw"]),
        "refit, all years equal": (fit_plain, plain_pred),
        "refit, recent years weighted": (fit_recent, plain_pred),
        "refit + matchup mismatch (model)": mx("model"),
        "refit + matchup mismatch (line, else model)": mx("market"),
    }
    if current:
        out["current"] = (lambda rows: list(current), lambda b, r: _sig(b[0] + b[1] * _logit(r["pdec_raw"])) if len(b) == 2
                          else _sig(b[0] + b[1] * _logit(r["pdec_raw"]) + b[2] * mismatch(r, "market")))
    return out


def rolling(rows: List[dict], fit: Callable, pred: Callable, label: str, test_from: int = TEST_FROM) -> Dict[str, object]:
    years = sorted({_year(r) for r in rows if _year(r) >= test_from})
    per, tot, n = {}, 0.0, 0
    for yr in years:
        train = [r for r in rows if _year(r) < yr]
        test = [r for r in rows if _year(r) == yr]
        params = fit(train)
        ll = sum(_ll(pred(params, r), r[label]) for r in test)
        per[yr] = {"n": len(test), "log_loss": round(ll / len(test), 4),
                   "predicted": round(sum(pred(params, r) for r in test) / len(test), 4),
                   "actual": round(sum(r[label] for r in test) / len(test), 4)}
        tot += ll
        n += len(test)
    return {"log_loss": round(tot / n, 5), "n": n, "by_year": per}


# Methods pricing can run (picks.dec_chance), by the parameter form they produce. The model-only mismatch
# variant is reported for comparison but not chosen: pricing uses the line whenever there is one.
KINDS = {"refit, all years equal": "plain", "refit, recent years weighted": "plain",
         "refit + matchup mismatch (line, else model)": "mismatch_line"}


def decision_study(rows: List[dict], current: Optional[Sequence[float]], method: str = "refit, all years equal") -> Dict[str, object]:
    cands = _dec_candidates(current)
    results = {name: rolling(rows, fit, pred, "dec") for name, (fit, pred) in cands.items()}
    # Matchmaking or a real trend? Decision rate by year within mismatch bands (closing line where there is one).
    bands = ((0, 0.4, "close (fav under ~60%)"), (0.4, 1.0, "clear fav (60-73%)"), (1.0, 99, "mismatch (fav over 73%)"))
    by_year = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    share = defaultdict(lambda: [0, 0])
    for r in rows:
        if r.get("market") is None:
            continue
        m = mismatch(r)
        band = next(lbl for lo, hi, lbl in bands if lo <= m < hi)
        cell = by_year[_year(r)][band]
        cell[0] += 1
        cell[1] += r["dec"]
        share[_year(r)][0] += 1
        share[_year(r)][1] += m >= 1.0
    table = {yr: {"bouts": share[yr][0], "mismatch_share": round(share[yr][1] / share[yr][0], 3),
                  "decision_rate": {b: (round(c[1] / c[0], 3) if c[0] else None) for b, c in by_year[yr].items()},
                  "n": {b: c[0] for b, c in by_year[yr].items()}} for yr in sorted(by_year)}
    best = min((k for k in results if k not in ("current", "refit, all years equal")), key=lambda k: results[k]["log_loss"])
    # The current correction was fitted on every year including the test years, so its own score here is
    # in-sample and flattering. The fair yardstick for "keep things as they are" is the current *method*
    # refitted out of sample; a different method has to beat that, pooled and in at least half the test years.
    method = method if method in KINDS else "refit, all years equal"
    cur = results[method]
    best = min(KINDS, key=lambda k: results[k]["log_loss"])
    years = cur["by_year"].keys()
    wins = sum(results[best]["by_year"][y]["log_loss"] < cur["by_year"][y]["log_loss"] for y in years)
    improves = best != method and results[best]["log_loss"] < cur["log_loss"] - MIN_GAIN and wins * 2 >= len(years)
    keep = best if improves else method
    return {"candidates": results, "best": best, "method": method, "current_log_loss": cur["log_loss"],
            "best_log_loss": results[best]["log_loss"], "years_won": f"{wins}/{len(years)}", "improves": improves,
            "chosen": keep, "chosen_params": cands[keep][0](rows), "by_year_mismatch": table}


# ------------------------------------------------------------------ 2. veterans
def veteran_study(rows: List[dict], age: float = 35.0) -> Dict[str, object]:
    """Shift on the win chance when one fighter is `age`+ and the other younger: fitted and tested rolling."""
    def flag(r):
        aa, ab = r["sa"].get("age"), r["sb"].get("age")
        if aa is None or ab is None:
            return 0
        return (aa >= age and ab < age) - (ab >= age and aa < age)  # +1 when a is the veteran

    use = [r for r in rows if r["sa"].get("age") and r["sb"].get("age")]
    X = lambda r: [_logit(r["pa"]), float(flag(r))]  # noqa: E731

    def fit(train):
        # Offset logistic: only the shift is fitted; the model's own chance stays as is (coefficient 1).
        k = 0.0
        for _ in range(30):
            g = h = 0.0
            for r in train:
                z, f = X(r)
                if not f:
                    continue
                q = _sig(z + k * f)
                g += (q - r["y"]) * f
                h += q * (1 - q) * f * f
            if h <= 0:
                break
            k -= g / (h + 1e-9)
        return k

    shifted = rolling(use, fit, lambda k, r: _sig(_logit(r["pa"]) + k * flag(r)), "y")
    none = rolling(use, lambda t: 0.0, lambda k, r: r["pa"], "y")
    wins = sum(shifted["by_year"][y]["log_loss"] < none["by_year"][y]["log_loss"] for y in none["by_year"])
    vets = [r for r in use if flag(r)]
    won = sum((r["y"] == 1) == (flag(r) > 0) for r in vets)
    model_p = sum(r["pa"] if flag(r) > 0 else 1 - r["pa"] for r in vets)
    priced = [r for r in vets if r.get("market") is not None]
    by_era = {}
    for name, lo, hi in ERAS:
        e = [r for r in vets if lo <= _year(r) <= hi]
        if e:
            by_era[name] = {"n": len(e), "won": round(sum((r["y"] == 1) == (flag(r) > 0) for r in e) / len(e), 3),
                            "model": round(sum(r["pa"] if flag(r) > 0 else 1 - r["pa"] for r in e) / len(e), 3)}
    return {"age": age, "n": len(vets), "veteran_won": round(won / len(vets), 3), "model_gave": round(model_p / len(vets), 3),
            "market_gave": round(sum(r["market"] if flag(r) > 0 else 1 - r["market"] for r in priced) / max(1, len(priced)), 3),
            "by_era": by_era, "shift": round(fit(use), 4), "with_shift": shifted["log_loss"], "without": none["log_loss"],
            "years_won": f"{wins}/{len(none['by_year'])}",
            "improves": shifted["log_loss"] < none["log_loss"] - MIN_GAIN and wins * 2 >= len(none["by_year"]),
            "rolling": {"with": shifted, "without": none}}


# ------------------------------------------------------------------ 3. underdogs
def _diff(dog, fav, key):
    a, b = dog.get(key), fav.get(key)
    return None if a is None or b is None else a - b


UNDERDOG_TRAITS: Dict[str, Tuple[str, Callable]] = {
    # name: (description, f(dog, fav, row) -> value or None); buckets are the value's sign or tertiles
    "younger": ("dog is 4+ years younger", lambda d, f, r: None if _diff(d, f, "age") is None else _diff(d, f, "age") <= -4),
    "older": ("dog is 4+ years older", lambda d, f, r: None if _diff(d, f, "age") is None else _diff(d, f, "age") >= 4),
    "fav_35plus": ("favourite is 35+", lambda d, f, r: None if f.get("age") is None else f["age"] >= 35),
    "reach_edge": ("dog has 5+ cm more reach", lambda d, f, r: None if _diff(d, f, "reach_cm") is None else _diff(d, f, "reach_cm") >= 5),
    "fav_long_layoff": ("favourite out 400+ days", lambda d, f, r: None if f.get("layoff_days") is None else f["layoff_days"] >= 400),
    "dog_long_layoff": ("dog out 400+ days", lambda d, f, r: None if d.get("layoff_days") is None else d["layoff_days"] >= 400),
    "fav_recent_ko_loss": ("favourite was KO'd in the last 2 fights", lambda d, f, r: None if f.get("recent_ko_losses") is None else f["recent_ko_losses"] >= 1),
    "dog_wrestling_edge": ("dog takes down 1+ more per 15 min", lambda d, f, r: None if _diff(d, f, "td_per15") is None else _diff(d, f, "td_per15") >= 1),
    "dog_power_edge": ("dog lands more knockdowns per 15", lambda d, f, r: None if _diff(d, f, "kd_per15") is None else _diff(d, f, "kd_per15") > 0.2),
    "dog_on_streak": ("dog on a 3+ win streak", lambda d, f, r: None if d.get("streak") is None else d["streak"] >= 3),
    "fav_on_skid": ("favourite lost last fight", lambda d, f, r: None if f.get("streak") is None else f["streak"] < 0),
    "dog_more_experienced": ("dog has 5+ more pro fights", lambda d, f, r: None if _diff(d, f, "fights") is None else _diff(d, f, "fights") >= 5),
    "fav_ufc_newcomer": ("favourite has 2 or fewer fights in our data", lambda d, f, r: None if f.get("fights") is None else f["fights"] <= 2),
    "fav_chin_flags": ("favourite has 2+ career KO losses", lambda d, f, r: None if f.get("ko_losses") is None else f["ko_losses"] >= 2),
    "dog_better_sos": ("dog has faced tougher opposition", lambda d, f, r: None if _diff(d, f, "sos") is None else _diff(d, f, "sos") > 50),
    "model_likes_dog": ("our model gives the dog 5+ pts more than the line", lambda d, f, r: r["_model_dog"] - r["_mkt_dog"] >= 0.05),
    "model_hates_dog": ("our model gives the dog 5+ pts less than the line", lambda d, f, r: r["_model_dog"] - r["_mkt_dog"] <= -0.05),
    "grappler_dog_vs_striker": ("dog is the better wrestler, favourite the better striker",
                                lambda d, f, r: None if None in (_diff(d, f, "wrestling"), _diff(d, f, "striking")) else (_diff(d, f, "wrestling") > 30 and _diff(d, f, "striking") < -30)),
    "striker_dog_vs_grappler": ("dog is the better striker, favourite the better wrestler",
                                lambda d, f, r: None if None in (_diff(d, f, "wrestling"), _diff(d, f, "striking")) else (_diff(d, f, "striking") > 30 and _diff(d, f, "wrestling") < -30)),
    "dog_better_td_defense": ("dog stops 15+ pts more takedowns", lambda d, f, r: None if _diff(d, f, "td_def") is None else _diff(d, f, "td_def") >= 0.15),
    "dog_more_volume": ("dog lands 1+ more sig. strikes a minute", lambda d, f, r: None if _diff(d, f, "slpm") is None else _diff(d, f, "slpm") >= 1),
    "five_round_streak_dog": ("five-round bout and the dog is on a 3+ streak", lambda d, f, r: r["rounds"] == 5 and (d.get("streak") or 0) >= 3),
    "five_rounds": ("five-round bout", lambda d, f, r: r["rounds"] == 5),
    "small_dog": ("line has the dog at 35-45%", lambda d, f, r: 0.35 <= r["_mkt_dog"] < 0.45),
    "big_dog": ("line has the dog under 25%", lambda d, f, r: r["_mkt_dog"] < 0.25),
    "heavyweight": ("heavyweight bout", lambda d, f, r: "heavy" in (r.get("wc") or "").lower() and "light" not in (r.get("wc") or "").lower()),
    "women": ("women's bout", lambda d, f, r: "women" in (r.get("wc") or "").lower()),
}


def underdog_study(rows: List[dict], vig: float = 0.045) -> Dict[str, object]:
    """Underdog (closing line under 47%) results by trait. `return` is the flat-stake return at the closing
    price, approximated from the no-vig line less a typical margin."""
    dogs = []
    for r in rows:
        if r.get("market") is None or abs(r["market"] - 0.5) < 0.03:
            continue
        a_dog = r["market"] < 0.5
        d, f = (r["sa"], r["sb"]) if a_dog else (r["sb"], r["sa"])
        x = dict(r, _mkt_dog=r["market"] if a_dog else 1 - r["market"], _model_dog=r["pa"] if a_dog else 1 - r["pa"],
                 _won=int((r["y"] == 1) == a_dog), _d=d, _f=f)
        dogs.append(x)

    def summary(group):
        n = len(group)
        if not n:
            return None
        won = sum(x["_won"] for x in group)
        implied = sum(x["_mkt_dog"] for x in group)
        ret = sum((x["_won"] / (x["_mkt_dog"] * (1 + vig))) - 1 for x in group)
        return {"n": n, "won": round(won / n, 3), "line": round(implied / n, 3), "edge": round((won - implied) / n, 3),
                "return": round(ret / n, 3)}

    base = summary(dogs)
    out = {}
    for name, (desc, fn) in UNDERDOG_TRAITS.items():
        hit = [x for x in dogs if fn(x["_d"], x["_f"], x) is True]
        if len(hit) < 60:
            continue
        eras = {lbl: summary([x for x in hit if lo <= _year(x) <= hi]) for lbl, lo, hi in ERAS}
        signs = [e["edge"] > 0 for e in eras.values() if e and e["n"] >= 20]
        out[name] = dict(summary(hit), desc=desc, eras=eras,
                         consistent=(len(signs) == 3 and (all(signs) or not any(signs))))
    # Multivariate check: does the trait still matter once the line is known? logit(win) = a + b*logit(line) + c*trait
    for name, s in out.items():
        fn = UNDERDOG_TRAITS[name][1]
        use = [x for x in dogs if fn(x["_d"], x["_f"], x) is not None]
        X = [[1.0, _logit(x["_mkt_dog"]), float(fn(x["_d"], x["_f"], x) is True)] for x in use]
        yv = [x["_won"] for x in use]
        beta = logistic(X, yv, start=[0.0, 1.0, 0.0])
        se = _std_errors(X, yv, beta)
        s["coef"], s["z"] = round(beta[2], 3), round(beta[2] / se[2], 2) if se[2] else None
    # Trends: dog win rate by year against the line
    years = defaultdict(list)
    for x in dogs:
        years[_year(x)].append(x)
    return {"all": base, "by_year": {y: summary(v) for y, v in sorted(years.items())}, "traits": out}


# ------------------------------------------------------------------ 4. pre-fight claims vs the fights
def fight_checks() -> Dict[str, object]:
    """The Sunday review's checks (data/scouting/recaps/*.json, stories.*.checks): each pre-fight claim (Claude's pick,
    the scouting read, the model's biggest drivers) marked held / failed / mixed / untested against the play-by-play.
    Tallied by factor so a driver that keeps failing in the fights shows up before the backtest can see it."""
    by_tag: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    by_source: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    verdicts: Dict[str, int] = defaultdict(int)
    cards = bouts = 0
    for f in sorted((ROOT / "data" / "scouting" / "recaps").glob("*.json")):
        doc = json.loads(f.read_text())
        stories = [s for s in doc.get("stories", {}).values() if s.get("checks")]
        if not stories:
            continue
        cards += 1
        for st in stories:
            bouts += 1
            verdicts[st.get("verdict", "")] += 1
            for c in st["checks"]:
                by_tag[c.get("tag") or "other"][c["verdict"]] += 1
                by_source[c["by"]][c["verdict"]] += 1

    def rate(d):
        tested = d.get("held", 0) + d.get("failed", 0) + d.get("mixed", 0)
        return {**d, "tested": tested, "held_rate": round((d.get("held", 0) + 0.5 * d.get("mixed", 0)) / tested, 3) if tested else None}

    tags = {k: rate(dict(v)) for k, v in by_tag.items()}
    # A model driver that keeps failing in the fights gets a targeted backtest (like the wear and age caps tested
    # on 2026-10-12), never an automatic change: the fights are a few dozen claims, the backtest thousands of bouts.
    from .fight_recaps import FEATURE_TEXT
    watch = [k for k, v in tags.items() if k in FEATURE_TEXT and v["tested"] >= 10 and (v["held_rate"] or 0) < 0.4]
    return {"cards": cards, "bouts": bouts, "verdicts": dict(verdicts), "watch": watch,
            "by_source": {k: rate(dict(v)) for k, v in by_source.items()},
            "by_tag": dict(sorted(tags.items(), key=lambda kv: -kv[1]["tested"]))}


# ------------------------------------------------------------------ run
def run(rows: List[dict], adopt: bool = True, log=print) -> Dict[str, object]:
    cal = json.loads(CALIBRATION.read_text()) if CALIBRATION.exists() else {}
    dec = decision_study(rows, cal.get("dec_cal"), cal.get("method", "refit, all years equal"))
    vet = veteran_study(rows)
    dogs = underdog_study(rows)
    out = {"run": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "bouts": len(rows),
           "through": max(r["date"] for r in rows), "decision": dec, "veterans": vet, "underdogs": dogs,
           "checks": fight_checks(), "switched": []}
    kind = KINDS.get(dec["chosen"])
    if adopt and kind:
        # Every review refits the chosen method on all bouts so far (new cards included); the method itself
        # only changes when another one beat it out of sample (decision_study).
        old, old_kind, old_method = cal.get("dec_cal"), cal.get("dec_cal_kind", "plain"), cal.get("method")
        cal.update({"dec_cal": [round(v, 6) for v in dec["chosen_params"]], "dec_cal_kind": kind, "fitted_on": len(rows),
                    "method": dec["chosen"], "reviewed": out["run"][:10], "through": out["through"],
                    "evidence": {k: v["log_loss"] for k, v in dec["candidates"].items()}})
        if dec["chosen"] != old_method:
            cal.update({"previous": {"dec_cal": old, "dec_cal_kind": old_kind, "method": old_method}, "switched": out["run"][:10]})
            out["switched"].append(f"decision chance: {old_method or 'original correction'} -> {dec['chosen']} "
                                   f"({dec['current_log_loss']:.5f} -> {dec['best_log_loss']:.5f})")
        CALIBRATION.write_text(json.dumps(cal, indent=1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=str))
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"run": out["run"], "through": out["through"], "bouts": len(rows),
                             "decision": {"best": dec["best"], "current": dec["current_log_loss"], "best_ll": dec["best_log_loss"]},
                             "veterans": {k: vet[k] for k in ("n", "veteran_won", "model_gave", "with_shift", "without", "improves")},
                             "switched": out["switched"]}) + "\n")
    return out


APP = ROOT / "app" / "review.json"


def publish(out: Dict[str, object]) -> None:
    """The page's copy (Insights > Model review): the choice, the evidence, and the underdog patterns."""
    d, v, u = out["decision"], out["veterans"], out["underdogs"]
    slim = {
        "run": out["run"], "through": out["through"], "bouts": out["bouts"], "switched": out["switched"],
        "decision": {"chosen": d["chosen"], "years_won": d["years_won"], "improves": d["improves"],
                     "candidates": {k: {"log_loss": c["log_loss"], "y2026": c["by_year"].get(2026) or c["by_year"].get("2026")}
                                    for k, c in d["candidates"].items() if k != "current"},
                     "by_year_mismatch": d["by_year_mismatch"]},
        "veterans": {k: v[k] for k in ("age", "n", "veteran_won", "model_gave", "market_gave", "by_era", "shift", "with_shift", "without", "years_won", "improves")},
        "checks": out.get("checks") or fight_checks(),
        "underdogs": {"all": u["all"], "by_year": u["by_year"],
                      "traits": {k: {x: t[x] for x in ("desc", "n", "won", "line", "edge", "return", "z", "consistent", "eras")}
                                 for k, t in u["traits"].items()}},
    }
    APP.write_text(json.dumps(slim, default=str))


def cmd_model_review(args) -> int:
    from . import review_data

    if args.rebuild or not review_data.OUT.exists():
        review_data.build()
    out = run(review_data.load(), adopt=not args.no_adopt)
    publish(out)
    d, v = out["decision"], out["veterans"]
    print(f"Decision chance ({d['candidates'][d['best']]['n']} bouts tested, {TEST_FROM} on):")
    for k, c in sorted(d["candidates"].items(), key=lambda kv: kv[1]["log_loss"]):
        print(f"  {c['log_loss']:.5f}  {k}")
    print(f"Veterans 35+ vs younger: {v['n']} bouts, won {v['veteran_won']:.1%}, model gave {v['model_gave']:.1%}, "
          f"line gave {v['market_gave']:.1%}; shift {v['shift']:+.3f} -> {v['with_shift']:.5f} vs {v['without']:.5f}")
    print("Switched: " + (", ".join(out["switched"]) or "nothing (no candidate beat the current setting)"))
    return 0


def register(sub) -> None:
    p = sub.add_parser("model-review", help="post-card review: decision chance, veterans, underdogs (switch only if better)")
    p.add_argument("--rebuild", action="store_true", help="rebuild the per-bout dataset first (about 15 minutes)")
    p.add_argument("--no-adopt", action="store_true", help="report only; never change a setting")
    p.set_defaults(func=cmd_model_review)
