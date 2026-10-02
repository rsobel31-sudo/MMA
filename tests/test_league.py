"""My Picks: players' bets are validated and graded like Claude's."""

from mma_predictor import picks as P
from mma_predictor.league import board_from_sheet, leaderboard, parse_player_export, standings_for

SHEET = {
    "event": "UFC 999", "date": "2026-10-03", "event_starts": "2026-10-03T12:00:00+00:00", "fetched_at": "2026-10-02T16:00:00+00:00",
    "bouts": [{"bout": "A vs B", "a": "A", "b": "B", "rounds": 3}, {"bout": "C vs D", "a": "C", "b": "D", "rounds": 3}],
    "markets": [
        {"id": "1:ml:a", "bout": "A vs B", "market": ["ml", "a"], "selection": "A to win", "odds": -200, "p_fanduel": 0.64, "p": 0.7},
        {"id": "1:ml:b", "bout": "A vs B", "market": ["ml", "b"], "selection": "B to win", "odds": 170, "p_fanduel": 0.36, "p": 0.3},
        {"id": "2:ml:a", "bout": "C vs D", "market": ["ml", "a"], "selection": "C to win", "odds": 150, "p_fanduel": 0.38, "p": 0.45},
        {"id": "1:distance:True", "bout": "A vs B", "market": ["distance", True], "selection": "Goes to decision", "odds": -120, "p_fanduel": 0.52, "p": 0.5},
    ],
}


def leg(mid, odds=None):
    m = next(x for x in SHEET["markets"] if x["id"] == mid)
    return {"id": mid, "bout": m["bout"], "market": m["market"], "selection": m["selection"], "odds": odds if odds is not None else m["odds"]}


def bet(i, legs, stake, saved="2026-10-02T20:00:00+00:00"):
    return {"id": f"b{i}", "updatedAt": saved, "data": {"event": "UFC 999", "placed_at": saved, "legs": legs, "stake": stake}}


def test_board_hides_claudes_numbers():
    b = board_from_sheet(SHEET)
    assert b["locks_at"] == "2026-10-03T12:00:00+00:00"
    assert all("p" not in m for m in b["markets"]) and b["markets"][0]["p_fanduel"] == 0.64


def test_player_standings_rules_and_grading():
    boards = {"UFC 999": [board_from_sheet(SHEET)]}
    results = {"UFC 999": {"A vs B": P.Result("a", "DEC", 3, 300), "C vs D": P.Result("b", "KO/TKO", 1, 30)}}
    bets = [
        bet(1, [leg("1:ml:a")], 20),                                   # won +10
        bet(2, [leg("2:ml:a")], 10),                                   # lost -10
        bet(3, [leg("1:ml:a"), leg("2:ml:a")], 5),                     # parlay lost -5
        bet(4, [leg("1:ml:b", odds=900)], 5),                          # fake price -> void
        bet(5, [leg("1:ml:a")], 5, saved="2026-10-03T23:00:00+00:00"),  # after lock -> void
        bet(6, [leg("1:ml:a"), leg("1:distance:True")], 5),            # same bout twice -> void
        bet(7, [leg("1:distance:True")], 70),                          # 100 - 35 staked = 65 left -> void
        bet(8, [leg("1:distance:True")], 0.5),                         # under minimum -> void
    ]
    s = standings_for("u_1", bets, boards, results)
    st = {b["id"]: (b["status"], b.get("void_reason", "")) for b in s["bets"]}
    assert st["b1"][0] == "won" and st["b2"][0] == "lost" and st["b3"][0] == "lost"
    assert "price" in st["b4"][1] and "locked" in st["b5"][1] and "bout" in st["b6"][1]
    assert "bankroll" in st["b7"][1] and "minimum" in st["b8"][1]
    assert s["bankroll"] == 100 + 10 - 10 - 5 and s["won"] == 1 and s["lost"] == 2 and s["void"] == 5


def test_open_bets_hold_bankroll_until_results():
    boards = {"UFC 999": [board_from_sheet(SHEET)]}
    s = standings_for("u_2", [bet(1, [leg("2:ml:a")], 40)], boards, {})
    assert s["bets"][0]["status"] == "open" and s["available"] == 60 and s["bankroll"] == 100
    lb = leaderboard([s], {"bankroll": 100, "start": 100, "won": 0, "lost": 0, "staked": 0})
    assert {r["uid"] for r in lb["rows"]} == {"u_2", "claude"}


def test_parse_inline_listing():
    text = 'header\n=== BEGIN ===\n{"id":"b1","data":{"stake":5},"version":1,"updatedAt":"2026-10-02T20:00:00Z"}\n=== END ===\n'
    assert parse_player_export(text)[0]["updatedAt"] == "2026-10-02T20:00:00Z"


def test_bet_saved_exactly_at_the_lock_is_void():
    # Same rule as AI Bets: betting closes when the card starts (found by scripts/dry_run_card.py).
    boards = {"UFC 999": [board_from_sheet(SHEET)]}
    s = standings_for("u_3", [bet(1, [leg("1:ml:a")], 5, saved=SHEET["event_starts"])], boards, {})
    assert s["bets"][0]["status"] == "void" and "locked" in s["bets"][0]["void_reason"]
