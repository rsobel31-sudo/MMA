"""Scouting reads and pundit picks for UFC 332 (2026-09-30).

logit: how far (log-odds, 0..0.8) the read moves the model toward `favours`, for what the model can't see.
The model's number at the time is recorded (p_model, toward a) so the read can be graded against it.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
from mma_predictor.reads import Pundits, check_read  # noqa: E402

SHEET = Path(sys.argv[1]) if len(sys.argv) > 1 else None
EVENT, DATE = "UFC 332: Silva vs. Wang", "2026-10-03"

# Model and FanDuel numbers when the reads were written (picks sheet, 2026-09-30), toward a.
P = {  # (a, b): (p_model_a, p_fanduel_a no-vig)
    ("Natalia Silva", "Cong Wang"): (0.67, 0.665),
    ("Deiveson Figueiredo", "Payton Talbott"): (0.18, 0.169),
    ("King Green", "Esteban Ribovics"): (0.39, 0.314),
    ("Roberto Soldic", "Kalinn Williams"): (0.61, 0.707),
    ("Ateba Abega Gautier", "Roman Kopylov"): (0.59, 0.685),
    ("Imanol Rodriguez", "Alden Coria"): (0.42, 0.589),
    ("Damian Pinas", "Andrey Pulyaev"): (0.80, 0.805),
    ("Marcus McGhee", "Anthony Romero"): (None, None),
    ("Anthony Wint", "Lucas Armand"): (0.56, 0.817),
    ("Johnny Walker", "Mick Parkin"): (0.35, 0.577),
    ("Rafael dos Anjos", "Alexander Hernandez"): (0.16, 0.303),
    ("Jacobe Smith", "Bruce Whitehead"): (0.88, 0.868),
    ("Marvin Vettori", "Ismail Naurdiev"): (0.47, 0.442),
    ("Court McGee", "Eric Nolan"): (0.38, 0.307),
}

READS = [
    dict(a="Natalia Silva", b="Cong Wang", favours="Natalia Silva", logit=0.15, confidence="moderate",
         reasoning="Silva's defense is her movement, and five rounds reward the fighter who is harder to hit and can change the fight with "
                   "grappling. Wang's only loss was a submission, and a championship weight cut after missing weight earlier this year is a real "
                   "risk over 25 minutes at altitude. Wang's accuracy and pressure keep it close; the model and market already agree on Silva.",
         factors=["Silva's grappling vs Wang's only loss (submission)", "Wang's weight cut for five rounds", "Silva's elusiveness vs Wang's pressure"]),
    dict(a="Deiveson Figueiredo", b="Payton Talbott", favours="Payton Talbott", logit=0.10, confidence="moderate",
         reasoning="At 39 and 1-4 in his last five, finished twice, Figueiredo's decline shows most against long, busy strikers, which is exactly "
                   "Talbott. The main risk to Talbott is Figueiredo's early power and chokes if Talbott gets careless, plus Talbott's ten-month layoff.",
         factors=["Age and recent stoppage losses", "Talbott's length and volume"]),
    dict(a="King Green", b="Esteban Ribovics", favours="King Green", logit=0.20, confidence="moderate",
         reasoning="Stylistically Green is well built for Ribovics: an accurate counter-puncher against a hittable volume striker, and a capable "
                   "wrestler against a man who lost two of three UFC fights to takedowns (MMA Mania's Andrew Richardson picks Green). The market "
                   "prices in Green's age and a fifth fight in 12 months; I think it prices them too heavily.",
         factors=["Takedowns vs Ribovics' grappling", "Counters vs a hittable pressure fighter", "Age and schedule (against Green)"]),
    dict(a="Roberto Soldic", b="Kalinn Williams", favours="Roberto Soldic", logit=0.10, confidence="low",
         reasoning="Soldic's KSW body of work (Khalidov, two belts) is stronger than Williams' UFC record, but a 20-month layoff and a debut against a "
                   "fast-starting power puncher make round one dangerous. Small lean to the more complete fighter.",
         factors=["Layoff and debut", "Williams' early power", "Soldic's pedigree"]),
    dict(a="Ateba Abega Gautier", b="Roman Kopylov", favours="Ateba Abega Gautier", logit=0.20, confidence="moderate",
         reasoning="The model underrates Gautier on thin UFC data: 24, 6'4\" with an 81\" reach, 5-0 with four KOs, and only a durable, lanky "
                   "Pulyaev took him the distance. Kopylov is a solid gatekeeper who loses to bigger, better strikers; wrestling is his best path.",
         factors=["Size, reach and power", "Kopylov's ceiling vs top middleweights", "Kopylov's wrestling (for him)"]),
    dict(a="Imanol Rodriguez", b="Alden Coria", favours="Imanol Rodriguez", logit=0.25, confidence="moderate",
         reasoning="The model likes Coria's longer record, but Rodriguez's athleticism and grappling target Coria's weak spot (takedown defense around "
                   "45%). Coria's accurate countering keeps it competitive. Sherdog's Tom Feely: Rodriguez by decision.",
         factors=["Rodriguez's athleticism and wrestling", "Coria's takedown defense", "Coria's counters vs wild pressure"]),
    dict(a="Damian Pinas", b="Andrey Pulyaev", favours="Damian Pinas", logit=0.10, confidence="moderate",
         reasoning="Pulyaev has lost three straight and was just submitted; his durability-and-range approach is risky against Pinas' one-shot power. "
                   "Pinas is unproven past round one, which is Pulyaev's only real path.",
         factors=["Pinas' power", "Pulyaev's slide"]),
    dict(a="Marcus McGhee", b="Anthony Romero", favours="Marcus McGhee", logit=None, confidence="none",
         reasoning="No read yet: Romero took the fight on three days' notice, sources disagree on his record, and FanDuel had no line when "
                   "this was written. McGhee should be a solid favourite; revisit Friday.",
         factors=["Short-notice newcomer", "Thin data on Romero"]),
    dict(a="Anthony Wint", b="Lucas Armand", favours="Anthony Wint", logit=0.60, confidence="moderate",
         reasoning="The model has almost nothing on either man (both get league-average stats), so its 56% is a shrug. Wint is an elite athlete with a "
                   "wrestling base who ran through regional opposition; Armand's unbeaten record came against weak competition. Wint's size and "
                   "defensive holes are the risks.",
         factors=["No UFC data for either (model near 50/50)", "Athleticism and wrestling", "Armand's level of opposition"]),
    dict(a="Johnny Walker", b="Mick Parkin", favours="Mick Parkin", logit=0.10, confidence="low",
         reasoning="Walker's chin has failed against heavy hitters (Oezdemir, Ankalaev), and heavyweight punches are heavier; his recent fights have "
                   "been frozen at range. Parkin is durable, steady and applies pressure, but he's hittable and returns from 18 months out. "
                   "The model is already on Parkin; the market isn't. Tom Feely: Parkin by second-round KO.",
         factors=["Walker's durability at heavyweight", "Parkin's layoff", "Walker's length and explosiveness"]),
    dict(a="Rafael dos Anjos", b="Alexander Hernandez", favours="Alexander Hernandez", logit=0.10, confidence="moderate",
         reasoning="Dos Anjos is 42, two years out after three knee surgeries, and cutting to 155 where his cardio has failed before. His pressure is "
                   "the style that beat Hernandez last time out (Rafa Garcia), which keeps it from being a blowout.",
         factors=["Age, layoff and knee surgery", "Pressure vs Hernandez's counters"]),
    dict(a="Jacobe Smith", b="Bruce Whitehead", favours="Jacobe Smith", logit=0.20, confidence="moderate",
         reasoning="Whitehead debuts on about nine days' notice from the regional scene and was knocked out quickly in 2025; Smith's wrestling and "
                   "ground-and-pound should end it early. Smith's defensive holes are the only upset path.",
         factors=["Short-notice debut", "Wrestling and ground-and-pound"]),
    dict(a="Marvin Vettori", b="Ismail Naurdiev", favours="Ismail Naurdiev", logit=0.0, confidence="low",
         reasoning="Genuinely even. Vettori's four losses all went to the cards against good opposition, and a camp change could restore his pressure "
                   "style; Naurdiev is sharp but aimless. No adjustment to the model.",
         factors=["Vettori's form and camp change", "Naurdiev's sharpness"]),
    dict(a="Court McGee", b="Eric Nolan", favours="Eric Nolan", logit=0.10, confidence="low",
         reasoning="McGee is 42 and has been knocked out twice since 2022; Nolan has the power to exploit it. McGee's early grappling and the "
                   "hometown farewell are real, and Tom Feely picks McGee by first-round submission, but the smarter side is Nolan.",
         factors=["Age and durability", "McGee's early grappling"]),
]

PUNDIT_PICKS = [  # (a, b, outlet, author, pick, method, url)
    ("King Green", "Esteban Ribovics", "MMA Mania", "Andrew Richardson", "King Green", "", "mania_green"),
    ("Imanol Rodriguez", "Alden Coria", "Sherdog", "Tom Feely", "Imanol Rodriguez", "DEC", "sd1"),
    ("Damian Pinas", "Andrey Pulyaev", "Sherdog", "Tom Feely", "Damian Pinas", "KO/TKO R2", "sd2"),
    ("Anthony Wint", "Lucas Armand", "Sherdog", "Tom Feely", "Anthony Wint", "KO/TKO R1", "sd4"),
    ("Johnny Walker", "Mick Parkin", "Sherdog", "Tom Feely", "Mick Parkin", "KO/TKO R2", "sd5"),
    ("Rafael dos Anjos", "Alexander Hernandez", "Sherdog", "Tom Feely", "Alexander Hernandez", "DEC", "sd6"),
    ("Marvin Vettori", "Ismail Naurdiev", "Sherdog", "Tom Feely", "Ismail Naurdiev", "DEC", "sd7"),
    ("Court McGee", "Eric Nolan", "Sherdog", "Tom Feely", "Court McGee", "SUB R1", "sd8"),
    ("Jacobe Smith", "Bruce Whitehead", "Sherdog", "Tom Feely", "Jacobe Smith", "KO/TKO R1", "sd9"),
    # Feely's McGhee pick was made against Benardo Sopaj, who withdrew: not recorded.
]

src = json.loads((ROOT / "sources_ufc332.json").read_text())
bouts = []
for r in READS:
    pm, pf = P[(r["a"], r["b"])]
    r.update(event=EVENT, date=DATE, p_model=pm, p_market=pf, created="2026-09-30T23:30:00+00:00",
             pundits=[{"outlet": o, "author": au, "pick": pk, "method": m, "url": src[u]["url"]}
                      for a, b, o, au, pk, m, u in PUNDIT_PICKS if {a, b} == {r["a"], r["b"]}])
    check_read(r)
    bouts.append(r)
(ROOT / "reads").mkdir(exist_ok=True)
(ROOT / "reads" / "2026-10-03-ufc-332.json").write_text(json.dumps({"event": EVENT, "date": DATE, "results_url": "https://en.wikipedia.org/wiki/UFC_332", "bouts": bouts}, indent=1, ensure_ascii=False) + "\n")

pun = Pundits(ROOT / "pundits.jsonl")
for a, b, o, au, pk, m, u in PUNDIT_PICKS:
    pm, pf = P[(a, b)]
    p_pick = None if pf is None else (pf if pk == a else 1 - pf)
    pun.add({"event": EVENT, "date": DATE, "a": a, "b": b, "outlet": o, "author": au, "pick": pk, "method": m,
             "url": src[u]["url"], "p_market": p_pick})
pun.save()
print(len(bouts), "reads;", len(pun.rows), "pundit picks")
