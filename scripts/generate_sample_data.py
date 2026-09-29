#!/usr/bin/env python3
"""Generate a SYNTHETIC demo dataset of fictional fighters.

Nothing here is real. Each fictional fighter gets hidden attributes
(striking, power, chin, wrestling, takedown defence, submissions, cardio,
reach, age) and bouts are simulated from them, so the dataset has learnable
structure for exercising the pipeline, the model and the backtester.
For real predictions, import real records (see README).

    python scripts/generate_sample_data.py [--out data/sample] [--seed 7]
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mma_predictor.data import fight_csv_header  # noqa: E402

FIRST = ["Aren", "Bodhi", "Cato", "Dario", "Emrys", "Fenn", "Galen", "Hollis", "Ivo", "Jory", "Kestrel", "Lazlo",
         "Marek", "Nilo", "Orrin", "Pax", "Quill", "Rune", "Soren", "Tamsin", "Ulric", "Vale", "Wren", "Xander",
         "Yusuf", "Zeke", "Anselm", "Brannoc", "Cyrus", "Dov", "Evander", "Faris", "Gideon", "Hale", "Idris", "Jasper"]
LAST = ["Ashgrove", "Blackthorn", "Coldwater", "Dunmore", "Emberly", "Fairholt", "Greywind", "Harrowgate", "Ironwood",
        "Juniper", "Kettleby", "Longmire", "Marchbank", "Northcott", "Oakhurst", "Pellow", "Quarry", "Ravensworth",
        "Stonebridge", "Thornbury", "Underhill", "Varga", "Westbrook", "Yarrow", "Zeller", "Ambrose", "Brightwater",
        "Crowhurst", "Delacroix-Venn", "Eastwick"]
CLASSES = [("Lightweight", 180), ("Welterweight", 185), ("Middleweight", 191), ("Light Heavyweight", 196)]


@dataclass
class Sim:
    name: str
    weight_class: str
    dob: date
    reach: float
    stance: str
    striking: float
    power: float
    chin: float
    wrestling: float
    td_def: float
    bjj: float
    cardio: float
    prior_w: int
    prior_l: int
    last_fight: date = date(1900, 1, 1)
    record: list = field(default_factory=list)
    retired: bool = False

    def age(self, when: date) -> float:
        return (when - self.dob).days / 365.25

    def decline(self, when: date) -> float:
        a = self.age(when)
        return max(0.0, a - 32) ** 1.5 * 0.08 + len([r for r in self.record if r == "KO_L"]) * 0.08


def make_fighter(rng: random.Random, used: set, wc: str, base_reach: float, debut: date) -> Sim:
    while True:
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        if name not in used:
            used.add(name)
            break
    age = rng.uniform(22, 31)
    g = lambda: rng.gauss(0, 1)  # noqa: E731
    style = rng.random()
    s = Sim(
        name=name,
        weight_class=wc,
        dob=debut - timedelta(days=int(age * 365.25)),
        reach=round(base_reach + rng.gauss(0, 5), 1),
        stance=rng.choices(["Orthodox", "Southpaw", "Switch"], [0.72, 0.22, 0.06])[0],
        striking=g() + (0.6 if style < 0.35 else 0),
        power=g(),
        chin=g(),
        wrestling=g() + (0.9 if 0.35 <= style < 0.6 else 0),
        td_def=g(),
        bjj=g() + (0.9 if 0.6 <= style < 0.75 else 0),
        cardio=g(),
        prior_w=rng.randint(4, 14),
        prior_l=rng.randint(0, 4),
    )
    s.record = []
    return s


def sigmoid(z: float) -> float:
    return 1 / (1 + math.exp(-z))


def effective(x: Sim, y: Sim, when: date, rounds: int) -> float:
    """How well x's attributes play against y's."""
    strike = 0.55 * x.striking + 0.15 * x.reach / 10 - 0.2 * y.striking
    wrestle = 0.45 * max(0.0, x.wrestling - y.td_def) + 0.1 * x.wrestling
    grapple = 0.25 * x.bjj * (1 if x.wrestling > y.td_def - 0.5 else 0.4)
    power = 0.3 * x.power - 0.25 * y.chin
    cardio = 0.15 * x.cardio * (1.6 if rounds == 5 else 1.0)
    stance = 0.08 if (x.stance == "Southpaw" and y.stance == "Orthodox") else 0.0
    return strike + wrestle + grapple + power + cardio + stance - x.decline(when)


def simulate_bout(rng: random.Random, a: Sim, b: Sim, when: date, rounds: int) -> dict:
    ea, eb = effective(a, b, when, rounds), effective(b, a, when, rounds)
    p_a = sigmoid(1.3 * (ea - eb))
    a_wins = rng.random() < p_a
    w, l = (a, b) if a_wins else (b, a)
    ko = math.exp(0.6 * w.power - 0.6 * l.chin + 0.3 * l.decline(when)) * 0.32
    sub = math.exp(0.7 * w.bjj - 0.3 * l.bjj + 0.2 * (w.wrestling - l.td_def)) * 0.19
    dec = 0.49 * (1.25 if rounds == 3 else 0.9)
    r = rng.random() * (ko + sub + dec)
    method = "KO/TKO" if r < ko else "SUB" if r < ko + sub else "DEC"
    if method == "DEC":
        end_round, secs = rounds, 300
        if rng.random() < 0.18:
            method = "S-DEC"
    else:
        weights = [1.4 ** -(i) for i in range(rounds)]
        end_round = rng.choices(range(1, rounds + 1), weights)[0]
        secs = rng.randint(10, 299)
    minutes = ((end_round - 1) * 300 + secs) / 60
    stats = {}
    for me, opp, px in ((a, b, "a"), (b, a, "b")):
        att = max(0, int(rng.gauss(8.5 + 1.8 * me.striking + 0.5 * me.cardio - 0.8 * max(0, opp.wrestling - me.td_def), 2) * minutes))
        acc = min(0.8, max(0.2, 0.45 + 0.05 * me.striking - 0.04 * opp.striking + rng.gauss(0, 0.05)))
        td_att = max(0, int(rng.gauss(0.35 + 0.35 * max(0, me.wrestling), 0.2) * minutes / 3 * 1.5 + 0.5))
        td_acc = min(0.9, max(0.05, 0.38 + 0.12 * (me.wrestling - opp.td_def)))
        td = sum(rng.random() < td_acc for _ in range(td_att))
        kd = sum(rng.random() < 0.02 * math.exp(0.6 * me.power - 0.4 * opp.chin) for _ in range(int(minutes)))
        if method == "KO/TKO" and me is w and kd == 0 and rng.random() < 0.6:
            kd = 1
        subs = sum(rng.random() < 0.035 * math.exp(0.8 * me.bjj) for _ in range(int(minutes)))
        if method == "SUB" and me is w:
            subs = max(1, subs)
        ctrl = int(min(minutes * 60 * 0.8, td * rng.uniform(40, 110)))
        stats.update({
            f"{px}_sig_landed": int(att * acc), f"{px}_sig_attempted": att, f"{px}_td_landed": td,
            f"{px}_td_attempted": td_att, f"{px}_sub_attempts": subs, f"{px}_knockdowns": kd, f"{px}_ctrl_seconds": ctrl,
        })
    # A noisy but informed betting market (4.5% vig).
    m = min(0.95, max(0.05, sigmoid(math.log(p_a / (1 - p_a)) * 0.85 + rng.gauss(0, 0.35))))
    odds = [_american(m * 1.045 / 1.0), _american((1 - m) * 1.045)]
    w.record.append("W")
    l.record.append("KO_L" if method == "KO/TKO" else "L")
    return {
        "winner": w.name, "method": method, "round": end_round, "time": f"{secs // 60}:{secs % 60:02d}",
        "a_odds": odds[0], "b_odds": odds[1], **stats,
    }


def _american(p: float) -> int:
    p = min(0.97, max(0.03, p))
    return int(round(-100 * p / (1 - p))) if p >= 0.5 else int(round(100 * (1 - p) / p))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "data" / "sample"))
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--years", type=int, default=7)
    ap.add_argument("--per-class", type=int, default=36)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    start = date(2019, 1, 12)
    used: set = set()
    roster = {wc: [make_fighter(rng, used, wc, reach, start) for _ in range(args.per_class)] for wc, reach in CLASSES}
    everyone = [f for fs in roster.values() for f in fs]
    rows = []
    when = start
    event_no = 1
    end = start + timedelta(days=int(365.25 * args.years))
    while when < end:
        card = []
        for wc, reach in CLASSES:
            pool = [f for f in roster[wc] if not f.retired and (when - f.last_fight).days >= 100]
            rng.shuffle(pool)
            # Matchmaking: pair fighters with similar recent success.
            pool.sort(key=lambda f: sum(1 if r == "W" else -1 for r in f.record[-4:]) + rng.gauss(0, 1.2))
            for i in range(0, min(len(pool) - 1, 6), 2):
                card.append((wc, pool[i], pool[i + 1]))
        for idx, (wc, a, b) in enumerate(card):
            main_event = idx == 0
            rounds = 5 if main_event else 3
            res = simulate_bout(rng, a, b, when, rounds)
            rows.append({
                "date": when.isoformat(), "event": f"Demo FC {event_no}", "weight_class": wc,
                "fighter_a": a.name, "fighter_b": b.name, "scheduled_rounds": rounds, "title_fight": 0, **res,
            })
            a.last_fight = b.last_fight = when
        for wc, reach in CLASSES:
            for f in roster[wc]:
                if not f.retired and (f.age(when) > 38.5 or f.record[-4:] == ["L", "L", "L", "L"] or f.record[-3:].count("KO_L") >= 2):
                    f.retired = True
                    newcomer = make_fighter(rng, used, wc, reach, when)
                    roster[wc].append(newcomer)
                    everyone.append(newcomer)
        when += timedelta(days=rng.choice([14, 21, 28]))
        event_no += 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "fighters.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "dob", "height_cm", "reach_cm", "stance", "prior_wins", "prior_losses"])
        for f in everyone:
            w.writerow([f.name, f.dob.isoformat(), round(f.reach - 2 + rng.gauss(0, 3), 1), f.reach, f.stance, f.prior_w, f.prior_l])
    with open(out / "fights.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fight_csv_header())
        w.writeheader()
        w.writerows(rows)

    # An "upcoming card" between active fighters for the card command.
    active = {wc: sorted([f for f in fs if not f.retired], key=lambda f: -f.record.count("W")) for wc, fs in roster.items()}
    with open(out / "upcoming_card.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["fighter_a", "fighter_b", "scheduled_rounds", "title_fight", "a_odds", "b_odds"])
        for i, (wc, fs) in enumerate(active.items()):
            w.writerow([fs[0].name, fs[1].name, 5 if i == 0 else 3, 1 if i == 0 else 0, "", ""])
            w.writerow([fs[2].name, fs[5].name, 3, 0, "", ""])
    print(f"Wrote {len(everyone)} fictional fighters and {len(rows)} bouts to {out}")


if __name__ == "__main__":
    main()
