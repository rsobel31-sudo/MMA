"""MMA news and analysis from the major outlets, linked to fighters.

Two ways in:

- ``feeds``: the outlets' RSS/Atom feeds (latest headlines: fight-week news,
  injuries, replacements, weight misses, camp changes).
- ``search``: the archive search some outlets expose (WordPress' public API),
  for everything written about one fighter.

Only metadata is kept in the repository (outlet, title, link, date and the
fighters an article is about). Article text is cached locally for reading and
never committed: scouting reports are written in our own words and cite the
articles they draw on.
"""

from __future__ import annotations

import hashlib
import html as htmllib
import json
import re
import unicodedata
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

FEEDS = {
    "MMA Fighting": "https://www.mmafighting.com/rss/index.xml",
    "Sherdog": "https://www.sherdog.com/rss/news.xml",
    "Bloody Elbow": "https://bloodyelbow.com/feed/",
    "Cageside Press": "https://cagesidepress.com/feed/",
    "MMA Mania": "https://www.mmamania.com/rss/index.xml",
    "BJPenn.com": "https://www.bjpenn.com/feed/",
    "MMA Weekly": "https://www.mmaweekly.com/feed",
    "LowKick MMA": "https://www.lowkickmma.com/feed/",
    "ESPN": "https://www.espn.com/espn/rss/mma/news",
}
# Outlets whose archives answer https://<host>/wp-json/wp/v2/posts?search=...
SEARCHABLE = {
    "Cageside Press": "https://cagesidepress.com",
    "BJPenn.com": "https://www.bjpenn.com",
    "LowKick MMA": "https://www.lowkickmma.com",
}


def fold(s: str) -> str:
    """Lowercase, accents stripped, punctuation to spaces."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " " + re.sub(r"[^a-z0-9]+", " ", s).strip() + " "


def text_of(fragment: str) -> str:
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", fragment, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</p>|</h\d>|</li>", "\n", s, flags=re.I)
    s = htmllib.unescape(re.sub(r"<[^>]+>", " ", s))
    return re.sub(r"[ \t\r\f\v]+", " ", re.sub(r"\n\s*\n+", "\n\n", s)).strip()


def _date(raw: str) -> str:
    raw = raw.strip()
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError):
        pass
    m = re.match(r"(\d{4}-\d{2}-\d{2})", raw)
    return m.group(1) if m else ""


def parse_feed(xml: str, outlet: str) -> List[Dict[str, str]]:
    """Items from an RSS or Atom feed: title, url, date, and the teaser (for tagging only)."""
    out = []
    for block in re.findall(r"<(?:item|entry)\b.*?</(?:item|entry)>", xml, re.S):
        title = re.search(r"<title[^>]*>(.*?)</title>", block, re.S)
        link = re.search(r'<link[^>]*rel="alternate"[^>]*href="([^"]+)"', block) or re.search(r"<link>(.*?)</link>", block, re.S) \
            or re.search(r'<link[^>]*href="([^"]+)"', block)
        date = re.search(r"<(?:pubDate|published|updated|dc:date)>(.*?)</", block, re.S)
        desc = re.search(r"<(?:description|summary|content)[^>]*>(.*?)</(?:description|summary|content)>", block, re.S)
        if not title or not link:
            continue
        unwrap = lambda s: re.sub(r"^<!\[CDATA\[|\]\]>$", "", s.strip())  # noqa: E731
        out.append({
            "outlet": outlet, "title": text_of(unwrap(title.group(1))), "url": unwrap(link.group(1)).strip(),
            "date": _date(date.group(1)) if date else "", "teaser": text_of(unwrap(htmllib.unescape(desc.group(1)))) if desc else "",
        })
    return out


class Roster:
    """Full-name matching of fighters in text (accent- and case-insensitive)."""

    def __init__(self, names: Iterable[str], aliases: Optional[Dict[str, str]] = None) -> None:
        self.keys: Dict[str, str] = {}
        for n in names:
            if len(fold(n).split()) >= 2:
                self.keys[fold(n)] = n
        for other, n in (aliases or {}).items():
            if not other.startswith("_") and n in names and len(fold(other).split()) >= 2:
                self.keys[fold(other)] = n
        self._rx = re.compile("|".join(re.escape(k.strip()) for k in sorted(self.keys, key=len, reverse=True))) if self.keys else None

    def find(self, text: str) -> List[str]:
        if not self._rx:
            return []
        t = fold(text)
        hits = []
        for m in self._rx.finditer(t):
            # whole words only
            if t[m.start() - 1] == " " and t[m.end()] == " ":
                n = self.keys[" " + m.group(0) + " "]
                if n not in hits:
                    hits.append(n)
        return hits


class NewsIndex:
    """data/scouting/news.jsonl: one line per article (metadata only), keyed by URL."""

    def __init__(self, path: Path, cache: Path) -> None:
        self.path, self.cache = Path(path), Path(cache)
        self.items: Dict[str, Dict[str, object]] = {}
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    it = json.loads(line)
                    self.items[it["url"]] = it

    def add(self, item: Dict[str, object], fighters: List[str], text: Optional[str] = None) -> bool:
        url = str(item["url"])
        new = url not in self.items
        cur = self.items.setdefault(url, {k: item.get(k, "") for k in ("outlet", "title", "url", "date")})
        cur["fighters"] = sorted(set(cur.get("fighters", [])) | set(fighters))
        if text:
            self.cache.mkdir(parents=True, exist_ok=True)
            (self.cache / self.key(url)).write_text(text)
        return new

    @staticmethod
    def key(url: str) -> str:
        return hashlib.sha1(url.encode()).hexdigest() + ".txt"

    def text(self, url: str) -> Optional[str]:
        p = self.cache / self.key(url)
        return p.read_text() if p.exists() else None

    def about(self, name: str) -> List[Dict[str, object]]:
        return sorted((it for it in self.items.values() if name in it.get("fighters", [])), key=lambda it: str(it.get("date", "")), reverse=True)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        rows = sorted(self.items.values(), key=lambda it: (str(it.get("date", "")), str(it["url"])), reverse=True)
        self.path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def wp_search_url(base: str, name: str, per_page: int = 20) -> str:
    from urllib.parse import quote

    return f"{base}/wp-json/wp/v2/posts?search={quote(name)}&per_page={per_page}&_fields=date,link,title,content"


def parse_wp(payload: str, outlet: str) -> List[Dict[str, str]]:
    try:
        rows = json.loads(payload)
    except ValueError:
        return []
    out = []
    for r in rows if isinstance(rows, list) else []:
        out.append({"outlet": outlet, "url": r.get("link", ""), "date": str(r.get("date", ""))[:10],
                    "title": text_of((r.get("title") or {}).get("rendered", "")),
                    "text": text_of((r.get("content") or {}).get("rendered", ""))})
    return out


def mentions(text: str, name: str, limit: int = 8, window: int = 1) -> List[str]:
    """Sentences about a fighter (full name or surname), with a sentence of context either side."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+|\n+", text) if p.strip()]
    keys = {fold(name).strip(), fold(name).split()[-1]}
    out, seen = [], set()
    for i, p in enumerate(parts):
        f = fold(p)
        if any(f" {k} " in f for k in keys):
            lo, hi = max(0, i - window), min(len(parts), i + window + 1)
            chunk = " ".join(parts[lo:hi])
            if chunk not in seen:
                seen.add(chunk)
                out.append(chunk)
        if len(out) >= limit:
            break
    return out


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
