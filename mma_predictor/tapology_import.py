"""Import Tapology pages you saved yourself (Claude doesn't fetch Tapology: its robots.txt bars Anthropic's crawlers).

    python -m mma_predictor tapology-import                       # everything in data/prospects/inbox/
    python -m mma_predictor tapology-import page.html --date 2026-09-14
    python -m mma_predictor tapology-import list.txt --author Hellowhosthat --title "Flyweight prospects" --date 2026-09

What it reads:
- A saved ranking page (browser "Save page as", .html): someone's "My Rankings" list or a community
  ranking. Every fighter linked in it, in page order, becomes one dated call by the list's author,
  added to data/prospects/noted.json and graded like every other call.
- A saved fighter page: the record is parsed and kept in data/tapology/fighters.jsonl, a
  further source to check Sherdog against.
- A pasted list (.txt / .md): one fighter per line; numbering, records and notes after a dash
  are dropped. Give --author, --title and --date (the page's URL with --url if you have it).

A list's author who already has calls elsewhere (e.g. Hellowhosthat on Sherdog's forums) is the
same person: their calls share one track record. Imported files are removed from the inbox.
"""

from __future__ import annotations

import html as htmllib
import json
import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from .prospects import DIVISIONS, fold

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "data" / "prospects" / "inbox"
NOTED = ROOT / "data" / "prospects" / "noted.json"
TAPOLOGY = "https://www.tapology.com"
FIGHTER_LINK = re.compile(r'<a\b[^>]*href="((?:https?://(?:www\.)?tapology\.com)?/fightcenter/fighters/[^"#?]+)"[^>]*>(.*?)</a>', re.S | re.I)


def _text(s: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def page_url(page: str) -> str:
    for rx in (r"<!-- saved from url=\(\d+\)(\S+?) -->", r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"',
               r'<meta[^>]+property="og:url"[^>]+content="([^"]+)"'):
        m = re.search(rx, page, re.I)
        if m:
            return m.group(1)
    return ""


def page_title(page: str) -> str:
    m = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', page, re.I) or re.search(r"<title>(.*?)</title>", page, re.S | re.I)
    t = _text(m.group(1)) if m else ""
    return re.sub(r"\s*[|\-–]\s*Tapology.*$", "", t).strip()


def page_author(page: str, url: str) -> str:
    m = re.search(r"/profiles/([^/\"]+)/", url)
    if m:
        return m.group(1)
    m = re.search(r'(?:by|created by|ranked by)\s*<a[^>]+href="[^"]*/profiles/([^/"]+)', page, re.I)
    return m.group(1) if m else ""


def page_date(page: str) -> str:
    from .sources.common import find_date

    text = _text(re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S | re.I))
    for rx in (r"(?:Last\s+)?Updated:?\s*(.{6,30})", r"(?:Published|Created):?\s*(.{6,30})"):
        for m in re.finditer(rx, text, re.I):
            d = find_date(m.group(1))
            if d:
                return d.isoformat()
    return ""


def clean_name(raw: str) -> str:
    s = _text(raw)
    s = re.sub(r"[\"“”'‘’][^\"“”'‘’]{1,40}[\"“”'‘’]", " ", s)  # nickname in quotes
    s = re.sub(r"\(.*?\)|\[.*?\]", " ", s)
    return re.sub(r"\s+", " ", s).strip(" -–·,")


def ranking_names(page: str) -> List[str]:
    """Fighters linked in the page, in order, once each (navigation and sidebars repeat some links)."""
    names, seen = [], set()
    for href, inner in FIGHTER_LINK.findall(page):
        n = clean_name(inner)
        if not n or len(n) > 60 or not re.search(r"[A-Za-z]", n) or len(n.split()) < 2:
            continue
        k = href.rstrip("/").rsplit("/", 1)[-1]
        if k in seen:
            continue
        seen.add(k)
        names.append(n)
    return names


def text_names(txt: str) -> List[str]:
    out = []
    for line in txt.splitlines():
        s = re.sub(r"^\s*(#?\d+[.)]?|[-*•])\s*", "", line)
        s = re.split(r"\s+[-–—|:]\s+", s)[0]
        s = re.sub(r"\(.*?\)|\[.*?\]|\b\d+-\d+(-\d+)?\b", " ", s)
        s = re.sub(r"\s+", " ", s).strip(" -–·,")
        if s and len(s.split()) >= 2 and len(s) <= 60:
            out.append(s)
    return list(dict.fromkeys(out))


def division_hint(title: str) -> str:
    t = title.lower()
    women = bool(re.search(r"\b(women|wmma|female)", t))
    for d in sorted(DIVISIONS, key=len, reverse=True):
        base = d.replace("Women's ", "").lower()
        if base in t.replace("light heavy", "light heavyweight").replace("lightheavy", "light heavyweight") and (d.startswith("Women") == women):
            return d
    return ""


def add_list(noted: Dict, lst: Dict) -> bool:
    """Append a call list unless the same author/url/date is already there. Links the author to their other calls."""
    key = (fold(lst.get("author", "")), lst.get("url", ""), lst.get("date", ""))
    for l in noted["lists"]:
        if (fold(l.get("author", "")), l.get("url", ""), l.get("date", "")) == key:
            new = [n for n in lst.get("names", []) if fold(n) not in {fold(x) for x in l.get("names", [])}]
            if not new:
                return False
            l["names"] = l.get("names", []) + new  # same caller, same day: one list, more names
            if lst.get("background"):
                l["background"] = (l.get("background", "") + "\n\n" + lst["background"]).strip()
            return True
    who = fold(lst.get("person") or lst.get("author", ""))
    same = [l for l in noted["lists"] if who and fold(l.get("person") or l.get("author", "")) == who]
    if same:
        person = same[0].get("person") or same[0].get("author")
        lst["person"] = person
        for l in same:
            l.setdefault("person", person)
    noted["lists"].append(lst)
    return True


def import_file(path: Path, noted: Dict, args) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    is_html = path.suffix.lower() in (".html", ".htm") or "<html" in raw[:2000].lower()
    url = (args.url or (page_url(raw) if is_html else "")).strip()
    if is_html and "/fightcenter/fighters/" in url:
        from .sources import tapology

        page = tapology.parse_fighter(raw, url)
        out = ROOT / "data" / "tapology" / "fighters.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        rec = {"url": url, "name": page.name, "dob": page.dob.isoformat() if page.dob else "", "bouts": [
            {"date": b.date.isoformat(), "opponent": b.opponent, "result": b.result, "method": getattr(b.method, "value", str(b.method)),
             "round": b.round, "event": b.event} for b in page.bouts]}
        from .refresh import upsert_jsonl

        upsert_jsonl(out, [rec])
        return f"fighter page: {page.name}, {len(page.bouts)} bouts -> data/tapology/fighters.jsonl"
    head: Dict[str, str] = {}
    if not is_html:  # optional "author: / title: / date: / url:" lines at the top of a pasted list
        body = []
        for line in raw.splitlines():
            m = re.match(r"^\s*(author|title|date|url|person)\s*:\s*(.+?)\s*$", line, re.I)
            if m and not body:
                head[m.group(1).lower()] = m.group(2)
            elif line.strip() or body:
                body.append(line)
        raw = "\n".join(body)
        url = url or head.get("url", "")
    names = ranking_names(raw) if is_html else text_names(raw)
    if not names:
        raise ValueError("no fighters found (is this a Tapology ranking page or a one-per-line list?)")
    title = args.title or head.get("title") or (page_title(raw) if is_html else path.stem.replace("-", " "))
    author = args.author or head.get("author") or (page_author(raw, url) if is_html else "")
    when = args.date or head.get("date") or (page_date(raw) if is_html else "")
    if not author:
        raise ValueError("no author found: pass --author")
    if not when:
        when = date.today().isoformat()  # dated when we saw it: never earlier than the real call, so grading stays fair
    lst = {"kind": args.kind, "outlet": "Tapology" if (is_html or "tapology" in url) else args.outlet, "author": author,
           "title": title, "url": url, "date": when, "names": names, "source_file": path.name}
    if args.person or head.get("person"):
        lst["person"] = args.person or head["person"]
    added = add_list(noted, lst)
    hint = division_hint(title)
    if hint:
        for n in names:
            noted.setdefault("division_hints", {}).setdefault(n, hint)
    return f"{'added' if added else 'already there'}: {author} · {title} · {when} · {len(names)} fighters" + (f" · {hint}" if hint else "")


def cmd_tapology_import(args) -> int:
    files = [Path(f) for f in args.files] or sorted(p for p in INBOX.glob("*") if p.is_file() and p.suffix.lower() in (".html", ".htm", ".txt", ".md") and not p.name.lower().startswith("readme"))
    if not files:
        print(f"Nothing to import. Save Tapology pages (or paste lists as .txt) into {INBOX.relative_to(ROOT)}/")
        return 0
    noted = json.loads(NOTED.read_text())
    failed = 0
    for f in files:
        try:
            print(f"{f.name}: {import_file(f, noted, args)}")
            if INBOX in f.resolve().parents and not args.keep:
                f.unlink()
        except Exception as exc:  # noqa: BLE001 - report and keep the file for a retry
            failed += 1
            print(f"{f.name}: NOT imported ({exc})")
    NOTED.write_text(json.dumps(noted, ensure_ascii=False, indent=1))
    print("Next: python scripts/crawl_prospects.py --skip-ranks --noted data/prospects/noted.json  (looks the new names up on Sherdog),"
          " then python -m mma_predictor prospects")
    return 1 if failed else 0


def register(sub) -> None:
    p = sub.add_parser("tapology-import", help="import Tapology pages you saved (ranking lists, fighter pages) or pasted lists")
    p.add_argument("files", nargs="*", help="files to import (default: everything in data/prospects/inbox/)")
    p.add_argument("--author", default="", help="who made the list (default: from the page)")
    p.add_argument("--person", default="", help="same person as an existing caller, if the names differ")
    p.add_argument("--title", default="")
    p.add_argument("--date", default="", help="when the list was made or last updated (YYYY-MM or YYYY-MM-DD)")
    p.add_argument("--url", default="", help="the page's address, if the saved file doesn't carry it")
    p.add_argument("--kind", default="creator", choices=["creator", "forum", "outlet"])
    p.add_argument("--outlet", default="Tapology", help="for pasted lists from elsewhere")
    p.add_argument("--keep", action="store_true", help="leave imported files in the inbox")
    p.set_defaults(func=cmd_tapology_import)
