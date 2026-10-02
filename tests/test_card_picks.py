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
    picks = [{"bout": "Ann Ace vs Bea Bold", "winner": "Bea Bold", "method": "SUB", "confidence": 0.55},
             {"bout": "Cy Cole vs Di Dunn", "winner": "Cy Cole", "method": "KO/TKO", "confidence": 0.7}]
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


def test_grade_and_summary():
    rec = C.lock(_draft(), _spec(), now="2098-12-31T00:00:00+00:00")
    assert rec["bouts"][0]["pick"]["side"] == "b"
    C.grade_card(rec, {"Ann Ace vs Bea Bold": Result("b", "SUB", 2, 100), "Cy Cole vs Di Dunn": Result("a", "DEC", 3, 300)})
    assert rec["graded"]
    a, b = rec["bouts"]
    assert a["claude"] == {"winner": True, "method": True, "points": 2}
    assert a["model_score"]["winner"] is False
    assert b["claude"] == {"winner": True, "method": False, "points": 1}
    s = C.summarize([rec])
    assert s["claude"]["points"] == 3 and s["model"]["points"] == 1
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
