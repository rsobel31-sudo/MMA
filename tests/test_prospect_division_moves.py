from datetime import date

from mma_predictor import prospect_report


def test_attach_adds_the_move_within_the_division(monkeypatch):
    base = {"taken": "2026-10-01", "prospects": [
        {"name": "A", "p4p_rank": 24, "div_rank": 6, "division": "Featherweight", "score": 80.0},
        {"name": "B", "p4p_rank": 5, "div_rank": 1, "division": "Lightweight", "score": 85.0}]}
    monkeypatch.setattr(prospect_report, "baseline", lambda today: base)
    monkeypatch.setattr(prospect_report, "REPORTS", prospect_report.REPORTS / "_none_")
    out = {"prospects": [
        {"name": "A", "p4p_rank": 1, "div_rank": 1, "division": "Featherweight", "score": 90.0},
        {"name": "B", "p4p_rank": 7, "div_rank": 2, "division": "Featherweight", "score": 84.0},
        {"name": "C", "p4p_rank": 9, "div_rank": 3, "division": "Featherweight", "score": 83.0}]}
    prospect_report.attach(out, date(2026, 11, 2))
    a, b, c = out["prospects"]
    assert (a["move"]["places"], a["move"]["div_from"], a["move"]["div_places"]) == (23, 6, 5)
    assert b["move"]["places"] == -2 and b["move"]["div_new"] is True  # moved up from lightweight
    assert c["move"] == {"new": True, "since": "2026-10-01"}
