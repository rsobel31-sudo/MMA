"""Prospect movement: monthly ranking snapshots, risers and fallers, and the monthly prospect report.

    python -m mma_predictor prospect-snapshot              # save this month's ranking (the 1st-of-month routine)
    python -m mma_predictor prospect-snapshot --from-git 2af2d39 --month 2026-10   # a past build, from history
    python -m mma_predictor prospect-report                # compare the last two snapshots -> data/prospects/reports/

Every rebuild of the list (`prospects`) marks each prospect's move since the latest snapshot taken before
today: places up or down overall, the score change, or "new" for someone who wasn't listed then. The
monthly report compares this month's snapshot with last month's: the biggest risers and fallers (with the
fights in between that explain them), new entries in the top 100, and who left the list and why (signed
with a major promotion, too old, too many fights, a losing record...). Movement also comes from the field:
a newly swept promotion or a fresh Fight Matrix release moves people without them fighting, and the
report says when a move has no fight behind it.
"""

from __future__ import annotations

import json
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
SNAPS = ROOT / "data" / "prospects" / "snapshots"
REPORTS = ROOT / "data" / "prospects" / "reports"
FIELDS = ("name", "sherdog_url", "p4p_rank", "div_rank", "division", "score", "wins", "losses", "draws", "promotion", "last_fight")


def _key(p: Dict) -> str:
    return p.get("sherdog_url") or p["name"]


def snapshot_rows(data: Dict) -> List[Dict]:
    return [{k: p.get(k) for k in FIELDS} for p in data["prospects"]]


def save_snapshot(data: Dict, month: str, taken: Optional[str] = None, source: str = "app/prospects.json") -> Path:
    SNAPS.mkdir(parents=True, exist_ok=True)
    path = SNAPS / f"{month}.json"
    path.write_text(json.dumps({"month": month, "taken": taken or date.today().isoformat(), "built": data.get("built"),
                                "source": source, "prospects": snapshot_rows(data)}, ensure_ascii=False, indent=0))
    return path


def load_snapshots() -> List[Dict]:
    return [json.loads(p.read_text()) for p in sorted(SNAPS.glob("*.json"))] if SNAPS.exists() else []


def baseline(today: date) -> Optional[Dict]:
    """The latest snapshot taken before today: what each prospect's move is measured against."""
    snaps = [s for s in load_snapshots() if s["taken"] < today.isoformat()]
    return snaps[-1] if snaps else None


def attach(out: Dict, today: date) -> None:
    """Add each prospect's move since the baseline snapshot (in place), and the latest report if there is one."""
    base = baseline(today)
    if base:
        then = {_key(p): p for p in base["prospects"]}
        for p in out["prospects"]:
            b = then.get(_key(p))
            p["move"] = ({"new": True, "since": base["taken"]} if b is None else
                         {"from": b["p4p_rank"], "places": b["p4p_rank"] - p["p4p_rank"], "score": round(p["score"] - b["score"], 1), "since": base["taken"]})
        out["moves_since"] = base["taken"]
    reports = sorted(REPORTS.glob("*.json")) if REPORTS.exists() else []
    if reports:
        out["report"] = json.loads(reports[-1].read_text())


def _fights_between(p: Dict, since: str) -> List[Dict]:
    return [b for b in p.get("recent", []) if b["date"] > since]


def report(prev: Dict, cur: Dict, current: Dict, candidates: List[Dict], n: int = 12) -> Dict:
    """Compare two snapshots. `current` is the full built list (for the fights between); `candidates` explain departures."""
    then = {_key(p): p for p in prev["prospects"]}
    now = {_key(p): p for p in cur["prospects"]}
    full = {_key(p): p for p in current["prospects"]}

    def row(k: str) -> Dict:
        a, b = then.get(k), now[k]
        fights = _fights_between(full.get(k, {}), prev["taken"])
        return {"name": b["name"], "division": b["division"], "promotion": b.get("promotion"), "rank": b["p4p_rank"],
                "from": a["p4p_rank"] if a else None, "places": (a["p4p_rank"] - b["p4p_rank"]) if a else None,
                "score": b["score"], "score_change": round(b["score"] - a["score"], 1) if a else None,
                "record": f"{b['wins']}-{b['losses']}" + (f"-{b['draws']}" if b.get("draws") else ""),
                "fights": [{"date": f["date"], "result": f["result"], "opponent": f["opponent"], "method": f.get("method"), "event": f.get("event")} for f in fights],
                "sherdog_url": b.get("sherdog_url")}

    both = [k for k in now if k in then]
    # Risers and fallers among those near the top now or then (a move from 900 to 700 isn't news).
    near = [k for k in both if min(now[k]["p4p_rank"], then[k]["p4p_rank"]) <= 300]
    moves = sorted(near, key=lambda k: then[k]["p4p_rank"] - now[k]["p4p_rank"], reverse=True)
    risers = [row(k) for k in moves if then[k]["p4p_rank"] > now[k]["p4p_rank"]][:n]
    fallers = [row(k) for k in reversed(moves) if then[k]["p4p_rank"] < now[k]["p4p_rank"]][:n]
    new_top = [row(k) for k in now if now[k]["p4p_rank"] <= 100 and (k not in then or then[k]["p4p_rank"] > 100)]
    new_top.sort(key=lambda r: r["rank"])
    by_url = {(c.get("sherdog") or {}).get("url") or c.get("name"): c for c in candidates}
    signed = {s.get("sherdog_url") or s["name"]: s for s in current.get("signed", [])}
    gone = []
    for k, a in then.items():
        if k in now:
            continue
        why = "no longer in the data"
        if k in signed:
            s = signed[k]
            why = f"signed: {s['promotion']} debut {s['debut']}"
        elif k in by_url and (by_url[k].get("check") or {}).get("issues"):
            why = "; ".join(by_url[k]["check"]["issues"])
        gone.append({"name": a["name"], "division": a["division"], "was": a["p4p_rank"], "why": why})
    gone.sort(key=lambda g: g["was"])
    return {"month": cur["month"], "compared_with": prev["month"], "from": prev["taken"], "to": cur["taken"],
            "counts": {"then": len(then), "now": len(now), "new": sum(1 for k in now if k not in then), "left": len(gone)},
            "risers": risers, "fallers": fallers, "new_top100": new_top, "left": gone[:40], "summary": "",
            "made": datetime.now(timezone.utc).replace(microsecond=0).isoformat()}


def cmd_snapshot(args) -> int:
    month = args.month or date.today().strftime("%Y-%m")
    if args.from_git:
        raw = subprocess.run(["git", "show", f"{args.from_git}:app/prospects.json"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
        data = json.loads(raw)
        when = subprocess.run(["git", "show", "-s", "--format=%cs", args.from_git], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
        path = save_snapshot(data, month, taken=when, source=f"git {args.from_git}:app/prospects.json")
    else:
        data = json.loads((ROOT / "app" / "prospects.json").read_text())
        path = save_snapshot(data, month)
    print(f"{len(data['prospects'])} prospects -> {path}")
    return 0


def cmd_report(args) -> int:
    snaps = load_snapshots()
    if len(snaps) < 2:
        print("Need two monthly snapshots to compare; the first report comes after next month's snapshot.")
        return 1
    prev, cur = snaps[-2], snaps[-1]
    current = json.loads((ROOT / "app" / "prospects.json").read_text())
    cpath = ROOT / "data" / "prospects" / "candidates.jsonl"
    cands = [json.loads(l) for l in cpath.read_text().splitlines() if l.strip()] if cpath.exists() else []
    rep = report(prev, cur, current, cands)
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / f"{cur['month']}.json"
    if path.exists():  # keep a summary already written for this month
        rep["summary"] = json.loads(path.read_text()).get("summary", "")
    path.write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    print(f"{cur['month']} vs {prev['month']}: {rep['counts']['new']} new, {rep['counts']['left']} left -> {path}")
    for label, xs in (("Risers", rep["risers"]), ("Fallers", rep["fallers"])):
        print(label + ":")
        for r in xs[:8]:
            fights = ", ".join(f"{f['result']} vs {f['opponent']}" for f in r["fights"]) or "no fight since"
            print(f"  {r['name']:<26} #{r['from']} -> #{r['rank']} (score {r['score_change']:+}) · {fights}")
    print("Write the month's summary into the report's 'summary' field, then rebuild with `prospects`.")
    return 0


def register(sub) -> None:
    p = sub.add_parser("prospect-snapshot", help="save this month's prospect ranking (for risers/fallers)")
    p.add_argument("--month", default="", help="YYYY-MM (default: this month)")
    p.add_argument("--from-git", default="", help="take it from app/prospects.json at this commit (a past build)")
    p.set_defaults(func=cmd_snapshot)
    p = sub.add_parser("prospect-report", help="the monthly prospect report: risers, fallers, new and departed")
    p.set_defaults(func=cmd_report)
