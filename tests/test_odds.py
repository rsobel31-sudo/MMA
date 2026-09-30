import json
from datetime import date
from pathlib import Path

from mma_predictor.data import Fight, Method
from mma_predictor.odds import link, load_lines
from mma_predictor.sources import bestfightodds as bfo

FIX = Path(__file__).resolve().parent / "fixtures"


def test_fighter_page_lines_and_movement():
    bouts = bfo.parse_fighter((FIX / "bestfightodds_fighter.html").read_text(encoding="utf-8"), "u")
    b = bouts[1]
    assert (b.date, b.event, b.fighter, b.opponent) == (date(2026, 4, 9), "EFC 132", "Adama Diop", "Matunga Djikasa")
    assert (b.fighter_line.open, b.fighter_line.close_lo, b.fighter_line.close_hi) == (115, -450, -225)
    assert b.opponent_line.open == -155 and b.movement[0] == 2.15


def test_odds_maths():
    assert abs(bfo.implied(-200) - 2 / 3) < 1e-9 and abs(bfo.implied(200) - 1 / 3) < 1e-9
    assert abs(bfo.fair_pair(-110, -110) - 0.5) < 1e-9
    # The middle of a closing range, in probability terms.
    assert bfo.closing(bfo.Line(None, -200, -200)) == -200
    assert bfo.closing(bfo.Line(None, 150, 150)) == 150


def test_lines_link_to_our_bouts_and_both_pages_are_compared(tmp_path):
    page = lambda me, them, ml, tl, mv: {"url": me, "bouts": [{  # noqa: E731
        "date": "2024-03-02", "event": "UFC 299", "fighter": me.split("/")[-1], "fighter_url": me,
        "opponent": them.split("/")[-1], "opponent_url": them,
        "fighter_line": ml, "opponent_line": tl, "movement": mv}]}
    a, b = "https://x/fighters/Ann Lee", "https://x/fighters/Bea Kim"
    la = {"open": -120, "close_lo": -180, "close_hi": -160}
    lb = {"open": 100, "close_lo": 140, "close_hi": 150}
    path = tmp_path / "bfo.jsonl"
    path.write_text("\n".join(json.dumps(x) for x in (page(a, b, la, lb, [1.8, 1.6]), page(b, a, lb, la, []))))
    ours = [Fight(date(2024, 3, 2), "Bea Kim", "Ann Lee", "Ann Lee", Method.DEC, 3, 300)]
    lines, rep = link(ours, load_lines(path))
    ml = lines[id(ours[0])]
    assert rep["matched"] == 1 and rep["both pages"] == 1
    assert ml.a_close > 0 and ml.b_close < 0  # oriented to our corners: Bea Kim is the underdog
    assert ml.p_close < 0.5 and ml.move < 0  # money came in on Ann Lee
    assert ml.movement_a and ml.movement_a[0] > 2  # Bea's price, converted from Ann's series
