"""Scouting reads for UFC Fight Night: Moicano vs. Nolan (Las Vegas, 2026-10-31).

logit: how far (log-odds, 0..0.8) the read moves the model toward `favours`, for what the model can't see.
The model's number at the time is recorded (p_model, toward a) so the read can be graded against it.
Drafted Tuesday 2026-10-27 from the reports and the picks sheet; finalized Friday 2026-10-30 after weigh-ins (all made
weight except Francis Marshall, 148 lb for the 146 lb featherweight limit) with the published pundit picks (101 picks
from 20 writers) in ufcmoicano_pundits.json and the fight-week news in ufcmoicano_fightweek.json.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
from mma_predictor.reads import Pundits, check_read  # noqa: E402

EVENT, DATE = "UFC Fight Night: Moicano vs. Nolan", "2026-10-31"
RESULTS = "https://en.wikipedia.org/wiki/UFC_Fight_Night:_Moicano_vs._Nolan"
CREATED = "2026-10-30T18:00:00+00:00"

# Model (stats only) and FanDuel no-vig numbers toward a, from the picks sheet of 2026-10-27 16:06 UTC.
# Erosa-Lee and Reese-Gall had no FanDuel line yet (and so no sheet row).
P = {
    ("Renato Moicano", "Tom Nolan"): (0.40, 0.519),
    ("Jacobe Smith", "Randy Brown"): (0.74, 0.685),
    ("Cody Durden", "Ode Osbourne"): (0.55, 0.50),
    ("Luana Santos", "Yana Santos"): (0.70, 0.696),
    ("Farman Hasanov", "Jean Paul Lebosnoyani"): (0.58, 0.299),
    ("Dakota Hope", "Francis Marshall"): (0.47, 0.319),
    ("Rodrigo Sezinando", "Theodor Berggren"): (0.68, 0.604),
    ("Julian Erosa", "Lee Jeong-yeong"): (None, None),
    ("Zachary Reese", "Mickey Gall"): (None, None),
    ("Joseph Kropschot", "Nick Klein"): (0.61, 0.723),
    ("Piera Rodriguez", "Talita Alencar"): (0.64, 0.701),
    ("Lucia Szabova", "Tainara Lisboa"): (0.89, 0.812),
}

READS = [
    dict(a="Renato Moicano", b="Tom Nolan", favours="Renato Moicano", logit=0.05, confidence="low",
         reasoning="The model has Moicano at 40% against an even market, which looks like age and his losses to big, strong "
                   "opponents. Nolan has never been past three rounds and is hittable early, and Moicano jumps on the back the "
                   "moment an opponent is hurt or scrambles. Against that, Nolan's size in the clinch, his August move to City "
                   "Kickboxing, his plan to ground-and-pound from the body triangle, and Moicano's fade when he spends time on "
                   "his back keep it very small; the pundits lean Nolan 9-7.",
         factors=["Moicano's back takes in scrambles", "Nolan untested past R3", "Nolan's size and clinch (against)", "Age 37 (against)"]),
    dict(a="Jacobe Smith", b="Randy Brown", favours="Jacobe Smith", logit=0.0, confidence="low",
         reasoning="Smith's wrestling and ground strikes are exactly what has beaten Brown (Battle, Belal), and Brown, 36, was "
                   "stopped by Bonfim last time; but Brown's guard is dangerous and Smith's defence is loose against a long puncher. "
                   "The model is already above the market on Smith; no lean.",
         factors=["Smith's wrestling vs Brown's takedown defence", "Brown's guard and range (against)", "Short notice for Smith"]),
    dict(a="Cody Durden", b="Ode Osbourne", favours="Cody Durden", logit=0.10, confidence="low",
         reasoning="Osbourne loses when he is taken down and held (Rodriguez, Erceg, Idiris), and Durden's whole game is takedowns "
                   "and control; Osbourne's counter left hand and Durden's habit of giving up his neck in scrambles keep it small.",
         factors=["Osbourne's takedown defence", "Durden's control", "Osbourne's counter power (against)", "Durden's submission defence (against)"]),
    dict(a="Luana Santos", b="Yana Santos", favours="Luana Santos", logit=0.0, confidence="low",
         reasoning="Yana takes the early rounds at range and has been taken down late; Luana's control is the better path over "
                   "15 minutes, and Yana is a year out at 37. Model and market agree near 70%; no lean.",
         factors=["Luana's top control", "Yana's late takedown defence", "Yana's layoff"]),
    dict(a="Farman Hasanov", b="Jean Paul Lebosnoyani", favours="Jean Paul Lebosnoyani", logit=0.30, confidence="low",
         reasoning="The model gives Hasanov 58% against a market at 30%, which looks like the unbeaten record. On tape he faded "
                   "from R2 in his only UFC fight while landing little damage, and Lebosnoyani is a front-running wrestle-boxer "
                   "with a guillotine in scrambles who won the late rounds of both UFC fights with takedowns. Hasanov's chain "
                   "wrestling can still steal round one.",
         factors=["Hasanov's cardio after R1", "Lebosnoyani's guillotine in scrambles", "Hasanov's chain wrestling (against)"]),
    dict(a="Dakota Hope", b="Francis Marshall", favours="Francis Marshall", logit=0.15, confidence="low",
         reasoning="Hope is a front-loaded power striker who faded in his UFC debut and now takes a second short-notice fight and "
                   "a cut back to featherweight; Marshall's takedowns and top control get better as opponents tire. Hope has never "
                   "been finished and Marshall's striking is inaccurate, so he has to get it down. Marshall missed weight by "
                   "2 lb, a small worry about his cut; Hope made 145.5.",
         factors=["Hope's R2-R3 cardio", "Marshall's top control", "Hope's short notice and weight cut", "Hope's early power (against)"]),
    dict(a="Rodrigo Sezinando", b="Theodor Berggren", favours="Rodrigo Sezinando", logit=0.0, confidence="low",
         reasoning="Two front-runners: Berggren has never won a decision and was dropped by body work in his debut, Sezinando "
                   "turns fights into clinch and takedowns but was knocked out by the only real puncher he faced and is 13 months "
                   "out. The model is above the market already; no lean.",
         factors=["Sezinando's clinch and takedowns", "Berggren's defence vs kicks and body work", "Sezinando's layoff (against)"]),
    dict(a="Julian Erosa", b="Lee Jeong-yeong", favours="Lee Jeong-yeong", logit=0.10, confidence="low",
         reasoning="Erosa, 37, has five R1 knockout losses to fast punchers and was stopped with three knockdowns in March; Lee "
                   "looks for the right hand early. Lee's 17-month layoff and the weight miss that scrapped his UFC 326 bout keep "
                   "it small, and Erosa's late scrambles and volume are real if it goes long. Erosa calls this his retirement "
                   "fight. Both made 145.5.",
         factors=["Erosa's chin against early power", "Lee's layoff and weight cut (against)", "Erosa's late scrambles (against)"]),
    dict(a="Zachary Reese", b="Mickey Gall", favours="Zachary Reese", logit=0.15, confidence="low",
         reasoning="Gall is nearly two years out, failed a medical in September, moves up to middleweight, and has been knocked out "
                   "in R1 in two of his last three; Reese finishes in round one. Reese's own early defensive lapses and Gall's "
                   "back takes keep it small. No line or model number yet.",
         factors=["Gall's layoff and medical flag", "Reese's R1 finishing", "Reese's early defensive lapses (against)"]),
    dict(a="Joseph Kropschot", b="Nick Klein", favours="Joseph Kropschot", logit=0.0, confidence="low",
         reasoning="Klein starts fast and has been stopped in R2 of both UFC fights; Kropschot is a submission finisher who has "
                   "won in R1 and R2, but this is his UFC debut and he was dropped on the Contender Series. Model and market "
                   "agree on Kropschot; no lean.",
         factors=["Klein's R2 fade", "Kropschot's debut (against)"]),
    dict(a="Piera Rodriguez", b="Talita Alencar", favours="Piera Rodriguez", logit=0.0, confidence="low",
         reasoning="Rodriguez's pressure and body knees win three-round fights, and Alencar is usually out-landed and fades late; "
                   "but Alencar's jiu-jitsu is the kind that caught Rodriguez before (the Robertson armbar). Model and market agree; "
                   "no lean.",
         factors=["Rodriguez's pressure and volume", "Alencar's submissions (against)"]),
    dict(a="Lucia Szabova", b="Tainara Lisboa", favours="Lucia Szabova", logit=0.0, confidence="low",
         reasoning="Lisboa has been finished late in her last two fights and is a year out at 36; Szabova finishes from the clinch "
                   "and mount and has gone five rounds. Her level of opposition is the only question, and the model is already "
                   "above the market; no lean.",
         factors=["Lisboa's late durability", "Szabova's competition level (against)"]),
]

# Picks published by Friday 2026-10-30 (outlet, author, pick, method, url).
PUNDIT_PICKS = [(r["a"], r["b"], r["outlet"], r["author"], r["pick"], r["method"], r["url"])
                for r in json.loads((Path(__file__).with_name("ufcmoicano_pundits.json")).read_text())]


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
(ROOT / "reads" / "2026-10-31-ufc-fight-night-moicano-vs-nolan.json").write_text(
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
