"""Walk-forward backtesting.

The model is retrained periodically on bouts strictly before the evaluation
window and then scored on the next block of fights, which is what it would
have faced in real time. Baselines: Elo alone, and the betting market when
odds are available.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .data import devig
from .history import FightHistory
from .model import WinModel
from .predictor import build_training_set
from .ratings import expected_score


@dataclass
class Scores:
    n: int = 0
    correct: int = 0
    log_loss_sum: float = 0.0
    brier_sum: float = 0.0

    def add(self, p: float, y: int) -> None:
        p = min(1 - 1e-6, max(1e-6, p))
        self.n += 1
        self.correct += int((p >= 0.5) == bool(y))
        self.log_loss_sum -= y * math.log(p) + (1 - y) * math.log(1 - p)
        self.brier_sum += (p - y) ** 2

    @property
    def accuracy(self) -> float:
        return self.correct / self.n if self.n else float("nan")

    @property
    def log_loss(self) -> float:
        return self.log_loss_sum / self.n if self.n else float("nan")

    @property
    def brier(self) -> float:
        return self.brier_sum / self.n if self.n else float("nan")

    def line(self, label: str) -> str:
        return f"{label:<14} n={self.n:<5} acc={self.accuracy:6.1%}  log-loss={self.log_loss:.4f}  brier={self.brier:.4f}"


@dataclass
class BacktestResult:
    model: Scores = field(default_factory=Scores)
    elo: Scores = field(default_factory=Scores)
    market: Scores = field(default_factory=Scores)
    model_on_market: Scores = field(default_factory=Scores)
    calibration: List[Tuple[float, int, int]] = field(default_factory=list)  # (bin lower, n, wins)
    high_conf: Scores = field(default_factory=Scores)

    def report(self) -> str:
        lines = ["Walk-forward backtest", "---------------------", self.model.line("model"), self.elo.line("elo only")]
        if self.market.n:
            lines.append(self.market.line("market"))
            lines.append(self.model_on_market.line("model (same)"))
        if self.high_conf.n:
            lines.append(self.high_conf.line("model >=65%"))
        lines += ["", "Calibration (predicted favourite prob -> actual win rate):"]
        for lo, n, wins in self.calibration:
            if n:
                lines.append(f"  {lo:.0%}-{lo + 0.1:.0%}: n={n:<5} actual={wins / n:6.1%}")
        return "\n".join(lines)


def walk_forward(
    history: FightHistory,
    train_fraction: float = 0.4,
    retrain_every: int = 100,
    min_prior_fights: int = 1,
    l2: float = 25.0,
    iterations: int = 300,
) -> BacktestResult:
    X, y, fights = build_training_set(history, min_prior_fights=min_prior_fights)
    if len(X) < 20:
        raise ValueError(f"only {len(X)} usable bouts; need more data to backtest")
    start = max(10, int(len(X) * train_fraction))
    result = BacktestResult()
    bins = [[0, 0] for _ in range(5)]  # favourite prob bins 50-60 ... 90-100
    model: Optional[WinModel] = None
    since_train = retrain_every
    for i in range(start, len(X)):
        f = fights[i]
        if since_train >= retrain_every:
            # Train only on bouts before this date (same-day bouts excluded).
            cutoff = next(j for j in range(i + 1) if j == i or fights[j].date >= f.date)
            model = WinModel()
            model.fit(X[:cutoff], y[:cutoff], l2=l2, iterations=iterations)
            since_train = 0
        since_train += 1
        assert model is not None
        p = model.predict(X[i])
        result.model.add(p, y[i])
        pe = expected_score(history.elo.rating_before(f.fighter_a, f.date), history.elo.rating_before(f.fighter_b, f.date))
        result.elo.add(pe, y[i])
        fav = max(p, 1 - p)
        fav_won = int((p >= 0.5) == bool(y[i]))
        b = min(4, int((fav - 0.5) * 10))
        bins[b][0] += 1
        bins[b][1] += fav_won
        if fav >= 0.65:
            result.high_conf.add(p, y[i])
        if f.odds_a is not None and f.odds_b is not None:
            result.market.add(devig(f.odds_a, f.odds_b)[0], y[i])
            result.model_on_market.add(p, y[i])
    result.calibration = [(0.5 + k / 10, n, w) for k, (n, w) in enumerate(bins)]
    return result
