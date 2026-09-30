"""Men's and women's MMA as separate sports.

Men and women never share a cage, so their fight graphs are disjoint and
ratings never mix. What a single model *does* share across them is the base
rates (women's UFC bouts end by KO/TKO about half as often: 18% vs 35%, and
go the distance 64% vs 46% of the time) and the learned feature weights.

``split_histories`` builds one ``FightHistory`` per sport with priors and
rating base rates estimated from that sport's own UFC bouts, and
``backtest --split-sports`` trains a separate model on each. Tested on
3,923 UFC bouts, the split did not beat the pooled model (see README), so
the pooled model stays the default and this is kept to re-test as data grows.
"""

from __future__ import annotations

import dataclasses
from collections import Counter
from typing import Dict, List, Optional, Tuple

from .data import Fight, FighterBio, METHOD_BUCKETS
from .history import DEFAULT_PRIORS, FightHistory, Priors
from .scouting import Scouting
from .skills import SkillConfig

SPORTS = {"M": "Men's", "F": "Women's"}


def sport_of(fight: Fight, bios: Dict[str, FighterBio]) -> str:
    """'M' or 'F' from the fighters' genders ('M' when neither is known)."""
    for name in (fight.fighter_a, fight.fighter_b):
        bio = bios.get(name)
        if bio and bio.gender in SPORTS:
            return bio.gender
    return "M"


def base_rates(fights: List[Fight], smoothing: float = 20.0) -> Tuple[Dict[str, float], float, float]:
    """(method shares, KO/TKO wins per fighter per 15 min, submission wins per fighter per 15 min) in UFC bouts.

    Shares are smoothed toward the pooled defaults by ``smoothing`` bouts so a
    small sample can't produce a zero rate.
    """
    decided = [f for f in fights if f.winner and f.event.lower().startswith("ufc")] or [f for f in fights if f.winner]
    n = len(decided)
    if not n:
        return dict(DEFAULT_PRIORS.method_share), 0.0, 0.0
    methods = Counter(f.method.bucket for f in decided)
    fighter_15s = 2 * sum(f.duration_seconds for f in decided) / 900.0
    prior = DEFAULT_PRIORS.method_share
    return ({m: (methods[m] + smoothing * prior[m]) / (n + smoothing) for m in METHOD_BUCKETS},
            methods["KO/TKO"] / fighter_15s, methods["SUB"] / fighter_15s)


def sport_settings(sport_fights: List[Fight], all_fights: List[Fight]) -> Tuple[Priors, SkillConfig]:
    """Priors and rating base rates scaled from the pooled defaults by this sport's finish rates."""
    shares, ko, sub = base_rates(sport_fights)
    _, ko_all, sub_all = base_rates(all_fights)
    rk = ko / ko_all if ko_all else 1.0
    rs = sub / sub_all if sub_all else 1.0
    cfg = SkillConfig()
    priors = dataclasses.replace(DEFAULT_PRIORS, method_share=shares, kd_per15=DEFAULT_PRIORS.kd_per15 * rk)
    cfg = dataclasses.replace(cfg, ko_win_per15=cfg.ko_win_per15 * rk, sub_win_per15=cfg.sub_win_per15 * rs,
                              kd_per15=cfg.kd_per15 * rk)
    return priors, cfg


def split_histories(
    bios: Dict[str, FighterBio], fights: List[Fight], scouting: Optional[Scouting] = None
) -> Dict[str, FightHistory]:
    """One FightHistory per sport, each with its own base rates."""
    out: Dict[str, FightHistory] = {}
    for sport in SPORTS:
        fs = [f for f in fights if sport_of(f, bios) == sport]
        if not fs:
            continue
        names = {f.fighter_a for f in fs} | {f.fighter_b for f in fs}
        priors, cfg = sport_settings(fs, fights)
        out[sport] = FightHistory({n: b for n, b in bios.items() if n in names}, fs,
                                  priors=priors, skill_config=cfg, scouting=scouting)
    return out
