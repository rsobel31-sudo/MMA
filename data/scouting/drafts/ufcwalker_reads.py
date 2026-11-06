"""Scouting reads for UFC Fight Night: Cortes-Acosta vs. Walker (Las Vegas, 2026-11-07).

logit: how far (log-odds, 0..0.8) the read moves the model toward `favours`, for what the model can't see.
The model's number at the time is recorded (p_model, toward a) so the read can be graded against it.
Drafted Tuesday 2026-11-03 from the reports and the picks sheet. The card was Bonfim vs. Brady until Sean Brady withdrew
injured on Oct 29. Finalized Friday 2026-11-06 after weigh-ins (no misses reported; Lourenco 234, Petersen 253.5) with
162 published pundit picks (ufcwalker_pundits.json). Carlos Calderon replaced Lucas Brennan (torn ACL) against Austin
Bashi on four days' notice.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
from mma_predictor.reads import Pundits, check_read  # noqa: E402

EVENT, DATE = "UFC Fight Night: Cortes-Acosta vs. Walker", "2026-11-07"
RESULTS = "https://en.wikipedia.org/wiki/UFC_Fight_Night:_Cortes-Acosta_vs._Walker"
CREATED = "2026-11-06T18:30:00+00:00"

# Model (stats only) and FanDuel no-vig numbers toward a, from the picks sheet of 2026-11-06 17:54 UTC (finalized Friday).
# Ko-Turman has no FanDuel line; the model number is from the card-picks draft.
P = {
    ("Johnny Walker", "Waldo Cortes-Acosta"): (0.18, 0.320),
    ("Tatiana Suarez", "Virna Jandiroba"): (0.57, 0.645),
    ("Davey Grant", "Elijah Smith"): (0.25, 0.280),
    ("Billy Elekana", "Lucas Fernando"): (0.44, 0.272),
    ("Nina Milosevic", "Priscila Cachoeira"): (0.88, 0.793),
    ("Marcos Degli", "Mitch Raposo"): (0.72, 0.664),
    ("Keiichiro Nakamura", "Ollie Schmid"): (0.85, 0.752),
    ("Gabriel Lorenco", "Thomas Petersen"): (0.60, 0.400),
    ("Gabriella Fernandes", "Karine Silva"): (0.35, 0.340),
    ("Jose Delano", "Murtazali Magomedov"): (0.45, 0.519),
    ("Austin Bashi", "Carlos Calderon"): (0.57, 0.806),
    ("Andre Petroski", "Mantas Kondratavicius"): (0.22, 0.285),
    ("Jonny Parsons", "Jose Souza"): (0.32, 0.336),
    ("Ko Seok-hyeon", "Wellington Turman"): (0.76, None),
}

READS = [
    dict(a="Johnny Walker", b="Waldo Cortes-Acosta", favours="Waldo Cortes-Acosta", logit=0.0, confidence="low",
         reasoning="Walker has been knocked out when opponents force the issue and now faces heavyweight power; Cortes-Acosta "
                   "is the bigger, more active man. The model (18%) is already below the market (32%) on Walker; no lean.",
         factors=["Walker's chin against heavyweight power", "Walker freezes under pressure", "Walker's reach and explosiveness (against)"]),
    dict(a="Tatiana Suarez", b="Virna Jandiroba", favours="Tatiana Suarez", logit=0.10, confidence="low",
         reasoning="Jandiroba has mostly been the one shooting in her fights, and Suarez is one of the best takedown artists in "
                   "the division; only Zhang has stopped her wrestling. Jandiroba has never been stopped and is dangerous off "
                   "her back, and Suarez's injury history and late fade keep it small.",
         factors=["Suarez's wrestling vs Jandiroba's takedown defence", "Jandiroba's submissions (against)",
                  "Suarez's injury history (against)"]),
    dict(a="Davey Grant", b="Elijah Smith", favours="Elijah Smith", logit=0.0, confidence="low",
         reasoning="Grant is 40 against a 23-year-old finisher, but he has never been knocked out and his volume wins late rounds; "
                   "Smith tends to give up round one. Model and market agree near 75% for Smith; no lean.",
         factors=["Age gap", "Grant's durability and volume (against)"]),
    dict(a="Billy Elekana", b="Lucas Fernando", favours="Lucas Fernando", logit=0.10, confidence="low",
         reasoning="The model has Elekana at 45% against a market at 28%. Fernando's busy, rangy kicking is the style that out-"
                   "works Elekana's low-output counter game, and Elekana was dropped by Tafa and broken down by Guskov's body "
                   "work. Fernando's short turnaround (third fight since late May) and Elekana's chokes after he hurts someone "
                   "keep it small.",
         factors=["Fernando's volume vs Elekana's output", "Elekana's body-work problem", "Fernando's turnaround (against)"]),
    dict(a="Andre Petroski", b="Mantas Kondratavicius", favours="Andre Petroski", logit=0.10, confidence="low",
         reasoning="Kondratavicius ran out of steam in R3 of his only UFC fight, and a grinding wrestler is the worst style for a "
                   "fader. But Petroski has been knocked out in his last two and Kondratavicius hits hard early, so the lean is "
                   "small.",
         factors=["Kondratavicius's cardio past 10 minutes", "Petroski's takedowns and control", "Petroski's chin (against)"]),
    dict(a="Gabriel Lorenco", b="Thomas Petersen", favours="Gabriel Lorenco", logit=0.0, confidence="low",
         reasoning="Petersen took this on about two weeks' notice, three and a half months after a 92-second leg-lock loss, and "
                   "gets stopped by stronger strikers. The model (60%) is already well above the market (41%) on Lourenco; no "
                   "further lean.",
         factors=["Petersen's short notice", "Petersen's wrestling (against)"]),
    dict(a="Gabriella Fernandes", b="Karine Silva", favours="Karine Silva", logit=0.0, confidence="low",
         reasoning="Fernandes is coming off an R1 knockout loss and gets held down by grapplers; Silva is 1-3 in her last four "
                   "and struggles to get fights down against good takedown defence. Model and market agree; no lean.",
         factors=["Fernandes's bottom game", "Silva's recent form (against)"]),
    dict(a="Marcos Degli", b="Mitch Raposo", favours="Marcos Degli", logit=0.0, confidence="low",
         reasoning="Degli is a finisher on a 13-fight streak making his UFC debut; Raposo is durable and mobile and has gone the "
                   "distance in all four UFC fights. Model and market agree; no lean.",
         factors=["Degli's debut", "Raposo's durability (against)"]),
    dict(a="Jose Delano", b="Murtazali Magomedov", favours="Murtazali Magomedov", logit=0.0, confidence="low",
         reasoning="Magomedov has finished all eleven opponents but has less than three minutes of UFC cage time and has never "
                   "been past R3 or behind. A near coin flip in both model and market; no lean.",
         factors=["Magomedov untested late", "Magomedov's finishing (both ways)"]),
    dict(a="Keiichiro Nakamura", b="Ollie Schmid", favours="Keiichiro Nakamura", logit=0.0, confidence="low",
         reasoning="Nakamura is a knockout puncher who came from behind to win Road to UFC; he gives away early rounds and is "
                   "nine months out. The model is already above the market; no lean.",
         factors=["Nakamura's power", "Nakamura's layoff and slow starts (against)"]),
    dict(a="Nina Milosevic", b="Priscila Cachoeira", favours="Nina Milosevic", logit=0.0, confidence="low",
         reasoning="Cachoeira is 38, 1-5 since 2023 and has been submitted five times in the UFC; her R1 power is the only path. "
                   "The model is already above the market; no lean.",
         factors=["Cachoeira's form and bottom game", "Cachoeira's R1 power (against)"]),
    dict(a="Jonny Parsons", b="Jose Souza", favours="Jose Souza", logit=0.15, confidence="low",
         reasoning="Parsons is 35 and has not fought in about 40 months, with repeated hip flexor and groin problems and two "
                   "bookings that never happened. The model can't see a layoff that long; the market agrees with it at 33%, but "
                   "ring rust and his body after that time out lean further toward Souza.",
         factors=["Parsons's 40-month layoff and injuries", "Age 35", "Parsons's Muay Thai (against)"]),
    dict(a="Austin Bashi", b="Carlos Calderon", favours="Austin Bashi", logit=0.30, confidence="low",
         reasoning="The model has Bashi at 57% against a market at 81%. Calderon, the Fury FC featherweight champion, took this "
                   "on four days' notice and the model knows little of his regional opposition; a short-notice debut against a "
                   "wrestler who made weight on a full camp is the kind of gap the stats can't see. Calderon's submissions in "
                   "scrambles and Bashi's late-round fade in both UFC losses keep it from being larger.",
         factors=["Calderon on four days' notice", "Calderon's thin data", "Bashi's late fade (against)", "Calderon's submissions (against)"]),
    dict(a="Ko Seok-hyeon", b="Wellington Turman", favours="Ko Seok-hyeon", logit=0.15, confidence="low",
         reasoning="Turman has not fought since December 2023, had four shoulder surgeries in the layoff, and lost his last three; "
                   "Ko's judo takedowns and top control won his first two UFC fights. Turman's grappling and early rounds keep "
                   "it small. No FanDuel line.",
         factors=["Turman's three-year layoff and shoulder surgeries", "Ko's takedowns and control", "Turman's jiu-jitsu (against)"]),
]

# Picks published by Friday 2026-11-06 (outlet, author, pick, method, url): 162 picks from 16 outlets.
PUNDIT_PICKS = [(r["a"], r["b"], r["outlet"], r["author"], r["pick"], r["method"], r["url"])
                for r in json.loads((Path(__file__).with_name("ufcwalker_pundits.json")).read_text())]


def _p(a, b):
    """The (model, market) pair toward a, whichever way round the bout is listed."""
    if (a, b) in P:
        return P[(a, b)]
    pm, pf = P[(b, a)]
    return (None if pm is None else 1 - pm, None if pf is None else 1 - pf)


bouts = []
for r in READS:
    pm, pf = P[(r["a"], r["b"])]
    r.update(event=EVENT, date=DATE, p_model=pm, p_market=pf, created=CREATED,
             pundits=[{"outlet": o, "author": au, "pick": pk, "method": m, "url": u}
                      for a, b, o, au, pk, m, u in PUNDIT_PICKS if {a, b} == {r["a"], r["b"]}])
    check_read(r)
    bouts.append(r)
(ROOT / "reads" / "2026-11-07-ufc-fight-night-cortes-acosta-vs-walker.json").write_text(
    json.dumps({"event": EVENT, "date": DATE, "results_url": RESULTS, "bouts": bouts}, indent=1, ensure_ascii=False) + "\n")
if PUNDIT_PICKS:
    pun = Pundits(ROOT / "pundits.jsonl")
    for a, b, o, au, pk, m, u in PUNDIT_PICKS:
        pm, pf = _p(a, b)
        p_pick = None if pf is None else (pf if pk == a else 1 - pf)
        pun.add({"event": EVENT, "date": DATE, "a": a, "b": b, "outlet": o, "author": au, "pick": pk, "method": m,
                 "url": u, "p_market": None if p_pick is None else round(p_pick, 3)})
    pun.save()
print(len(bouts), "reads;", len(PUNDIT_PICKS), "pundit picks")
