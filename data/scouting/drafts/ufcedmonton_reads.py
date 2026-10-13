"""Scouting reads and pundit picks for UFC Fight Night: Buckley vs. Malott (UFC Edmonton, 2026-10-17).

logit: how far (log-odds, 0..0.8) the read moves the model toward `favours`, for what the model can't see.
The model's number at the time is recorded (p_model, toward a) so the read can be graded against it.
Tuesday draft, 2026-10-13, from the fight-week scouting reports; to be revisited after Friday's weigh-ins.
No pundit picks for this card were published at the time of writing.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
from mma_predictor.reads import Pundits, check_read  # noqa: E402

EVENT, DATE = "UFC Fight Night: Buckley vs. Malott", "2026-10-17"
RESULTS = "https://en.wikipedia.org/wiki/UFC_Fight_Night:_Buckley_vs._Malott"

# Model and FanDuel numbers when the reads were written (picks sheet, 2026-10-13 16:04 UTC), toward a.
# Jourdain-Cuamba and Chovancek-You are not on the sheet (no model number); Chovancek's market is from the odds sweep.
P = {  # (a, b): (p_model_a, p_fanduel_a no-vig)
    ("Joaquin Buckley", "Mike Malott"): (0.46, 0.468),
    ("Erin Blanchfield", "Jasmine Jasudavicius"): (0.74, 0.746),
    ("Cristian Perez", "Kyle Nelson"): (0.67, 0.746),
    ("Kyle Daukaus", "Marc-Andre Barriault"): (0.74, 0.654),
    ("Mandel Nallo", "Nate Landwehr"): (0.69, 0.726),
    ("Jhonata Diniz", "Tanner Boser"): (0.76, 0.704),
    ("Julien Leblanc", "Nick Galanti"): (0.32, 0.160),
    ("Javad Mahjoub", "Joel Faglier"): (0.40, 0.522),
    ("Katlyn Cerminara", "Mackenzie Stiller"): (0.55, 0.726),
    ("Chad Anheliger", "Steven Koslow"): (0.47, 0.512),
    ("Chelsea Chandler", "Melissa Croden"): (0.39, 0.293),
    ("Louis Jourdain", "Timothy Cuamba"): (None, None),
    ("Cody Chovancek", "You Su-young"): (None, 0.581),
}

READS = [
    dict(a="Joaquin Buckley", b="Mike Malott", favours="Mike Malott", logit=0.0, confidence="low",
         reasoning="Buckley's two straight losses came to elite wrestlers (Usman, Brady); Malott is a long kickboxer with submissions, not a "
                   "chain wrestler, so the fight Buckley lost twice isn't the obvious one here. Against that, Malott faded and was stopped late "
                   "by Magny and has never gone five rounds, and Buckley's power grows in rounds two and three. Home crowd for Malott. "
                   "Model and market agree; no lean.",
         factors=["Malott's five-round cardio (against)", "Buckley's trouble off his back", "Buckley's mid-fight power", "Home favourite"]),
    dict(a="Erin Blanchfield", b="Jasmine Jasudavicius", favours="Erin Blanchfield", logit=0.0, confidence="low",
         reasoning="Blanchfield's back takes punish the wrestling exchanges Jasudavicius needs, but she is nearly a year out and returning from "
                   "the injury that moved this fight from August. Jasudavicius said the delay disrupted her own camp. Model and market agree.",
         factors=["Blanchfield's grappling edge", "Blanchfield's layoff and injury (against)", "Jasudavicius's disrupted camp"]),
    dict(a="Cristian Perez", b="Kyle Nelson", favours="Cristian Perez", logit=0.10, confidence="low",
         reasoning="Nelson was finished in round one in both of his last two losses, most recently knocked out in 24 seconds in March, and is "
                   "in his mid-30s; Perez is a 27-year-old finisher. The model, which has no Contender Series data, sees less of Perez than "
                   "the market does. Perez's late-round cardio after wrestling keeps the lean small.",
         factors=["Nelson's recent first-round stoppages", "Age", "Perez's late cardio (against)"]),
    dict(a="Kyle Daukaus", b="Marc-Andre Barriault", favours="Kyle Daukaus", logit=0.0, confidence="low",
         reasoning="Daukaus's front-headlock game should find Barriault's neck when he presses, but his chin against forward pressure is the "
                   "question after the Nickal stoppage, and Barriault always brings volume. The model already sits above the market on Daukaus.",
         factors=["Daukaus's chokes vs Barriault's pressure", "Daukaus's durability (against)", "Barriault 1-5 in his last six"]),
    dict(a="Mandel Nallo", b="Nate Landwehr", favours="Mandel Nallo", logit=0.15, confidence="moderate",
         reasoning="Landwehr is 38, has been knocked out three straight times and moves up to lightweight against a longer first-round "
                   "finisher (12 of Nallo's 14 wins in round one). Nallo's own chin and cardio are shaky, but this matchup asks Landwehr to "
                   "walk forward into power with a shrinking chin.",
         factors=["Landwehr's three straight KO losses", "Landwehr moving up at 38", "Nallo's chin (against)"]),
    dict(a="Jhonata Diniz", b="Tanner Boser", favours="Jhonata Diniz", logit=0.0, confidence="low",
         reasoning="Diniz has the size and reach, and Boser has been hurt by bigger hitters; but Diniz is a year out and pulled out of a June "
                   "booking for undisclosed reasons, and Boser fights at home. The model is already above the market; no lean.",
         factors=["Size and reach", "Diniz's layoff and withdrawal (against)", "Boser at home"]),
    dict(a="Julien Leblanc", b="Nick Galanti", favours="Nick Galanti", logit=0.30, confidence="moderate",
         reasoning="Leblanc is 35, coming back from a knee that gave out on the first kick of his April debut (kneecap micro-fractures, two torn "
                   "ligaments), was submitted quickly once the fight hit the mat, and prepared for a different opponent. Galanti is a 28-year-old "
                   "submission grappler with new power. The model can't see the knee or the opponent switch.",
         factors=["Leblanc's knee injury", "Galanti's grappling vs Leblanc's ground defence", "Leblanc's late opponent switch"]),
    dict(a="Javad Mahjoub", b="Joel Faglier", favours="Javad Mahjoub", logit=0.10, confidence="low",
         reasoning="Faglier took this on two and a half weeks' notice for his UFC debut against regional opposition, and his top game runs "
                   "into a two-time Olympic judoka. Mahjoub's age (35) and thin MMA experience keep it small.",
         factors=["Faglier on short notice", "Mahjoub's Olympic judo", "Mahjoub's age and inexperience (against)"]),
    dict(a="Katlyn Cerminara", b="Mackenzie Stiller", favours="Katlyn Cerminara", logit=0.25, confidence="moderate",
         reasoning="Stiller is a strawweight moving up on under three weeks' notice, about 17 cm shorter, and her last 125-lb fight was a TKO "
                   "loss; on TUF she lost to a striker who out-landed her at range, which is Cerminara's whole game. Cerminara is 38 and 31 "
                   "months out, so not more.",
         factors=["Stiller on short notice and moving up", "Size and range", "Cerminara's age and layoff (against)"]),
    dict(a="Chad Anheliger", b="Steven Koslow", favours="Steven Koslow", logit=0.0, confidence="low",
         reasoning="Anheliger's takedown defence and submission losses (six of eight) suit a 10th Planet grappler, but Koslow hasn't fought in "
                   "nearly four years and has never shown three-round cardio. Two long layoffs cancel out; no lean.",
         factors=["Anheliger's takedown defence", "Koslow's four-year layoff (against)", "Anheliger's age and knee"]),
    dict(a="Chelsea Chandler", b="Melissa Croden", favours="Melissa Croden", logit=0.10, confidence="low",
         reasoning="Chandler has missed weight at 135 twice and says she has been fighting through injuries; Croden has never been finished "
                   "and builds late. Chandler's early power and armbar are the danger, so the lean stays small.",
         factors=["Chandler's weight cut and injuries", "Croden's durability and late pressure", "Chandler's early finishes (against)"]),
    dict(a="Louis Jourdain", b="Timothy Cuamba", favours="Louis Jourdain", logit=0.10, confidence="low",
         reasoning="Cuamba has been taken down and choked twice recently and is uncomfortable going backwards against counters; Jourdain is a "
                   "rangy counter-striker who finished on the Contender Series with a back-take. Jourdain's year out and regional schedule keep "
                   "it small. No model number for this bout.",
         factors=["Cuamba's back-take defence", "Jourdain's range and counters", "Jourdain's layoff (against)"]),
    dict(a="Cody Chovancek", b="You Su-young", favours="Cody Chovancek", logit=0.0, confidence="low",
         reasoning="You grinds decisions with chain wrestling and Chovancek's takedown defence against that volume is untested; Chovancek is "
                   "an unbeaten finisher who has gone five rounds twice, but he is 13 months out. No model number; no lean.",
         factors=["You's wrestling volume", "Chovancek's finishing and cardio", "Chovancek's layoff"]),
]

# Picks already published for this card (none found by Tuesday).
PUNDIT_PICKS = []

bouts = []
for r in READS:
    pm, pf = P[(r["a"], r["b"])]
    r.update(event=EVENT, date=DATE, p_model=pm, p_market=pf, created="2026-10-13T16:20:00+00:00",
             pundits=[{"outlet": o, "author": au, "pick": pk, "method": m, "url": u}
                      for a, b, o, au, pk, m, u in PUNDIT_PICKS if {a, b} == {r["a"], r["b"]}])
    check_read(r)
    bouts.append(r)
(ROOT / "reads").mkdir(exist_ok=True)
(ROOT / "reads" / "2026-10-17-ufc-fight-night-buckley-vs-malott.json").write_text(
    json.dumps({"event": EVENT, "date": DATE, "results_url": RESULTS, "bouts": bouts}, indent=1, ensure_ascii=False) + "\n")

if PUNDIT_PICKS:
    pun = Pundits(ROOT / "pundits.jsonl")
    for a, b, o, au, pk, m, u in PUNDIT_PICKS:
        pm, pf = P[(a, b)]
        p_pick = None if pf is None else (pf if pk == a else 1 - pf)
        pun.add({"event": EVENT, "date": DATE, "a": a, "b": b, "outlet": o, "author": au, "pick": pk, "method": m,
                 "url": u, "p_market": None if p_pick is None else round(p_pick, 3)})
    pun.save()
print(len(bouts), "reads;", len(PUNDIT_PICKS), "pundit picks")
