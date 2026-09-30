"""Walk-forward backtesting.

The model is retrained periodically on bouts strictly before the evaluation
window and then scored on the next block of fights, which is what it would
have faced in real time. Baselines: Elo alone, and the betting market when
odds are available.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .data import Fight, devig
from .history import FightHistory
from .model import WinModel
from .predictor import build_training_set
from .ratings import expected_score
from .sports import SPORTS, split_histories, sport_of


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

    def merge(self, other: "Scores") -> None:
        self.n += other.n
        self.correct += other.correct
        self.log_loss_sum += other.log_loss_sum
        self.brier_sum += other.brier_sum

    def line(self, label: str) -> str:
        return f"{label:<14} n={self.n:<5} acc={self.accuracy:6.1%}  log-loss={self.log_loss:.4f}  brier={self.brier:.4f}"


@dataclass
class BacktestResult:
    model: Scores = field(default_factory=Scores)
    elo: Scores = field(default_factory=Scores)  # classic single-number Elo
    overall: Scores = field(default_factory=Scores)  # category-aggregate rating alone
    market: Scores = field(default_factory=Scores)
    model_on_market: Scores = field(default_factory=Scores)
    calibration: List[Tuple[float, int, int]] = field(default_factory=list)  # (bin lower, n, wins)
    high_conf: Scores = field(default_factory=Scores)
    by_sport: Dict[str, Scores] = field(default_factory=dict)  # model scores on men's / women's bouts
    # Bouts where both fighters' full records are in the data. When only one is, the one we
    # crawled tends to be the one who went on to succeed (we crawl ranked fighters), which
    # leaks the future: that fighter won 73% of such UFC bouts. This is the fair measure.
    fair: Scores = field(default_factory=Scores)
    fair_elo: Scores = field(default_factory=Scores)
    # Out-of-sample prediction for every scored bout: (fight, P(fighter_a wins), features).
    predictions: List[Tuple[Fight, float, dict]] = field(default_factory=list)

    def report(self) -> str:
        lines = ["Walk-forward backtest", "---------------------", self.model.line("model"), self.overall.line("overall rating"), self.elo.line("classic elo")]
        if self.market.n:
            lines.append(self.market.line("market"))
            lines.append(self.model_on_market.line("model (same)"))
        if self.high_conf.n:
            lines.append(self.high_conf.line("model >=65%"))
        if self.fair.n:
            lines.append(self.fair.line("both complete"))
            lines.append(self.fair_elo.line("  classic elo"))
        for sport, sc in sorted(self.by_sport.items(), key=lambda kv: -kv[1].n):
            lines.append(sc.line(f"  {SPORTS.get(sport, sport).lower()}"))
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
    event_prefix: str = "",
) -> BacktestResult:
    """Train on everything before each block; score bouts whose event starts with ``event_prefix``."""
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
        if event_prefix and not f.event.lower().startswith(event_prefix.lower()):
            continue
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
        result.predictions.append((f, p, X[i]))
        result.by_sport.setdefault(sport_of(f, history.bios), Scores()).add(p, y[i])
        both = all(getattr(history.bios.get(n), "complete", True) for n in (f.fighter_a, f.fighter_b))
        classic = history.classic_elo
        e_classic = expected_score(classic.rating_before(f.fighter_a, f.date), classic.rating_before(f.fighter_b, f.date))
        result.elo.add(e_classic, y[i])
        if both:
            result.fair.add(p, y[i])
            result.fair_elo.add(e_classic, y[i])
        skills = history.skills
        result.overall.add(expected_score(skills.overall_before(f.fighter_a, f.date), skills.overall_before(f.fighter_b, f.date)), y[i])
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


def walk_forward_split(bios, fights, scouting=None, **kwargs) -> BacktestResult:
    """Men's and women's MMA as separate sports: own ratings, base rates and model each."""
    merged = BacktestResult()
    bins: Dict[float, List[int]] = {}
    for history in split_histories(bios, fights, scouting).values():
        res = walk_forward(history, **kwargs)
        for name in ("model", "elo", "overall", "market", "model_on_market", "high_conf", "fair", "fair_elo"):
            getattr(merged, name).merge(getattr(res, name))
        for sport, sc in res.by_sport.items():
            merged.by_sport.setdefault(sport, Scores()).merge(sc)
        for lo, n, w in res.calibration:
            b = bins.setdefault(lo, [0, 0])
            b[0] += n
            b[1] += w
        merged.predictions += res.predictions
    merged.predictions.sort(key=lambda t: t[0].date)
    merged.calibration = [(lo, n, w) for lo, (n, w) in sorted(bins.items())]
    return merged
