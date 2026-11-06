"""Scouting report for Carlos Calderon, Austin Bashi's late replacement opponent at UFC Fight Night: Cortes-Acosta vs.
Walker (UFC Vegas 124 / Fight Night 293, 2026-11-07), written Friday 2026-11-06 (weigh-in day).

Calderon replaced Lucas Brennan (torn ACL) on four days' notice, so there is no fight-week preview of him beyond the
booking news and one betting preview. Round/method counts are taken from data/verified/fights.csv (16 bouts: 11-4, 1 NC);
the only bout with full stats is his 2024 Contender Series loss. Style notes lean on Cageside Press's 2024 Contender
Series breakdown and the UFC.com result write-up; nothing recent describes his game in detail.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATED = "2026-11-06T18:00:00+00:00"
EVENT = "UFC Fight Night: Cortes-Acosta vs. Walker"


def src(outlet, title, url, date, author=""):
    return {"outlet": outlet, "author": author, "title": title, "url": url, "date": date}


SRC = {
    # booking
    "sherdog_booking": src("Sherdog", "Fury FC champ steps in on 4 days' notice for UFC debut",
                           "https://www.sherdog.com/news/news/Fury-FC-champ-steps-in-on-4-days-notice-for-UFC-debut-203501",
                           "2026-11-05", "Sayan Nag"),
    "sbn_booking": src("Yahoo Sports (SB Nation)", "UFC Vegas 124 adds replacement fighter on 4 days' notice",
                       "https://sports.yahoo.com/articles/ufc-vegas-124-adds-replacement-190000727.html", "2026-11-04",
                       "Alexander K. Lee"),
    "mania_booking": src("Yahoo Sports (MMA Mania)", "UFC newcomer steps up on four days' notice for UFC Vegas 124",
                         "https://sports.yahoo.com/articles/ufc-newcomer-steps-four-days-221116340.html", "2026-11-04",
                         "Alexander Behunin"),
    "si_booking": src("Yahoo Sports (MMA Knockout, SI)",
                      "Fighter Steps in on Four Days' Notice to Debut on Saturday's UFC Fight Night Card",
                      "https://sports.yahoo.com/articles/fighter-steps-four-days-notice-163653174.html", "2026-11-04",
                      "Drew Beaupre"),
    "clutch_pick": src("Yahoo Sports (ClutchPoints)",
                       "Austin Bashi vs. Carlos Calderon prediction, odds, pick for UFC Vegas 124",
                       "https://sports.yahoo.com/articles/austin-bashi-vs-carlos-calderon-160627480.html", "2026-11-06",
                       "Garrett Kerman"),
    "sbn_weighin": src("Yahoo Sports (SB Nation)", "UFC Vegas 124 early weigh ins video results, LIVE stream updates",
                       "https://sports.yahoo.com/articles/ufc-vegas-124-early-weigh-163000711.html", "2026-11-06",
                       "Jesse Holland"),
    # Contender Series 2024
    "cage_dwcs_prev": src("Cageside Press", "DWCS 2024: Episode 8 Breakdown and Predictions",
                          "https://cagesidepress.com/2024/09/30/dwcs-2024-episode-8-breakdown-and-predictions/2",
                          "2024-09-30", "Shawn Bitter"),
    "ufc_dwcs": src("UFC.com", "Week 8 Results & Scorecards | Dana White's Contender Series Season 8",
                    "https://www.ufc.com/news/week-8-results-scorecards-dana-whites-contender-series-season-8",
                    "2024-10-02"),
}


def slug(name):
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


R = {}


def report(name, summary, how, patterns, concerns, keys, news, sources, depth):
    R[name] = {"name": name, "updated": UPDATED, "event": EVENT, "summary": summary, "how_they_fight": how,
               "patterns": patterns, "concerns": concerns, "keys_to_beat": keys, "news": news,
               "sources": [SRC[k] for k in sources], "depth": depth}


def n(date, text, key):
    return {"date": date, "text": text, "source": SRC[key]["url"]}


# ---------------------------------------------------------------------------------------------------------------
report("Carlos Calderon",
       "Carlos 'The Chief' Calderon (11-4, 1 NC, age 31) is the reigning Fury FC featherweight champion. He makes his UFC "
       "debut against Austin Bashi on four days' notice after Lucas Brennan tore his ACL. He is a submission-first "
       "finisher: six of his 11 wins are submissions, two more are R1 KOs, and he is on a three-fight win streak (5-1 in his "
       "last six). He won the Fury belt by R4 rear-naked choke over UFC veteran Damon Jackson in May and defended it over "
       "five rounds against Lorram Esteves on Oct 2. His one step up to UFC-level opposition was a 2024 Contender Series "
       "loss, a R2 anaconda choke by Alberto Montes, also taken on short notice.",
       {"Striking": "A volume striker who starts fast (Cageside Press, 2024), but that breakdown was harsh on the craft: "
                    "low hands, 'leads in with his chin', sloppy and reckless entries. On the Contender Series he threw a lot "
                    "(37 of 88 significant, 42%) while Montes landed 38 of 57; UFC.com said Calderon 'showed a varied "
                    "offense' in a fast first round. His two KO wins were both in R1 and very fast (0:17 and 0:25, 2022), "
                    "against regional opposition.",
        "Grappling": "This is the main weapon. Six submission wins: R1 x3 (Ellis 2024, Alvarez 2025, Torres 2026), R2 x1 "
                     "(Gavidia 2023), R3 x1 (Broadwater 2021, at 4:59) and R4 x1 (Jackson, RNC, 2:07). ClutchPoints says he "
                     "threatens to take the back and finish. Cageside (2024) said he 'can snatch up the neck if his opponent "
                     "is lazy', but rated his position and takedown defense poorly. He landed 2 of 6 takedowns and had "
                     "about 2:39 of control against Montes.",
        "Defense": "The 2024 Cageside breakdown called his defense 'terrible all around', and that was before the Fury FC "
                   "title run. His four losses: two submissions (Motaz Askar R1, 2022; Montes R2, 2024 anaconda choke after "
                   "a takedown) and two decisions (Elijah Leggett 2023, Mauricio Gomez split 2025). Never stopped by "
                   "strikes in our data. Both submission losses came against grapplers who got on top of him.",
        "Pace & cardio": "Went deep twice in 2026: a R4 finish of Jackson and a full 25-minute decision over Esteves. "
                         "He has three decision wins (two of them split or five-round) and finishes spread across R1-R4. "
                         "Cardio over 15 minutes shouldn't be a problem. He fought five weeks ago, so ClutchPoints argues "
                         "the weight cut on short notice is not a concern; that is their opinion, not a reported weight.",
        "Fight IQ": "Took both of his biggest opportunities (Contender Series and now the UFC) on short notice. Has beaten one "
                    "UFC veteran (Damon Jackson) and nobody else of note; Cageside said in 2024 the best record he had beaten "
                    "was 4-3."},
       ["Submission finisher: 6 of 11 wins by submission, back-taking and chokes",
        "Fast starter: 5 of 8 finishes in R1",
        "Two five-round fights in 2026, both wins",
        "Short-notice UFC debut; a big betting underdog (+400 per DraftKings, via ClutchPoints)"],
       ["Defense and hand position (Cageside, 2024); untested against UFC strikers",
        "Taken down and submitted by the one UFC-calibre prospect he has faced (Montes)",
        "Thin evidence: no tracked stats beyond one 2024 bout, and nothing recent describes his style in detail",
        "Short notice: four days, after a fight five weeks earlier"],
       ["Wrestle him: Montes took him down in R2 and finished from top",
        "Avoid giving him the back in scrambles",
        "Make him strike defensively; Cageside rated his defense poorly"],
       [n("2026-11-04", "Signed to replace Lucas Brennan (torn ACL) against Austin Bashi at featherweight, on four days' notice; "
                        "UFC debut. Heavy.com first reported it; MMA Fighting's Mike Heck confirmed.", "sbn_booking"),
        n("2026-11-04", "Was originally scheduled to defend his Fury FC title in the Fury FC 127 main event on Jan 15.",
          "si_booking"),
        n("2026-11-06", "DraftKings odds via ClutchPoints: Bashi -535, Calderon +400; ClutchPoints picks Bashi inside 2.5 rounds.",
          "clutch_pick"),
        n("2026-10-02", "Defended the Fury FC featherweight title with a five-round unanimous decision over Lorram Esteves.",
          "sbn_booking"),
        n("2026-05-17", "Won the Fury FC featherweight title by R4 rear-naked choke over Damon Jackson.", "mania_booking"),
        n("2024-10-01", "Submitted by Alberto Montes (anaconda choke, 2:38 R2) on the Contender Series after Montes took him "
                        "down; Montes got the contract.", "ufc_dwcs")],
       ["sbn_booking", "mania_booking", "si_booking", "sherdog_booking", "clutch_pick", "cage_dwcs_prev", "ufc_dwcs",
        "sbn_weighin"],
       "thin")


out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
