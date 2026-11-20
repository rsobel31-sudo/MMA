"""Scouting reports (part D) for UFC Fight Night: Procházka vs. Stirling (Doha, 2026-11-21): the late-notice lightweight
debut added on 2026-11-17, John Mitchell vs. Shoaib Yousaf, which replaced Manoel Sousa's cancelled bout. Written Friday
2026-11-20 after weigh-ins (Yousaf 156, Mitchell 155.5). Round counts come from data/verified/fights.csv."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATED = "2026-11-20T17:30:00+00:00"
EVENT = "UFC Fight Night: Procházka vs. Stirling"
MMAF = {"outlet": "MMA Fighting", "author": "", "title": "UFC signs two fighters for late-notice undercard matchup for UFC Qatar",
        "url": "https://www.mmafighting.com/ufc/522129/ufc-signs-two-fighters-for-late-notice-undercard-matchup-for-ufc-qatar", "date": "2026-11-17"}
BE = {"outlet": "Bloody Elbow", "author": "Donagh Corby", "title": "UFC signs up new Irish lightweight star to debut this weekend in surprise fight at UFC Qatar",
      "url": "https://bloodyelbow.com/2026/11/17/ufc-signs-up-new-irish-lightweight-star-to-debut-this-weekend-in-surprise-fight-at-ufc-qatar/", "date": "2026-11-17"}
WEIGH = {"outlet": "MMA Fighting", "author": "", "title": "UFC Qatar weigh-in results: Jiri Prochazka vs. Navajo Stirling official, 1 fighter misses weight",
         "url": "https://www.mmafighting.com/ufc/522520/ufc-qatar-weigh-in-results-jiri-prochazka-vs-navajo-stirling-official-1-fighter-misses-weight", "date": "2026-11-20"}
DATA = {"outlet": "Fight Lab verified records", "author": "", "title": "data/verified/fights.csv", "url": "https://www.sherdog.com/", "date": "2026-11-20"}

R = {
 "john-mitchell": {"name": "John Mitchell", "updated": UPDATED, "event": EVENT,
  "summary": "An Irish lightweight from Cork ('The Cork Horse', 11-3, age 31), based in the UAE, signed four days before the card. "
             "Best known for five PFL fights: he reached the 2023 PFL Europe lightweight final (stopped by Jakub Kaszuba in R2) and "
             "lost a decision to Makkasharip Zaynukov in 2025. He knocked out Kallew dos Santos in 59 seconds in July. He is 2-0 as "
             "a pro boxer.",
  "how_they_fight": {"Striking": "A boxer first (2-0 pro boxing): four knockouts in our data, in R1, R2 and R3.",
                     "Grappling": "Two R1 submissions.",
                     "Defense": "Stopped twice: by Kaszuba (R2 TKO) and by submission (R1).",
                     "Pace & cardio": "Five decision wins; goes three rounds comfortably.",
                     "Fight IQ": "Experienced against PFL-level opposition."},
  "patterns": ["Boxing-led; finishes spread over all three rounds", "Five decision wins"],
  "concerns": ["Four days' notice for his UFC debut", "Stopped by the best opponent he faced (Kaszuba)"],
  "keys_to_beat": ["Pressure him early before he finds his range"],
  "news": [{"date": "2026-11-17", "text": "Signed with the UFC and booked against Shoaib Yousaf on four days' notice; he had been due to fight for "
            "a BullWaves title on Nov. 27.", "source": BE["url"]},
           {"date": "2026-11-20", "text": "Weighed in at 155.5.", "source": WEIGH["url"]}],
  "sources": [MMAF, BE, WEIGH, DATA], "depth": "thin"},
 "shoaib-yousaf": {"name": "Shoaib Yousaf", "updated": UPDATED, "event": EVENT,
  "summary": "An English lightweight from Manchester Top Team (14-3, age 31), a former IMMAF world champion and veteran of Brave, ACB "
             "and Oktagon, on a six-fight winning streak. His last three wins were R1 knockouts, the latest over Tariel Abbasov at FCC "
             "47 in September. He makes his UFC debut on a few days' notice.",
  "how_they_fight": {"Striking": "Eight knockouts in our data, all in R1.",
                     "Grappling": "Two submissions; an IMMAF background.",
                     "Defense": "Never stopped; all three losses are decisions.",
                     "Pace & cardio": "Four decision wins; goes three rounds when needed.",
                     "Fight IQ": "Experienced across several European promotions."},
  "patterns": ["Early knockouts (all eight in R1)", "Never finished"],
  "concerns": ["Short-notice UFC debut", "Out-pointed in all three losses"],
  "keys_to_beat": ["Survive R1 and out-work him over three rounds"],
  "news": [{"date": "2026-11-17", "text": "Signed with the UFC for a short-notice debut against John Mitchell.", "source": MMAF["url"]},
           {"date": "2026-11-20", "text": "Weighed in at 156.", "source": WEIGH["url"]}],
  "sources": [MMAF, BE, WEIGH, DATA], "depth": "thin"},
}
for slug, doc in R.items():
    (ROOT / "reports" / f"{slug}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
