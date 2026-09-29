#!/usr/bin/env python3
"""Fetch full Sherdog records for every fighter on scheduled UFC cards.

Uses Sherdog's own upcoming UFC event pages (which link each scheduled
fighter) plus any card fighter whose Sherdog link is already known.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mma_predictor.sources import sherdog  # noqa: E402
from mma_predictor.sources.common import Fetcher  # noqa: E402
from mma_predictor.sources.events import link_names  # noqa: E402

f = Fetcher(Path(".cache/pages"), delay=3.0)
urls = []
try:
    urls += sherdog.upcoming_event_fighters(f)
except Exception as exc:
    print("upcoming events failed:", exc, flush=True)
up = json.loads(Path("data/upcoming.json").read_text())
rows = {r["name"]: r["url"] for r in csv.DictReader(open("data/sherdog/fighters.csv")) if r.get("url")}
aliases = json.loads(Path("data/name_aliases.json").read_text())
names = {str(b[k]) for e in up["events"] for b in e["bouts"] for k in ("a", "b")}
linked = link_names(names, set(rows), aliases)
urls += [rows[n] for n in linked.values()]
urls = list(dict.fromkeys(u for u in urls if "/fighter/" in u))
print(f"{len(urls)} card fighters", flush=True)
for i, u in enumerate(urls, 1):
    try:
        cached = f._cache_path(u).exists()
        p = sherdog.parse_fighter(f.get(u), u)
        if not cached:
            print(f"  [{i}/{len(urls)}] {p.name}: {len(p.bouts)} bouts", flush=True)
    except Exception as exc:
        print(f"  skip {u}: {exc}", flush=True)
print("Done", flush=True)
