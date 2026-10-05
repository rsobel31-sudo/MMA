"""`python -m mma_predictor card-picks ...`: AI Picks, Claude's pick'em. No money: a winner, a method and a round for every bout.

    card-picks draft   the model's pick for every bout on the next UFC card (winner, method, round, chances)
    card-picks lock    record Claude's picks for the card from a picks file (every bout, before the card starts)
    card-picks grade   grade finished cards from results two sources agree on, and update the record
    card-picks sync    write the page-database documents (ai_picks collection, ids "card-...")

AI Bets (the `picks` command) judges betting: prices, staking, bankroll. This judges the reading
of fights: did Claude pick the winner, how it ended and when. Scoring: 2 points for the winner, 1 more
for the method, and a bonus point when the winner, method and round are all right (a decision goes the
distance, so its round is the last scheduled round). Each pick is stored beside the model's own
pick for the same bout, so the record shows whether Claude's overrides help or hurt, and the grading
checks the method model's calibration (predicted KO/TKO, submission and decision rates against what
happened). What that teaches goes back into the code (see `lessons` and AI_PICKS.md).
"""

from __future__ import annotations

import json
import math
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from . import picks as P
from .picks_cli import (CALIBRATION, SHEETS, _fetcher, _fresh, _in_us, _lock_time, _model, _pair, _results_for, _slug, next_event,
                        replay_args, replay_event, sigmoid_logit)

DIR = Path("data/card_picks")
SUMMARY = DIR / "summary.json"
ADJUST = DIR / "method_adjust.json"
DRAFT = Path(".cache/card_picks_draft.json")
ROUND_TABLE = Path("data/card_picks/round_table.json")  # P(round | finish method), from UFC finishes (written by draft)
METHODS = ("KO/TKO", "SUB", "DEC")
# Thresholds before the record is allowed to change anything.
MIN_METHOD_N = 100  # graded bouts before the method model's rates are re-weighted
MIN_OVERRIDE_N = 30  # overrides before "trust the model more / less" is called
POINTS = {"winner": 2, "method": 1, "round": 1}  # the round point needs the winner and method right too
MAX_POINTS = sum(POINTS.values())


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _surname(name: str) -> str:
    return re.sub(r"\s+(Jr|Sr|II|III)\.?$", "", name).split()[-1]


def use_dir(d: str) -> None:
    """Keep a separate record (e.g. data/card_picks/dwcs for the Contender Series): its own cards and summary.
    Only the main UFC record re-weights the method model."""
    global DIR, SUMMARY
    if d and Path(d) != DIR:
        DIR, SUMMARY = Path(d), Path(d) / "summary.json"


def load_adjust() -> Dict[str, float]:
    """Per-method multipliers learned from graded picks (1.0 = no change)."""
    return json.loads(ADJUST.read_text()).get("factors", {}) if ADJUST.exists() else {}


def joint_methods(pa: float, dist_a: Dict[str, float], dist_b: Dict[str, float],
                  dec_cal: Optional[tuple], adjust: Optional[Dict[str, float]] = None) -> Dict[str, Dict[str, float]]:
    """P(side wins by method), with the decision calibration and any learned method re-weighting applied.
    The re-weighting moves probability between methods inside each fighter's wins, so the win chance is unchanged."""
    out = {}
    for side in ("a", "b"):
        out[side] = {m: P.model_prob(("method", side, m), pa, dist_a, dist_b, 3, None, dec_cal) for m in METHODS}
        if adjust:
            w = {m: out[side][m] * adjust.get(m, 1.0) for m in METHODS}
            t = sum(w.values()) or 1.0
            win = pa if side == "a" else 1 - pa
            out[side] = {m: win * w[m] / t for m in METHODS}
    return out


def round_table(timing: P.Timing) -> Dict[str, Dict[str, List[float]]]:
    """P(round k | a finish by method) for three- and five-round fights, from the finish-timing model."""
    out = {}
    for r in (3, 5):
        out[str(r)] = {}
        for m in ("KO/TKO", "SUB"):
            ps = [timing.in_round(r, m, k) for k in range(1, r + 1)]
            t = sum(ps) or 1.0
            out[str(r)][m] = [round(x / t, 4) for x in ps]
    return out


def load_round_table() -> Optional[Dict[str, Dict[str, List[float]]]]:
    return json.loads(ROUND_TABLE.read_text())["table"] if ROUND_TABLE.exists() else None


def round_chances(table: Optional[Dict], rounds: int, method: str, history: Optional[Dict[str, List[int]]] = None) -> List[float]:
    """P(the fight ends in round k | it ends by `method`), k = 1..rounds, for this fight: the league's finish timing
    (`table`) moved by when the winner has finished people and when the loser has been finished (`history`: per-round
    counts "wins" and "losses"), each fight worth a quarter of the league's ten. A decision ends in the last round.
    Reference for Claude's round read; it never changes the model's winner or method."""
    if method == "DEC":
        return [0.0] * (rounds - 1) + [1.0]
    row = (table or {}).get(str(5 if rounds >= 5 else 3), {}).get(method)
    lg = list(row) if row and len(row) == rounds else [1.0 / rounds] * rounds
    h = history or {}
    v = [10 * lg[k] + 0.25 * (h.get("wins") or [0] * rounds)[k] + 0.25 * (h.get("losses") or [0] * rounds)[k] for k in range(rounds)]
    t = sum(v) or 1.0
    return [x / t for x in v]


def finish_rounds(fights, winner: str, loser: str, before: date, rounds: int) -> Dict[str, List[int]]:
    """When `winner` has finished opponents and when `loser` has been finished, by round, in bouts before `before`."""
    from .data import Method

    out = {"wins": [0] * rounds, "losses": [0] * rounds}
    for f in fights:
        if f.date >= before or not f.is_scored or f.method not in (Method.KO, Method.SUB) or not 1 <= f.end_round <= rounds:
            continue
        if f.winner == winner:
            out["wins"][f.end_round - 1] += 1
        elif f.involves(loser) and f.winner != loser:
            out["losses"][f.end_round - 1] += 1
    return out


def add_model_round(model: Dict, rounds: int, table: Optional[Dict], history: Optional[Dict[str, List[int]]] = None) -> Dict:
    """The model's round, for reference: the likeliest round of its own method for this fight (in place).
    The winner and method stay the model's likeliest; the round is a lighter, separate read."""
    rc = {m: [round(x, 3) for x in round_chances(table, rounds, m, history)] for m in ("KO/TKO", "SUB")}
    m = model["method"]
    model["round"] = rounds if m == "DEC" else max(range(rounds), key=lambda k: rc[m][k]) + 1
    side = "a" if model["p_a"] >= 0.5 else "b"
    model["p_exact"] = round(model["joint"][side][m] * (1.0 if m == "DEC" else rc[m][model["round"] - 1]), 4)
    model["round_chances"] = rc
    if history:
        model["finish_rounds"] = history
    return model


# ------------------------------------------------------------------- draft
def cmd_draft(args) -> int:
    from .cli import _history
    from .features import BoutContext
    from .methods import method_distribution
    from .predictor import FightPredictor
    from .reads import Reads
    from .sources import events
    from .sources.events import link_names

    fetcher = _fetcher(args.cache)
    ev = replay_event(args) or next_event(fetcher, args.event)
    if ev is None:
        print("No scheduled UFC event found.")
        return 1
    card = events.parse_card(_fresh(fetcher, ev["url"])) if ev["url"] else []
    if not card:
        print(f"No bouts listed for {ev['name']} yet.")
        return 1
    h = _history(args)
    model, _ = _model(Path(args.app_data))
    pr = FightPredictor(h, model)
    aliases = json.loads(Path(args.aliases).read_text()) if Path(args.aliases).exists() else {}
    linked = link_names({n for w in card for n in (w["a"], w["b"])}, set(h.names()), aliases)
    reads = Reads.load()
    dec_cal = tuple(json.loads(CALIBRATION.read_text())["dec_cal"]) if CALIBRATION.exists() else None
    adjust = load_adjust()
    table = round_table(P.Timing.from_fights([f for f in h.fights if f.date < date.fromisoformat(ev["date"])]))
    if not getattr(args, "wiki_url", ""):  # a replay of a past card doesn't overwrite the current table
        ROUND_TABLE.parent.mkdir(parents=True, exist_ok=True)
        ROUND_TABLE.write_text(json.dumps({"made": _now(), "before": ev["date"], "table": table}, indent=1) + "\n")
    # FanDuel's moneyline from this week's AI Bets sheet, when there is one: a third opinion to compare with.
    sheet_path = Path(args.sheet) if getattr(args, "sheet", "") else SHEETS / f"{ev['date']}-{_slug(ev['name'])}.json"
    ml = {}
    if sheet_path.exists():
        for b in json.loads(sheet_path.read_text())["bouts"]:
            ml[_pair(b["a"], b["b"])] = (b["a"], b["ml"])
    # Otherwise the BestFightOdds line the site shows (app/data.json, exported from the same crawl).
    if not ml and Path(args.app_data).exists():
        for e in json.loads(Path(args.app_data).read_text()).get("upcoming", {}).get("events", []):
            for b in e["bouts"]:
                mk = b.get("market") or {}
                if mk.get("a_now") is not None and mk.get("b_now") is not None:
                    ml.setdefault(_pair(b["a"], b["b"]), (b["a"], {"a": mk["a_now"], "b": mk["b_now"]}))
    when = date.fromisoformat(ev["date"])
    bouts = []
    for w in card:
        rounds = int(w.get("rounds") or 3)
        row = {"bout": f"{w['a']} vs {w['b']}", "a": w["a"], "b": w["b"], "segment": w.get("segment", ""),
               "weight_class": w.get("weight_class", ""), "rounds": rounds, "title": bool(w.get("title"))}
        a, b = linked.get(w["a"]), linked.get(w["b"])
        if a and b:
            sa, sb, x = pr.features(a, b, when, BoutContext(rounds, bool(w.get("title"))))
            # The model's own pick is the statistics alone; Claude's scouting read is Claude's, so it belongs to Claude's pick.
            pa = sigmoid_logit(model, x)
            j = joint_methods(pa, method_distribution(sa, sb, rounds), method_distribution(sb, sa, rounds), dec_cal, adjust)
            side = "a" if pa >= 0.5 else "b"
            method = max(METHODS, key=lambda m: j[side][m])
            row["read_a"] = round(reads.logit(a, b), 3)
            fr = finish_rounds(h.fights, a if side == "a" else b, b if side == "a" else a, when, rounds)
            row["model"] = add_model_round({"p_a": round(pa, 4), "winner": w[side], "method": method, "p_win": round(max(pa, 1 - pa), 4),
                                            "joint": {s: {m: round(v, 4) for m, v in j[s].items()} for s in j}}, rounds, table, fr)
        else:
            row["model"] = None
            row["no_data"] = [n for n, l in ((w["a"], a), (w["b"], b)) if not l]
        hit = ml.get(_pair(w["a"], w["b"]))
        if hit and hit[1].get("a") is not None and hit[1].get("b") is not None:
            pa_m = P.implied(hit[1]["a"]) / (P.implied(hit[1]["a"]) + P.implied(hit[1]["b"]))
            if _pair(hit[0], hit[0]) != _pair(w["a"], w["a"]):  # the sheet lists the bout the other way round
                pa_m = 1 - pa_m
            row["market_p_a"] = round(pa_m, 4)
        bouts.append(row)
    draft = {"event": ev["name"], "date": ev["date"], "results_url": ev["url"], "location": ev.get("location", ""),
             "locks_at": _lock_time(ev["date"], _in_us(ev.get("location", ""))), "drafted_at": _now(),
             "dec_cal": dec_cal, "method_adjust": adjust, "round_table": table, "bouts": bouts}
    DRAFT.parent.mkdir(exist_ok=True)
    DRAFT.write_text(json.dumps(draft, indent=1, ensure_ascii=False))
    print(f"{ev['name']} ({ev['date']}) · picks lock {draft['locks_at']} · {len(bouts)} bouts")
    for r in bouts:
        m = r["model"]
        mk = ""
        if m and "market_p_a" in r:
            mk = f" · market {r['market_p_a'] if m['winner'] == r['a'] else 1 - r['market_p_a']:.0%} on {_surname(m['winner'])}"
        if r.get("read_a"):
            mk += f" · Claude's read {r['read_a']:+.2f} to {_surname(r['a'])}"
        print(f"  {r['bout']:<46} " + (f"model: {m['winner']} by {m['method']}{'' if m['method'] == 'DEC' else ' R' + str(m['round'])} ({m['p_win']:.0%} to win; "
              f"{m['joint']['a' if m['winner'] == r['a'] else 'b'][m['method']]:.0%} by that method, {m['p_exact']:.0%} exact){mk}"
              + (f"\n  {'':<46} finish rounds: {_surname(m['winner'])} finishes in R1-R{r['rounds']} {m['finish_rounds']['wins']}, "
                 f"opponent finished in {m['finish_rounds']['losses']} · KO by round {[f'{x:.0%}' for x in m['round_chances']['KO/TKO']]}" if m.get("finish_rounds") else "") if m else f"no model pick (no data on {', '.join(r['no_data'])})"))
    print(f"\nDraft -> {DRAFT}. Write a picks file covering every bout and run `card-picks lock --picks FILE`.")
    return 0


# -------------------------------------------------------------------- lock
def card_path(event: str, day: str) -> Path:
    return DIR / f"{day}-{_slug(event)}.json"


def lock(draft: Dict, spec: Dict, now: Optional[str] = None) -> Dict:
    """Validate Claude's picks against the draft (every bout, a real winner and method) and build the card record."""
    now = now or _now()
    if now >= draft["locks_at"]:
        raise ValueError(f"{draft['event']} locked at {draft['locks_at']}: picks must go in before the card starts")
    by_pair = {_pair(b["a"], b["b"]): b for b in draft["bouts"]}
    picks = {}
    for p in spec.get("picks", []):
        a, b = re.split(r"\s+vs\.?\s+", p["bout"], maxsplit=1)
        key = _pair(a, b)
        if key not in by_pair:
            raise ValueError(f"{p['bout']}: not on the card")
        bout = by_pair[key]
        if _pair(p["winner"], p["winner"]) not in (_pair(bout["a"], bout["a"]), _pair(bout["b"], bout["b"])):
            raise ValueError(f"{p['bout']}: winner must be {bout['a']} or {bout['b']}")
        if p["method"] not in METHODS:
            raise ValueError(f"{p['bout']}: method must be one of {', '.join(METHODS)}")
        n_rounds = int(bout.get("rounds") or 3)
        if p["method"] == "DEC":
            p = dict(p, round=n_rounds)  # a decision goes the distance
        elif not isinstance(p.get("round"), int) or not 1 <= p["round"] <= n_rounds:
            raise ValueError(f"{p['bout']}: a finish needs the round it ends in, 1 to {n_rounds}")
        conf = float(p.get("confidence", 0))
        if not 0.5 <= conf < 1:
            raise ValueError(f"{p['bout']}: confidence is the chance the pick wins, from 0.50 to 0.99")
        picks[key] = p
    missing = [b["bout"] for k, b in by_pair.items() if k not in picks]
    if missing:
        raise ValueError("every bout needs a pick; missing: " + "; ".join(missing))
    rows = []
    for key, bout in by_pair.items():
        p = picks[key]
        side = "a" if _pair(p["winner"], p["winner"]) == _pair(bout["a"], bout["a"]) else "b"
        rows.append({k: bout[k] for k in ("bout", "a", "b", "segment", "weight_class", "rounds", "title") if k in bout} | {
            "pick": {"winner": bout[side], "side": side, "method": p["method"], "round": p["round"], "confidence": round(conf_of(p), 2), "why": p.get("why", "").strip()},
            "model": bout.get("model"), "market_p_a": bout.get("market_p_a")})
    return {"event": draft["event"], "date": draft["date"], "results_url": draft["results_url"], "locks_at": draft["locks_at"],
            "locked_at": now, "note": spec.get("note", "").strip(), "dec_cal": draft.get("dec_cal"),
            "method_adjust": draft.get("method_adjust") or {}, "rounds_picked": True, "bouts": rows, "graded": False}


def conf_of(p: Dict) -> float:
    return float(p.get("confidence", 0))


def cmd_lock(args) -> int:
    use_dir(args.dir)
    draft = json.loads(Path(args.draft).read_text())
    spec = json.loads(Path(args.picks).read_text())
    try:
        rec = lock(draft, spec, now=args.as_of or None)
    except ValueError as exc:
        print(f"Not locked: {exc}")
        return 1
    path = card_path(rec["event"], rec["date"])
    if path.exists():
        rec["revision"] = json.loads(path.read_text()).get("revision", 1) + 1
    DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    agree = sum(1 for b in rec["bouts"] if b["model"] and b["model"]["winner"] == b["pick"]["winner"])
    exact = sum(1 for b in rec["bouts"] if b["model"] and b["model"]["winner"] == b["pick"]["winner"] and b["model"]["method"] == b["pick"]["method"])
    full = sum(1 for b in rec["bouts"] if b["model"] and b["model"]["winner"] == b["pick"]["winner"] and b["model"]["method"] == b["pick"]["method"]
               and b["model"].get("round") == b["pick"]["round"])
    print(f"{rec['event']}: {len(rec['bouts'])} picks locked at {rec['locked_at']} -> {path}")
    print(f"  same winner as the model on {agree}, same winner and method on {exact}, and the same round on {full}; commit this file before the card.")
    return 0


# ------------------------------------------------------------------- grade
def same_outcome(x: Optional[P.Result], y: Optional[P.Result]) -> bool:
    """The pick'em grades once the winner and the method agree; the round point also needs the round to agree (see grade_card)."""
    return x is not None and y is not None and x.winner == y.winner and x.method == y.method


def score(pick_side: Optional[str], pick_method: Optional[str], pick_round: Optional[int], result: Dict) -> Dict[str, object]:
    """Pick'em points: 2 for the winner, 1 more for the method, and 1 more when the round is right too.
    `result` is a graded bout's result; the round point needs both sources to agree on the round."""
    win = pick_side == result["side"]
    meth = win and pick_method == result["method"]
    rnd = bool(meth and pick_round is not None and pick_round == result["round"] and result.get("round_confirmed", True))
    return {"winner": win, "method": bool(meth), "round": rnd,
            "points": POINTS["winner"] * win + POINTS["method"] * meth + POINTS["round"] * rnd}


def rescore(rec: Dict) -> None:
    """Score every graded bout from its stored result (after a scoring change, the whole record moves together)."""
    for b in rec["bouts"]:
        r = b.get("result")
        if not r or "void" in r:
            continue
        b["claude"] = score(b["pick"]["side"], b["pick"]["method"], b["pick"].get("round"), r)
        m = b.get("model")
        if m:
            b["model_score"] = score("a" if m["winner"] == b["a"] else "b", m["method"], m.get("round") if rec.get("rounds_picked") else None, r)


def grade_card(rec: Dict, results: Dict[str, Optional[P.Result]], round_agrees: Optional[Dict[str, bool]] = None) -> int:
    """Store each finished bout's result and score it. `round_agrees[bout]` is False when the sources differ on the round."""
    done = 0
    for b in rec["bouts"]:
        if "result" in b or b["bout"] not in results:
            continue
        r = results[b["bout"]]
        if r is None:
            b["result"] = {"void": "did not take place"}
        elif r.winner is None:
            b["result"] = {"void": r.method.lower()}  # draw or no contest: not graded
        else:
            b["result"] = {"winner": b[r.winner], "side": r.winner, "method": r.method, "round": r.round}
            if round_agrees is not None and not round_agrees.get(b["bout"], True):
                b["result"]["round_confirmed"] = False
        done += 1
    rescore(rec)
    rec["graded"] = all("result" in b for b in rec["bouts"])
    return done


def _ll(p: float, y: int) -> float:
    p = min(1 - 1e-6, max(1e-6, p))
    return -math.log(p if y else 1 - p)


def summarize(cards: List[Dict]) -> Dict:
    """The running record: Claude vs the model, the method model's calibration, and what it should change."""
    rows = [(c, b) for c in cards for b in c["bouts"] if "claude" in b]
    tot = lambda key, who: sum(int(b[who][key]) for _, b in rows if who in b)  # noqa: E731
    n = len(rows)
    nm = sum(1 for _, b in rows if "model_score" in b)
    claude_ll = sum(_ll(b["pick"]["confidence"], int(b["claude"]["winner"])) for _, b in rows) / n if n else None
    model_ll = (sum(_ll(b["model"]["p_win"], int(b["model_score"]["winner"])) for _, b in rows if "model_score" in b) / nm) if nm else None
    s = {"updated": _now(), "cards": len({c["event"] for c, _ in rows}), "bouts": n,
         "scoring": dict(POINTS),
         "claude": {"n": n, "winners": tot("winner", "claude"), "methods": tot("method", "claude"), "rounds": tot("round", "claude"),
                    "points": tot("points", "claude"), "possible": sum(MAX_POINTS if c.get("rounds_picked") else MAX_POINTS - POINTS["round"] for c, _ in rows),
                    "log_loss": round(claude_ll, 4) if claude_ll is not None else None},
         "model": {"n": nm, "winners": tot("winner", "model_score"), "methods": tot("method", "model_score"), "rounds": tot("round", "model_score"),
                   "points": tot("points", "model_score"), "log_loss": round(model_ll, 4) if model_ll is not None else None}}
    # Rounds: on finishes Claude picked right (winner and method), how often the round was right too.
    fin = [b for c, b in rows if c.get("rounds_picked") and b["claude"]["method"] and b["result"]["method"] != "DEC"]
    s["finish_rounds"] = {"n": len(fin), "right": sum(1 for b in fin if b["claude"]["round"])}
    # Market favourite, where a line was on the sheet.
    mk = [(b, b["market_p_a"]) for _, b in rows if b.get("market_p_a") is not None]
    s["market"] = {"n": len(mk), "winners": sum(1 for b, p in mk if (p >= 0.5) == (b["result"]["side"] == "a"))}
    # Overrides: bouts where Claude's winner differs from the model's.
    ov = [b for _, b in rows if "model_score" in b and b["pick"]["winner"] != b["model"]["winner"]]
    s["overrides"] = {"n": len(ov), "claude_right": sum(1 for b in ov if b["claude"]["winner"])}
    mov = [b for _, b in rows if "model_score" in b and b["pick"]["winner"] == b["model"]["winner"] and b["pick"]["method"] != b["model"]["method"]]
    s["method_overrides"] = {"n": len(mov), "claude_right": sum(1 for b in mov if b["claude"]["method"]),
                             "model_right": sum(1 for b in mov if b["model_score"]["method"])}
    # Picks by method, and how often each kind came in.
    s["by_method"] = {m: {"picked": sum(1 for _, b in rows if b["pick"]["method"] == m),
                          "right": sum(1 for _, b in rows if b["pick"]["method"] == m and b["claude"]["method"]),
                          "happened": sum(1 for _, b in rows if b["result"]["method"] == m)} for m in METHODS}
    # Method model calibration: the model's predicted share of each ending vs what happened.
    cal = {}
    jm = [b for _, b in rows if b.get("model")]
    for m in METHODS:
        ps = [b["model"]["joint"]["a"][m] + b["model"]["joint"]["b"][m] for b in jm]
        exp, act = sum(ps), sum(1 for b in jm if b["result"]["method"] == m)
        var = sum(p * (1 - p) for p in ps)
        cal[m] = {"expected": round(exp, 2), "actual": act, "z": round((act - exp) / math.sqrt(var), 2) if var > 0 else 0.0}
    s["method_calibration"] = {"n": len(jm), **cal}
    # Claude's confidence calibration.
    bands = []
    for lo, hi in ((0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 1.0)):
        xs = [b for _, b in rows if lo <= b["pick"]["confidence"] < hi]
        if xs:
            bands.append({"from": lo, "to": hi, "n": len(xs), "said": round(sum(b["pick"]["confidence"] for b in xs) / len(xs), 3),
                          "won": round(sum(1 for b in xs if b["claude"]["winner"]) / len(xs), 3)})
    s["confidence"] = bands
    s["lessons"] = lessons(s)
    return s


def lessons(s: Dict) -> List[Dict[str, str]]:
    """What the record says to change, once there's enough of it. Each lesson names the code it touches."""
    out = []
    cal = s["method_calibration"]
    if cal["n"] < MIN_METHOD_N:
        out.append({"kind": "wait", "text": f"Method model: {cal['n']} of {MIN_METHOD_N} graded bouts needed before its KO/TKO, submission and decision rates are re-weighted."})
    else:
        for m in METHODS:
            c = cal[m]
            if abs(c["z"]) >= 1.96:
                out.append({"kind": "change", "area": "methods",
                            "text": f"{m}: the model expected {c['expected']:.0f} of {cal['n']}, {c['actual']} happened (z {c['z']:+.2f}). "
                                    f"`card-picks grade` re-weights {m} in data/card_picks/method_adjust.json; if the gap is in decisions, also re-run `picks calibrate`."})
        if not any(l.get("area") == "methods" for l in out):
            out.append({"kind": "ok", "text": f"Method model: within noise on all three endings over {cal['n']} bouts."})
    ov = s["overrides"]
    if ov["n"] < MIN_OVERRIDE_N:
        out.append({"kind": "wait", "text": f"Overrides: Claude has picked against the model {ov['n']} times; {MIN_OVERRIDE_N} needed before judging them."})
    else:
        rate = ov["claude_right"] / ov["n"]
        se = math.sqrt(0.25 / ov["n"])
        if rate - 0.5 >= 1.96 * se:
            out.append({"kind": "change", "area": "reads", "text": f"Claude's overrides win {rate:.0%} of {ov['n']}: what drives them (scouting reads) deserves more weight in the model (reads.py cap, scouting factor)."})
        elif 0.5 - rate >= 1.96 * se:
            out.append({"kind": "change", "area": "reads", "text": f"Claude's overrides win only {rate:.0%} of {ov['n']}: follow the model more, and shrink the scouting reads' weight."})
        else:
            out.append({"kind": "ok", "text": f"Overrides: {ov['claude_right']} of {ov['n']} right, not clearly better or worse than the model yet."})
    return out


def fit_adjust(s: Dict) -> Optional[Dict]:
    """Per-method multipliers from the calibration, only where the gap is beyond noise; shrunk halfway, capped at ±25%."""
    cal = s["method_calibration"]
    if cal["n"] < MIN_METHOD_N or not any(abs(cal[m]["z"]) >= 1.96 for m in METHODS):
        return None
    f = {}
    for m in METHODS:
        c = cal[m]
        ratio = (c["actual"] / c["expected"]) if c["expected"] > 0 else 1.0
        f[m] = round(min(1.25, max(0.8, 1 + 0.5 * (ratio - 1))), 3) if abs(c["z"]) >= 1.96 else 1.0
    return {"fitted": _now(), "from_bouts": cal["n"], "factors": f,
            "note": "Multiplies the method model's chances of each ending inside each fighter's wins (card-picks draft). Refitted after each graded card; only gaps beyond noise move a factor."}


def load_cards() -> List[Dict]:
    return [json.loads(p.read_text()) for p in sorted(DIR.glob("20*.json"))]


def cmd_grade(args) -> int:
    use_dir(args.dir)
    main = DIR == Path("data/card_picks")
    fetcher = _fetcher(args.cache)
    today = date.today().isoformat()
    for path in sorted(DIR.glob("20*.json")):
        rec = json.loads(path.read_text())
        if rec.get("graded") or (rec["date"] >= today and not args.force):
            before = json.dumps(rec, sort_keys=True)
            rescore(rec)  # keeps finished cards on the current scoring
            if json.dumps(rec, sort_keys=True) != before:
                path.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
            continue
        week = {"results_url": rec["results_url"], "event_date": rec["date"], "bets": [{"legs": [{"bout": b["bout"]}]} for b in rec["bouts"] if "result" not in b]}
        agrees: Dict[str, bool] = {}
        n = grade_card(rec, _results_for(fetcher, week, agree=same_outcome, round_agrees=agrees), agrees)
        rec["graded_at"] = _now()
        path.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
        g = [b for b in rec["bouts"] if "claude" in b]
        print(f"{rec['event']}: {n} bouts graded now; Claude {sum(b['claude']['winner'] for b in g)}/{len(g)} winners, "
              f"{sum(b['claude']['method'] for b in g)} with the method, {sum(b['claude']['round'] for b in g)} with the round too, "
              f"{sum(b['claude']['points'] for b in g)} pts" + ("" if rec["graded"] else " (some results still pending)"))
    s = summarize(load_cards())
    adj = fit_adjust(s) if main else None
    if adj:
        ADJUST.write_text(json.dumps(adj, indent=1) + "\n")
        s["method_adjust"] = adj["factors"]
    elif ADJUST.exists():
        s["method_adjust"] = load_adjust()
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(s, indent=1) + "\n")
    c, m = s["claude"], s["model"]
    print(f"Record: Claude {c['winners']}/{c['n']} winners, {c['methods']} methods, {c['rounds']} rounds, {c['points']} of {c['possible']} pts · "
          f"model {m['winners']}/{m['n']}, {m['methods']} methods, {m['rounds']} rounds, {m['points']} pts")
    for l in s["lessons"]:
        print(f"  [{l['kind']}] {l['text']}")
    return 0


# -------------------------------------------------------------------- sync
def sync_docs(prefix: str = "card-") -> Dict[str, Dict]:
    docs = {}
    if SUMMARY.exists():
        docs[prefix + "summary"] = json.loads(SUMMARY.read_text())
    for rec in load_cards():
        docs[prefix + rec["date"] + "-" + _slug(rec["event"])[:60]] = rec
    return docs


def cmd_sync(args) -> int:
    use_dir(args.dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    docs = sync_docs(args.prefix)
    for k, v in docs.items():
        (out / f"{k}.json").write_text(json.dumps(v, ensure_ascii=False))
    print(json.dumps([{"op": "set", "collection": "ai_picks", "doc_id": k, "file_path": str((out / f"{k}.json").resolve())} for k in docs], indent=1))
    return 0


def register(sub, data_arg) -> None:
    p = sub.add_parser("card-picks", help="AI Picks: Claude's winner, method and round for every bout, graded and tracked (see AI_PICKS.md)")
    ps = p.add_subparsers(dest="card_picks_cmd", required=True)
    q = ps.add_parser("draft", help="the model's pick for every bout on the next UFC card")
    data_arg(q)
    q.add_argument("--event", default="")
    q.add_argument("--cache", default=".cache/pages")
    q.add_argument("--app-data", default="app/data.json")
    q.add_argument("--aliases", default="data/name_aliases.json")
    replay_args(q)
    q.add_argument("--sheet", default="", help="this card's AI Bets sheet (default: data/ai_picks/sheets/<date>-<event>.json)")
    q.set_defaults(func=cmd_draft)
    q = ps.add_parser("lock", help="record Claude's picks (every bout) before the card starts")
    q.add_argument("--draft", default=str(DRAFT))
    q.add_argument("--as-of", default="", help="UTC timestamp to lock at (replays only)")
    q.add_argument("--picks", required=True, help='{"note": "...", "picks": [{"bout": "A vs B", "winner": "A", "method": "KO/TKO|SUB|DEC", "round": 2, "confidence": 0.62, "why": "..."}]}')
    q.add_argument("--dir", default="", help="a separate record, e.g. data/card_picks/dwcs")
    q.set_defaults(func=cmd_lock)
    q = ps.add_parser("grade", help="grade finished cards and update the record and lessons")
    q.add_argument("--cache", default=".cache/pages")
    q.add_argument("--force", action="store_true")
    q.add_argument("--dir", default="")
    q.set_defaults(func=cmd_grade)
    q = ps.add_parser("league", help="My Picks: grade the players' pick'em entries and build the leaderboard (standings/picks-*)")
    q.add_argument("--players", default=".cache/players_picks", help="one <uid>.txt per player: ArtifactData's inline list of players/<uid>/picks")
    q.add_argument("--out", default=".cache/pickem_sync")
    q.set_defaults(func=lambda a: __import__("mma_predictor.pickem", fromlist=["cmd_league"]).cmd_league(a))
    q = ps.add_parser("sync", help="write card-* documents for the page database")
    q.add_argument("--out", default=".cache/card_picks_sync")
    q.add_argument("--dir", default="")
    q.add_argument("--prefix", default="card-", help="document id prefix (dwcs- for the Contender Series record)")
    q.set_defaults(func=cmd_sync)
