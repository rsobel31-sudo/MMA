"""Post-fight descriptions: how each bout on a card actually went, from the outlets' own recaps.

For the newest recapped card (or --event), finds in our news index (data/scouting/news.jsonl, the outlets' RSS feeds)
and the outlets' archive search:

- the play-by-play pages: Sherdog's 'play-by-play, results & round scoring' (every bout, round by round, with three
  Sherdog writers' round scores) and MMA Mania's live results (main card), found through each outlet's RSS feed, and
- per-bout recap stories (Cageside Press, MMA Fighting, Sherdog, BJPenn, LowKick MMA, MMA Mania),

and writes a reading packet to .cache/recaps/<id>.json (the outlets' text stays out of the repository) with each bout's
round-by-round text and the recap paragraphs about it. The Sunday card review reads the packet and, for each bout
where two outlets describe it:

- writes a two-or-three sentence "what happened" in our own words (data/scouting/recaps/<id>.json, and the
  `stories` field of recap_reviews/<id> so the Recaps page shows it under the bout), and
- records judged performances in data/scouting/fight_notes.json (-2..+2 per domain, against expectation), which feed
  the sub-ratings on the next export.

    python -m mma_predictor fight-recaps [--event "UFC 332"]
"""

from __future__ import annotations

import html
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .news import SEARCHABLE, fold, parse_wp, wp_search_url
from .recap_cli import bout_key, recap_id

ROOT = Path(__file__).resolve().parents[1]
NEWS = ROOT / "data" / "scouting" / "news.jsonl"
PACKETS = ROOT / ".cache" / "recaps"
STORIES = ROOT / "data" / "scouting" / "recaps"
UA = "mma-predictor/0.1 (personal research)"
RECAP_OUTLETS = ("Cageside Press", "MMA Fighting", "Sherdog", "BJPenn.com", "LowKick MMA", "MMA Mania", "MMA Junkie")
RECAP_WORDS = re.compile(r"\b(def(eats?|eated)?\.?|results?|wins?|won|stops?|submits?|knocks? out|finish(es|ed)?|turns back|decision|edges?|outpoints?|taps?|recap)\b", re.I)


def _text(page: str) -> str:
    page = re.sub(r"<(script|style|noscript).*?</\1>", " ", page, flags=re.S)
    paras = re.findall(r"<p[^>]*>(.*?)</p>", page, flags=re.S)
    body = "\n".join(re.sub(r"<[^>]+>", " ", p) for p in paras) if paras else re.sub(r"<[^>]+>", " ", page)
    return html.unescape(re.sub(r"[ \t\r\f\v]+", " ", body)).strip()


def _surname(name: str) -> str:
    return fold(name).split()[-1]


def play_by_play(page: str, bouts: List[dict]) -> Dict[str, str]:
    """MMA Mania's live blog: '<A> vs. <B> Round 1: ... Round 2: ...' per bout -> {bout key: that text}."""
    flat = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style).*?</\1>", " ", page, flags=re.S))))
    start = flat.upper().find("PLAY-BY-PLAY")
    flat = flat[start:] if start >= 0 else flat
    out_prelims: Dict[str, str] = {}
    heads = list(re.finditer(r"([A-Z][^.:]{2,60}? vs\. [A-Z][^.:]{2,60}?) Round 1:", flat))
    # Prelims get one paragraph each: '<A> vs. <B>: <summary> Official decision: ...'
    pre = flat.find("Prelims", heads[-1].end()) if heads else -1
    if pre >= 0:
        for m in re.finditer(r"([A-Z][\w'.\- ]{2,40}? vs\. [A-Z][\w'.\- ]{2,40}?)\s?: (.+?Official (?:decision|result): [^()]+?\([^)]*\)(?:, round \d \([\d:]+\))?)", flat[pre:pre + 8000]):
            title = fold(m.group(1))
            for b in bouts:
                if _surname(b["a"]) in title and _surname(b["b"]) in title:
                    out_prelims.setdefault(bout_key(b), m.group(0).strip())
    out = {}
    for i, m in enumerate(heads):
        seg = flat[m.start(): heads[i + 1].start() if i + 1 < len(heads) else min(len(flat), m.start() + 6000)]
        title = fold(m.group(1))
        for b in bouts:
            if _surname(b["a"]) in title and _surname(b["b"]) in title:
                out[bout_key(b)] = seg.strip()[:5000]
    for k, t in out_prelims.items():
        out.setdefault(k, t)
    return out


def sherdog_play_by_play(page: str, bouts: List[dict]) -> Dict[str, dict]:
    """Sherdog's '<event> play-by-play, results & round scoring': every bout on the card, round by round, with three
    Sherdog writers' score for each round -> {bout key: {"text", "scores": [[round, "10-9 X", ...], ...]}}."""
    flat = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style).*?</\1>", " ", page, flags=re.S))))
    name = r"[A-Z][\w'.\-]*(?: (?:[A-Z][\w'.\-]*|d[aeo]s?|van|von|de la|bin|al))*"  # 'Lucas dos Santos', 'R.J. Harris'
    heads = list(re.finditer(rf"({name}) \(\d+(?:\.\d+)?[^)]*\) vs\. ({name}) \(\d+(?:\.\d+)?[^)]*\) Round 1", flat))
    out = {}
    for i, m in enumerate(heads):
        seg = flat[m.start(): heads[i + 1].start() if i + 1 < len(heads) else min(len(flat), m.start() + 8000)]
        title = fold(m.group(1) + " " + m.group(2))
        for b in bouts:
            if _surname(b["a"]) in title and _surname(b["b"]) in title:
                rounds = re.split(r"\bRound (\d)\b", seg)
                scores = []
                for j in range(1, len(rounds) - 1, 2):
                    found = re.findall(r"scores the round: (\d+-\d+ [A-Z][\w'.-]+)", rounds[j + 1])
                    if found:
                        scores.append([int(rounds[j])] + found)
                out[bout_key(b)] = {"text": seg.strip()[:7000], "scores": scores}
    return out


PLAY_BY_PLAY_FEEDS = {
    # outlet: (RSS feed, link test, parser kind). MMA Junkie's live blog refuses automated reads (HTTP 402) and Yahoo
    # republishes Sherdog's play-by-play, so neither counts as another source.
    "Sherdog": ("https://www.sherdog.com/rss/news.xml", lambda u: "playbyplay" in u.lower(), "sherdog"),
    "MMA Mania": ("https://www.mmamania.com/rss/index.xml", lambda u: "/ufc-results/" in u and "live-results" in u, "mmamania"),
}


def _feed_links(fetcher, url: str) -> List[Tuple[str, str]]:
    xml = fetcher.get(url, cache=False, fresh=True)
    items = re.findall(r"<(?:item|entry)\b.*?</(?:item|entry)>", xml, flags=re.S)
    out = []
    for it in items:
        t = re.search(r"<title[^>]*>(.*?)</title>", it, flags=re.S)
        l = re.search(r"<link[^>]*>(.*?)</link>|<link[^>]*href=\"([^\"]+)\"", it, flags=re.S)
        if t and l:
            title = html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", t.group(1))).strip()
            out.append((title, (l.group(1) or l.group(2) or "").strip()))
    return out


def _event_words(ev: dict) -> List[str]:
    """Surnames from the main event ('Allen vs. Duncan') to match a play-by-play title to this card."""
    m = re.search(r"([A-Z][\w.' -]+?) vs\.? ([A-Z][\w.' -]+)$", ev["event"])
    return [fold(x).split()[-1] for x in m.groups()] if m else []


def _bout_paragraphs(text: str, b: dict) -> str:
    keys = (_surname(b["a"]), _surname(b["b"]))
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    keep = [p for p in paras if any(k in fold(p) for k in keys) or re.search(r"\bround\b|\bscorecards?\b|\bjudges\b", p, re.I)]
    return "\n".join(keep)[:5000]


def collect(ev: dict, fetcher, log=print) -> dict:
    when = date.fromisoformat(ev["date"])
    window = {(when + timedelta(days=d)).isoformat() for d in (-1, 0, 1, 2, 3)}
    news = [json.loads(l) for l in NEWS.read_text().splitlines() if l.strip()] if NEWS.exists() else []
    near = [n for n in news if n.get("date", "")[:10] in window]
    bouts = {bout_key(b): {"a": b["a"], "b": b["b"], "winner": b.get("winner"), "method": b.get("method"),
                           "round": b.get("round"), "sources": []} for b in ev["bouts"]}
    # 1. Play-by-play pages (round-by-round notes for the card): the outlets' feeds, then our news index.
    words = _event_words(ev)
    for outlet, (feed, test, kind) in PLAY_BY_PLAY_FEEDS.items():
        links = []
        try:
            links = [u for t, u in _feed_links(fetcher, feed) if test(u) and all(w in fold(t + " " + u) for w in words)]
        except Exception as exc:  # noqa: BLE001 - fall back to the news index
            log(f"  {outlet} feed: {str(exc)[:80]}")
        links += [n["url"] for n in near if n.get("outlet") == outlet and test(n.get("url", ""))
                  and all(w in fold(n.get("title", "") + " " + n["url"]) for w in words)]
        for url in list(dict.fromkeys(links))[:1]:
            try:
                page = fetcher.get(url)
            except Exception as exc:  # noqa: BLE001
                log(f"  {outlet} play-by-play: {str(exc)[:80]}")
                continue
            if kind == "sherdog":
                got = sherdog_play_by_play(page, ev["bouts"])
                for k, v in got.items():
                    bouts[k]["sources"].append({"outlet": outlet, "kind": "play-by-play", "url": url, "text": v["text"],
                                                "round_scores": v["scores"]})
            else:
                got = play_by_play(page, ev["bouts"])
                for k, t in got.items():
                    bouts[k]["sources"].append({"outlet": outlet, "kind": "play-by-play", "url": url, "text": t})
            log(f"  {outlet} play-by-play: {len(got)} of {len(bouts)} bouts ({url})")
    # 2. Per-bout recap stories: the news index first, then the outlets' archive search.
    for k, b in bouts.items():
        sa, sb = _surname(b["a"]), _surname(b["b"])
        cands = [n for n in near if n.get("outlet") in RECAP_OUTLETS and "live-results" not in n.get("url", "") and "playbyplay" not in n.get("url", "").lower()
                 and (sa in fold(n.get("title", "")) or sb in fold(n.get("title", "")))
                 and RECAP_WORDS.search(n.get("title", "")) and not re.search(r"\b(preview|predictions?|picks|odds|weigh)", n.get("title", ""), re.I)]
        seen = {s["url"] for s in b["sources"]}
        for n in cands[:3]:
            if n["url"] in seen:
                continue
            try:
                t = _bout_paragraphs(_text(fetcher.get(n["url"])), b)
            except Exception as exc:  # noqa: BLE001
                log(f"  {n['outlet']} {n['url'][:60]}: {str(exc)[:60]}")
                continue
            if t and sa in fold(t) and sb in fold(t):  # a story about this bout, not a namesake's
                b["sources"].append({"outlet": n["outlet"], "kind": "recap", "url": n["url"], "title": n.get("title", ""), "text": t})
                seen.add(n["url"])
        if len({s["outlet"] for s in b["sources"]}) < 2:
            for outlet, base in SEARCHABLE.items():
                posts = []
                for q in (f"{b['a'].split()[-1]} {b['b'].split()[-1]}", b["a"], b["b"]):
                    try:
                        posts += parse_wp(fetcher.get(wp_search_url(base, q, 5)), outlet)
                    except Exception:  # noqa: BLE001
                        continue
                for p in posts:
                    if p.get("date", "")[:10] in window and p["url"] not in seen and RECAP_WORDS.search(p.get("title", "")) \
                            and not re.search(r"\b(preview|predictions?|picks|odds|weigh)", p.get("title", ""), re.I):
                        both = sa in fold(p.get("title", "") + " " + p.get("text", "")) and sb in fold(p.get("title", "") + " " + p.get("text", ""))
                        t = _bout_paragraphs(p.get("text", "").replace(". ", ".\n"), b) if both else ""
                        if t:
                            b["sources"].append({"outlet": outlet, "kind": "recap", "url": p["url"], "title": p.get("title", ""), "text": t})
                            seen.add(p["url"])
                if len({s["outlet"] for s in b["sources"]}) >= 2:
                    break
    rid = recap_id(ev)
    packet = {"id": rid, "event": ev["event"], "date": ev["date"], "bouts": bouts}
    PACKETS.mkdir(parents=True, exist_ok=True)
    (PACKETS / f"{rid}.json").write_text(json.dumps(packet, ensure_ascii=False, indent=1))
    save_index(packet)
    return packet


def closeness(scores: List[list], winner: Optional[str], decision: bool) -> Optional[str]:
    """How the bout read to Sherdog's three scorers, round by round:
    - decisions: 'disputed' (most scorers had the loser ahead), 'close' (rounds split or scorers disagreed), 'clear';
    - finishes: 'from behind' (most scorers had the winner trailing before the finish), else None."""
    if not scores or not winner:
        return None
    w = fold(winner).split()[-1]

    # "10-9 X": X gets 10 and the other fighter 9. Each scorer's total margin for the official winner:
    margins = []
    for i in range(max(len(r) - 1 for r in scores)):
        me = them = 0
        for r in scores:
            if i + 1 < len(r):
                m = re.match(r"(\d+)-(\d+) (.+)", r[i + 1])
                if m:
                    hi, lo, who = int(m.group(1)), int(m.group(2)), fold(m.group(3)).split()[-1]
                    me, them = (me + hi, them + lo) if who == w else (me + lo, them + hi)
        margins.append(me - them)
    behind = sum(1 for d in margins if d < 0)
    if decision:
        if behind * 2 > len(margins):
            return "disputed"
        split = any(len({x.split()[-1] for x in r[1:]}) > 1 for r in scores) or len({r[1].split()[-1] for r in scores}) > 1
        return "close" if split else "clear"
    return "from behind" if behind * 2 > len(margins) else None


def save_index(packet: dict) -> None:
    """The committed part: which outlets described each bout (links) and Sherdog's round scores (facts, not the
    outlets' text), next to any summaries already written for the card."""
    f = STORIES / f"{packet['id']}.json"
    doc = json.loads(f.read_text()) if f.exists() else {"id": packet["id"], "event": packet["event"], "date": packet["date"], "stories": {}}
    doc["coverage"] = {}
    for k, b in packet["bouts"].items():
        sc = next((s.get("round_scores") for s in b["sources"] if s.get("round_scores")), None)
        doc["coverage"][k] = {"a": b["a"], "b": b["b"], "winner": b["winner"], "method": b["method"], "round": b["round"],
                              "outlets": [{"outlet": s["outlet"], "kind": s["kind"], "url": s["url"]} for s in b["sources"]],
                              "round_scores": sc, "closeness": closeness(sc, b["winner"], "DEC" in str(b["method"]))}
    STORIES.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")


def cmd_fight_recaps(args) -> int:
    from .sources.common import Fetcher

    recaps = json.loads((ROOT / "app" / "data.json").read_text()).get("recaps") or {}
    events = recaps.get("events") or []
    ev = next((e for e in events if args.event.lower() in e["event"].lower()), None) if args.event else (events[0] if events else None)
    if not ev:
        print("No recapped card found.")
        return 1
    f = Fetcher(ROOT / ".cache" / "pages", delay=args.delay, user_agent=UA)
    print(f"{ev['event']} ({ev['date']}): recap id {recap_id(ev)}")
    packet = collect(ev, f)
    two = 0
    for k, b in packet["bouts"].items():
        outlets = sorted({s["outlet"] for s in b["sources"]})
        two += len(outlets) >= 2
        print(f"  {b['winner'] or 'draw':<26} {b['a']} vs {b['b']}: {', '.join(outlets) or 'no recap found'}")
    print(f"{two} of {len(packet['bouts'])} bouts described by two outlets; packet: {PACKETS / (packet['id'] + '.json')}")
    written = json.loads((STORIES / f"{packet['id']}.json").read_text()).get("stories", {})
    missing = [f"{b['a']} vs {b['b']} [{k}]" for k, b in packet["bouts"].items() if k not in written]
    print(f"'What happened' written for {len(packet['bouts']) - len(missing)} of {len(packet['bouts'])} bouts"
          + (": still to write: " + "; ".join(missing) if missing else ""))
    if args.show:
        for k, b in packet["bouts"].items():
            print(f"\n===== {b['a']} vs {b['b']} [{k}] — {b['winner']} by {b['method']} R{b['round']}")
            for s in b["sources"]:
                print(f"--- {s['outlet']} ({s['kind']}): {s['url']}\n{s['text'][:2500]}")
    return 0


def register(sub) -> None:
    p = sub.add_parser("fight-recaps", help="post-fight descriptions of each bout (MMA Mania play-by-play + outlet recaps)")
    p.add_argument("--event", default="")
    p.add_argument("--show", action="store_true", help="print the packet's text for reading")
    p.add_argument("--delay", type=float, default=1.5)
    p.set_defaults(func=cmd_fight_recaps)
