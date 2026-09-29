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

from .history import DEFAULT_PRIORS, FighterSnapshot, log_experience

P = DEFAULT_PRIORS


@dataclass(frozen=True)
class BoutContext:
    scheduled_rounds: int = 3
    title_fight: bool = False


FEATURES: List[str] = [
    "elo",
    "striking_exchange",
    "striking_defense",
    "power_vs_chin",
    "wrestling_edge",
    "control",
    "submission_threat",
    "reach",
    "age_curve",
    "experience",
    "form",
    "layoff",
    "chin_damage",
    "cardio",
    "schedule_strength",
    "stance",
]

FEATURE_LABELS: Dict[str, str] = {
    "elo": "overall rating (Elo)",
    "striking_exchange": "projected striking exchanges",
    "striking_defense": "striking defence",
    "power_vs_chin": "knockdown power vs opponent's chin",
    "wrestling_edge": "takedown offence vs opponent's takedown defence",
    "control": "top control time",
    "submission_threat": "submission threat",
    "reach": "reach",
    "age_curve": "age / athletic prime",
    "experience": "experience",
    "form": "recent form",
    "layoff": "ring rust (layoff)",
    "chin_damage": "accumulated KO damage",
    "cardio": "cardio / late-round performance",
    "schedule_strength": "strength of schedule",
    "stance": "stance matchup",
}


def _clip(x: float, lo: float = -3.0, hi: float = 3.0) -> float:
    return max(lo, min(hi, x))


def age_penalty(age: Optional[float]) -> float:
    """Athletic decline curve: flat through the prime, accelerating after ~33."""
    if age is None:
        return 0.0
    penalty = max(0.0, age - 32.0) ** 1.5 / 10.0
    if age < 24:  # very young fighters are often still raw
        penalty += (24.0 - age) * 0.05
    return penalty


def layoff_penalty(days: Optional[int]) -> float:
    if days is None:
        return 0.0
    return min(2.5, max(0.0, days - 400) / 365.0)


def lands_on(attacker: FighterSnapshot, defender: FighterSnapshot) -> float:
    """Projected significant strikes per minute ``attacker`` lands on ``defender``."""
    hittable = (1.0 - defender.str_def) / (1.0 - P.str_def)
    return attacker.slpm * hittable


def takedowns_on(attacker: FighterSnapshot, defender: FighterSnapshot) -> float:
    """Projected takedowns per 15 minutes."""
    porous = (1.0 - defender.td_def) / (1.0 - P.td_def)
    return attacker.td_per15 * porous


def chin_vulnerability(s: FighterSnapshot) -> float:
    base = 0.5 * P.method_share["KO/TKO"]
    return (s.ko_loss_rate / base) * (1.0 + 0.5 * s.kd_absorbed_per15 / P.kd_per15) / 1.5


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
    sub_a = a.sub_per15 * (b.sub_loss_rate / (0.5 * P.method_share["SUB"]))
    sub_b = b.sub_per15 * (a.sub_loss_rate / (0.5 * P.method_share["SUB"]))
    return {
        "elo": _clip((a.elo - b.elo) / 400.0),
        "striking_exchange": _clip((lands_on(a, b) - lands_on(b, a)) / 3.0),
        "striking_defense": _clip((a.str_def - b.str_def) * 10.0),
        "power_vs_chin": _clip(2.0 * (a.kd_per15 * chin_vulnerability(b) - b.kd_per15 * chin_vulnerability(a))),
        "wrestling_edge": _clip((takedowns_on(a, b) - takedowns_on(b, a)) / 2.0),
        "control": _clip(((a.ctrl_share - a.ctrl_against_share) - (b.ctrl_share - b.ctrl_against_share)) * 3.0),
        "submission_threat": _clip((sub_a - sub_b) / 1.5),
        "reach": _clip(reach, -2.0, 2.0),
        "age_curve": _clip(age_penalty(b.age) - age_penalty(a.age)),
        "experience": _clip(log_experience(a.total_fights) - log_experience(b.total_fights)),
        "form": a.form - b.form,
        "layoff": layoff_penalty(b.layoff_days) - layoff_penalty(a.layoff_days),
        "chin_damage": float(b.recent_ko_losses - a.recent_ko_losses),
        "cardio": (a.late_win_rate - b.late_win_rate) * (2.0 if five else 1.0),
        "schedule_strength": _clip((a.sos - b.sos) / 200.0),
        "stance": _stance(a, b),
    }
