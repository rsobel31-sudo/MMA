"""My Picks: the pick'em for everyone who opens the page, scored like Claude's AI Picks.

Each player picks every bout they like on the card from the board (`ai_picks/board`): the winner,
the method and, for a finish, the round. Picks are saved on the page in
`players/<id>/picks/<card id>` (writable only by that player):

    {"event": "...", "date": "YYYY-MM-DD", "picks": [{"bout": "A vs B", "winner": "A", "method": "KO/TKO", "round": 1}], "updated": "..."}

Claude grades them after the card with the same scoring as AI Picks (card_picks.score: 2 for the
winner, 1 for the method, a bonus point for the round) and the same two-source results, and publishes
`standings/picks-<id>` and `standings/picks-leaderboard`. A card's picks count only if the document was
saved before the card locked (the database's own update time). Claude is on the leaderboard too, and each
player's record shows how Claude did on the same bouts, so the comparison is like for like.

    python -m mma_predictor card-picks league --players .cache/players_picks   # -> .cache/pickem_sync/*.json
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from . import card_picks as C
from .league import load_boards, parse_player_export
from .picks_cli import _pair
from .sources.wikipedia import match_key

LEAGUE_RESULTS = Path("data/ai_picks/results")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _same(x: str, y: str) -> bool:
    return bool(x) and bool(y) and match_key(x).split()[-1:] == match_key(y).split()[-1:]


def load_results(cards: Optional[List[Dict]] = None, folder: Path = LEAGUE_RESULTS) -> Dict[str, Dict[frozenset, Dict]]:
    """Graded results by event, then by bout (surname pair): {"winner": name, "method", "round", "round_confirmed"} or {"void": ...}.
    From Claude's AI Picks records first (winner and method agreed on two sources), then the My Bets results files."""
    out: Dict[str, Dict[frozenset, Dict]] = {}
    for rec in cards if cards is not None else C.load_cards():
        ev = out.setdefault(rec["event"], {})
        for b in rec["bouts"]:
            if b.get("result"):
                r = dict(b["result"])
                r["claude_points"] = b.get("claude", {}).get("points")
                ev[_pair(b["a"], b["b"])] = r
    for p in sorted(Path(folder).glob("*.json")) if Path(folder).exists() else []:
        d = json.loads(p.read_text())
        ev = out.setdefault(d["event"], {})
        for bout, r in d["bouts"].items():
            a, b = re.split(r"\s+vs\.?\s+", bout, maxsplit=1)
            key = _pair(a, b)
            if key in ev:
                continue
            if r is None:
                ev[key] = {"void": "did not take place"}
            elif r["winner"] is None:
                ev[key] = {"void": r["method"].lower()}
            else:
                ev[key] = {"winner": a if r["winner"] == "a" else b, "method": r["method"], "round": r["round"]}
    return out


def _locks(boards: Dict[str, List[Dict]]) -> Dict[str, Tuple[str, List[Dict]]]:
    """Each event's lock time and bouts, from the boards players picked from."""
    out = {}
    for ev, bs in boards.items():
        out[ev] = (min(b["locks_at"] for b in bs), bs[-1]["bouts"])
    return out


def score_pick(pick: Dict, bout: Dict, result: Dict) -> Dict[str, object]:
    """One player pick against a graded result, with AI Picks' scoring."""
    rounds = int(bout.get("rounds") or 3)
    rnd = rounds if pick.get("method") == "DEC" else pick.get("round")
    side = "w" if _same(pick.get("winner", ""), result["winner"]) else "l"
    return C.score(side, pick.get("method"), rnd, {"side": "w", "method": result["method"], "round": result["round"],
                                                  "round_confirmed": result.get("round_confirmed", True)})


def standings_for(uid: str, docs: Iterable[Dict], boards: Dict[str, List[Dict]], results: Dict[str, Dict[frozenset, Dict]]) -> Dict:
    """One player's official pick'em record, recomputed from all their pick documents."""
    locks = _locks(boards)
    cards = []
    for raw in docs:
        d = dict(raw.get("data") or raw)
        if isinstance(d.get("picks"), list):  # the page saves a list of {bout, winner, method, round}
            d["picks"] = {p["bout"]: p for p in d["picks"] if isinstance(p, dict) and p.get("bout")}
        saved = str(raw.get("updatedAt") or d.get("updated") or "")
        ev = d.get("event", "")
        lock, bouts = locks.get(ev, ("", []))
        card = {"id": raw.get("id") or d.get("id"), "event": ev, "date": d.get("date", ""), "bouts": [], "points": 0, "possible": 0,
                "claude_points": 0, "graded": 0}
        if not lock:
            card["void_reason"] = "no board for this event"
        elif saved >= lock:
            card["void_reason"] = "saved after the card locked"
        res = results.get(ev, {})
        for bt in bouts:
            p = (d.get("picks") or {}).get(bt["bout"])
            if not p or p.get("winner") not in (bt["a"], bt["b"]) or p.get("method") not in C.METHODS:
                continue
            row = {"bout": bt["bout"], "pick": {"winner": p["winner"], "method": p["method"],
                                                "round": int(bt.get("rounds") or 3) if p["method"] == "DEC" else p.get("round")}}
            r = res.get(_pair(bt["a"], bt["b"]))
            if r and "void" in r:
                row["result"] = {"void": r["void"]}
            elif r and "void_reason" not in card:
                row["result"] = {k: r[k] for k in ("winner", "method", "round")}
                row["score"] = score_pick(p, bt, r)
                card["points"] += row["score"]["points"]
                card["possible"] += C.MAX_POINTS
                card["graded"] += 1
                if r.get("claude_points") is not None:
                    row["claude_points"] = r["claude_points"]
                    card["claude_points"] += r["claude_points"]
            card["bouts"].append(row)
        cards.append(card)
    cards.sort(key=lambda c: c["date"])
    graded = [b for c in cards for b in c["bouts"] if "score" in b]
    tot = lambda k: sum(int(b["score"][k]) for b in graded)  # noqa: E731
    same = [b for b in graded if "claude_points" in b]
    return {"uid": uid, "points": tot("points"), "possible": len(graded) * C.MAX_POINTS, "bouts": len(graded),
            "winners": tot("winner"), "methods": tot("method"), "rounds": tot("round"),
            "vs_claude": {"bouts": len(same), "mine": sum(b["score"]["points"] for b in same), "claude": sum(b["claude_points"] for b in same)},
            "cards": cards, "updated": _now()}


def leaderboard(standings: Iterable[Dict], claude: Optional[Dict]) -> Dict:
    rows = [{k: s[k] for k in ("uid", "points", "bouts", "winners", "methods", "rounds")} | {"vs_claude": s["vs_claude"]} for s in standings if s["bouts"]]
    if claude and claude.get("n"):
        rows.append({"uid": "claude", "points": claude["points"], "bouts": claude["n"], "winners": claude["winners"],
                     "methods": claude["methods"], "rounds": claude.get("rounds", 0)})
    for r in rows:
        r["per_bout"] = round(r["points"] / r["bouts"], 3) if r["bouts"] else 0
    rows.sort(key=lambda r: (-r["points"], -r["per_bout"]))
    return {"rows": rows, "updated": _now(), "scoring": dict(C.POINTS)}


def cmd_league(args) -> int:
    boards = load_boards()
    results = load_results()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    standings = []
    for f in sorted(Path(args.players).glob("*.txt")):
        s = standings_for(f.stem, parse_player_export(f.read_text()), boards, results)
        standings.append(s)
        (out / f"picks-{f.stem}.json").write_text(json.dumps(s, ensure_ascii=False))
        vs = s["vs_claude"]
        print(f"  {f.stem}: {s['points']} pts on {s['bouts']} bouts ({s['winners']} winners, {s['methods']} methods, {s['rounds']} rounds)"
              f" · same bouts: {vs['mine']} vs Claude {vs['claude']}" + "".join(f" · {c['event']}: {c['void_reason']}" for c in s["cards"] if c.get("void_reason")))
    summary = json.loads(C.SUMMARY.read_text())["claude"] if C.SUMMARY.exists() else None
    (out / "picks-leaderboard.json").write_text(json.dumps(leaderboard(standings, summary), ensure_ascii=False))
    print(json.dumps([{"op": "set", "collection": "standings", "doc_id": p.stem, "file_path": str(p.resolve())}
                      for p in sorted(out.glob("picks-*.json"))], indent=1))
    return 0
