from datetime import date

import pytest

from mma_predictor.data import CornerStats, Fight, Method
from mma_predictor.ratings import EloConfig, EloRatings
from mma_predictor.skills import CATEGORIES, SUB_RATINGS, SkillConfig, SkillRatings, category_rating

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
        classic = EloRatings([f], config=EloConfig(k=SkillConfig().k_result))
        # Stat-free bouts add small finish-based evidence on top of the result.
        gain = sk.overall_before("A", D2) - sk.overall(sk.initial("A"))
        # A debut rating is uncertain, so it moves faster than classic Elo by the RD factor.
        classic_gain = (classic.rating_before("A", D2) - 1500) * sk._rd_k(sk.rd_initial("A"))
        assert gain > 0
        assert gain == pytest.approx(classic_gain, abs=20)


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


def test_every_key_present():
    a = CornerStats(50, 100, 2, 5, 1, 1, 200, 15)
    b = CornerStats(20, 80, 0, 3, 0, 0, 30, 0)
    sk, ra, rb = after(bout("A", Method.DEC, a, b))
    assert set(ra) == set(SUB_RATINGS)
    assert set(sk.breakdown(ra)) == set(CATEGORIES) | {"overall"}


def survive_gain(opponent_sub_off: float) -> float:
    """Submission-defence gain for B after surviving a full fight with A (A wins on points)."""
    f = Fight(D1, "A", "B", "A", Method.DEC, 3, 300)
    sk = SkillRatings([f], pedigree={"A": {"sub_off": opponent_sub_off}})
    return sk.before("B", D2)["sub_def"] - sk.initial("B")["sub_def"]


def test_surviving_an_elite_grappler_counts_more():
    # B loses the decision either way, but going the distance with an elite
    # submission grappler leaves B's submission defence far higher.
    elite, average = survive_gain(400), survive_gain(0)
    assert elite - average > 15


def test_not_finishing_costs_the_attacker_less_than_it_earns_the_defender():
    f = Fight(D1, "A", "B", None, Method.DRAW, 3, 300)  # a draw removes result evidence
    sk = SkillRatings([f], pedigree={"A": {"sub_off": 300}})
    lost = sk.initial("A")["sub_off"] - (sk.before("A", D2)["sub_off"] - sk.pedigree("A", 1)["sub_off"])
    gained = sk.before("B", D2)["sub_def"] - sk.initial("B")["sub_def"]
    assert 0 < lost < gained


def test_pedigree_fades_but_persists():
    sk = SkillRatings([], pedigree={"A": {"sub_off": 200}})
    assert sk.pedigree("A", 0)["sub_off"] == pytest.approx(200)
    assert sk.pedigree("A", 10)["sub_off"] == pytest.approx(100)
    assert sk.before("A", D2)["sub_off"] == pytest.approx(1700)


def test_commentary_is_judged_against_expectation():
    from mma_predictor.scouting import FightNote

    def gain(opp_boost: float) -> float:
        f = Fight(D1, "A", "B", None, Method.DRAW, 3, 300)
        note = FightNote(D1, "B", "A", "grappling", 0.0)  # "B held even on the mat"
        sk = SkillRatings([f], pedigree={"A": {k: opp_boost for k in CATEGORIES["grappling"]}}, notes=[note])
        base = SkillRatings([f], pedigree={"A": {k: opp_boost for k in CATEGORIES["grappling"]}})
        return category_rating(sk.before("B", D2), "grappling") - category_rating(base.before("B", D2), "grappling")

    assert gain(300) > gain(0) > -1e-9  # holding even with a great grappler is impressive


def test_regional_debuts_start_lower():
    from mma_predictor.skills import promotion_tier

    assert promotion_tier("UFC 300 - Pereira vs. Hill") == "ufc"
    assert promotion_tier("Bellator 300") == "major"
    assert promotion_tier("Dana White's Contender Series 2023: Week 1") == "feeder"
    assert promotion_tier("Fury FC 80") == "feeder"
    assert promotion_tier("Hoosier Fight Club 12") == "regional"
    f = Fight(D1, "A", "B", "A", Method.DEC, 3, 300, event="Hoosier Fight Club 12")
    assert SkillRatings([f]).initial("B")["td_off"] < 1500


def test_beating_much_weaker_opponents_proves_little():
    """Uncertainty shrinks far less from a mismatch than from an even fight."""
    from mma_predictor.skills import glicko_expected
    even = [Fight(date(2024, 1, i + 1), "A", f"E{i}", "A", Method.DEC, 3, 300) for i in range(5)]
    weak = [Fight(date(2024, 1, i + 1), "B", f"W{i}", "B", Method.DEC, 3, 300) for i in range(5)]
    # Opponents of B are rated far below (a big pedigree gap stands in for a weak record).
    sk = SkillRatings(even + weak, pedigree={f"W{i}": {k: -400 for k in SUB_RATINGS} for i in range(5)})
    assert sk.rd_before("B", date(2024, 2, 1)) > sk.rd_before("A", date(2024, 2, 1)) + 20
    assert glicko_expected(1900, 1500, 50) > 0.9
