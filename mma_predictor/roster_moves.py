"""UFC roster moves: new signings and releases, from Wikipedia's "List of current UFC fighters".

The page keeps a "Recent signings" table (fighters signed who haven't debuted yet: renewals of existing
contracts never appear there, so only newly added fighters count) and a "Recent releases and retirements"
table. Every row cites its source. A move counts once a second source agrees: the cited report itself
(fetched once, and it has to name the fighter and the move; MMA Junkie is approved, though it refuses automated
reads with HTTP 402), an outlet story in our news index, or the outlets' archive search. Tapology and
social-media posts aren't used.

State lives in data/roster/moves.json; confirmed moves feed the prospects build (a signed prospect is marked
and shown on Signed!; they stay ranked until the debut) and the Roster moves panel on UFC Rankings.

    python -m mma_predictor roster-moves
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data" / "roster" / "moves.json"
UA = "mma-predictor/0.1 (personal research)"
SKIP_DOMAINS = ("tapology.com", "instagram.com", "twitter.com", "x.com", "facebook.com", "youtube.com", "tiktok.com")
SIGN_WORDS = re.compile(r"\b(sign(s|ed|ing)?|contract|joins?|added to the roster|debut)\b", re.I)
RELEASE_WORDS = re.compile(r"\b(releas(e|ed|es)|cut|part(s|ed)? ways|retir(e|ed|es|ement)|no longer|depart(s|ed|ure))\b", re.I)


def _text(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def _section(html: str, anchor: str) -> str:
    i = html.find(f'id="{anchor}"')
    if i < 0:
        return ""
    j = html.find("<h2", i + 10)
    return html[i: j if j > 0 else len(html)]


def _refs(html: str) -> Dict[str, str]:
    """cite_note id -> the first external link in that reference."""
    out = {}
    for m in re.finditer(r'<li[^>]*id="(cite_note-[^"]+)"(.*?)</li>', html, re.S):
        link = re.search(r'class="external[^"]*"[^>]*href="([^"]+)"|href="([^"]+)"[^>]*class="external', m.group(2))
        if link:
            out[m.group(1)] = (link.group(1) or link.group(2)).replace("&amp;", "&")
    return out


def _date(s: str) -> str:
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def parse(html: str) -> Dict[str, List[dict]]:
    """{"signings": [...], "releases": [...]} from the roster page, each with name, date, division, refs."""
    refs = _refs(html)
    out: Dict[str, List[dict]] = {"signings": [], "releases": []}
    for kind, anchor in (("signings", "Recent_signings"), ("releases", "Recent_releases_and_retirements")):
        sec = _section(html, anchor)
        header: List[str] = []
        for tr in re.findall(r"<tr.*?</tr>", sec, re.S):
            ths = re.findall(r"<th.*?</th>", tr, re.S)
            if ths and not re.search(r"<td", tr):
                header = [_text(t).lower() for t in ths]
                continue
            tds = re.findall(r"<td.*?</td>", tr, re.S)
            if not header or len(tds) < 3:
                continue
            cells = dict(zip(header, tds))
            name = _text(cells.get("name", ""))
            name = re.sub(r"\s*\[.*?\]\s*|\s*\*\s*$", "", name).strip()
            when = _date(_text(cells.get("date", "")))
            if not name or not when:
                continue
            row = {"name": name, "date": when, "division": _text(cells.get("division", "")),
                   "refs": [refs[r] for r in re.findall(r'href="#(cite_note-[^"]+)"', tr) if r in refs]}
            if kind == "releases":
                row["reason"] = _text(cells.get("reason", "")) or "Released"
            else:
                row["info"] = _text(cells.get("status / next fight / info", ""))[:200]
            if row not in out[kind]:
                out[kind].append(row)
    return out


def _confirm(fetcher, move: dict, kind: str, news: List[dict], log=print) -> Optional[dict]:
    """A second source for the move: the cited report naming the fighter and the move, or a news-index story."""
    last = move["name"].split()[-1].lower()
    words = SIGN_WORDS if kind == "signings" else RELEASE_WORDS
    for url in move.get("refs", []):
        host = urlparse(url).netloc.lower()
        if not host or any(d in host for d in SKIP_DOMAINS):
            continue
        try:
            page = fetcher.get(url)  # cached: each report is read once
        except Exception as exc:  # noqa: BLE001 - a dead link isn't fatal; another source may do
            log(f"  {move['name']}: {url}: {str(exc)[:80]}")
            continue
        text = _text(re.sub(r"<(script|style).*?</\1>", " ", page, flags=re.S))
        if last in text.lower() and words.search(text):
            return {"source": host.replace("www.", ""), "url": url}
    for n in news:
        title = n.get("title", "")
        if (move["name"] in n.get("fighters", []) or last in title.lower()) and words.search(title) and "UFC" in title:
            return {"source": n.get("outlet", ""), "url": n.get("url", "")}
    # Last, the outlets' own archive search (Cageside Press covers every Contender Series result and its
    # contracts): a story near the move's date whose sentences about the fighter mention the move.
    from .news import SEARCHABLE, mentions, parse_wp, wp_search_url

    when = date.fromisoformat(move["date"])
    for outlet, base in SEARCHABLE.items():
        try:
            posts = parse_wp(fetcher.get(wp_search_url(base, move["name"], 10)), outlet)
        except Exception as exc:  # noqa: BLE001
            log(f"  {move['name']}: {outlet} search: {str(exc)[:80]}")
            continue
        for p in posts:
            try:
                near = abs((date.fromisoformat(p["date"]) - when).days) <= 45
            except ValueError:
                near = False
            said = " ".join(mentions(p["text"] + " " + p["title"], move["name"], limit=12, window=0))
            if near and words.search(said):
                return {"source": outlet, "url": p["url"]}
    return None


def sweep(fetcher, log=print) -> dict:
    """Read the roster page, carry over what's already confirmed, try to confirm the rest. Saves the state."""
    from .sources import wikipedia

    html = fetcher.get(wikipedia.ROSTER_URL, cache=False, fresh=True)
    found = parse(html)
    old = json.loads(STATE.read_text()) if STATE.exists() else {"signings": [], "releases": []}
    known = {(k, m["name"], m["date"]): m for k in ("signings", "releases") for m in old.get(k, [])}
    news_path = ROOT / "data" / "scouting" / "news.jsonl"
    news = [json.loads(l) for l in news_path.read_text().splitlines() if l.strip()] if news_path.exists() else []
    state = {"fetched": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "source": wikipedia.ROSTER_URL,
             "signings": [], "releases": []}
    for kind in ("signings", "releases"):
        for m in found[kind]:
            prev = known.get((kind, m["name"], m["date"]), {})
            m["confirmed_by"] = prev.get("confirmed_by") or _confirm(fetcher, m, kind, news, log)
            m["first_seen"] = prev.get("first_seen") or date.today().isoformat()
            state[kind].append(m)
        # A signing that leaves the table has debuted (or the deal fell through): keep it as history.
        current = {(m["name"], m["date"]) for m in found[kind]}
        for m in old.get(kind, []):
            if (m["name"], m["date"]) not in current:
                m.setdefault("left_table", date.today().isoformat())
                state[kind].append(m)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n")
    return state


def current_signings(state: dict) -> List[dict]:
    """Confirmed signings still awaiting a debut."""
    return [m for m in state.get("signings", []) if m.get("confirmed_by") and not m.get("left_table")]


def cmd_roster_moves(args) -> int:
    from .sources.common import Fetcher

    f = Fetcher(ROOT / ".cache" / "pages", delay=args.delay, user_agent=UA)
    st = sweep(f)
    for kind in ("signings", "releases"):
        live = [m for m in st[kind] if not m.get("left_table")]
        ok = [m for m in live if m.get("confirmed_by")]
        print(f"{kind}: {len(live)} on Wikipedia, {len(ok)} confirmed by a second source")
        for m in live[-8:]:
            print(f"  {m['date']}  {m['name']:<26} {m['division']:<20} {m.get('reason', '')[:12]:<12} "
                  f"{'confirmed: ' + m['confirmed_by']['source'] if m.get('confirmed_by') else 'awaiting a second source'}")
    return 0


def register(sub) -> None:
    p = sub.add_parser("roster-moves", help="UFC signings and releases (Wikipedia, confirmed by the cited report)")
    p.add_argument("--delay", type=float, default=1.5)
    p.set_defaults(func=cmd_roster_moves)
