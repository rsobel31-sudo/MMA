"""MMA-tuned Elo ratings.

Differences from vanilla Elo:

* Dominant results move ratings more than close ones (a first-round KO says
  more than a split decision).
* Newcomers are provisional: their K-factor is larger for their first few
  fights so the rating converges quickly.
* Fighters debuting with a strong regional record start slightly above the
  baseline rating.
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

from .data import FighterBio, Fight, Method


@dataclass(frozen=True)
class EloConfig:
    base: float = 1500.0
    k: float = 32.0
    provisional_fights: int = 4
    provisional_multiplier: float = 1.75
    finish_multiplier: float = 1.3
    early_finish_bonus: float = 0.15  # extra per round the finish came early
    split_multiplier: float = 0.6
    title_multiplier: float = 1.1
    regional_bonus_per_net_win: float = 8.0
    regional_bonus_cap: float = 80.0


def expected_score(r_a: float, r_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((r_b - r_a) / 400.0))


class EloRatings:
    """Computes a rating timeline for every fighter from a chronological fight list."""

    def __init__(
        self,
        fights: List[Fight],
        bios: Optional[Dict[str, FighterBio]] = None,
        config: EloConfig = EloConfig(),
    ) -> None:
        self.config = config
        self._bios = bios or {}
        self._dates: Dict[str, List[date]] = defaultdict(list)
        self._values: Dict[str, List[float]] = defaultdict(list)
        self._counts: Dict[str, int] = defaultdict(int)
        current: Dict[str, float] = {}
        for fight in sorted(fights, key=lambda f: f.date):
            self._apply(fight, current)

    def initial_rating(self, name: str) -> float:
        bio = self._bios.get(name)
        if bio is None:
            return self.config.base
        net = bio.prior_wins - bio.prior_losses
        bonus = max(-self.config.regional_bonus_cap, min(self.config.regional_bonus_cap, net * self.config.regional_bonus_per_net_win))
        return self.config.base + bonus

    def _k(self, name: str) -> float:
        k = self.config.k
        if self._counts[name] < self.config.provisional_fights:
            k *= self.config.provisional_multiplier
        return k

    def _margin(self, fight: Fight) -> float:
        cfg = self.config
        if fight.method.is_finish or fight.method is Method.DQ:
            early = max(0, fight.scheduled_rounds - fight.end_round)
            m = cfg.finish_multiplier + cfg.early_finish_bonus * early
        elif fight.method is Method.SPLIT_DEC:
            m = cfg.split_multiplier
        else:
            m = 1.0
        if fight.title_fight:
            m *= cfg.title_multiplier
        return m

    def _apply(self, fight: Fight, current: Dict[str, float]) -> None:
        if fight.method is Method.NC:
            return
        a, b = fight.fighter_a, fight.fighter_b
        r_a = current.get(a, self.initial_rating(a))
        r_b = current.get(b, self.initial_rating(b))
        e_a = expected_score(r_a, r_b)
        if fight.winner is None:
            s_a, margin = 0.5, 1.0
        else:
            s_a = 1.0 if fight.winner == a else 0.0
            margin = self._margin(fight)
        new_a = r_a + self._k(a) * margin * (s_a - e_a)
        new_b = r_b + self._k(b) * margin * ((1 - s_a) - (1 - e_a))
        for name, value in ((a, new_a), (b, new_b)):
            current[name] = value
            self._dates[name].append(fight.date)
            self._values[name].append(value)
            self._counts[name] += 1

    def rating_before(self, name: str, when: date) -> float:
        """Rating entering a bout on ``when`` (same-day results excluded)."""
        dates = self._dates.get(name)
        if not dates:
            return self.initial_rating(name)
        idx = bisect.bisect_left(dates, when)
        if idx == 0:
            return self.initial_rating(name)
        return self._values[name][idx - 1]

    def current(self, name: str) -> float:
        values = self._values.get(name)
        return values[-1] if values else self.initial_rating(name)

    def leaderboard(self, names: Optional[List[str]] = None) -> List[Tuple[str, float]]:
        pool = names if names is not None else list(self._values)
        return sorted(((n, self.current(n)) for n in pool), key=lambda t: -t[1])
