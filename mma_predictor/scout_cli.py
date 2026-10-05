"""`python -m mma_predictor scout ...`: news, analysis and scouting reports.

    scout news      pull the outlets' feeds and tag articles with the fighters they're about
    scout search    search outlet archives for everything on some fighters (or a card)
    scout card      the next card's fighters and the state of their reports
    scout brief     a reading packet on one fighter: numbers, recent fights, background, coverage
    scout sync      write the page-database documents (scouting collection)

Reports live in data/scouting/reports/<slug>.json and are written by hand
(by Claude) from the reading; see SCOUTING.md.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

from . import news as N

NEWS = Path("data/scouting/news.jsonl")
REPORTS = Path("data/scouting/reports")
UA = "Mozilla/5.0 (compatible; mma-predictor/0.1; personal research)"


def slug(name: str) -> str:
    return N.fold(name).strip().replace(" ", "-")


def _fetcher(cache: str):
    from .sources.common import Fetcher

    return Fetcher(Path(cache), delay=1.5, user_agent=UA)


def _fresh(fetcher, url: str) -> str:
    fetcher._cache_path(url).unlink(missing_ok=True)
    return fetcher.get(url, cache=False)


def _roster(app_data: str, aliases: str) -> N.Roster:
    d = json.loads(Path(app_data).read_text())
    al = json.loads(Path(aliases).read_text()) if Path(aliases).exists() else {}
    names = [f["name"] for f in d["fighters"]]
    for f in d["fighters"]:
        for a in f.get("aka") or []:
            al.setdefault(a, f["name"])
    return N.Roster(names, al)


def _index(args) -> N.NewsIndex:
    return N.NewsIndex(Path(args.news), Path(args.cache) / "news")


def _article_text(fetcher, url: str) -> str:
    page = fetcher.get(url, cache=False)
    body = re.search(r"<article\b.*?</article>", page, re.S) or re.search(r"<main\b.*?</main>", page, re.S)
    paras = re.findall(r"<p\b[^>]*>(.*?)</p>", body.group(0) if body else page, re.S)
    return "\n".join(t for t in (N.text_of(p) for p in paras) if len(t) > 40)


def cmd_news(args) -> int:
    fetcher, idx, roster = _fetcher(args.cache), _index(args), _roster(args.app_data, args.aliases)
    new = tagged = 0
    for outlet, url in N.FEEDS.items():
        try:
            items = N.parse_feed(_fresh(fetcher, url), outlet)
        except OSError as exc:
            print(f"  {outlet}: {exc}")
            continue
        for it in items:
            who = roster.find(it["title"] + " " + it["teaser"])
            if who:
                tagged += 1
                new += idx.add(it, who)
        print(f"  {outlet}: {len(items)} items")
    idx.save()
    print(f"{new} new articles about roster fighters ({tagged} tagged this pull); index has {len(idx.items)}")
    return 0


def _card(fetcher, event: str = "") -> Dict[str, object]:
    from .sources import events

    sched = [e for e in events.scheduled_events(_fresh(fetcher, events.EVENTS_URL)) if e["date"] >= date.today().isoformat()]
    if event:
        sched = [e for e in sched if event.lower() in e["name"].lower()]
    ev = sched[0]
    ev["bouts"] = events.parse_card(_fresh(fetcher, ev["url"])) if ev["url"] else []
    return ev


def _card_names(ev, roster: N.Roster) -> List[str]:
    out = []
    for b in ev["bouts"]:
        for n in (b["a"], b["b"]):
            hit = roster.find(n)
            out.append(hit[0] if hit else n)
    return out


def cmd_search(args) -> int:
    fetcher, idx, roster = _fetcher(args.cache), _index(args), _roster(args.app_data, args.aliases)
    names = list(args.names)
    if args.card:
        names += _card_names(_card(fetcher, args.event), roster)
    for name in names:
        found = 0
        for outlet, base in N.SEARCHABLE.items():
            try:
                rows = N.parse_wp(fetcher.get(N.wp_search_url(base, name, args.per_outlet), cache=False), outlet)
            except OSError as exc:
                print(f"  {name} @ {outlet}: {exc}")
                continue
            for r in rows:
                who = roster.find(r["title"] + " " + r["text"])
                if name in who or N.fold(name) in N.fold(r["title"] + " " + r["text"]):
                    idx.add(r, sorted(set(who) | {name}), r["text"])
                    found += 1
        print(f"  {name}: {found} articles")
    idx.save()
    return 0


def _report(name: str) -> Dict[str, object]:
    p = REPORTS / f"{slug(name)}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def cmd_card(args) -> int:
    fetcher, roster = _fetcher(args.cache), _roster(args.app_data, args.aliases)
    ev = _card(fetcher, args.event)
    from .reads import Pundits, pundit_consensus
    pun = Pundits()
    board = pun.scoreboard()
    print(f"{ev['name']} ({ev['date']})")
    for b in ev["bouts"]:
        row = []
        for n in (b["a"], b["b"]):
            hit = roster.find(n)
            name = hit[0] if hit else n
            r = _report(name)
            row.append(f"{name} [{('report ' + r['updated'][:10]) if r else 'NO REPORT'}]")
        print("  " + "  vs  ".join(row))
        mine = [p for p in pun.rows if not p.get("grade") and {p["a"], p["b"]} == {b["a"], b["b"]}]
        cs = pundit_consensus(mine, board)
        if cs:
            print(f"      pundits: {cs['pick']} {cs['share']:.0%} weighted by track record ({cs['raw_share']:.0%} by headcount, {cs['n']} picks)")
    return 0


def cmd_brief(args) -> int:
    """Everything worth reading before writing (or refreshing) one fighter's report."""
    d = json.loads(Path(args.app_data).read_text())
    f = next((x for x in d["fighters"] if x["name"].lower() == args.name.lower()), None)
    idx = _index(args)
    fetcher = _fetcher(args.cache)
    if f:
        rec = f"{f['wins'] + f.get('prior_wins', 0)}-{f['losses'] + f.get('prior_losses', 0)}"
        print(f"# {f['name']} ({f.get('division') or f.get('weight_class')}, {rec}, age {f.get('age') and round(f['age'])}, {f.get('stance') or '?'} stance, "
              f"{f.get('height_cm') or '?'} cm, reach {f.get('reach_cm') or '?'} cm, team {f.get('team') or '?'})")
        keys = ("slpm", "sapm", "str_acc", "str_def", "td_per15", "td_acc", "td_def", "sub_per15", "ctrl_share", "kd_per15", "finish_rate", "late_win_rate")
        print("Numbers: " + ", ".join(f"{k} {f[k]:.2f}" for k in keys if isinstance(f.get(k), (int, float))))
        print(f"Wins by {f.get('win_methods')}; losses by {f.get('loss_methods')}")
        print("Recent:")
        for r in (f.get("recent") or [])[:8]:
            print(f"  {r.get('date')} {r.get('result')} vs {r.get('opponent')} ({r.get('method')} R{r.get('round', '')}) {r.get('event', '')}")
        bg = f.get("background")
        if bg:
            print(f"Background: {bg.get('summary', '')}")
    cur = _report(args.name)
    if cur:
        print(f"\nCurrent report ({cur.get('updated', '')[:10]}): {cur.get('summary', '')}")
    items = idx.about(f["name"] if f else args.name)[: args.articles]
    print(f"\n{len(idx.about(f['name'] if f else args.name))} articles indexed; the latest {len(items)}:")
    for it in items:
        text = idx.text(str(it["url"]))
        if text is None and args.fetch:
            try:
                text = _article_text(fetcher, str(it["url"]))
                if text:
                    (idx.cache / idx.key(str(it["url"]))).parent.mkdir(parents=True, exist_ok=True)
                    (idx.cache / idx.key(str(it["url"]))).write_text(text)
            except OSError:
                text = None
        print(f"\n## {it['date']} · {it['outlet']} · {it['title']}\n{it['url']}")
        for s in N.mentions(text or "", f["name"] if f else args.name, limit=args.lines):
            print(f"  > {s[:500]}")
    return 0


def cmd_grade(args) -> int:
    """Grade reads and pundit picks for finished cards (results Wikipedia and Sherdog agree on)."""
    from .picks_cli import _fetcher as picks_fetcher, _results_for
    from .reads import READS_DIR, Pundits, Reads, grade_reads

    fetcher = picks_fetcher(args.cache)
    pun = Pundits()
    today = date.today().isoformat()
    graded_rows = []
    for path in sorted(READS_DIR.glob("*.json")):
        doc = json.loads(path.read_text())
        rows = doc["bouts"]
        if doc["date"] >= today and not args.force:
            graded_rows += [r for r in rows if r.get("y") in (0, 1)]
            continue
        todo = [r for r in rows if "y" not in r]
        if todo:
            week = {"results_url": doc.get("results_url", ""), "event_date": doc["date"],
                    "bets": [{"legs": [{"bout": f"{r['a']} vs {r['b']}"}]} for r in todo]}
            results = _results_for(fetcher, week)
            reads = Reads(rows)
            for r in todo:
                key = f"{r['a']} vs {r['b']}"
                if key not in results:
                    continue
                res = results[key]
                if res is None or res.winner is None:
                    r["y"] = None  # no contest, draw or cancelled: not graded
                    r["outcome"] = "void" if res is None else res.method
                    continue
                r["y"] = 1 if res.winner == "a" else 0
                r["signed_logit"] = reads.logit(r["a"], r["b"])
                r["winner"] = r["a"] if r["y"] else r["b"]
                r["result"] = {"method": res.method, "round": res.round, "seconds": res.seconds}
                for pr in pun.rows:
                    if pr["event"] == doc["event"] and {pr["a"], pr["b"]} == {r["a"], r["b"]} and pr.get("grade") is None:
                        pr["winner"] = r["winner"]
                        pr["grade"] = "won" if pr["pick"] == r["winner"] else "lost"
            path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
        graded_rows += [r for r in rows if r.get("y") in (0, 1)]
    pun.save()
    print("Reads:", json.dumps(grade_reads(graded_rows)))
    for s in pun.scoreboard():
        print(f"  {s['outlet']:<14} {s['author']:<22} {s['correct']}/{s['picks']} ({s['accuracy']:.0%}; market expected {s['expected'] or 0:.0%}) z {s['z']:+.2f} weight {s['weight']}")
    return 0


def cmd_sync(args) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    writes = []
    from .reads import READS_DIR, Pundits, grade_reads, pair_id

    # Reads (one document per bout) and the pundit scoreboard.
    graded = []
    for path in sorted(READS_DIR.glob("*.json")):
        ev = json.loads(path.read_text())
        for r in ev["bouts"]:
            doc_id = pair_id(r["a"], r["b"])
            (out / f"{doc_id}.json").write_text(json.dumps(dict(r, kind="read"), ensure_ascii=False))
            writes.append({"op": "set", "collection": "scouting", "doc_id": doc_id, "file_path": str((out / f"{doc_id}.json").resolve())})
            if r.get("y") in (0, 1):
                graded.append(r)
    board = {"kind": "scoreboard", "reads": grade_reads(graded), "pundits": Pundits().scoreboard(),
             "updated": N.now()}
    (out / "scoreboard.json").write_text(json.dumps(board, ensure_ascii=False))
    writes.append({"op": "set", "collection": "scouting", "doc_id": "scoreboard", "file_path": str((out / "scoreboard.json").resolve())})
    for p in sorted(REPORTS.glob("*.json")):
        doc = json.loads(p.read_text())
        if args.since and str(doc.get("updated", "")) < args.since:
            continue
        (out / p.name).write_text(json.dumps(dict(doc, kind="report"), ensure_ascii=False))
        writes.append({"op": "set", "collection": "scouting", "doc_id": p.stem, "file_path": str((out / p.name).resolve())})
    print(json.dumps(writes, indent=1))
    print(f"{len(writes)} documents", flush=True)
    return 0


def register(sub) -> None:
    p = sub.add_parser("scout", help="MMA news, analysis and scouting reports (see SCOUTING.md)")
    ps = p.add_subparsers(dest="scout_cmd", required=True)

    def common(q):
        q.add_argument("--news", default=str(NEWS))
        q.add_argument("--cache", default=".cache/pages")
        q.add_argument("--app-data", default="app/data.json")
        q.add_argument("--aliases", default="data/name_aliases.json")

    q = ps.add_parser("news", help="pull outlet feeds and tag articles with fighters")
    common(q)
    q.set_defaults(func=cmd_news)

    q = ps.add_parser("search", help="search outlet archives for fighters")
    common(q)
    q.add_argument("names", nargs="*")
    q.add_argument("--card", action="store_true", help="everyone on the next card")
    q.add_argument("--event", default="")
    q.add_argument("--per-outlet", type=int, default=20)
    q.set_defaults(func=cmd_search)

    q = ps.add_parser("card", help="next card and report status")
    common(q)
    q.add_argument("--event", default="")
    q.set_defaults(func=cmd_card)

    q = ps.add_parser("brief", help="reading packet on one fighter")
    common(q)
    q.add_argument("name")
    q.add_argument("--articles", type=int, default=15)
    q.add_argument("--lines", type=int, default=6)
    q.add_argument("--fetch", action="store_true", help="download articles not yet cached")
    q.set_defaults(func=cmd_brief)

    q = ps.add_parser("grade", help="grade reads and pundit picks for finished cards")
    q.add_argument("--cache", default=".cache/pages")
    q.add_argument("--force", action="store_true")
    q.set_defaults(func=cmd_grade)

    from .pundit_history import cmd_history
    q = ps.add_parser("history", help="collect published fight picks from outlets' archives into the pundit ledger, graded")
    q.add_argument("--sources", default="sherdog,cageside,mmasucka,bleacher,rotowire,oddsbreaker,mmaintel,cbs,staff")
    q.add_argument("--since", default="2024-01-01")
    q.add_argument("--limit", type=int, default=0, help="articles per source (testing)")
    q.add_argument("--cache", default=".cache/pages")
    q.add_argument("--verbose", action="store_true")
    q.set_defaults(func=cmd_history)

    q = ps.add_parser("sync", help="write scouting documents for the page database")
    q.add_argument("--out", default=".cache/scouting_sync")
    q.add_argument("--since", default="", help="only reports updated on/after this date")
    q.set_defaults(func=cmd_sync)
