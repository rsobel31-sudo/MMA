"""Backtest the prospect score on the field as it was: Fight Matrix ranking snapshots from past issues.

    python scripts/backtest_prospects.py crawl     # snapshots + profiles (resumable)
    python scripts/backtest_prospects.py analyse   # fit and compare the score's mix

Our own fight data was crawled outward from UFC fighters, so regional fighters who later
made it are over-represented in it; a backtest on it would flatter any score. Fight
Matrix's monthly ranking snapshots list every ranked fighter as of that date, whoever
they became. For each snapshot we keep the ranked fighters who were prospects by our rules
*on that date* (under 28, fewer than 14 pro fights, no major-promotion bout, active in
the last two years), rebuild the score's inputs as of that date from the fighter's Fight
Matrix history, and check what happened in the next four years.
"""

import argparse
import dataclasses
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mma_predictor import prospects as PR  # noqa: E402
from mma_predictor.sources import fightmatrix  # noqa: E402
from mma_predictor.sources.common import Fetcher  # noqa: E402
from mma_predictor.sources.wikipedia import match_key  # noqa: E402

OUT = Path("data/prospects/backtest")
SNAP_URL = "https://www.fightmatrix.com/historical-mma-rankings/ranking-snapshots/?Issue={issue}&Division={div}&Page={page}"
ISSUES = {"2019-01-06": 631, "2021-01-03": 740}  # fit on the first, test on the second
DIVISIONS = {1: "Heavyweight", 2: "Light Heavyweight", 3: "Middleweight", 4: "Welterweight", 5: "Lightweight",
             6: "Featherweight", 7: "Bantamweight", 8: "Flyweight", 15: "Women's Bantamweight",
             14: "Women's Flyweight", 13: "Women's Strawweight", 12: "Women's Atomweight"}
ROW = re.compile(r'class="tdRank(?:Alt)?">(\d+)</td>.*?href="(/fighter-profile/[^"]+)"[^>]*>\s*<strong>([^<]+)</strong>.*?class="tdBar"[^>]*>(\d+)<', re.S)


def parse_snapshot(page: str):
    return [{"rank": int(r), "url": "https://www.fightmatrix.com" + u, "name": n.strip(), "points": int(p)} for r, u, n, p in ROW.findall(page)]


def known_ineligible(cutoff: date) -> set:
    """match_keys our Sherdog data already shows weren't prospects on `cutoff` (saves fetching their profiles)."""
    import csv

    dob = {r["name"]: r["dob"] for r in csv.DictReader(open("data/sherdog/fighters.csv", encoding="utf-8"))}
    n, major = {}, set()
    for r in csv.DictReader(open("data/sherdog/fights.csv", encoding="utf-8")):
        if r["date"] >= cutoff.isoformat():
            continue
        for k in ("fighter_a", "fighter_b"):
            n[r[k]] = n.get(r[k], 0) + 1
            if PR.is_major(r["event"]):
                major.add(r[k])
    out = set()
    for name in set(n) | set(dob):
        age = PR.age_on(dob.get(name) or None, cutoff)
        if name in major or n.get(name, 0) >= PR.MAX_FIGHTS or (age is not None and age >= PR.MAX_AGE):
            out.add(match_key(name))
    return out


def crawl(args) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    f = Fetcher(Path(".cache/pages"), delay=args.delay, user_agent="Mozilla/5.0 (compatible; mma-predictor/0.1; personal research)")
    field = {}
    for when, issue in ISSUES.items():
        path = OUT / f"snapshot_{when}.jsonl"
        if not path.exists():
            rows = []
            for div, label in DIVISIONS.items():
                for page in range(1, args.pages + 1):
                    got = parse_snapshot(f.get(SNAP_URL.format(issue=issue, div=div, page=page), cache=False))
                    if not got:
                        break
                    rows += [dict(r, division=label) for r in got]
                print(f"{when} {label}: {sum(r['division'] == label for r in rows)}", flush=True)
            path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        skip = known_ineligible(date.fromisoformat(when))
        keep = [r for r in rows if match_key(r["name"]) not in skip]
        print(f"{when}: {len(rows)} ranked, {len(keep)} not known to be ineligible", flush=True)
        for r in keep:
            field[r["url"]] = r
    have = {}
    for src in (Path("data/fightmatrix/profiles.jsonl"), OUT / "profiles.jsonl"):
        if src.exists():
            for l in src.read_text(encoding="utf-8").splitlines():
                if l.strip():
                    have[json.loads(l)["url"]] = 1
    todo = [u for u in field if u not in have]
    print(f"{len(field)} fighters in the field, {len(todo)} profiles to fetch", flush=True)
    with (OUT / "profiles.jsonl").open("a", encoding="utf-8") as fh:
        for i, u in enumerate(todo, 1):
            try:
                prof = fightmatrix.parse_profile(f.get(u, cache=False), u)
                fh.write(json.dumps(dataclasses.asdict(prof), default=str, ensure_ascii=False) + "\n")
                fh.flush()
            except Exception as exc:  # noqa: BLE001
                print(f"  {u}: {exc}", flush=True)
            if i % 100 == 0:
                print(f"  {i}/{len(todo)} profiles", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["crawl", "analyse"])
    ap.add_argument("--pages", type=int, default=12, help="snapshot pages (25 fighters) per division")
    ap.add_argument("--delay", type=float, default=1.5)
    args = ap.parse_args()
    if args.stage == "crawl":
        crawl(args)
    else:
        from mma_predictor.prospects_backtest import run

        print(json.dumps(run(OUT), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
