"""`python -m mma_predictor card-picks ...`: AI Picks, Claude's pick'em. No money: a winner and a method for every bout.

    card-picks draft   the model's pick for every bout on the next UFC card (winner, method, chances)
    card-picks lock    record Claude's picks for the card from a picks file (every bout, before the card starts)
    card-picks grade   grade finished cards from results two sources agree on, and update the record
    card-picks sync    write the page-database documents (ai_picks collection, ids "card-...")

AI Bets (the `picks` command) judges betting: prices, staking, bankroll. This judges the reading
of fights: did Claude pick the winner, and how it ended. Each pick is stored beside the model's own
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
from .picks_cli import CALIBRATION, SHEETS, _fetcher, _fresh, _in_us, _lock_time, _model, _pair, _results_for, _slug, sigmoid_logit

DIR = Path("data/card_picks")
SUMMARY = DIR / "summary.json"
ADJUST = DIR / "method_adjust.json"
DRAFT = Path(".cache/card_picks_draft.json")
METHODS = ("KO/TKO", "SUB", "DEC")
# Thresholds before the record is allowed to change anything.
MIN_METHOD_N = 100  # graded bouts before the method model's rates are re-weighted
MIN_OVERRIDE_N = 30  # overrides before "trust the model more / less" is called


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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
    sched = [e for e in events.scheduled_events(_fresh(fetcher, events.EVENTS_URL)) if e["date"] >= date.today().isoformat()]
    if args.event:
        sched = [e for e in sched if args.event.lower() in e["name"].lower()]
    if not sched:
        print("No scheduled UFC event found.")
        return 1
    ev = sched[0]
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
    # FanDuel's moneyline from this week's AI Bets sheet, when there is one: a third opinion to compare with.
    sheet_path = SHEETS / f"{ev['date']}-{_slug(ev['name'])}.json"
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
            row["model"] = {"p_a": round(pa, 4), "winner": w[side], "method": method, "p_win": round(max(pa, 1 - pa), 4),
                            "joint": {s: {m: round(v, 4) for m, v in j[s].items()} for s in j}}
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
             "dec_cal": dec_cal, "method_adjust": adjust, "bouts": bouts}
    DRAFT.parent.mkdir(exist_ok=True)
    DRAFT.write_text(json.dumps(draft, indent=1, ensure_ascii=False))
    print(f"{ev['name']} ({ev['date']}) · picks lock {draft['locks_at']} · {len(bouts)} bouts")
    for r in bouts:
        m = r["model"]
        mk = ""
        if m and "market_p_a" in r:
            mk = f" · market {r['market_p_a'] if m['winner'] == r['a'] else 1 - r['market_p_a']:.0%} on {m['winner'].split()[-1]}"
        if r.get("read_a"):
            mk += f" · Claude's read {r['read_a']:+.2f} to {r['a'].split()[-1]}"
        print(f"  {r['bout']:<46} " + (f"model: {m['winner']} by {m['method']} ({m['p_win']:.0%} to win; "
              f"{m['joint']['a' if m['winner'] == r['a'] else 'b'][m['method']]:.0%} exact){mk}" if m else f"no model pick (no data on {', '.join(r['no_data'])})"))
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
            "pick": {"winner": bout[side], "side": side, "method": p["method"], "confidence": round(conf_of(p), 2), "why": p.get("why", "").strip()},
            "model": bout.get("model"), "market_p_a": bout.get("market_p_a")})
    return {"event": draft["event"], "date": draft["date"], "results_url": draft["results_url"], "locks_at": draft["locks_at"],
            "locked_at": now, "note": spec.get("note", "").strip(), "dec_cal": draft.get("dec_cal"),
            "method_adjust": draft.get("method_adjust") or {}, "bouts": rows, "graded": False}


def conf_of(p: Dict) -> float:
    return float(p.get("confidence", 0))


def cmd_lock(args) -> int:
    draft = json.loads(Path(args.draft).read_text())
    spec = json.loads(Path(args.picks).read_text())
    try:
        rec = lock(draft, spec)
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
    print(f"{rec['event']}: {len(rec['bouts'])} picks locked at {rec['locked_at']} -> {path}")
    print(f"  same winner as the model on {agree}, same winner and method on {exact}; commit this file before the card.")
    return 0


# ------------------------------------------------------------------- grade
def score(pick_side: Optional[str], pick_method: Optional[str], res: P.Result) -> Dict[str, object]:
    """Pick'em points: 1 for the winner, 1 more for the method when the winner is right."""
    win = pick_side == res.winner
    meth = win and pick_method == res.method
    return {"winner": win, "method": bool(meth), "points": int(win) + int(meth)}


def grade_card(rec: Dict, results: Dict[str, Optional[P.Result]]) -> int:
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
            b["claude"] = score(b["pick"]["side"], b["pick"]["method"], r)
            m = b.get("model")
            if m:
                b["model_score"] = score("a" if m["winner"] == b["a"] else "b", m["method"], r)
        done += 1
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
         "claude": {"n": n, "winners": tot("winner", "claude"), "methods": tot("method", "claude"), "points": tot("points", "claude"),
                    "log_loss": round(claude_ll, 4) if claude_ll is not None else None},
         "model": {"n": nm, "winners": tot("winner", "model_score"), "methods": tot("method", "model_score"),
                   "points": tot("points", "model_score"), "log_loss": round(model_ll, 4) if model_ll is not None else None}}
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
    fetcher = _fetcher(args.cache)
    today = date.today().isoformat()
    for path in sorted(DIR.glob("20*.json")):
        rec = json.loads(path.read_text())
        if rec.get("graded") or (rec["date"] >= today and not args.force):
            continue
        week = {"results_url": rec["results_url"], "event_date": rec["date"], "bets": [{"legs": [{"bout": b["bout"]}]} for b in rec["bouts"] if "result" not in b]}
        n = grade_card(rec, _results_for(fetcher, week))
        rec["graded_at"] = _now()
        path.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
        g = [b for b in rec["bouts"] if "claude" in b]
        print(f"{rec['event']}: {n} bouts graded now; Claude {sum(b['claude']['winner'] for b in g)}/{len(g)} winners, "
              f"{sum(b['claude']['method'] for b in g)} with the method" + ("" if rec["graded"] else " (some results still pending)"))
    s = summarize(load_cards())
    adj = fit_adjust(s)
    if adj:
        ADJUST.write_text(json.dumps(adj, indent=1) + "\n")
        s["method_adjust"] = adj["factors"]
    elif ADJUST.exists():
        s["method_adjust"] = load_adjust()
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(s, indent=1) + "\n")
    c, m = s["claude"], s["model"]
    print(f"Record: Claude {c['winners']}/{c['n']} winners, {c['methods']} methods, {c['points']} pts · model {m['winners']}/{m['n']}, {m['methods']} methods, {m['points']} pts")
    for l in s["lessons"]:
        print(f"  [{l['kind']}] {l['text']}")
    return 0


# -------------------------------------------------------------------- sync
def sync_docs() -> Dict[str, Dict]:
    docs = {}
    if SUMMARY.exists():
        docs["card-summary"] = json.loads(SUMMARY.read_text())
    for rec in load_cards():
        docs["card-" + rec["date"] + "-" + _slug(rec["event"])[:60]] = rec
    return docs


def cmd_sync(args) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    docs = sync_docs()
    for k, v in docs.items():
        (out / f"{k}.json").write_text(json.dumps(v, ensure_ascii=False))
    print(json.dumps([{"op": "set", "collection": "ai_picks", "doc_id": k, "file_path": str((out / f"{k}.json").resolve())} for k in docs], indent=1))
    return 0


def register(sub, data_arg) -> None:
    p = sub.add_parser("card-picks", help="AI Picks: Claude's winner-and-method pick for every bout, graded and tracked (see AI_PICKS.md)")
    ps = p.add_subparsers(dest="card_picks_cmd", required=True)
    q = ps.add_parser("draft", help="the model's pick for every bout on the next UFC card")
    data_arg(q)
    q.add_argument("--event", default="")
    q.add_argument("--cache", default=".cache/pages")
    q.add_argument("--app-data", default="app/data.json")
    q.add_argument("--aliases", default="data/name_aliases.json")
    q.set_defaults(func=cmd_draft)
    q = ps.add_parser("lock", help="record Claude's picks (every bout) before the card starts")
    q.add_argument("--draft", default=str(DRAFT))
    q.add_argument("--picks", required=True, help='{"note": "...", "picks": [{"bout": "A vs B", "winner": "A", "method": "KO/TKO|SUB|DEC", "confidence": 0.62, "why": "..."}]}')
    q.set_defaults(func=cmd_lock)
    q = ps.add_parser("grade", help="grade finished cards and update the record and lessons")
    q.add_argument("--cache", default=".cache/pages")
    q.add_argument("--force", action="store_true")
    q.set_defaults(func=cmd_grade)
    q = ps.add_parser("sync", help="write card-* documents for the page database")
    q.add_argument("--out", default=".cache/card_picks_sync")
    q.set_defaults(func=cmd_sync)
