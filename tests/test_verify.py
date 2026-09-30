import csv
from datetime import date
from pathlib import Path

from mma_predictor.data import CornerStats, Fight, Method
from mma_predictor.sources import fightmatrix, kaggle_ufc, statsfight
from mma_predictor.verify import match_bouts, name_map, name_score, result_check, stats_check

FIX = Path(__file__).resolve().parent / "fixtures"


def test_fightmatrix_profile_parses_ratings_and_metrics():
    p = fightmatrix.parse_profile((FIX / "fightmatrix_profile.html").read_text(encoding="utf-8"), "u")
    assert p.name == "Justin Gaethje"
    assert p.sherdog_url == "https://www.sherdog.com/fighter/Justin-Gaethje-46648"
    assert p.number("Combat Age") == 45 and abs(p.number("540 Metric") - 0.727) < 1e-9
    b = p.bouts[0]
    assert (b.date, b.opponent, b.result, b.end_round) == (date(2026, 6, 14), "Ilia Topuria", "W", 4)
    assert b.ratings["glicko"] == (2336, 2468) and b.opp_ratings["glicko"] == (2487, 2363)
    assert b.rank == "#4 LW" and b.opp_rank == "#1 LW"


def test_statsfight_bout_parses_result_stats_and_reach():
    r = statsfight.parse_bout((FIX / "statsfight_bout.html").read_text(encoding="utf-8"), "u")
    assert (r["a"], r["b"], r["a_result"], r["method"], r["round"], r["date"]) == (
        "Justin Gaethje", "Paddy Pimblett", "Win", "UD", 5, "2026-01-24")
    assert r["strikes"] == {"a": [180, 264], "b": [173, 345]}
    assert r["takedowns"]["b"] == [0, 6]
    assert r["reach_cm"] == {"a": 178, "b": 185}


def _fight(d, a, b, winner, method=Method.DEC, rnd=3, sa=None, sb=None):
    return Fight(d, a, b, winner, method, rnd, 300, stats_a=sa, stats_b=sb)


def test_bouts_match_across_name_spellings_order_and_a_day():
    base = [_fight(date(2020, 1, 1), "Georges St. Pierre", "B.J. Penn", "Georges St. Pierre")]
    other = [_fight(date(2020, 1, 2), "BJ Penn", "Georges St-Pierre", "Georges St-Pierre"),
             _fight(date(2020, 1, 1), "Someone Else", "Another Person", "Someone Else")]
    ms = match_bouts(base, other)
    assert ms[0].base is base[0] and ms[0].swapped
    assert ms[1].base is None
    assert result_check(ms[0]) == "agree"
    assert name_map(ms) == {"BJ Penn": "B.J. Penn", "Georges St-Pierre": "Georges St. Pierre"}
    assert name_score("Jacare Souza", "Ronaldo Souza") == 1 and name_score("A B", "C D") == 0


def test_result_conflicts_are_detected():
    base = [_fight(date(2020, 1, 1), "Ann Lee", "Bea Kim", "Ann Lee", Method.KO, 1)]
    other = [_fight(date(2020, 1, 1), "Ann Lee", "Bea Kim", "Bea Kim", Method.KO, 1)]
    assert result_check(match_bouts(base, other)[0]) == "winner"
    other = [_fight(date(2020, 1, 1), "Ann Lee", "Bea Kim", "Ann Lee", Method.SUB, 1)]
    assert result_check(match_bouts(base, other)[0]) == "method"


def test_stats_are_disputed_only_when_sources_clearly_disagree():
    s = lambda sig, td: CornerStats(sig_landed=sig, sig_attempted=sig * 2, td_landed=td, td_attempted=td + 1)  # noqa: E731
    f = _fight(date(2020, 1, 1), "Ann Lee", "Bea Kim", "Ann Lee", sa=s(80, 1), sb=s(40, 0))
    agree = {"strikes": {"a": [150, 300], "b": [90, 250]}, "takedowns": {"a": [2, 3], "b": [0, 1]}}
    assert stats_check(f, agree, False).verdict == "agree"
    flipped = {"strikes": {"a": [50, 300], "b": [150, 250]}, "takedowns": {"a": [1, 3], "b": [0, 1]}}
    assert stats_check(f, flipped, False).verdict == "disputed"
    assert stats_check(f, flipped, True).verdict == "agree"  # same record with corners swapped


def test_kaggle_conversion(tmp_path):
    master = ["fight_id,event_id,event_name,event_date,weight_class,title_fight,winner_id,result_status,method,finish_round,"
              "finish_time,time_format,r_fighter_id,r_fighter_name,b_fighter_id,b_fighter_name," +
              ",".join(f"{p}_total_{k}" for p in "rb" for k in ("sig_landed", "sig_atmp", "td_success", "td_atmp", "sub_att", "kd",
                                                                   "ctrl_seconds", "sig_str_landed_ground")),
              "f1,e1,UFC 1,2020-01-01,Lightweight,0,x,win,Could Not Continue,2,1:00,3 Rnd (5-5-5),x,Ann Lee,y,Bea Kim," +
              "10,20,1,2,0,1,60,5,8,30,0,1,1,0,10,0"]
    (tmp_path / "master.csv").write_text("\n".join(master) + "\n")
    (tmp_path / "fighter.csv").write_text("fighter_id,fighter_name,height,reach_inches,stance,dob\nx,Ann Lee,\"5' 10\"\"\",70,Orthodox,1990-01-01\n")
    fighters, fights = kaggle_ufc.convert(tmp_path)
    assert fighters[0]["height_cm"] == "177.8" and fighters[0]["reach_cm"] == "177.8"
    f = fights[0]
    assert f["winner"] == "Ann Lee" and f["method"] == "TKO - Could Not Continue" and f["scheduled_rounds"] == "3"
    assert (f["a_sig_landed"], f["a_knockdowns"], f["b_ctrl_seconds"], f["a_ground_landed"]) == ("10", "1", "10", "5")
