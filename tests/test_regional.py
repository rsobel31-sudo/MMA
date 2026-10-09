from datetime import date

from mma_predictor import regional as R


def test_promotion_names():
    assert R.promotion("Fury FC 103 - Fury Fighting Championship 103") == "Fury FC"
    assert R.promotion("Pancrase - Blood.9") == "Pancrase"
    assert R.promotion("UFC - Road to UFC Season 4: Shanghai") == "Road to UFC"


def test_replay_moves_winner_up_and_skips_self_bouts():
    bs = [R.Bout(date(2024, 1, 1), "a", "b", 1.0, "KO", "x"), R.Bout(date(2024, 2, 1), "a", "a", 1.0, "KO", "x")]
    ps = R.replay(bs)
    assert ps["a"].r > 1500 > ps["b"].r and ps["a"].n == 1
    # A firmer prior moves a single result less.
    assert R.replay(bs, rd0=200)["a"].r < ps["a"].r


def test_ufc_feeder_shows_are_not_minor_leagues():
    from mma_predictor import minor_leagues as ML

    assert {"Dana White's Contender Series", "Road to UFC"} <= ML.FEEDERS


def test_a_promotions_old_event_names_count_with_its_new_ones():
    from mma_predictor import minor_leagues as ML

    orgs = {"CW": {"org_url": "https://www.sherdog.com/organizations/Cage-Warriors-186", "org_name": "Cage Warriors",
                   "events": [["2013-07-06", "CWFC 56 - Cage Warriors Fighting Championship 56", ""],
                              ["2018-02-24", "CW 90 - Cage Warriors 90", ""]]}}
    canon = ML.canonicalizer(orgs)
    assert canon("CWFC 60 - Cage Warriors Fighting Championship 60") == "CW"
    assert canon("UFC 300 - Pereira vs. Hill") == "UFC"
