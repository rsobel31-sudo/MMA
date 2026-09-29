"""High-level prediction API."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple

from .data import METHOD_BUCKETS, Fight, Matchup, devig
from .features import FEATURE_LABELS, BoutContext, matchup_features
from .history import FightHistory, FighterSnapshot
from .methods import method_distribution
from .model import WinModel, ranked_contributions
from .styles import matchup_insights, scouting_line


@dataclass
class Prediction:
    fighter_a: str
    fighter_b: str
    prob_a: float
    methods: Dict[Tuple[str, str], float]  # (fighter, method bucket) -> probability
    factors: List[Tuple[str, float]]  # (feature, logit contribution toward A)
    insights: List[str]
    profiles: Tuple[str, str]
    confidence: str
    market_a: Optional[float] = None
    features: Dict[str, float] = field(default_factory=dict)

    @property
    def prob_b(self) -> float:
        return 1.0 - self.prob_a

    @property
    def pick(self) -> str:
        return self.fighter_a if self.prob_a >= 0.5 else self.fighter_b

    @property
    def pick_prob(self) -> float:
        return max(self.prob_a, self.prob_b)

    @property
    def most_likely_outcome(self) -> Tuple[str, str, float]:
        (fighter, method), p = max(self.methods.items(), key=lambda kv: kv[1])
        return fighter, method, p

    @property
    def distance_prob(self) -> float:
        return sum(p for (_, m), p in self.methods.items() if m == "DEC")

    @property
    def edge_a(self) -> Optional[float]:
        return None if self.market_a is None else self.prob_a - self.market_a

    def report(self, top_factors: int = 6) -> str:
        a, b = self.fighter_a, self.fighter_b
        lines = [
            f"{a} vs {b}",
            "=" * (len(a) + len(b) + 4),
            f"Pick: {self.pick} ({self.pick_prob:.1%}) - confidence: {self.confidence}",
            f"  {a:<28} {self.prob_a:6.1%}",
            f"  {b:<28} {self.prob_b:6.1%}",
            "",
            "Method breakdown:",
        ]
        for fighter in (a, b):
            parts = "  ".join(f"{m} {self.methods[(fighter, m)]:5.1%}" for m in METHOD_BUCKETS)
            lines.append(f"  {fighter:<28} {parts}")
        f, m, p = self.most_likely_outcome
        lines.append(f"  Most likely: {f} by {m} ({p:.1%}); goes the distance {self.distance_prob:.1%}")
        if self.market_a is not None:
            edge = self.edge_a or 0.0
            side = a if edge > 0 else b
            lines += [
                "",
                f"Market (no-vig): {a} {self.market_a:.1%} / {b} {1 - self.market_a:.1%}",
                f"Model edge: {abs(edge):.1%} toward {side}",
            ]
        lines += ["", "Key factors (log-odds contribution):"]
        for name, c in self.factors[:top_factors]:
            if abs(c) < 0.01:
                continue
            who = a if c > 0 else b
            lines.append(f"  {c:+.2f}  {FEATURE_LABELS.get(name, name)} -> favours {who}")
        lines += ["", "Profiles:", f"  {self.profiles[0]}", f"  {self.profiles[1]}"]
        if self.insights:
            lines += ["", "Matchup patterns:"]
            lines += [f"  - {n}" for n in self.insights]
        return "\n".join(lines)


def _confidence(p: float, a: FighterSnapshot, b: FighterSnapshot) -> str:
    edge = abs(p - 0.5)
    thin = min(a.fights, b.fights) < 3
    if edge >= 0.25 and not thin:
        return "high"
    if edge >= 0.12:
        return "medium" if not thin else "low-medium (thin data)"
    return "low (coin-flip range)" if not thin else "low (thin data)"


class FightPredictor:
    def __init__(self, history: FightHistory, model: Optional[WinModel] = None) -> None:
        self.history = history
        self.model = model or WinModel()

    def features(self, a: str, b: str, when: date, ctx: BoutContext) -> Tuple[FighterSnapshot, FighterSnapshot, Dict[str, float]]:
        sa, sb = self.history.snapshot(a, when), self.history.snapshot(b, when)
        return sa, sb, matchup_features(sa, sb, ctx)

    def predict(
        self,
        fighter_a: str,
        fighter_b: str,
        when: Optional[date] = None,
        scheduled_rounds: int = 3,
        title_fight: bool = False,
        odds_a: Optional[float] = None,
        odds_b: Optional[float] = None,
    ) -> Prediction:
        a, b = self.history.resolve(fighter_a), self.history.resolve(fighter_b)
        if a == b:
            raise ValueError("a fighter can't fight themselves")
        if when is None:
            when = self.history.default_date()
        ctx = BoutContext(scheduled_rounds, title_fight)
        sa, sb, x = self.features(a, b, when, ctx)
        p = self.model.predict(x)
        dist_a = method_distribution(sa, sb, scheduled_rounds)
        dist_b = method_distribution(sb, sa, scheduled_rounds)
        methods = {(a, m): p * dist_a[m] for m in METHOD_BUCKETS}
        methods.update({(b, m): (1 - p) * dist_b[m] for m in METHOD_BUCKETS})
        market = devig(odds_a, odds_b)[0] if odds_a is not None and odds_b is not None else None
        return Prediction(
            fighter_a=a,
            fighter_b=b,
            prob_a=p,
            methods=methods,
            factors=ranked_contributions(self.model, x),
            insights=matchup_insights(sa, sb, ctx),
            profiles=(scouting_line(sa), scouting_line(sb)),
            confidence=_confidence(p, sa, sb),
            market_a=market,
            features=x,
        )

    def predict_matchup(self, m: Matchup) -> Prediction:
        return self.predict(m.fighter_a, m.fighter_b, m.date, m.scheduled_rounds, m.title_fight, m.odds_a, m.odds_b)


def build_training_set(
    history: FightHistory, fights: Optional[List[Fight]] = None, min_prior_fights: int = 1
) -> Tuple[List[Dict[str, float]], List[int], List[Fight]]:
    """Point-in-time features for every decided bout (no look-ahead)."""
    X: List[Dict[str, float]] = []
    y: List[int] = []
    used: List[Fight] = []
    for f in fights if fights is not None else history.fights:
        if not f.is_scored:
            continue
        sa = history.snapshot(f.fighter_a, f.date)
        sb = history.snapshot(f.fighter_b, f.date)
        if min(sa.fights, sb.fights) < min_prior_fights:
            continue
        X.append(matchup_features(sa, sb, BoutContext(f.scheduled_rounds, f.title_fight)))
        y.append(int(f.winner == f.fighter_a))
        used.append(f)
    return X, y, used
