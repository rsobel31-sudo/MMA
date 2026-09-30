#!/usr/bin/env python3
"""Crawl the second sources used to verify (and extend) the main data.

  statsfight   every UFC bout page in StatsFight's sitemap -> data/statsfight/bouts.jsonl
  fightmatrix  Fight Matrix profiles: the top of every division, then their
               UFC opponents, up to --max -> data/fightmatrix/profiles.jsonl

Pages are parsed on the fly and only the parsed record is kept (the raw
pages are large). Both are resumable: URLs already in the output are skipped.
"""
import argparse
import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mma_predictor.sources import fightmatrix, statsfight  # noqa: E402
from mma_predictor.sources.common import Fetcher  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("source", choices=["statsfight", "fightmatrix"])
ap.add_argument("--delay", type=float, default=2.0)
ap.add_argument("--max", type=int, default=1500, help="fightmatrix profile budget")
ap.add_argument("--rank-pages", type=int, default=2, help="fightmatrix ranking pages (25 each) per division")
args = ap.parse_args()

fetcher = Fetcher(Path(".cache/pages"), delay=args.delay, user_agent="mma-predictor/0.1 (personal research)")


def done_urls(path: Path) -> set:
    if not path.exists():
        return set()
    return {json.loads(line)["url"] for line in path.open(encoding="utf-8") if line.strip()}


def encode(o):
    if dataclasses.is_dataclass(o):
        return dataclasses.asdict(o)
    return str(o)


if args.source == "statsfight":
    out = Path("data/statsfight/bouts.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    seen = done_urls(out)
    urls = [u for u in statsfight.bout_urls(fetcher.get(statsfight.SITEMAP, cache=False)) if u not in seen]
    print(f"{len(urls)} UFC bouts to fetch ({len(seen)} already done)", flush=True)
    with out.open("a", encoding="utf-8") as fh:
        for i, u in enumerate(urls, 1):
            try:
                rec = statsfight.parse_bout(fetcher.get(u, cache=False), u) or {"url": u, "error": "unparsed"}
            except Exception as exc:  # keep going; the record notes the failure
                rec = {"url": u, "error": str(exc)[:200]}
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            if i % 50 == 0:
                print(f"  {i}/{len(urls)}", flush=True)
else:
    out = Path("data/fightmatrix/profiles.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    seen = done_urls(out)
    queue = []
    for gender, slugs in fightmatrix.RANK_PAGES.items():
        for slug in slugs:
            for page in range(1, args.rank_pages + 1):
                try:
                    queue += [u for _, _, u, _ in fightmatrix.parse_rankings(fetcher.get(fightmatrix.rankings_url(slug, page)))]
                except Exception as exc:
                    print(f"  ranking {slug} p{page}: {exc}", flush=True)
    if out.exists():  # resuming: re-expand from profiles already saved
        for line in out.open(encoding="utf-8"):
            for b in json.loads(line).get("bouts", []):
                if str(b.get("event", "")).upper().startswith("UFC"):
                    queue.append(b["opponent_url"])
    print(f"{len(queue)} fighters to start from ({len(seen)} profiles already done)", flush=True)
    queued = set(queue)
    fetched = 0
    with out.open("a", encoding="utf-8") as fh:
        while queue and len(seen) < args.max:
            u = queue.pop(0)
            if u in seen:
                continue
            try:
                prof = fightmatrix.parse_profile(fetcher.get(u, cache=False), u)
            except Exception as exc:
                print(f"  skip {u}: {exc}", flush=True)
                seen.add(u)
                continue
            seen.add(u)
            fh.write(json.dumps(dataclasses.asdict(prof), default=encode) + "\n")
            fh.flush()
            fetched += 1
            # Expand through UFC opponents only, so the crawl stays on UFC-level fighters.
            for b in prof.bouts:
                if b.event.upper().startswith("UFC") and b.opponent_url not in queued:
                    queued.add(b.opponent_url)
                    queue.append(b.opponent_url)
            if fetched % 50 == 0:
                print(f"  {len(seen)} profiles, {len(queue)} queued", flush=True)
print("done", flush=True)
