"""Written fighter bios, generated from the data.

Each bio reads a fighter's snapshot against the rest of their division
(same weight class and gender) and describes who they are, how they win and
lose, what they're best and worst at, and where their career is heading.
Researched background (data/scouting) is woven in where it exists. Bios
refer to fighters by name and "they" rather than guessing pronouns.
"""

from __future__ import annotations

from collections import Counter
from statistics import median
from typing import Dict, List, Optional, Sequence

from .data import Method
from .features import wear_index
from .history import FighterSnapshot
from .scouting import Background
from .skills import SUB_LABELS

DIVISION_WORDS = {"F": "Women's ", "M": ""}


def division_label(weight_class: str, gender: str) -> str:
    if not weight_class:
        return ""
    return (DIVISION_WORDS.get(gender, "") + weight_class).strip()


def _ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _list(items: Sequence[str]) -> str:
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def method_counts(s: FighterSnapshot) -> Dict[str, Counter]:
    wins: Counter = Counter()
    losses: Counter = Counter()
    for a in s.all_appearances:
        if a.result is True:
            wins[a.method.bucket] += 1
        elif a.result is False:
            losses[a.method.bucket] += 1
    return {"wins": wins, "losses": losses}


def write_bio(
    s: FighterSnapshot,
    peers: Sequence[FighterSnapshot],
    division: str = "",
    background: Optional[Background] = None,
) -> List[str]:
    """Paragraphs of prose about one fighter. ``peers`` are their division-mates."""
    name, first = s.name, s.name.split()[0]
    paras: List[str] = []

    # --- who they are
    div = division.lower()
    lead = f"{name} is a " + (f"{s.age:.0f}-year-old " if s.age else "") + (div or "mixed martial artist")
    if s.bio.nationality:
        lead += f" from {s.bio.nationality}"
    if s.bio.team:
        lead += f" who trains with {s.bio.team}"
    counts = method_counts(s)
    w, l = counts["wins"], counts["losses"]
    lead += f". The data has them at {s.record} as a pro"
    if sum(w.values()):
        parts = [f"{w[k]} by {lbl}" for k, lbl in (("KO/TKO", "knockout"), ("SUB", "submission"), ("DEC", "decision")) if w[k]]
        lead += f", with {_list(parts)} among the wins it has on record"
    lead += "."
    ranked = sorted(peers, key=lambda p: -p.elo)
    if division and len(ranked) >= 5 and s in ranked:
        pos = ranked.index(s) + 1
        lead += f" By overall rating they sit {_ordinal(pos)} of {len(ranked)} {div} fighters in this dataset."
    paras.append(lead)

    # --- style, strengths and weaknesses relative to the division
    if len(peers) >= 5 and s.ratings:
        med = {k: median(p.ratings[k] for p in peers) for k in s.ratings}
        edge = {k: s.ratings[k] - med[k] for k in s.ratings}
        best = [k for k, v in sorted(edge.items(), key=lambda kv: -kv[1]) if v > 25][:3]
        worst = [k for k, v in sorted(edge.items(), key=lambda kv: kv[1]) if v < -25][:2]
        cats = {"striking": s.striking, "wrestling": s.wrestling, "grappling": s.grappling}
        top_cat = max(cats, key=cats.get)
        style = f"{first}'s strongest category is {top_cat} ({cats[top_cat]:.0f})."
        if best:
            style += f" Against the division, the standout skills are {_list([SUB_LABELS[k].lower() for k in best])}."
        if worst:
            style += f" The weak spots are {_list([SUB_LABELS[k].lower() for k in worst])}, where they rate below the division middle."
        if not best and not worst:
            style += " No skill stands far above or below the division middle, so this reads as a well-rounded profile."
        paras.append(style)

    # --- how fights end
    finishes = []
    if sum(w.values()) >= 3:
        fin = (w["KO/TKO"] + w["SUB"]) / sum(w.values())
        finishes.append(f"they finish {fin:.0%} of their wins")
    if sum(l.values()) >= 2:
        if l["KO/TKO"]:
            finishes.append(f"{l['KO/TKO']} of their {sum(l.values())} losses came by KO/TKO")
        elif l["SUB"]:
            finishes.append(f"their losses have come on the mat rather than on the feet ({l['SUB']} by submission)")
    if s.recent_ko_losses >= 2:
        finishes.append(f"{s.recent_ko_losses} of their last three fights ended in a KO/TKO loss, a durability warning")
    if finishes:
        text = "; ".join(finishes)
        paras.append(text[0].upper() + text[1:] + ".")

    # --- trajectory
    if s.recent:
        last = s.recent[-1]
        res = {True: "beat", False: "lost to", None: "drew with"}[last.result]
        traj = f"Most recently, {first} {res} {last.opponent} ({last.fight.date.strftime('%b %Y')}, {last.method.value})"
        if s.streak >= 3:
            traj += f" to extend a {s.streak}-fight win streak"
        elif s.streak <= -2:
            traj += f", a {-s.streak}-fight losing skid"
        if s.layoff_days and s.layoff_days > 540:
            traj += f", and has been out of action for {s.layoff_days // 30} months since"
        paras.append(traj + ".")
    wear = wear_index(s)
    if s.age and s.age >= 34 and wear >= 3:
        paras.append(f"At {s.age:.0f} with heavy mileage (wear index {wear:.1f}), age-related decline is a real risk.")
    elif s.age and s.age <= 26 and s.fights >= 5:
        paras.append(f"At {s.age:.0f}, {first} is still well short of the usual athletic peak.")

    # --- researched background
    if background:
        bg = background.summary
        if background.credentials:
            creds = "; ".join(c.detail for c in background.credentials if c.detail)
            bg = (bg + " " if bg else "") + f"Credentials: {creds}."
        if bg:
            paras.append(bg)

    if s.fights < 4:
        paras.append(f"Only {s.fights} of {first}'s bouts are in this dataset, so treat the ratings above as provisional.")
    return paras
