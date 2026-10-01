"""Crawler health: is every source still answering, and do our parsers still understand it?

    python -m mma_predictor health        # exit 1 if any check fails

Sites change their layouts without warning, and a parser that no longer matches doesn't
crash: it quietly returns nothing, and a crawl "succeeds" with no data. Each check fetches
one known page fresh and asks the real parser for a plausible amount of data. Results go
to data/health.json, with the date each source last passed, so a failure says how long
it has been broken. The routines run this first and report any failure.
"""

from __future__ import annotations

import json
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "health.json"
UA = "Mozilla/5.0 (compatible; mma-predictor/0.1; personal research)"
SHERDOG_FIGHTER = "https://www.sherdog.com/fighter/Ciryl-Gane-293973"
FM_FIGHTER = "https://www.fightmatrix.com/fighter-profile/Ciryl%20Gane/193933/"


def _at_least(n: int, got: int, what: str) -> Tuple[bool, str]:
    return got >= n, f"{got} {what}" + ("" if got >= n else f" (expected at least {n})")


def checks() -> List[Tuple[str, str, Callable]]:
    """(source, what uses it, check(fetcher) -> (ok, detail))."""
    from . import news, picks
    from . import prospects as PR
    from .prospect_week import listing
    from .sources import bestfightodds, events, fightmatrix, sherdog, statsfight, wikipedia

    def get(f, url):
        return f.get(url, cache=False, fresh=True)

    def sherdog_fighter(f):
        p = sherdog.parse_fighter(get(f, SHERDOG_FIGHTER), SHERDOG_FIGHTER)
        return _at_least(10, len(p.bouts), "bouts on a known fighter page") if p.dob else (False, "no birth date parsed")

    def sherdog_events(f):
        return _at_least(20, len(listing(get(f, "https://www.sherdog.com/events/upcoming/1-page"))), "upcoming events listed")

    def sherdog_ufc(f):
        rows = listing(get(f, sherdog.UFC_ORG))
        recent = [d for d, _ in rows if date.today() - timedelta(days=45) <= d <= date.today()]
        return _at_least(1, len(recent), "UFC events in the last 45 days")

    def fm_ranks(f):
        return _at_least(20, len(PR.parse_rank_page(get(f, f"{PR.FM}/mma-ranks/lightweight/"), "Lightweight")), "ranked lightweights")

    def fm_profile(f):
        p = fightmatrix.parse_profile(get(f, FM_FIGHTER), FM_FIGHTER)
        if not p.stats.get("Birth Date"):
            return False, "no birth date parsed"
        return _at_least(10, len(p.bouts), "bouts with ratings")

    def bfo_events(f):
        links = picks.event_links(get(f, bestfightodds.BASE))
        ufc = [l for l in links if l[0].upper().startswith("UFC")]
        if not ufc:
            return False, f"no UFC event among {len(links)} on the front page"
        ev = picks.parse_event(get(f, ufc[0][1]), ufc[0][1])
        priced = sum(1 for b in ev["bouts"] if any(v is not None for v in b["ml"].values()))
        return priced >= 1, f"{len(links)} events; {ev['name']}: {len(ev['bouts'])} bouts, {priced} with FanDuel moneylines"

    def bfo_fighter(f):
        hits = bestfightodds.search_results(get(f, bestfightodds.search_url("Ciryl Gane")))
        if not hits:
            return False, "fighter search returned nothing"
        return _at_least(5, len(bestfightodds.parse_fighter(get(f, hits[0][1]), hits[0][1])), "bouts with lines")

    def wiki_events(f):
        return _at_least(1, len(events.scheduled_events(get(f, events.EVENTS_URL))), "scheduled UFC events")

    def wiki_roster(f):
        return _at_least(400, len(wikipedia.parse_roster(get(f, wikipedia.ROSTER_URL))), "fighters on the UFC roster")

    def wiki_rankings(f):
        return _at_least(50, len(wikipedia.parse_rankings(get(f, wikipedia.RANKINGS_URL))), "ranked fighters")

    def statsfight_sitemap(f):
        return _at_least(1000, len(statsfight.bout_urls(get(f, statsfight.SITEMAP))), "UFC bouts in the sitemap")

    def kaggle(f):
        from .sources import kaggle_ufc

        req = urllib.request.Request(kaggle_ufc.DOWNLOAD_URL, headers={"User-Agent": UA, "Range": "bytes=0-1023"})
        with urllib.request.urlopen(req, timeout=60) as r:
            head = r.read(4)
            return head[:2] == b"PK", f"HTTP {r.status}, " + ("zip archive" if head[:2] == b"PK" else f"not a zip ({head!r})")

    def feed(outlet, url):
        def run(f):
            items = news.parse_feed(get(f, url), outlet)
            fresh = [i for i in items if i.get("date", "") >= (date.today() - timedelta(days=14)).isoformat()]
            if not items:
                return False, "feed parsed to nothing"
            return (len(fresh) >= 1, f"{len(items)} items, {len(fresh)} from the last 14 days")
        return run

    def wp(outlet, base):
        def run(f):
            return _at_least(1, len(news.parse_wp(get(f, news.wp_search_url(base, "Pereira")), outlet)), "search results")
        return run

    out = [
        ("Sherdog fighter pages", "fight records, prospects, refresh", sherdog_fighter),
        ("Sherdog event listings", "prospect fights this week", sherdog_events),
        ("Sherdog UFC events", "weekly refresh", sherdog_ufc),
        ("Fight Matrix rankings", "prospects crawl", fm_ranks),
        ("Fight Matrix profiles", "ratings, prospects", fm_profile),
        ("BestFightOdds events", "betting sheet (FanDuel)", bfo_events),
        ("BestFightOdds fighters", "closing lines, signings", bfo_fighter),
        ("Wikipedia UFC events", "upcoming cards, results", wiki_events),
        ("Wikipedia UFC roster", "divisions and gender", wiki_roster),
        ("Wikipedia UFC rankings", "rankings comparison", wiki_rankings),
        ("StatsFight", "stat verification", statsfight_sitemap),
        ("Kaggle UFCStats dump", "per-fight stats", kaggle),
    ]
    out += [(f"News: {o}", "scouting", feed(o, u)) for o, u in news.FEEDS.items()]
    out += [(f"Search: {o}", "scouting", wp(o, b)) for o, b in news.SEARCHABLE.items()]
    return out


def run_checks(delay: float = 1.0, only: str = "", log=print) -> dict:
    from .sources.common import Fetcher

    f = Fetcher(ROOT / ".cache" / "pages", delay=delay, user_agent=UA)
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    last_ok = {s["source"]: s.get("last_ok") for s in prev.get("sources", [])}
    today = date.today().isoformat()
    results = []
    for name, used_by, check in checks():
        if only and only.lower() not in name.lower():
            continue
        t = time.monotonic()
        try:
            ok, detail = check(f)
        except Exception as exc:  # noqa: BLE001 - a failure is a result here
            ok, detail = False, f"{type(exc).__name__}: {str(exc)[:200]}"
        r = {"source": name, "used_by": used_by, "ok": bool(ok), "detail": detail, "seconds": round(time.monotonic() - t, 1),
             "last_ok": today if ok else last_ok.get(name)}
        results.append(r)
        log(f"  {'ok  ' if ok else 'FAIL'} {name:<28} {detail}" + ("" if ok else f"  (last passed {r['last_ok'] or 'never'})"))
    report = {"checked": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "ok": all(r["ok"] for r in results),
              "failed": [r["source"] for r in results if not r["ok"]], "sources": results}
    if not only:
        OUT.write_text(json.dumps(report, indent=1))
    return report


def cmd_health(args) -> int:
    rep = run_checks(args.delay, args.only)
    n = len(rep["sources"])
    print(f"{n - len(rep['failed'])}/{n} sources healthy" + (f"; FAILED: {', '.join(rep['failed'])}" if rep["failed"] else ""))
    return 0 if rep["ok"] else 1


def register(sub) -> None:
    p = sub.add_parser("health", help="check every data source still answers and still parses")
    p.add_argument("--only", default="", help="run only checks whose name contains this")
    p.add_argument("--delay", type=float, default=1.0)
    p.set_defaults(func=cmd_health)
