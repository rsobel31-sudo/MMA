"""Scouting reads for UFC Fight Night: Adesanya vs. Magomedov (UFC Saudi Arabia, Riyadh, 2026-12-05).

logit: how far (log-odds, 0..0.8) the read moves the model toward `favours`, for what the model can't see.
The model's number at the time is recorded (p_model, toward a) so the read can be graded against it.
Drafted Tuesday 2026-11-24 from the reports (ufcriyadh_reports.py, ufc335_reports.py for Riley and Santos) and the
picks sheet of 2026-11-24 17:07 UTC. No pundit picks are published yet; Friday's run finalizes the reads with weigh-ins
and pundit picks.

Two leans are about data the model can't trust rather than the fighters:
- Bruno Gustavo da Silva: our records merge several Brazilian "Bruno Silva"s, so the model's 12% is not about him.
- Ivan Gnizditskiy: our data holds one of his seven pro fights, so the model's 33% rests on almost nothing.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
from mma_predictor.reads import Pundits, check_read  # noqa: E402

EVENT, DATE = "UFC Fight Night: Adesanya vs. Magomedov", "2026-12-05"
RESULTS = "https://en.wikipedia.org/wiki/UFC_Fight_Night:_Adesanya_vs._Magomedov"
CREATED = "2026-11-24T21:00:00+00:00"

# Model (stats only) and FanDuel no-vig numbers toward a, from the picks sheet of 2026-11-24 17:07 UTC.
P = {
    ("Israel Adesanya", "Sharabutdin Magomedov"): (0.37, 0.611),
    ("Ian Garry", "Yaroslav Amosov"): (0.48, 0.620),
    ("Islam Dulatov", "Levan Chokheli"): (0.60, 0.653),
    ("Mario Pinto", "Serghei Spivac"): (0.78, 0.738),
    ("Akbar Abdullaev", "Mairon Santos"): (0.63, 0.723),
    ("Ion Cutelaba", "Magomed Tuchalov"): (0.41, 0.384),
    ("Gabriel Santos", "Luke Riley"): (0.35, 0.420),
    ("Bruno Gustavo da Silva", "Jafel Filho"): (0.12, 0.417),
    ("Ivan Gnizditskiy", "Uran Satybaldiev"): (0.33, 0.500),
    ("Park Jun-yong", "Marco Tulio"): (0.55, 0.384),
    ("Matthieu Letho Duclos", "Modestino Rodrigues"): (0.62, 0.583),
    ("Abdul Hussein", "Hecher Sosa"): (0.55, 0.604),
    ("Elves Brener", "Mateusz Rebecki"): (0.39, 0.425),
    ("Mehemmedeli Osmanli", "Pavel Andrusca"): (None, None),
}

READS = [
    dict(a="Israel Adesanya", b="Sharabutdin Magomedov", favours="Israel Adesanya", logit=0.0, confidence="low",
         reasoning="The model has Magomedov at 63% on Adesanya's four straight losses and age; the market has Adesanya at 61% "
                   "on class and the new camp. Magomedov has never fought a former champion or gone five rounds. No lean "
                   "until fight week.",
         factors=["Adesanya's four-fight skid and reduced durability (against)", "Magomedov's first five-rounder",
                  "Adesanya's new camp"]),
    dict(a="Ian Garry", b="Yaroslav Amosov", favours="Ian Garry", logit=0.0, confidence="low",
         reasoning="Garry's range and volume against Amosov's wrestling; Amosov is unbeaten but inactive and 33. The model has "
                   "a coin flip, the market Garry at 62%. No lean yet.",
         factors=["Amosov's wrestling (against)", "Garry's volume at range", "Amosov's activity"]),
    dict(a="Islam Dulatov", b="Levan Chokheli", favours="Islam Dulatov", logit=0.0, confidence="low",
         reasoning="Model and market agree on Dulatov.", factors=["Dulatov's power"]),
    dict(a="Mario Pinto", b="Serghei Spivac", favours="Mario Pinto", logit=0.0, confidence="low",
         reasoning="Model and market agree on the unbeaten Pinto against Spivac's wrestling.",
         factors=["Spivac's wrestling (against)", "Pinto's power"]),
    dict(a="Akbar Abdullaev", b="Mairon Santos", favours="Akbar Abdullaev", logit=0.0, confidence="low",
         reasoning="Model and market agree on Abdullaev in his UFC debut.", factors=["Abdullaev's debut"]),
    dict(a="Ion Cutelaba", b="Magomed Tuchalov", favours="Magomed Tuchalov", logit=0.0, confidence="low",
         reasoning="Model and market agree on Tuchalov; Cutelaba fades after R1.", factors=["Cutelaba's cardio"]),
    dict(a="Gabriel Santos", b="Luke Riley", favours="Luke Riley", logit=0.0, confidence="low",
         reasoning="Riley is unbeaten and active, though on two weeks' notice; Santos has been out nearly 22 months. The "
                   "model and market both favour Riley; no lean yet.",
         factors=["Santos's 22-month layoff", "Riley on short notice (against)", "Santos's submissions (against)"]),
    dict(a="Bruno Gustavo da Silva", b="Jafel Filho", favours="Bruno Gustavo da Silva", logit=0.25, confidence="low",
         reasoning="The model's 12% for Silva comes from records that merge several Brazilian 'Bruno Silva's; the market has "
                   "him at 42%. The read moves part of the way back toward the market until his record is fixed.",
         factors=["Merged records in our data", "Jafel Filho's grappling (against)"]),
    dict(a="Ivan Gnizditskiy", b="Uran Satybaldiev", favours="Ivan Gnizditskiy", logit=0.15, confidence="low",
         reasoning="Our data has one of Gnizditskiy's seven pro fights (all finishes), so the model's 33% rests on almost "
                   "nothing; the market has a coin flip.",
         factors=["Thin data on Gnizditskiy", "Gnizditskiy's finishing record"]),
    dict(a="Park Jun-yong", b="Marco Tulio", favours="Marco Tulio", logit=0.0, confidence="low",
         reasoning="The model has Park at 55% on his UFC experience; the market has Tulio at 62%. No lean until fight week.",
         factors=["Park's experience", "Tulio's power (against)"]),
    dict(a="Matthieu Letho Duclos", b="Modestino Rodrigues", favours="Matthieu Letho Duclos", logit=0.0, confidence="low",
         reasoning="Model and market agree on Duclos.", factors=["Duclos's form"]),
    dict(a="Abdul Hussein", b="Hecher Sosa", favours="Abdul Hussein", logit=0.0, confidence="low",
         reasoning="Model and market agree on Hussein.", factors=["Hussein's form"]),
    dict(a="Elves Brener", b="Mateusz Rebecki", favours="Mateusz Rebecki", logit=0.0, confidence="low",
         reasoning="Model and market agree on Rebecki; Brener's R1 submissions are the danger.",
         factors=["Rebecki's pressure", "Brener's submissions (against)"]),
    dict(a="Mehemmedeli Osmanli", b="Pavel Andrusca", favours="Pavel Andrusca", logit=0.0, confidence="low",
         reasoning="The model can't price Osmanli. Andrusca is unbeaten and beat Nathaniel Wood; Osmanli is 22 and lost the "
                   "TUF final by disqualification. No lean.",
         factors=["Osmanli's thin data", "Andrusca's win over Wood"]),
]
# Picks published by Tuesday 2026-11-24: none yet.
PUNDIT_PICKS = []


def _p(a, b):
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
(ROOT / "reads" / "2026-12-05-ufc-fight-night-adesanya-vs-magomedov.json").write_text(
    json.dumps({"event": EVENT, "date": DATE, "results_url": RESULTS, "bouts": bouts}, indent=1, ensure_ascii=False) + "\n")
if PUNDIT_PICKS:
    pun = Pundits(ROOT / "pundits.jsonl")
    for a, b, o, au, pk, m, u in PUNDIT_PICKS:
        pm, pf = _p(a, b)
        p_pick = None if pf is None else (pf if pk == a else 1 - pf)
        pun.add({"event": EVENT, "date": DATE, "a": a, "b": b, "outlet": o, "author": au, "pick": pk, "method": m,
                 "url": u, "p_market_pick": p_pick})
    pun.save()
print(len(bouts), "reads;", len(PUNDIT_PICKS), "pundit picks")
