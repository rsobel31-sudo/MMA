import math
import random

from mma_predictor import picks as P
from mma_predictor import review


def test_dec_chance_mismatch_term_uses_line_then_model():
    cal = [0.0, 1.0, -0.5]
    even = P.dec_chance(0.5, cal, pa=0.5)
    lopsided_line = P.dec_chance(0.5, cal, pa=0.5, p_line=0.85)
    lopsided_model = P.dec_chance(0.5, cal, pa=0.85)
    assert even == 0.5
    assert lopsided_line < even and abs(lopsided_line - lopsided_model) < 1e-12
    # two coefficients: the old correction, untouched by the line
    assert P.dec_chance(0.5, [0.0, 1.0], pa=0.5, p_line=0.9) == 0.5


def test_logistic_recovers_coefficients():
    rng = random.Random(1)
    X, y = [], []
    for _ in range(4000):
        x = rng.uniform(-2, 2)
        X.append([1.0, x])
        y.append(int(rng.random() < 1 / (1 + math.exp(-(0.3 + 1.5 * x)))))
    b = review.logistic(X, y)
    assert abs(b[0] - 0.3) < 0.15 and abs(b[1] - 1.5) < 0.15


def _rows(n=3000, mismatch_effect=-0.6):
    rng = random.Random(7)
    rows = []
    for i in range(n):
        line = rng.uniform(0.2, 0.8)
        raw = rng.uniform(0.35, 0.6)
        z = math.log(raw / (1 - raw)) + mismatch_effect * abs(math.log(line / (1 - line)))
        rows.append({"date": f"{2016 + i * 11 // n}-06-01", "pdec_raw": raw, "pa": line, "market": line,
                     "dec": int(rng.random() < 1 / (1 + math.exp(-z))), "y": int(rng.random() < line),
                     "sa": {"age": 30}, "sb": {"age": 30}})
    return rows


def test_decision_study_switches_only_when_mismatch_matters():
    d = review.decision_study(_rows(), [0.0, 1.0])
    assert d["chosen"] == "refit + matchup mismatch (line, else model)" and d["improves"]
    flat = review.decision_study(_rows(mismatch_effect=0.0), [0.0, 1.0])
    assert flat["chosen"] == "refit, all years equal" and not flat["improves"]
