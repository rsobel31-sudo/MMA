"""My Bets: the same $100 FanDuel game for everyone who opens the page, graded against Claude.

Each player writes their own bets on the page (page database `players/<id>/bets/<bet>`,
writable only by them). Prices come from the board Claude publishes each fight
week (`ai_picks/board`, the FanDuel sheet without Claude's own probabilities).
Claude grades everyone after the card and publishes the official standings
(`standings/<id>` and `standings/leaderboard`, writable only by Claude):

- a bet counts only if it was saved before the card locked (the store's own
  update time when available, else the bet's timestamp), at a price that was on
  one of that week's boards, within the player's bankroll, with at most one leg
  per bout;
- legs are graded from results Wikipedia and Sherdog agree on (picks.grade_leg),
  exactly like Claude's own bets.

Standings are recomputed from every bet each time, so they're deterministic.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from . import picks as P

START = P.START_BANKROLL
BOARDS = Path("data/ai_picks/boards")
RESULTS = Path("data/ai_picks/results")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ------------------------------------------------------------------- board
def board_from_sheet(sheet: Dict[str, object]) -> Dict[str, object]:
    """What players see: FanDuel's prices and no-vig probabilities, never Claude's numbers."""
    # The whole card (My Picks picks every bout); bouts Claude couldn't price simply have no markets for My Bets.
    bouts = [{"bout": b["bout"], "a": b["a"], "b": b["b"], "rounds": b["rounds"], "title": b.get("title", False)} for b in sheet.get("card") or sheet["bouts"]]
    order = {b["bout"]: i for i, b in enumerate(bouts)}
    markets = [{"id": m["id"], "bout": m["bout"], "market": m["market"], "selection": m["selection"], "odds": m["odds"],
                "p_fanduel": m["p_fanduel"]} for m in sheet["markets"]]
    markets.sort(key=lambda m: (order.get(m["bout"], 99), m["market"][0] != "ml", m["id"]))
    return {"event": sheet["event"], "date": sheet["date"], "locks_at": sheet["event_starts"], "fetched_at": sheet["fetched_at"],
            "book": "FanDuel", "odds_url": sheet.get("odds_url", ""), "results_url": sheet.get("results_url", ""),
            "bouts": bouts, "markets": markets}


def save_board(board: Dict[str, object], folder: Path = BOARDS) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    stamp = board["fetched_at"].replace(":", "").replace("-", "")[:15]
    path = folder / f"{board['date']}-{_slug(board['event'])}-{stamp}.json"
    path.write_text(json.dumps(board, indent=1, ensure_ascii=False) + "\n")
    return path


def _slug(s: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def load_boards(folder: Path = BOARDS) -> Dict[str, List[Dict[str, object]]]:
    out: Dict[str, List[Dict[str, object]]] = {}
    for p in sorted(Path(folder).glob("*.json")) if Path(folder).exists() else []:
        b = json.loads(p.read_text())
        out.setdefault(b["event"], []).append(b)
    return out


def load_results(folder: Path = RESULTS) -> Dict[str, Dict[str, Optional[P.Result]]]:
    out: Dict[str, Dict[str, Optional[P.Result]]] = {}
    for p in sorted(Path(folder).glob("*.json")) if Path(folder).exists() else []:
        d = json.loads(p.read_text())
        out[d["event"]] = {k: (None if v is None else P.Result(v["winner"], v["method"], v["round"], v["seconds"])) for k, v in d["bouts"].items()}
    return out


# ------------------------------------------------------------------ grading
def _valid_prices(boards: List[Dict[str, object]]) -> Dict[str, set]:
    prices: Dict[str, set] = {}
    for b in boards:
        for m in b["markets"]:
            prices.setdefault(m["id"], set()).add(int(m["odds"]))
    return prices


def standings_for(uid: str, bets: Iterable[Dict[str, object]], boards: Dict[str, List[Dict[str, object]]],
                  results: Dict[str, Dict[str, Optional[P.Result]]]) -> Dict[str, object]:
    """One player's official record, recomputed from all their bets."""
    rows = []
    for raw in bets:
        d = dict(raw.get("data") or raw)
        d["_id"] = raw.get("id") or d.get("id")
        d["_saved"] = raw.get("updatedAt") or d.get("placed_at") or ""
        rows.append(d)
    events = {ev: min(b["date"] for b in bs) for ev, bs in boards.items()}
    rows.sort(key=lambda d: (events.get(d.get("event"), "9999"), str(d.get("placed_at", ""))))
    bankroll = START
    out_bets, curve = [], [{"week": "Start", "bankroll": START}]
    by_event: Dict[str, List[Dict[str, object]]] = {}
    for d in rows:
        by_event.setdefault(d.get("event", "?"), []).append(d)
    open_stakes = 0.0
    for ev in sorted(by_event, key=lambda e: events.get(e, "9999")):
        bs = boards.get(ev) or []
        locks = min((b["locks_at"] for b in bs), default="")
        prices = _valid_prices(bs)
        res = results.get(ev)
        available = bankroll - open_stakes
        settled_any = False
        for d in by_event[ev]:
            legs = d.get("legs") or []
            stake = round(float(d.get("stake") or 0), 2)
            bet = {"id": d["_id"], "event": ev, "placed_at": d.get("placed_at"), "legs": legs, "stake": stake,
                   "odds": d.get("odds"), "kind": "parlay" if len(legs) > 1 else "single"}
            why = None
            if not bs:
                why = "no board for this event"
            elif locks and str(d["_saved"]) >= locks:  # betting closes when the card starts, as for AI Bets
                why = "saved after the card locked"
            elif stake < P.MIN_STAKE:
                why = f"minimum stake is ${P.MIN_STAKE:.2f}"
            elif not legs or len({l.get("bout") for l in legs}) != len(legs):
                why = "one leg per bout"
            elif any(int(l.get("odds", 0)) not in prices.get(l.get("id"), set()) for l in legs):
                why = "price not on the board"
            elif stake > round(available, 2) + 1e-9:
                why = "stake above the available bankroll"
            if why:
                bet.update(status="void", profit=0.0, void_reason=why)
                out_bets.append(bet)
                continue
            dec = 1.0
            for l in legs:
                dec *= P.decimal(l["odds"])
            bet["decimal"] = round(dec, 4)
            bet["to_win"] = P._money(stake * (dec - 1))
            available -= stake
            if res is None:
                bet.update(status="open", profit=0.0)
                open_stakes += stake
            else:
                gl = []
                for l in legs:
                    r = res.get(l["bout"], "missing")
                    gl.append(dict(l, grade=None if r == "missing" else P.grade_leg(l["market"], r)))
                if any(x["grade"] is None for x in gl):
                    bet.update(legs=gl, status="open", profit=0.0)
                    open_stakes += stake
                else:
                    bet["legs"] = gl
                    bet["status"], bet["profit"] = P.grade_bet({"legs": gl, "stake": stake})
                    bankroll = round(bankroll + bet["profit"], 2)
                    settled_any = True
            out_bets.append(bet)
        if settled_any:
            curve.append({"week": ev, "bankroll": bankroll})
    settled = [b for b in out_bets if b["status"] in ("won", "lost")]
    staked = sum(b["stake"] for b in settled)
    profit = round(sum(b["profit"] for b in settled), 2)
    return {
        "uid": uid, "start": START, "bankroll": round(bankroll, 2), "open_stakes": round(open_stakes, 2),
        "available": round(bankroll - open_stakes, 2), "bust": bankroll - open_stakes < P.MIN_STAKE and open_stakes == 0,
        "won": sum(b["status"] == "won" for b in settled), "lost": sum(b["status"] == "lost" for b in settled),
        "void": sum(b["status"] == "void" for b in out_bets), "staked": round(staked, 2), "profit": profit,
        "roi": round(profit / staked, 4) if staked else None, "bets": out_bets, "curve": curve, "updated": _now(),
    }


def leaderboard(standings: Iterable[Dict[str, object]], claude: Dict[str, object]) -> Dict[str, object]:
    rows = [{k: s[k] for k in ("uid", "bankroll", "profit", "roi", "won", "lost", "staked")} | {"bets": s["won"] + s["lost"]} for s in standings]
    rows.append({"uid": "claude", "bankroll": claude["bankroll"], "profit": round(claude["bankroll"] - claude["start"], 2), "roi": claude.get("roi"),
                 "won": claude.get("won", 0), "lost": claude.get("lost", 0), "staked": claude.get("staked", 0),
                 "bets": claude.get("won", 0) + claude.get("lost", 0)})
    rows.sort(key=lambda r: -r["bankroll"])
    return {"rows": rows, "updated": _now(), "start": START}


def parse_player_export(text: str) -> List[Dict[str, object]]:
    """Documents as ArtifactData prints them inline ({"id","data","version","updatedAt"} per line)."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{") and '"data"' in line:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out
