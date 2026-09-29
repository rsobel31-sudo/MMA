#!/usr/bin/env python3
"""Crawl Sherdog careers for every UFC-ranked fighter, then their UFC opponents.

Phase 1: the fighters in data/ranked_fighters.json (champion + top 15, both ranking systems).
Phase 2: opponents they met in the UFC, plus fighters from recent UFC events, up to --max.
Everything lands in the page cache; build the dataset afterwards with
`python -m mma_predictor rebuild --data data/sherdog`.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mma_predictor.sources import sherdog  # noqa: E402
from mma_predictor.sources.common import Fetcher  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--cache", default=".cache/pages")
ap.add_argument("--delay", type=float, default=2.5)
ap.add_argument("--max", type=int, default=900, help="phase-2 page budget")
ap.add_argument("--ufc-events", type=int, default=60)
args = ap.parse_args()

f = Fetcher(Path(args.cache), delay=args.delay)
ranked = list(json.load(open("data/ranked_fighters.json"))["urls"].values())
pages = []
print(f"Phase 1: {len(ranked)} ranked fighters", flush=True)
for i, url in enumerate(ranked, 1):
    try:
        p = sherdog.parse_fighter(f.get(url), url)
        pages.append(p)
        print(f"  [{i}/{len(ranked)}] {p.name}: {len(p.bouts)} bouts", flush=True)
    except Exception as exc:  # keep going; report at the end
        print(f"  skip {url}: {exc}", flush=True)

queue = []
for p in pages:
    for b in p.bouts:
        if b.opponent_url and b.event.lower().startswith("ufc"):
            queue.append(b.opponent_url)
try:
    queue += sherdog.recent_event_fighters(f, args.ufc_events, log=lambda m: None)
except Exception as exc:
    print("event seeds failed:", exc, flush=True)
seen = set(ranked)
todo = [u for u in dict.fromkeys(queue) if u not in seen]
print(f"Phase 2: {len(todo)} opponents / event fighters (budget {args.max})", flush=True)
done = 0
for url in todo[: args.max]:
    try:
        cached = f._cache_path(url).exists()
        f.get(url)
        done += 1
        if not cached and done % 10 == 0:
            print(f"  phase 2: {done} pages", flush=True)
    except Exception as exc:
        print(f"  skip {url}: {exc}", flush=True)
print(f"Done: {len(pages)} ranked, {done} phase-2 pages", flush=True)
