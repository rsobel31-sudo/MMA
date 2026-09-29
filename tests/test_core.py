import math
from datetime import date
from pathlib import Path

import pytest

from mma_predictor.backtest import walk_forward
from mma_predictor.data import CornerStats, Fight, FighterBio, Method, devig, load_dataset, parse_method
from mma_predictor.features import FEATURES, matchup_features
from mma_predictor.history import FightHistory
from mma_predictor.model import WinModel
from mma_predictor.predictor import FightPredictor, build_training_set

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample"


@pytest.fixture(scope="module")
def history():
    bios, fights = load_dataset(SAMPLE)
    return FightHistory(bios, fights)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("KO/TKO", Method.KO),
        ("TKO - Doctor's Stoppage", Method.KO),
        ("Submission", Method.SUB),
        ("U-DEC", Method.DEC),
        ("Decision - Split", Method.SPLIT_DEC),
        ("S-DEC", Method.SPLIT_DEC),
        ("Draw", Method.DRAW),
        ("NC", Method.NC),
        ("DQ", Method.DQ),
    ],
)
def test_parse_method(raw, expected):
    assert parse_method(raw) is expected


def test_devig_sums_to_one():
    a, b = devig(-150, 130)
    assert math.isclose(a + b, 1.0)
    assert a > b


def _fight(d, a, b, winner, method=Method.DEC, stats=True):
    s = CornerStats(40, 90, 2, 4, 1, 0, 120) if stats else None
    return Fight(date=d, fighter_a=a, fighter_b=b, winner=winner, method=method, end_round=3, end_seconds=300, stats_a=s, stats_b=s)


def test_snapshot_excludes_same_day_and_future_bouts():
    fights = [
        _fight(date(2020, 1, 1), "A", "B", "A", Method.KO),
        _fight(date(2021, 1, 1), "A", "C", "C"),
    ]
    h = FightHistory({"A": FighterBio("A")}, fights)
    s = h.snapshot("A", date(2021, 1, 1))
    assert (s.wins, s.losses, s.fights) == (1, 0, 1)
    assert h.elo.rating_before("A", date(2020, 1, 1)) == h.elo.initial_rating("A")
    assert h.elo.rating_before("A", date(2020, 1, 2)) > h.elo.initial_rating("A")


def test_small_samples_shrink_toward_priors():
    h = FightHistory({}, [_fight(date(2020, 1, 1), "A", "B", "A")])
    s = h.snapshot("A", date(2020, 6, 1))
    raw_acc = 40 / 90
    assert abs(s.str_acc - h.priors.str_acc) < abs(raw_acc - h.priors.str_acc)


def test_features_are_antisymmetric(history):
    names = history.names()[:12]
    when = history.default_date()
    for a, b in zip(names, names[1:]):
        fa = matchup_features(history.snapshot(a, when), history.snapshot(b, when))
        fb = matchup_features(history.snapshot(b, when), history.snapshot(a, when))
        assert set(fa) == set(FEATURES)
        for k in FEATURES:
            assert math.isclose(fa[k], -fb[k], abs_tol=1e-9), k


def test_prediction_is_corner_independent_and_methods_sum(history):
    p = FightPredictor(history)
    a, b = history.names()[0], history.names()[5]
    ab, ba = p.predict(a, b), p.predict(b, a)
    assert math.isclose(ab.prob_a, ba.prob_b, abs_tol=1e-9)
    assert math.isclose(sum(ab.methods.values()), 1.0, abs_tol=1e-9)
    assert "Method breakdown" in ab.report()


def test_resolve_partial_names(history):
    full = history.names()[3]
    assert history.resolve(full.lower()) == full
    with pytest.raises(KeyError):
        history.resolve("no such fighter xyz")


def test_training_beats_priors(history):
    X, y, _ = build_training_set(history)
    model = WinModel()
    report = model.fit(X, y, iterations=200)
    assert report.log_loss < report.prior_log_loss


def test_backtest_beats_coin_flip_and_elo(history):
    res = walk_forward(history, retrain_every=200, iterations=150)
    assert res.model.n > 100
    assert res.model.accuracy > 0.58
    assert res.model.log_loss < math.log(2)
    assert res.model.log_loss <= res.elo.log_loss + 0.01


def test_model_roundtrip(tmp_path):
    m = WinModel()
    m.weights["elo"] = 0.5
    m.save(tmp_path / "m.json")
    assert WinModel.load(tmp_path / "m.json").weights["elo"] == 0.5
