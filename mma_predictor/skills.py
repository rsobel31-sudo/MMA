"""Category skill ratings: Striking, Wrestling and Grappling.

Each fighter carries eleven sub-ratings on an Elo scale (1500 = average).
Most come in attack/defence pairs. The attacker's skill is measured against
the defender's matching skill, so beating a great wrestler's takedown
defence counts for more than beating a poor one's.

    STRIKING   strike_off  vs strike_def     accuracy and share of exchanges
               power       vs chin           knockdowns and KO/TKO wins
    WRESTLING  td_off      vs td_def         takedown success per attempt
    GRAPPLING  control     vs scramble       share of the fight spent on top
               gnp         vs scramble       ground strikes per control minute
               sub_off     vs sub_def        submission wins and attempts

A category rating is the mean of its sub-ratings, and the overall rating is
a weighted aggregate of the three categories (45% striking, 25% wrestling,
30% grappling by default). There is no separate single Elo.

Per bout, two kinds of evidence update the sub-ratings:

1. Stat evidence (when per-bout stats exist). For each attack/defence pair
   the expected outcome is

       expected = sigmoid(logit(base_rate) + ln(10)/400 * (attack - defence))

   and both sub-ratings move by

       delta = K_stat * weight * clip((observed - expected) / sd(base_rate), +-3)

   (attacker up, defender down). ``weight`` scales with the sample size
   (strikes thrown, takedown attempts, minutes of control).

2. Result evidence (every bout). Like classic Elo, the overall rating should
   move by K * margin * (result - expected_win), with
   expected_win = 1 / (1 + 10^((overall_B - overall_A) / 400)).
   That change is tilted toward the categories the bout was decided in: a
   KO/TKO toward striking, a submission toward grappling, and a decision in
   proportion to who won each domain on the stats (or a default split
   without stats). Category c's sub-ratings all move by

       step_c = change * (1 + 0.5 * (share_c / weight_c - 1))

   and because sum(weight_c * step_c) == change, the overall moves by
   exactly the classic Elo amount.
"""

from __future__ import annotations

import bisect
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple

from .data import CornerStats, FighterBio, Fight, Method, normalise_name
from .scouting import FightNote, notes_key

CATEGORIES: Dict[str, Tuple[str, ...]] = {
    "striking": ("strike_off", "strike_def", "power", "chin"),
    "wrestling": ("td_off", "td_def"),
    "grappling": ("control", "scramble", "gnp", "sub_off", "sub_def"),
}
SUB_RATINGS: Tuple[str, ...] = tuple(k for keys in CATEGORIES.values() for k in keys)
SUB_LABELS: Dict[str, str] = {
    "strike_off": "Striking offence",
    "strike_def": "Striking defence",
    "power": "Power",
    "chin": "Chin",
    "td_off": "Takedown offence",
    "td_def": "Takedown defence",
    "control": "Top control",
    "scramble": "Escapes / get-ups",
    "gnp": "Ground and pound",
    "sub_off": "Submission offence",
    "sub_def": "Submission defence",
}
C = math.log(10) / 400.0


def sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def logit(p: float) -> float:
    return math.log(p / (1.0 - p))


def per_fight_rate(rate_per15: float, minutes: float) -> float:
    """Chance an event with a given 15-minute rate happens in ``minutes``."""
    p = 1.0 - (1.0 - rate_per15) ** (max(minutes, 0.5) / 15.0)
    return min(0.6, max(0.02, p))


@dataclass(frozen=True)
class SkillConfig:
    base: float = 1500.0
    k_stat: float = 14.0
    k_result: float = 48.0  # tuned: best ranking agreement and backtest log-loss (see README)
    provisional_fights: int = 4
    provisional_multiplier: float = 1.75
    finish_multiplier: float = 1.3
    early_finish_bonus: float = 0.15
    split_multiplier: float = 0.6
    title_multiplier: float = 1.1
    regional_bonus_per_net_win: float = 8.0
    regional_bonus_cap: float = 80.0
    surprise_cap: float = 3.0
    # Share of the penalty an attacker takes for NOT finishing (see _pair).
    nonevent_weight: float = 0.4
    # Commentary evidence per note, and how slowly pedigree priors fade (bouts).
    k_note: float = 18.0
    pedigree_k: float = 10.0
    # Starting rating by the level of the promotion a fighter is first seen in, so
    # beating regional opponents counts for less than beating UFC fighters.
    tier_base: Dict[str, float] = field(default_factory=lambda: {"ufc": 1500.0, "major": 1470.0, "feeder": 1440.0, "regional": 1400.0})
    # 0 = every category moves equally with the result; 1 = fully by the shares below.
    attribution_strength: float = 0.5
    category_weights: Dict[str, float] = field(
        default_factory=lambda: {"striking": 0.45, "wrestling": 0.25, "grappling": 0.30}
    )
    # How a finish is attributed across categories.
    ko_shares: Dict[str, float] = field(default_factory=lambda: {"striking": 0.7, "wrestling": 0.1, "grappling": 0.2})
    sub_shares: Dict[str, float] = field(default_factory=lambda: {"striking": 0.1, "wrestling": 0.15, "grappling": 0.75})
    decision_shares: Dict[str, float] = field(default_factory=lambda: {"striking": 0.45, "wrestling": 0.25, "grappling": 0.30})
    # Base rates (UFC-ish).
    strike_acc: float = 0.45
    td_acc: float = 0.38
    ctrl_share: float = 0.15
    gnp_per_ctrl_min: float = 2.0
    kd_per15: float = 0.25  # chance of scoring >=1 knockdown in 15 min
    ko_win_per15: float = 0.16  # without stats: chance of a KO/TKO win
    sub_win_per15: float = 0.09
    sub_attempt_per15: float = 0.30
    # Rating uncertainty (Glicko). A newcomer starts unproven; each bout shrinks
    # the uncertainty by how informative it was, and beating someone far below
    # you is barely informative. Inactivity grows it back.
    rd_start: Dict[str, float] = field(default_factory=lambda: {"ufc": 250.0, "major": 280.0, "feeder": 300.0, "regional": 330.0})
    rd_floor: float = 45.0
    rd_growth_per_year: float = 45.0
    # Proven rating used for rankings = overall - rank_sigmas * uncertainty.
    rank_sigmas: float = 0.5
    # Stat evidence from a bout against a much weaker opponent is discounted:
    # full weight up to a 100-point gap, fading to 35% at a 300-point gap.
    mismatch_free_gap: float = 100.0
    mismatch_full_gap: float = 300.0
    mismatch_min_weight: float = 0.35
    # Recency: an uncertain rating (new, or after a layoff) moves faster, so the
    # latest results outweigh old ones. K is scaled by (RD / rd_k_ref)^2, clamped.
    rd_k_ref: float = 110.0
    rd_k_min: float = 0.8
    rd_k_max: float = 1.6


Ratings = Dict[str, float]
Q = math.log(10) / 400.0


def glicko_g(rd: float) -> float:
    """How much a rating difference counts given the uncertainty around it."""
    return 1.0 / math.sqrt(1.0 + 3.0 * Q * Q * rd * rd / (math.pi ** 2))


def glicko_expected(r: float, r_opp: float, rd_opp: float) -> float:
    return 1.0 / (1.0 + 10 ** (-glicko_g(rd_opp) * (r - r_opp) / 400.0))


_MAJOR = ("bellator", "pfl", "one championship", "one fc", "one:", "rizin", "strikeforce", "pride", "wec",
          "ksw", "m-1", "acb", "aca ", "dream", "affliction", "invicta", "professional fighters league")
_FEEDER = ("contender series", "lfa", "legacy fighting", "cage warriors", "cffc", "titan fc", "rfa", "ring of combat",
           "brave", "ares", "uae warriors", "oktagon", "eagle fc", "lux fight", "road to ufc", "ultimate fighter",
           "jungle fight", "shooto", "pancrase", "deep", "fury fc", "cage fury", "lfc", "hexagone")


def promotion_tier(event: str) -> str:
    """ufc | major | feeder | regional, from an event name like 'UFC 300 - ...'."""
    e = (event or "").lower().strip()
    if e.startswith("ufc") and "road to ufc" not in e:
        return "ufc"
    if any(k in e for k in _MAJOR):
        return "major"
    if any(k in e for k in _FEEDER):
        return "feeder"
    return "regional"


def category_rating(r: Ratings, cat: str) -> float:
    keys = CATEGORIES[cat]
    return sum(r[k] for k in keys) / len(keys)


def overall_rating(r: Ratings, weights: Dict[str, float]) -> float:
    total = sum(weights.values())
    return sum(w * category_rating(r, cat) for cat, w in weights.items()) / total


class SkillRatings:
    """Chronological sub-rating timelines for every fighter."""

    def __init__(
        self,
        fights: List[Fight],
        bios: Optional[Dict[str, FighterBio]] = None,
        config: SkillConfig = SkillConfig(),
        pedigree: Optional[Dict[str, Dict[str, float]]] = None,
        notes: Optional[List[FightNote]] = None,
    ) -> None:
        self.config = config
        self._bios = bios or {}
        self._pedigree = pedigree or {}
        self._notes: Dict[tuple, List[FightNote]] = defaultdict(list)
        for n in notes or []:
            # Sites disagree by a day on some dates (time zones), so index both neighbours.
            for shift in (-1, 0, 1):
                self._notes[notes_key(date.fromordinal(n.date.toordinal() + shift), n.fighter, n.opponent)].append(n)
        self._dates: Dict[str, List[date]] = defaultdict(list)
        self._values: Dict[str, List[Ratings]] = defaultdict(list)
        self._rds: Dict[str, List[float]] = defaultdict(list)
        self._counts: Dict[str, int] = defaultdict(int)
        ordered = sorted(fights, key=lambda f: f.date)
        self._first_event: Dict[str, str] = {}
        for f in ordered:
            for n in (f.fighter_a, f.fighter_b):
                self._first_event.setdefault(n, f.event or "UFC")
        current: Dict[str, Ratings] = {}
        for f in ordered:
            self._apply(f, current)

    # ---------------------------------------------------------------- lookup
    def initial(self, name: str) -> Ratings:
        """Evidence ratings before a fighter's first bout in the data (no pedigree)."""
        base = self.config.tier_base[promotion_tier(self._first_event.get(name, "UFC"))]
        bio = self._bios.get(name)
        if bio is not None:
            net = bio.prior_wins - bio.prior_losses
            cap = self.config.regional_bonus_cap
            base += max(-cap, min(cap, net * self.config.regional_bonus_per_net_win))
        return {k: base for k in SUB_RATINGS}

    def pedigree(self, name: str, bouts: int) -> Dict[str, float]:
        """The part of each rating that comes from background, fading with bouts."""
        boosts = self._pedigree.get(name)
        if not boosts:
            return {}
        fade = self.config.pedigree_k / (self.config.pedigree_k + bouts)
        return {k: v * fade for k, v in boosts.items()}

    def effective(self, name: str, raw: Ratings, bouts: int) -> Ratings:
        out = dict(raw)
        for k, v in self.pedigree(name, bouts).items():
            out[k] += v
        return out

    def before(self, name: str, when: date) -> Ratings:
        dates = self._dates.get(name)
        if not dates:
            return self.effective(name, self.initial(name), 0)
        idx = bisect.bisect_left(dates, when)
        raw = self._values[name][idx - 1] if idx else self.initial(name)
        return self.effective(name, raw, idx)

    # ------------------------------------------------------------ uncertainty
    def rd_initial(self, name: str) -> float:
        return self.config.rd_start[promotion_tier(self._first_event.get(name, "UFC"))]

    def rd_before(self, name: str, when: date) -> float:
        """Rating uncertainty entering a bout on ``when`` (grows with inactivity)."""
        dates = self._dates.get(name)
        cap = self.rd_initial(name)
        if not dates:
            return cap
        idx = bisect.bisect_left(dates, when)
        if idx == 0:
            return cap
        rd = self._rds[name][idx - 1]
        years = max(0, (when - dates[idx - 1]).days) / 365.25
        return min(cap, math.sqrt(rd * rd + self.config.rd_growth_per_year ** 2 * years))

    def proven(self, overall: float, rd: float) -> float:
        """Conservative rating for rankings: you have to prove it to be ranked by it."""
        return overall - self.config.rank_sigmas * (rd - self.config.rd_floor)

    def _rd_k(self, rd: float) -> float:
        cfg = self.config
        return max(cfg.rd_k_min, min(cfg.rd_k_max, (rd / cfg.rd_k_ref) ** 2))

    def _mismatch_weight(self, gap: float) -> float:
        cfg = self.config
        if gap <= cfg.mismatch_free_gap:
            return 1.0
        t = min(1.0, (gap - cfg.mismatch_free_gap) / (cfg.mismatch_full_gap - cfg.mismatch_free_gap))
        return 1.0 - t * (1.0 - cfg.mismatch_min_weight)

    def bouts_before(self, name: str, when: date) -> int:
        return bisect.bisect_left(self._dates.get(name, []), when)

    def current(self, name: str) -> Ratings:
        values = self._values.get(name)
        raw = values[-1] if values else self.initial(name)
        return self.effective(name, raw, len(values or []))

    def overall(self, r: Ratings) -> float:
        return overall_rating(r, self.config.category_weights)

    def overall_before(self, name: str, when: date) -> float:
        return self.overall(self.before(name, when))

    def breakdown(self, r: Ratings) -> Dict[str, float]:
        out = {cat: category_rating(r, cat) for cat in CATEGORIES}
        out["overall"] = self.overall(r)
        return out

    def leaderboard(self, names: Optional[List[str]] = None) -> List[Tuple[str, float]]:
        pool = names if names is not None else list(self._values)
        return sorted(((n, self.overall(self.current(n))) for n in pool), key=lambda t: -t[1])

    # --------------------------------------------------------------- updates
    def _k(self, name: str) -> float:
        if self._counts[name] < self.config.provisional_fights:
            return self.config.provisional_multiplier
        return 1.0

    def _pair(self, deltas, att: str, dfn: str, ra: Ratings, rd: Ratings, att_key: str, def_key: str,
              observed: float, base_rate: float, weight: float, k_scale: Tuple[float, float],
              finish_event: bool = False) -> None:
        cfg = self.config
        expected = sigmoid(logit(base_rate) + C * (ra[att_key] - rd[def_key]))
        z = (observed - expected) / math.sqrt(base_rate * (1.0 - base_rate))
        z = max(-cfg.surprise_cap, min(cfg.surprise_cap, z))
        d = cfg.k_stat * weight * z
        # Not finishing someone is weak evidence against the attacker (a grappler
        # can win on control without needing the tap), but surviving a dangerous
        # finisher is full evidence for the defender.
        att_scale = cfg.nonevent_weight if finish_event and d < 0 else 1.0
        deltas[att][att_key] += d * k_scale[0] * att_scale
        deltas[dfn][def_key] -= d * k_scale[1]

    def _stat_evidence(self, f: Fight, x: str, y: str, rx: Ratings, ry: Ratings, own: Optional[CornerStats],
                       opp: Optional[CornerStats], deltas, ks) -> None:
        """Evidence about x attacking y."""
        cfg = self.config
        minutes = f.duration_seconds / 60.0
        ko_win = f.winner == x and f.method is Method.KO
        sub_win = f.winner == x and f.method is Method.SUB
        if own is None or opp is None:
            # Records only: finishes are the one domain signal available.
            self._pair(deltas, x, y, rx, ry, "power", "chin", float(ko_win), per_fight_rate(cfg.ko_win_per15, minutes), 1.0, ks, True)
            self._pair(deltas, x, y, rx, ry, "sub_off", "sub_def", float(sub_win), per_fight_rate(cfg.sub_win_per15, minutes), 1.0, ks, True)
            return
        if own.sig_attempted > 0:
            self._pair(deltas, x, y, rx, ry, "strike_off", "strike_def", own.sig_landed / own.sig_attempted,
                       cfg.strike_acc, min(1.0, own.sig_attempted / 40.0), ks)
        knocked = own.knockdowns > 0 or ko_win
        self._pair(deltas, x, y, rx, ry, "power", "chin", float(knocked), per_fight_rate(cfg.kd_per15, minutes), 1.0, ks, True)
        if own.td_attempted > 0:
            self._pair(deltas, x, y, rx, ry, "td_off", "td_def", own.td_landed / own.td_attempted,
                       cfg.td_acc, min(1.0, own.td_attempted / 4.0), ks)
        if f.duration_seconds > 0:
            share = min(1.0, own.ctrl_seconds / f.duration_seconds)
            self._pair(deltas, x, y, rx, ry, "control", "scramble", share, cfg.ctrl_share, min(1.0, minutes / 10.0), ks)
        ctrl_min = own.ctrl_seconds / 60.0
        if own.ground_landed is not None and ctrl_min >= 0.5:
            rate = own.ground_landed / ctrl_min
            self._pair(deltas, x, y, rx, ry, "gnp", "scramble", rate / (rate + cfg.gnp_per_ctrl_min), 0.5,
                       min(1.0, ctrl_min / 3.0), ks)
        self._pair(deltas, x, y, rx, ry, "sub_off", "sub_def", float(sub_win), per_fight_rate(cfg.sub_win_per15, minutes), 1.0, ks, True)
        self._pair(deltas, x, y, rx, ry, "sub_off", "sub_def", float(own.sub_attempts > 0),
                   per_fight_rate(cfg.sub_attempt_per15, minutes), 0.5, ks, True)

    def _exchange(self, f: Fight, ra: Ratings, rb: Ratings, deltas, ka: float, kb: float) -> None:
        """Share of significant strikes landed: offence and defence of both fighters."""
        sa, sb = f.stats_a, f.stats_b
        if sa is None or sb is None or sa.sig_landed + sb.sig_landed == 0:
            return
        total = sa.sig_landed + sb.sig_landed
        edge = (ra["strike_off"] - rb["strike_def"]) - (rb["strike_off"] - ra["strike_def"])
        expected = sigmoid(C * edge / 2.0)
        z = max(-3.0, min(3.0, (sa.sig_landed / total - expected) / 0.5))
        d = self.config.k_stat * min(1.0, total / 60.0) * z / 2.0
        a, b = f.fighter_a, f.fighter_b
        deltas[a]["strike_off"] += d * ka
        deltas[a]["strike_def"] += d * ka
        deltas[b]["strike_off"] -= d * kb
        deltas[b]["strike_def"] -= d * kb

    def _shares(self, f: Fight) -> Dict[str, float]:
        cfg = self.config
        if f.method is Method.KO:
            return cfg.ko_shares
        if f.method is Method.SUB:
            return cfg.sub_shares
        sa, sb = f.stats_a, f.stats_b
        if sa is None or sb is None:
            return cfg.decision_shares
        # Decisions: weight each domain by how lopsided it was.
        def lopsided(x: float, y: float) -> float:
            return abs(x - y) / (x + y) if x + y > 0 else 0.0
        raw = {
            "striking": lopsided(sa.sig_landed, sb.sig_landed) + 0.15,
            "wrestling": lopsided(sa.td_landed, sb.td_landed) * 0.8 + 0.05,
            "grappling": lopsided(sa.ctrl_seconds, sb.ctrl_seconds) * 0.8 + 0.05,
        }
        total = sum(raw.values())
        return {k: v / total for k, v in raw.items()}

    def _margin(self, f: Fight) -> float:
        cfg = self.config
        if f.method.is_finish or f.method is Method.DQ:
            m = cfg.finish_multiplier + cfg.early_finish_bonus * max(0, f.scheduled_rounds - f.end_round)
        elif f.method is Method.SPLIT_DEC:
            m = cfg.split_multiplier
        else:
            m = 1.0
        return m * (cfg.title_multiplier if f.title_fight else 1.0)

    def _notes_evidence(self, f: Fight, ra: Ratings, rb: Ratings, deltas, ka: float, kb: float) -> None:
        """Commentary: a judged domain edge, scored against what the ratings expected."""
        for note in self._notes.get(notes_key(f.date, f.fighter_a, f.fighter_b), []):
            me_a = normalise_name(note.fighter) == normalise_name(f.fighter_a)
            x, y = (f.fighter_a, f.fighter_b) if me_a else (f.fighter_b, f.fighter_a)
            rx, ry = (ra, rb) if me_a else (rb, ra)
            kx, ky = (ka, kb) if me_a else (kb, ka)
            keys = [k for k in note.skills if k in CATEGORIES[note.category]] or list(CATEGORIES[note.category])
            mine = sum(rx[k] for k in keys) / len(keys)
            theirs = sum(ry[k] for k in keys) / len(keys)
            expected = sigmoid(C * (mine - theirs))
            observed = (note.rating + 2.0) / 4.0
            z = max(-3.0, min(3.0, (observed - expected) / 0.5))
            d = self.config.k_note * z
            for k in keys:
                deltas[x][k] += d * kx
                deltas[y][k] -= d * ky

    def _apply(self, f: Fight, current: Dict[str, Ratings]) -> None:
        if f.method is Method.NC:
            return
        cfg = self.config
        a, b = f.fighter_a, f.fighter_b
        raw_a = current.get(a) or self.initial(a)
        raw_b = current.get(b) or self.initial(b)
        # Expectations use the effective ratings (evidence + fading pedigree).
        ra = self.effective(a, raw_a, self._counts[a])
        rb = self.effective(b, raw_b, self._counts[b])
        oa, ob = self.overall(ra), self.overall(rb)
        rd_a, rd_b = self.rd_before(a, f.date), self.rd_before(b, f.date)
        ka, kb = self._k(a) * self._rd_k(rd_a), self._k(b) * self._rd_k(rd_b)
        deltas: Dict[str, Dict[str, float]] = {a: defaultdict(float), b: defaultdict(float)}

        # Dominating someone far below you says little about how you'd fare
        # against your peers, so that stat evidence counts for less.
        wa, wb = self._mismatch_weight(oa - ob), self._mismatch_weight(ob - oa)
        self._stat_evidence(f, a, b, ra, rb, f.stats_a, f.stats_b, deltas, (ka * wa, kb * wa))
        self._stat_evidence(f, b, a, rb, ra, f.stats_b, f.stats_a, deltas, (kb * wb, ka * wb))
        wx = min(wa, wb)
        self._exchange(f, ra, rb, deltas, ka * wx, kb * wx)
        self._notes_evidence(f, ra, rb, deltas, ka, kb)

        expected = sigmoid(C * (self.overall(ra) - self.overall(rb)))
        if f.winner is None:
            result, margin = 0.5, 1.0
        else:
            result, margin = (1.0 if f.winner == a else 0.0), self._margin(f)
        surprise = cfg.k_result * margin * (result - expected)
        weights = cfg.category_weights
        wsum = sum(weights.values())
        lam = cfg.attribution_strength
        for cat, share in self._shares(f).items():
            # Tilt the change toward the categories the bout was decided in. Because
            # sum(w * m) == 1, the overall still moves by exactly `surprise`.
            m = 1.0 + lam * (share * wsum / weights[cat] - 1.0)
            step = surprise * m
            for key in CATEGORIES[cat]:
                deltas[a][key] += step * ka
                deltas[b][key] -= step * kb

        # Glicko uncertainty: information from this bout is g(RD_opp)^2 * E * (1 - E),
        # which is tiny when the result was a foregone conclusion.
        new_rd = {}
        for me, rd_me, o_me, o_opp, rd_opp in ((a, rd_a, oa, ob, rd_b), (b, rd_b, ob, oa, rd_a)):
            e = glicko_expected(o_me, o_opp, rd_opp)
            info = Q * Q * glicko_g(rd_opp) ** 2 * e * (1.0 - e)
            new_rd[me] = max(cfg.rd_floor, math.sqrt(1.0 / (1.0 / (rd_me * rd_me) + info)))

        for name, r in ((a, raw_a), (b, raw_b)):
            new = {k: r[k] + deltas[name].get(k, 0.0) for k in SUB_RATINGS}
            current[name] = new
            self._dates[name].append(f.date)
            self._values[name].append(new)
            self._rds[name].append(new_rd[name])
            self._counts[name] += 1
