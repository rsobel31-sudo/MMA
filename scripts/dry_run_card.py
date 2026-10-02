"""Dry run of a whole fight week on a past card, in a scratch folder: nothing real is written.

    python scripts/dry_run_card.py --wiki-url https://en.wikipedia.org/wiki/UFC_Fight_Night_289 \
        --odds-url https://www.bestfightodds.com/events/ufc-vegas-121-4368 --date 2026-09-26 \
        --location "Las Vegas, Nevada, U.S." --out .cache/dry_run

Friday, as of two hours before the lock:
  1. AI Bets: `picks sheet` prices the card, the My Picks board is built from it, and `picks place` records
     stand-in bets (the best-EV moneyline, the best-EV method prop and a two-leg parlay, quarter-Kelly, $1 minimum)
     into a scratch ledger.
  2. AI Picks: `card-picks draft` drafts every bout; stand-in picks follow the model (one winner flipped, to
     exercise an override) and `card-picks lock` locks them.
Sunday:
  3. `picks settle` grades the bets from two sources; a stand-in My Picks player's bets are graded by
     `picks results` + `picks league`.
  4. `card-picks grade` grades the picks and writes the record and lessons.
  5. `picks sync` + `card-picks sync` write the page-database documents, collected into ai_picks.json for a
     local preview of the page (copy it next to app/index.html to see the AI Picks and AI Bets tabs).
Checks at the end: every bout picked and graded or void, the bankroll adds up, and the real data is untouched.
The stand-in bets and picks test the machinery, not Claude's judgment.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mma_predictor import card_picks as C  # noqa: E402
from mma_predictor import league as L  # noqa: E402
from mma_predictor import picks as P  # noqa: E402
from mma_predictor import picks_cli as PC  # noqa: E402
from mma_predictor.cli import DEFAULT_SCOUTING  # noqa: E402

REAL = [Path("data/ai_picks"), Path("data/card_picks")]


def fingerprint() -> str:
    h = hashlib.sha256()
    for root in REAL:
        for p in sorted(root.rglob("*")) if root.exists() else []:
            if p.is_file():
                h.update(str(p).encode())
                h.update(p.read_bytes())
    return h.hexdigest()


def step(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki-url", required=True)
    ap.add_argument("--odds-url", action="append", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--event", default="")
    ap.add_argument("--location", default="")
    ap.add_argument("--data", default="data/verified")
    ap.add_argument("--out", default=".cache/dry_run")
    a = ap.parse_args()
    before = fingerprint()
    out = Path(a.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    # Point every writer at the scratch folder.
    C.DIR, C.SUMMARY, C.ADJUST, C.DRAFT = out / "card_picks", out / "card_picks/summary.json", out / "card_picks/method_adjust.json", out / "card_picks_draft.json"
    L.RESULTS = out / "results"
    L.load_boards = functools.partial(L.load_boards, out / "boards")
    L.load_results = functools.partial(L.load_results, out / "results")
    ledger = out / "ledger.json"
    ledger.write_text(json.dumps({"book": "FanDuel", "start": 100.0, "min_stake": 1.0, "created": "dry run", "weeks": []}))
    common = dict(data=a.data, scouting=str(DEFAULT_SCOUTING), no_external=False, cache=".cache/pages", app_data="app/data.json",
                  aliases="data/name_aliases.json", wiki_url=a.wiki_url, date=a.date, location=a.location, event=a.event)
    failures = []

    step("Friday · AI Bets: price the card")
    sheet_path = out / "sheet.json"
    rc = PC.cmd_sheet(SimpleNamespace(**common, ledger=str(ledger), out=str(sheet_path), top=12, odds_url=a.odds_url, no_board=True))
    if rc:
        print("sheet failed")
        return 1
    sheet = json.loads(sheet_path.read_text())
    lock = sheet["event_starts"]
    as_of = (datetime.fromisoformat(lock) - timedelta(hours=2)).astimezone(timezone.utc).replace(microsecond=0).isoformat()
    print(f"lock {lock} · placing as of {as_of}")
    board = L.board_from_sheet(sheet)
    L.save_board(board, out / "boards")

    step("Friday · AI Bets: place stand-in bets")
    mk = [m for m in sheet["markets"] if m["ev"] > 0]
    ml = [m for m in mk if m["market"][0] == "ml"]
    props = [m for m in mk if m["market"][0] == "method"]
    picks = []
    for m in (ml[:1] + props[:1]):
        picks.append({"legs": [m["id"]], "stake": max(1.0, round(100 * m["kelly"] / 4, 2)), "reasoning": "dry run: best EV of its kind"})
    two = []
    for m in ml:
        if all(m["bout"] != x["bout"] for x in two):
            two.append(m)
        if len(two) == 2:
            break
    if len(two) == 2:
        picks.append({"legs": [m["id"] for m in two], "stake": 1.0, "reasoning": "dry run: two-leg parlay"})
    spec = out / "bets.json"
    spec.write_text(json.dumps({"note": "Dry run: stand-in bets.", "picks": picks}))
    rc = PC.cmd_place(SimpleNamespace(sheet=str(sheet_path), bets=str(spec), ledger=str(ledger), any_date=False, as_of=as_of))
    if rc:
        failures.append("picks place")
    # Late bets must be refused.
    try:
        P.Ledger(ledger).place({"name": "late", "date": a.date}, {}, [], "", event_starts=lock, placed_at=lock)
        failures.append("a bet at the lock time was accepted")
    except ValueError:
        print("late bet refused ✓")

    step("Friday · AI Picks: draft and lock every bout")
    rc = C.cmd_draft(SimpleNamespace(**common, sheet=str(sheet_path)))
    if rc:
        print("draft failed")
        return 1
    draft = json.loads(C.DRAFT.read_text())
    entries = []
    for i, b in enumerate(draft["bouts"]):
        m = b["model"]
        if m:
            w, meth, conf = m["winner"], m["method"], m["p_win"]
            if i == 1:  # one override, to exercise the override tracking
                w = b["b"] if w == b["a"] else b["a"]
                meth, conf = "DEC", 0.52
        else:
            w, meth, conf = b["a"], "DEC", 0.5
        entries.append({"bout": b["bout"], "winner": w, "method": meth, "confidence": round(min(0.99, max(0.5, conf)), 2), "why": "dry run"})
    pf = out / "picks.json"
    pf.write_text(json.dumps({"note": "Dry run: stand-in picks (the model's, one flipped).", "picks": entries[:-1]}))
    rc = C.cmd_lock(SimpleNamespace(draft=str(C.DRAFT), picks=str(pf), as_of=as_of))
    if rc == 0:
        failures.append("lock accepted a card with a bout missing")
    else:
        print("missing bout refused ✓")
    pf.write_text(json.dumps({"note": "Dry run: stand-in picks (the model's, one flipped).", "picks": entries}))
    if C.cmd_lock(SimpleNamespace(draft=str(C.DRAFT), picks=str(pf), as_of=as_of)):
        failures.append("card-picks lock")
    if C.cmd_lock(SimpleNamespace(draft=str(C.DRAFT), picks=str(pf), as_of=lock)) == 0:
        failures.append("lock accepted picks at the lock time")
    else:
        print("late picks refused ✓")

    step("Friday · My Picks: a stand-in player bets the board")
    first = next(m for m in board["markets"] if m["market"][0] == "ml")
    player = out / "players"
    player.mkdir()
    bet = {"event": board["event"], "placed_at": as_of, "board_fetched_at": board["fetched_at"], "stake": 10, "odds": first["odds"],
           "legs": [{k: first[k] for k in ("id", "bout", "market", "selection", "odds")}]}
    late = dict(bet, stake=5)
    (player / "u_dryrun.txt").write_text(json.dumps({"id": "b1", "data": bet, "version": 1, "updatedAt": as_of}) + "\n"
                                         + json.dumps({"id": "b2", "data": late, "version": 1, "updatedAt": lock}) + "\n")

    step("Sunday · AI Bets: settle from two sources")
    rc = PC.cmd_settle(SimpleNamespace(ledger=str(ledger), cache=".cache/pages", force=False))
    print(f"settle exit {rc}")
    if rc == 2:
        failures.append("some bets still waiting on results")

    step("Sunday · My Picks: results and standings")
    PC.cmd_results(SimpleNamespace(ledger=str(ledger), cache=".cache/pages", force=False))
    PC.cmd_league(SimpleNamespace(ledger=str(ledger), cache=".cache/pages", players=str(player), out=str(out / "league")))
    st = json.loads((out / "league/u_dryrun.json").read_text())
    reasons = [b.get("void_reason") for b in st["bets"]]
    if "saved after the card locked" not in reasons:
        failures.append("a player bet saved after the lock wasn't voided")

    step("Sunday · AI Picks: grade")
    C.cmd_grade(SimpleNamespace(cache=".cache/pages", force=False))
    rec = C.load_cards()[0]
    ungraded = [b["bout"] for b in rec["bouts"] if "result" not in b]
    if ungraded:
        failures.append("ungraded bouts: " + "; ".join(ungraded))

    # Independent check of the graded results: the card recap (built from the backtest's own results data).
    from mma_predictor.sources.wikipedia import match_key
    recap = next((e for e in json.loads(Path("app/data.json").read_text()).get("recaps", {}).get("events", []) if e["date"] == a.date), None)
    if recap:
        last = lambda n: match_key(n).split()[-1]  # noqa: E731
        by = {frozenset((last(x["a"]), last(x["b"]))): x for x in recap["bouts"]}
        checked = 0
        for b in rec["bouts"]:
            x = by.get(frozenset((last(b["a"]), last(b["b"]))))
            r = b.get("result", {})
            if not x or "void" in r:
                continue
            checked += 1
            # Same conventions as the grader: a DQ counts as KO/TKO (FanDuel's rule), any decision is DEC; names in either order.
            meth = {"DQ": "KO/TKO", "S-DEC": "DEC", "M-DEC": "DEC", "U-DEC": "DEC"}.get(x["method"], x["method"])
            if set(match_key(x["winner"]).split()) != set(match_key(r["winner"]).split()) or meth != r["method"]:
                failures.append(f"{b['bout']}: graded {r['winner']} by {r['method']}, recap says {x['winner']} by {x['method']}")
        print(f"results cross-checked against the card recap: {checked} bouts")
    else:
        print("no card recap for this date to cross-check against")

    step("Both days · page documents")
    PC.cmd_sync(SimpleNamespace(ledger=str(ledger), out=str(out / "ai_picks_sync")))
    C.cmd_sync(SimpleNamespace(out=str(out / "card_picks_sync")))
    docs = [dict(json.loads(p.read_text()), _id=p.stem) for d in ("ai_picks_sync", "card_picks_sync") for p in sorted((out / d).glob("*.json"))]
    (out / "ai_picks.json").write_text(json.dumps(docs, ensure_ascii=False))

    step("Checks")
    led = P.Ledger(ledger)
    s = led.summary()
    profit = round(sum(b["profit"] for b in led.bets()), 2)
    if abs(s["bankroll"] - (100 + profit)) > 0.005:
        failures.append(f"bankroll {s['bankroll']} != 100 + profit {profit}")
    if any(b["status"] == "open" for b in led.bets()):
        failures.append("bets left open")
    after = fingerprint()
    if after != before:
        failures.append("real data under data/ai_picks or data/card_picks changed")
    S = json.loads(C.SUMMARY.read_text())
    print(f"AI Bets: {s['won']}-{s['lost']} ({s['void']} void), bankroll ${s['bankroll']:.2f}")
    for b in led.bets():
        print(f"  {b['status']:<5} ${b['profit']:+6.2f}  ${b['stake']:.2f} @ {b['odds']:+d}  {' + '.join(l['selection'] + ' [' + l.get('grade', '?') + ']' for l in b['legs'])}")
    print(f"AI Picks: Claude {S['claude']['points']} pts ({S['claude']['winners']}/{S['claude']['n']} winners, {S['claude']['methods']} methods) · "
          f"model {S['model']['points']} pts · favourite {S['market']['winners']}/{S['market']['n']} · voids {sum(1 for b in rec['bouts'] if 'void' in b.get('result', {}))}")
    print(f"My Picks player: bankroll ${st['bankroll']:.2f}, bets {[(b['status'], b.get('void_reason')) for b in st['bets']]}")
    print(f"Page documents: {len(docs)} -> {out / 'ai_picks.json'}")
    print("\nRESULT: " + ("all checks passed" if not failures else "FAILED:\n  - " + "\n  - ".join(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
