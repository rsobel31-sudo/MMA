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
from .history import FighterSnapshot


def method_distribution(winner: FighterSnapshot, loser: FighterSnapshot, scheduled_rounds: int = 3) -> Dict[str, float]:
    P = winner.priors  # both fighters are in the same sport
    pop = P.method_share
    raw = {m: winner.win_methods[m] * loser.loss_methods[m] / pop[m] for m in METHOD_BUCKETS}

    ko_matchup = (winner.kd_per15 / P.kd_per15) * chin_vulnerability(loser)
    sub_matchup = (winner.sub_per15 / P.sub_per15) * (loser.sub_loss_rate / (0.5 * pop["SUB"]))
    raw["KO/TKO"] *= _damp(ko_matchup)
    raw["SUB"] *= _damp(sub_matchup)

    # No five-round tilt. A fixed 15% shift toward finishes in five-rounders was tested out of
    # sample (picks calibrate data, 2014-18 -> 2019-26 and 2019-22 -> 2023-26): since 2019
    # five-rounders go the distance as often as three-rounders (51% vs 50%), so the tilt
    # hurt, and a separately fitted five-round term flips sign between eras. When finishes
    # come in five-rounders is modelled separately (picks.Timing).

    total = sum(raw.values())
    return {m: v / total for m, v in raw.items()}


def _damp(ratio: float) -> float:
    """Pull an evidence ratio toward 1 so a single signal can't dominate."""
    return max(0.5, min(2.0, ratio)) ** 0.5
