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
