"""Intangibles: your 1-10 read of each fighter, per matchup.

Striking, Wrestling and Grappling are learned from results and stats. The
intangibles are the things the data can't see, so nothing is pre-filled:
you score each fighter from 1 (poor) to 10 (elite) on any of the qualities
below, for a specific matchup (a fighter's cardio matters more over five
rounds; their athleticism may be gone by the time a fight happens).

Only qualities scored for BOTH fighters count. Their average gap feeds the
prediction:

    intangibles log-odds = WEIGHT x mean(score_a - score_b)

With WEIGHT = 0.15, a one-point edge across the board is worth about 4
percentage points near a coin flip, and the largest possible edge (10 vs 1
on everything) about 1.35 log-odds (50% -> 79%): enough to decide close
fights, not to overturn a mismatch the data is sure about.

Stored with the matchup in adjustments:
    {"a": "Fighter A", "b": "Fighter B", "logit": 0, "note": "",
     "intangibles": {"a": {"cardio": 8}, "b": {"cardio": 5}}}
"""

from __future__ import annotations

from typing import Dict, Mapping, Optional, Tuple

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
    "athleticism": "Speed, explosiveness and strength right now. 10 = elite for the division; 1 = well below it.",
    "durability": "Tread left on the tyres: how much the body and chin have left after the fights, cage time and damage so far.",
    "killer_instinct": "Closing the show: how reliably they finish a hurt opponent instead of letting them off the hook.",
    "cardio": "Holding pace and power late, especially over five rounds.",
    "fight_iq": "Game planning, adjusting mid-fight, winning close rounds and staying out of bad positions.",
    "resilience": "Heart: coming back from being hurt or losing rounds, and from losses.",
    "big_fight": "Composure under the lights: title fights, main events, hostile crowds.",
}
WEIGHT = 0.15  # log-odds per point of average score gap
SCALE = (1, 10)


def clean(scores: Optional[Mapping[str, object]]) -> Dict[str, float]:
    """Only known qualities with a score in 1-10."""
    out: Dict[str, float] = {}
    for k, v in (scores or {}).items():
        try:
            x = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if k in INTANGIBLES and SCALE[0] <= x <= SCALE[1]:
            out[k] = x
    return out


def logit(scores_a: Optional[Mapping[str, object]], scores_b: Optional[Mapping[str, object]]) -> float:
    """Log-odds toward A from the qualities scored for both fighters (0 if none)."""
    a, b = clean(scores_a), clean(scores_b)
    both = [k for k in INTANGIBLES if k in a and k in b]
    if not both:
        return 0.0
    return WEIGHT * sum(a[k] - b[k] for k in both) / len(both)
