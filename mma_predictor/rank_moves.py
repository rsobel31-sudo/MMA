"""Monthly movement in our UFC division rankings.

Our ranking is the UFC Rankings page's default: current UFC roster fighters with at least one bout, ordered within
each division by the `proven` rating (app/data.json). After every UFC card (the refresh's review step, i.e. the Sunday
sweep) the top 30 of each division are snapshotted to data/rankings/snapshots/<date>.json; the first snapshot is the
baseline. Movement for a month compares the latest snapshot with the last one taken before the month began (the
baseline until there is one), and each finished month is kept as history. The page reads app/rank_moves.json.

    python -m mma_predictor rank-moves            # snapshot now (after a card) and rebuild app/rank_moves.json
    python -m mma_predictor rank-moves --no-snapshot
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
SNAPS = ROOT / "data" / "rankings" / "snapshots"
APP = ROOT / "app" / "rank_moves.json"
DEPTH = 30  # tracked per division, so fighters entering or leaving the top 15 are seen


def current(data: dict) -> Dict[str, List[dict]]:
    """Division -> [{name, rank, proven}], the page's default order."""
    divs: Dict[str, List[dict]] = {}
    for f in data["fighters"]:
        if f.get("weight_class_source") != "ufc-roster" or f.get("proven") is None or (f.get("fights") or 0) < 1:
            continue
        divs.setdefault(f.get("division") or "Unknown", []).append(f)
    out = {}
    for d, fs in divs.items():
        fs.sort(key=lambda f: -f["proven"])
        out[d] = [{"name": f["name"], "rank": i + 1, "proven": round(f["proven"], 1)} for i, f in enumerate(fs[:DEPTH])]
    return out


def snapshot(data: dict, when: Optional[str] = None) -> Path:
    when = when or date.today().isoformat()
    meta = data.get("meta", {})
    snap = {"date": when, "through": meta.get("last_fight"), "divisions": current(data)}
    SNAPS.mkdir(parents=True, exist_ok=True)
    p = SNAPS / f"{when}.json"
    p.write_text(json.dumps(snap, ensure_ascii=False, indent=0) + "\n")
    return p


def _load() -> List[dict]:
    return [json.loads(p.read_text()) for p in sorted(SNAPS.glob("*.json"))]


def diff(old: dict, new: dict, top: int = 15) -> Dict[str, List[dict]]:
    """Per division, the current top `top` with their rank change since `old` (None = new to the tracked list)."""
    out = {}
    for d, rows in new["divisions"].items():
        before = {r["name"]: r for r in old["divisions"].get(d, [])}
        lst = []
        for r in rows[:top]:
            b = before.get(r["name"])
            lst.append({"name": r["name"], "rank": r["rank"], "was": b["rank"] if b else None,
                        "change": (b["rank"] - r["rank"]) if b else None,
                        "proven_change": round(r["proven"] - b["proven"], 1) if b else None})
        now = {r["name"] for r in rows[:top]}
        left = [{"name": n, "was": b["rank"]} for n, b in before.items() if b["rank"] <= top and n not in now]
        out[d] = {"rows": lst, "left": left}
    return out


def build() -> dict:
    snaps = _load()
    if not snaps:
        return {}
    base, last = snaps[0], snaps[-1]
    month = last["date"][:7]
    # The month's starting point: the last snapshot taken before this month began, else the baseline.
    start = next((s for s in reversed(snaps) if s["date"][:7] < month), base)
    out = {"baseline": base["date"], "latest": last["date"], "through": last.get("through"), "month": month,
           "from": start["date"], "tracking": len(snaps) > 1,
           "divisions": diff(start, last) if len(snaps) > 1 else {}, "history": []}
    # Finished months: from the last snapshot before the month to the month's last snapshot.
    months = sorted({s["date"][:7] for s in snaps if s["date"][:7] < month and s is not base})
    for m in months:
        end = [s for s in snaps if s["date"][:7] == m][-1]
        st = next((s for s in reversed(snaps) if s["date"][:7] < m), base)
        if end is st:
            continue
        moves = []
        for d, v in diff(st, end).items():
            for r in v["rows"]:
                if r["change"]:
                    moves.append({"division": d, **r})
        moves.sort(key=lambda r: -abs(r["change"]))
        out["history"].append({"month": m, "from": st["date"], "to": end["date"], "biggest": moves[:12]})
    out["history"].reverse()
    APP.write_text(json.dumps(out, ensure_ascii=False))
    return out


def after_card(data: dict) -> dict:
    """Refresh hook: one snapshot per day, then rebuild the page file."""
    snapshot(data)
    return build()


def cmd_rank_moves(args) -> int:
    data = json.loads((ROOT / "app" / "data.json").read_text())
    if not args.no_snapshot:
        print(f"snapshot: {snapshot(data)}")
    out = build()
    if not out.get("tracking"):
        print(f"Baseline {out.get('baseline')}: movement starts with the next snapshot (after the next card).")
        return 0
    print(f"{out['month']}: {out['from']} -> {out['latest']} (data through {out['through']})")
    for d, v in out["divisions"].items():
        moved = [r for r in v["rows"] if r["change"] or r["was"] is None]
        if moved:
            print(f"  {d}: " + ", ".join(f"{r['name']} {'NEW' if r['was'] is None else ('+' if r['change'] > 0 else '') + str(r['change'])}" for r in moved))
    return 0


def register(sub) -> None:
    p = sub.add_parser("rank-moves", help="monthly movement in our UFC division rankings (snapshot after each card)")
    p.add_argument("--no-snapshot", action="store_true", help="rebuild app/rank_moves.json without a new snapshot")
    p.set_defaults(func=cmd_rank_moves)
