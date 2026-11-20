"""Scouting reads for UFC Fight Night: Procházka vs. Stirling (Doha, 2026-11-21).

logit: how far (log-odds, 0..0.8) the read moves the model toward `favours`, for what the model can't see.
The model's number at the time is recorded (p_model, toward a) so the read can be graded against it.
Drafted Tuesday 2026-11-10 from the reports and the picks sheet. Finalized Friday 2026-11-13 after weigh-ins (Terrance
McKinney 160.2 for a lightweight bout, his first miss; Juan Diaz 0.4 lb over; everyone else on weight, Gane 242.6 and
Hokit 231.4) with 131 published pundit picks from 12 outlets (ufc334_pundits.json).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
from mma_predictor.reads import Pundits, check_read  # noqa: E402

EVENT, DATE = "UFC Fight Night: Procházka vs. Stirling", "2026-11-21"
RESULTS = "https://en.wikipedia.org/wiki/UFC_Fight_Night:_Proch%C3%A1zka_vs._Stirling"
CREATED = "2026-11-20T18:00:00+00:00"

# Model (stats only) and FanDuel no-vig numbers toward a, from the picks sheet of 2026-11-20 17:40 UTC.
P = {
    ('Jiri Prochazka', 'Navajo Stirling'): (0.33, 0.397),
    ('Aljamain Sterling', 'Kevin Vallejos'): (0.45, 0.454),
    ('Brian Ortega', 'Dan Hooker'): (0.62, 0.375),
    ('Asu Almabayev', 'Kyoji Horiguchi'): (0.49, 0.378),
    ('Ikram Aliskerov', 'Jared Cannonier'): (0.84, 0.715),
    ('Aleksandre Topuria', 'Santiago Luna'): (0.4, 0.707),
    ('Shamil Gaziev', 'Tallison Teixeira'): (0.39, 0.645),
    ('Alessandro Costa', 'Amir Albazi'): (0.44, 0.509),
    ('Jake Matthews', 'Tahir Abdullayev'): (0.49, 0.685),
    ('Dom Mar Fan', 'Nikolas Motta'): (0.67, 0.6),
    ('Alik Lorenz', 'Diyar Nurgozhay'): (0.26, 0.315),
    ('John Mitchell', 'Shoaib Yousaf'): (0.43, 0.563),
}

READS = [
    dict(a="Jiri Prochazka", b="Navajo Stirling", favours="Navajo Stirling", logit=0.0, confidence="low",
         reasoning="Procházka has been knocked out in three of his last four against top opposition and is 34; Stirling is "
                   "unbeaten but has never gone past three rounds in the UFC and was hurt in his last two. Model and market "
                   "both favour Stirling; no lean until fight week.",
         factors=["Procházka's recent knockout losses", "Stirling's first five-rounder (against)", "Procházka's power (against)"]),
    dict(a="Aljamain Sterling", b="Kevin Vallejos", favours="Aljamain Sterling", logit=0.0, confidence="low",
         reasoning="Sterling's back-taking against a puncher who has never faced an elite grappler, but Sterling is 37 and has "
                   "been knocked out by explosive strikers. Model and market agree on a near coin flip; no lean.",
         factors=["Sterling's grappling", "Vallejos's power (against)", "Sterling's age (against)"]),
    dict(a="Brian Ortega", b="Dan Hooker", favours="Dan Hooker", logit=0.15, confidence="low",
         reasoning="The model has Ortega at 62% against a market at 38%. It can't see that Ortega has been out about 15 months, "
                   "pulled out of two bookings this year with injuries, and moves up to lightweight for the first time. "
                   "Hooker's three straight stoppage losses and quick turnaround keep the lean small.",
         factors=["Ortega's 15-month layoff and two withdrawals", "Ortega's first fight at 155", "Hooker's durability (against)"]),
    dict(a="Asu Almabayev", b="Kyoji Horiguchi", favours="Kyoji Horiguchi", logit=0.0, confidence="low",
         reasoning="Almabayev's grappling against Horiguchi's speed and takedown defence; Horiguchi is 36 and was stopped by Kape "
                   "in R3. The model is above the market on Almabayev; no lean.",
         factors=["Horiguchi's takedown defence", "Almabayev's grappling (against)"]),
    dict(a="Ikram Aliskerov", b="Jared Cannonier", favours="Ikram Aliskerov", logit=0.0, confidence="low",
         reasoning="Aliskerov's wrestling against a 42-year-old who has lost four of five with very low output lately. The model "
                   "is already above the market; no lean.",
         factors=["Cannonier's age and form", "Aliskerov's wrestling", "Cannonier's power early (against)"]),
    dict(a="Aleksandre Topuria", b="Santiago Luna", favours="Aleksandre Topuria", logit=0.0, confidence="low",
         reasoning="A big gap: the model has Topuria at 41%, the market at 71%. Topuria is nearly a year out and was hobbled by "
                   "leg kicks; Luna is 22 and was submitted from the bottom by Mitchell. Too little evidence to lean against "
                   "either number; revisit with the previews.",
         factors=["Topuria's layoff (against)", "Luna's bottom game"]),
    dict(a="Shamil Gaziev", b="Tallison Teixeira", favours="Shamil Gaziev", logit=0.0, confidence="low",
         reasoning="Two heavyweights who have been knocked out quickly; both finish inside two rounds. Model 39%, market 63% on "
                   "Gaziev; no lean.",
         factors=["Both chins", "Teixeira's cardio past R1"]),
    dict(a="Alessandro Costa", b="Amir Albazi", favours="Alessandro Costa", logit=0.10, confidence="low",
         reasoning="Albazi has lost two straight decisions, fights once a year or less after heart and spine surgery, and has "
                   "landed 2 of 20 takedowns in his last three; Costa has finished three straight in 2026. Albazi's knockout of "
                   "Costa in their first fight keeps it small.",
         factors=["Albazi's inactivity and health history", "Costa's form", "Albazi's previous knockout of Costa (against)"]),
    dict(a="Jake Matthews", b="Tahir Abdullayev", favours="Jake Matthews", logit=0.10, confidence="low",
         reasoning="The model has Matthews at 49% against a market at 69%. Abdullayev, a pound over at 172, has one UFC fight and a regional record that "
                   "differs by source, so his numbers rest on weak opposition; Matthews has 24 UFC fights and won his last "
                   "clearly. Matthews fading in R3 scrambles keeps it small.",
         factors=["Abdullayev's thin UFC data", "Matthews's experience", "Matthews's late fades (against)"]),
    dict(a="Dom Mar Fan", b="Nikolas Motta", favours="Dom Mar Fan", logit=0.10, confidence="low",
         reasoning="Motta returns from 17 months out after a broken jaw that needed titanium plates, and has little ground game "
                   "against a grappler. Fan's leg-lock loss to Steele keeps it small.",
         factors=["Motta's layoff and jaw injury", "Fan's grappling", "Fan's submission defence (against)"]),
    dict(a="Alik Lorenz", b="Diyar Nurgozhay", favours="Diyar Nurgozhay", logit=0.0, confidence="low",
         reasoning="Lorenz debuts with nearly every fight ending in R1 either way; Nurgozhay has won two straight. Model and market "
                   "agree; no lean.",
         factors=["Lorenz's debut", "Nurgozhay's submission defence (against)"]),
    dict(a="John Mitchell", b="Shoaib Yousaf", favours="John Mitchell", logit=0.0, confidence="low",
         reasoning="Two 31-year-old debutants signed four days out. Mitchell is the boxer with PFL experience; Yousaf has knocked "
                   "out his last three in R1 and has never been stopped. Little film either way; no lean.",
         factors=["Both on short notice", "Yousaf's early power (against)"]),
]
# Picks published by Friday 2026-11-20 (outlet, author, pick, method, url): 99 picks from 11 outlets.
PUNDIT_PICKS = [(r["a"], r["b"], r["outlet"], r["author"], r["pick"], r["method"], r["url"])
                for r in json.loads((Path(__file__).with_name("ufcprochazka_pundits.json")).read_text())]


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
(ROOT / "reads" / "2026-11-21-ufc-fight-night-prochazka-vs-stirling.json").write_text(
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
