"""Matchup features.

Each feature is *antisymmetric*: swapping the fighters flips its sign. With a
no-intercept logistic model this guarantees P(A beats B) = 1 - P(B beats A),
so the corner a fighter is listed in can never change the prediction.

Most features are interactions -- what fighter A does well *against what
fighter B is bad at* -- rather than raw stat differences. A 4-takedowns-per-15
wrestler is a very different problem for an opponent with 90% takedown defence
than for one with 50%.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import math

from .history import FighterSnapshot, log_experience
from .skills import glicko_g



@dataclass(frozen=True)
class BoutContext:
    scheduled_rounds: int = 3
    title_fight: bool = False


FEATURES: List[str] = [
    "overall",
    "striking_rating",
    "wrestling_rating",
    "grappling_rating",
    "striking_exchange",
    "striking_defense",
    "power_vs_chin",
    "wrestling_edge",
    "control",
    "submission_threat",
    "reach",
    "age_curve",
    "wear_and_tear",
    "experience",
    "form",
    "layoff",
    "chin_damage",
    "cardio",
    "schedule_strength",
    "outside_rating",
    "size",
    "size_gap",
    "height",
    "stance",
]

FEATURE_LABELS: Dict[str, str] = {
    "overall": "overall rating (aggregate of the three)",
    "striking_rating": "striking ratings matchup",
    "wrestling_rating": "wrestling ratings matchup",
    "grappling_rating": "grappling ratings matchup",
    "striking_exchange": "projected striking exchanges",
    "striking_defense": "striking defence",
    "power_vs_chin": "knockdown power vs opponent's chin",
    "wrestling_edge": "takedown offence vs opponent's takedown defence",
    "control": "top control time",
    "submission_threat": "submission threat",
    "reach": "reach",
    "age_curve": "age / athletic prime",
    "wear_and_tear": "wear and tear (fights, cage time, damage taken)",
    "experience": "experience",
    "form": "recent form",
    "layoff": "ring rust (layoff)",
    "chin_damage": "accumulated KO damage",
    "cardio": "cardio / late-round performance",
    "schedule_strength": "strength of schedule",
    "outside_rating": "Fight Matrix rating edge",
    "size": "size (weight class fought at)",
    "size_gap": "size mismatch beyond a division",
    "height": "height",
    "stance": "stance matchup",
    "manual": "your matchup read",
    "intangibles": "your intangibles (1-10 scores)",
}


def _clip(x: float, lo: float = -3.0, hi: float = 3.0) -> float:
    return max(lo, min(hi, x))


def _size_units(a: FighterSnapshot, b: FighterSnapshot) -> float:
    """How much heavier A fights than B, in 5% steps (0 unless both fighting weights are known)."""
    if not a.fight_weight or not b.fight_weight:
        return 0.0
    return math.log(a.fight_weight / b.fight_weight) / 0.05


def age_penalty(age: Optional[float]) -> float:
    """Athletic decline curve: flat through the prime, accelerating after ~33."""
    if age is None:
        return 0.0
    penalty = max(0.0, age - 32.0) ** 1.5 / 10.0
    if age < 24:  # very young fighters are often still raw
        penalty += (24.0 - age) * 0.05
    return penalty


def wear_index(s: FighterSnapshot) -> float:
    """Mileage and damage: ~0.4 for a 5-fight prospect, ~4-5 for a 50-fight veteran.

    Pro fights (including regional record) and cage time measure mileage;
    KO/TKO losses, knockdowns absorbed and significant strikes absorbed
    measure damage. Only bouts in the data count toward cage time and
    damage, so it undercounts for fighters whose early career is missing.
    """
    mileage = 0.5 * s.total_fights / 20.0 + 0.5 * s.minutes / 150.0
    damage = 0.6 * s.ko_losses + 0.25 * s.kd_absorbed + s.sig_absorbed / 1000.0
    return mileage + damage


def wear_penalty(s: FighterSnapshot) -> float:
    """Wear hurts more the older the body carrying it."""
    older = max(0.0, (s.age or 30.0) - 30.0) / 8.0
    return wear_index(s) * (1.0 + older)


def layoff_penalty(days: Optional[int]) -> float:
    if days is None:
        return 0.0
    return min(2.5, max(0.0, days - 400) / 365.0)


def lands_on(attacker: FighterSnapshot, defender: FighterSnapshot) -> float:
    """Projected significant strikes per minute ``attacker`` lands on ``defender``."""
    hittable = (1.0 - defender.str_def) / (1.0 - defender.priors.str_def)
    return attacker.slpm * hittable


def takedowns_on(attacker: FighterSnapshot, defender: FighterSnapshot) -> float:
    """Projected takedowns per 15 minutes."""
    porous = (1.0 - defender.td_def) / (1.0 - defender.priors.td_def)
    return attacker.td_per15 * porous


def chin_vulnerability(s: FighterSnapshot) -> float:
    p = s.priors
    base = 0.5 * p.method_share["KO/TKO"]
    return (s.ko_loss_rate / base) * (1.0 + 0.5 * s.kd_absorbed_per15 / p.kd_per15) / 1.5


def _stance(a: FighterSnapshot, b: FighterSnapshot) -> float:
    sa, sb = (a.bio.stance or "").lower(), (b.bio.stance or "").lower()
    if sa == "southpaw" and sb == "orthodox":
        return 1.0
    if sb == "southpaw" and sa == "orthodox":
        return -1.0
    return 0.0


def matchup_features(a: FighterSnapshot, b: FighterSnapshot, ctx: BoutContext = BoutContext()) -> Dict[str, float]:
    five = ctx.scheduled_rounds >= 5
    reach = 0.0
    if a.bio.reach_cm is not None and b.bio.reach_cm is not None:
        reach = (a.bio.reach_cm - b.bio.reach_cm) / 10.0
    sub_a = a.sub_per15 * (b.sub_loss_rate / (0.5 * b.priors.method_share["SUB"]))
    sub_b = b.sub_per15 * (a.sub_loss_rate / (0.5 * a.priors.method_share["SUB"]))
    ra, rb = a.ratings, b.ratings

    def edge(att: str, dfn: str) -> float:
        """A's attack against B's defence minus the reverse, in rating points."""
        if not ra or not rb:
            return 0.0
        return (ra[att] - rb[dfn]) - (rb[att] - ra[dfn])

    return {
        # Damped by combined uncertainty: a gap between unproven ratings means less.
        "overall": _clip((a.elo - b.elo) / 400.0 * glicko_g(math.hypot(a.rd, b.rd))),
        "striking_rating": _clip((edge("strike_off", "strike_def") + edge("power", "chin")) / 800.0),
        "wrestling_rating": _clip(edge("td_off", "td_def") / 400.0),
        "grappling_rating": _clip((edge("control", "scramble") + edge("gnp", "scramble") + edge("sub_off", "sub_def")) / 1200.0),
        "striking_exchange": _clip((lands_on(a, b) - lands_on(b, a)) / 3.0),
        "striking_defense": _clip((a.str_def - b.str_def) * 10.0),
        "power_vs_chin": _clip(2.0 * (a.kd_per15 * chin_vulnerability(b) - b.kd_per15 * chin_vulnerability(a))),
        "wrestling_edge": _clip((takedowns_on(a, b) - takedowns_on(b, a)) / 2.0),
        "control": _clip(((a.ctrl_share - a.ctrl_against_share) - (b.ctrl_share - b.ctrl_against_share)) * 3.0),
        "submission_threat": _clip((sub_a - sub_b) / 1.5),
        "reach": _clip(reach, -2.0, 2.0),
        "age_curve": _clip(age_penalty(b.age) - age_penalty(a.age)),
        "wear_and_tear": _clip((wear_penalty(b) - wear_penalty(a)) / 3.0),
        "experience": _clip(log_experience(a.total_fights) - log_experience(b.total_fights)),
        "form": a.form - b.form,
        "layoff": layoff_penalty(b.layoff_days) - layoff_penalty(a.layoff_days),
        "chin_damage": float(b.recent_ko_losses - a.recent_ko_losses),
        "cardio": (a.late_win_rate - b.late_win_rate) * (2.0 if five else 1.0),
        "schedule_strength": _clip((a.sos - b.sos) / 200.0),
        # Fight Matrix Glicko rating (point in time); 0 unless both fighters have one.
        "outside_rating": _clip((a.ext_rating - b.ext_rating) / 400.0) if a.ext_rating is not None and b.ext_rating is not None else 0.0,
        # Size: log ratio of fighting weights in 5% steps (about a third of a division); 0 unless both
        # known. "size" is learned from bouts within about a division of each other; "size_gap" is the
        # part beyond 15% (more than a full division), which real bouts almost never reach, so its
        # weight is set from MMA knowledge (model.FIXED_WEIGHTS) rather than fitted.
        "size": _clip(_size_units(a, b)),
        "size_gap": _clip(math.copysign(max(0.0, abs(_size_units(a, b)) - 3.0), _size_units(a, b)), -10.0, 10.0),
        "height": (a.bio.height_cm - b.bio.height_cm) / 10.0 if a.bio.height_cm and b.bio.height_cm else 0.0,
        "stance": _stance(a, b),
    }
