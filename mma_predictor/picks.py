"""AI Picks: a $100 FanDuel bankroll, bet weekly and tracked honestly.

Every Friday the bettor (Claude) looks at the weekend's UFC card and decides
what, if anything, to bet. This module is the bookkeeping around that
discretion:

- ``parse_event``: FanDuel's prices for every bout and prop on a
  BestFightOdds event page (FanDuel is one of the books BestFightOdds tracks).
- ``price_card``: a betting sheet. Every FanDuel market with our
  probability, FanDuel's no-vig probability, the edge, expected value and a
  Kelly stake. Win probability is the model/market blend the backtest found
  best (it beat the closing line alone on later bouts). Props the model
  can't be checked against are shrunk halfway to FanDuel's own price.
- ``Ledger``: bets are placed only at sheet prices, before the event, within
  the bankroll, and are graded from results that two sources agree on
  (Wikipedia's event page and Sherdog's fighter records).

The ledger lives in ``data/ai_picks/ledger.json`` (committed before the
fights, so the git history timestamps every bet) and is mirrored to the web
page's database for display.
"""

from __future__ import annotations

import html as htmllib
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .data import METHOD_BUCKETS, Fight, Method
from .model import sigmoid

FANDUEL = "21"  # BestFightOdds' column id for FanDuel
START_BANKROLL = 100.0
MIN_STAKE = 1.0  # below this the bankroll is treated as bust
ROUND_SECONDS = 300
PROP_SHRINK = 0.5  # weight on our number for props (the rest is FanDuel's no-vig price)


# ------------------------------------------------------------------ odds math
def decimal(american: float) -> float:
    return 1 + american / 100 if american > 0 else 1 + 100 / -american


def american(dec: float) -> int:
    return int(round((dec - 1) * 100)) if dec >= 2 else int(round(-100 / (dec - 1)))


def implied(american_odds: float) -> float:
    return 1 / decimal(american_odds)


def _logit(p: float) -> float:
    p = min(1 - 1e-6, max(1e-6, p))
    return math.log(p / (1 - p))


# --------------------------------------------------------- BestFightOdds page
def _text(s: str) -> str:
    s = re.sub(r'<a[^>]*bfo-admin-link[^>]*>.*?</a>', "", s, flags=re.S)
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def _odds(s: str) -> Optional[int]:
    s = s.strip().replace("−", "-")
    return int(s) if re.fullmatch(r"[+-]?\d+", s) else None


def parse_event(page: str, url: str = "", book: str = FANDUEL) -> Dict[str, object]:
    """One book's moneylines and props for every bout on a BestFightOdds event page."""
    title = re.search(r"<title>([^<]*)", page)
    name = re.sub(r"\s+Odds.*$", "", htmllib.unescape(title.group(1))).strip() if title else ""
    when = re.search(r'table-header-date">([^<]*)', page)
    tables = [m.start() for m in re.finditer(r"<table", page)]
    body = page[tables[1]:] if len(tables) > 1 else page
    body = body[:body.find("</table>")] if "</table>" in body else body
    bouts: Dict[str, Dict[str, object]] = {}
    order: List[str] = []
    for attrs, row in re.findall(r"<tr([^>]*)>(.*?)</tr>", body, re.S):
        th = re.search(r"<th[^>]*>(.*?)</th>", row, re.S)
        cells = re.findall(r'data-li="\[([^\]]*)\]"[^>]*>\s*<span[^>]*>([^<]*)</span>', row)
        mine = [(li.split(","), v) for li, v in cells if li.split(",")[0].strip() == book]
        mu_ids = {li.split(",")[2].strip() for li, _ in cells if len(li.split(",")) >= 3}
        if not th:
            continue
        label = _text(th.group(1))
        if 'class="pr"' not in attrs:
            # A fighter row: [book, side, matchup].
            link = re.search(r'href="(/fighters/[^"]+)"', th.group(1))
            mid = re.search(r'id="mu-(\d+)"', attrs)
            mu = next(iter(mu_ids), None) or (mid.group(1) if mid else None)
            if mu is None and order and len(bouts[order[-1]]["fighters"]) == 1:
                mu = order[-1]  # the second fighter of a bout with no prices at this book
            if mu is None:
                continue
            b = bouts.setdefault(mu, {"mu": mu, "fighters": [], "urls": [], "ml": {}, "props": []})
            if mu not in order:
                order.append(mu)
            b["fighters"].append(label)
            b["urls"].append("https://www.bestfightodds.com" + link.group(1) if link else "")
            if mine:
                b["ml"][label] = _odds(mine[0][1])
        else:
            mu = next(iter(mu_ids), None)
            if mu in bouts and mine:
                o = _odds(mine[0][1])
                if o is not None:
                    bouts[mu]["props"].append({"label": label, "odds": o})
    out = []
    for mu in order:
        b = bouts[mu]
        if len(b["fighters"]) != 2:
            continue
        fa, fb = b["fighters"]
        out.append({"mu": mu, "a": fa, "b": fb, "a_url": b["urls"][0], "b_url": b["urls"][1],
                    "ml": {"a": b["ml"].get(fa), "b": b["ml"].get(fb)}, "props": b["props"]})
    return {"name": name, "url": url, "date_label": when.group(1).strip() if when else "", "book": "FanDuel" if book == FANDUEL else book, "bouts": out}


def event_links(page: str) -> List[Tuple[str, str]]:
    """[(name, url)] of events listed on the BestFightOdds front page."""
    seen, out = set(), []
    for href, label in re.findall(r'href="(/events/[^"]+)"[^>]*>View ([^<]*?) Odds', page):
        if href not in seen:
            seen.add(href)
            out.append((label.strip(), "https://www.bestfightodds.com" + href))
    return out


# ------------------------------------------------------------- prop markets
def canonical(label: str, a: str, b: str, rounds: int) -> Optional[Tuple]:
    """A prop label -> a market we can price and grade, or None.

    Returns ("method", side, bucket) | ("itd", side) | ("win_round", side, k)
    | ("distance", yes) | ("total", over, line) | ("ends_round", k).
    """
    s = label.strip()
    s_low = s.lower()

    def side_of(prefix: str) -> Optional[str]:
        p = prefix.strip().lower()
        hits = [side for side, full in (("a", a.lower()), ("b", b.lower())) if p == full or full.endswith(" " + p) or full.startswith(p + " ")]
        return hits[0] if len(hits) == 1 else None

    m = re.fullmatch(r"(.+?) wins by (tko/ko|submission|decision)", s, re.I)
    if m and side_of(m.group(1)):
        return ("method", side_of(m.group(1)), {"tko/ko": "KO/TKO", "submission": "SUB", "decision": "DEC"}[m.group(2).lower()])
    m = re.fullmatch(r"(.+?) wins inside distance", s, re.I)
    if m and side_of(m.group(1)):
        return ("itd", side_of(m.group(1)))
    m = re.fullmatch(r"(.+?) wins in round (\d)", s, re.I)
    if m and side_of(m.group(1)) and int(m.group(2)) <= rounds:
        return ("win_round", side_of(m.group(1)), int(m.group(2)))
    if s_low == "fight goes to decision":
        return ("distance", True)
    if s_low == "fight doesn't go to decision":
        return ("distance", False)
    m = re.fullmatch(r"(over|under) (\d)(?:½|\.5) rounds", s_low)
    if m and int(m.group(2)) < rounds:
        return ("total", m.group(1) == "over", int(m.group(2)) + 0.5)
    m = re.fullmatch(r"fight (starts|won't start) round (\d)", s_low)
    if m and 2 <= int(m.group(2)) <= rounds:
        return ("starts_round", int(m.group(2)), m.group(1) == "starts")
    m = re.fullmatch(r"fight ends in round (\d)", s_low)
    if m and int(m.group(1)) <= rounds:
        return ("ends_round", int(m.group(1)))
    return None


def describe(market: Tuple, a: str, b: str) -> str:
    who = lambda side: a if side == "a" else b  # noqa: E731
    kind = market[0]
    if kind == "ml":
        return f"{who(market[1])} to win"
    if kind == "method":
        return f"{who(market[1])} by {dict(zip(METHOD_BUCKETS, ('KO/TKO', 'submission', 'decision')))[market[2]]}"
    if kind == "itd":
        return f"{who(market[1])} inside the distance"
    if kind == "win_round":
        return f"{who(market[1])} in round {market[2]}"
    if kind == "distance":
        return "Goes to decision" if market[1] else "Doesn't go to decision"
    if kind == "total":
        return f"{'Over' if market[1] else 'Under'} {market[2]:g} rounds"
    if kind == "ends_round":
        return f"Fight ends in round {market[1]}"
    if kind == "starts_round":
        return f"Fight {'starts' if market[2] else 'does not start'} round {market[1]}"
    return str(market)


# -------------------------------------------------------------- finish timing
@dataclass
class Timing:
    """When finishes happen: from recent UFC bouts, by scheduled length and method."""

    ends: Dict[Tuple[int, str], List[int]] = field(default_factory=dict)  # elapsed seconds at the finish

    @classmethod
    def from_fights(cls, fights: Iterable[Fight], since: date = date(2012, 1, 1)) -> "Timing":
        ends: Dict[Tuple[int, str], List[int]] = defaultdict(list)
        for f in fights:
            if f.date < since or not f.event.startswith("UFC") or f.method not in (Method.KO, Method.SUB):
                continue
            if f.end_round < 1 or f.end_round > f.scheduled_rounds:
                continue
            sched = 5 if f.scheduled_rounds >= 5 else 3
            ends[(sched, f.method.value)].append(f.duration_seconds)
        return cls(dict(ends))

    def _sample(self, rounds: int, method: str) -> List[int]:
        return self.ends.get((5 if rounds >= 5 else 3, method), []) or [150]

    def after(self, rounds: int, method: str, seconds: float) -> float:
        """P(the finish comes at or after `seconds` elapsed | a finish by `method`)."""
        xs = self._sample(rounds, method)
        return sum(x >= seconds for x in xs) / len(xs)

    def in_round(self, rounds: int, method: str, k: int) -> float:
        xs = self._sample(rounds, method)
        return sum((k - 1) * ROUND_SECONDS < x <= k * ROUND_SECONDS or (k == 1 and x == 0) for x in xs) / len(xs)


# ------------------------------------------------------------------ pricing
def blend(p_model: float, p_market: Optional[float], weights: Optional[Dict[str, float]]) -> float:
    if p_market is None or not weights:
        return p_model
    return sigmoid(weights["model"] * _logit(p_model) + weights["market"] * _logit(p_market))


def model_prob(market: Tuple, pa: float, dist_a: Dict[str, float], dist_b: Dict[str, float], rounds: int, timing: Timing,
               dec_cal: Optional[Tuple[float, float]] = None) -> float:
    """Our probability of a market from the win probability and method split.

    `dec_cal` = (intercept, slope) recalibrates the chance the fight goes the
    distance (the method model finishes too many fights; see `fit_distance`).
    """
    pb = 1 - pa
    joint = {("a", m): pa * dist_a[m] for m in METHOD_BUCKETS}
    joint.update({("b", m): pb * dist_b[m] for m in METHOD_BUCKETS})
    if dec_cal:
        raw = joint[("a", "DEC")] + joint[("b", "DEC")]
        cal = sigmoid(dec_cal[0] + dec_cal[1] * _logit(raw))
        for k in joint:
            joint[k] *= cal / raw if k[1] == "DEC" else (1 - cal) / (1 - raw)
    finishes = [(s, m) for (s, m) in joint if m != "DEC"]
    kind = market[0]
    if kind == "ml":
        return pa if market[1] == "a" else pb
    if kind == "method":
        return joint[(market[1], market[2])]
    if kind == "itd":
        return joint[(market[1], "KO/TKO")] + joint[(market[1], "SUB")]
    if kind == "win_round":
        return sum(joint[(market[1], m)] * timing.in_round(rounds, m, market[2]) for m in ("KO/TKO", "SUB"))
    dec = joint[("a", "DEC")] + joint[("b", "DEC")]
    if kind == "distance":
        return dec if market[1] else 1 - dec
    if kind == "total":
        cut = market[2] * ROUND_SECONDS
        over = dec + sum(joint[k] * timing.after(rounds, k[1], cut) for k in finishes)
        return over if market[1] else 1 - over
    if kind == "ends_round":
        return sum(joint[k] * timing.in_round(rounds, k[1], market[1]) for k in finishes)
    if kind == "starts_round":
        cut = (market[1] - 1) * ROUND_SECONDS + 1
        starts = dec + sum(joint[k] * timing.after(rounds, k[1], cut) for k in finishes)
        return starts if market[2] else 1 - starts
    raise ValueError(market)


def fit_distance(rows: List[Tuple[float, int]], iterations: int = 400) -> Tuple[float, float]:
    """Logistic recalibration of P(goes the distance): logit(p') = a + b * logit(p)."""
    a, b = 0.0, 1.0
    for _ in range(iterations):
        ga = gb = 0.0
        haa = hab = hbb = 1e-9
        for p, y in rows:
            z = _logit(p)
            q = sigmoid(a + b * z)
            ga += q - y
            gb += (q - y) * z
            w = q * (1 - q)
            haa += w
            hab += w * z
            hbb += w * z * z
        det = haa * hbb - hab * hab
        a -= (hbb * ga - hab * gb) / det
        b -= (haa * gb - hab * ga) / det
    return a, b


def _no_vig(markets: List[Dict[str, object]]) -> None:
    """FanDuel's price with the margin taken out, where the complementary prices are known."""
    groups: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for m in markets:
        key = m["market"]
        if key[0] in ("ml", "distance"):
            groups[key[0]].append(m)
        elif key[0] == "total":
            groups[f"total{key[2]}"].append(m)
        elif key[0] == "starts_round":
            groups[f"starts{key[1]}"].append(m)
        elif key[0] == "method":
            groups["method"].append(m)
    for m in markets:
        m["p_book"] = implied(m["odds"])
        m["p_fair"] = m["p_book"] / 1.12  # typical FanDuel prop margin when the other side isn't shown
    for name, g in groups.items():
        complete = len(g) == 2 or (name == "method" and len(g) == 6)
        if complete:
            total = sum(x["p_book"] for x in g)
            for x in g:
                x["p_fair"] = x["p_book"] / total


def price_bout(bout: Dict[str, object], pa_model: float, dist_a: Dict[str, float], dist_b: Dict[str, float],
               rounds: int, timing: Timing, blend_weights: Optional[Dict[str, float]],
               dec_cal: Optional[Tuple[float, float]] = None) -> List[Dict[str, object]]:
    a, b = bout["a"], bout["b"]
    raw: List[Dict[str, object]] = []
    ml = bout.get("ml") or {}
    for side in ("a", "b"):
        if ml.get(side) is not None:
            raw.append({"market": ("ml", side), "odds": ml[side]})
    seen = set()
    for pr in bout.get("props", []):
        key = canonical(pr["label"], a, b, rounds)
        if key and key not in seen:
            seen.add(key)
            raw.append({"market": key, "odds": pr["odds"]})
    _no_vig(raw)
    p_mkt_a = next((m["p_fair"] for m in raw if m["market"] == ("ml", "a")), None)
    if p_mkt_a is not None and ml.get("b") is None:
        p_mkt_a = None
    pa = blend(pa_model, p_mkt_a, blend_weights)
    out = []
    for m in raw:
        key = m["market"]
        ours = model_prob(key, pa, dist_a, dist_b, rounds, timing, dec_cal)
        if key[0] == "ml":
            p = ours  # already blended with the market
        else:
            p = sigmoid(PROP_SHRINK * _logit(ours) + (1 - PROP_SHRINK) * _logit(m["p_fair"]))
        d = decimal(m["odds"])
        ev = p * d - 1
        kelly = max(0.0, ev / (d - 1))
        out.append({
            "id": f"{bout['mu']}:{':'.join(str(x) for x in key)}",
            "bout": f"{a} vs {b}", "market": list(key), "selection": describe(key, a, b),
            "odds": m["odds"], "decimal": round(d, 4),
            "p_model": round(ours, 4), "p_fanduel": round(m["p_fair"], 4), "p": round(p, 4),
            "edge": round(p - m["p_fair"], 4), "ev": round(ev, 4), "kelly": round(kelly, 4),
        })
    return out


# ------------------------------------------------------------------- ledger
def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _money(x: float) -> float:
    return math.floor(x * 100 + 1e-6) / 100


@dataclass
class Result:
    """How a bout ended: the winner's side ('a'/'b'), None for a draw; nc for no contest."""

    winner: Optional[str]
    method: str  # KO/TKO | SUB | DEC | DRAW | NC
    round: int
    seconds: int  # elapsed in the final round

    @property
    def elapsed(self) -> int:
        return (self.round - 1) * ROUND_SECONDS + self.seconds


def grade_leg(market: List, result: Optional[Result]) -> str:
    """won | lost | void. None (bout didn't happen) and no contests are void."""
    if result is None or result.method == "NC":
        return "void"
    kind = market[0]
    draw = result.winner is None
    finish = result.method in ("KO/TKO", "SUB")
    if kind == "ml":
        return "void" if draw else ("won" if result.winner == market[1] else "lost")
    if kind == "method":
        return "won" if not draw and result.winner == market[1] and result.method == market[2] else "lost"
    if kind == "itd":
        return "won" if not draw and result.winner == market[1] and finish else "lost"
    if kind == "win_round":
        return "won" if not draw and finish and result.winner == market[1] and result.round == market[2] else "lost"
    if kind == "distance":
        return "won" if (not finish) == bool(market[1]) else "lost"
    if kind == "total":
        over = not finish or result.elapsed >= market[2] * ROUND_SECONDS
        return "won" if over == bool(market[1]) else "lost"
    if kind == "ends_round":
        return "won" if finish and result.round == market[1] else "lost"
    if kind == "starts_round":
        starts = not finish or result.elapsed > (market[1] - 1) * ROUND_SECONDS
        return "won" if starts == bool(market[2]) else "lost"
    raise ValueError(market)


def grade_bet(bet: Dict[str, object]) -> Tuple[str, float]:
    """(status, profit) from the legs' grades. Void legs drop out of a parlay."""
    grades = [leg.get("grade") for leg in bet["legs"]]
    if any(g is None for g in grades):
        return "open", 0.0
    if "lost" in grades:
        return "lost", -bet["stake"]
    live = [leg for leg in bet["legs"] if leg["grade"] == "won"]
    if not live:
        return "void", 0.0
    dec = 1.0
    for leg in live:
        dec *= decimal(leg["odds"])
    return "won", _money(bet["stake"] * (dec - 1))


class Ledger:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        if self.path.exists():
            self.doc = json.loads(self.path.read_text())
        else:
            self.doc = {"book": "FanDuel", "start": START_BANKROLL, "min_stake": MIN_STAKE, "created": _now(), "weeks": []}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.doc, indent=1) + "\n")

    @property
    def weeks(self) -> List[Dict[str, object]]:
        return self.doc["weeks"]

    def bets(self) -> Iterable[Dict[str, object]]:
        for w in self.weeks:
            yield from w["bets"]

    def settled_profit(self) -> float:
        return round(sum(b.get("profit", 0.0) for b in self.bets() if b["status"] in ("won", "lost", "void")), 2)

    def open_stakes(self) -> float:
        return round(sum(b["stake"] for b in self.bets() if b["status"] == "open"), 2)

    def bankroll(self) -> float:
        """Settled bankroll: start plus everything graded."""
        return round(self.doc["start"] + self.settled_profit(), 2)

    def available(self) -> float:
        return round(self.bankroll() - self.open_stakes(), 2)

    def bust(self) -> bool:
        return self.available() < MIN_STAKE and self.open_stakes() == 0

    def place(self, event: Dict[str, object], sheet: Dict[str, Dict[str, object]], picks: List[Dict[str, object]],
              card_note: str, event_starts: Optional[str] = None, placed_at: Optional[str] = None) -> Dict[str, object]:
        """Record a week's bets at sheet prices. An empty `picks` list is a pass (still recorded)."""
        placed_at = placed_at or _now()
        if event_starts and placed_at >= event_starts:
            raise ValueError("bets must be placed before the event starts")
        if any(w["event"] == event["name"] for w in self.weeks):
            raise ValueError(f"already bet {event['name']}")
        bets = []
        total = 0.0
        for i, pk in enumerate(picks, 1):
            stake = round(float(pk["stake"]), 2)
            if stake < MIN_STAKE:
                raise ValueError(f"minimum stake is ${MIN_STAKE:.2f}")
            legs = []
            for mid in pk["legs"]:
                if mid not in sheet:
                    raise ValueError(f"not on this week's sheet: {mid}")
                m = sheet[mid]
                legs.append({k: m[k] for k in ("id", "bout", "market", "selection", "odds", "p", "p_fanduel")})
            if len({leg["bout"] for leg in legs}) != len(legs):
                raise ValueError("a parlay can't have two legs from the same bout (FanDuel prices those as same-game parlays)")
            dec = 1.0
            p = 1.0
            for leg in legs:
                dec *= decimal(leg["odds"])
                p *= leg["p"]
            bets.append({
                "id": f"{len(self.weeks) + 1}-{i}", "kind": "parlay" if len(legs) > 1 else "single", "legs": legs,
                "odds": american(dec), "decimal": round(dec, 4), "stake": stake, "to_win": _money(stake * (dec - 1)),
                "p": round(p, 4), "ev": round(p * dec - 1, 4), "reasoning": pk.get("reasoning", ""),
                "status": "open", "profit": 0.0,
            })
            total += stake
        if round(total, 2) > self.available() + 1e-9:
            raise ValueError(f"stakes ${total:.2f} exceed the available bankroll ${self.available():.2f}")
        week = {
            "id": f"w{len(self.weeks) + 1}", "event": event["name"], "event_date": event.get("date", ""),
            "odds_url": event.get("url", ""), "results_url": event.get("results_url", ""), "book": "FanDuel",
            "placed_at": placed_at, "bankroll_before": self.bankroll(), "available_before": self.available(),
            "note": card_note, "bets": bets, "staked": round(total, 2), "settled": not bets, "settled_at": None,
        }
        if not bets:
            week["settled_at"] = placed_at
        self.weeks.append(week)
        return week

    def settle(self, week: Dict[str, object], results: Dict[str, Optional[Result]], sources: List[str]) -> List[str]:
        """Grade a week's legs from `results` keyed by bout ("A vs B"). Returns bouts still unresolved."""
        missing = []
        for bet in week["bets"]:
            for leg in bet["legs"]:
                if leg.get("grade"):
                    continue
                if leg["bout"] not in results:
                    missing.append(leg["bout"])
                    continue
                r = results[leg["bout"]]
                leg["grade"] = grade_leg(leg["market"], r)
                leg["result"] = None if r is None else {"winner": r.winner, "method": r.method, "round": r.round, "seconds": r.seconds}
            bet["status"], bet["profit"] = grade_bet(bet)
        if all(b["status"] != "open" for b in week["bets"]):
            week["settled"] = True
            week["settled_at"] = _now()
            week["bankroll_after"] = self.bankroll()
            week["result_sources"] = sources
        return sorted(set(missing))

    def summary(self) -> Dict[str, object]:
        settled = [b for b in self.bets() if b["status"] in ("won", "lost")]
        staked = sum(b["stake"] for b in settled)
        profit = sum(b["profit"] for b in settled)
        curve = [{"week": "Start", "bankroll": self.doc["start"]}]
        for w in self.weeks:
            if w["settled"]:
                curve.append({"week": w["event"], "bankroll": w.get("bankroll_after", w["bankroll_before"])})
        by_kind: Dict[str, Dict[str, float]] = {}
        for b in settled:
            k = b["kind"] if b["kind"] == "parlay" else ("moneyline" if b["legs"][0]["market"][0] == "ml" else "prop")
            s = by_kind.setdefault(k, {"bets": 0, "won": 0, "staked": 0.0, "profit": 0.0})
            s["bets"] += 1
            s["won"] += b["status"] == "won"
            s["staked"] = round(s["staked"] + b["stake"], 2)
            s["profit"] = round(s["profit"] + b["profit"], 2)
        clv = [b for b in settled if b.get("closing_p") is not None]
        return {
            "start": self.doc["start"], "bankroll": self.bankroll(), "available": self.available(),
            "open_stakes": self.open_stakes(), "bust": self.bust(), "min_stake": MIN_STAKE,
            "bets": len(settled), "won": sum(b["status"] == "won" for b in settled),
            "lost": sum(b["status"] == "lost" for b in settled),
            "void": sum(b["status"] == "void" for b in self.bets()),
            "staked": round(staked, 2), "profit": round(profit, 2), "roi": round(profit / staked, 4) if staked else None,
            "expected_profit": round(sum(b["stake"] * b["ev"] for b in settled), 2),
            "weeks": len(self.weeks), "passes": sum(1 for w in self.weeks if not w["bets"]),
            "curve": curve, "by_kind": by_kind, "clv_n": len(clv), "updated": _now(),
        }


# ------------------------------------------------------------------ results
def _clock(t: str) -> int:
    m = re.match(r"(\d+):(\d{2})", t.strip())
    return int(m.group(1)) * 60 + int(m.group(2)) if m else 0


def _bucket(method_text: str) -> str:
    s = method_text.upper()
    if "NO CONTEST" in s or re.search(r"\bNC\b", s) or "OVERTURNED" in s:
        return "NC"
    if "DRAW" in s:
        return "DRAW"
    if "DISQUALIFICATION" in s or re.search(r"\bDQ\b", s):
        return "DQ"
    if "SUBMISSION" in s or re.search(r"\bSUB\b", s) or "TECHNICAL SUBMISSION" in s:
        return "SUB"
    if re.search(r"\bKO\b|\bTKO\b|KNOCKOUT|DOCTOR|CORNER|RETIREMENT", s):
        return "KO/TKO"
    if "DECISION" in s or "DEC" in s:
        return "DEC"
    return "?"


def wiki_result(row: Dict[str, object]) -> Optional[Result]:
    """A Wikipedia results row (sources.events.parse_card) -> Result, oriented to the row's left fighter as 'a'."""
    method = _bucket(str(row.get("result", "")))
    if method == "?" or not row.get("round"):
        return None
    rnd = int(re.sub(r"\D", "", str(row["round"])) or 0)
    if method in ("NC", "DRAW"):
        return Result(None, method, rnd, _clock(str(row.get("time", ""))))
    if not row.get("decided"):
        return None
    if method == "DQ":
        method = "KO/TKO"  # FanDuel groups DQ with TKO/KO for method props
    return Result("a", method, rnd, _clock(str(row.get("time", ""))))


def sherdog_result(bouts, opponent_key: str, when: date, match_key) -> Optional[Result]:
    """The same bout on one fighter's Sherdog record, oriented to that fighter as 'a'."""
    for cb in bouts:
        if abs((cb.date - when).days) > 2 or match_key(cb.opponent) != opponent_key:
            continue
        method = _bucket(cb.method.value if hasattr(cb.method, "value") else str(cb.method))
        if cb.result == "nc":
            method = "NC"
        if cb.result == "draw":
            return Result(None, "DRAW", cb.round, _clock(cb.time))
        if method == "NC":
            return Result(None, "NC", cb.round, _clock(cb.time))
        if method == "DQ":
            method = "KO/TKO"
        if method == "S-DEC":
            method = "DEC"
        return Result("a" if cb.result == "win" else "b", method, cb.round, _clock(cb.time))
    return None


def agree(x: Optional[Result], y: Optional[Result]) -> bool:
    return (x is not None and y is not None and x.winner == y.winner and x.method == y.method
            and x.round == y.round and abs(x.seconds - y.seconds) <= 5)


def flip(r: Optional[Result]) -> Optional[Result]:
    if r is None or r.winner is None:
        return r
    return Result("b" if r.winner == "a" else "a", r.method, r.round, r.seconds)
