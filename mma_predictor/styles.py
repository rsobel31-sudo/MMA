"""Style classification and matchup pattern detection.

The model features quantify matchups. This module turns the same attributes
into readable scouting notes: what kind of fighter each is, and which known
matchup patterns apply (wrestler vs poor takedown defence, power vs a
compromised chin, a five-round fight against a fader, age cliffs, ring rust).
"""

from __future__ import annotations

from typing import List

from .features import BoutContext, lands_on, takedowns_on
from .history import FighterSnapshot


def classify(s: FighterSnapshot) -> str:
    P = s.priors
    wrestling = s.td_per15 / P.td_per15 + s.ctrl_share / P.ctrl_share
    grappling = s.sub_per15 / P.sub_per15
    striking = s.slpm / P.slpm
    power = s.kd_per15 / P.kd_per15
    tags = []
    if wrestling >= 3.0:
        tags.append("wrestler")
    if grappling >= 2.0:
        tags.append("submission grappler")
    if striking >= 1.25:
        tags.append("volume striker")
    if power >= 1.8:
        tags.append("power puncher")
    if s.str_def >= P.str_def + 0.05 and s.sapm <= P.sapm * 0.8:
        tags.append("defensive/technical")
    if s.td_def >= 0.78 and striking >= 1.0:
        tags.append("anti-wrestler")
    if not tags:
        tags.append("well-rounded")
    return ", ".join(tags)


def scouting_line(s: FighterSnapshot) -> str:
    age = f"{s.age:.0f}y" if s.age is not None else "age ?"
    reach = f"{s.bio.reach_cm:.0f}cm reach" if s.bio.reach_cm else "reach ?"
    return (
        f"{s.name} ({s.record}, rating {s.elo:.0f} [S {s.striking:.0f} / W {s.wrestling:.0f} / G {s.grappling:.0f}], "
        f"{age}, {reach}, {s.bio.stance or 'stance ?'}) - {classify(s)}. "
        f"Strikes {s.slpm:.1f} landed / {s.sapm:.1f} absorbed per min ({s.sig_diff5:+.1f} per 5 min) at {s.str_acc:.0%} acc, {s.str_def:.0%} def; "
        f"TD {s.td_per15:.1f}/15 at {s.td_acc:.0%}, TD def {s.td_def:.0%}; subs {s.sub_per15:.1f}/15; "
        f"finish rate {s.finish_rate:.0%}; form {s.form:+.2f} (streak {s.streak:+d})."
    )


def matchup_insights(a: FighterSnapshot, b: FighterSnapshot, ctx: BoutContext = BoutContext()) -> List[str]:
    notes: List[str] = []
    for x, y in ((a, b), (b, a)):
        notes.extend(_one_way(x, y, ctx))
    if a.fights < 3 or b.fights < 3:
        few = [s.name for s in (a, b) if s.fights < 3]
        notes.append(f"Limited data on {', '.join(few)} (<3 bouts in dataset); profile leans on population averages.")
    return notes


def _one_way(x: FighterSnapshot, y: FighterSnapshot, ctx: BoutContext) -> List[str]:
    out: List[str] = []
    tds = takedowns_on(x, y)
    if x.td_per15 >= 2.0 and y.td_def <= 0.6:
        out.append(
            f"Wrestling path: {x.name} averages {x.td_per15:.1f} TD/15 and {y.name} defends only "
            f"{y.td_def:.0%} -> projects ~{tds:.1f} takedowns per 15 min."
        )
    if x.td_per15 >= 2.0 and y.td_def >= 0.8:
        out.append(f"{y.name}'s {y.td_def:.0%} takedown defence neutralises much of {x.name}'s wrestling.")
    if x.kd_per15 >= 0.5 and (y.recent_ko_losses >= 1 or y.ko_loss_rate >= 0.25):
        out.append(
            f"Power vs chin: {x.name} scores {x.kd_per15:.2f} knockdowns/15 and {y.name} has "
            f"{y.recent_ko_losses} KO loss(es) in the last 3 ({y.ko_loss_rate:.0%} of bouts lost by KO)."
        )
    if x.sub_per15 >= 1.0 and y.sub_loss_rate >= 0.12:
        out.append(f"Submission threat: {x.name} attempts {x.sub_per15:.1f} subs/15 and {y.name} has been tapped before.")
    lx, ly = lands_on(x, y), lands_on(y, x)
    if lx - ly >= 1.5:
        out.append(f"Striking volume: projected {lx:.1f} vs {ly:.1f} significant strikes per minute in {x.name}'s favour.")
    if ctx.scheduled_rounds >= 5 and x.late_win_rate - y.late_win_rate >= 0.15:
        out.append(
            f"Five rounds favour {x.name}: {x.late_win_rate:.0%} win rate in fights reaching round 3+ vs {y.late_win_rate:.0%}."
        )
    if x.age is not None and y.age is not None and y.age >= 35 and y.age - x.age >= 5:
        out.append(f"Age: {y.name} is {y.age:.0f} facing a {x.age:.0f}-year-old; decline risk is real past 35.")
    if y.layoff_days is not None and y.layoff_days >= 500:
        out.append(f"Ring rust: {y.name} has been out {y.layoff_days // 30} months.")
    if x.bio.reach_cm and y.bio.reach_cm and x.bio.reach_cm - y.bio.reach_cm >= 10:
        out.append(f"Reach: {x.name} has a {x.bio.reach_cm - y.bio.reach_cm:.0f}cm reach advantage.")
    if (x.bio.stance or "").lower() == "southpaw" and (y.bio.stance or "").lower() == "orthodox":
        out.append(f"Stance: southpaw {x.name} vs orthodox {y.name} (open-stance exchanges).")
    if x.streak >= 4:
        out.append(f"Momentum: {x.name} is on a {x.streak}-fight win streak.")
    if x.sos - y.sos >= 100:
        out.append(f"Competition level: {x.name}'s opponents averaged {x.sos:.0f} Elo vs {y.sos:.0f} for {y.name}'s.")
    return out
