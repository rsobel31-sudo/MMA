"""Command-line interface.

    python -m mma_predictor predict  --data DIR "Fighter A" "Fighter B" [--rounds 5] [--odds -150 +130]
    python -m mma_predictor card     --data DIR --card card.csv
    python -m mma_predictor profile  --data DIR "Fighter"
    python -m mma_predictor rankings --data DIR [--top 25]
    python -m mma_predictor train    --data DIR --out models/model.json
    python -m mma_predictor backtest --data DIR
    python -m mma_predictor import   {sherdog,tapology} SEED... --out DIR [--depth 1]
    python -m mma_predictor merge    DIR1 DIR2 ... --out DIR
"""

from __future__ import annotations

import argparse
from datetime import date
import sys
from pathlib import Path
from typing import List, Optional

from .adjustments import Adjustments
from .backtest import walk_forward
from .data import load_card, load_dataset
from .history import FightHistory
import math

from .model import WinModel, fit_scale, sigmoid
from .predictor import FightPredictor, build_training_set
from .scouting import Scouting
from .skills import CATEGORIES, SUB_LABELS
from .styles import scouting_line

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "sample"
DEFAULT_SCOUTING = Path(__file__).resolve().parent.parent / "data" / "scouting"


def _history(args) -> FightHistory:
    from .external import for_dataset

    bios, fights = load_dataset(Path(args.data))
    scouting = Scouting.load(Path(args.scouting)) if getattr(args, "scouting", None) else None
    external = None if getattr(args, "no_external", False) else for_dataset(Path(args.data), bios)
    return FightHistory(bios, fights, scouting=scouting, external=external)


def _predictor(args, history: FightHistory) -> FightPredictor:
    model = WinModel.load(Path(args.model)) if getattr(args, "model", None) else None
    if model is None and getattr(args, "fit", False):
        model = WinModel()
        X, y, _ = build_training_set(history)
        model.fit(X, y)
    adjustments = Adjustments.load(Path(args.adjustments)) if getattr(args, "adjustments", None) else None
    return FightPredictor(history, model, adjustments)


def cmd_predict(args) -> int:
    h = _history(args)
    pred = _predictor(args, h).predict(
        args.fighter_a,
        args.fighter_b,
        scheduled_rounds=args.rounds,
        title_fight=args.title,
        odds_a=args.odds[0] if args.odds else None,
        odds_b=args.odds[1] if args.odds else None,
    )
    print(pred.report())
    return 0


def cmd_card(args) -> int:
    h = _history(args)
    p = _predictor(args, h)
    rows = []
    for m in load_card(Path(args.card)):
        pred = p.predict_matchup(m)
        rows.append(pred)
        if args.verbose:
            print(pred.report())
            print()
    print(f"{'Matchup':<48} {'Pick':<24} {'Prob':>6}  {'Likely outcome':<30} {'Edge':>6}")
    for pred in rows:
        f, meth, pp = pred.most_likely_outcome
        edge = pred.edge_a
        edge_s = "" if edge is None else f"{(edge if pred.pick == pred.fighter_a else -edge):+.1%}"
        print(
            f"{pred.fighter_a + ' vs ' + pred.fighter_b:<48} {pred.pick:<24} {pred.pick_prob:6.1%}  "
            f"{f.split()[-1] + ' by ' + meth + f' ({pp:.0%})':<30} {edge_s:>6}"
        )
    return 0


def cmd_profile(args) -> int:
    h = _history(args)
    name = h.resolve(args.fighter)
    s = h.snapshot(name)
    print(scouting_line(s))
    print("\nRatings (1500 = average):")
    print(f"  Overall {s.elo:6.0f}   = {', '.join(f'{w:.0%} {c}' for c, w in h.skills.config.category_weights.items())}")
    for cat, keys in CATEGORIES.items():
        subs = "  ".join(f"{SUB_LABELS[k]} {s.ratings[k]:.0f}" for k in keys)
        print(f"  {cat.title():<9} {getattr(s, cat):6.0f}   {subs}")
    print(f"\nWins by method:   " + "  ".join(f"{k} {v:.0%}" for k, v in s.win_methods.items()))
    print(f"Losses by method: " + "  ".join(f"{k} {v:.0%}" for k, v in s.loss_methods.items()))
    print(f"Strength of schedule (avg opp Elo): {s.sos:.0f}; avg Elo of beaten opponents: {s.quality_win_elo:.0f}")
    if s.layoff_days is not None:
        print(f"Days since last fight: {s.layoff_days}")
    print("\nRecent bouts:")
    for a in reversed(s.recent):
        res = {True: "W", False: "L", None: "D/NC"}[a.result]
        print(f"  {a.fight.date}  {res:<4} vs {a.opponent:<26} {a.method.value:<7} R{a.fight.end_round}  (opp Elo {a.opp_elo:.0f})")
    return 0


def cmd_rankings(args) -> int:
    h = _history(args)
    snaps = [h.snapshot(n) for n in h.names()]
    key = {"overall": "proven", "raw": "elo"}.get(args.by, args.by)
    wc = (args.weight_class or "").lower()
    rows = sorted(
        (s for s in snaps if s.fights >= args.min_fights and (not wc or s.bio.weight_class.lower() == wc)
         and (args.active_years <= 0 or (s.layoff_days is not None and s.layoff_days <= args.active_years * 365))),
        key=lambda s: -getattr(s, key),
    )
    print(f"{'':>4} {'Fighter':<28} {'Proven':>7} {'Overall':>7} {'±':>4} {'Strike':>7} {'Wrestle':>7} {'Grapple':>7} {'Record':>8}")
    for i, s in enumerate(rows[: args.top], 1):
        inactive = " (inactive)" if s.layoff_days and s.layoff_days > 730 else ""
        print(f"{i:>3}. {s.name:<28} {s.proven:7.0f} {s.elo:7.0f} {s.rd:4.0f} {s.striking:7.0f} {s.wrestling:7.0f} {s.grappling:7.0f} {s.record:>8}{inactive}")
    return 0


def cmd_train(args) -> int:
    h = _history(args)
    X, y, _ = build_training_set(h, min_prior_fights=args.min_fights)
    model = WinModel()
    rep = model.fit(X, y, l2=args.l2, iterations=args.iterations)
    print(f"Trained on {rep.samples} bouts: log-loss {rep.prior_log_loss:.4f} (priors) -> {rep.log_loss:.4f}")
    for k, v in sorted(model.weights.items(), key=lambda kv: -abs(kv[1])):
        print(f"  {k:<20} {v:+.3f}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    model.save(Path(args.out))
    print(f"Saved to {args.out}")
    return 0


def cmd_backtest(args) -> int:
    kw = dict(train_fraction=args.train_fraction, retrain_every=args.retrain_every, min_prior_fights=args.min_fights, event_prefix=args.events)
    if args.split_sports:
        from .backtest import walk_forward_split

        bios, fights = load_dataset(Path(args.data))
        scouting = Scouting.load(Path(args.scouting)) if getattr(args, "scouting", None) else None
        res = walk_forward_split(bios, fights, scouting, **kw)
        print("Men's and women's MMA as separate sports (own ratings, base rates and model)\n")
    else:
        res = walk_forward(_history(args), **kw)
    print(res.report())
    return 0


def cmd_import(args) -> int:
    from .sources import common, kaggle_ufc, sherdog, tapology, ufcstats

    if args.source == "kaggle":
        if not args.dir:
            raise ValueError(f"--dir: the unzipped dataset (download: {kaggle_ufc.DOWNLOAD_URL})")
        fighters, fights = kaggle_ufc.convert(Path(args.dir))
        common.write_dataset(Path(args.out), fighters, fights)
        print(f"Wrote {len(fighters)} fighters and {len(fights)} bouts to {args.out}")
        return 0
    fetcher = common.Fetcher(Path(args.cache), delay=args.delay)
    if args.source == "ufcstats":
        fighters, fights = ufcstats.crawl(fetcher, events=args.ufc_events or None)
        common.write_dataset(Path(args.out), fighters, fights)
        print(f"Wrote {len(fighters)} fighters and {len(fights)} bouts to {args.out}")
        return 0
    mod = sherdog if args.source == "sherdog" else tapology
    seeds = [mod.fighter_url(s) for s in args.seeds]
    if args.ufc_events:
        if args.source != "sherdog":
            raise ValueError("--ufc-events is only supported for sherdog")
        seeds += sherdog.recent_event_fighters(fetcher, args.ufc_events)
    if not seeds:
        raise ValueError("give seed fighters and/or --ufc-events")
    pages = common.crawl(seeds, fetcher, mod.parse_fighter, depth=args.depth, max_fighters=args.max_fighters)
    fighters, fights = common.pages_to_rows(pages, args.source)
    common.write_dataset(Path(args.out), fighters, fights)
    print(f"Wrote {len(fighters)} fighters and {len(fights)} bouts to {args.out}")
    return 0


def cmd_enrich(args) -> int:
    """Add current UFC division and gender (Wikipedia roster + fight-graph propagation)."""
    import csv

    from .sources import common, wikipedia

    data_dir = Path(args.data)
    if args.roster_html:
        html = Path(args.roster_html).read_text(encoding="utf-8")
    else:
        fetcher = common.Fetcher(Path(args.cache), delay=1.0, user_agent="mma-predictor/0.1 (personal research)")
        html = fetcher.get(wikipedia.ROSTER_URL)
    roster = wikipedia.parse_roster(html)
    with open(data_dir / "fighters.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with open(data_dir / "fights.csv", newline="", encoding="utf-8") as fh:
        bouts = [(r["fighter_a"], r["fighter_b"]) for r in csv.DictReader(fh)]
    matched = wikipedia.resolve([r["name"] for r in rows], roster)
    seeds = {n: g for n, (_, g) in matched.items()}
    # Divisions only women contest are a second source of known women.
    for r in rows:
        if r["name"] not in seeds and r.get("weight_class") in ("Strawweight", "Atomweight"):
            seeds[r["name"]] = "F"
    # Women's MMA has no divisions above featherweight, so heavier listed
    # classes are men's. These are seeds too, and they override propagation.
    men_only = {"Lightweight", "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"}
    for r in rows:
        if r["name"] not in seeds and r.get("weight_class") in men_only:
            seeds[r["name"]] = "M"
    genders = wikipedia.reconcile_gender(bouts, wikipedia.propagate_gender(bouts, seeds))
    women_classes = {"Atomweight", "Strawweight", "Flyweight", "Bantamweight", "Featherweight"}
    for r in rows:
        if r["name"] in matched:
            r["weight_class"], _ = matched[r["name"]]
            r["weight_class_source"] = "ufc-roster"
        elif r.get("weight_class"):
            r["weight_class_source"] = r.get("weight_class_source") or r.get("source") or "sherdog"
        r["gender"] = genders.get(r["name"], "")
        if r["gender"] == "F" and r.get("weight_class") and r["weight_class"] not in women_classes:
            # A men's class on a woman's record is a source error; infer it from opponents instead.
            r["weight_class"], r["weight_class_source"] = "", ""
    common.write_fighters(data_dir, rows)
    print(f"Roster: {len(roster)} UFC fighters, {len(matched)} matched to this dataset")
    known = sum(1 for r in rows if r["gender"])
    print(f"Gender known for {known} of {len(rows)} fighters "
          f"({sum(1 for r in rows if r['gender'] == 'F')} women, {sum(1 for r in rows if r['gender'] == 'M')} men)")
    return 0


def cmd_upcoming(args) -> int:
    """Fetch scheduled UFC cards (Wikipedia) to data/upcoming.json."""
    import json

    from .sources import common, events

    fetcher = common.Fetcher(Path(args.cache), delay=1.0, user_agent="mma-predictor/0.1 (personal research)")
    if args.refresh:  # the schedule changes daily; drop cached copies of these pages
        for url in [events.EVENTS_URL] + [e["url"] for e in events.scheduled_events(fetcher.get(events.EVENTS_URL))]:
            fetcher._cache_path(url).unlink(missing_ok=True)
    cards = events.upcoming_cards(fetcher, limit=args.limit)
    Path(args.out).write_text(json.dumps({"fetched": date.today().isoformat(), "source": events.EVENTS_URL, "events": cards}, indent=1))
    print(f"Wrote {len(cards)} events, {sum(len(e['bouts']) for e in cards)} bouts to {args.out}")
    return 0


def cmd_rebuild(args) -> int:
    """Rebuild a Sherdog dataset from every fighter page in the cache."""
    from .sources import common, sherdog

    pages = sherdog.pages_from_cache(Path(args.cache))
    fighters, fights = common.pages_to_rows(pages, "sherdog")
    common.write_dataset(Path(args.data), fighters, fights)
    print(f"Rebuilt {args.data}: {len(pages)} fighter pages, {len(fighters)} fighters, {len(fights)} bouts")
    return 0


def spearman(xs: List[float], ys: List[float]) -> float:
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for pos, i in enumerate(order):
            r[i] = pos
        return r

    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    if n < 3:
        return float("nan")
    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1 - 6 * d2 / (n * (n * n - 1))


def cmd_compare(args) -> int:
    """How closely our proven rating orders each division compared with the official UFC rankings."""
    import json

    from .sources.events import link_names

    h = _history(args)
    ranked = json.loads(Path(args.rankings).read_text())["rankings"]
    aliases = json.loads(Path(args.aliases).read_text()) if Path(args.aliases).exists() else {}
    linked = link_names({r["name"] for r in ranked}, set(h.names()), aliases)
    rhos = []
    for division in dict.fromkeys(r["division"] for r in ranked):
        rows = [r for r in ranked if r["system"] == args.system and r["division"] == division]
        pairs = []
        for r in rows:
            n = linked.get(r["name"])
            if n:
                s = h.snapshot(n)
                pairs.append((0 if r["rank"] in ("C", "IC") else int(r["rank"]), n, getattr(s, args.by)))
        if len(pairs) < 5:
            continue
        rho = spearman([-p[0] for p in pairs], [p[2] for p in pairs])
        rhos.append(rho)
        ours = sorted(pairs, key=lambda p: -p[2])
        print(f"\n{division}: rank correlation {rho:+.2f} ({len(pairs)} of {len(rows)} ranked fighters in data)")
        for i, (off, n, v) in enumerate(ours, 1):
            flag = "  <-- we rate much higher" if off - i >= 6 else ("  <-- we rate much lower" if i - off >= 6 else "")
            print(f"  ours #{i:<2} UFC {('C' if off == 0 else '#' + str(off)):<4} {n:<26} {v:6.0f}{flag}")
    if rhos:
        print(f"\nMean rank correlation across {len(rhos)} divisions: {sum(rhos) / len(rhos):+.3f}")
    return 0


def cmd_analyze(args) -> int:
    """Regression of past results on every factor, and model accuracy by matchup pattern."""
    from .analysis import insights

    h = _history(args)
    res = walk_forward(h, event_prefix=args.events)
    scale = fit_scale((math.log(p / (1 - p)), int(f.winner == f.fighter_a)) for f, p, _ in res.predictions) if args.calibrate else 1.0
    preds = [(f, sigmoid(scale * math.log(p / (1 - p))), x) for f, p, x in res.predictions]
    X, y, used = build_training_set(h)
    keep = [i for i, f in enumerate(used) if not args.events or f.event.lower().startswith(args.events.lower())]
    st = insights(h, preds, [X[i] for i in keep], [y[i] for i in keep])
    print(f"Confidence calibration scale: {scale}" + ("" if args.calibrate else " (off)"))
    print(f"Regression on {st['n_regression']} bouts (effect of +1 standard deviation, in log-odds)")
    for r in st["regression"]:
        stars = "***" if r["p"] < 0.001 else "**" if r["p"] < 0.01 else "*" if r["p"] < 0.05 else ""
        print(f"  {r['label']:<50} {r['coef_per_sd']:+.3f} ± {r['se']:.3f}  OR {r['odds_ratio_per_sd']:.2f}  p={r['p']:.3f} {stars}")
    print(f"\nModel accuracy by confidence ({st['n_bouts']} out-of-sample bouts)")
    for b in st["calibration"]:
        print(f"  {b['from']:.0%}-{b['to']:.0%}: n={b['n']:<4} favourite won {b['hit_rate']:.0%}")
    print("\nMatchup patterns: actual win rate of the side with the edge vs what the model expected")
    for p in sorted(st["patterns"], key=lambda r: -abs(r.get("z", 0))):
        if not p["n"]:
            continue
        print(f"  {p['label']:<42} n={p['n']:<4} won {p['win_rate']:.0%}  model {p['expected']:.0%}  gap {p['gap'] * 100:+5.1f}  z={p['z']:+.1f}  {p['verdict']}")
    return 0


def cmd_verify(args) -> int:
    """Build a dataset from Sherdog + UFCStats that keeps only what a second source confirms."""
    from .verify import build_verified

    rep = build_verified(Path(args.data), Path(args.stats), Path(args.statsfight), Path(args.out), strict_stats=args.strict_stats,
                         fightmatrix_path=Path(args.fightmatrix), odds_path=Path(args.odds))
    total = sum(rep["results"].values())
    print(f"UFCStats bouts: {total}")
    for k, v in sorted(rep["results"].items(), key=lambda kv: -kv[1]):
        print(f"  result vs Sherdog, {k}: {v}")
    for k, v in sorted(rep["statsfight_results"].items(), key=lambda kv: -kv[1]):
        print(f"  result vs StatsFight, {k}: {v}")
    for k, v in sorted(rep["stats"].items(), key=lambda kv: -kv[1]):
        print(f"  stats {k}: {v}")
    for k in ("dob", "height", "reach"):
        print(f"  {k}: {rep[k]}")
    if rep.get("odds"):
        print(f"  betting lines: {rep['odds']}")
    for c in rep["conflicts"][:10]:
        print(f"  conflict {c['date']} {c['bout']}: UFCStats {c['ufcstats']}, Sherdog {c['sherdog']}, StatsFight {c['statsfight']}")
    print(f"Wrote {args.out} (report: {args.out}/verification.json)")
    return 0


def cmd_merge(args) -> int:
    from .sources.merge import merge_datasets

    nf, nb = merge_datasets([Path(d) for d in args.dirs], Path(args.out))
    print(f"Merged into {args.out}: {nf} fighters, {nb} bouts")
    return 0


def cmd_export(args) -> int:
    from .export import export, write

    h = _history(args)
    model = WinModel.load(Path(args.model)) if args.model else None
    if model is None:
        model = WinModel()
        X, y, _ = build_training_set(h)
        model.fit(X, y)
    summary = None
    study = None
    if not args.no_backtest:
        from .analysis import insights

        res = walk_forward(h, event_prefix=args.events)
        summary = {
            "n": res.model.n, "accuracy": res.model.accuracy, "log_loss": res.model.log_loss,
            "elo_accuracy": res.elo.accuracy, "scope": args.events or "",
            "high_conf_n": res.high_conf.n, "high_conf_accuracy": res.high_conf.accuracy,
            "by_sport": {k: {"n": v.n, "accuracy": v.accuracy, "log_loss": v.log_loss} for k, v in res.by_sport.items()},
            "fair": {"n": res.fair.n, "accuracy": res.fair.accuracy, "log_loss": res.fair.log_loss, "elo_accuracy": res.fair_elo.accuracy},
        }
        # Calibrate confidence on the out-of-sample predictions only, then judge
        # patterns and confidence bands against the calibrated predictions.
        model.scale = fit_scale((math.log(p / (1 - p)), int(f.winner == f.fighter_a)) for f, p, _ in res.predictions)
        summary["calibration_scale"] = model.scale
        calibrated = [(f, sigmoid(model.scale * math.log(p / (1 - p))), x) for f, p, x in res.predictions]
        X, y, used = build_training_set(h)
        keep = [i for i, f in enumerate(used) if not args.events or f.event.lower().startswith(args.events.lower())]
        study = insights(h, calibrated, [X[i] for i in keep], [y[i] for i in keep])
    import json

    upcoming = json.loads(Path(args.upcoming).read_text()) if args.upcoming and Path(args.upcoming).exists() else None
    aliases = json.loads(Path(args.aliases).read_text()) if args.aliases and Path(args.aliases).exists() else {}
    rankings = None
    if args.rankings and Path(args.rankings).exists():
        rankings = json.loads(Path(args.rankings).read_text()).get("rankings")
    from .export import fightmatrix_metrics
    from .external import DEFAULT_PATH as FM_PATH

    vdir = Path(args.data)
    checks = json.loads((vdir / "fighter_checks.json").read_text()) if (vdir / "fighter_checks.json").exists() else None
    verification = None
    if (vdir / "verification.json").exists():
        rep = json.loads((vdir / "verification.json").read_text())
        verification = {k: rep.get(k) for k in ("results", "statsfight_results", "stats", "dob", "height", "reach")}
        verification["conflicts"] = rep.get("conflicts", [])[:20]
        verification["disputed_stats"] = len(rep.get("disputed_stats", []))
    outside = fightmatrix_metrics(FM_PATH, vdir, h.bios.keys()) if FM_PATH.exists() else None
    odds_path = Path(args.odds)
    upcoming_market = None
    if odds_path.exists():
        from .odds import upcoming_lines

        upcoming_market = upcoming_lines(odds_path, h.last_date())
    if study is not None and (vdir / "odds.json").exists():
        from .analysis import market_study

        study["market"] = market_study(calibrated, json.loads((vdir / "odds.json").read_text()))
    data = export(h, model, min_fights=args.min_fights, active_years=args.active_years, backtest=summary,
                  source=args.source or Path(args.data).name, upcoming=upcoming, aliases=aliases, rankings=rankings,
                  insights=study, checks=checks, verification=verification, outside=outside,
                  upcoming_market=upcoming_market)
    if args.log and data["upcoming"]["events"]:
        from . import predlog
        from .predictor import FightPredictor

        fp = FightPredictor(h, model)

        def _predict(a, b, rounds):
            pr = fp.predict(a, b, scheduled_rounds=rounds)
            f_, m_, mp = pr.most_likely_outcome
            return {"p_a": round(pr.prob_a, 4), "pick": pr.pick, "method": f"{f_} by {m_}", "method_p": round(mp, 4)}

        log = predlog.update(Path(args.log), h, data["upcoming"]["events"], _predict,
                             {"scale": model.scale, "trained_on": model.trained_on})
        data["prediction_log"] = {"scorecard": log["scorecard"], "entries": list(log["entries"].values())}
    if study is not None and study.get("market") and (vdir / "odds.json").exists():
        from .analysis import card_recaps

        live = json.loads(Path(args.log).read_text())["entries"] if args.log and Path(args.log).exists() else {}
        data["recaps"] = card_recaps(calibrated, json.loads((vdir / "odds.json").read_text()),
                                     study["market"]["blend"]["weights"], live)
    write(data, Path(args.out))
    print(f"Exported {data['meta']['fighters_exported']} fighters to {args.out}")
    return 0


def cmd_serve(args) -> int:
    import functools
    import http.server

    app_dir = Path(args.dir) if args.dir else Path(__file__).resolve().parent.parent / "app"

    class Handler(http.server.SimpleHTTPRequestHandler):
        # index.html is written without a document skeleton (the artifact
        # host adds one), so add it here for local viewing.
        def do_GET(self):
            if self.path.split("?")[0] in ("/", "/index.html"):
                body = (
                    '<!doctype html><html><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
                    "</head><body>" + (app_dir / "index.html").read_text(encoding="utf-8") + "</body></html>"
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

    handler = functools.partial(Handler, directory=str(app_dir))
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as srv:
        print(f"MMA Fight Lab at http://127.0.0.1:{args.port}  (Ctrl+C to stop)")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="mma-predict", description="Evaluate MMA matchups and predict outcomes.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def data_arg(p):
        p.add_argument("--data", default=str(DEFAULT_DATA), help="directory with fighters.csv and fights.csv")
        p.add_argument("--scouting", default=str(DEFAULT_SCOUTING),
                       help="directory with backgrounds.json and fight_notes.json ('' to ignore)")
        p.add_argument("--no-external", action="store_true", help="ignore Fight Matrix ratings (data/fightmatrix)")

    def model_args(p):
        p.add_argument("--model", help="trained model JSON (default: built-in prior weights)")
        p.add_argument("--fit", action="store_true", help="fit a model on the dataset before predicting")
        p.add_argument("--adjustments", help="JSON of your manual adjustments (exported from the web interface)")

    p = sub.add_parser("predict", help="predict a single matchup")
    data_arg(p)
    model_args(p)
    p.add_argument("fighter_a")
    p.add_argument("fighter_b")
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--title", action="store_true")
    p.add_argument("--odds", nargs=2, type=float, metavar=("A_ODDS", "B_ODDS"), help="American moneylines")
    p.set_defaults(func=cmd_predict)

    p = sub.add_parser("card", help="predict every bout in a card CSV")
    data_arg(p)
    model_args(p)
    p.add_argument("--card", required=True)
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=cmd_card)

    p = sub.add_parser("profile", help="scouting profile for one fighter")
    data_arg(p)
    p.add_argument("fighter")
    p.set_defaults(func=cmd_profile)

    p = sub.add_parser("rankings", help="Elo leaderboard")
    data_arg(p)
    p.add_argument("--top", type=int, default=25)
    p.add_argument("--min-fights", type=int, default=3)
    p.add_argument("--by", choices=["overall", "raw", "striking", "wrestling", "grappling"], default="overall",
                   help="overall = proven rating (overall minus uncertainty); raw = overall without the uncertainty penalty")
    p.add_argument("--active-years", type=float, default=2.0, help="only fighters who fought within this many years (0 = everyone)")
    p.add_argument("--class", dest="weight_class", help="only this weight class, e.g. Lightweight (listed classes only)")
    p.set_defaults(func=cmd_rankings)

    p = sub.add_parser("train", help="fit model weights on the dataset")
    data_arg(p)
    p.add_argument("--out", default="models/model.json")
    p.add_argument("--l2", type=float, default=25.0)
    p.add_argument("--iterations", type=int, default=600)
    p.add_argument("--min-fights", type=int, default=1)
    p.set_defaults(func=cmd_train)

    p = sub.add_parser("backtest", help="walk-forward evaluation")
    data_arg(p)
    p.add_argument("--train-fraction", type=float, default=0.4)
    p.add_argument("--retrain-every", type=int, default=100)
    p.add_argument("--min-fights", type=int, default=1)
    p.add_argument("--events", default="", help="only score bouts whose event name starts with this (e.g. UFC)")
    p.add_argument("--split-sports", action="store_true", help="treat men's and women's MMA as separate sports (own ratings, base rates and model)")
    p.set_defaults(func=cmd_backtest)

    p = sub.add_parser("import", help="crawl fighter records from Sherdog, Tapology or UFCStats")
    p.add_argument("source", choices=["sherdog", "tapology", "ufcstats", "kaggle"])
    p.add_argument("--dir", help="kaggle: the unzipped UFC Datasets 1994-2025 folder")
    p.add_argument("seeds", nargs="*", help="fighter URLs or slugs (e.g. Israel-Adesanya-56374 / israel-adesanya)")
    p.add_argument("--ufc-events", type=int, default=0, help="sherdog: also seed with every fighter on the N most recent UFC events; ufcstats: import the N most recent events (default all)")
    p.add_argument("--out", required=True)
    p.add_argument("--depth", type=int, default=1, help="how many opponent hops to follow")
    p.add_argument("--max-fighters", type=int, default=2000)
    p.add_argument("--delay", type=float, default=3.0, help="seconds between requests")
    p.add_argument("--cache", default=".cache/pages")
    p.set_defaults(func=cmd_import)

    p = sub.add_parser("export", help="build app/data.json for the web interface")
    data_arg(p)
    p.add_argument("--model", help="trained model JSON (default: train on the dataset)")
    p.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "app" / "data.json"))
    p.add_argument("--min-fights", type=int, default=2)
    p.add_argument("--active-years", type=float, default=4.0)
    p.add_argument("--events", default="", help="backtest scope, e.g. UFC")
    p.add_argument("--source", default="")
    p.add_argument("--no-backtest", action="store_true")
    p.add_argument("--upcoming", default="data/upcoming.json", help="scheduled cards from the upcoming command")
    p.add_argument("--rankings", default="data/ranked_fighters.json", help="official UFC rankings, for comparison")
    p.add_argument("--aliases", default="data/name_aliases.json")
    p.add_argument("--log", default="data/predictions/log.json", help="prediction log to update ('' to skip)")
    p.add_argument("--odds", default="data/bestfightodds/fighters.jsonl", help="BestFightOdds lines (upcoming cards)")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("serve", help="open the web interface locally")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--dir", help="directory holding index.html, engine.js and data.json (default: app/)")
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("analyze", help="regression of past results and model accuracy by matchup pattern")
    data_arg(p)
    p.add_argument("--events", default="UFC")
    p.add_argument("--no-calibrate", dest="calibrate", action="store_false", help="judge patterns against raw predictions")
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("compare", help="compare our division order with the official UFC rankings")
    data_arg(p)
    p.add_argument("--rankings", default="data/ranked_fighters.json")
    p.add_argument("--aliases", default="data/name_aliases.json")
    p.add_argument("--system", choices=["meta", "media"], default="media")
    p.add_argument("--by", default="proven", choices=["proven", "elo"])
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("upcoming", help="fetch scheduled UFC fight cards from Wikipedia")
    p.add_argument("--out", default="data/upcoming.json")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--cache", default=".cache/pages")
    p.add_argument("--refresh", action="store_true", help="re-download the schedule instead of using the cache")
    p.set_defaults(func=cmd_upcoming)

    p = sub.add_parser("rebuild", help="rebuild a Sherdog dataset from all cached fighter pages")
    p.add_argument("--data", required=True)
    p.add_argument("--cache", default=".cache/pages")
    p.set_defaults(func=cmd_rebuild)

    p = sub.add_parser("enrich", help="add current UFC division and gender from Wikipedia's UFC roster")
    p.add_argument("--data", required=True)
    p.add_argument("--roster-html", help="use a saved copy of the roster page instead of fetching it")
    p.add_argument("--cache", default=".cache/pages")
    p.set_defaults(func=cmd_enrich)

    p = sub.add_parser("verify", help="Sherdog + UFCStats stats, keeping only what a second source confirms")
    p.add_argument("--data", default="data/sherdog", help="career dataset (the base)")
    p.add_argument("--stats", default="data/ufcstats", help="UFCStats dataset (import kaggle)")
    p.add_argument("--statsfight", default="data/statsfight/bouts.jsonl")
    p.add_argument("--out", default="data/verified")
    p.add_argument("--fightmatrix", default="data/fightmatrix/profiles.jsonl", help="third source for birth dates")
    p.add_argument("--odds", default="data/bestfightodds/fighters.jsonl", help="betting lines (BestFightOdds)")
    p.add_argument("--strict-stats", action="store_true", help="attach only stats StatsFight confirms")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("merge", help="merge datasets (e.g. career records + UFC stats)")
    p.add_argument("dirs", nargs="+")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_merge)

    from .picks_cli import register as register_picks
    register_picks(sub, data_arg)
    from .scout_cli import register as register_scout
    register_scout(sub)
    from .prospects import register as register_prospects
    register_prospects(sub)
    from .refresh import register as register_refresh
    register_refresh(sub)
    from .prospect_week import register as register_week
    register_week(sub)
    from .health import register as register_health
    register_health(sub)
    from .recap_cli import register as register_recap
    register_recap(sub)
    from .tapology_import import register as register_tapology_import
    register_tapology_import(sub)
    from .suggestions import register as register_suggestions
    register_suggestions(sub)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (KeyError, ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
