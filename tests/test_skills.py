from datetime import date

import pytest

from mma_predictor.data import CornerStats, Fight, Method
from mma_predictor.ratings import EloRatings
from mma_predictor.skills import CATEGORIES, SUB_RATINGS, SkillRatings, category_rating

D1, D2 = date(2024, 1, 1), date(2024, 1, 2)


def bout(winner, method, stats_a=None, stats_b=None, end_round=3, end_seconds=300):
    return Fight(D1, "A", "B", winner, method, end_round, end_seconds, stats_a=stats_a, stats_b=stats_b)


def after(fight):
    sk = SkillRatings([fight])
    return sk, sk.before("A", D2), sk.before("B", D2)


def moved(before, after_, cat):
    return category_rating(after_, cat) - category_rating(before, cat)


def test_overall_moves_like_classic_elo_without_stats():
    """With records only, the aggregate moves by exactly the classic Elo amount."""
    for method in (Method.KO, Method.SUB, Method.DEC):
        f = bout("A", method, end_round=1 if method.is_finish else 3, end_seconds=120 if method.is_finish else 300)
        sk = SkillRatings([f])
        classic = EloRatings([f])
        # Stat-free bouts add small finish-based evidence on top of the result.
        gain = sk.overall_before("A", D2) - sk.overall(sk.initial("A"))
        classic_gain = classic.rating_before("A", D2) - 1500
        assert gain > 0
        assert gain == pytest.approx(classic_gain, abs=12)


def test_finish_type_decides_which_category_moves():
    base = SkillRatings([]).initial("A")
    _, ko_a, _ = after(bout("A", Method.KO, end_round=1, end_seconds=90))
    _, sub_a, _ = after(bout("A", Method.SUB, end_round=1, end_seconds=90))
    assert moved(base, ko_a, "striking") > moved(base, ko_a, "grappling")
    assert moved(base, sub_a, "grappling") > moved(base, sub_a, "striking")
    assert ko_a["power"] > ko_a["sub_off"]
    assert sub_a["sub_off"] > sub_a["power"]


def test_takedowns_raise_offence_and_lower_opponent_defence():
    a = CornerStats(sig_landed=30, sig_attempted=70, td_landed=5, td_attempted=6, ctrl_seconds=500)
    b = CornerStats(sig_landed=30, sig_attempted=70, td_landed=0, td_attempted=0)
    _, ra, rb = after(bout(None, Method.DRAW, a, b))  # a draw isolates the stat evidence
    assert ra["td_off"] > 1500 > rb["td_def"]
    assert ra["control"] > 1500 > rb["scramble"]
    assert rb["td_off"] == pytest.approx(1500) and ra["td_def"] == pytest.approx(1500)  # B never shot


def test_ground_and_pound_needs_ground_stats():
    a = CornerStats(sig_landed=40, sig_attempted=80, td_landed=3, td_attempted=4, ctrl_seconds=400, ground_landed=40)
    b = CornerStats(sig_landed=10, sig_attempted=40)
    _, ra, rb = after(bout(None, Method.DRAW, a, b))
    assert ra["gnp"] > 1500 and rb["scramble"] < 1500
    a_no_ground = CornerStats(sig_landed=40, sig_attempted=80, td_landed=3, td_attempted=4, ctrl_seconds=400)
    _, ra2, _ = after(bout(None, Method.DRAW, a_no_ground, b))
    assert ra2["gnp"] == pytest.approx(1500)


def test_updates_are_zero_sum_and_every_key_present():
    a = CornerStats(50, 100, 2, 5, 1, 1, 200, 15)
    b = CornerStats(20, 80, 0, 3, 0, 0, 30, 0)
    sk, ra, rb = after(bout("A", Method.DEC, a, b))
    assert set(ra) == set(SUB_RATINGS)
    total = sum(ra.values()) + sum(rb.values())
    assert total == pytest.approx(2 * 1500 * len(SUB_RATINGS))
    assert set(sk.breakdown(ra)) == set(CATEGORIES) | {"overall"}
