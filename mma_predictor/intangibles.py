"""Intangibles: the fourth rating category.

Striking, Wrestling and Grappling are learned from results and stats. The
intangibles are qualities the data only hints at, so each starts from a
data-based estimate on the same 1500-average scale and is meant to be
corrected by your own judgement (edit any of them in the web interface or
via ``overrides`` in adjustments, e.g. ``"i_athleticism": 1700``).

    athleticism        speed, explosiveness, strength
                       estimate: age (peak years highest) + share of wins inside two rounds
    durability         tread left on the tyres (wear and tear, inverted)
                       estimate: wear index (mileage + damage absorbed), weighted more past 30
    killer_instinct    closing the show when the chance comes
                       estimate: share of wins that are finishes, especially early ones
    cardio             holding up late
                       estimate: win rate in fights that reach round 3+
    fight_iq           winning the close ones
                       estimate: decision record, split decisions counting as the closest
    resilience         heart; bouncing back
                       estimate: record in the fight right after a loss
    big_fight          composure under the lights
                       estimate: five-round and title fights, and results in them

Every estimate is shrunk toward 1500 when there's little evidence, and clipped
to 1100-1900 so no single proxy can dominate.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Dict, Tuple

from .data import Method

if TYPE_CHECKING:  # pragma: no cover
    from .history import FighterSnapshot

INTANGIBLES: Tuple[str, ...] = (
    "athleticism", "durability", "killer_instinct", "cardio", "fight_iq", "resilience", "big_fight",
)
INTANGIBLE_LABELS: Dict[str, str] = {
    "athleticism": "Athleticism",
    "durability": "Durability (wear and tear)",
    "killer_instinct": "Killer instinct",
    "cardio": "Cardio",
    "fight_iq": "Fight IQ",
    "resilience": "Resilience / heart",
    "big_fight": "Big-fight experience",
}
INTANGIBLE_HELP: Dict[str, str] = {
    "athleticism": "Speed, explosiveness and strength. Estimated from age and early wins; mainly your call.",
    "durability": "Tread left on the tyres: the inverse of wear and tear (fights, cage time, damage absorbed, age).",
    "killer_instinct": "Closing the show when the chance comes: share of wins that are finishes, especially early.",
    "cardio": "Holding up late: win rate in fights that reach round 3 or later.",
    "fight_iq": "Winning the close ones: decision record, with split decisions counting as the closest.",
    "resilience": "Heart: record in the fight right after a loss.",
    "big_fight": "Composure under the lights: five-round and title fights, and results in them.",
}
LO, HI = 1100.0, 1900.0


def _clip(v: float) -> float:
    return max(LO, min(HI, v))


def _shrunk_rate(wins: float, total: float, prior: float = 0.5, weight: float = 3.0) -> float:
    return (wins + prior * weight) / (total + weight)


def estimate(s: "FighterSnapshot") -> Dict[str, float]:
    """Data-based starting values for one fighter (before any edits)."""
    from .features import wear_penalty

    apps = s.all_appearances
    decided = [a for a in apps if a.result is not None]
    wins = [a for a in decided if a.result]

    # Athleticism: peak around 27-30, fading after; plus winning fast.
    age = s.age if s.age is not None else 30.0
    if age < 24:
        youth = 0.3 - (24 - age) * 0.05  # often still raw
    elif age <= 30:
        youth = 0.3  # athletic prime
    else:
        youth = max(-1.5, 0.3 - (age - 30) / 5.0)
    early_wins = sum(1 for a in wins if a.method.is_finish and a.fight.end_round <= 2)
    early_share = _shrunk_rate(early_wins, len(wins), 0.3, 4)
    athleticism = 1500 + 110 * youth + 350 * (early_share - 0.3)

    durability = 1500 - 70 * (wear_penalty(s) - 1.5)

    finish_share = _shrunk_rate(sum(1 for a in wins if a.method.is_finish), len(wins), 0.5, 4)
    killer = 1500 + 450 * (finish_share - 0.5) + 250 * (early_share - 0.3)

    cardio = 1500 + 500 * (s.late_win_rate - 0.5)

    # Fight IQ: decisions are the fights decided by margins; split decisions most of all.
    dec_w = sum(1.5 if a.method is Method.SPLIT_DEC else 1.0 for a in decided if a.method.is_decision and a.result)
    dec_l = sum(1.5 if a.method is Method.SPLIT_DEC else 1.0 for a in decided if a.method.is_decision and not a.result)
    fight_iq = 1500 + 450 * (_shrunk_rate(dec_w, dec_w + dec_l, 0.5, 4) - 0.5)

    after_loss = [decided[i + 1] for i in range(len(decided) - 1) if decided[i].result is False]
    resilience = 1500 + 450 * (_shrunk_rate(sum(1 for a in after_loss if a.result), len(after_loss), 0.5, 3) - 0.5)

    big = [a for a in decided if a.fight.scheduled_rounds >= 5 or a.fight.title_fight]
    big_rate = _shrunk_rate(sum(1 for a in big if a.result), len(big), 0.5, 3)
    big_fight = 1500 + 70 * math.log1p(len(big)) + 300 * (big_rate - 0.5)

    raw = {"athleticism": athleticism, "durability": durability, "killer_instinct": killer, "cardio": cardio,
           "fight_iq": fight_iq, "resilience": resilience, "big_fight": big_fight}
    return {k: round(_clip(v), 1) for k, v in raw.items()}


def category(values: Dict[str, float]) -> float:
    return sum(values[k] for k in INTANGIBLES) / len(INTANGIBLES)
