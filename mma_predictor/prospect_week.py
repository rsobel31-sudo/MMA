"""Prospect fights this week: listed prospects booked on any card in the next days, and how they did.

    python -m mma_predictor prospect-week            # find this week's bouts, grade last week's
    python -m mma_predictor prospect-week --days 9

Sherdog lists upcoming events from every promotion; each event page links both fighters
of every bout, so prospects are matched by their Sherdog profile, not by name. Once an
event date has passed, the prospect's own Sherdog page is re-read for the result.
The bouts and results are written into app/prospects.json ("week") and kept in
data/prospects/fights.jsonl.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from .prospects import is_major


ROOT = Path(__file__).resolve().parent.parent
SHERDOG = "https://www.sherdog.com"
UA = "Mozilla/5.0 (compatible; mma-predictor/0.1; personal research)"
FIGHTS = ROOT / "data" / "prospects" / "fights.jsonl"
PROSPECTS = ROOT / "app" / "prospects.json"
ROW = re.compile(r"<tr.*?</tr>", re.S)
FIGHTER = re.compile(r'href="(/fighter/[^"]+)"')


def listing(page: str) -> List[Tuple[date, str]]:
    """(date, event url) rows of a Sherdog events listing page."""
    from .sources.common import find_date

    out = []
    for tr in ROW.findall(page):
        m = re.search(r'href="(/events/[^"]+)"', tr)
        d = find_date(re.sub(r"<[^>]+>", " ", tr)) if m else None
        if m and d:
            out.append((d, SHERDOG + m.group(1)))
    return out


def event_bouts(page: str) -> Tuple[str, List[Tuple[str, str]]]:
    """(event name, [(fighter url, fighter url)]) from a Sherdog event page: the main event, then each card row."""
    name = re.search(r'<h1[^>]*>\s*<span itemprop="name">([^<]+)', page) or re.search(r"<title>([^<|]+)", page)
    bouts: List[Tuple[str, str]] = []
    i = page.find("fight_card")
    if i >= 0:
        main = list(dict.fromkeys(FIGHTER.findall(page[i:i + 6000])))[:2]
        if len(main) == 2:
            bouts.append((SHERDOG + main[0], SHERDOG + main[1]))
    for tr in ROW.findall(page):
        links = list(dict.fromkeys(FIGHTER.findall(tr)))
        if len(links) == 2 and (SHERDOG + links[0], SHERDOG + links[1]) not in bouts:
            bouts.append((SHERDOG + links[0], SHERDOG + links[1]))
    return (name.group(1).strip() if name else ""), bouts


def _slug_name(url: str) -> str:
    return re.sub(r"-\d+$", "", url.rstrip("/").rsplit("/", 1)[-1]).replace("-", " ")


def find_bouts(fetcher, prospects: Dict[str, dict], start: date, end: date, log=print) -> List[dict]:
    events: List[Tuple[date, str]] = []
    for n in range(1, 15):
        url = f"{SHERDOG}/events/upcoming/{n}-page"
        rows = listing(fetcher.get(url, cache=False, fresh=True))
        if not rows:
            break
        events += [r for r in rows if start <= r[0] <= end]
        if min(r[0] for r in rows) > end:
            break
    events = list(dict.fromkeys(events))
    log(f"  {len(events)} events between {start} and {end}")
    out = []
    for d, url in events:
        try:
            name, bouts = event_bouts(fetcher.get(url, cache=False, fresh=True))
        except Exception as exc:  # noqa: BLE001
            log(f"  skip {url}: {exc}")
            continue
        for a, b in bouts:
            for me, opp in ((a, b), (b, a)):
                p = prospects.get(me)
                if p:
                    out.append({"date": d.isoformat(), "event": name, "event_url": url, "prospect": p["name"], "prospect_url": me,
                                "p4p_rank": p.get("p4p_rank"), "div_rank": p.get("div_rank"), "division": p.get("division"),
                                "record": f"{p.get('wins', 0)}-{p.get('losses', 0)}" + (f"-{p['draws']}" if p.get("draws") else ""),
                                "opponent": _slug_name(opp), "opponent_url": opp,
                                "opponent_prospect": opp in prospects, "major_debut": is_major(name)})
    return out


def grade(fetcher, bouts: List[dict], today: date, log=print) -> int:
    """Fill in results for bouts whose date has passed, from the prospect's Sherdog page."""
    from .sources import sherdog

    done = 0
    pages: Dict[str, object] = {}
    for b in bouts:
        if b.get("result") or date.fromisoformat(b["date"]) >= today:
            continue
        try:
            if b["prospect_url"] not in pages:
                pages[b["prospect_url"]] = sherdog.parse_fighter(fetcher.get(b["prospect_url"], cache=False, fresh=True), b["prospect_url"])
        except Exception as exc:  # noqa: BLE001
            log(f"  {b['prospect']}: {exc}")
            continue
        page = pages[b["prospect_url"]]
        for cb in page.bouts:
            if abs((cb.date - date.fromisoformat(b["date"])).days) <= 1 and (cb.opponent_url or "").rstrip("/") == b["opponent_url"].rstrip("/").replace(SHERDOG, ""):
                b.update(result=cb.result, method=cb.method.value if hasattr(cb.method, "value") else str(cb.method), round=cb.round,
                         opponent=cb.opponent or b["opponent"])
                done += 1
                break
            if abs((cb.date - date.fromisoformat(b["date"])).days) <= 1 and _slug_name(b["opponent_url"]).lower() in (cb.opponent or "").lower():
                b.update(result=cb.result, method=cb.method.value if hasattr(cb.method, "value") else str(cb.method), round=cb.round, opponent=cb.opponent)
                done += 1
                break
        else:
            if (today - date.fromisoformat(b["date"])).days > 10:
                b["result"] = "not held"  # off the record ten days later: cancelled or moved
    return done


def cmd_prospect_week(args) -> int:
    from .sources.common import Fetcher

    today = date.today()
    data = json.loads(PROSPECTS.read_text())
    prospects = {p["sherdog_url"]: p for p in data["prospects"] if p.get("sherdog_url")}
    f = Fetcher(ROOT / ".cache" / "pages", delay=args.delay, user_agent=UA)
    known = [json.loads(l) for l in FIGHTS.read_text().splitlines() if l.strip()] if FIGHTS.exists() else []
    key = lambda b: (b["date"], b["prospect_url"], b["opponent_url"])  # noqa: E731
    have = {key(b) for b in known}
    found = find_bouts(f, prospects, today - timedelta(days=1), today + timedelta(days=args.days))
    new = [b for b in found if key(b) not in have]
    known += new
    graded = grade(f, known, today)
    known.sort(key=lambda b: (b["date"], b.get("p4p_rank") or 9999))
    FIGHTS.parent.mkdir(parents=True, exist_ok=True)
    FIGHTS.write_text("".join(json.dumps(b, ensure_ascii=False) + "\n" for b in known))
    upcoming = [b for b in known if b["date"] >= today.isoformat() and not b.get("result")]
    recent = [b for b in known if b.get("result") and b["result"] != "not held" and b["date"] >= (today - timedelta(days=60)).isoformat()]
    data["week"] = {"fetched": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "upcoming": upcoming,
                    "recent": sorted(recent, key=lambda b: b["date"], reverse=True)}
    PROSPECTS.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print(f"{len(found)} prospect bouts in the next {args.days} days ({len(new)} new); {graded} results filled in; "
          f"{len(recent)} results in the last 60 days")
    for b in upcoming[:20]:
        print(f"  {b['date']}  #{b['p4p_rank']:<4} {b['prospect']:<26} vs {b['opponent']:<24} {b['event'][:40]}")
    return 0


def register(sub) -> None:
    p = sub.add_parser("prospect-week", help="listed prospects booked in the coming days, and last week's results")
    p.add_argument("--days", type=int, default=9)
    p.add_argument("--delay", type=float, default=1.5)
    p.set_defaults(func=cmd_prospect_week)
