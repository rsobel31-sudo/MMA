#!/usr/bin/env python3
"""Fetch a list of Sherdog fighter pages into the page cache.

    python scripts/crawl_urls.py urls.json   # {"name": "https://www.sherdog.com/fighter/..."} or ["url", ...]

Used to complete the records of fighters we only knew as opponents, so their
UFC bouts can be checked against UFCStats. Rebuild afterwards with
`python -m mma_predictor rebuild --data data/sherdog`.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mma_predictor.sources import sherdog  # noqa: E402
from mma_predictor.sources.common import Fetcher  # noqa: E402

data = json.loads(Path(sys.argv[1]).read_text())
urls = list(dict.fromkeys(data.values() if isinstance(data, dict) else data))
f = Fetcher(Path(".cache/pages"), delay=float(sys.argv[2]) if len(sys.argv) > 2 else 2.5)
print(f"{len(urls)} pages", flush=True)
for i, u in enumerate(urls, 1):
    try:
        p = sherdog.parse_fighter(f.get(u), u)
        if i % 25 == 0:
            print(f"  [{i}/{len(urls)}] {p.name}: {len(p.bouts)} bouts", flush=True)
    except Exception as exc:  # keep going
        print(f"  skip {u}: {exc}", flush=True)
print("done", flush=True)
