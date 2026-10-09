"""Sherdog organization pages for the regional promotions in our rating (the Minor Leagues tab).

For each promotion: one fighter page (cached when we have it) for an event link, that event's page for the
organization link, then the organization's event list (date, event, venue and city) across its pages.
Stored in data/regional/orgs.json; resumable (promotions already stored are skipped). Polite: requests are
spaced (--delay) and only fighter, event and organization pages are read.

    python scripts/crawl_promotions.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mma_predictor import regional as R  # noqa: E402
from mma_predictor.sources.common import Fetcher  # noqa: E402
from mma_predictor.sources.html import parse_html  # noqa: E402

BASE = "https://www.sherdog.com"
OUT = ROOT / "data" / "regional" / "orgs.json"
UA = "Mozilla/5.0 (compatible; mma-predictor/0.1; personal research)"


def org_events(f: Fetcher, org_url: str, max_pages: int = 12) -> list:
    rows, seen = [], set()
    for page in range(1, max_pages + 1):
        html = f.get(org_url if page == 1 else f"{org_url}/recent-events/{page}")
        new = 0
        for tr in parse_html(html).find_all("tr"):
            a = tr.find("a", pred=lambda x: x.attrs.get("href", "").startswith("/events/"))
            tds = tr.child_elements()
            if a is None or len(tds) < 3:
                continue
            href = a.attrs["href"]
            if href in seen:
                continue
            try:
                d = datetime.strptime(re.sub(r"\s+", " ", tds[0].text().strip()), "%b %d %Y").date().isoformat()
            except ValueError:
                continue
            seen.add(href)
            new += 1
            rows.append([d, tds[1].text().strip(), tds[2].text().strip()])
        if not new or f"recent-events/{page + 1}" not in html:
            break
    return sorted(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--delay", type=float, default=1.6)
    args = ap.parse_args()
    f = Fetcher(ROOT / ".cache" / "pages", delay=args.delay, user_agent=UA)
    store = json.loads(OUT.read_text()) if OUT.exists() else {}
    recs = R.load_records()
    proms = [p["promotion"] for p in R.promotions()]
    # Fighters we crawled who fought in each promotion, most recent bout first.
    who: dict = {}
    for url, r in recs.items():
        for b in r["bouts"]:
            who.setdefault(R.promotion(b.get("e", "")), []).append((b["d"], url))
    for i, prom in enumerate(proms, 1):
        if prom in store:
            continue
        org = None
        for _, url in sorted(set(who.get(prom, [])), reverse=True)[:4]:
            try:
                html = f.get(url)
            except OSError as exc:
                print(f"  {prom}: {url}: {exc}", flush=True)
                continue
            links = [(m.group(1), re.sub(r"<[^>]+>", "", m.group(2))) for m in re.finditer(r'href="(/events/[^"]+)"[^>]*>(.*?)</a>', html, re.S)]
            ev = next((h for h, t in links if R.promotion(t.strip()) == prom), None)
            if not ev:
                continue
            m = re.search(r'class="organization".*?href=\'?"?(/organizations/[^\'"]+)', f.get(BASE + ev), re.S)
            if m:
                org = BASE + m.group(1)
                break
        if not org:
            store[prom] = {"org_url": None}
            print(f"[{i}/{len(proms)}] {prom}: no organization found", flush=True)
        else:
            known = next((v for v in store.values() if v.get("org_url") == org), None)
            events = known["events"] if known else org_events(f, org)
            name = re.search(r"/organizations/(.+)-\d+$", org).group(1).replace("-", " ")
            store[prom] = {"org_url": org, "org_name": name, "events": events}
            print(f"[{i}/{len(proms)}] {prom}: {name}, {len(events)} events", flush=True)
        OUT.write_text(json.dumps(store, ensure_ascii=False, indent=0))
    print("Done", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
