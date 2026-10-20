"""Scouting reports for UFC Fight Night: Moicano vs. Nolan (UFC Vegas 123, 2026-10-31), batch C, written 2026-10-20.

Fighters: Joseph Kropschot, Talita Alencar, Piera Rodriguez, Lucia Szabova, Tainara Lisboa, Francis Marshall.
Records, results, methods and rounds are from our verified fight data; outlet coverage is cited inline.
Fight-week previews (UFC.com, Sherdog, MMA Mania) were not out yet; the Friday run should fold them in.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATED = "2026-10-20T18:00:00+00:00"
EVENT = "UFC Fight Night: Moicano vs. Nolan"


def slug(name):
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def src(outlet, author, title, url, date):
    return {"outlet": outlet, "author": author, "title": title, "url": url, "date": date}


S = {
    # Kropschot
    "lk_kropschot": src("LowKick MMA", "Subham", "Joe Kropschot Snaps Jon Kunneman's Arm at Dana White's Contender Series Season 10, Week 1",
                        "https://www.lowkickmma.com/joe-kropschot-snaps-jon-kunnemans-arm-at-dana-whites-contender-series-season-10-week-1/", "2026-08-11"),
    "cage_dwcs": src("Cageside Press", "", "Dana White's Contender Series Season 10, Week 1 Results",
                     "https://cagesidepress.com/2026/08/11/dana-whites-contender-series-season-10-week-1-results/", "2026-08-11"),
    "lfa_226": src("LFA", "", "Kropschot Takes the Belt in LFA 226", "https://www.lfa.com/kropschot-takes-the-belt-in-lfa-226/", "2026-02-06"),
    "bn_kropschot": src("Boxing News", "MMA News Staff", "Kropschot Books UFC Debut Against Klein",
                        "https://boxingnews.com/news/kropschot-ufc-debut-klein-october/", "2026-08-26"),
    "roto_kropschot": src("Rotowire", "", "Joe Kropschot MMA Stats & News", "https://www.rotowire.com/mma/player/joe-kropschot-2816", "2026-08-25"),
    # Alencar
    "cage_alencar_carnelossi": src("Cageside Press", "Jay Anderson", "UFC Vegas 110: Talita Alencar Overcomes Cardio Issues, Subs Ariane Carnelossi",
                                   "https://cagesidepress.com/2025/11/01/ufc-vegas-110-talita-alencar-overcomes-cardio-issues-subs-ariane-carnelossi", "2025-11-01"),
    "cage_luciano": src("Cageside Press", "", "Stephanie Luciano Kicks Off UFC Vegas 95 by Defeating Talita Alencar in Rematch",
                        "https://cagesidepress.com/2024/08/10/stephanie-luciano-kicks-off-ufc-vegas-95-by-defeating-talita-alencar-in-rematch", "2024-08-10"),
    "bjp_vegas116": src("BJPenn.com", "", "UFC Vegas 116: 'Sterling vs. Zalal' Live Results and Highlights",
                        "https://www.bjpenn.com/mma-news/ufc-vegas-116/ufc-vegas-116-sterling-vs-zalal-live-results-and-highlights/", "2026-04-25"),
    "roto_alencar": src("Rotowire", "", "Talita Alencar MMA Stats & News", "https://www.rotowire.com/mma/player/talita-alencar-2522", "2026-09-24"),
    "wiki_alencar": src("Wikipedia", "", "Talita Alencar", "https://en.wikipedia.org/wiki/Talita_Alencar", "2026-10-03"),
    "agent_alencar_rodriguez": src("AgentMMA", "Oscar Nascimento", "Talita Alancar vs Piera Rodriguez Targeted for UFC Vegas 123",
                                   "https://agentmma.com/news/89843-talita-alancar-vs-piera-rodriguez-targeted-for-ufc-vegas-123", "2026-09-10"),
    # Rodriguez
    "cage_rodriguez_hughes": src("Cageside Press", "Eddie Law", "Piera Rodriguez Outworks Sam Hughes for Unanimous Decision Win",
                                 "https://cagesidepress.com/2026/03/14/piera-rodriguez-outworks-sam-hughes-for-unanimous-decision-win", "2026-03-14"),
    "cage_rodriguez_souza": src("Cageside Press", "", "Piera Rodriguez Controls Souza to a Split-Decision Victory",
                                "https://cagesidepress.com/2025/08/02/piera-rodriguez-controls-souza-to-a-split-decision-victory/", "2025-08-02"),
    "lk_rodriguez_souza": src("LowKick MMA", "", "Piera Rodriguez Scores Close Split Decision Win Over Ketlen Souza - UFC Vegas 108 Highlights",
                              "https://www.lowkickmma.com/piera-rodriguez-vs-ketlen-souza-ufc/", "2025-08-02"),
    "cage_rodriguez_knutsson": src("Cageside Press", "", "Piera Rodriguez Uses Improved Wrestling, Dominates Knutsson",
                                   "https://cagesidepress.com/2024/12/14/piera-rodriguez-uses-improved-wrestling-dominates-knutsson", "2024-12-14"),
    "bjp_vegas92": src("BJPenn.com", "", "UFC Vegas 92: 'Barboza vs. Murphy' Live Results and Highlights",
                       "https://www.bjpenn.com/mma-news/ufc-vegas-92/ufc-vegas-92-barboza-vs-murphy-live-results-and-highlights/", "2024-05-18"),
    "cage_robertson": src("Cageside Press", "", "UFC Kansas City: Gillian Robertson Arm-Bars Piera Rodriguez to Extend Submissions Record",
                          "https://cagesidepress.com/2023/04/15/ufc-kansas-city-gillian-robertson-vs-piera-rodriguez/", "2023-04-15"),
    "roto_rodriguez": src("Rotowire", "", "Piera Rodriguez MMA Stats & News", "https://www.rotowire.com/mma/player/piera-rodriguez-2253", "2026-09-24"),
    # Szabova
    "sucka_szabova": src("MMA Sucka", "Felipe Castello Branco", "Lucia Szabova Signs With UFC, Set to Face Tainara Lisboa in Debut",
                         "https://mmasucka.com/news/lucia-szabova-signs-with-ufc-set-to-face-tainara-lisboa-in-debut/", "2026-08-22"),
    "agent_szabova": src("AgentMMA", "", "Unbeaten Oktagon Two-Division Champion Lucia Szabova Signs With UFC",
                         "https://agentmma.com/news/88663-unbeaten-oktagon-two-division-champion-lucia-szabova-signs-with-ufc", "2026-08-21"),
    "lk_szabova_fernandes": src("LowKick MMA", "Craig Pekios", "History Made! Lucia Szabova Smashes Leidiane Fernandes to Claim Flyweight Gold - Oktagon 87 Highlights",
                                "https://www.lowkickmma.com/lucia-szabova-vs-fernandes-oktagon-87/", "2026-04-25"),
    "cage_szabova_pudilova": src("Cageside Press", "Jay Anderson", "Oktagon Double Champ Szabova to Face UFC Vet Pudilova",
                                 "https://cagesidepress.com/2026/05/26/oktagon-double-champ-szabova-to-face-ufc-vet-pudilova/", "2026-05-26"),
    "cage_okt92": src("Cageside Press", "", "Oktagon 92: Szabova vs. Pudilova Full Results",
                      "https://cagesidepress.com/2026/08/01/oktagon-92-szabova-vs-pudilova-full-results/", "2026-08-01"),
    "sherdog_szabova": src("Sherdog", "", "Lucia Szabova fighter profile", "https://www.sherdog.com/fighter/Lucia-Szabova-363981", "2026-08-01"),
    "bn_card": src("Boxing News", "", "UFC Vegas 123 Card Set for Oct. 31 at Apex",
                   "https://boxingnews.com/news/ufc-vegas-123-moicano-nolan-fight-card/", "2026-09-24"),
    # Lisboa
    "cage_croden_lisboa": src("Cageside Press", "", "Melissa Croden Makes Statement in UFC Debut, Stops Tainara Lisboa in Vancouver",
                              "https://cagesidepress.com/2025/10/18/melissa-croden-makes-statement-in-ufc-debut-stops-tainara-lisboa-in-vancouver", "2025-10-18"),
    "lk_croden_lisboa": src("LowKick MMA", "", "Hometown Hero Melissa Croden Crushes Tainara Lisboa in Round 3 - UFC Vancouver Highlights",
                            "https://www.lowkickmma.com/hometown-hero-melissa-croden-crushes-tainara-lisboa-in-round-3-ufc-vancouver-highlights/", "2025-10-18"),
    "bjp_vegas106": src("BJPenn.com", "", "UFC Vegas 106: 'Burns vs. Morales' Live Results and Highlights",
                        "https://www.bjpenn.com/mma-news/ufc-vegas-106/ufc-vegas-106-burns-vs-morales-live-results-and-highlights/", "2025-05-17"),
    "cage_lisboa_clark": src("Cageside Press", "", "UFC Charlotte: Tainara Lisboa Endures Nasty Cut, Submits Jessica-Rose Clark",
                             "https://cagesidepress.com/2023/05/13/ufc-charlotte-jessica-rose-clark-vs-tainara-lisboa", "2023-05-13"),
    "roto_lisboa": src("Rotowire", "", "Tainara Lisboa MMA Stats & News", "https://www.rotowire.com/mma/player/tainara-lisboa-2299", "2026-08-21"),
    # Marshall
    "mania_bolanos": src("MMA Mania", "", "Pic: Nasty cut boots Gaston Bolanos from UFC Vegas 123, replacement steps in",
                         "https://www.mmamania.com/ufc-fight-announcements/477582/pic-nasty-cut-boots-gaston-bolanos-from-ufc-vegas-123-replacement-steps-in", "2026-10-08"),
    "heavy_marshall": src("Heavy", "Marcel Dorff", "Francis Marshall Draws New Opponent for UFC Halloween Event",
                          "https://heavy.com/sports/ufc/francis-marshall-new-opponent-ufc-halloween/", "2026-10-08"),
    "ufc_marshall_mexico": src("UFC.com", "Simon Head", "Francis Marshall Wants to Make It Emphatic at UFC Mexico",
                               "https://www.ufc.com/news/francis-marshall-wants-make-it-emphatic-ufc-mexico", "2026-02-25"),
    "ufc_marshall_313": src("UFC.com", "Thomas Gerbasi", "Francis Marshall Ready for His Breakthrough Moment at UFC 313",
                            "https://www.ufc.com/news/francis-marshall-ready-for-his-breakthrough-moment-ufc-313", "2025-03-07"),
    "cage_marshall_brennan": src("Cageside Press", "", "UFC Vegas 116: Francis Marshall Turns Back Bellator Standout Lucas Brennan",
                                 "https://cagesidepress.com/2026/04/25/ufc-vegas-116-francis-marshall-turns-back-bellator-standout-lucas-brennan/", "2026-04-25"),
    "cage_marshall_santos": src("Cageside Press", "", "Mairon Santos Gets Split Nod Over Marshall, Fans Disagree",
                                "https://cagesidepress.com/2025/03/08/mairon-santos-gets-split-nod-over-marshall-crowd-boos", "2025-03-08"),
    "cage_dulgarian": src("Cageside Press", "", "UFC Vegas 78: Isaac Dulgarian Earns Another First Round Finish, Stops Francis Marshall in Debut",
                          "https://cagesidepress.com/2023/08/12/ufc-vegas-78-francis-marshall-vs-isaac-dulgarian", "2023-08-12"),
    "bjp_mexico": src("BJPenn.com", "", "UFC Mexico City: 'Moreno vs. Kavanagh' Live Results and Highlights",
                      "https://www.bjpenn.com/mma-news/ufc-mexico/ufc-mexico-city-moreno-vs-kavanagh-live-results-and-highlights/", "2026-02-28"),
    "es_vegas123": src("EssentiallySports", "", "Matchmakers scramble for replacements as multiple fighters pull out from UFC 334 and Vegas 123",
                       "https://www.essentiallysports.com/ufc-mma-news-matchmakers-scramble-for-replacements-as-multiple-fighters-pull-out-from-ufc-334-and-vegas-123/", "2026-10-09"),
}

R = {}


def report(name, summary, how, patterns, concerns, keys, news, sources, depth):
    R[name] = {"name": name, "updated": UPDATED, "event": EVENT, "summary": summary, "how_they_fight": how,
               "patterns": patterns, "concerns": concerns, "keys_to_beat": keys, "news": news,
               "sources": [S[k] for k in sources], "depth": depth}


# ---------------------------------------------------------------- Joseph Kropschot
report(
    "Joseph Kropschot",
    "A 31-year-old California middleweight (9-3) making his UFC debut off a Contender Series decision over the unbeaten Jon Kunneman; "
    "he came in as the reigning LFA middleweight champion after choking out David Allakhverdiev in February. A submission finisher by "
    "record (six subs, two KOs), with a five-fight win streak, but all three of his losses were stoppages.",
    {"Striking": "Against Kunneman he kickboxed from range: a long jab, leg kicks and body work, building output as the fight went on (per LowKick MMA). "
                 "Rotowire lists a 79-inch reach (we have no verified reach). Only two KO wins, both in the first round on the regionals.",
     "Grappling": "The finishing tool: six submission wins, four of them in round two, including a rear-naked choke on the previously unbeaten "
                  "LFA champion Allakhverdiev (LFA). On the Contender Series he landed an early round-two takedown but couldn't hold it, then "
                  "answered a late Kunneman takedown by rolling into an armbar that dislocated Kunneman's arm; Kunneman didn't tap (per LowKick MMA). "
                  "Rotowire calls him a fighter who prefers to work on the ground.",
     "Defense": "Hittable. Kunneman dropped him with a right hook in round two and bloodied him with follow-up combinations (per LowKick MMA; our "
                "verified data has no strike totals for that bout). Stopped three times: KO/TKO by Orion Cosce (R3, 2019), a submission by "
                "Cody Brundage (R3, 2021) and a KO/TKO by Daniel Compton (R1, 2021; time not recorded).",
     "Pace & cardio": "Middle-rounds finisher: of eight stoppage wins, four came in R1 (all 2018-2023 regionals) and four in R2 (his last four "
                      "finishes, 2019-2026). The Kunneman fight is the only time he has gone to the scorecards (Boxing News agrees), and he "
                      "won the third round on output after being dropped in the second. His losses lean late: two of three stoppage losses "
                      "came in R3, one in R1.",
     "Fight IQ": "Showed he can win a range fight he wasn't expected to (+180 per our odds) and stay composed after a knockdown. Told Dana White "
                 "his next fight would end in a finish (per LowKick MMA)."},
    ["Finishes in R1-R2 when he wins early: 4 R1 + 4 R2 stoppages, only one decision",
     "Submission-first: six of nine wins by submission, mostly the rear-naked choke and armbar off scrambles",
     "Jab and leg kicks at range to set up grappling",
     "Never stopped since 2021; five straight wins, two over unbeaten opponents (Allakhverdiev, Kunneman)",
     "All three losses were stoppages (2 x KO/TKO, 1 x SUB), two of them in R3"],
    ["UFC debut, at 31, against a UFC-tested opponent",
     "Dropped and bloodied by Kunneman's right hand on the Contender Series (per LowKick MMA)",
     "Has been finished by strikes twice (2019, 2021); limited recent tape at UFC level",
     "Only one 15-minute fight on record"],
    ["Make him strike first and counter the jab with the right hand; he was dropped by a hook in his last fight",
     "Stay out of scrambles: his submissions come off reversals and back takes",
     "Push the pace into round three, where two of his three losses came"],
    [{"date": "2026-08-25", "text": "Booked for his UFC debut against Nick Klein (6-3, 0-2 UFC, out since an August 2025 TKO loss to Andrey Pulyaev) at middleweight on Oct. 31 (Rotowire, citing Heavy; Boxing News, citing Sherdog).",
      "source": S["bn_kropschot"]["url"]},
     {"date": "2026-08-11", "text": "Won a UFC contract with a unanimous decision (30-27, 30-27, 29-28) over Jon Kunneman on the Contender Series season 10 opener.",
      "source": S["cage_dwcs"]["url"]},
     {"date": "2026-02-06", "text": "Became LFA middleweight champion, submitting the unbeaten David Allakhverdiev with a rear-naked choke at 3:24 of R2 (LFA). Cageside Press described it as a 170 lb title; LFA lists it at 185 lb.",
      "source": S["lfa_226"]["url"]}],
    ["lk_kropschot", "cage_dwcs", "lfa_226", "bn_kropschot", "roto_kropschot"],
    "moderate")

# ---------------------------------------------------------------- Talita Alencar
report(
    "Talita Alencar",
    "A 36-year-old Brazilian jiu-jitsu black belt and multiple-time IBJJF world champion (8-1-1, 4-1 UFC; ranked No. 14 at strawweight per Wikipedia) on a three-fight win streak. "
    "She wins by getting on top or to the back and grinding; she has never been finished, and her only loss and her draw both came against Stephanie Luciano, who kept the fight standing.",
    {"Striking": "Functional at best and usually out-landed: 36-57 vs Rayanne dos Santos, 41-72 vs Luciano and 60-78 vs Julia Polastri in our data. "
                 "She throws to close distance and has some pop when she connects: a right hand and knee put Carnelossi on the mat in R2 (per Cageside Press; our data credits no knockdown).",
     "Grappling": "Elite jiu-jitsu (IBJJF world champion 2017; world no-gi champion 2016, 2017, 2021, per Wikipedia). Every submission win is a rear-naked choke (Wikipedia). "
                  "Takedowns are effortful rather than clean: 29% career accuracy; 1-of-9 vs dos Santos, 1-of-10 vs Luciano and 4-of-24 on the Contender Series, "
                  "but 4-of-5 with 12:38 of control against Vanessa Demopoulos and 3-of-5 against Polastri, which won her that decision. Caught a kick to start the "
                  "finishing sequence against Carnelossi.",
     "Defense": "Never stopped in 10 fights. Luciano dropped her with a knee in R3 and stuffed nine of ten takedowns to win 30-27 x3 (Cageside Press). "
                "Takedown defense around 66%; nobody has controlled her for long (Luciano's 3:41 in the DWCS draw is the most).",
     "Pace & cardio": "A slow burner who wins late: of four submission wins, two came in R1 (2021-22 regionals) and two in R3 (Contreras 2022, Carnelossi 2025 at 4:36). "
                      "Six of ten fights have gone the distance, including four of five in the UFC. Cardio is a question: Cageside Press described her slowing in R2 "
                      "and tiring in R3 against Carnelossi, though she still took her down and choked her late. Never stopped, so durability is not the worry; "
                      "losing rounds on the feet is.",
     "Fight IQ": "Patient and position-first; she will keep chaining shots until one lands. Struggles to change plans when an opponent stuffs the takedown and out-strikes her (Luciano twice)."},
    ["Wins by getting on top and grinding: three of four UFC wins went the distance",
     "Rear-naked choke finisher; late finishes (two R3 subs) as well as early regional ones (two R1 subs)",
     "Never finished; her only loss and draw are decisions to Luciano",
     "Usually loses the striking count, even in wins",
     "Has won as an underdog (+197 vs Polastri, +133 vs dos Santos)"],
    ["Age 36",
     "Low takedown accuracy against good defenders",
     "Fades in the second half of fights (per Cageside Press, Carnelossi fight)",
     "Out-landed on the feet in most UFC fights"],
    ["Stuff the first shots and make her strike; Luciano's blueprint",
     "Keep the fight at range and win the volume battle",
     "Avoid scrambles where she can take the back",
     "Push the pace early to tax her cardio"],
    [{"date": "2026-09-24", "text": "Booked against Piera Rodriguez at strawweight for Oct. 31 (Rotowire, citing Nolan King of USA Today); AgentMMA first had the bout as 'targeted' on Sept. 10.",
      "source": S["roto_alencar"]["url"]},
     {"date": "2026-04-25", "text": "Beat Julia Polastri by unanimous decision (29-28 x3) as a +197 underdog; her takedowns (3 of 5) won the rounds despite being out-landed 60-78.",
      "source": S["bjp_vegas116"]["url"]}],
    ["cage_alencar_carnelossi", "cage_luciano", "bjp_vegas116", "roto_alencar", "wiki_alencar", "agent_alencar_rodriguez"],
    "good")

# ---------------------------------------------------------------- Piera Rodriguez
report(
    "Piera Rodriguez",
    "A 34-year-old Venezuelan strawweight (12-2, 5-2 UFC) out of Black House MMA: a pressure fighter with heavy hands, Thai-clinch knees to the body and a "
    "volume of takedowns, on a three-fight win streak. Every one of her UFC wins has been a decision, and neither of her losses came by strikes.",
    {"Striking": "Comes forward with combinations and heavy single shots, then ties up in the Thai clinch for knees to the body (Cageside Press, LowKick MMA on the Souza and Hughes fights). "
                 "Landed a career-best 107 significant strikes against Sam Hughes in March, out-landing her 107-77. About 4.3 significant strikes a minute at 49% in our data. "
                 "Five KO wins, all on the regionals (one of them in R5 in LFA).",
     "Grappling": "Wrestles a lot: 8-of-10 takedowns and 10:24 of control against Josefine Knutsson, seven takedowns against Ketlen Souza. Little submission threat "
                  "(0.1 attempts per 15 minutes). Takedown defense is strong (77%; stuffed all seven of Hughes' shots), but when a real grappler did get on top, "
                  "Gillian Robertson controlled her for over six minutes and armbarred her in R2.",
     "Defense": "Never stopped by strikes. The Robertson submission is disputed: Rodriguez said she never tapped, and Cageside Press thought the replay showed a slight tap "
                "just before the referee stepped in. The Carnelossi loss was a DQ for an intentional headbutt in R2 while she was ahead (she had a knockdown and 3:53 of control in our data).",
     "Pace & cardio": "Decision fighter who gets stronger late: all six of her DWCS/UFC wins went the full 15 minutes; her five stoppage wins (R2 x3, R3 x1, R5 x1) were all on the regionals before 2021. "
                      "Both losses came in R2 (Robertson sub at 4:21, Carnelossi DQ at 3:16). Kept pressing through R3 against Hughes and took Souza down again in the last minute, so no sign of a fade.",
     "Fight IQ": "Usually disciplined and sets the pace, but the Carnelossi DQ shows she can lose her head in a scrappy fight. Adapts the mix: more striking vs Hughes, more wrestling vs Knutsson and Souza."},
    ["Wins on pressure and volume across three rounds: six straight decisions in UFC/DWCS wins",
     "Body knees from the Thai clinch, then takedowns late in rounds",
     "Never stopped by strikes; both losses in R2 (one disputed submission, one DQ)",
     "Has won as an underdog (+219 vs Knutsson)",
     "Close fights can go either way: split decision over Souza"],
    ["Bottom position against a high-level jiu-jitsu player (the Robertson armbar)",
     "Discipline: DQ'd for an intentional headbutt in 2024",
     "No UFC finish; leaves fights to the judges",
     "Age 34"],
    ["Get her to the mat or take her back; she has been submitted from underneath",
     "Make her pay for clinch entries with trips and scrambles",
     "Bank early rounds before her pressure builds"],
    [{"date": "2026-09-24", "text": "Booked against Talita Alencar at strawweight for Oct. 31 (Rotowire, citing Nolan King of USA Today).",
      "source": S["roto_rodriguez"]["url"]},
     {"date": "2026-03-14", "text": "Beat Sam Hughes for the second time, unanimous decision (30-27 x3), with a career-best 107 significant strikes and 7-of-7 takedown defense.",
      "source": S["cage_rodriguez_hughes"]["url"]}],
    ["cage_rodriguez_hughes", "cage_rodriguez_souza", "lk_rodriguez_souza", "cage_rodriguez_knutsson", "bjp_vegas92", "cage_robertson", "roto_rodriguez", "agent_alencar_rodriguez"],
    "good")

# ---------------------------------------------------------------- Lucia Szabova
report(
    "Lucia Szabova",
    "An unbeaten Slovakian (10-0 in our data; other outlets list 11-0 or 12-0) who signs with the UFC as Oktagon's two-division champion, the first woman to hold Oktagon "
    "titles at bantamweight and flyweight at once. Makes her debut at bantamweight; she finishes from mount and from the clinch, and has gone five rounds.",
    {"Striking": "Comes from Muay Thai and kickboxing (Cageside Press). Pressures and does damage in the clinch with knees and elbows: that is how she broke Leidiane Fernandes "
                 "in rounds two and three before the finish (per LowKick MMA). Two first-round TKOs on top of that.",
     "Grappling": "Trips and takedowns into mount, then ground strikes: both title-winning finishes (Bolander 2025, Fernandes 2026) were ground-and-pound from mount "
                  "(Cageside Press). Four submission wins, two in R1, one in R2, one in R3.",
     "Defense": "Never beaten. Took heavy shots in the first round against Fernandes before taking over (per a fan post quoted by LowKick MMA; treat as soft). "
                "We have no strike-by-strike data for her; the numbers in our brief are placeholders, not her stats.",
     "Pace & cardio": "Finishes early or grinds late: of seven stoppages, four came in R1 (Petkeviciute sub, Netza TKO, Faria sub, Bolander TKO), one in R2 and two in R3 "
                      "(Gumienna sub at 4:38, Fernandes TKO at 2:12). Went the full 25 minutes to beat ex-UFC fighter Lucie Pudilova in August. "
                      "Against Fernandes she outlasted an opponent who tired in R2. Never stopped.",
     "Fight IQ": "Composed; has dealt with title fights, a rebooked opponent and a five-rounder. A two-and-a-half-year gap between July 2021 and March 2024 (reason not found)."},
    ["Unbeaten; a -200 favourite or shorter in every fight with a line in our data",
     "Four R1 finishes, but her two most recent title wins came by R3 TKO and a five-round decision",
     "Clinch knees and elbows, then a trip to mount and ground strikes",
     "Has gone five rounds; got stronger as Fernandes tired"],
    ["UFC debut; every pro fight has been in Oktagon",
     "Competition level: our data shows few opponents of UFC calibre (Pudilova is the best)",
     "Was hit hard early by Fernandes (single, soft source)",
     "Record differs between outlets (10-0 here, 11-0 or 12-0 elsewhere)"],
    ["Keep her off the clinch and out of mount",
     "Hit her early, before she settles into pressure",
     "Make her deal with real takedown defense and scrambles"],
    [{"date": "2026-08-22", "text": "Reported signed by the UFC (her Oktagon promoter acknowledged it, per AgentMMA) and booked against Tainara Lisboa at bantamweight for Oct. 31; Ag Fight first reported the bout (MMA Sucka).",
      "source": S["sucka_szabova"]["url"]},
     {"date": "2026-08-01", "text": "Retained the Oktagon bantamweight title with a five-round unanimous decision over Lucie Pudilova in Prague.",
      "source": S["cage_okt92"]["url"]},
     {"date": "2026-04-25", "text": "Won the vacant Oktagon flyweight title, TKO of Leidiane Fernandes from mount at 2:12 of R3, becoming a two-division champion.",
      "source": S["lk_szabova_fernandes"]["url"]}],
    ["sucka_szabova", "agent_szabova", "lk_szabova_fernandes", "cage_szabova_pudilova", "cage_okt92", "sherdog_szabova", "bn_card"],
    "moderate")

# ---------------------------------------------------------------- Tainara Lisboa
report(
    "Tainara Lisboa",
    "A 36-year-old Brazilian bantamweight (7-4, 2-2 UFC) and former Muay Thai world champion in Thailand (per MMA Sucka), on two straight stoppage losses and out "
    "for a year since a R3 TKO by Melissa Croden. Has early power and a sneaky back-take, but has been finished from bottom position and by late pressure.",
    {"Striking": "Muay Thai base; lands knees in the clinch (she won R1 against Croden that way, per Cageside Press). About 2.4 significant strikes a minute and absorbs more (3.4). "
                 "Three KO wins on the regionals (two in R1, one in R3).",
     "Grappling": "Opportunistic scrambler: took Jessica-Rose Clark's back after a scramble and choked her in R3 (Cageside Press). Three submission wins. "
                  "Was still threatening submissions against Croden while hurt (Cageside Press). Wrestling offense is modest (32% takedown accuracy).",
     "Defense": "The worry. Luana Santos took her down twice, held her for nearly eight minutes and finished her with an americana at 4:59 of R2. Croden dropped her late in R2 and "
                "stopped her with punches at 4:32 of R3. Clark held her down for 7:36 in a fight Lisboa still won. Takedown defense around 54%.",
     "Pace & cardio": "Fast starter who fades: of six stoppage wins, four came in R1 and two in R3. All three stoppage losses came after she had been worn on: R1 sub "
                      "in her 2016 debut (Norma Dumont), then R2 (Santos sub) and R3 (Croden TKO) in her last two. Against Croden she won R1 and was overwhelmed from late R2 on. "
                      "Stopped three times in four losses (two submissions, one TKO).",
     "Fight IQ": "Tough and keeps fighting when hurt; finished Clark through a bad cut. But she hasn't found answers once taken down by stronger grapplers."},
    ["Starts well: four R1 finishes, won R1 vs Croden",
     "Back-take rear-naked choke out of scrambles (Clark, R3)",
     "Fades and gets broken late: last two losses at 4:59 of R2 and 4:32 of R3",
     "Stopped in three of four losses (2 SUB, 1 TKO)",
     "Two straight losses after a 2-0 UFC start; Rotowire said she likely needs a win to stay"],
    ["Bottom position against strong grapplers",
     "Late-round durability",
     "Year-long layoff and age 36",
     "Faces an unbeaten debutant who finishes from mount"],
    ["Weather the first round, then pressure",
     "Take her down and hold top position; she was finished from underneath by Santos",
     "Stay heavy in scrambles to avoid giving up the back"],
    [{"date": "2026-08-21", "text": "Booked against unbeaten UFC debutant Lucia Szabova at bantamweight for Oct. 31 (Rotowire, citing Heavy; Rotowire's blurb gives 'Oct. 1', which is a typo for Oct. 31).",
      "source": S["roto_lisboa"]["url"]},
     {"date": "2025-10-18", "text": "Lost to Melissa Croden by TKO (punches) at 4:32 of R3 in Vancouver as a slight favourite, after winning the first round in the clinch.",
      "source": S["cage_croden_lisboa"]["url"]}],
    ["cage_croden_lisboa", "lk_croden_lisboa", "bjp_vegas106", "cage_lisboa_clark", "roto_lisboa", "sucka_szabova", "bn_card"],
    "moderate")

# ---------------------------------------------------------------- Francis Marshall
report(
    "Francis Marshall",
    "A 28-year-old American Top Team grappler (10-3, 4-3 UFC) back at featherweight after two straight wins, a first-round choke of Erik Silva and a short-notice "
    "lightweight decision over Lucas Brennan. His opponent changed three weeks out: Gaston Bolanos withdrew with a cut and Dakota Hope stepped in.",
    {"Striking": "The weak link. Only 34% accurate (15-of-132 against William Gomis); throws power shots off quick movement rather than volume. Has knockdowns (Rojo, Buzukja; Cageside Press also says he "
                 "dropped Mairon Santos with a left hook, which our data doesn't record). Says his stand-up has improved at ATT (UFC.com).",
     "Grappling": "The strength: takedowns (47% accuracy) into long top control (6:36 against Brennan, 5:49 on the Contender Series, 5:26 against Buzukja) and back takes. "
                  "Five submission wins, mostly chokes. Calmly escaped a deep heel hook from Brennan (Cageside Press).",
     "Defense": "Takedown defense about 80%, but when he does get taken down by a strong grappler it can go badly: Isaac Dulgarian took him down inside 30 seconds and finished "
                "him with elbows and punches from mount at 4:48 of R1 (Cageside Press). That is the only time he has been stopped.",
     "Pace & cardio": "Early or late finisher, decision otherwise: of six stoppage wins, three came in R1, one in R2 and two in R3 (both regional subs late in the round). "
                      "Five of his last seven fights went the full 15 minutes; two of those (Gomis, Santos) were split-decision losses. Holds position well into R3 (Brennan). "
                      "One stoppage loss, in R1.",
     "Fight IQ": "Leans on control to win rounds, which has left close fights to the judges (two split-decision losses; he felt he beat Santos, and Cageside Press reported fans and the "
                 "broadcast agreed). Said before Mexico City he wants to finish rather than rely on judges (UFC.com)."},
    ["Takedowns and long top control; back takes into chokes",
     "Finishes when he gets one early: R1 rear-naked choke of Erik Silva in 2:29",
     "Otherwise goes the distance: five of last seven fights went to decision",
     "Only stoppage loss: R1 TKO from mount after being wrestled by Dulgarian",
     "Low-accuracy striking; loses close striking fights on the cards"],
    ["Opponent switch three weeks out; Hope is a power striker per Heavy",
     "Inaccurate striking in a range fight",
     "Split decisions: has lost two of them",
     "Injuries in 2025 (knee, torn rib cartilage) cost him a bout with Austin Bashi (UFC.com)"],
    ["Stop the first takedowns and keep it standing",
     "Out-land him at range; his accuracy is poor",
     "If you wrestle, wrestle hard: Dulgarian finished him from top position"],
    [{"date": "2026-10-08", "text": "Gaston Bolanos withdrew from their Oct. 31 bout with an eyebrow cut from training; Dakota Hope (11-2, 0-1 UFC, 4oz Fight Club) steps in on short notice at featherweight (MMA Mania, Heavy). EssentiallySports noted UFC.com still listed Bolanos on Oct. 9.",
      "source": S["mania_bolanos"]["url"]},
     {"date": "2026-04-25", "text": "Beat Lucas Brennan by unanimous decision (30-27 x3) at lightweight on short notice: 2-of-3 takedowns, 6:36 of control, stuffed all six of Brennan's attempts.",
      "source": S["cage_marshall_brennan"]["url"]},
     {"date": "2026-02-28", "text": "Submitted Erik Silva with a rear-naked choke at 2:29 of R1 in Mexico City; earned a finish bonus.",
      "source": S["bjp_mexico"]["url"]}],
    ["mania_bolanos", "heavy_marshall", "es_vegas123", "ufc_marshall_mexico", "ufc_marshall_313", "cage_marshall_brennan", "cage_marshall_santos", "cage_dulgarian", "bjp_mexico"],
    "good")

out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
