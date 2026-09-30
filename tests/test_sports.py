import dataclasses
from datetime import date, timedelta

from mma_predictor.adjustments import Adjustments
from mma_predictor.data import Fight, FighterBio, Method
from mma_predictor.history import FightHistory
from mma_predictor.methods import method_distribution
from mma_predictor.sports import sport_of, sport_settings, split_histories


def _league(prefix, gender, ko_every):
    """Twelve fighters in a round robin; every ``ko_every``-th bout ends by KO, the rest by decision."""
    names = [f"{prefix}{i}" for i in range(12)]
    bios = {n: FighterBio(name=n, gender=gender) for n in names}
    fights, d, k = [], date(2015, 1, 1), 0
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            k += 1
            ko = k % ko_every == 0
            fights.append(Fight(d, a, b, a, Method.KO if ko else Method.DEC, 1 if ko else 3, 120 if ko else 300,
                                event="UFC Test"))
            d += timedelta(days=3)
    return bios, fights


def test_each_sport_gets_its_own_base_rates_and_history():
    mb, mf = _league("M", "M", 2)  # half the men's bouts end by KO
    wb, wf = _league("W", "F", 6)  # a sixth of the women's
    bios, fights = {**mb, **wb}, mf + wf
    assert sport_of(wf[0], bios) == "F" and sport_of(mf[0], bios) == "M"
    men, _ = sport_settings(mf, fights)
    women, cfg = sport_settings(wf, fights)
    assert women.method_share["KO/TKO"] < men.method_share["KO/TKO"]
    assert women.method_share["DEC"] > 0.7  # 83% observed, smoothed toward the pooled 49%
    hs = split_histories(bios, fights)
    assert set(hs) == {"M", "F"}
    assert set(hs["F"].names()) == set(wb) and set(hs["M"].names()) == set(mb)
    # Newcomers' method expectations follow their own sport's base rates.
    w = hs["F"].snapshot("W0", date(2015, 1, 1))
    m = hs["M"].snapshot("M0", date(2015, 1, 1))
    assert w.priors.method_share["KO/TKO"] < m.priors.method_share["KO/TKO"]
    assert method_distribution(w, hs["F"].snapshot("W1", date(2015, 1, 1)))["KO/TKO"] < \
        method_distribution(m, hs["M"].snapshot("M1", date(2015, 1, 1)))["KO/TKO"]


def test_strike_differential_edit_keeps_output():
    bios, fights = _league("M", "M", 2)
    s = FightHistory(bios, fights).snapshot("M0")
    adj = Adjustments.from_dict({"fighters": {"M0": {"overrides": {"sig_diff5": 4.0}}}})
    t = adj.apply(s)
    assert abs(t.sig_diff5 - 4.0) < 1e-9
    assert abs((t.slpm + t.sapm) - (s.slpm + s.sapm)) < 1e-9
    assert abs(s.sig_diff5 - 5 * (s.slpm - s.sapm)) < 1e-9


def test_intangibles_are_your_scores_per_matchup():
    from mma_predictor.intangibles import logit

    assert logit({}, {}) == 0.0  # nothing filled in: no effect
    assert logit({"cardio": 8}, {"fight_iq": 9}) == 0.0  # only qualities scored for both count
    assert abs(logit({"cardio": 8, "fight_iq": 6}, {"cardio": 5, "fight_iq": 6}) - 0.15 * 1.5) < 1e-9
    assert logit({"cardio": 11}, {"cardio": 1}) == 0.0  # off the 1-10 scale is ignored
    adj = Adjustments.from_dict({"matchups": [{"a": "X", "b": "Y", "intangibles": {"a": {"cardio": 9}, "b": {"cardio": 3}}}]})
    assert abs(adj.intangibles_logit("X", "Y") - 0.9) < 1e-9 and abs(adj.intangibles_logit("Y", "X") + 0.9) < 1e-9
