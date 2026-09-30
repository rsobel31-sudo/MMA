"""Win-probability model.

A no-intercept logistic regression over the antisymmetric matchup features.
It ships with hand-set *prior* weights encoding conventional MMA wisdom, so it
is usable before any training. ``fit`` then learns from data with an L2
penalty that pulls weights toward those priors rather than toward zero (a
MAP estimate with a Gaussian prior), which keeps the model sane on small
datasets and lets the data override the priors when it has evidence.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from .features import FEATURES

PRIOR_WEIGHTS: Dict[str, float] = {
    "overall": 1.00,
    "striking_rating": 0.30,
    "wrestling_rating": 0.30,
    "grappling_rating": 0.25,
    "intangibles_rating": 0.30,
    "striking_exchange": 0.35,
    "striking_defense": 0.10,
    "power_vs_chin": 0.25,
    "wrestling_edge": 0.30,
    "control": 0.25,
    "submission_threat": 0.12,
    "reach": 0.06,
    "age_curve": 0.30,
    "wear_and_tear": 0.20,
    "experience": 0.12,
    "form": 0.20,
    "layoff": 0.10,
    "chin_damage": 0.15,
    "cardio": 0.20,
    "schedule_strength": 0.30,
    "outside_rating": 0.30,
    "stance": 0.05,
}


def sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


@dataclass
class FitReport:
    samples: int
    iterations: int
    log_loss: float
    prior_log_loss: float


@dataclass
class WinModel:
    weights: Dict[str, float] = field(default_factory=lambda: dict(PRIOR_WEIGHTS))
    trained_on: int = 0
    # Confidence calibration: the backtest showed the fitted model hedges toward
    # 50/50 (its 70-85% picks won 80-86%), so logits are stretched by a factor
    # fitted on out-of-sample predictions. Contributions are shown unscaled.
    scale: float = 1.0

    def logit(self, x: Dict[str, float]) -> float:
        return self.scale * sum(self.weights.get(k, 0.0) * v for k, v in x.items())

    def predict(self, x: Dict[str, float]) -> float:
        return sigmoid(self.logit(x))

    def contributions(self, x: Dict[str, float]) -> Dict[str, float]:
        return {k: self.weights.get(k, 0.0) * v for k, v in x.items()}

    # --------------------------------------------------------------- training
    def fit(
        self,
        X: Sequence[Dict[str, float]],
        y: Sequence[int],
        l2: float = 25.0,
        lr: float = 0.3,
        iterations: int = 600,
        prior: Dict[str, float] = PRIOR_WEIGHTS,
    ) -> FitReport:
        """Full-batch gradient descent on penalised log loss.

        ``l2`` is the strength of the pull toward the prior weights, measured
        roughly in "fights' worth" of evidence: larger values trust the priors
        more, and its influence fades as the dataset grows.
        """
        if not X:
            return FitReport(0, 0, float("nan"), float("nan"))
        names = list(FEATURES)
        rows = [[x.get(k, 0.0) for k in names] for x in X]
        n = len(rows)
        w = [self.weights.get(k, prior.get(k, 0.0)) for k in names]
        mu = [prior.get(k, 0.0) for k in names]
        penalty = l2 / n
        prior_ll = _log_loss(rows, y, mu)
        try:
            import numpy as np
        except ImportError:  # pure-Python fallback below (same maths, much slower)
            np = None
        if np is not None:
            Xa, ya, wa, mua = np.array(rows, float), np.array(y, float), np.array(w, float), np.array(mu, float)
            for _ in range(iterations):
                err = 1.0 / (1.0 + np.exp(-(Xa @ wa))) - ya
                wa -= lr * (Xa.T @ err / n + penalty * (wa - mua))
            w = [float(v) for v in wa]
            iterations = 0
        for _ in range(iterations):
            grad = [0.0] * len(names)
            for row, label in zip(rows, y):
                err = sigmoid(sum(wi * xi for wi, xi in zip(w, row))) - label
                for j, xj in enumerate(row):
                    grad[j] += err * xj
            for j in range(len(w)):
                g = grad[j] / n + penalty * (w[j] - mu[j])
                w[j] -= lr * g
        self.weights = dict(zip(names, w))
        self.trained_on = n
        return FitReport(n, iterations, _log_loss(rows, y, w), prior_ll)

    # ------------------------------------------------------------ persistence
    def save(self, path: Path) -> None:
        Path(path).write_text(json.dumps({"weights": self.weights, "trained_on": self.trained_on, "scale": self.scale}, indent=2))

    @classmethod
    def load(cls, path: Path) -> "WinModel":
        data = json.loads(Path(path).read_text())
        return cls(weights={**PRIOR_WEIGHTS, **data["weights"]}, trained_on=data.get("trained_on", 0), scale=data.get("scale", 1.0))


def _log_loss(rows: List[List[float]], y: Sequence[int], w: Sequence[float]) -> float:
    total = 0.0
    for row, label in zip(rows, y):
        p = min(1 - 1e-9, max(1e-9, sigmoid(sum(wi * xi for wi, xi in zip(w, row)))))
        total -= label * math.log(p) + (1 - label) * math.log(1 - p)
    return total / len(rows)


def ranked_contributions(model: WinModel, x: Dict[str, float]) -> List[Tuple[str, float]]:
    return sorted(model.contributions(x).items(), key=lambda kv: -abs(kv[1]))


def fit_scale(logits_and_labels, lo: float = 0.8, hi: float = 2.0) -> float:
    """Logit stretch that maximises likelihood of out-of-sample predictions (1-D search)."""
    pairs = list(logits_and_labels)
    if len(pairs) < 50:
        return 1.0

    def nll(s: float) -> float:
        total = 0.0
        for z, y in pairs:
            p = min(1 - 1e-9, max(1e-9, sigmoid(s * z)))
            total -= y * math.log(p) + (1 - y) * math.log(1 - p)
        return total

    for _ in range(40):  # golden-section search
        a, b = lo + 0.382 * (hi - lo), lo + 0.618 * (hi - lo)
        if nll(a) < nll(b):
            hi = b
        else:
            lo = a
    return round((lo + hi) / 2, 3)
