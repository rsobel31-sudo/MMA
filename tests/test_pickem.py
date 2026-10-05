from mma_predictor import pickem as K

BOARDS = {"UFC 999: A vs B": [{"event": "UFC 999: A vs B", "date": "2099-01-01", "locks_at": "2099-01-01T22:00:00+00:00",
                               "bouts": [{"bout": "Ann Ace vs Bea Bold", "a": "Ann Ace", "b": "Bea Bold", "rounds": 3},
                                         {"bout": "Cy Cole vs Di Dunn", "a": "Cy Cole", "b": "Di Dunn", "rounds": 5},
                                         {"bout": "Ed Eel vs Fi Fox", "a": "Ed Eel", "b": "Fi Fox", "rounds": 3}]}]}
CARD = {"event": "UFC 999: A vs B", "date": "2099-01-01", "rounds_picked": True, "bouts": [
    {"bout": "Ann Ace vs Bea Bold", "a": "Ann Ace", "b": "Bea Bold", "result": {"winner": "Bea Bold", "side": "b", "method": "SUB", "round": 2},
     "claude": {"points": 3}},
    {"bout": "Cy Cole vs Di Dunn", "a": "Cy Cole", "b": "Di Dunn", "result": {"winner": "Cy Cole", "side": "a", "method": "DEC", "round": 5},
     "claude": {"points": 4}},
    {"bout": "Ed Eel vs Fi Fox", "a": "Ed Eel", "b": "Fi Fox", "result": {"void": "did not take place"}}]}


def _doc(updated, picks):
    return {"id": "2099-01-01-ufc-999", "updatedAt": updated, "data": {"event": "UFC 999: A vs B", "date": "2099-01-01", "picks": picks}}


def test_scores_like_ai_picks_and_compares_with_claude():
    picks = {"Ann Ace vs Bea Bold": {"winner": "Bea Bold", "method": "SUB", "round": 2},
             "Cy Cole vs Di Dunn": {"winner": "Cy Cole", "method": "DEC"},
             "Ed Eel vs Fi Fox": {"winner": "Fi Fox", "method": "KO/TKO", "round": 1}}
    s = K.standings_for("u1", [_doc("2099-01-01T20:00:00Z", picks)], BOARDS, K.load_results([CARD], folder="nowhere"))
    assert (s["points"], s["bouts"], s["winners"], s["methods"], s["rounds"]) == (8, 2, 2, 2, 2)
    assert s["vs_claude"] == {"bouts": 2, "mine": 8, "claude": 7}
    assert s["cards"][0]["bouts"][2]["result"] == {"void": "did not take place"}
    lb = K.leaderboard([s], {"n": 2, "points": 7, "winners": 2, "methods": 2, "rounds": 1})
    assert [r["uid"] for r in lb["rows"]] == ["u1", "claude"]


def test_wrong_round_and_wrong_winner():
    picks = {"Ann Ace vs Bea Bold": {"winner": "Bea Bold", "method": "SUB", "round": 1},
             "Cy Cole vs Di Dunn": {"winner": "Di Dunn", "method": "DEC"}}
    s = K.standings_for("u1", [_doc("2099-01-01T20:00:00Z", picks)], BOARDS, K.load_results([CARD], folder="nowhere"))
    assert s["points"] == 3 and s["rounds"] == 0


def test_saved_after_lock_counts_nothing():
    picks = {"Ann Ace vs Bea Bold": {"winner": "Bea Bold", "method": "SUB", "round": 2}}
    s = K.standings_for("u1", [_doc("2099-01-01T22:00:00Z", picks)], BOARDS, K.load_results([CARD], folder="nowhere"))
    assert s["points"] == 0 and s["bouts"] == 0 and s["cards"][0]["void_reason"] == "saved after the card locked"


def test_board_lists_the_whole_card_even_unpriced_bouts():
    from mma_predictor.league import board_from_sheet
    sheet = {"event": "E", "date": "2099-01-01", "event_starts": "2099-01-01T22:00:00+00:00", "fetched_at": "x",
             "bouts": [{"bout": "A vs B", "a": "A", "b": "B", "rounds": 3}],
             "card": [{"bout": "A vs B", "a": "A", "b": "B", "rounds": 3, "title": False},
                      {"bout": "C vs D", "a": "C", "b": "D", "rounds": 5, "title": True}],
             "markets": [{"id": "1:ml:a", "bout": "A vs B", "market": ["ml", "a"], "selection": "A to win", "odds": -150, "p_fanduel": 0.58}]}
    board = board_from_sheet(sheet)
    assert [b["bout"] for b in board["bouts"]] == ["A vs B", "C vs D"] and board["bouts"][1]["rounds"] == 5
    assert len(board["markets"]) == 1


def test_reads_picks_saved_as_a_list():
    picks = [{"bout": "Ann Ace vs Bea Bold", "winner": "Bea Bold", "method": "SUB", "round": 2},
             {"bout": "Cy Cole vs Di Dunn", "winner": "Cy Cole", "method": "DEC"}]
    s = K.standings_for("u1", [_doc("2099-01-01T20:00:00Z", picks)], BOARDS, K.load_results([CARD], folder="nowhere"))
    assert s["points"] == 8 and s["bouts"] == 2
