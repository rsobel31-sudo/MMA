from datetime import date

from mma_predictor import prospect_report as pr


def _p(name, rank, score, **kw):
    return {"name": name, "sherdog_url": f"https://www.sherdog.com/fighter/{name}", "p4p_rank": rank, "div_rank": 1,
            "division": "Lightweight", "score": score, "wins": 5, "losses": 0, "draws": 0, **kw}


def test_report_risers_fallers_new_and_left():
    prev = {"month": "2026-10", "taken": "2026-10-01", "prospects": [_p("A", 50, 70), _p("B", 10, 90), _p("C", 120, 60), _p("D", 5, 95)]}
    cur = {"month": "2026-11", "taken": "2026-11-01", "prospects": [_p("A", 20, 80), _p("B", 30, 75), _p("C", 90, 66), _p("E", 40, 77)]}
    current = {"prospects": [_p("A", 20, 80, recent=[{"date": "2026-10-12", "result": "win", "opponent": "X", "method": "KO"}]), _p("B", 30, 75), _p("C", 90, 66), _p("E", 40, 77)],
               "signed": [{"name": "D", "sherdog_url": "https://www.sherdog.com/fighter/D", "promotion": "UFC", "debut": "2026-10-20"}]}
    rep = pr.report(prev, cur, current, [])
    assert [r["name"] for r in rep["risers"]] == ["A", "C"]
    assert rep["risers"][0]["places"] == 30 and rep["risers"][0]["fights"][0]["opponent"] == "X"
    assert [r["name"] for r in rep["fallers"]] == ["B"]
    assert {r["name"] for r in rep["new_top100"]} == {"C", "E"}
    assert rep["left"] == [{"name": "D", "division": "Lightweight", "was": 5, "why": "signed: UFC debut 2026-10-20"}]
    assert rep["counts"] == {"then": 4, "now": 4, "new": 1, "left": 1}


def test_attach_marks_moves_against_snapshot_before_today(tmp_path, monkeypatch):
    monkeypatch.setattr(pr, "SNAPS", tmp_path / "snaps")
    monkeypatch.setattr(pr, "REPORTS", tmp_path / "reports")
    pr.save_snapshot({"prospects": [_p("A", 5, 80), _p("B", 3, 85)]}, "2026-10", taken="2026-10-01")
    pr.save_snapshot({"prospects": [_p("A", 1, 99)]}, "2026-11", taken="2026-11-01")  # taken today: not the baseline yet
    out = {"prospects": [_p("A", 2, 88), _p("B", 3, 85), _p("N", 9, 70)]}
    pr.attach(out, date(2026, 11, 1))
    assert out["moves_since"] == "2026-10-01"
    assert out["prospects"][0]["move"] == {"from": 5, "places": 3, "score": 8.0, "since": "2026-10-01"}
    assert out["prospects"][1]["move"]["places"] == 0
    assert out["prospects"][2]["move"] == {"new": True, "since": "2026-10-01"}
    assert "report" not in out
