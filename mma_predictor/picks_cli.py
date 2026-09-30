"""`python -m mma_predictor picks ...`: the weekly AI Picks routine.

    picks sheet    fetch FanDuel's lines for the next UFC card and price every market
    picks place    record this week's bets (or a pass) from a picks file, at sheet prices
    picks settle   grade finished weeks from results two sources agree on
    picks status   bankroll and record (exit code 3 when the bankroll is bust)
    picks sync     write the page-database documents (ai_picks collection)

See AI_PICKS.md for the Friday playbook.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from . import picks as P

DIR = Path("data/ai_picks")
LEDGER = DIR / "ledger.json"
SHEETS = DIR / "sheets"
BFO_HOME = "https://www.bestfightodds.com/"
UA = "mma-predictor/0.1 (personal research)"


def _fetcher(cache: str):
    from .sources.common import Fetcher

    return Fetcher(Path(cache), delay=2.0, user_agent=UA)


def _fresh(fetcher, url: str) -> str:
    """Prices and results change: never read them from the page cache."""
    fetcher._cache_path(url).unlink(missing_ok=True)
    return fetcher.get(url, cache=False)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _pair(a: str, b: str) -> frozenset:
    """A bout's identity across sources: the two surnames (accent- and order-insensitive)."""
    from .sources.wikipedia import match_key

    return frozenset(match_key(x).split()[-1] for x in (a, b) if match_key(x))


def _model(data_json: Path):
    from .model import PRIOR_WEIGHTS, WinModel

    d = json.loads(data_json.read_text())
    blend_w = ((d.get("insights") or {}).get("market") or {}).get("blend", {}).get("weights")
    return WinModel(weights={**PRIOR_WEIGHTS, **d["weights"]}, scale=d.get("calibration_scale", 1.0)), blend_w


# ------------------------------------------------------------------- sheet
def cmd_sheet(args) -> int:
    from .cli import _history
    from .features import BoutContext
    from .methods import method_distribution
    from .predictor import FightPredictor
    from .sources import events
    from .sources.events import link_names
    from .sources.wikipedia import match_key

    fetcher = _fetcher(args.cache)
    # 1. The next UFC card on Wikipedia (the schedule, rounds and title bouts).
    sched = [e for e in events.scheduled_events(_fresh(fetcher, events.EVENTS_URL)) if e["date"] >= date.today().isoformat()]
    if args.event:
        sched = [e for e in sched if args.event.lower() in e["name"].lower()]
    if not sched:
        print("No scheduled UFC event found.")
        return 1
    ev = sched[0]
    card = events.parse_card(_fresh(fetcher, ev["url"])) if ev["url"] else []

    # 2. FanDuel's prices from BestFightOdds, matched to the card by the fighters.
    # BestFightOdds may split one card over several pages ("UFC 332" and "UFC" for the prelims):
    # take every UFC page and keep the bouts Wikipedia also lists (two sources for each bout).
    home = _fresh(fetcher, BFO_HOME)
    wiki_pairs = {_pair(w["a"], w["b"]) for w in card}
    found, pages = {}, []
    for name, url in P.event_links(home):
        if not name.upper().startswith("UFC"):
            continue
        parsed = P.parse_event(_fresh(fetcher, url), url)
        hits = [b for b in parsed["bouts"] if _pair(b["a"], b["b"]) in wiki_pairs]
        if hits:
            pages.append(url)
        for b in hits:
            found.setdefault(_pair(b["a"], b["b"]), b)
    if not found:
        print(f"No FanDuel lines found for {ev['name']} on BestFightOdds yet.")
        return 1
    order = {_pair(w["a"], w["b"]): i for i, w in enumerate(card)}
    best = {"url": pages[0], "urls": pages, "bouts": sorted(found.values(), key=lambda b: order[_pair(b["a"], b["b"])])}
    unpriced = [f"{w['a']} vs {w['b']}" for w in card if _pair(w["a"], w["b"]) not in found]

    # 3. Price it with the model the site shows, blended with FanDuel's own moneyline.
    h = _history(args)
    model, blend_w = _model(Path(args.app_data))
    predictor = FightPredictor(h, model)
    aliases = json.loads(Path(args.aliases).read_text()) if Path(args.aliases).exists() else {}
    names = {n for b in best["bouts"] for n in (b["a"], b["b"])}
    linked = link_names(names, set(h.names()), aliases)
    timing = P.Timing.from_fights(h.fights)
    from .reads import Reads

    reads = Reads.load()  # Claude's scouting reads: nudge the model before it meets the market
    dec_cal = tuple(json.loads(CALIBRATION.read_text())["dec_cal"]) if CALIBRATION.exists() else None
    if dec_cal is None:
        print("warning: no decision calibration (run `picks calibrate`); props will be biased toward finishes")
    when = date.fromisoformat(ev["date"])
    bouts, markets, skipped = [], [], []
    for b in best["bouts"]:
        wiki = next((w for w in card if _pair(w["a"], w["b"]) == _pair(b["a"], b["b"])), None)
        rounds = int(wiki["rounds"]) if wiki else 3
        a, bb = linked.get(b["a"]), linked.get(b["b"])
        if not a or not bb:
            skipped.append(f"{b['a']} vs {b['b']} (not enough data on {'/'.join(x for x, y in ((b['a'], a), (b['b'], bb)) if not y)})")
            continue
        sa, sb, x = predictor.features(a, bb, when, BoutContext(rounds, bool(wiki and wiki["title"])))
        pa_stats = sigmoid_logit(model, x)
        read = reads.logit(a, bb)
        pa = P.sigmoid(P._logit(pa_stats) + read)
        rows = P.price_bout(b, pa, method_distribution(sa, sb, rounds), method_distribution(sb, sa, rounds), rounds, timing, blend_w, dec_cal)
        bouts.append({"bout": f"{b['a']} vs {b['b']}", "a": b["a"], "b": b["b"], "dataset": [a, bb], "rounds": rounds,
                      "title": bool(wiki and wiki["title"]), "p_model_a": round(pa, 4), "p_stats_a": round(pa_stats, 4), "read_a": round(read, 3), "ml": b["ml"], "markets": len(rows)})
        markets += rows
    sheet = {
        "event": ev["name"], "date": ev["date"], "results_url": ev["url"], "odds_url": best["url"], "book": "FanDuel",
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "event_starts": f"{ev['date']}T12:00:00+00:00",
        "odds_urls": best["urls"], "unpriced": unpriced,
        "blend_weights": blend_w, "dec_cal": dec_cal, "prop_shrink": P.PROP_SHRINK, "bouts": bouts, "skipped": skipped,
        "markets": sorted(markets, key=lambda m: -m["ev"]),
    }
    SHEETS.mkdir(parents=True, exist_ok=True)
    out = Path(args.out) if args.out else SHEETS / f"{ev['date']}-{_slug(ev['name'])}.json"
    out.write_text(json.dumps(sheet, indent=1))
    led = P.Ledger(Path(args.ledger))
    print(f"{ev['name']} ({ev['date']}) · FanDuel via {best['url']}")
    print(f"Bankroll ${led.bankroll():.2f} · available ${led.available():.2f}" + ("  ** BUST **" if led.bust() else ""))
    for b in bouts:
        rd = f" (stats {b['p_stats_a']:.0%}, read {b['read_a']:+.2f})" if b["read_a"] else ""
        print(f"  {b['bout']:<44} model {b['p_model_a']:.0%}{rd} · FanDuel {b['ml']['a']} / {b['ml']['b']} · {b['rounds']} rds")
    for s in skipped:
        print(f"  skipped: {s}")
    for s in unpriced:
        print(f"  no FanDuel line yet: {s}")
    print(f"\n{'id':<34} {'selection':<40} {'odds':>6} {'ours':>6} {'FD':>6} {'EV':>7} {'¼K $':>6}")
    for m in sheet["markets"][: args.top]:
        stake = led.available() * m["kelly"] / 4
        print(f"{m['id']:<34} {m['selection'][:40]:<40} {m['odds']:>+6} {m['p']:>6.1%} {m['p_fanduel']:>6.1%} {m['ev']:>+7.1%} {stake:>6.2f}")
    print(f"\n{len(markets)} markets priced -> {out}")
    return 0


def sigmoid_logit(model, x) -> float:
    from .model import sigmoid

    return sigmoid(model.logit(x))


# --------------------------------------------------------------- calibrate
CALIBRATION = DIR / "calibration.json"


def cmd_calibrate(args) -> int:
    """Fit the decision-rate correction on recent UFC bouts (point-in-time snapshots); report a later-years test."""
    from .cli import _history
    from .data import Method
    from .features import BoutContext
    from .methods import method_distribution
    from .predictor import FightPredictor

    h = _history(args)
    model, _ = _model(Path(args.app_data))
    pr = FightPredictor(h, model)
    since, split = date(args.since, 1, 1), date(args.test_from, 1, 1)
    timing = P.Timing.from_fights([f for f in h.fights if f.date < since])
    rows = []
    for f in h.fights:
        if f.date < since or not f.event.startswith("UFC") or not f.is_scored:
            continue
        try:
            sa, sb, x = pr.features(f.fighter_a, f.fighter_b, f.date, BoutContext(f.scheduled_rounds, f.title_fight))
        except KeyError:
            continue
        if sa.fights < 2 or sb.fights < 2:
            continue
        p = P.model_prob(("distance", True), sigmoid_logit(model, x), method_distribution(sa, sb, f.scheduled_rounds),
                         method_distribution(sb, sa, f.scheduled_rounds), f.scheduled_rounds, timing)
        rows.append((f.date, p, int(f.method not in (Method.KO, Method.SUB))))
    train = [(p, y) for d, p, y in rows if d < split]
    test = [(p, y) for d, p, y in rows if d >= split]
    held = P.fit_distance(train)
    brier = lambda xs, c=None: sum(((P.sigmoid(c[0] + c[1] * P._logit(p)) if c else p) - y) ** 2 for p, y in xs) / len(xs)  # noqa: E731
    final = P.fit_distance(train + test)
    out = {"dec_cal": list(final), "fitted_on": len(rows), "since": since.isoformat(),
           "test": {"from": split.isoformat(), "n": len(test), "actual": round(sum(y for _, y in test) / len(test), 4),
                    "raw_mean": round(sum(p for p, _ in test) / len(test), 4), "raw_brier": round(brier(test), 4),
                    "calibrated_brier": round(brier(test, held), 4)}}
    CALIBRATION.parent.mkdir(parents=True, exist_ok=True)
    CALIBRATION.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0


# ------------------------------------------------------------------- place
def cmd_place(args) -> int:
    sheet = json.loads(Path(args.sheet).read_text())
    spec = json.loads(Path(args.bets).read_text())
    led = P.Ledger(Path(args.ledger))
    if led.bust():
        print("Bankroll is bust: no bets can be placed.")
        return 3
    days = (date.fromisoformat(sheet["date"]) - date.today()).days
    if not 0 <= days <= 3 and not args.any_date:
        print(f"{sheet['event']} is {days} days away: picks are for this weekend's card only.")
        return 1
    by_id = {m["id"]: m for m in sheet["markets"]}
    week = led.place({"name": sheet["event"], "date": sheet["date"], "url": sheet["odds_url"], "results_url": sheet["results_url"]},
                     by_id, spec.get("picks", []), spec.get("note", ""), event_starts=sheet.get("event_starts"))
    week["sheet"] = str(Path(args.sheet))
    week["odds_urls"] = sheet.get("odds_urls", [sheet["odds_url"]])
    week["sheet_fetched_at"] = sheet["fetched_at"]
    led.save()
    print(f"{week['event']}: {len(week['bets'])} bets, ${week['staked']:.2f} staked of ${week['available_before']:.2f}")
    for b in week["bets"]:
        print(f"  ${b['stake']:.2f} {b['kind']} {' + '.join(l['selection'] for l in b['legs'])} @ {b['odds']:+d} (to win ${b['to_win']:.2f}, EV {b['ev']:+.1%})")
    return 0


# ------------------------------------------------------------------ settle
def _results_for(fetcher, week, log=print) -> Dict[str, Optional[P.Result]]:
    """Results for this week's bouts that Wikipedia and Sherdog agree on."""
    from .sources import events, sherdog
    from .sources.wikipedia import match_key

    card = events.parse_card(_fresh(fetcher, week["results_url"]))
    decided = [r for r in card if r.get("round")]
    when = date.fromisoformat(week["event_date"])
    out: Dict[str, Optional[P.Result]] = {}
    for bout in sorted({l["bout"] for b in week["bets"] for l in b["legs"] if not l.get("grade")}):
        a, b = bout.split(" vs ", 1)
        ka, kb = match_key(a), match_key(b)
        last = lambda k: k.split()[-1:]  # noqa: E731
        toks = lambda k: frozenset(k.split())  # noqa: E731  ("Wang Cong" == "Cong Wang")
        row = next((r for r in card if {match_key(r["a"]), match_key(r["b"])} == {ka, kb}), None) or \
            next((r for r in card if {toks(match_key(r["a"])), toks(match_key(r["b"]))} == {toks(ka), toks(kb)}), None) or \
            next((r for r in card if {tuple(last(match_key(r["a"]))), tuple(last(match_key(r["b"])))} == {tuple(last(ka)), tuple(last(kb))}), None)
        if row is None:
            if decided and date.today() > when:
                log(f"  {bout}: not on the results card -> void (bout did not take place)")
                out[bout] = None
            continue
        wr = P.wiki_result(row)
        if wr is None:
            log(f"  {bout}: no result on Wikipedia yet")
            continue
        if match_key(row["a"]) != ka and toks(match_key(row["a"])) != toks(ka) and last(match_key(row["a"])) != last(ka):
            wr = P.flip(wr)  # Wikipedia's left fighter is our b
        # Second source: the fighter's Sherdog record.
        sr = None
        for name, opp in ((a, b), (b, a)):
            try:
                hits = sherdog.search_fighter(fetcher, name)
            except OSError as exc:
                log(f"  {bout}: Sherdog search failed ({exc})")
                continue
            hit = next((u for n, u in hits if match_key(n) == match_key(name)), None)
            if not hit:
                continue
            page = sherdog.parse_fighter(_fresh(fetcher, hit), hit)
            r = P.sherdog_result(page.bouts, match_key(opp), when, match_key)
            if r is None:
                opp_last = last(match_key(opp))
                r = next((P.sherdog_result([cb], match_key(cb.opponent), when, match_key) for cb in page.bouts
                          if last(match_key(cb.opponent)) == opp_last and abs((cb.date - when).days) <= 2), None)
            if r is not None:
                sr = r if name == a else P.flip(r)
                break
        if P.agree(wr, sr):
            out[bout] = wr
        else:
            log(f"  {bout}: waiting for sources to agree (Wikipedia {wr}, Sherdog {sr})")
    return out


def _closing(fetcher, week, log=print) -> None:
    """FanDuel's last price on each leg, for closing-line value (did we beat the close?)."""
    by_bout = {}
    for url in week.get("odds_urls") or [week["odds_url"]]:
        try:
            ev = P.parse_event(_fresh(fetcher, url), url)
        except OSError as exc:
            log(f"  closing lines unavailable ({exc})")
            continue
        by_bout.update({f"{b['a']} vs {b['b']}": b for b in ev["bouts"]})
    for bet in week["bets"]:
        for leg in bet["legs"]:
            b = by_bout.get(leg["bout"])
            if not b or leg.get("close_odds") is not None:
                continue
            key = leg["market"]
            if key[0] == "ml":
                leg["close_odds"] = b["ml"].get(key[1])
            else:
                a_, b_ = leg["bout"].split(" vs ", 1)
                for pr in b["props"]:
                    if list(P.canonical(pr["label"], a_, b_, 5) or []) == key:
                        leg["close_odds"] = pr["odds"]
                        break
        if all(l.get("close_odds") for l in bet["legs"]):
            close = 1.0
            for l in bet["legs"]:
                close *= P.decimal(l["close_odds"])
            bet["clv"] = round(bet["decimal"] / close - 1, 4)


def cmd_settle(args) -> int:
    led = P.Ledger(Path(args.ledger))
    fetcher = _fetcher(args.cache)
    today = date.today().isoformat()
    pending = 0
    for week in led.weeks:
        if week["settled"] or week["event_date"] >= today and not args.force:
            continue
        print(f"{week['event']} ({week['event_date']})")
        _closing(fetcher, week)
        results = _results_for(fetcher, week)
        missing = led.settle(week, results, ["Wikipedia event page", "Sherdog fighter records"])
        for bet in week["bets"]:
            print(f"  {bet['status']:<5} ${bet['profit']:+.2f}  {' + '.join(l['selection'] for l in bet['legs'])}")
        if missing:
            pending += 1
            print(f"  still waiting on: {', '.join(missing)}")
    led.save()
    s = led.summary()
    print(f"Bankroll ${s['bankroll']:.2f} (start ${s['start']:.2f}) · record {s['won']}-{s['lost']}" + ("  ** BUST **" if s["bust"] else ""))
    return 3 if s["bust"] else (2 if pending else 0)


def cmd_status(args) -> int:
    led = P.Ledger(Path(args.ledger))
    s = led.summary()
    print(json.dumps({k: v for k, v in s.items() if k != "curve"}, indent=1))
    return 3 if s["bust"] else 0


# -------------------------------------------------------------------- sync
def sync_docs(led: P.Ledger) -> Dict[str, Dict[str, object]]:
    """The page database's ai_picks documents: one summary plus one per week."""
    docs = {"summary": led.summary()}
    for w in led.weeks:
        docs[w["id"]] = {k: v for k, v in w.items() if k not in ("sheet",)}
    return docs


def cmd_sync(args) -> int:
    led = P.Ledger(Path(args.ledger))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    docs = sync_docs(led)
    for doc_id, body in docs.items():
        (out / f"{doc_id}.json").write_text(json.dumps(body, indent=1))
    print(json.dumps([{"op": "set", "collection": "ai_picks", "doc_id": k, "file_path": str((out / f"{k}.json").resolve())} for k in docs], indent=1))
    return 0


def register(sub, data_arg) -> None:
    p = sub.add_parser("picks", help="AI Picks: FanDuel betting sheet, ledger and settlement (see AI_PICKS.md)")
    ps = p.add_subparsers(dest="picks_cmd", required=True)

    def common(q):
        q.add_argument("--ledger", default=str(LEDGER))
        q.add_argument("--cache", default=".cache/pages")

    q = ps.add_parser("sheet", help="price every FanDuel market on the next UFC card")
    data_arg(q)
    common(q)
    q.add_argument("--event", default="", help="part of the event name (default: the next UFC event)")
    q.add_argument("--app-data", default="app/data.json", help="model weights the site uses")
    q.add_argument("--aliases", default="data/name_aliases.json")
    q.add_argument("--out", default="")
    q.add_argument("--top", type=int, default=40)
    q.set_defaults(func=cmd_sheet)

    q = ps.add_parser("calibrate", help="fit the decision-rate correction for props")
    data_arg(q)
    q.add_argument("--app-data", default="app/data.json")
    q.add_argument("--since", type=int, default=2019)
    q.add_argument("--test-from", type=int, default=2023)
    q.set_defaults(func=cmd_calibrate)

    q = ps.add_parser("place", help="record this week's bets from a picks file")
    common(q)
    q.add_argument("--sheet", required=True)
    q.add_argument("--any-date", action="store_true", help="allow a card more than 3 days out")
    q.add_argument("--bets", required=True, help='{"note": "...", "picks": [{"legs": [market ids], "stake": 5, "reasoning": "..."}]}')
    q.set_defaults(func=cmd_place)

    q = ps.add_parser("settle", help="grade finished weeks")
    common(q)
    q.add_argument("--force", action="store_true", help="try weeks whose event date hasn't passed")
    q.set_defaults(func=cmd_settle)

    q = ps.add_parser("status", help="bankroll and record")
    common(q)
    q.set_defaults(func=cmd_status)

    q = ps.add_parser("sync", help="write ai_picks documents for the page database")
    common(q)
    q.add_argument("--out", default=".cache/ai_picks_sync")
    q.set_defaults(func=cmd_sync)
