import json
import random
from datetime import date
from pathlib import Path

from mma_predictor.analysis import PATTERNS, calibration_bands, match_patterns, pattern_table, regression
from mma_predictor.backtest import walk_forward
from mma_predictor.data import Fight, FighterBio, Method, load_dataset
from mma_predictor.features import FEATURES, BoutContext, matchup_features
from mma_predictor.history import FightHistory
from mma_predictor.model import fit_scale, sigmoid
from mma_predictor import predlog

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample"


def test_regression_recovers_a_planted_effect():
    rng = random.Random(1)
    X, y = [], []
    for _ in range(1500):
        x = {k: 0.0 for k in FEATURES}
        x["elo" if "elo" in FEATURES else "overall"] = rng.gauss(0, 1)
        x["reach"] = rng.gauss(0, 1)  # pure noise
        X.append(x)
        key = "overall" if "overall" in FEATURES else "elo"
        y.append(int(rng.random() < sigmoid(1.2 * x[key])))
    rows = {r["feature"]: r for r in regression(X, y)}
    assert abs(rows["overall"]["coef_per_sd"] - 1.2) < 0.2 and rows["overall"]["p"] < 1e-6
    assert rows["reach"]["p"] > 0.01


def test_fit_scale_stretches_underconfident_predictions():
    rng = random.Random(2)
    pairs = []
    for _ in range(3000):
        z = rng.gauss(0, 1)
        pairs.append((z, int(rng.random() < sigmoid(1.5 * z))))  # truth is 1.5x sharper
    assert 1.35 < fit_scale(pairs) < 1.65


def test_patterns_and_bands_on_sample_backtest():
    bios, fights = load_dataset(SAMPLE)
    h = FightHistory(bios, fights)
    res = walk_forward(h, retrain_every=200, iterations=100)
    table = {p["key"]: p for p in pattern_table(h, res.predictions)}
    assert set(table) == {p.key for p in PATTERNS}
    gap = table["rating_gap"]
    assert gap["n"] > 20 and gap["win_rate"] > 0.6  # big favourites win
    bands = calibration_bands(res.predictions)
    assert sum(b["n"] for b in bands) == res.model.n
    # A matchup always reports the edge on the fighter who has it.
    a, b = h.names()[0], h.names()[1]
    sa, sb = h.snapshot(a), h.snapshot(b)
    fwd = dict(match_patterns(sa, sb, matchup_features(sa, sb), BoutContext()))
    rev = dict(match_patterns(sb, sa, matchup_features(sb, sa), BoutContext()))
    assert all(rev[k] == -v for k, v in fwd.items() if k != "close_ratings")


def test_prediction_log_freezes_first_pick_and_grades(tmp_path):
    fights = [Fight(date(2024, 1, 1), "A", "B", "A", Method.DEC, 3, 300),
              Fight(date(2024, 6, 1), "A", "C", "C", Method.KO, 1, 60)]
    h = FightHistory({n: FighterBio(n) for n in "ABC"}, fights)
    events = [{"name": "UFC X", "date": "2024-06-01", "bouts": [{"a_id": "A", "b_id": "C", "rounds": 3}]}]
    log_path = tmp_path / "log.json"
    first = lambda a, b, r: {"p_a": 0.7, "pick": a, "method": "x", "method_p": 0.3}  # noqa: E731
    later = lambda a, b, r: {"p_a": 0.2, "pick": b, "method": "x", "method_p": 0.3}  # noqa: E731
    predlog.update(log_path, FightHistory({}, fights[:1]), events, first, {})
    log = predlog.update(log_path, h, events, later, {})
    entry = next(iter(log["entries"].values()))
    assert entry["first"]["p_a"] == 0.7  # the pre-fight pick is kept
    assert entry["result"]["correct"] is False and log["scorecard"]["graded"] == 1
    assert json.loads(log_path.read_text())["scorecard"]["accuracy"] == 0.0
