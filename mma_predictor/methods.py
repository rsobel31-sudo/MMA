"""How will it end? KO/TKO, submission or decision.

Given that W beats L, combine two independent signals about the method:
how W tends to win and how L tends to lose. Each is a smoothed share over
the three buckets. They're combined as a product of experts normalised by
the population share (Bayes' rule with both treated as evidence), then
nudged by the specific matchup (power vs chin, submission threat vs
submission defence) and by the scheduled length.
"""

from __future__ import annotations

from typing import Dict

from .data import METHOD_BUCKETS
from .features import chin_vulnerability
from .history import DEFAULT_PRIORS, FighterSnapshot

P = DEFAULT_PRIORS


def method_distribution(winner: FighterSnapshot, loser: FighterSnapshot, scheduled_rounds: int = 3) -> Dict[str, float]:
    pop = P.method_share
    raw = {m: winner.win_methods[m] * loser.loss_methods[m] / pop[m] for m in METHOD_BUCKETS}

    ko_matchup = (winner.kd_per15 / P.kd_per15) * chin_vulnerability(loser)
    sub_matchup = (winner.sub_per15 / P.sub_per15) * (loser.sub_loss_rate / (0.5 * pop["SUB"]))
    raw["KO/TKO"] *= _damp(ko_matchup)
    raw["SUB"] *= _damp(sub_matchup)

    if scheduled_rounds >= 5:
        # Two extra rounds give more time to find a finish.
        raw["KO/TKO"] *= 1.15
        raw["SUB"] *= 1.15
        raw["DEC"] *= 0.85

    total = sum(raw.values())
    return {m: v / total for m, v in raw.items()}


def _damp(ratio: float) -> float:
    """Pull an evidence ratio toward 1 so a single signal can't dominate."""
    return max(0.5, min(2.0, ratio)) ** 0.5
