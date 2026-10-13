import json

from mma_predictor import rank_moves as R


def _data(order, through="2026-10-10"):
    fs = [{"name": n, "weight_class_source": "ufc-roster", "proven": 2000 - i * 10, "fights": 5, "division": "Lightweight"}
          for i, n in enumerate(order)]
    fs.append({"name": "Not Roster", "weight_class_source": "sherdog", "proven": 3000, "fights": 5, "division": "Lightweight"})
    return {"fighters": fs, "meta": {"last_fight": through}}


def test_baseline_then_monthly_movement(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "SNAPS", tmp_path / "snaps")
    monkeypatch.setattr(R, "APP", tmp_path / "rank_moves.json")
    R.snapshot(_data(["A", "B", "C"]), "2026-10-13")
    assert R.build()["tracking"] is False
    R.snapshot(_data(["B", "A", "C", "D"]), "2026-10-18")
    out = R.build()
    rows = {r["name"]: r for r in out["divisions"]["Lightweight"]["rows"]}
    assert out["from"] == "2026-10-13" and rows["B"]["change"] == 1 and rows["A"]["change"] == -1
    assert rows["D"]["was"] is None and "Not Roster" not in rows
    # Next month: compared with October's last snapshot; October goes into the history.
    R.snapshot(_data(["C", "B", "A", "D"]), "2026-11-08")
    out = R.build()
    rows = {r["name"]: r for r in out["divisions"]["Lightweight"]["rows"]}
    assert out["month"] == "2026-11" and out["from"] == "2026-10-18" and rows["C"]["change"] == 2
    assert out["history"][0]["month"] == "2026-10" and out["history"][0]["biggest"][0]["change"] in (1, -1)
    assert json.loads((tmp_path / "rank_moves.json").read_text())["latest"] == "2026-11-08"
