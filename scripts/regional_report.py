"""Our regional rating, all in one run: backtest vs Fight Matrix, early-schedule analysis, today's prospects
compared with Fight Matrix, a fighter's schedule (Anthony Wint by default), and the promotion table for tiering.

    python scripts/regional_report.py            # writes data/regional/report.json
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mma_predictor import prospects as PR  # noqa: E402
from mma_predictor import regional as R  # noqa: E402


def schedule_of(url: str, rows, names) -> list:
    opp = sorted(rb for b, ra, rb, na, nb in rows if PR.is_major(b.event) and na and nb)
    out = []
    for b, ra, rb, na, nb in rows:
        if url not in (b.a, b.b):
            continue
        mine = b.a == url
        o, r_op, r_me = (b.b, rb, ra) if mine else (b.a, ra, rb)
        out.append({"date": b.day.isoformat(), "opponent": names.get(o, o), "opp_rating": round(r_op),
                    "my_rating": round(r_me), "won": b.score_a if mine else 1 - b.score_a, "event": b.event,
                    "major_opp_pct": round(sum(x < r_op for x in opp) / len(opp), 2) if PR.is_major(b.event) else None})
    return out


def main() -> int:
    who = sys.argv[1:] or ["Anthony Wint"]
    rep = {}
    print("backtest ...", flush=True)
    rep["backtest"] = R.backtest(finish_weights=(1.0,), log=lambda *a: None)
    print("schedules ...", flush=True)
    sch = R.schedules(min_later=1)
    rep["schedules"] = {k: v for k, v in sch.items() if k != "starts"}
    print("compare ...", flush=True)
    rep["compare_current"] = R.compare_current(top=20, k_rd=0.0)
    print("promotions ...", flush=True)
    rep["promotions"] = R.promotions()
    recs = R.load_records()
    names = {r["url"]: r["name"] for r in csv.DictReader((ROOT / "data/sherdog/fighters.csv").open(encoding="utf-8")) if r.get("url")}
    names.update({u: r["name"] for u, r in recs.items()})
    rows = R.pre_fight_ratings(R.all_bouts(recs))
    rep["fighters"] = {}
    for n in who:
        for u in [k for k, v in names.items() if v == n]:
            rep["fighters"][n] = schedule_of(u, rows, names)
    rep["records"] = len(recs)
    (ROOT / "data/regional/report.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(f"wrote data/regional/report.json ({len(recs):,} crawled records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
