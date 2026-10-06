"""Dana White's Contender Series: predictions for the weeks left in the season, and Claude's picks.

    python -m mma_predictor dwcs build                 # remaining weeks -> drafts + app/dwcs.json
    python -m mma_predictor dwcs build --week 8        # one week (a past one replays, for testing)
    python -m mma_predictor card-picks lock --dir data/card_picks/dwcs --draft data/dwcs/drafts/<date>.json --picks FILE
    python -m mma_predictor card-picks grade --dir data/card_picks/dwcs
    python -m mma_predictor dwcs export                # app/dwcs.json again, with picks and results

Two sources for every bout: the season's Wikipedia page and Sherdog's event page for that week. Most
Contender Series fighters have never fought in the UFC, so they aren't in the site's data: each fighter's
full Sherdog record is fetched and added to a scratch copy of the verified dataset, and the model prices
the bout from there. Their records are mostly regional, so many opponents' own records are unknown and
the numbers are rougher than for a UFC card (each bout says how much of the record the model could see).
BestFightOdds lines are attached when they're posted (usually a day or two before). Claude's picks are
kept in their own record (data/card_picks/dwcs) so they don't feed the UFC record's lessons.
"""

from __future__ import annotations

import csv
import json
import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from . import picks as P
from .card_picks import METHODS, add_model_round, finish_rounds, joint_methods, load_adjust, load_round_table
from .picks_cli import BFO_HOME, CALIBRATION, _fetcher, _fresh, _lock_time, _model, _pair, sigmoid_logit

ROOT = Path(__file__).resolve().parent.parent
SEASON_URL = "https://en.wikipedia.org/wiki/Dana_White%27s_Contender_Series_season_10"
RAW = "https://en.wikipedia.org/w/index.php?title=Dana_White%27s_Contender_Series_season_10&action=raw"
DRAFTS = Path("data/dwcs/drafts")
PICKS_DIR = Path("data/card_picks/dwcs")
OUT = Path("app/dwcs.json")
SCRATCH = Path(".cache/dwcs/data")
UA = "Mozilla/5.0 (compatible; mma-predictor/0.1; personal research)"
MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                       "September", "October", "November", "December"], 1)}


def _clean(s: str) -> str:
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)  # [[link|text]] -> text
    s = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    return re.sub(r"\s+", " ", s).strip()


def parse_season(raw: str, year: int = 2026) -> List[Dict]:
    """Weeks of the season page (wikitext): number, date, Sherdog event link, bouts (weight class, a, b)."""
    weeks = []
    parts = re.split(r"^==\s*Week (\d+)\s*[–-]\s*([A-Z][a-z]+ \d+)\s*==\s*$", raw, flags=re.M)
    for i in range(1, len(parts) - 2, 3):
        n, day, body = int(parts[i]), parts[i + 1], parts[i + 2]
        m = re.match(r"([A-Z][a-z]+) (\d+)", day)
        when = date(year, MONTHS[m.group(1)], int(m.group(2)))
        name = re.search(r"\|name=([^\n|]+)", body)
        sd = re.search(r"https://www\.sherdog\.com/events/[^\s|}]+", body)
        bouts = []
        for t in re.findall(r"\{\{MMAevent bout\s*\n(.*?)\}\}", body, flags=re.S):
            cells = [_clean(c) for c in t.split("\n|")]
            cells[0] = cells[0].lstrip("|")
            if len(cells) >= 4 and re.match(r"(vs|def|draw|nc)", cells[2].lower()):  # "def." once the bout is over
                wc, a, b = cells[0], cells[1], cells[3]
                result = [c for c in cells[4:] if c]
                if b and a and "TBA" not in (a, b):
                    bouts.append({"weight_class": wc, "a": a, "b": b, "decided": bool(result)})
        weeks.append({"week": n, "date": when.isoformat(), "name": _clean(name.group(1)) if name else f"Contender Series Week {n}",
                      "sherdog_url": sd.group(0) if sd else "", "bouts": bouts})
    return weeks


def _same(x: str, y: str) -> bool:
    """Same fighter across sources: any shared name token, accent-insensitive ('Greg Foster'/'Gregory Foster',
    'Douglas da Lapa'/'Douglas Lapa'). Used only within one bout's two names, where a shared first name can't mislead."""
    from .sources.wikipedia import match_key

    stop = {"da", "de", "dos", "do", "jr", "junior"}
    return bool((set(match_key(x).split()) - stop) & (set(match_key(y).split()) - stop))


def build_week(week: Dict, f, history, model, dec_cal, adjust, prospects: Dict[str, dict], bfo: Dict, log=print) -> Dict:
    from .features import BoutContext
    from .methods import method_distribution
    from .predictor import FightPredictor
    from .prospect_week import event_bouts

    _, sd_bouts = event_bouts(f.get(week["sherdog_url"], cache=False, fresh=True))
    pr = FightPredictor(history, model)
    when = date.fromisoformat(week["date"])
    names = history.names()
    rows = []
    for b in week["bouts"]:
        hit = next(((x, y) for x, y in sd_bouts if (_same(b["a"], _slug_name(x)) and _same(b["b"], _slug_name(y)))
                    or (_same(b["a"], _slug_name(y)) and _same(b["b"], _slug_name(x)))), None)
        row = {"bout": f"{b['a']} vs {b['b']}", "a": b["a"], "b": b["b"], "weight_class": b["weight_class"], "rounds": 3, "title": False,
               "segment": "Fight card", "sources": ["Wikipedia"] + (["Sherdog"] if hit else [])}
        if not hit:
            log(f"  {row['bout']}: not on Sherdog's event page; left out until both sources list it")
            continue
        ua, ub = (hit[0], hit[1]) if _same(b["a"], _slug_name(hit[0])) else (hit[1], hit[0])
        row["a_url"], row["b_url"] = ua, ub
        side = {}
        for k, url in (("a", ua), ("b", ub)):
            name = _url_name.get(url)
            side[k] = name if name in names else None
            p = prospects.get(url)
            if p:
                row[k + "_prospect"] = {"rank": p["p4p_rank"], "score": p["score"], "division_rank": p["div_rank"]}
        if side["a"] and side["b"]:
            sa, sb, x = pr.features(side["a"], side["b"], when, BoutContext(3, False))
            pa = sigmoid_logit(model, x)
            j = joint_methods(pa, method_distribution(sa, sb, 3), method_distribution(sb, sa, 3), dec_cal, adjust)
            s = "a" if pa >= 0.5 else "b"
            row["model"] = add_model_round({"p_a": round(pa, 4), "winner": b[s], "method": max(METHODS, key=lambda m: j[s][m]), "p_win": round(max(pa, 1 - pa), 4),
                                            "joint": {q: {m: round(v, 4) for m, v in j[q].items()} for q in j}}, 3, load_round_table(),
                                           finish_rounds(history.fights, side[s], side["b" if s == "a" else "a"], when, 3))
            row["records"] = {k: _record(history, side[k], when) for k in ("a", "b")}
        else:
            row["model"] = None
        apply_lines(row, _line(bfo, b["a"], b["b"]))
        rows.append(row)
    return {"event": week["name"], "week": week["week"], "date": week["date"], "results_url": SEASON_URL, "sherdog_url": week["sherdog_url"],
            "location": "Las Vegas, Nevada, U.S.", "locks_at": _lock_time(week["date"], True), "drafted_at": _now(),
            "dec_cal": dec_cal, "method_adjust": adjust, "round_table": load_round_table(), "bouts": rows}


_url_name: Dict[str, str] = {}


def _slug_name(url: str) -> str:
    return re.sub(r"-\d+$", "", url.rstrip("/").rsplit("/", 1)[-1]).replace("-", " ")


def _record(history, name: str, when: date) -> Dict[str, object]:
    """What the model could see: the fighter's pro record before the bout, and how many of those opponents it knows."""
    fs = [f for f in history.fights if f.date < when and name in (f.fighter_a, f.fighter_b)]
    w = sum(1 for f in fs if f.winner == name)
    l = sum(1 for f in fs if f.winner and f.winner != name and f.winner in (f.fighter_a, f.fighter_b))
    known = sum(1 for f in fs if len([g for g in history.fights if (f.fighter_b if f.fighter_a == name else f.fighter_a) in (g.fighter_a, g.fighter_b)]) > 1)
    return {"record": f"{w}-{l}", "bouts": len(fs), "opponents_known": known}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def scratch_dataset(f, urls: List[str], data: Path, log=print) -> Path:
    """data/verified plus the fighters' fresh Sherdog records, in a scratch folder (nothing real is changed)."""
    from .refresh import _read_csv, merge_rows
    from .sources import common, sherdog

    pages = []
    for u in urls:
        try:
            pages.append(sherdog.parse_fighter(f.get(u, cache=False, fresh=True), u))
        except Exception as exc:  # noqa: BLE001
            log(f"  {u}: {exc}")
    for p in pages:
        _url_name[p.url] = p.name
    new_f, new_b = common.pages_to_rows(pages, "sherdog")
    fighters, fights = _read_csv(data / "fighters.csv"), _read_csv(data / "fights.csv")
    merge_rows(fighters, fights, new_f, new_b)
    by_url = {r["url"]: r["name"] for r in fighters if r.get("url")}
    for p in pages:
        _url_name[p.url] = by_url.get(p.url, p.name)
    shutil.rmtree(SCRATCH, ignore_errors=True)
    SCRATCH.mkdir(parents=True)
    common.write_dataset(SCRATCH, fighters, fights)
    log(f"  {len(pages)} Sherdog records added to a scratch copy of {data}")
    return SCRATCH


def bfo_lines(f) -> Dict:
    """Every bout on BestFightOdds' current events, by fighter pair: (first-listed fighter, moneylines)."""
    out = {}
    try:
        for _, url in P.event_links(_fresh(f, BFO_HOME)):
            for b in P.parse_event(_fresh(f, url), url)["bouts"]:
                out.setdefault(_pair(b["a"], b["b"]), (b["a"], b["ml"]))
    except OSError:
        pass
    return out


def _line(bfo: Dict, a: str, b: str):
    """BestFightOdds' line for a bout, by exact pair, else by a pair whose names each share a token with ours
    ('Mateus Soares' for 'Matheus Soares' still needs the other fighter to match too)."""
    ml = bfo.get(_pair(a, b))
    if ml:
        return ml
    hits = [v for key, v in bfo.items() if len(key) == 2
            and any(_same(a, x) and _same(b, y) for x, y in (tuple(key), tuple(key)[::-1]))]
    return hits[0] if len(hits) == 1 else None


def apply_lines(row: Dict, ml) -> bool:
    """Set a bout's moneylines and no-vig market chance for A; True when they changed."""
    if not ml or ml[1].get("a") is None or ml[1].get("b") is None:
        return False
    first_is_a = _same(ml[0], row["a"]) and not _same(ml[0], row["b"])
    pa_m = P.implied(ml[1]["a"]) / (P.implied(ml[1]["a"]) + P.implied(ml[1]["b"]))
    new = {"market_p_a": round(pa_m if first_is_a else 1 - pa_m, 4),
           "odds": ml[1] if first_is_a else {"a": ml[1]["b"], "b": ml[1]["a"]}}
    if all(row.get(k) == v for k, v in new.items()):
        return False
    row.update(new)
    return True


def refresh_odds(f, bfo: Optional[Dict] = None, log=print) -> int:
    """Re-price every upcoming draft from BestFightOdds without rebuilding the model numbers. Returns bouts changed."""
    bfo = bfo_lines(f) if bfo is None else bfo
    today, changed = date.today().isoformat(), 0
    for p in sorted(DRAFTS.glob("20*.json")) if DRAFTS.exists() else []:
        d = json.loads(p.read_text())
        if d["date"] < today:
            continue
        n = 0
        for r in d["bouts"]:
            if apply_lines(r, _line(bfo, r["a"], r["b"])):
                n += 1
                log(f"  {d['event']}: {r['bout']} {r['odds']['a']:+d} / {r['odds']['b']:+d} (market {r['market_p_a']:.0%} on {r['a']})")
        priced = sum(1 for r in d["bouts"] if r.get("odds"))
        log(f"Week {d['week']} ({d['date']}): {priced}/{len(d['bouts'])} bouts priced, {n} changed")
        if n:
            d["odds_at"] = _now()
            p.write_text(json.dumps(d, indent=1, ensure_ascii=False))
        changed += n
    return changed


def cmd_odds(args) -> int:
    log = print
    bfo = bfo_lines(_fetcher(args.cache))
    log(f"BestFightOdds: {len(bfo)} bouts on current events")
    if not bfo:
        log("BestFightOdds unreachable or empty; drafts left as they were")
        return 1
    refresh_odds(None, bfo)
    export()
    return 0


def cmd_build(args) -> int:
    from types import SimpleNamespace

    from .cli import DEFAULT_SCOUTING, _history
    from .prospect_week import event_bouts

    f = _fetcher(args.cache)
    import urllib.request

    req = urllib.request.Request(RAW, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
    weeks = parse_season(raw)
    today = date.today().isoformat()
    todo = [w for w in weeks if (w["week"] == args.week if args.week else w["date"] >= today)]
    if not todo:
        print("No Contender Series weeks left this season.")
        export()
        return 0
    urls = []
    for w in todo:
        if not w["sherdog_url"]:
            print(f"Week {w['week']}: no Sherdog event page yet")
            continue
        urls += [u for pair in event_bouts(f.get(w["sherdog_url"], cache=False, fresh=True))[1] for u in pair]
    data = scratch_dataset(f, list(dict.fromkeys(urls)), Path(args.data))
    history = _history(SimpleNamespace(data=str(data), scouting=str(DEFAULT_SCOUTING), no_external=False))
    model, _ = _model(Path(args.app_data))
    dec_cal = tuple(json.loads(CALIBRATION.read_text())["dec_cal"]) if CALIBRATION.exists() else None
    pros = json.loads(Path("app/prospects.json").read_text()) if Path("app/prospects.json").exists() else {"prospects": []}
    prospects = {p["sherdog_url"]: p for p in pros["prospects"] if p.get("sherdog_url")}
    bfo = bfo_lines(f)
    DRAFTS.mkdir(parents=True, exist_ok=True)
    for w in todo:
        if not w["sherdog_url"]:
            continue
        d = build_week(w, f, history, model, dec_cal, load_adjust(), prospects, bfo)
        path = DRAFTS / f"{w['date']}-week-{w['week']}.json"
        path.write_text(json.dumps(d, indent=1, ensure_ascii=False))
        print(f"Week {w['week']} ({w['date']}): {len(d['bouts'])} bouts -> {path}")
        for r in d["bouts"]:
            m = r["model"]
            rec = r.get("records", {})
            print(f"  {r['bout']:<44} " + (f"model {m['winner']} by {m['method']}{'' if m['method'] == 'DEC' else ' R' + str(m['round'])} {m['p_win']:.0%}" if m else "no model pick")
                  + (f" · market {r['market_p_a']:.0%} on {r['a']}" if "market_p_a" in r else "")
                  + (f" · records {rec['a']['record']} / {rec['b']['record']}" if rec else "")
                  + "".join(f" · {r[k]} prospect #{r[k + '_prospect']['rank']}" for k in ("a", "b") if r.get(k + "_prospect")))
    export()
    return 0


def export() -> Dict:
    """app/dwcs.json: each remaining (or recent) week's bouts, the model's numbers, Claude's picks and results."""
    weeks = []
    locked = {}
    for p in sorted(PICKS_DIR.glob("20*.json")) if PICKS_DIR.exists() else []:
        rec = json.loads(p.read_text())
        locked[rec["date"]] = rec
    for p in sorted(DRAFTS.glob("20*.json")) if DRAFTS.exists() else []:
        d = json.loads(p.read_text())
        rec = locked.get(d["date"])
        if rec:  # picks, and results once graded, for each bout
            by = {_pair(b["a"], b["b"]): b for b in rec["bouts"]}
            for b in d["bouts"]:
                r = by.get(_pair(b["a"], b["b"]))
                if r:
                    b.update({k: r[k] for k in ("pick", "result", "claude", "model_score") if k in r})
            d["locked_at"], d["note"] = rec.get("locked_at"), rec.get("note", "")
        weeks.append(d)
    summary = json.loads((PICKS_DIR / "summary.json").read_text()) if (PICKS_DIR / "summary.json").exists() else None
    out = {"fetched": _now(), "season": "Season 10", "source": SEASON_URL, "weeks": weeks, "record": summary}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(f"{OUT}: {len(weeks)} weeks")
    return out


def register(sub, data_arg) -> None:
    p = sub.add_parser("dwcs", help="Dana White's Contender Series: predictions for the season's remaining weeks (see AI_PICKS.md)")
    ps = p.add_subparsers(dest="dwcs_cmd", required=True)
    q = ps.add_parser("build", help="fetch the remaining weeks, price every bout, write drafts and app/dwcs.json")
    data_arg(q)
    q.add_argument("--week", type=int, default=0, help="one week (a past one replays, for testing)")
    q.add_argument("--cache", default=".cache/pages")
    q.add_argument("--app-data", default="app/data.json")
    q.set_defaults(func=cmd_build)
    q = ps.add_parser("odds", help="re-price the upcoming weeks from BestFightOdds (no model rebuild) and rewrite app/dwcs.json")
    q.add_argument("--cache", default=".cache/pages")
    q.set_defaults(func=cmd_odds)
    q = ps.add_parser("export", help="rewrite app/dwcs.json from the drafts, picks and results")
    q.set_defaults(func=lambda a: (export(), 0)[1])
