"""Scouting reads for UFC 334: Gane vs. Hokit (2026-11-14).

logit: how far (log-odds, 0..0.8) the read moves the model toward `favours`, for what the model can't see.
The model's number at the time is recorded (p_model, toward a) so the read can be graded against it.
Drafted Tuesday 2026-11-10 from the reports and the picks sheet; Friday's run finalizes these after weigh-ins and adds
the published pundit picks.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
from mma_predictor.reads import Pundits, check_read  # noqa: E402

EVENT, DATE = "UFC 334: Gane vs. Hokit", "2026-11-14"
RESULTS = "https://en.wikipedia.org/wiki/UFC_334"
CREATED = "2026-11-10T18:30:00+00:00"

# Model (stats only) and FanDuel no-vig numbers toward a, from the picks sheet of 2026-11-10 17:15 UTC.
# Diaz-Heili has no FanDuel line yet.
P = {
    ("Ciryl Gane", "Josh Hokit"): (0.69, 0.658),
    ("Amanda Nunes", "Kayla Harrison"): (0.39, 0.375),
    ("Caio Borralho", "Yousri Belgaroui"): (0.69, 0.583),
    ("Kevin Holland", "Uros Medic"): (0.37, 0.425),
    ("Bilal Hasan", "Luis Gurule"): (0.76, 0.879),
    ("Charles Radtke", "Stephen Thompson"): (0.70, 0.422),
    ("Chris Duncan", "Drew Dober"): (0.84, 0.586),
    ("Jim Miller", "Terrance McKinney"): (0.33, 0.36),
    ("Cesar Almeida", "Donte Johnson"): (0.22, 0.40),
    ("Jared Gordon", "Melquizael Costa"): (0.17, 0.245),
    ("Bia Mesquita", "Macy Chiasson"): (0.67, 0.685),
    ("Evan Elder", "Samuel Sanches"): (0.44, 0.485),
    ("Juan Diaz", "Alateng Heili"): (None, None),
}

READS = [
    dict(a="Ciryl Gane", b="Josh Hokit", favours="Ciryl Gane", logit=0.0, confidence="low",
         reasoning="Gane's footwork and long kicking game against an unbeaten wrestler who gives up about 21 cm of reach and has "
                   "never gone five rounds. Model and market agree near two to one; no lean until fight week.",
         factors=["Gane's range and movement", "Hokit's wrestling and power (against)", "Hokit's first five-rounder"]),
    dict(a="Amanda Nunes", b="Kayla Harrison", favours="Kayla Harrison", logit=0.0, confidence="low",
         reasoning="Both come back from long absences: Nunes after more than three years retired, Harrison about 17 months "
                   "after neck surgery. Harrison's judo and top control against Nunes's power. Model and market agree; no lean.",
         factors=["Nunes's layoff", "Harrison's neck surgery and layoff", "Harrison's grappling"]),
    dict(a="Caio Borralho", b="Yousri Belgaroui", favours="Caio Borralho", logit=0.0, confidence="low",
         reasoning="Borralho returns from rib surgery against a kickboxer whose three UFC wins were all TKOs; his wrestling and "
                   "control are the path. The model is already above the market; no lean.",
         factors=["Borralho's wrestling", "Belgaroui's striking (against)", "Borralho's rib surgery (against)"]),
    dict(a="Kevin Holland", b="Uros Medic", favours="Uros Medic", logit=0.10, confidence="low",
         reasoning="Holland withdrew injured from two bookings this year and hasn't fought since April; Medic has four straight "
                   "first-round finishes and every win by stoppage. Holland's chin and experience keep it small.",
         factors=["Holland's injuries and inactivity", "Medic's early finishing", "Holland's experience (against)"]),
    dict(a="Bilal Hasan", b="Luis Gurule", favours="Bilal Hasan", logit=0.0, confidence="low",
         reasoning="Hasan is unbeaten and fresh off a knockout; Gurule is 1-4 in the UFC. Hasan's third fight in about three months "
                   "is the only question. Market is above the model already; no lean.",
         factors=["Hasan's form", "Hasan's quick turnaround (against)"]),
    dict(a="Charles Radtke", b="Stephen Thompson", favours="Charles Radtke", logit=0.05, confidence="low",
         reasoning="Thompson, 43, returns from 16 months out after his shin was split to the bone, on a three-fight skid in which "
                   "he lost the grappling each time; Radtke's last two wins came from takedowns and control. The model (70%) "
                   "already sees the age and layoff and is far above the market (42%); the matchup adds only a little. Radtke "
                   "was knocked out by both strikers he faced in the UFC.",
         factors=["Thompson's age and layoff", "Radtke's takedowns", "Radtke's chin against strikers (against)"]),
    dict(a="Chris Duncan", b="Drew Dober", favours="Chris Duncan", logit=0.0, confidence="low",
         reasoning="Duncan is coming off a round-two submission loss; Dober has two straight stoppages and real power. The model "
                   "is far above the market on Duncan; no read until fight week.",
         factors=["Dober's power", "Duncan's form"]),
    dict(a="Jim Miller", b="Terrance McKinney", favours="Terrance McKinney", logit=0.0, confidence="low",
         reasoning="McKinney starts like a sprinter and has been stopped when he fades; Miller, 43, submitted Gordon in round one "
                   "in May. Either man can finish it early. Model and market agree; no lean.",
         factors=["McKinney's first-round power", "Miller's submissions in scrambles"]),
    dict(a="Cesar Almeida", b="Donte Johnson", favours="Donte Johnson", logit=0.0, confidence="low",
         reasoning="Almeida is 38 and was knocked out in round one last time; Johnson took him as a replacement opponent. The "
                   "model is already below the market on Almeida; no lean.",
         factors=["Almeida's age and recent KO loss"]),
    dict(a="Jared Gordon", b="Melquizael Costa", favours="Melquizael Costa", logit=0.0, confidence="low",
         reasoning="Gordon is 38 with three losses in four; Costa moves up from featherweight. Model and market agree; no lean.",
         factors=["Gordon's form", "Costa's move up in weight"]),
    dict(a="Bia Mesquita", b="Macy Chiasson", favours="Bia Mesquita", logit=0.0, confidence="low",
         reasoning="Mesquita's grappling against a much taller fighter on a three-fight skid who has missed weight before. Model "
                   "and market agree; no lean.",
         factors=["Mesquita's grappling", "Chiasson's size (against)"]),
    dict(a="Evan Elder", b="Samuel Sanches", favours="Samuel Sanches", logit=0.0, confidence="low",
         reasoning="Elder returns from about 19 months out after a leg injury; Sanches debuts after his own 14-month absence. "
                   "Too little to lean either way.",
         factors=["Elder's layoff", "Sanches's debut"]),
    dict(a="Juan Diaz", b="Alateng Heili", favours="Juan Diaz", logit=0.15, confidence="low",
         reasoning="Heili took the fight on about eight days' notice, seven weeks after his last; Diaz has had a full camp. Heili "
                   "is durable (not stopped since 2017) and experienced, so the lean is small. No line yet.",
         factors=["Heili's short notice", "Heili's durability (against)"]),
]

# Picks published by Friday (outlet, author, pick, method, url); filled on the Friday run.
PUNDIT_PICKS = []


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
(ROOT / "reads" / "2026-11-14-ufc-334-gane-vs-hokit.json").write_text(
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
