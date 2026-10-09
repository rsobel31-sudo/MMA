"""Scouting reads and pundit picks for UFC Fight Night: Allen vs. Duncan (UFC Vegas 122, 2026-10-10).

logit: how far (log-odds, 0..0.8) the read moves the model toward `favours`, for what the model can't see.
The model's number at the time is recorded (p_model, toward a) so the read can be graded against it.
Written Friday 2026-10-09 during weigh-ins (no misses reported at the time of writing).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
from mma_predictor.reads import Pundits, check_read  # noqa: E402

EVENT, DATE = "UFC Fight Night: Allen vs. Duncan", "2026-10-10"
RESULTS = "https://en.wikipedia.org/wiki/UFC_Fight_Night:_Allen_vs._Duncan"

# Model and FanDuel numbers when the reads were written (picks sheet, 2026-10-09 16:01 UTC), toward a.
P = {  # (a, b): (p_model_a, p_fanduel_a no-vig)
    ("Brendan Allen", "Christian Leroy Duncan"): (0.45, 0.546),
    ("Jai Herbert", "Matheus Camilo"): (0.32, 0.370),
    ("Ketlen Souza", "Lupita Godinez"): (0.45, 0.320),
    ("Andre Fili", "Kai Kamaka III"): (0.29, 0.578),
    ("Malcolm Wellmaker", "Otari Tanzilovi"): (0.38, 0.664),
    ("Gerald Meerschaert", "Julius Walker"): (0.20, 0.283),
    ("Francisco Prado", "Ismael Bonfim"): (0.49, 0.524),
    ("Leon Shahbazyan", "Niko Price"): (0.64, 0.568),
    ("Brendson Ribeiro", "Felipe Franco"): (0.17, 0.244),
    ("Allen Frye", "Richard Harris"): (0.35, 0.272),
    ("Alice Pereira", "Darya Zheleznyakova"): (0.57, 0.563),
    ("Ernesta Kareckaite", "Melissa Gatto"): (0.42, 0.489),
}

READS = [
    dict(a="Brendan Allen", b="Christian Leroy Duncan", favours="Brendan Allen", logit=0.15, confidence="moderate",
         reasoning="Five rounds favour Allen: he wins by making opponents carry his weight and breaking them late, and Duncan has never been past "
                   "round three as a pro. Duncan's knees and kicks are a real early danger (Allen himself says Duncan 'better catch me early'), "
                   "and his grappling defense is the open question. The market already leans Allen; the model, short on Duncan's five-round "
                   "data, doesn't.",
         factors=["Five rounds vs Duncan's untested cardio", "Allen's top game vs Duncan's grappling defense", "Duncan's early striking (against)"]),
    dict(a="Jai Herbert", b="Matheus Camilo", favours="Matheus Camilo", logit=0.10, confidence="moderate",
         reasoning="A 25-year-old wrestler landing about three takedowns per 15 minutes against a 38-year-old long striker whose losses come from "
                   "being out-worked. Herbert's range and power keep him live early; Camilo's pace should take over.",
         factors=["Age (38) vs 25", "Camilo's wrestling vs Herbert being out-worked", "Herbert's power (against)"]),
    dict(a="Ketlen Souza", b="Lupita Godinez", favours="Lupita Godinez", logit=0.25, confidence="moderate",
         reasoning="Godinez hasn't lost to an unranked opponent in five UFC years; her losses are to elite grapplers (Suarez, Dern, Jandiroba), "
                   "which Souza is not. Her volume and takedowns suit a fight against a striker who tends to fall into clinches, per UFC.com. "
                   "The model weighs the recent submission loss and Souza's KO more than the matchup warrants.",
         factors=["Godinez's volume and wrestling", "Losses only to elite grapplers", "Souza's clinch tendency"]),
    dict(a="Andre Fili", b="Kai Kamaka III", favours="Andre Fili", logit=0.15, confidence="low",
         reasoning="The model makes Kamaka a big favourite on his accuracy, but he absorbs a lot and was stopped in round one by Luke Riley in July, "
                   "and his only UFC win this year was a split decision. Fili, 36, has lost two straight but one was a close decision and the other "
                   "a short-notice Fight of the Night; 27 UFC fights of experience against a hittable pressure fighter. The market's side looks "
                   "better, but Fili's age and recent stoppage keep it small.",
         factors=["Kamaka's defensive leaks and July KO loss", "Fili's experience", "Fili's age and recent stoppage (against)"]),
    dict(a="Malcolm Wellmaker", b="Otari Tanzilovi", favours="Malcolm Wellmaker", logit=0.0, confidence="low",
         reasoning="Genuinely uncertain. The model's case is sound: Tanzilovi wrestles (about 3.4 takedowns per 15 minutes) and grappling defense is "
                   "Wellmaker's weakness. The market's case is Wellmaker's first-round power and a fresh start at American Top Team after two losses. "
                   "No edge either way, so no lean.",
         factors=["Tanzilovi's wrestling vs Wellmaker's grappling defense", "Wellmaker's power", "Camp change"]),
    dict(a="Gerald Meerschaert", b="Julius Walker", favours="Julius Walker", logit=0.0, confidence="low",
         reasoning="Meerschaert is 38, on a five-fight skid and moving up to light heavyweight after missing weight in May, but he holds the "
                   "middleweight submission record and Walker has been stopped twice in a row. The model already leans Walker harder than the market; "
                   "nothing to add.",
         factors=["Age and skid (Meerschaert)", "Walker's back-to-back stoppage losses", "Meerschaert's submissions"]),
    dict(a="Francisco Prado", b="Ismael Bonfim", favours="Francisco Prado", logit=0.15, confidence="low",
         reasoning="Bonfim stepped in on short notice for Artur Minev and is on a three-fight losing skid; Prado gets a full camp and moves back to "
                   "lightweight, his natural weight, after three welterweight decisions. The model doesn't see the short notice.",
         factors=["Bonfim on short notice", "Bonfim's three-fight skid", "Prado back at his natural weight"]),
    dict(a="Leon Shahbazyan", b="Niko Price", favours="Leon Shahbazyan", logit=0.10, confidence="low",
         reasoning="Price is 37, returning from a short retirement after four straight losses with a damaged knee. Shahbazyan's own durability is a "
                   "worry (knocked out in 23 seconds in his UFC debut), and Price always swings, but the younger submission threat is the side.",
         factors=["Price's age, knee and skid", "Shahbazyan's chin (against)", "Shahbazyan's first-round submissions"]),
    dict(a="Brendson Ribeiro", b="Felipe Franco", favours="Felipe Franco", logit=0.0, confidence="low",
         reasoning="Ribeiro is a short-notice replacement on a long losing run against a Brazilian prospect in his third fight of the year. The model "
                   "already leans Franco harder than the market; no further lean.",
         factors=["Ribeiro on short notice", "Ribeiro's losing run"]),
    dict(a="Allen Frye", b="Richard Harris", favours="Richard Harris", logit=0.15, confidence="moderate",
         reasoning="The model has little on Harris (four verified fights, unbeaten, a first-round KO of Alvin Hines in his July debut after replacing "
                   "Frye). Frye lost his debut on the cards and was pulled from two assignments this year. Activity and momentum favour Harris.",
         factors=["Thin model data on Harris", "Frye's inactivity and withdrawals", "Harris's finishing record"]),
    dict(a="Alice Pereira", b="Darya Zheleznyakova", favours="Alice Pereira", logit=0.0, confidence="low",
         reasoning="Model and market agree near 56-57% for Pereira, the roster's youngest fighter, who alternates wins and losses. Nothing to add.",
         factors=["Model and market agree"]),
    dict(a="Ernesta Kareckaite", b="Melissa Gatto", favours="Melissa Gatto", logit=0.0, confidence="low",
         reasoning="Close on both numbers. Kareckaite lost a Fight of the Night decision after a late opponent change; Gatto lost a majority decision "
                   "after being hurt by an illegal upkick. No edge.",
         factors=["Even fight"]),
]

PALM = "https://sports.yahoo.com/articles/ufc-vegas-122-brendan-allen-230542548.html"
LANG = "https://www.wagertalk.com/news/mma/ufc-fight-night-allen-vs-duncan-picks-predictions-and-odds-october-10-2026/"
SHELTON = "https://www.rotowire.com/mma/article/ufc-best-bets-today-picks-odds-predictions-for-ufc-vegas-122-139443"

PUNDIT_PICKS = [  # (a, b, outlet, author, pick, method, url)
    ("Brendan Allen", "Christian Leroy Duncan", "The Big Lead", "Preston Palm", "Brendan Allen", "DEC", PALM),
    ("Jai Herbert", "Matheus Camilo", "The Big Lead", "Preston Palm", "Matheus Camilo", "KO/TKO R1", PALM),
    ("Ketlen Souza", "Lupita Godinez", "The Big Lead", "Preston Palm", "Lupita Godinez", "DEC", PALM),
    ("Andre Fili", "Kai Kamaka III", "The Big Lead", "Preston Palm", "Kai Kamaka III", "DEC", PALM),
    ("Malcolm Wellmaker", "Otari Tanzilovi", "The Big Lead", "Preston Palm", "Malcolm Wellmaker", "KO/TKO R2", PALM),
    ("Brendan Allen", "Christian Leroy Duncan", "WagerTalk", "Andy Lang", "Christian Leroy Duncan", "", LANG),
    ("Jai Herbert", "Matheus Camilo", "WagerTalk", "Andy Lang", "Matheus Camilo", "", LANG),
    ("Ketlen Souza", "Lupita Godinez", "WagerTalk", "Andy Lang", "Lupita Godinez", "", LANG),
    ("Gerald Meerschaert", "Julius Walker", "WagerTalk", "Andy Lang", "Julius Walker", "", LANG),
    ("Andre Fili", "Kai Kamaka III", "WagerTalk", "Andy Lang", "Andre Fili", "", LANG),
    ("Malcolm Wellmaker", "Otari Tanzilovi", "WagerTalk", "Andy Lang", "Otari Tanzilovi", "", LANG),
    ("Francisco Prado", "Ismael Bonfim", "WagerTalk", "Andy Lang", "Francisco Prado", "", LANG),
    ("Brendson Ribeiro", "Felipe Franco", "WagerTalk", "Andy Lang", "Brendson Ribeiro", "", LANG),
    ("Allen Frye", "Richard Harris", "WagerTalk", "Andy Lang", "Richard Harris", "", LANG),
    ("Alice Pereira", "Darya Zheleznyakova", "WagerTalk", "Andy Lang", "Alice Pereira", "", LANG),
    ("Ernesta Kareckaite", "Melissa Gatto", "WagerTalk", "Andy Lang", "Ernesta Kareckaite", "", LANG),
    ("Brendan Allen", "Christian Leroy Duncan", "RotoWire", "Cole Shelton", "Brendan Allen", "", SHELTON),
    ("Gerald Meerschaert", "Julius Walker", "RotoWire", "Cole Shelton", "Gerald Meerschaert", "", SHELTON),
    ("Jai Herbert", "Matheus Camilo", "RotoWire", "Cole Shelton", "Matheus Camilo", "KO/TKO", SHELTON),
    ("Allen Frye", "Richard Harris", "RotoWire", "Cole Shelton", "Richard Harris", "", SHELTON),
    ("Ketlen Souza", "Lupita Godinez", "RotoWire", "Cole Shelton", "Lupita Godinez", "", SHELTON),
    # Lang's Shahbazyan-Price pick was a total (the under), not a fighter: not recorded.
]

bouts = []
for r in READS:
    pm, pf = P[(r["a"], r["b"])]
    r.update(event=EVENT, date=DATE, p_model=pm, p_market=pf, created="2026-10-09T16:45:00+00:00",
             pundits=[{"outlet": o, "author": au, "pick": pk, "method": m, "url": u}
                      for a, b, o, au, pk, m, u in PUNDIT_PICKS if {a, b} == {r["a"], r["b"]}])
    check_read(r)
    bouts.append(r)
(ROOT / "reads").mkdir(exist_ok=True)
(ROOT / "reads" / "2026-10-10-ufc-fight-night-allen-vs-duncan.json").write_text(
    json.dumps({"event": EVENT, "date": DATE, "results_url": RESULTS, "bouts": bouts}, indent=1, ensure_ascii=False) + "\n")

pun = Pundits(ROOT / "pundits.jsonl")
for a, b, o, au, pk, m, u in PUNDIT_PICKS:
    pm, pf = P[(a, b)]
    p_pick = None if pf is None else (pf if pk == a else 1 - pf)
    pun.add({"event": EVENT, "date": DATE, "a": a, "b": b, "outlet": o, "author": au, "pick": pk, "method": m,
             "url": u, "p_market": round(p_pick, 3)})
pun.save()
print(len(bouts), "reads;", len(pun.rows), "pundit picks")
