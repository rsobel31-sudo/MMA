"""StatsFight (statsfight.com): an independent second source for recent bouts.

StatsFight collects its own live stats, separately from the UFC's official
provider (UFCStats), so it is used to *verify* rather than to supply data:

- the result (winner, method, round and time), and
- the per-fighter strike and takedown counts, and
- height and reach (a second source for reach, which Sherdog lacks).

Its strike counts use its own definition (not UFC "significant strikes"),
so they are compared by direction and rough size, not exactly. robots.txt
allows bout pages (it disallows /api/ and /search/).
"""

from __future__ import annotations

import html as htmllib
import re
from datetime import datetime
from typing import Dict, List, Optional

SITEMAP = "https://statsfight.com/sitemaps/0.xml"


def _text(page: str) -> str:
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)
    t = re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " | ", t)))
    return re.sub(r"(\|\s*)+", "| ", t)


def bout_urls(sitemap_xml: str, promotion: str = "ufc") -> List[str]:
    """Bout pages (schedule/<promotion>/<event>/<bout>/) listed in the sitemap."""
    urls = re.findall(r"<loc>([^<]+)</loc>", sitemap_xml)
    return [u for u in urls if re.match(rf"https://statsfight\.com/schedule/{promotion}/[^/]+/[^/]+/$", u)]


def _pair(txt: str, label: str) -> Optional[List[int]]:
    """'<label> | ... | a | / | b | Total | c | / | d' -> [a, b, c, d] (fighter A landed/attempted, then B)."""
    m = re.search(re.escape(label) + r" \| [^|]+\| (\d+) \| / \| (\d+) \| Total \| (\d+) \| / \| (\d+) \|", txt)
    return [int(x) for x in m.groups()] if m else None


def parse_bout(page: str, url: str) -> Optional[Dict]:
    title = re.search(r"<title>(.*?) - Stats Fight</title>", page)
    if not title or " vs " not in title.group(1):
        return None
    a, b = [htmllib.unescape(x).strip() for x in title.group(1).split(" vs ", 1)]
    txt = _text(page)
    out: Dict = {"url": url, "a": a, "b": b}
    # Result block: "<first> | <last> | Win | UD | R5, 25:00 | VS | ... | <first> | <last> | Loss"
    head = txt[txt.find("Live Stats, Fight Analytics & Results"):]
    res = re.search(r"\| (Win|Loss|Draw|NC|No Contest) \| ([^|]+?) \| (?:\(([^)]*)\) )?R(\d+), (\d+):(\d+) \| VS", head)
    if res:
        out["a_result"] = res.group(1)
        out["method"] = res.group(2).strip() + (f" ({res.group(3)})" if res.group(3) else "")
        out["round"] = int(res.group(4))
        out["elapsed"] = f"{int(res.group(5))}:{res.group(6)}"  # total fight time, as shown
    when = re.search(r"Event Date & Venue \|.*?\| \w{3}, (\w+ \d+, \d{4}) \|", txt)
    if when:
        out["date"] = datetime.strptime(when.group(1), "%B %d, %Y").date().isoformat()
    tape = txt[txt.find("Tale of the Tape"):]
    for key, label in (("height_cm", "Height"), ("reach_cm", "Reach")):
        m = re.search(r"\| (?:[^|]*\((\d+)cm\)|N/D) \| " + label + r" \| (?:[^|]*\((\d+)cm\)|N/D) \|", tape)
        if m:
            out[key] = {"a": int(m.group(1)) if m.group(1) else None, "b": int(m.group(2)) if m.group(2) else None}
    for key, label in (("strikes", "Strikes"), ("takedowns", "Takedowns"), ("submissions", "Submissions")):
        v = _pair(txt, label)
        if v:
            out[key] = {"a": v[:2], "b": v[2:]}
    return out
