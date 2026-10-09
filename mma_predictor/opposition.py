"""Opposition quality for fighter profiles: each fighter's recent opponents, ranked against every opponent faced
in a major promotion (our regional rating, the opponent's rating going into the fight). Writes app/opponents.json.

A percentile of 80 means the opponent was rated higher, going in, than 80% of all opponents faced in the majors
since 2008. Opponents with no rated bouts before the fight are left unranked.

    python -m mma_predictor.opposition
"""
from __future__ import annotations

import bisect
import csv
import json
from datetime import date
from pathlib import Path
from typing import Dict, List

from . import prospects as PR
from . import regional as R
from .minor_leagues import brand

OUT = Path("app/opponents.json")
KEEP = 10


def build() -> dict:
    recs = R.load_records()
    rows = R.pre_fight_ratings(R.all_bouts(recs))
    pool = sorted(r for b, ra, rb, na, nb in rows if PR.is_major(b.event) and b.day >= date(2008, 1, 1) and na and nb for r in (ra, rb))
    pct = lambda r: round(100 * bisect.bisect_left(pool, r) / len(pool))
    names: Dict[str, str] = {}
    by_name: Dict[str, List[str]] = {}
    for r in csv.DictReader(Path("data/sherdog/fighters.csv").open(encoding="utf-8")):
        if r.get("url"):
            names[r["url"]] = r["name"]
            by_name.setdefault(r["name"], []).append(r["url"])
    names.update({u: r["name"] for u, r in recs.items()})
    want: Dict[str, str] = {}  # sherdog url -> display key
    data = json.loads(Path("app/data.json").read_text())
    for f in data["fighters"]:
        us = by_name.get(f["name"], [])
        if len(us) == 1:
            want[us[0]] = f["name"]
    pros = json.loads(Path("app/prospects.json").read_text())["prospects"] if Path("app/prospects.json").exists() else []
    for p in pros:
        if p.get("sherdog_url"):
            want.setdefault(p["sherdog_url"], p["name"])
    hist: Dict[str, list] = {}
    for b, ra, rb, na, nb in rows:
        for me, op, r_op, n_op, s in ((b.a, b.b, rb, nb, b.score_a), (b.b, b.a, ra, na, 1 - b.score_a)):
            if me in want:
                slug = op.rstrip("/").rsplit("/", 1)[-1].rsplit("-", 1)[0].replace("-", " ")
                res = "W" if s == 1.0 else "L" if s == 0.0 else "D"
                prom = R.promotion(b.event)
                hist.setdefault(me, []).append([b.day.isoformat(), names.get(op, slug), res, pct(r_op) if n_op else None,
                                                brand(prom) if PR.is_major(b.event) else prom, PR.is_major(b.event)])
    out = {}
    for url, key in want.items():
        h = hist.get(url)
        if not h:
            continue
        ranked = [x for x in h if x[3] is not None]
        major = [x[3] for x in ranked if x[5]]
        last5 = [x[3] for x in ranked[-5:]]
        wins = [x for x in ranked if x[2] == "W"]
        best = max(wins, key=lambda x: x[3]) if wins else None
        out[key] = {"last": [x[:5] for x in h[-KEEP:]][::-1],
                    "avg5": round(sum(last5) / len(last5)) if last5 else None,
                    "major_avg": round(sum(major) / len(major)) if major else None, "major_n": len(major),
                    "best_win": best[:5] if best else None}
    return {"built": date.today().isoformat(), "fighters": out}


def main() -> int:
    d = build()
    OUT.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote {OUT} ({len(d['fighters'])} fighters, {OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
