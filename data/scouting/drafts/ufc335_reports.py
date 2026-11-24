"""Scouting reports for UFC 335: Oliveira vs. Lopes (T-Mobile Arena, Las Vegas, 2026-12-12), plus the late
Luke Riley vs. Gabriel Santos addition to UFC Fight Night: Adesanya vs. Magomedov (Riyadh, 2026-12-05).
First pass written Tuesday 2026-11-24, two to three weeks out; no previews are out yet.

These draw on our verified fight records (data/verified/fights.csv: methods and rounds below are counted from it), the
booking coverage indexed by `scout news`, and the outlets cited per fighter. Fight-week runs should refresh them with
previews, odds and weigh-in news.

Data caveats, noted in the reports concerned:
- Charles Oliveira: our records merge some regional "Charles Oliveira" bouts from 2025 (Centurion FC, SFT, BRTL); only
  his UFC fights are used for recent form.
- Gabriel Santos: a 2025 Thunder Fight bout under the same name is a different fighter; only the featherweight's UFC and
  LFA fights are used.
- Quentin Pasley and Roque Conceição Moreira Jr. have no records in our data yet; their records come from Cageside
  Press's Contender Series coverage.
- Carli Judice's opponent is TBD after Maycee Barber withdrew.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATED = "2026-11-24T21:00:00+00:00"
EVENT = "UFC 335: Oliveira vs. Lopes"
EVENT_DEC5 = "UFC Fight Night: Adesanya vs. Magomedov"


def src(outlet, title, url, date, author=""):
    return {"outlet": outlet, "author": author, "title": title, "url": url, "date": date}


SRC = {
    "bjp_main": src("BJPenn.com", "UFC 335 main card confirmed, Charles Oliveira vs Diego Lopes officially headlines",
                    "https://www.bjpenn.com/mma-news/charles-oliveira/ufc-335-main-card-confirmed-charles-oliveira-vs-diego-lopes-officially-headlines/",
                    "2026-11-15"),
    "be_oliveira_title": src("Bloody Elbow", "Charles Oliveira expects 155lb title shot after UFC 335: 'I sell a lot more than Arman Tsarukyan'",
                             "https://bloodyelbow.com/2026/10/15/charles-oliveira-expects-155lb-title-shot-after-ufc-335-i-sell-a-lot-more-than-arman-tsarukyan/",
                             "2026-10-15"),
    "mmaf_bmf": src("MMA Fighting", "Charles Oliveira: If the BMF belt is about rock 'em sock 'em robots, 'take it somewhere else'",
                    "https://www.mmafighting.com/ufc/515678/charles-oliveira-if-the-bmf-belt-is-about-rock-em-sock-em-robots-take-it-somewhere-else",
                    "2026-10-17"),
    "bjp_lopes_lw": src("BJPenn.com", "Diego Lopes discusses the logistics of his upcoming lightweight move",
                        "https://www.bjpenn.com/mma-news/diego-lopes/diego-lopes-discusses-the-logistics-of-his-upcoming-lightweight-move/",
                        "2026-10-16"),
    "be_pereira_hw": src("Bloody Elbow", "Alex Pereira allegedly considered leaving heavyweight before booking UFC 335 matchup",
                         "https://bloodyelbow.com/2026/10/20/alex-pereira-allegedly-considered-leaving-heavyweight-before-booking-ufc-335-matchup/",
                         "2026-10-20"),
    "bjp_pavlovich": src("BJPenn.com", "Sergei Pavlovich teases 'surprises' for Alex Pereira in UFC 335 co-main fight",
                         "https://www.bjpenn.com/mma-news/sergey-pavlovich/sergei-pavlovich-teases-surprises-alex-pereira-ufc-335/",
                         "2026-10-16"),
    "mania_moreno": src("MMA Mania", "Brandon Moreno vs. Charles Johnson set for UFC 335",
                        "https://www.mmamania.com/ufc-news/478748/brandon-moreno-vs-charles-johnson-set-for-ufc-335", "2026-10-13"),
    "cage_moreno": src("Cageside Press", "Brandon Moreno Lands Charles Johnson at UFC 335",
                       "https://cagesidepress.com/2026/10/13/brandon-moreno-lands-charles-johnson-at-ufc-335/", "2026-10-13"),
    "junkie_pinas": src("MMA Junkie (via Yahoo)", "Damian Pinas gets his wish, meets Baisangur Susurkaev at UFC 335",
                        "https://sports.yahoo.com/articles/damian-pinas-gets-wish-meets-183030816.html", "2026-11-04"),
    "knockout_pinas": src("MMA Knockout (via Yahoo)", "UFC Knockout Artist Meets Undefeated Finishing Machine in Massive UFC 335 Fight",
                          "https://sports.yahoo.com/articles/ufc-knockout-artist-meets-undefeated-175731315.html", "2026-11-04"),
    "cage_dwcs5": src("Cageside Press", "Dana White's Contender Series Season 10, Week 5 Results",
                      "https://cagesidepress.com/2026/09/08/dana-whites-contender-series-season-10-week-5-results/", "2026-09-08"),
    "cage_dwcs9": src("Cageside Press", "Dana White's Contender Series Season 10, Week 9 Results",
                      "https://cagesidepress.com/2026/10/06/dana-whites-contender-series-season-10-week-9-results/", "2026-10-06"),
    "cage_roque": src("Cageside Press", "Redemption: Second Chances on Dana White's Contender Series — Roque Conceição",
                      "https://cagesidepress.com/2026/10/05/redemption-second-chances-dana-whites-contender-series-roque-conceicao/",
                      "2026-10-05", "Patrick Danna"),
    "mania_humphrey": src("MMA Mania", "Contender Series standout books Octagon debut for UFC 335",
                          "https://www.mmamania.com/ufc-fight-announcements/480986/contender-series-standout-ronald-humphrey-books-octagon-debut-for-ufc-335",
                          "2026-10-22"),
    "be_hill": src("Bloody Elbow", "30-fight UFC veteran added to Charles Oliveira and Alex Pereira's UFC 335 undercard",
                   "https://bloodyelbow.com/2026/10/29/30-fight-ufc-veteran-added-to-charles-oliveira-and-alex-pereiras-ufc-335-undercard/",
                   "2026-10-29"),
    "knockout_cavalcanti": src("MMA Knockout (via Yahoo)", "UFC Pushes Major Qatar Fight Back Several Weeks to UFC 335 in Las Vegas",
                               "https://sports.yahoo.com/articles/ufc-pushes-major-qatar-fight-180105863.html", "2026-11-02"),
    "sherdog_montague": src("Sherdog", "Undefeated Michelle Montague to face Jacqueline Cavalcanti at UFC Qatar",
                            "https://www.sherdog.com/news/news/Undefeated-Michelle-Montague-to-face-Jacqueline-Cavalcanti-at-UFC-Qatar-203418",
                            "2026-10-30"),
    "be_barber": src("Bloody Elbow", "UFC 335 down a fight with promotion looking to reschedule Maycee Barber's return according to report",
                     "https://bloodyelbow.com/2026/11/07/ufc-335-down-a-fight-with-promotion-looking-to-reschedule-maycee-barbers-return-according-to-report/",
                     "2026-11-07"),
    "knockout_riley": src("MMA Knockout (via Yahoo)", "Late UFC Saudi Arabia Addition Could Steal \"Fight of the Night\" Honors",
                          "https://sports.yahoo.com/articles/ufc-saudi-arabia-addition-could-151328484.html", "2026-11-22"),
    "data": src("Fight Lab verified records", "data/verified/fights.csv (Sherdog, UFCStats and Wikipedia, cross-checked)",
                "https://www.sherdog.com/", "2026-11-24"),
}


def slug(name):
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


R = {}


def report(name, summary, how, patterns, concerns, keys, news, sources, depth, event=EVENT):
    R[name] = {"name": name, "updated": UPDATED, "event": event, "summary": summary, "how_they_fight": how,
               "patterns": patterns, "concerns": concerns, "keys_to_beat": keys, "news": news,
               "sources": [SRC[k] for k in sources], "depth": depth}


def n(date, text, key):
    return {"date": date, "text": text, "source": SRC[key]["url"]}


# ---------------------------------------------------------------- main event: Oliveira vs. Lopes (lightweight, BMF title)
report("Charles Oliveira",
       "The former lightweight champion (age 37), a Chute Boxe Diego Lima veteran with the UFC records for submissions and "
       "finishes. Since losing to Ilia Topuria by R1 knockout in June 2025 he has submitted Mateusz Gamrot (R2) and "
       "out-pointed Max Holloway over five rounds for the BMF belt in March. He defends it against Diego Lopes and expects a "
       "title shot afterwards.",
       {"Striking": "Aggressive Muay Thai: knees, elbows and long combinations behind pressure. Eleven knockouts, seven of "
                    "them in R1, in our UFC-era data.",
        "Grappling": "Elite: 23 submission wins, 12 of them in R1, from guard pulls, scrambles and the back. The threat "
                     "shapes every exchange.",
        "Defense": "Hittable early: stopped in R1 by Topuria (2025) and Makhachev (submission, R2, 2022), and he often "
                   "survives early knockdowns. His chin has been tested many times.",
        "Pace & cardio": "Has gone five rounds twice recently (Chandler, Holloway), winning both clearly.",
        "Fight IQ": "Takes risks; dangerous off his back and in scrambles."},
       ["Finishes early: most of his submissions come in R1-R2",
        "Five-round decision wins over Chandler and Holloway"],
       ["Age 37; stopped quickly by Topuria in 2025",
        "Hurt early in many fights"],
       ["Hurt him early on the feet, but stay out of scrambles",
        "Do not follow him to the ground"],
       [n("2026-10-15", "Says he expects a lightweight title shot after UFC 335 and sells more than Arman Tsarukyan.",
          "be_oliveira_title"),
        n("2026-10-17", "Says the BMF belt should not be about pure brawls.", "mmaf_bmf")],
       ["bjp_main", "be_oliveira_title", "mmaf_bmf", "data"], "moderate")

report("Diego Lopes",
       "A Brazilian featherweight from Lobo Gym in Mexico (28-8, age 31), moving up to lightweight. He lost two five-round "
       "decisions to Alexander Volkanovski for the featherweight title (April 2025 and January 2026), and in between and "
       "since knocked out Jean Silva (R2) and Steve Garcia (R2, June).",
       {"Striking": "Wild, powerful and creative: spinning attacks and heavy hooks. Twelve knockouts, six in R1 and five in R2.",
        "Grappling": "A real submission threat: twelve submissions, nine in R1, often off scrambles and from his back.",
        "Defense": "Stopped twice, both in R2 (early career). Gets hit in exchanges but recovers.",
        "Pace & cardio": "Kept pace over five rounds twice with Volkanovski but lost both on the cards.",
        "Fight IQ": "Takes risks to finish; can be out-pointed by technical boxers."},
       ["Fast finisher: R1-R2 knockouts and submissions", "Dangerous in scrambles"],
       ["First fight at 155 against a bigger, elite grappler", "Lost both five-round decisions to Volkanovski"],
       ["Out-point him with clean, disciplined boxing", "Beat him in the scrambles he invites"],
       [n("2026-10-16", "Discussed the logistics of moving up to lightweight for this fight.", "bjp_lopes_lw")],
       ["bjp_main", "bjp_lopes_lw", "data"], "moderate")

# ---------------------------------------------------------------- co-main: Pavlovich vs. Pereira (heavyweight)
report("Sergei Pavlovich",
       "A Russian heavyweight from Eagles MMA (21-3, age 34) with one of the division's hardest right hands. After losing "
       "to Tom Aspinall (R1 KO) and Alexander Volkov (decision), he won decisions over Rozenstruik and Cortes-Acosta and "
       "knocked out Tallison Teixeira in 39 seconds in May. He has promised Alex Pereira 'surprises'.",
       {"Striking": "Explosive overhand rights and blitzes. All 16 of his knockouts came in R1.",
        "Grappling": "Rarely wrestles; strong enough to defend takedowns.",
        "Defense": "Stopped once (Aspinall, R1). Volkov out-pointed him at range.",
        "Pace & cardio": "Five decision wins, three of them recent: he can go three rounds, but his danger is early.",
        "Fight IQ": "Blitz puncher; fights in bursts."},
       ["R1 knockouts (all 16 finishes)", "Decision wins when the early blitz doesn't land"],
       ["Out-pointed at range (Volkov)", "Knocked out in R1 by a faster heavyweight (Aspinall)"],
       ["Survive the first five minutes and work him at range"],
       [n("2026-10-16", "Teased 'surprises' for Alex Pereira and released a training video.", "bjp_pavlovich")],
       ["bjp_pavlovich", "be_pereira_hw", "data"], "moderate")

report("Alex Pereira",
       "The former two-division champion (age 39), a kickboxer who won the middleweight and light heavyweight titles. He "
       "moved to heavyweight in 2026 and was knocked out by Ciryl Gane in R2 in June. Bloody Elbow reported he considered "
       "leaving heavyweight before this booking.",
       {"Striking": "Elite left hook, calf kicks and counters. Twelve knockouts in our data, nine of them in R1-R2.",
        "Grappling": "A defensive grappler; Adesanya and Ankalaev beat him by pressure and control.",
        "Defense": "Stopped three times: twice in R2 (Adesanya, Gane) and once by submission (R3, early career).",
        "Pace & cardio": "Has finished in R4 and R5; slows when pressed.",
        "Fight IQ": "Patient, waits for counters; dangerous at any moment."},
       ["Left hook counters; knockouts in R1-R2", "Late knockouts in title fights (R4, R5)"],
       ["Age 39; second heavyweight fight after being knocked out by Gane",
        "Smaller than most heavyweights"],
       ["Pressure him and test him early with power", "Make him carry heavyweight size for three rounds"],
       [n("2026-10-20", "Reportedly considered leaving heavyweight before this fight was booked.", "be_pereira_hw")],
       ["be_pereira_hw", "bjp_pavlovich", "data"], "moderate")

# ---------------------------------------------------------------- Moreno vs. Johnson (flyweight)
report("Brandon Moreno",
       "The former flyweight champion from Mexico (24-12, age 32). Since 2025 he has lost to Tatsuro Taira (R2 TKO) and "
       "Lone'er Kavanagh (five-round decision), then won a split decision over Joseph Morales at Noche UFC in September.",
       {"Striking": "Busy boxer with good head movement; six knockouts, three of them in R3.",
        "Grappling": "Strong: eleven submissions, seven of them in R1, mostly from the back.",
        "Defense": "Stopped once since 2018 (Taira, R2). Many of his losses are decisions (seven, plus two split five-rounders).",
        "Pace & cardio": "Built for five rounds; often slow to start and stronger late.",
        "Fight IQ": "Experienced, adaptable; very close fights."},
       ["Close decisions; stronger as the fight goes on", "Late stoppages (R3 knockouts of Kara-France and Figueiredo)"],
       ["Two losses in his last three; a split win over Morales", "Taira stopped him in R2"],
       ["Win early rounds with volume; deny his back takes"],
       [n("2026-10-13", "Booked against Charles Johnson at UFC 335.", "mania_moreno")],
       ["mania_moreno", "cage_moreno", "data"], "moderate")

report("Charles Johnson",
       "An American flyweight (20-9, age 35), 5-4 in his last nine UFC fights. He was knocked out by Alex Perez (R1) and "
       "submitted by Asu Almabayev (R3) this year, but beat Bruno Silva (split) and submitted Eduardo Henrique (R3) in August.",
       {"Striking": "Long, busy boxer; nine knockouts, spread across R1 to R5.",
        "Grappling": "Opportunistic: four submissions, two of them late.",
        "Defense": "Stopped twice recently (Perez R1 KO, Almabayev R3 submission); six decision losses.",
        "Pace & cardio": "Goes the distance often and has late finishes (R3, R5).",
        "Fight IQ": "Volume over power."},
       ["Late finishes (R3 and later)", "Wins close decisions on volume"],
       ["Stopped twice in 2026", "Age 35"],
       ["Wrestle and control him; take his back"],
       [n("2026-10-13", "Booked against Brandon Moreno at UFC 335.", "cage_moreno")],
       ["cage_moreno", "data"], "moderate")

# ---------------------------------------------------------------- Phillips vs. Ewing (bantamweight)
report("Kyler Phillips",
       "An American bantamweight from MMA Lab (12-5, age 31) on a three-fight losing streak, all decisions: Rob Font, "
       "Vinicius Oliveira and Charles Jourdain (April).",
       {"Striking": "Long, creative kickboxer with spinning attacks; five knockouts, four in R1.",
        "Grappling": "Two submissions; good wrestling for the division.",
        "Defense": "Never stopped: all five losses are decisions (two split).",
        "Pace & cardio": "Goes three rounds comfortably.",
        "Fight IQ": "Technical; struggles to separate himself on the cards."},
       ["Decisions both ways (five decision wins, five decision losses)", "Early knockouts when he lands"],
       ["Three straight decision losses"],
       ["Out-work him on the cards"],
       [n("2026-11-15", "Added to the UFC 335 main card against Ethyn Ewing.", "bjp_main")],
       ["bjp_main", "data"], "moderate")

report("Ethyn Ewing",
       "An American bantamweight (10-2, age 28), 2-0 in the UFC: a decision over Malcolm Wellmaker (November 2025) and a R3 "
       "TKO of Rafael Estevam (April). This is his biggest step up.",
       {"Striking": "Seven knockouts, spread across all three rounds (three in R1, two in R2, two in R3).",
        "Grappling": "One submission; mostly a striker.",
        "Defense": "Stopped once (submission, R1, early career).",
        "Pace & cardio": "Late finishes: knockouts in R3 against Estevam and Carrillo.",
        "Fight IQ": "Patient, builds through the fight."},
       ["Finishes late as well as early (two R3 knockouts)"],
       ["First ranked-level opponent"],
       ["Out-class him technically and on the cards"],
       [n("2026-11-15", "Added to the UFC 335 main card against Kyler Phillips.", "bjp_main")],
       ["bjp_main", "data"], "moderate")

# ---------------------------------------------------------------- Pinas vs. Susurkaev (middleweight)
report("Baisangur Susurkaev",
       "An unbeaten Chechen middleweight from Kill Cliff FC (12-0, age 25), a Khamzat Chimaev teammate. 3-0 in the UFC since "
       "his Contender Series win: a R2 submission of Eric Nolan, a R3 TKO of Eric McConico and a R3 submission of Djorden "
       "Santos in May.",
       {"Striking": "Nine knockouts, seven of them in R1 (mostly regional).",
        "Grappling": "Two submissions, both in the UFC (R2, R3).",
        "Defense": "Never stopped or beaten.",
        "Pace & cardio": "His UFC finishes all came in R2-R3: he wears opponents down.",
        "Fight IQ": "Pressure fighter."},
       ["Late finishes in the UFC (R2, R3, R3)", "Early knockouts on the regional scene"],
       ["Untested against a power puncher like Pinas"],
       ["Hurt him early, before his pressure builds"],
       [n("2026-11-04", "Booked against Damian Pinas, who called him an 'easy' fight.", "junkie_pinas")],
       ["junkie_pinas", "knockout_pinas", "data"], "moderate")

# ---------------------------------------------------------------- Pasley vs. Tafa (light heavyweight)
report("Quentin Pasley",
       "An American light heavyweight who won his UFC contract on the Contender Series in September with a R1 knockout of "
       "Arlind Berisha (4:41). He was 3-0 before that, with kickboxing, grappling and a 38-second boxing knockout in June. "
       "This is his UFC debut. Our data has no record for him yet.",
       {"Striking": "A puncher; his Contender Series win was a R1 knockout.",
        "Grappling": "Has competed in grappling; untested in MMA.",
        "Defense": "Unbeaten in MMA.",
        "Pace & cardio": "Untested past R1 in the UFC.",
        "Fight IQ": "Inexperienced: four pro MMA fights."},
       ["Early knockouts"],
       ["Very thin MMA record (4-0)", "UFC debut"],
       ["Take him into deep water and test his grappling"],
       [n("2026-09-08", "Won a UFC contract with a R1 knockout of Arlind Berisha on the Contender Series.", "cage_dwcs5")],
       ["cage_dwcs5"], "thin")

report("Junior Tafa",
       "A New Zealand heavyweight/light heavyweight from NTG (7-6, age 30), 3-6 in the UFC. He knocked out Kevin Christian "
       "(R1) in May, then was knocked out by Iwo Baraniewski (R1) in June.",
       {"Striking": "A kickboxer with power: all seven wins are knockouts (five in R1).",
        "Grappling": "Weak: submitted three times (Walker R1, Tokkos R2, Elekana R2).",
        "Defense": "Stopped five times, two of them by knockout.",
        "Pace & cardio": "Fades when the fight goes to the ground.",
        "Fight IQ": "Striker only."},
       ["R1 knockouts", "Submitted when taken down (three times)"],
       ["Lost five of his last seven", "No ground defence"],
       ["Take him down: three submission losses"],
       [],
       ["data"], "moderate")

# ---------------------------------------------------------------- Hooper vs. Padilla (lightweight)
report("Chase Hooper",
       "An American lightweight grappler (17-6, age 27). He was knocked out in R1 twice in a row (Alexander Hernandez, "
       "Lance Gibson Jr.) before submitting Mitch Ramirez (R1) in July.",
       {"Striking": "Improved but limited; three knockouts.",
        "Grappling": "Excellent: nine submissions, six of them in R1 (Leavitt, Guida, Ramirez).",
        "Defense": "Three R1 knockout losses (Garcia, Hernandez, Gibson).",
        "Pace & cardio": "Fine over three rounds (decision wins over Fiore and Miller).",
        "Fight IQ": "Lives on the mat."},
       ["R1 submissions", "Knocked out early by powerful strikers"],
       ["Three R1 knockout losses"],
       ["Keep it standing and hit him early"],
       [],
       ["data"], "moderate")

report("Chris Padilla",
       "An American lightweight (18-7, age 31), 5-0-1 in his last six UFC fights. He drew with MarQuel Mederos in April and "
       "submitted Nasrat Haqparast with a second left in R3 in August.",
       {"Striking": "Long and powerful: nine knockouts (six in R1).",
        "Grappling": "Six submissions, including a R3 finish of Haqparast.",
        "Defense": "Stopped three times (one KO, two submissions) in his early career.",
        "Pace & cardio": "Finishes late as well as early.",
        "Fight IQ": "Well-rounded, aggressive."},
       ["R1 knockouts; late submissions"],
       ["Has been submitted twice"],
       ["Drag him into a grappling match"],
       [],
       ["data"], "moderate")

# ---------------------------------------------------------------- Humphrey vs. Veretennikov (welterweight)
report("Ronald Humphrey",
       "An unbeaten American welterweight from ATT Atlanta (5-0, age 26) who won his contract on the Contender Series in "
       "August with a R1 submission. UFC debut.",
       {"Striking": "Four knockouts, three in R1.",
        "Grappling": "R1 submission on the Contender Series.",
        "Defense": "Never beaten.",
        "Pace & cardio": "Has not been past R2 as a pro.",
        "Fight IQ": "Five pro fights."},
       ["Every win a finish, four in R1"],
       ["Untested past R2", "UFC debut"],
       ["Drag him into R3"],
       [n("2026-10-22", "Booked for his UFC debut against Nikolay Veretennikov.", "mania_humphrey")],
       ["mania_humphrey", "data"], "thin")

report("Nikolay Veretennikov",
       "A Kazakh welterweight from Kings MMA (14-8, age 36), 2-3 in the UFC: he knocked out Niko Price (R1) in February, then "
       "was knocked out by Kalinn Williams (R1) in May.",
       {"Striking": "Ten knockouts, six in R1.",
        "Grappling": "One submission.",
        "Defense": "Stopped three times by knockout, two of them recent (Vanderford R2, Williams R1).",
        "Pace & cardio": "Goes the distance with fellow strikers.",
        "Fight IQ": "Kickboxer."},
       ["R1 knockouts"],
       ["Age 36; knocked out twice in his last four"],
       ["Pressure him and test his chin"],
       [n("2026-10-22", "Booked against Contender Series winner Ronald Humphrey.", "mania_humphrey")],
       ["mania_humphrey", "data"], "moderate")

# ---------------------------------------------------------------- Conceição vs. Rojas (flyweight)
report("Roque Conceição Moreira Jr.",
       "A Brazilian flyweight (12-3 after his Contender Series win), a former Demo Fight and Thunder Fight champion. He was "
       "knocked out on his first Contender Series appearance, then won his contract in October with a R1 triangle choke of "
       "Alexander Chavez. UFC debut. Our data has no record for him yet.",
       {"Striking": "Was out-boxed and knocked out in his first Contender Series fight.",
        "Grappling": "Triangle-choke submission on the Contender Series.",
        "Defense": "Three losses: a knockout and two decisions.",
        "Pace & cardio": "Untested in the UFC.",
        "Fight IQ": "Grappling-first."},
       ["R1 submissions"],
       ["Knocked out by a boxer on his first Contender Series appearance"],
       ["Box him at range"],
       [n("2026-10-06", "Won a UFC contract with a R1 triangle choke of Alexander Chavez.", "cage_dwcs9")],
       ["cage_dwcs9", "cage_roque"], "thin")

report("Nilson Rojas",
       "A Peruvian flyweight from Pitbull MAC (9-1, age 27). He lost his UFC debut to Bilal Hasan by R2 TKO in August.",
       {"Striking": "Seven knockouts, four in R1.",
        "Grappling": "No submissions in our data.",
        "Defense": "Stopped once (Hasan, R2).",
        "Pace & cardio": "One decision win in his last two.",
        "Fight IQ": "Striker."},
       ["R1 knockouts on the regional scene"],
       ["Stopped in his UFC debut", "No submission game"],
       ["Take him down"],
       [],
       ["data"], "thin")

# ---------------------------------------------------------------- Hill vs. Dyer (strawweight)
report("Angela Hill",
       "A 30-fight UFC strawweight veteran (19-16, age 41) who beat Jingnan Xiong by decision in May after two decision "
       "losses. Twelve of her last fourteen fights went the distance.",
       {"Striking": "Muay Thai volume; five knockouts, none recent.",
        "Grappling": "One submission; defends well.",
        "Defense": "Never knocked out; two submission losses, both in R1, early career.",
        "Pace & cardio": "Elite pace over three and five rounds.",
        "Fight IQ": "Veteran, technical."},
       ["Decisions both ways"],
       ["Age 41"],
       ["Out-work her with power and takedowns"],
       [n("2026-10-29", "Added to UFC 335 against Shanelle Dyer.", "be_hill")],
       ["be_hill", "data"], "moderate")

report("Shanelle Dyer",
       "An English strawweight from Great Britain Top Team (8-1, age 25), 2-0 in the UFC with knockouts of Ravena Oliveira "
       "(R2) and Elise Reed (R3). Her only loss was a decision on the Contender Series.",
       {"Striking": "Six knockouts, including two in R3.",
        "Grappling": "No submissions.",
        "Defense": "Never stopped.",
        "Pace & cardio": "Finishes late (two R3 knockouts).",
        "Fight IQ": "Aggressive striker."},
       ["Late knockouts"],
       ["First veteran opponent"],
       ["Out-point her with volume"],
       [n("2026-10-30", "Booked against Angela Hill.", "be_hill")],
       ["be_hill", "data"], "moderate")

# ---------------------------------------------------------------- Cavalcanti vs. Montague (bantamweight)
report("Jacqueline Cavalcanti",
       "A Brazilian bantamweight from Syndicate MMA (10-2, age 29), 6-1 in the UFC. She lost a decision to Ketlen Vieira in "
       "May. This fight was moved from UFC Qatar to UFC 335.",
       {"Striking": "Long, busy boxer; three knockouts (two in R1).",
        "Grappling": "No submissions; defends takedowns well.",
        "Defense": "Never stopped: both losses on the cards.",
        "Pace & cardio": "Seven decision wins.",
        "Fight IQ": "Volume and distance."},
       ["Decisions"],
       ["Close decisions both ways"],
       ["Take her down and hold her"],
       [n("2026-11-02", "Her fight with Michelle Montague moved from UFC Qatar to UFC 335.", "knockout_cavalcanti")],
       ["knockout_cavalcanti", "sherdog_montague", "data"], "moderate")

report("Michelle Montague",
       "An unbeaten New Zealand bantamweight from ATT (8-0, age 33), 2-0 in the UFC with decisions over Luana Carolina and "
       "Mayra Bueno Silva. Six of her eight wins are submissions.",
       {"Striking": "Functional.",
        "Grappling": "Six submissions (three in R1).",
        "Defense": "Never beaten.",
        "Pace & cardio": "Both UFC wins went the distance.",
        "Fight IQ": "Grappler."},
       ["Submissions; decisions in the UFC"],
       ["UFC opponents have survived her grappling"],
       ["Stuff her takedowns and win at range"],
       [n("2026-10-30", "Booked against Jacqueline Cavalcanti.", "sherdog_montague")],
       ["sherdog_montague", "knockout_cavalcanti", "data"], "moderate")

# ---------------------------------------------------------------- Judice vs. TBD (flyweight)
report("Carli Judice",
       "An American flyweight from Headkicks MMA (7-2, age 27), 4-1 in the UFC with knockouts of Duben (R1), Caliari (R3) and "
       "Chaves (R1, August). Maycee Barber withdrew from their UFC 335 fight; her new opponent is not yet named.",
       {"Striking": "Six knockouts, five in R1.",
        "Grappling": "No submissions.",
        "Defense": "Never stopped: both losses are split decisions.",
        "Pace & cardio": "Has gone three rounds four times.",
        "Fight IQ": "Power striker."},
       ["R1 knockouts"],
       ["Split-decision losses to grapplers"],
       ["Wrestle her"],
       [n("2026-11-07", "Maycee Barber withdrew from their fight; the UFC is looking for a replacement.", "be_barber")],
       ["be_barber", "data"], "moderate")

# ---------------------------------------------------------------- Dec 5: Riley vs. Santos (featherweight)
report("Luke Riley",
       "An unbeaten English featherweight from Next Generation Liverpool (14-0, age 27), a Paddy Pimblett teammate. 3-0 in "
       "the UFC: a R2 knockout of Bogdan Grad (bonus), a decision over Michael Aswell and a R1 knockout of Kai Kamaka III "
       "in July. Added two weeks out.",
       {"Striking": "Ten knockouts: five in R1, four in R2, one in R3.",
        "Grappling": "No submissions; a striker first.",
        "Defense": "Never beaten.",
        "Pace & cardio": "Four decision wins; can go three rounds.",
        "Fight IQ": "Aggressive, entertaining striker."},
       ["R1-R2 knockouts"],
       ["Short notice (two weeks)"],
       ["Grapple with him"],
       [n("2026-11-22", "Added to UFC Saudi Arabia two weeks out against Gabriel Santos.", "knockout_riley")],
       ["knockout_riley", "data"], "moderate", EVENT_DEC5)

report("Gabriel Santos",
       "A Brazilian featherweight from Chute Boxe Diego Lima (10-0 before the UFC), 2-2 in the UFC: a split loss to Lerone "
       "Murphy, a R2 knockout by David Onama, then a decision over Zha Yi and a R3 submission of Jack Jenkins (UFC 312, "
       "February 2025). He has not fought since, nearly 22 months.",
       {"Striking": "Three knockouts.",
        "Grappling": "Five submissions, four in R1.",
        "Defense": "Stopped by Onama (R2) and submitted once (early career).",
        "Pace & cardio": "Late finishes (R3 submission of Jenkins).",
        "Fight IQ": "Well-rounded."},
       ["R1 submissions; late finishes"],
       ["Nearly two years out"],
       ["Pressure him early after the layoff"],
       [n("2026-11-22", "Returns against Luke Riley at UFC Saudi Arabia.", "knockout_riley")],
       ["knockout_riley", "data"], "moderate", EVENT_DEC5)


out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
