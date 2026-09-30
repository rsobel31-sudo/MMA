#!/usr/bin/env python3
"""Crawl the second sources used to verify (and extend) the main data.

  statsfight   every UFC bout page in StatsFight's sitemap -> data/statsfight/bouts.jsonl
  fightmatrix  Fight Matrix profiles: the top of every division, then their
               UFC opponents, up to --max -> data/fightmatrix/profiles.jsonl
  bestfightodds  BestFightOdds fighter pages (betting lines and their movement):
               everyone on the upcoming cards and in the UFC rankings, found by
               search, then their UFC opponents, up to --max
               -> data/bestfightodds/fighters.jsonl

Pages are parsed on the fly and only the parsed record is kept (the raw
pages are large). Both are resumable: URLs already in the output are skipped.
"""
import argparse
import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mma_predictor.sources import bestfightodds, fightmatrix, statsfight  # noqa: E402
from mma_predictor.sources.wikipedia import match_key  # noqa: E402
from mma_predictor.sources.common import Fetcher  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("source", choices=["statsfight", "fightmatrix", "bestfightodds"])
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


if args.source == "bestfightodds":
    out = Path("data/bestfightodds/fighters.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    seen = done_urls(out)
    queue: list = []
    if out.exists():  # resuming: re-expand from pages already saved
        for line in out.open(encoding="utf-8"):
            for b in json.loads(line).get("bouts", []):
                if str(b.get("event", "")).upper().startswith("UFC"):
                    queue.append(b["opponent_url"])
    else:
        up = json.loads(Path("data/upcoming.json").read_text())
        names = [str(b[k]) for e in up["events"] for b in e["bouts"] for k in ("a", "b")]
        names += [r["name"] for r in json.loads(Path("data/ranked_fighters.json").read_text()).get("rankings", [])]
        names = list(dict.fromkeys(names))
        print(f"searching {len(names)} card and ranked fighters", flush=True)
        for n in names:
            try:
                hits = bestfightodds.search_results(fetcher.get(bestfightodds.search_url(n), cache=False))
            except Exception as exc:
                print(f"  search {n}: {exc}", flush=True)
                continue
            exact = [u for name, u in hits if match_key(name) == match_key(n)]
            if len(exact) == 1:  # ambiguous or missing names are skipped
                queue.append(exact[0])
    print(f"{len(queue)} fighters to start from ({len(seen)} pages already done)", flush=True)
    queued = set(queue)
    with out.open("a", encoding="utf-8") as fh:
        while queue and len(seen) < args.max:
            u = queue.pop(0)
            if u in seen:
                continue
            seen.add(u)
            try:
                page = fetcher.get(u, cache=False)
                bouts = bestfightodds.parse_fighter(page, u)
            except Exception as exc:
                print(f"  skip {u}: {exc}", flush=True)
                continue
            name = bouts[0].fighter if bouts else ""
            fh.write(json.dumps({"url": u, "name": name, "bouts": [dataclasses.asdict(b) for b in bouts]}, default=encode) + "\n")
            fh.flush()
            for b in bouts:
                if b.event.upper().startswith("UFC") and b.opponent_url not in queued:
                    queued.add(b.opponent_url)
                    queue.append(b.opponent_url)
            if len(seen) % 100 == 0:
                print(f"  {len(seen)} pages, {len(queue)} queued", flush=True)
elif args.source == "statsfight":
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
