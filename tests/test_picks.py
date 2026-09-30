"""AI Picks: FanDuel parsing, grading, parlays and bankroll rules."""

import pytest

from mma_predictor import picks as P

PAGE = """<title>UFC 999 Odds: Test</title><span class="table-header-date">October 4th</span>
<table class="first"></table><table class="odds">
<tr><th scope="col"></th></tr>
<tr id="mu-1"><th scope="row"><a href="/cnadm/matchups/1" class="bfo-admin-link">1</a><a href="/fighters/ann-a-1"><span>Ann Alpha</span></a></th>
 <td class="but-sg" data-li="[22,1,1]"><span id="x">-150</span></td><td class="but-sg" data-li="[21,1,1]"><span id="y">-160</span></td></tr>
<tr><th scope="row"><a href="/fighters/bea-b-2"><span>Bea Beta</span></a></th>
 <td class="but-sg" data-li="[22,2,1]"><span>+130</span></td><td class="but-sg" data-li="[21,2,1]"><span>+135</span></td></tr>
<tr class="pr"><th scope="row">Over 2&#189; rounds</th><td class="but-sgp" data-li="[21,1,1,32,0]"><span>-200</span></td></tr>
<tr class="pr"><th scope="row">Under 2&#189; rounds</th><td class="but-sgp" data-li="[21,2,1,32,0]"><span>+165</span></td></tr>
<tr class="pr"><th scope="row">Alpha wins by submission</th><td class="but-sgp" data-li="[21,1,1,5,0]"><span>+600</span></td></tr>
<tr class="pr"><th scope="row">Fight is a draw</th><td class="but-sgp" data-li="[22,1,1,9,0]"><span>+5000</span></td></tr>
</table>"""


def test_parse_event_keeps_fanduel_only():
    ev = P.parse_event(PAGE, "u")
    assert ev["name"] == "UFC 999" and ev["date_label"] == "October 4th"
    (b,) = ev["bouts"]
    assert (b["a"], b["b"]) == ("Ann Alpha", "Bea Beta")
    assert b["ml"] == {"a": -160, "b": 135}
    assert [p["label"] for p in b["props"]] == ["Over 2½ rounds", "Under 2½ rounds", "Alpha wins by submission"]


def test_canonical_labels_use_surnames():
    a, b = "Ann Alpha", "Bea Beta"
    assert P.canonical("Alpha wins by submission", a, b, 3) == ("method", "a", "SUB")
    assert P.canonical("Beta wins by TKO/KO", a, b, 3) == ("method", "b", "KO/TKO")
    assert P.canonical("Under 2½ rounds", a, b, 3) == ("total", False, 2.5)
    assert P.canonical("Fight won't start round 3", a, b, 3) == ("starts_round", 3, False)
    assert P.canonical("Over 4½ rounds", a, b, 3) is None  # not a 3-round line
    assert P.canonical("Fight is a draw", a, b, 3) is None


def test_grading():
    ko_r2 = P.Result("a", "KO/TKO", 2, 170)  # 7:50 elapsed
    dec = P.Result("b", "DEC", 3, 300)
    assert P.grade_leg(["ml", "a"], ko_r2) == "won"
    assert P.grade_leg(["method", "a", "KO/TKO"], ko_r2) == "won"
    assert P.grade_leg(["method", "a", "SUB"], ko_r2) == "lost"
    assert P.grade_leg(["total", True, 1.5], ko_r2) == "won"   # past 7:30
    assert P.grade_leg(["total", True, 2.5], ko_r2) == "lost"
    assert P.grade_leg(["distance", True], dec) == "won"
    assert P.grade_leg(["starts_round", 3, True], ko_r2) == "lost"
    assert P.grade_leg(["itd", "b"], dec) == "lost"
    assert P.grade_leg(["ml", "a"], P.Result(None, "DRAW", 3, 300)) == "void"
    assert P.grade_leg(["distance", True], P.Result(None, "NC", 1, 30)) == "void"
    assert P.grade_leg(["ml", "a"], None) == "void"  # bout didn't happen


def _sheet():
    return {
        "1:ml:a": {"id": "1:ml:a", "bout": "A vs B", "market": ["ml", "a"], "selection": "A to win", "odds": -200, "p": 0.7, "p_fanduel": 0.64},
        "2:ml:a": {"id": "2:ml:a", "bout": "C vs D", "market": ["ml", "a"], "selection": "C to win", "odds": 150, "p": 0.45, "p_fanduel": 0.38},
        "1:total:True:1.5": {"id": "1:total:True:1.5", "bout": "A vs B", "market": ["total", True, 1.5], "selection": "Over 1.5", "odds": -120, "p": 0.6, "p_fanduel": 0.52},
    }


def test_ledger_place_and_settle(tmp_path):
    led = P.Ledger(tmp_path / "l.json")
    ev = {"name": "UFC 999", "date": "2026-10-03"}
    week = led.place(ev, _sheet(), [
        {"legs": ["1:ml:a"], "stake": 20},
        {"legs": ["1:ml:a", "2:ml:a"], "stake": 10},
    ], "note", event_starts="2026-10-03T12:00:00+00:00", placed_at="2026-10-02T16:00:00+00:00")
    assert week["bets"][1]["kind"] == "parlay"
    assert week["bets"][1]["decimal"] == pytest.approx(1.5 * 2.5)
    assert led.available() == 70
    led.settle(week, {"A vs B": P.Result("a", "DEC", 3, 300), "C vs D": P.Result(None, "NC", 1, 60)}, ["x", "y"])
    single, parlay = week["bets"]
    assert (single["status"], single["profit"]) == ("won", 10.0)
    assert (parlay["status"], parlay["profit"]) == ("won", 5.0)  # the void leg drops out: pays at -200
    assert week["settled"] and led.bankroll() == 115.0


def test_ledger_rules(tmp_path):
    led = P.Ledger(tmp_path / "l.json")
    ev = {"name": "UFC 999", "date": "2026-10-03"}
    with pytest.raises(ValueError, match="exceed"):
        led.place(ev, _sheet(), [{"legs": ["1:ml:a"], "stake": 100.01}], "", placed_at="2026-10-02T00:00:00+00:00")
    with pytest.raises(ValueError, match="same bout"):
        led.place(ev, _sheet(), [{"legs": ["1:ml:a", "1:total:True:1.5"], "stake": 5}], "", placed_at="2026-10-02T00:00:00+00:00")
    with pytest.raises(ValueError, match="sheet"):
        led.place(ev, _sheet(), [{"legs": ["9:ml:a"], "stake": 5}], "", placed_at="2026-10-02T00:00:00+00:00")
    with pytest.raises(ValueError, match="before the event"):
        led.place(ev, _sheet(), [{"legs": ["1:ml:a"], "stake": 5}], "", event_starts="2026-10-03T12:00:00+00:00", placed_at="2026-10-03T13:00:00+00:00")


def test_bust(tmp_path):
    led = P.Ledger(tmp_path / "l.json")
    week = led.place({"name": "UFC 999", "date": "2026-10-03"}, _sheet(), [{"legs": ["2:ml:a"], "stake": 100}], "all in",
                     placed_at="2026-10-02T00:00:00+00:00")
    assert not led.bust()  # money is still on the table
    led.settle(week, {"C vs D": P.Result("b", "SUB", 1, 90)}, [])
    assert led.bankroll() == 0 and led.bust() and led.summary()["bust"]
    with pytest.raises(ValueError):
        led.place({"name": "UFC 1000", "date": "2026-10-10"}, _sheet(), [{"legs": ["1:ml:a"], "stake": 1}], "", placed_at="2026-10-09T00:00:00+00:00")


def test_pass_week_is_recorded(tmp_path):
    led = P.Ledger(tmp_path / "l.json")
    week = led.place({"name": "UFC 999", "date": "2026-10-03"}, _sheet(), [], "Nothing worth it", placed_at="2026-10-02T00:00:00+00:00")
    assert week["settled"] and led.summary()["passes"] == 1


def test_distance_calibration_moves_toward_decisions():
    dist = {"KO/TKO": 0.4, "SUB": 0.2, "DEC": 0.4}
    t = P.Timing({(3, "KO/TKO"): [100, 400, 700], (3, "SUB"): [200, 500]})
    raw = P.model_prob(("distance", True), 0.6, dist, dist, 3, t)
    cal = P.model_prob(("distance", True), 0.6, dist, dist, 3, t, (0.22, 0.67))
    assert raw == pytest.approx(0.4) and cal > raw
    # Method shares still add up once recalibrated.
    tot = sum(P.model_prob(("method", s, m), 0.6, dist, dist, 3, t, (0.22, 0.67)) for s in "ab" for m in ("KO/TKO", "SUB", "DEC"))
    assert tot == pytest.approx(1.0)
