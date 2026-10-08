"""Crawl the regional fight network behind our prospect candidates, for our own rating of the regional scene.

Stage 1 reads every candidate's Sherdog page (cached copy when we have one) for its opponents' Sherdog links.
Stage 2 fetches each of those opponents' records once. Every record is stored compactly (one JSON line per
fighter: name, birth date, and each bout's date, opponent link, result, method, round and event), in gzipped
shards of 500 fighters under data/regional/, so a checkpoint commit only ever adds files.

Resumable: fighters already stored are skipped, so a stopped run picks up where it left off. Polite: Sherdog's
robots.txt is respected and requests are spaced (--delay). Never fetches member profiles, /search/ or /posts/.

    python scripts/crawl_opponents.py                # both stages
    python scripts/crawl_opponents.py --limit 50     # a short test
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mma_predictor.sources import sherdog  # noqa: E402
from mma_predictor.sources.common import Fetcher  # noqa: E402

OUT = ROOT / "data" / "regional"
SHARD = 500
UA = "Mozilla/5.0 (compatible; mma-predictor/0.1; personal research)"


def record(page) -> dict:
    return {"url": page.url, "name": page.name, "dob": page.dob.isoformat() if page.dob else "",
            "bouts": [{"d": b.date.isoformat(), "o": b.opponent, "u": b.opponent_url or "", "r": b.result,
                       "m": b.method.value if hasattr(b.method, "value") else str(b.method), "rd": b.round, "e": b.event}
                      for b in page.bouts]}


class Store:
    """Fighter records in closed shards (pages-NNNN.jsonl.gz) plus one open shard (open.jsonl)."""

    def __init__(self, out: Path) -> None:
        self.out = out
        out.mkdir(parents=True, exist_ok=True)
        self.open = out / "open.jsonl"
        self.seen = set()
        self.failed = set(json.loads((out / "failed.json").read_text())) if (out / "failed.json").exists() else set()
        for p in sorted(out.glob("pages-*.jsonl.gz")):
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                self.seen.update(json.loads(l)["url"] for l in fh if l.strip())
        if self.open.exists():
            self.seen.update(json.loads(l)["url"] for l in self.open.read_text(encoding="utf-8").splitlines() if l.strip())

    def records(self):
        for p in sorted(self.out.glob("pages-*.jsonl.gz")):
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                yield from (json.loads(l) for l in fh if l.strip())
        if self.open.exists():
            yield from (json.loads(l) for l in self.open.read_text(encoding="utf-8").splitlines() if l.strip())

    def add(self, rec: dict) -> None:
        with self.open.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.seen.add(rec["url"])
        lines = self.open.read_text(encoding="utf-8").splitlines()
        if len(lines) >= SHARD:
            n = len(list(self.out.glob("pages-*.jsonl.gz"))) + 1
            with gzip.open(self.out / f"pages-{n:04d}.jsonl.gz", "wt", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
            self.open.unlink()

    def fail(self, url: str) -> None:
        self.failed.add(url)
        (self.out / "failed.json").write_text(json.dumps(sorted(self.failed), indent=0))


def ok(url: str) -> bool:
    return bool(url) and "/fighter/" in url and not any(x in url for x in ("/search/", "/posts/", "/members/"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--delay", type=float, default=1.6)
    ap.add_argument("--limit", type=int, default=0, help="stop after this many new fetches (testing)")
    ap.add_argument("--cache", default=str(ROOT / ".cache" / "pages"))
    args = ap.parse_args()
    f = Fetcher(Path(args.cache), delay=args.delay, user_agent=UA)
    st = Store(OUT)
    cands = [json.loads(l) for l in (ROOT / "data/prospects/candidates.jsonl").read_text().splitlines() if l.strip()]
    seeds = list(dict.fromkeys(c["sherdog"]["url"] for c in cands if (c.get("sherdog") or {}).get("url")))
    fetched, t0 = 0, time.time()

    def visit(url: str) -> dict | None:
        nonlocal fetched
        if url in st.seen or url in st.failed or not ok(url):
            return None
        try:
            page = sherdog.parse_fighter(f.get(url, cache=False), url)  # a cached copy is used when there is one
        except Exception as exc:  # noqa: BLE001 - a removed or malformed page: note it and move on
            print(f"  skip {url}: {str(exc)[:120]}", flush=True)
            st.fail(url)
            return None
        rec = record(page)
        st.add(rec)
        fetched += 1
        if fetched % 100 == 0:
            rate = fetched / max(1, time.time() - t0) * 3600
            print(f"  {len(st.seen):,} fighters stored ({fetched:,} this run, {rate:,.0f}/hour)", flush=True)
        return rec

    print(f"Stage 1: {len(seeds):,} candidates", flush=True)
    for u in seeds:
        if args.limit and fetched >= args.limit:
            break
        visit(u)
    # One hop: every candidate's opponents. Their own bout lists then carry the opponents-of-opponents' results.
    seedset = set(seeds)
    opps = [b["u"] for rec in st.records() if rec["url"] in seedset for b in rec["bouts"] if ok(b["u"])]
    queue = [u for u in dict.fromkeys(opps) if u not in st.seen and u not in st.failed]
    print(f"Stage 2: {len(queue):,} opponents to fetch", flush=True)
    for u in queue:
        if args.limit and fetched >= args.limit:
            break
        visit(u)
    print(f"Done: {len(st.seen):,} fighters stored, {len(st.failed)} failed", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
