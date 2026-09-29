"""Point-in-time fighter profiles.

``FightHistory.snapshot(name, as_of)`` rebuilds a fighter's attributes using
only bouts strictly before ``as_of``. Every rate statistic is shrunk toward a
population prior so a fighter with one bout doesn't look like a 90%-accurate
striker because of fifteen lucky minutes.
"""

from __future__ import annotations

import bisect
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from .data import METHOD_BUCKETS, FighterBio, Fight, Method
from .ratings import EloConfig, EloRatings
from .scouting import Scouting
from .skills import SkillConfig, SkillRatings


@dataclass(frozen=True)
class Priors:
    """Population averages (roughly UFC-level) and their pseudo-sample sizes."""

    slpm: float = 3.8  # significant strikes landed per minute
    sapm: float = 3.8  # absorbed per minute
    str_acc: float = 0.45
    str_def: float = 0.55
    td_per15: float = 1.3
    td_acc: float = 0.38
    td_def: float = 0.62
    sub_per15: float = 0.5
    kd_per15: float = 0.3
    ctrl_share: float = 0.18
    # Share of bouts ending by each method.
    method_share: Dict[str, float] = field(
        default_factory=lambda: {"KO/TKO": 0.32, "SUB": 0.19, "DEC": 0.49}
    )
    minutes_weight: float = 15.0  # one full three-round fight
    strikes_weight: float = 60.0
    td_weight: float = 6.0
    fights_weight: float = 3.0


DEFAULT_PRIORS = Priors()


@dataclass
class Appearance:
    """One bout from one fighter's perspective."""

    fight: Fight
    opponent: str
    result: Optional[bool]  # True win, False loss, None draw/NC
    opp_elo: float

    @property
    def method(self) -> Method:
        return self.fight.method


@dataclass
class FighterSnapshot:
    name: str
    as_of: date
    bio: FighterBio
    elo: float  # overall rating: weighted aggregate of the three category ratings
    fights: int  # bouts in the dataset before as_of
    wins: int
    losses: int
    age: Optional[float]
    minutes: float
    # Striking
    slpm: float
    sapm: float
    str_acc: float
    str_def: float
    kd_per15: float
    kd_absorbed_per15: float
    # Grappling
    td_per15: float
    td_acc: float
    td_def: float
    sub_per15: float
    ctrl_share: float
    ctrl_against_share: float
    # Outcomes
    win_methods: Dict[str, float]  # smoothed share of wins by method bucket
    loss_methods: Dict[str, float]  # smoothed share of losses by method bucket
    finish_rate: float  # smoothed share of wins that were finishes
    ko_loss_rate: float  # smoothed share of all bouts lost by KO/TKO
    sub_loss_rate: float
    recent_ko_losses: int  # KO/TKO losses in last 3 bouts
    late_win_rate: float  # win rate in bouts that reached round 3+
    five_round_fights: int
    # Momentum / activity
    form: float  # recency-weighted results in [-1, 1]
    streak: int  # +n win streak, -n losing streak
    layoff_days: Optional[int]
    sos: float  # mean opponent Elo entering the bout
    quality_win_elo: float  # mean opponent Elo in wins
    stat_minutes: float = 0.0  # minutes of bouts that carried per-corner stats
    ratings: Dict[str, float] = field(default_factory=dict)  # sub-ratings, see skills.SUB_RATINGS
    striking: float = 1500.0
    wrestling: float = 1500.0
    grappling: float = 1500.0
    pedigree: Dict[str, float] = field(default_factory=dict)  # background boost still counting
    # Wear and tear
    ko_losses: int = 0
    kd_absorbed: int = 0
    sig_absorbed: int = 0
    recent: List[Appearance] = field(default_factory=list, repr=False)

    @property
    def total_wins(self) -> int:
        return self.wins + self.bio.prior_wins

    @property
    def total_losses(self) -> int:
        return self.losses + self.bio.prior_losses

    @property
    def total_fights(self) -> int:
        return self.total_wins + self.total_losses

    @property
    def record(self) -> str:
        return f"{self.total_wins}-{self.total_losses}"


def _shrink(count: float, exposure: float, prior_rate: float, prior_weight: float) -> float:
    return (count + prior_rate * prior_weight) / (exposure + prior_weight)


def _dirichlet(counts: Dict[str, int], prior: Dict[str, float], weight: float) -> Dict[str, float]:
    total = sum(counts.values()) + weight
    return {k: (counts.get(k, 0) + prior[k] * weight) / total for k in METHOD_BUCKETS}


class FightHistory:
    def __init__(
        self,
        bios: Dict[str, FighterBio],
        fights: List[Fight],
        priors: Priors = DEFAULT_PRIORS,
        elo_config: EloConfig = EloConfig(),
        skill_config: SkillConfig = SkillConfig(),
        scouting: Optional[Scouting] = None,
        adjust_for_opponents: bool = True,
    ) -> None:
        self.bios = dict(bios)
        self.fights = sorted(fights, key=lambda f: f.date)
        self.priors = priors
        self.scouting = scouting or Scouting()
        self.adjust_for_opponents = adjust_for_opponents
        self.skills = SkillRatings(self.fights, self.bios, skill_config, self.scouting.boosts(), self.scouting.notes)
        self._raw_cache: Dict[tuple, Dict[str, float]] = {}
        # Classic single-number Elo, kept only as a backtest baseline.
        self.classic_elo = EloRatings(self.fights, self.bios, elo_config)
        self._apps: Dict[str, List[Appearance]] = defaultdict(list)
        self._app_dates: Dict[str, List[date]] = defaultdict(list)
        for f in self.fights:
            for me in (f.fighter_a, f.fighter_b):
                opp = f.opponent_of(me)
                result = None if f.winner is None else f.winner == me
                self._apps[me].append(Appearance(f, opp, result, self.skills.overall_before(opp, f.date)))
                self._app_dates[me].append(f.date)
            for name in (f.fighter_a, f.fighter_b):
                self.bios.setdefault(name, FighterBio(name=name))
        self._cache: Dict[tuple, FighterSnapshot] = {}

    # ------------------------------------------------------------------ lookup
    def names(self) -> List[str]:
        return sorted(self.bios)

    def resolve(self, name: str) -> str:
        """Case-insensitive / partial-name lookup."""
        if name in self.bios:
            return name
        low = name.lower().strip()
        exact = [n for n in self.bios if n.lower() == low]
        if exact:
            return exact[0]
        partial = [n for n in self.bios if low in n.lower()]
        if len(partial) == 1:
            return partial[0]
        if not partial:
            raise KeyError(f"unknown fighter: {name!r}")
        raise KeyError(f"ambiguous fighter {name!r}: {', '.join(sorted(partial)[:8])}")

    def appearances_before(self, name: str, as_of: date) -> List[Appearance]:
        idx = bisect.bisect_left(self._app_dates.get(name, []), as_of)
        return self._apps.get(name, [])[:idx]

    def last_date(self) -> date:
        return self.fights[-1].date if self.fights else date.today()

    def default_date(self) -> date:
        """'Now' for upcoming bouts: today, or the day after the data ends if later."""
        return max(date.today(), date.fromordinal(self.last_date().toordinal() + 1))

    # ---------------------------------------------------------------- snapshot
    def snapshot(self, name: str, as_of: Optional[date] = None) -> FighterSnapshot:
        if as_of is None:
            as_of = self.default_date()
        key = (name, as_of)
        if key not in self._cache:
            self._cache[key] = self._build(name, as_of)
        return self._cache[key]

    def _raw_rates(self, name: str, as_of: date) -> Dict[str, float]:
        """Unadjusted, shrunk striking/takedown rates (the baseline for opponent adjustment)."""
        key = (name, as_of)
        if key in self._raw_cache:
            return self._raw_cache[key]
        p = self.priors
        mins = sl = sa = att = opp_att = td = td_att = opp_td = opp_td_att = 0.0
        for app in self.appearances_before(name, as_of):
            own, opp = app.fight.stats_for(name)
            if own is None or opp is None:
                continue
            mins += app.fight.duration_seconds / 60.0
            sl += own.sig_landed
            att += own.sig_attempted
            sa += opp.sig_landed
            opp_att += opp.sig_attempted
            td += own.td_landed
            td_att += own.td_attempted
            opp_td += opp.td_landed
            opp_td_att += opp.td_attempted
        mw = p.minutes_weight
        out = {
            "slpm": _shrink(sl, mins, p.slpm, mw),
            "sapm": _shrink(sa, mins, p.sapm, mw),
            "str_acc": _shrink(sl, att, p.str_acc, p.strikes_weight),
            "str_def": 1.0 - _shrink(sa, opp_att, 1.0 - p.str_def, p.strikes_weight),
            "td_acc": _shrink(td, td_att, p.td_acc, p.td_weight),
            "td_def": 1.0 - _shrink(opp_td, opp_td_att, 1.0 - p.td_def, p.td_weight),
        }
        self._raw_cache[key] = out
        return out

    def _build(self, name: str, as_of: date) -> FighterSnapshot:
        p = self.priors
        bio = self.bios.get(name) or FighterBio(name=name)
        apps = self.appearances_before(name, as_of)

        minutes = stat_minutes = 0.0
        sl = sl_acc = sa = sig_att = opp_sl = opp_att = 0.0
        td = td_att = opp_td = opp_td_att = 0.0
        subs = kd = kd_abs = ctrl = ctrl_against = td_raw = ko_losses = sig_absorbed = 0
        wins = losses = 0
        win_m: Dict[str, int] = defaultdict(int)
        loss_m: Dict[str, int] = defaultdict(int)
        late_wins = late_total = five_rounders = 0
        opp_elos: List[float] = []
        win_elos: List[float] = []

        for app in apps:
            f = app.fight
            mins = f.duration_seconds / 60.0
            minutes += mins
            opp_elos.append(app.opp_elo)
            if f.scheduled_rounds >= 5:
                five_rounders += 1
            if app.result is True:
                wins += 1
                win_m[f.method.bucket] += 1
                win_elos.append(app.opp_elo)
            elif app.result is False:
                losses += 1
                loss_m[f.method.bucket] += 1
            if f.end_round >= 3 and app.result is not None:
                late_total += 1
                late_wins += int(app.result)
            if app.result is False and f.method is Method.KO:
                ko_losses += 1
            own, opp = f.stats_for(name)
            if own is None or opp is None:
                continue
            stat_minutes += mins
            sig_absorbed += opp.sig_landed
            # Opponent adjustment: judge each bout against what this opponent
            # usually allows / does. Landing 5 a minute on a fighter who
            # normally absorbs 2 is worth more than on one who absorbs 6.
            o = self._raw_rates(app.opponent, f.date) if self.adjust_for_opponents else None
            if o is None:
                o = {"slpm": p.slpm, "sapm": p.sapm, "str_acc": p.str_acc, "str_def": p.str_def,
                     "td_acc": p.td_acc, "td_def": p.td_def}
            sl += own.sig_landed - (o["sapm"] - p.sapm) * mins
            sl_acc += own.sig_landed - ((1 - o["str_def"]) - (1 - p.str_def)) * own.sig_attempted
            sig_att += own.sig_attempted
            sa += opp.sig_landed - (o["slpm"] - p.slpm) * mins
            opp_sl += opp.sig_landed - (o["str_acc"] - p.str_acc) * opp.sig_attempted
            opp_att += opp.sig_attempted
            td += own.td_landed - ((1 - o["td_def"]) - (1 - p.td_def)) * own.td_attempted
            td_att += own.td_attempted
            opp_td += opp.td_landed - (o["td_acc"] - p.td_acc) * opp.td_attempted
            opp_td_att += opp.td_attempted
            td_raw += own.td_landed
            subs += own.sub_attempts
            kd += own.knockdowns
            kd_abs += opp.knockdowns
            ctrl += own.ctrl_seconds
            ctrl_against += opp.ctrl_seconds

        mw = p.minutes_weight
        per15 = lambda count, prior: _shrink(count, stat_minutes / 15.0, prior, mw / 15.0)  # noqa: E731
        bouts = wins + losses
        fw = p.fights_weight
        ko_losses = loss_m.get("KO/TKO", 0)
        sub_losses = loss_m.get("SUB", 0)
        finish_wins = win_m.get("KO/TKO", 0) + win_m.get("SUB", 0)
        prior_finish = p.method_share["KO/TKO"] + p.method_share["SUB"]

        form, streak = _form(apps)
        last = apps[-1].fight.date if apps else None
        ratings = self.skills.before(name, as_of)
        cats = self.skills.breakdown(ratings)
        return FighterSnapshot(
            name=name,
            as_of=as_of,
            bio=bio,
            elo=cats["overall"],
            fights=len(apps),
            wins=wins,
            losses=losses,
            age=bio.age_on(as_of),
            minutes=minutes,
            slpm=max(0.3, _shrink(sl, stat_minutes, p.slpm, mw)),
            sapm=max(0.3, _shrink(sa, stat_minutes, p.sapm, mw)),
            str_acc=_unit(_shrink(sl_acc, sig_att, p.str_acc, p.strikes_weight)),
            str_def=_unit(1.0 - _shrink(opp_sl, opp_att, 1.0 - p.str_def, p.strikes_weight)),
            kd_per15=per15(kd, p.kd_per15),
            kd_absorbed_per15=per15(kd_abs, p.kd_per15),
            td_per15=per15(td_raw, p.td_per15),
            td_acc=_unit(_shrink(td, td_att, p.td_acc, p.td_weight)),
            td_def=_unit(1.0 - _shrink(opp_td, opp_td_att, 1.0 - p.td_def, p.td_weight)),
            sub_per15=per15(subs, p.sub_per15),
            ctrl_share=_shrink(ctrl / 60.0, stat_minutes, p.ctrl_share, mw),
            ctrl_against_share=_shrink(ctrl_against / 60.0, stat_minutes, p.ctrl_share, mw),
            win_methods=_dirichlet(win_m, p.method_share, fw),
            loss_methods=_dirichlet(loss_m, p.method_share, fw),
            finish_rate=_shrink(finish_wins, wins, prior_finish, fw),
            ko_loss_rate=_shrink(ko_losses, bouts, 0.5 * p.method_share["KO/TKO"], fw),
            sub_loss_rate=_shrink(sub_losses, bouts, 0.5 * p.method_share["SUB"], fw),
            recent_ko_losses=sum(1 for a in apps[-3:] if a.result is False and a.method is Method.KO),
            late_win_rate=_shrink(late_wins, late_total, 0.5, fw),
            five_round_fights=five_rounders,
            form=form,
            streak=streak,
            layoff_days=(as_of - last).days if last else None,
            sos=sum(opp_elos) / len(opp_elos) if opp_elos else self.skills.config.base,
            quality_win_elo=sum(win_elos) / len(win_elos) if win_elos else self.skills.config.base,
            stat_minutes=stat_minutes,
            ratings=ratings,
            striking=cats["striking"],
            wrestling=cats["wrestling"],
            grappling=cats["grappling"],
            pedigree=self.skills.pedigree(name, self.skills.bouts_before(name, as_of)),
            ko_losses=ko_losses,
            kd_absorbed=kd_abs,
            sig_absorbed=sig_absorbed,
            recent=apps[-5:],
        )


def _unit(x: float) -> float:
    return max(0.05, min(0.95, x))


def _form(apps: List[Appearance]) -> tuple:
    """Recency-weighted result score and current streak."""
    scored = [a for a in apps if a.result is not None]
    recent = scored[-3:]
    weights = [1.0, 2.0, 3.0][-len(recent):] if recent else []
    total = 0.0
    for w, a in zip(weights, recent):
        value = 1.0 if a.result else -1.0
        # A finish is a louder signal than a decision, in either direction.
        if a.method.is_finish:
            value *= 1.25
        total += w * value
    form = total / (sum(weights) * 1.25) if weights else 0.0
    streak = 0
    for a in reversed(scored):
        if streak == 0:
            streak = 1 if a.result else -1
        elif (streak > 0) == a.result:
            streak += 1 if streak > 0 else -1
        else:
            break
    return max(-1.0, min(1.0, form)), streak


def log_experience(n: int) -> float:
    return math.log1p(max(0, n))
