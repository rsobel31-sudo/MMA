import json
from pathlib import Path

import pytest

from mma_predictor import card_picks as C
from mma_predictor.picks import Result


def _draft():
    j = {"a": {"KO/TKO": 0.2, "SUB": 0.1, "DEC": 0.3}, "b": {"KO/TKO": 0.1, "SUB": 0.05, "DEC": 0.25}}
    return {"event": "UFC 999: A vs B", "date": "2099-01-01", "results_url": "", "locks_at": "2099-01-01T22:00:00+00:00",
            "bouts": [{"bout": "Ann Ace vs Bea Bold", "a": "Ann Ace", "b": "Bea Bold", "rounds": 3,
                       "model": {"p_a": 0.6, "winner": "Ann Ace", "method": "DEC", "p_win": 0.6, "joint": j}, "market_p_a": 0.55},
                      {"bout": "Cy Cole vs Di Dunn", "a": "Cy Cole", "b": "Di Dunn", "rounds": 3,
                       "model": {"p_a": 0.7, "winner": "Cy Cole", "method": "KO/TKO", "p_win": 0.7, "joint": j}}]}


def _spec(**over):
    picks = [{"bout": "Ann Ace vs Bea Bold", "winner": "Bea Bold", "method": "SUB", "round": 2, "confidence": 0.55},
             {"bout": "Cy Cole vs Di Dunn", "winner": "Cy Cole", "method": "KO/TKO", "round": 1, "confidence": 0.7}]
    return {"picks": picks, **over}


def test_lock_needs_every_bout_and_valid_fields():
    with pytest.raises(ValueError, match="missing"):
        C.lock(_draft(), {"picks": _spec()["picks"][:1]}, now="2098-12-31T00:00:00+00:00")
    bad = _spec()
    bad["picks"][1]["method"] = "Decision"
    with pytest.raises(ValueError, match="method"):
        C.lock(_draft(), bad, now="2098-12-31T00:00:00+00:00")
    with pytest.raises(ValueError, match="locked"):
        C.lock(_draft(), _spec(), now="2099-01-02T00:00:00+00:00")
    no_round = _spec()
    del no_round["picks"][1]["round"]
    with pytest.raises(ValueError, match="round"):
        C.lock(_draft(), no_round, now="2098-12-31T00:00:00+00:00")
    late = _spec()
    late["picks"][1]["round"] = 4
    with pytest.raises(ValueError, match="round"):
        C.lock(_draft(), late, now="2098-12-31T00:00:00+00:00")
    dec = _spec()
    dec["picks"][1] = {"bout": "Cy Cole vs Di Dunn", "winner": "Cy Cole", "method": "DEC", "confidence": 0.7}
    assert C.lock(_draft(), dec, now="2098-12-31T00:00:00+00:00")["bouts"][1]["pick"]["round"] == 3  # a decision goes the distance


def test_grade_and_summary():
    rec = C.lock(_draft(), _spec(), now="2098-12-31T00:00:00+00:00")
    assert rec["bouts"][0]["pick"]["side"] == "b"
    C.grade_card(rec, {"Ann Ace vs Bea Bold": Result("b", "SUB", 2, 100), "Cy Cole vs Di Dunn": Result("a", "DEC", 3, 300)})
    assert rec["graded"]
    a, b = rec["bouts"]
    assert a["claude"] == {"winner": True, "method": True, "round": True, "points": 4}
    assert a["model_score"]["winner"] is False
    assert b["claude"] == {"winner": True, "method": False, "round": False, "points": 2}
    s = C.summarize([rec])
    assert s["claude"]["points"] == 6 and s["claude"]["rounds"] == 1 and s["claude"]["possible"] == 8
    assert s["model"]["points"] == 2  # the model's draft had no round: winner only on Cole
    assert s["overrides"] == {"n": 1, "claude_right": 1}
    assert s["market"] == {"n": 1, "winners": 0}
    assert s["method_calibration"]["DEC"]["actual"] == 1
    assert any(l["kind"] == "wait" for l in s["lessons"])
    assert C.fit_adjust(s) is None  # far too few bouts to move anything


def test_void_for_draw_and_cancelled():
    rec = C.lock(_draft(), _spec(), now="2098-12-31T00:00:00+00:00")
    C.grade_card(rec, {"Ann Ace vs Bea Bold": Result(None, "DRAW", 3, 300), "Cy Cole vs Di Dunn": None})
    assert all("void" in b["result"] for b in rec["bouts"]) and C.summarize([rec])["bouts"] == 0


def test_method_adjust_keeps_win_chance():
    j = C.joint_methods(0.6, {"KO/TKO": 0.3, "SUB": 0.2, "DEC": 0.5}, {"KO/TKO": 0.4, "SUB": 0.1, "DEC": 0.5}, None, {"KO/TKO": 1.2})
    assert abs(sum(j["a"].values()) - 0.6) < 1e-9 and abs(sum(j["b"].values()) - 0.4) < 1e-9


def test_round_point_needs_method_and_agreeing_sources():
    rec = C.lock(_draft(), _spec(), now="2098-12-31T00:00:00+00:00")
    # Right winner and method, wrong round: 3 points. Sources disagree on the round: no round point.
    C.grade_card(rec, {"Ann Ace vs Bea Bold": Result("b", "SUB", 1, 100), "Cy Cole vs Di Dunn": Result("a", "KO/TKO", 1, 30)},
                 {"Cy Cole vs Di Dunn": False})
    a, b = rec["bouts"]
    assert a["claude"]["points"] == 3 and not a["claude"]["round"]
    assert b["claude"]["points"] == 3 and b["result"]["round_confirmed"] is False


def test_decision_pick_and_rescore_old_cards():
    rec = C.lock(_draft(), _spec(), now="2098-12-31T00:00:00+00:00")
    rec["bouts"][1]["pick"].update(method="DEC", round=3)
    C.grade_card(rec, {"Ann Ace vs Bea Bold": Result("a", "DEC", 3, 300), "Cy Cole vs Di Dunn": Result("a", "DEC", 3, 300)})
    assert rec["bouts"][1]["claude"]["points"] == 4 and rec["bouts"][0]["claude"]["points"] == 0
    # A card from before rounds were picked: winner and method only (3 at most).
    old = C.lock(_draft(), _spec(), now="2098-12-31T00:00:00+00:00")
    for b in old["bouts"]:
        b["pick"].pop("round")
    old["rounds_picked"] = False
    C.grade_card(old, {"Ann Ace vs Bea Bold": Result("b", "SUB", 2, 100), "Cy Cole vs Di Dunn": Result("a", "KO/TKO", 1, 30)})
    assert [b["claude"]["points"] for b in old["bouts"]] == [3, 3]
    assert C.summarize([old])["claude"]["possible"] == 6


def test_round_chances_follow_the_fighters():
    table = {"3": {"KO/TKO": [0.5, 0.3, 0.2], "SUB": [0.5, 0.3, 0.2]}}
    assert C.round_chances(table, 3, "KO/TKO") == [0.5, 0.3, 0.2]
    # A winner who finishes late and a loser who gets finished late pull the chances later.
    late = C.round_chances(table, 3, "KO/TKO", {"wins": [0, 2, 6], "losses": [0, 1, 4]})
    assert late[2] > 0.2 and late[0] < 0.5 and abs(sum(late) - 1) < 1e-9
    assert C.round_chances(table, 5, "DEC") == [0, 0, 0, 0, 1.0]
    assert C.round_chances(None, 5, "SUB") == [0.2] * 5
    # The model's method is untouched; its round is the likeliest for that method.
    m = {"p_a": 0.6, "winner": "A", "method": "KO/TKO", "joint": {"a": {"KO/TKO": 0.3, "SUB": 0.05, "DEC": 0.25}, "b": {}}}
    C.add_model_round(m, 3, table, {"wins": [0, 0, 20], "losses": [0, 0, 10]})
    assert m["method"] == "KO/TKO" and m["round"] == 3
