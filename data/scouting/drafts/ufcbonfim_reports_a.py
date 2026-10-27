"""Scouting reports (part A) for UFC Fight Night: Bonfim vs. Brady (UFC Fight Night 293 / UFC Vegas 124, 2026-11-07),
first pass written 2026-10-27.

Fight-week previews aren't out yet: these draw on recent-fight recaps, earlier previews, booking news and our
verified records. Round/method counts are taken from data/verified/fights.csv (Ko appears there as "Seok Hyeon Ko").
Later runs should refresh them with the Sherdog/MMA Mania/UFC.com previews and weigh-in news.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATED = "2026-10-27T18:00:00+00:00"
EVENT = "UFC Fight Night: Bonfim vs. Brady"


def src(outlet, title, url, date, author=""):
    return {"outlet": outlet, "author": author, "title": title, "url": url, "date": date}


SRC = {
    # card / booking
    "wiki_event": src("Wikipedia", "UFC Fight Night: Bonfim vs. Brady",
                      "https://en.wikipedia.org/wiki/UFC_Fight_Night:_Bonfim_vs._Brady", "2026-10-27"),
    "cage_main": src("Cageside Press", "Sean Brady vs. Gabriel Bonfim to Headline Nov. 7 UFC Card",
                     "https://cagesidepress.com/2026/08/15/sean-brady-vs-gabriel-bonfim-headline-nov-7-ufc-card/",
                     "2026-08-15", "Jay Anderson"),
    "cage_330_next": src("Cageside Press", "What's Next: UFC 330 Losers",
                         "https://cagesidepress.com/2026/08/17/whats-next-ufc-330-losers/", "2026-08-17"),
    # Bonfim
    "sherdog_v118_prev": src("Sherdog", "Preview: UFC Vegas 118 'Muhammad vs. Bonfim'",
                             "https://www.sherdog.com/news/articles/1/Preview-UFC-Vegas-118-Muhammad-vs-Bonfim-201430",
                             "2026-06-04", "Ben Duffy"),
    "middleeasy_belal": src("MiddleEasy",
                            "Gabriel Bonfim Picks Apart Belal Muhammad With Jabs And Calf Kicks At UFC Vegas 118",
                            "https://middleeasy.com/mma-news/gabriel-bonfim-belal-muhammad-ufc-vegas-118-decision/",
                            "2026-06-06", "Jake Blend"),
    "unc_belal": src("Yahoo Sports (Uncrowned)",
                     "UFC Vegas 118 results: Gabriel Bonfim gives Belal Muhammad third straight loss; Brendan Allen makes a statement",
                     "https://sports.yahoo.com/mma/article/ufc-vegas-118-results-gabriel-bonfim-gives-belal-muhammad-third-straight-loss-brendan-allen-makes-a-statement-142151891.html",
                     "2026-06-07", "Chuck Mindenhall"),
    "lowkick_v111": src("LowKick MMA", "UFC Vegas 111 Power Rankings: Rating The Main Card Winners In Las Vegas",
                        "https://www.lowkickmma.com/ufc-vegas-111-power-rankings-rating-the-main-card-winners-in-las-vegas/",
                        "2025-11-10"),
    "cage_v111_next": src("Cageside Press", "What's Next: UFC Vegas 111 Winners",
                          "https://cagesidepress.com/2025/11/10/whats-next-ufc-vegas-111-winners/", "2025-11-10"),
    "cage_dalby": src("Cageside Press", "UFC Sao Paulo: Nicolas Dalby Stops Gabriel Bonfim, Silences Brazilian Crowd",
                      "https://cagesidepress.com/2023/11/04/ufc-sao-paulo-nicolas-dalby-stops-gabriel-bonfim-silences-brazilian-crowd/",
                      "2023-11-04", "Jay Anderson"),
    "cage_wonderboy": src("Cageside Press", "Gabriel Bonfim Battles With Thompson, Grinds Out Split Win",
                          "https://cagesidepress.com/2025/07/12/gabriel-bonfim-battles-with-thompson-grinds-out-split-win/",
                          "2025-07-12", "Eddie Law"),
    "sherdog_ismael": src("Sherdog", "Ismael Bonfim removed from UFC roster after gigantic weight miss",
                          "https://www.sherdog.com/news/news/Ismael-Bonfim-removed-from-UFC-roster-after-gigantic-weight-miss-203180",
                          "2026-10-13", "Sayan Nag"),
    # Brady
    "sherdog_328_prev": src("Sherdog", "Preview: UFC 328 'Chimaev vs. Strickland' - Brady vs. Buckley",
                            "https://www.sherdog.com/news/articles/4/Preview-UFC-328-Chimaev-vs-Strickland-201092",
                            "2026-05-07", "Tom Feely"),
    "cage_buckley": src("Cageside Press", "UFC 328: Sean Brady Cruises in Dominant Showing Against Joaquin Buckley",
                        "https://cagesidepress.com/2026/05/09/ufc-328-sean-brady-cruises-in-dominant-showing-against-joaquin-buckley/",
                        "2026-05-09", "Jay Anderson"),
    "cage_morales": src("Cageside Press", "UFC 322: Michael Morales Stays Perfect, Stops Sean Brady",
                        "https://cagesidepress.com/2025/11/15/ufc-322-michael-morales-stays-perfect-stops-sean-brady/",
                        "2025-11-15", "Brett Cagle"),
    "score_edwards": src("theScore", "Brady submits Edwards in 1-sided UFC London main event",
                         "https://www.thescore.com/mma/news/3248381/brady-submits-edwards-in-1-sided-ufc-london-main-event",
                         "2025-03-22", "Nick Baldwin"),
    "mmaj_brady_bonfim": src("Yahoo Sports (MMA Junkie)", "Sean Brady gladly will take Gabriel Bonfim in lieu of Muhammad rematch",
                             "https://sports.yahoo.com/articles/sean-brady-gladly-gabriel-bonfim-220033618.html",
                             "2026-06-07", "Matt Erickson"),
    "mmaj_brady_buckley": src("Yahoo Sports (MMA Junkie)", "Sean Brady: Joaquin Buckley 'always carries his power,' beats Mike Malott",
                              "https://sports.yahoo.com/articles/sean-brady-joaquin-buckley-always-003024297.html",
                              "2026-10-16", "Farah Hannoun"),
    # Suarez
    "wiki_suarez": src("Wikipedia", "Tatiana Suarez", "https://en.wikipedia.org/wiki/Tatiana_Suarez", "2026-10-27"),
    "cage_godinez": src("Cageside Press", "UFC 327: Tatiana Suarez First to Submit, Stop Loopy Godinez",
                        "https://cagesidepress.com/2026/04/11/ufc-327-tatiana-suarez-first-to-submit-stop-loopy-godinez/",
                        "2026-04-11", "Jay Anderson"),
    "cage_lemos_ts": src("Cageside Press", "Tatiana Suarez Shuts Down Lemos' Attacks, Earns Decision Win",
                         "https://cagesidepress.com/2025/09/13/tatiana-suarez-shuts-down-lemos-attacks-earns-decision-win/",
                         "2025-09-13", "Mathis Desjardins"),
    "cage_zhang": src("Cageside Press", "UFC 312: Weili Zhang Retains, Dominates Tatiana Suarez",
                      "https://cagesidepress.com/2025/02/09/ufc-312-weili-zhang-retains-dominates-tatiana-suarez/",
                      "2025-02-09", "Jay Anderson"),
    # Jandiroba
    "sherdog_virna": src("Sherdog", "Virna Jandiroba eyes third Mackenzie Dern fight after Tatiana Suarez",
                         "https://www.sherdog.com/news/news/Virna-Jandiroba-eyes-third-Mackenzie-Dern-fight-after-Tatiana-Suarez-203302",
                         "2026-10-22", "Marcelo Alonso, Sourav Chakraborty"),
    "cage_ricci": src("Cageside Press", "UFC Vegas 115: Virna Jandiroba Cruises to Victory Over Tabatha Ricci",
                      "https://cagesidepress.com/2026/04/04/ufc-vegas-115-virna-jandiroba-cruises-to-victory-over-tabatha-ricci/",
                      "2026-04-04", "Jay Anderson"),
    "unc_dern": src("Yahoo Sports (Uncrowned)", "UFC 321 results: Mackenzie Dern pummels Virna Jandiroba to win vacant UFC strawweight title",
                    "https://sports.yahoo.com/mma/breaking-news/article/ufc-321-results-mackenzie-dern-pummels-virna-jandiroba-to-win-vacant-ufc-strawweight-title-202955991.html",
                    "2025-10-25", "Alan Dawson"),
    # Grant
    "sherdog_v116_prev": src("Sherdog", "Preview: UFC Vegas 116 'Sterling vs. Zalal' - Luna Martinetti vs. Grant",
                             "https://www.sherdog.com/news/articles/4/Preview-UFC-Vegas-116-Sterling-vs-Zalal-200934",
                             "2026-04-23", "Ben Duffy"),
    "cage_luna": src("Cageside Press", "UFC Vegas 116: Davey Grant Fends Off Newcomer Adrian Luna Martinetti",
                     "https://cagesidepress.com/2026/04/25/ufc-vegas-116-davey-grant-fends-off-newcomer-adrian-luna-martinetti/",
                     "2026-04-25", "Shawn Bitter"),
    "cage_blackshear": src("Cageside Press", "UFC Abu Dhabi: Davey Grant Overcomes Slow Start, Beats Da'Mon Blackshear",
                           "https://cagesidepress.com/2025/07/26/ufc-abu-dhabi-davey-grant-overcomes-slow-start-beats-damon-blackshear/",
                           "2025-07-26"),
    "cage_vancouver_next": src("Cageside Press", "What's Next: UFC Vancouver Winners",
                               "https://cagesidepress.com/2025/10/20/whats-next-ufc-vancouver-winners/", "2025-10-20"),
    "britbrief_grant": src("Brit Brief", "Davey Grant: UFC star's Vegas move pays off for family",
                           "https://britbrief.co.uk/sports/boxing/davey-grant-ufc-stars-vegas-move-pays-off-for-family.html",
                           "2026-10-21"),
    # Elijah Smith
    "cage_you": src("Cageside Press", "UFC Vegas 114: Elijah Smith Claims Another Finish, Subs Su Young You",
                    "https://cagesidepress.com/2026/03/14/ufc-vegas-114-elijah-smith-claims-another-finish-subs-su-young-you/",
                    "2026-03-14", "Nick Holt"),
    "cage_kazama": src("Cageside Press", "UFC Vegas 109 Results: Elijah Smith Lands Rampage-Style Slam on Toshiomi Kazama",
                       "https://cagesidepress.com/2025/08/09/ufc-vegas-109-results-elijah-smith-lands-rampage-style-slam-on-toshiomi-kazama/",
                       "2025-08-09", "Jay Anderson"),
    "cage_vmorales": src("Cageside Press", "UFC Vegas 102: Second-Gen Star Elijah Smith Busts Open Vince Morales in Debut",
                         "https://cagesidepress.com/2025/02/15/ufc-vegas-102-second-gen-star-elijah-smith-busts-open-vince-morales-in-debut/",
                         "2025-02-15", "Jay Anderson"),
    "mmaj_smith": src("Yahoo Sports (MMA Junkie)", "Elijah Smith wants UFC 328 slot after rally from 'garbage' first round",
                      "https://sports.yahoo.com/articles/elijah-smith-wants-ufc-328-193018763.html", "2026-03-17",
                      "Matt Erickson, Ken Hathaway"),
    # Ko
    "ufc_ko": src("UFC.com", "Seokhyeon Ko (athlete profile)", "https://www.ufc.com/athlete/seokhyeon-ko", "2026-10-27"),
    "cage_jp": src("Cageside Press", "UFC Oklahoma City: Jean-Paul Lebosnoyani Claims Decision Over Seok Hyeon Ko",
                   "https://cagesidepress.com/2026/07/18/ufc-oklahoma-city-jean-paul-lebosnoyani-claims-decision-over-seok-hyeon-ko/",
                   "2026-07-18", "Nick Holt"),
    "kherald_ko": src("The Korea Herald", "Ko Seok-hyun suffers first UFC loss", "https://www.koreaherald.com/article/10812773",
                      "2026-07-19"),
    "sherdog_elliott": src("Sherdog", "UFC Baku Prelims: Seok Hyeon Ko Outshines Oban Elliott in Azerbaijan",
                           "https://www.sherdog.com/news/news/UFC-Baku-Prelims-Seok-Hyeon-Ko-Outshines-Oban-Elliott-in-Azerbaijan-197404",
                           "2025-06-21", "Brian Knapp"),
    "starnews_ko": src("StarNews Korea", "'Korean Fighters Duo' Set to Restore UFC Honor... Ko Suk-hyun and Lee Jung-young Step Into the Octagon",
                       "https://www.starnewskorea.com/en/sports/2026/10/08/2026100809530534759", "2026-10-08", "Park Geon-do"),
    # Turman
    "wiki_turman": src("Wikipedia", "Wellington Turman", "https://en.wikipedia.org/wiki/Wellington_Turman", "2026-10-27"),
    "lowkick_dulatov": src("LowKick MMA", "UFC Abu Dhabi Suffers Last-Minute Blow After Fighter Is Rushed To Hospital Due To Illness",
                           "https://www.lowkickmma.com/ufc-abu-dhabi-islam-dulatov-hospitalized/", "2026-07-25", "Pranav Pandey"),
    "rotowire_turman": src("Rotowire", "Wellington Turman MMA Stats & News",
                           "https://www.rotowire.com/mma/player/wellington-turman-1918", "2026-09-09"),
    "cage_rbrown": src("Cageside Press", "UFC Jacksonville: Randy Brown Takes Decision in Close Fight with Wellington Turman",
                       "https://cagesidepress.com/2023/06/24/ufc-jacksonville-randy-brown-defeats-wellington-turman/",
                       "2023-06-24", "Val Dewar"),
    "mmaj_gooden": src("Yahoo Sports (MMA Junkie)",
                       "UFC on ESPN 52 video: Jared Gooden batters Wellington Turman, tops off wild comeback with choke",
                       "https://sports.yahoo.com/ufc-espn-52-video-jared-210013257.html", "2023-12-02", "Nolan King"),
    "cage_igor": src("Cageside Press", "Redemption: Second Chances on Dana White's Contender Series - Igor Cavalcanti",
                     "https://cagesidepress.com/2026/09/15/redemption-second-chances-dana-whites-contender-series-igor-cavalcanti/",
                     "2026-09-15"),
    # Kondratavicius
    "cage_trocoli": src("Cageside Press", "UFC London: Mantas Kondratavičius Out-Points Antonio Trócoli",
                        "https://cagesidepress.com/2026/03/21/ufc-london-mantas-kondratavicius-out-points-antonio-trocoli/",
                        "2026-03-21", "Nick Holt"),
    "lowkick_trocoli": src("LowKick MMA", "Mantas Kondratavičius Drops Antonio Trócoli With Brutal Elbow, Secures Victory",
                           "https://www.lowkickmma.com/trocoli-vs-mantas-kondratavicius-ufc-london/", "2026-03-21",
                           "Craig Pekios"),
    "ufc_mantas": src("UFC.com", "Mantas Kondratavicius Out To Prove He Belongs",
                      "https://www.ufc.com/news/mantas-kondratavicius-out-to-prove-he-belongs-ufc-london", "2026-03-18",
                      "E. Spencer Kyte"),
    "es_bekoev": src("EssentiallySports", "Medical Emergency Forces UFC Vegas 123 Fighter to Withdraw as Dana White Faces Setback",
                     "https://www.essentiallysports.com/ufc-mma-news-medical-emergency-forces-ufc-vegas-123-fighter-to-withdraw-as-dana-white-faces-setback/",
                     "2026-10-26", "Biplob Chakraborty"),
    "middleeasy_bekoev": src("MiddleEasy", "Azamat Bekoev Withdraws From Andre Petroski Fight After Health Scare",
                             "https://middleeasy.com/mma-news/azamat-bekoev-petroski-withdrawal-health/", "2026-10-25",
                             "Jake Blend"),
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
report("Gabriel Bonfim",
       "A big, athletic Brazilian welterweight (20-1, age 29) and former LFA champion, on a five-fight win streak capped by a "
       "50-45 x3 shutout of former champion Belal Muhammad in June, his first 25-minute fight. He came up as a finishing "
       "grappler (13 submissions, most of them chokes) but beat Muhammad entirely on the feet with a jab and calf kicks. His "
       "only loss is a R2 TKO to Nicolas Dalby in 2023, after he had won R1.",
       {"Striking": "Straight, fast, heavy shots and kicks to the legs (Sherdog's Ben Duffy), though Duffy notes he doesn't always "
                    "put his hands together in combination. Against Muhammad he ran the fight behind the jab and calf kicks, made "
                    "Muhammad switch stances, countered him cleanly and knocked his mouthpiece out with a jab-right in R3 "
                    "(MiddleEasy; Uncrowned). Out-landed him 128-86 in our data. Knocked out Randy Brown with a knee in R2 after a "
                    "patient, range-finding first round (LowKick MMA).",
        "Grappling": "Duffy rates his ground game elite: good shots from range, trips and throws from the clinch, a heavy and tiring "
                     "top game that hunts the back. Duffy says guillotines and D'Arces account for most of his UFC finishes; his "
                     "first two UFC wins were R1 submissions at 0:49 and 1:13; he also submitted Kalinn Williams at 4:58 of R2. Against Stephen Thompson he scored "
                     "takedowns in every round, briefly took the back and attacked a neck crank (Cageside). Our data: 2.3 takedowns "
                     "per 15 at 51%.",
        "Defense": "Hard to take down (78% takedown defense; Muhammad got nothing, 0-for-2 in our data). Hittable at times: "
                   "Thompson rocked him with a head kick in R2 (Cageside), and Dalby broke him down along the fence in R2, where "
                   "Bonfim covered up and threw blind uppercuts before a knee dropped him (Cageside). That is his only stoppage "
                   "loss.",
        "Pace & cardio": "Used to be a front-loaded finisher; that has changed. Of his 17 finishes, 8 came in R1, 7 in R2 and 2 in R3. "
                         "His only loss came after he won R1 against Dalby and then faded and was overwhelmed in R2 (Duffy). Duffy "
                         "says the pace problems look solved: he was the stronger man late in each of his last four wins before "
                         "Muhammad, and he then won all five rounds against Muhammad with his clearest work in R3 (MiddleEasy). Wins "
                         "since the loss: decision, R2 sub, split decision, R2 KO, five-round decision.",
        "Fight IQ": "Shows tactical flexibility: a grappler who chose not to wrestle Muhammad and instead neutralised him at range, "
                    "which he said was the plan (Uncrowned). Cageside thought he looked shaky in wins over Ange Loosa and Thompson "
                    "after the Dalby loss, with confidence restored by the Brown knockout."},
       ["Jab and calf kicks at range; counters off opponents' entries",
        "Chokes (guillotine, D'Arce, RNC) whenever an opponent shoots or gives the back",
        "Finishes now come in R2 more than R1; recent wins are decisions or R2 stoppages",
        "Has gone 25 minutes once and won every round",
        "Only loss: won R1, wilted under clinch pressure on the fence in R2"],
       ["How he handles a heavy wrestler who stays on him: Muhammad barely got hold of him, so the takedown defense hasn't "
        "been tested by a top-five grappler",
        "Pressure along the fence (the Dalby pattern)",
        "Head kicks and clean shots: Thompson rocked him in R2"],
       ["Close distance, pin him on the fence and make him carry weight in the clinch",
        "Win R1 with grappling exchanges and test his gas from R2 on",
        "Don't shoot carelessly from the outside: he punishes level changes with knees and front-headlock chokes"],
       [n("2026-08-15", "Booked to headline against Sean Brady on Nov. 7; announced during the UFC 330 broadcast. Ranked No. 5 and "
                        "No. 6 depending on the ranking used.", "cage_main"),
        n("2026-10-13", "His brother Ismael Bonfim was cut by the UFC after a 7.5-lb weight miss and a R1 TKO loss to Francisco "
                        "Prado. Off-cage family news; nothing reported about Gabriel's own camp.", "sherdog_ismael"),
        n("2026-06-06", "Beat Belal Muhammad 50-45 x3, his first five-round fight and his biggest win.", "middleeasy_belal")],
       ["sherdog_v118_prev", "middleeasy_belal", "unc_belal", "lowkick_v111", "cage_v111_next", "cage_dalby", "cage_wonderboy",
        "cage_main", "sherdog_ismael", "wiki_event"],
       "good")

# ---------------------------------------------------------------------------------------------------------------
report("Sean Brady",
       "A Philadelphia welterweight (19-2, age 34; Renzo Gracie Philly) and one of the division's best top-position grapplers. "
       "He builds fights over time: took Gilbert Burns the distance in five rounds, submitted Leon Edwards in R4 and held "
       "Joaquin Buckley down for about 12 of 15 minutes in May. Both losses were stoppages by strikers who kept the fight "
       "standing: Belal Muhammad (R2 TKO, 2022) and Michael Morales (R1 TKO, Nov. 2025).",
       {"Striking": "Better than it was, but mostly a means to an end (Sherdog). He lands 53% of significant strikes but rarely "
                    "knocks anyone down (0.08 knockdowns per 15 minutes in our data). Against Morales he backed away, "
                    "then lunged in with a double jab and was countered by a right over the top and an uppercut (Cageside). Showed "
                    "a high kick and spinning back fist against Buckley without landing them cleanly.",
        "Grappling": "Elite chain wrestling into mount and back control, with heavy ground-and-pound. Against Buckley: takedown off a "
                     "kick, mount, kimura attempt in R1; re-takedowns and mount with hammerfists and elbows in R2; double-leg and "
                     "mount again in R3 (Cageside). Against Edwards: back and body lock in R2, mount in R3, mounted one-arm "
                     "guillotine at 1:39 of R4 (theScore). Control time in our data: 10:34 vs Burns, 11:10 vs Edwards, 12:09 vs "
                     "Buckley. Takedowns land at 46%, about 3.3 per 15 minutes.",
        "Defense": "Never submitted. On the feet he can be frozen out by a longer, faster striker: Morales hurt him early and stopped "
                   "him at 3:27 of R1, and Brady landed 8 significant strikes and attempted one takedown. Muhammad stuffed all five "
                   "of his takedowns (our data) and stopped him late in R2 (4:47).",
        "Pace & cardio": "A slow burner and late finisher. His UFC finishes came in R2 (Aguilera), R3 (Matthews, Gastelum) and R4 "
                         "(Edwards); his last R1 finish was in 2017. Ten of his 19 wins are decisions, including a 25-minute win "
                         "over Burns. Sherdog says he gets stronger as fights go on and suits five rounds more than three. The risk "
                         "is early: both losses came before the end of R2, and Sherdog says he needs early success in the feel-out "
                         "to get going.",
        "Fight IQ": "Patient and methodical; picks his entries off the opponent's kicks. Said in June that Bonfim is 'a tough "
                    "matchup' because of his size, submissions and striking, and that he wants top-five opponents (MMA Junkie)."},
       ["Takedown, mount, back, repeat; dominant control time",
        "Gets better as the fight goes on; finishes in R2-R4",
        "Has never been submitted",
        "Both losses: stopped on the feet in R1-R2 by strikers who kept it standing"],
       ["Rough early stretches on the feet against long, powerful strikers (Morales)",
        "Taking down a bigger welterweight with 78% takedown defense and dangerous front-headlock chokes",
        "Low knockdown power if the fight stays standing"],
       ["Keep it standing in R1-R2 with the jab and counters as he enters",
        "Stuff the first shots and make him strike: his confidence drops when the wrestling doesn't land (Sherdog)",
        "Threaten chokes when he changes levels"],
       [n("2026-08-15", "Booked to headline against Gabriel Bonfim on Nov. 7. Cageside noted his absence from the hometown UFC 330 "
                        "card raised eyebrows; no reason was given.", "cage_main"),
        n("2026-10-16", "Picked Joaquin Buckley over Mike Malott and praised Buckley's late power, a sign he is following the "
                        "division; no camp or injury news in the piece.", "mmaj_brady_buckley"),
        n("2026-05-09", "Beat Buckley by decision (30-25, 30-25, 30-27) after the Morales loss.", "cage_buckley")],
       ["sherdog_328_prev", "cage_buckley", "cage_morales", "score_edwards", "mmaj_brady_bonfim", "mmaj_brady_buckley",
        "cage_main", "cage_330_next", "wiki_event"],
       "good")

# ---------------------------------------------------------------------------------------------------------------
report("Tatiana Suarez",
       "An elite American wrestler (12-1, age 36) and one of the best takedown artists in women's MMA. Her only loss is the "
       "five-round title fight with Weili Zhang in February 2025, where Zhang stopped 14 of her 15 takedowns. She's 2-0 since, "
       "most recently becoming the first fighter to stop Loopy Godinez (RNC, R2) in April. A long history of injuries has kept "
       "her out for years at a time.",
       {"Striking": "Functional, used to get into range: kicks and pressure to push opponents to the fence (Cageside on Lemos). Low "
                    "output (about 2.1 significant strikes a minute) and not much power (one knockdown in her UFC run). Opponents "
                    "have hurt her on the feet: Godinez landed a hard right in R1, and Lemos wobbled her with elbows and rights in R3 "
                    "(Cageside).",
        "Grappling": "Her entire game. A junior and senior world bronze medallist in freestyle wrestling (Wikipedia). Chains attempts "
                     "until one lands, then takes the back or sets up chokes: RNC on Godinez after a quick R2 takedown, and "
                     "guillotines on Jessica Andrade and Montana De La Rosa, all in R2. Control time in our data: 9:34 of 15 minutes "
                     "against Lemos, 5:12 against Godinez.",
        "Defense": "Never stopped. But Godinez took her down twice in R1 (thrown and slammed, per Cageside), and Zhang reversed her "
                   "to top in R2 and tripped her in R4, then nearly finished an arm-triangle (Cageside). On her back she has been the less comfortable "
                   "fighter.",
        "Pace & cardio": "Starts hard and can fade. Finishes: 3 subs in R1 and 3 in R2, 2 TKOs (R2 and R3); her last three "
                         "submissions all came in R2. Against Zhang she won R1, then her shots got weaker from range and she lost "
                         "R2-R5, and Cageside tied that to her early energy output. Lemos rallied in R3 and wobbled her "
                         "(Cageside). She is most dangerous in R1-R2, less effective late.",
        "Fight IQ": "Disciplined about her game and keeps shooting even after stuffed attempts; that persistence wins rounds but "
                    "costs energy when the shots aren't landing (Zhang)."},
       ["Chain-wrestling pressure from the first exchange",
        "Back-takes and chokes; recent finishes all in R2",
        "Heavy top control in decisions",
        "Fades when her takedowns are stopped repeatedly"],
       ["Injury history: neck injury in 2012, a 3.5-year layoff from 2019 to 2023, and withdrawals in 2016, 2021, 2024 "
        "and from UFC 310 against this same opponent (Wikipedia)",
        "Gets hit when she's on her way in; Lemos and Godinez both hurt her",
        "Late-round fade when the takedowns stop landing (Zhang)"],
       ["Stop the first wave of takedowns and make her work in R1-R2",
        "Counter-strike on her entries",
        "Threaten from bottom or reverse when she does get you down"],
       [n("2026-09-11", "Booked against Virna Jandiroba for the third time, after the 2023 (Jandiroba knee injury) and Dec. 2024 "
                        "(Suarez health issue) bookings fell through.", "wiki_event"),
        n("2026-04-11", "Submitted Loopy Godinez with a rear-naked choke at 2:29 of R2 after a rough first round.", "cage_godinez")],
       ["wiki_suarez", "cage_godinez", "cage_lemos_ts", "cage_zhang", "sherdog_virna", "wiki_event"],
       "good")

# ---------------------------------------------------------------------------------------------------------------
report("Virna Jandiroba",
       "A Brazilian jiu-jitsu specialist (23-4, age 38) and the most dangerous submission grappler at strawweight: 14 of her 23 "
       "wins are submissions. She lost a five-round decision to Mackenzie Dern for the vacant title in October 2025, then "
       "out-grappled Tabatha Ricci in April. She has never been stopped; all four losses were decisions.",
       {"Striking": "Serviceable, not a weapon: about 2.3 significant strikes landed a minute and absorbs more than she lands. "
                    "Held her own on the feet with Ricci and kept landing in R2 (Cageside). Dern out-landed her 118-106 over five "
                    "rounds and cut her with the jab in R2 (Uncrowned).",
        "Grappling": "Cuts off the cage, closes, and takes the back or drags opponents down along the fence (Cageside on Ricci). Top "
                     "game is heavy: half guard and arm-triangle attempts against Ricci, and an armbar off a back take against Amanda "
                     "Lemos (R2, 4:48, 2024). She took Dern down nine times in 17 attempts, more than any of Dern's previous "
                     "opponents (Uncrowned). Control: 8:00 against Ricci and about 10 minutes against Yan Xiaonan in our data.",
        "Defense": "Never finished. Takedown defense of 62% in our data; Suarez is a different class of wrestler than anyone she "
                   "has faced. Comfortable off her back, but she has spent little time there in recent fights.",
        "Pace & cardio": "Steady, good cardio; has gone 25 minutes twice (a 2018 split-decision win over Mizuki "
                         "Inoue in Invicta, and the Dern loss), and submitted Lemos late in R2 of a scheduled five-rounder. Her finishes came early in her career (8 subs in R1, 5 in R2, 1 in R3; one R2 "
                         "TKO), but in the UFC she has gone to decision in five of her last six. Stayed aggressive through R5 against "
                         "Dern (Uncrowned). Not a late fader.",
        "Fight IQ": "Experienced and patient; she trained with Demian Maia in a previous camp for insight on facing strong wrestlers "
                    "and has done two camps for this fight (Sherdog)."},
       ["Cut off the cage, clinch, take the back",
        "Heavy top control and arm attacks (arm-triangle, armbar)",
        "Recent fights go to decision; never stopped",
        "Consistent pace across three or five rounds"],
       ["Age 38",
        "Wrestling defense against an elite wrestler; she has mostly been the one shooting",
        "Gets out-struck at range by better strikers (Dern)"],
       ["Out-wrestle her or keep it standing and win the striking exchanges",
        "Don't give up the back in scrambles",
        "Keep top position tight: she threatens from guard"],
       [n("2026-10-22", "Said she has done two training camps for Suarez, and called the matchup a 'clash of titans'. She wants a "
                        "third fight with champion Mackenzie Dern in early 2027.", "sherdog_virna"),
        n("2026-04-04", "Beat Tabatha Ricci by decision (30-27, 29-28, 29-28), with takedowns in every round.", "cage_ricci")],
       ["sherdog_virna", "cage_ricci", "unc_dern", "wiki_suarez", "wiki_event"],
       "good")

# ---------------------------------------------------------------------------------------------------------------
report("Davey Grant",
       "An English bantamweight veteran (18-8, age 40, turns 41 in December; Syndicate MMA, where he is now head striking "
       "coach). A volume boxer with sneaky power and underrated clinch wrestling, he won three of his last four, the latest a "
       "Fight of the Night decision over Adrian Luna Martinetti in April. He has never been knocked out, but five of his eight "
       "losses are submissions, the latest a flying-knee-then-guillotine finish by Charles Jourdain in R1.",
       {"Striking": "Clean boxing combinations, steady volume and sneaky power (Sherdog). Very high output: about 5.9 significant "
                    "strikes a minute; he out-landed Luna Martinetti 162-99 and Ramon Taveras 147-69. Against Luna Martinetti he "
                    "chopped the lead calf until his opponent had to keep switching stance, then added looping rights, knees and "
                    "body shots (Cageside). Walks opponents down and goes to the body (Blackshear).",
        "Grappling": "Underrated, per Sherdog: trips and throws from the clinch and quick level changes. Submitted Raphael "
                     "Assuncao late in R3. Rarely wrestles now (about 0.5 takedowns per 15). Gets taken down but gets up fast: "
                     "Blackshear took him down twice and took his back in R1, and Luna Martinetti's late takedown didn't keep him "
                     "down (Cageside).",
        "Defense": "Never stopped by strikes in 26 fights in our data. Hittable (absorbs about 3.6 a minute). The weakness is the "
                   "neck and limbs: submission losses in R1 (three), R2 and R3. Jourdain floored him with a flying knee and "
                   "finished him with a guillotine while he was stunned (Cageside).",
        "Pace & cardio": "Slow starter, strong finisher. Lost R1 to Blackshear on the mat, then won R2 and R3 (Cageside). His UFC "
                         "stoppages came late: TKOs in R3 (Martin Day, Louis Smolka) and R2 (Jonathan Martinez), and a sub in R3 "
                         "(Assuncao). Most UFC wins are decisions. His recent losses came early (Jourdain R1) or on close cards "
                         "(Marcos split).",
        "Fight IQ": "Veteran who adjusts after a bad first round. Sherdog says the only way these fights look close is if he starts "
                    "to show his age."},
       ["High-volume boxing and calf kicks; pulls ahead in R2-R3",
        "Late finisher: three of his four UFC stoppages came in R3",
        "Very durable to strikes",
        "Submission losses, including early ones"],
       ["Age 40, against a 23-24-year-old",
        "Slow starts; can drop R1 to a wrestler",
        "Chokes in scrambles (five career submission losses)"],
       ["Win R1 with takedowns and back control",
        "Front headlock and guillotine threats when he ducks in or shoots",
        "Avoid a volume brawl over 15 minutes"],
       [n("2026-10-21", "Has moved his family from Bishop Auckland to Las Vegas and is head striking coach at Syndicate MMA; this "
                        "is his 17th UFC fight.", "britbrief_grant"),
        n("2026-04-25", "Beat Adrian Luna Martinetti by decision (29-28 x3) in a Fight of the Night bout.", "cage_luna")],
       ["sherdog_v116_prev", "cage_luna", "cage_blackshear", "cage_vancouver_next", "britbrief_grant", "wiki_event"],
       "good")

# ---------------------------------------------------------------------------------------------------------------
report("Elijah Smith",
       "An American bantamweight prospect (10-1, age 23-24; 3-0 UFC), son of former UFC fighter Gilbert Smith, from the 2024 "
       "Contender Series. Quick hands, kicks and wrestling, with real finishing instincts: a slam knockout of Toshiomi Kazama (R1) "
       "and a knockdown into a rear-naked choke against SuYoung You (R2). He tends to lose the first round to grapplers and "
       "then turn the fight.",
       {"Striking": "Fast hands, kicks and an uppercut he uses against level changes: he stopped You's takedown with an uppercut "
                    "and hook, then dropped him (Cageside). Bloodied Vince Morales with an uppercut in R3 of his debut. About 0.4 "
                    "knockdowns per 15 minutes.",
        "Grappling": "Strong in the scramble and on top: punched Kazama from top while defending a toe hold, then lifted him out of a "
                     "triangle attempt and slammed him for a KO at 4:10 of R1 (Cageside). Chose the choke over ground strikes to "
                     "finish You (MMA Junkie). Gets taken down by chain wrestlers: You controlled most of R1 with chain takedowns, "
                     "and Morales took him down in R2.",
        "Defense": "Composed under trouble: survived a deep D'Arce from Morales in R2 and a low blow in R1, and still won the "
                   "decision (Cageside). Only loss was a R3 TKO to Reyes Cortez Jr. on the regional scene in 2023. Absorbs about "
                   "3.3 strikes a minute.",
        "Pace & cardio": "Has finished in R1 (four, including the Kazama slam), R2 (two) and R3 (one sub). Three decisions (Aaron "
                         "Tau on the Contender Series, Morales, Robert Trujillo). In both of his last two hard fights he lost R1 "
                         "and came back: Morales (won R3 decisively) and You (called his own R1 'garbage', then finished in R2). "
                         "His single loss was a late stoppage.",
        "Fight IQ": "Adjusts mid-fight and credits his corner for the changes (MMA Junkie). Young and still improving."},
       ["Fast hands, uppercuts against level changes",
        "Big-moment finishes: slam KO, knockdown-to-choke",
        "Often down after R1, strong R2-R3",
        "Chokes over ground-and-pound when the back is there"],
       ["Gives up R1 to chain wrestlers",
        "Hittable at 23-24, with one regional R3 TKO loss",
        "First fight against a high-volume veteran striker"],
       ["Chain takedowns early to win R1",
        "Out-volume him on the feet over 15 minutes",
        "Don't dip into his uppercut"],
       [n("2026-03-17", "After submitting You, he asked for a quick turnaround at UFC 328 in Newark; it didn't happen, and he next "
                        "fights Grant on Nov. 7.", "mmaj_smith"),
        n("2026-03-14", "Submitted SuYoung You (RNC, 1:04 of R2) after a knockdown; first submission loss of You's career.",
          "cage_you")],
       ["cage_you", "cage_kazama", "cage_vmorales", "mmaj_smith", "wiki_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Ko Seok-hyeon",
       "A South Korean welterweight from Busan (13-3, age 32; HAVAS MMA), nicknamed 'The Korean Tyson', a judo black belt and "
       "former amateur sambo world champion (UFC.com). Won his first two UFC fights by decision on takedowns and top control, "
       "then lost a close decision to Jean-Paul Lebosnoyani in July. Regional KO power (six KOs, four in R1) but no UFC finish "
       "yet. Listed in our data as Seok Hyeon Ko.",
       {"Striking": "Jab, leg kicks, right hand and uppercut at range; won R1 against Lebosnoyani on kicks and the jab and landed "
                    "a sharp elbow in R3 (Cageside; Korea Herald). Slashing elbows cut Oban Elliott (Sherdog). UFC.com: 3.15 "
                    "significant strikes landed and 1.93 absorbed a minute; no UFC knockdowns.",
        "Grappling": "Judo and sambo base. Took Elliott down in all three rounds and ended in full mount (Sherdog: 30-27 x3). His "
                     "win over Phil Rowe was also a clear decision; we haven't read a recap of it, so its details aren't covered here. Takedown accuracy on UFC.com is only 26% (6 of 23); Lebosnoyani defended a judo throw.",
        "Defense": "Lebosnoyani took him down in every round and threatened two tight guillotines, which Ko escaped (Cageside). "
                   "Takedown defense 50% (UFC.com). Was stopped twice on the regional scene, R2 in 2018 and R1 in 2021.",
        "Pace & cardio": "Decision fighter in the UFC (three of three). Regional finishes were all KOs in R1 (four) or R2 (two). The "
                         "Korea Herald says he slowed in the middle of R2 against Lebosnoyani, who took over with combinations, knees "
                         "and a takedown to mount. He came back in R3. Both stoppage losses came in R1-R2.",
        "Fight IQ": "Has rebranded as 'Technical' Ko, aiming for his first UFC finish (StarNews)."},
       ["Judo/sambo takedowns and top control in the UFC",
        "Jab and leg kicks at range",
        "All three UFC fights went to decision",
        "Slowed in R2 of his loss"],
       ["Gets taken down by a committed wrestler and has been caught in guillotines",
        "Low takedown accuracy against good defense",
        "No UFC knockdowns despite regional KO record"],
       ["Make him wrestle you back and threaten guillotines on his entries",
        "Push the pace in R2",
        "Win the clinch exchanges along the fence"],
       [n("2026-09-15", "Booked against Wellington Turman for Nov. 7.", "cage_igor"),
        n("2026-10-08", "Korean coverage says he has changed his nickname to 'Technical' and is chasing his first UFC finish.",
          "starnews_ko"),
        n("2026-07-18", "Lost a unanimous decision (29-28 x3) to Jean-Paul Lebosnoyani, his first UFC loss.", "cage_jp")],
       ["ufc_ko", "cage_jp", "kherald_ko", "sherdog_elliott", "starnews_ko", "cage_igor", "wiki_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Wellington Turman",
       "A Brazilian welterweight (18-8, age 30; Teixeira MMA in Connecticut) who returns from nearly three years out: his last "
       "fight was a R2 submission loss to Jared Gooden in December 2023, his third straight loss (3-6 UFC). LowKick reports four "
       "shoulder surgeries in the layoff. A July return against Islam Dulatov was cancelled on fight day when Dulatov was "
       "hospitalized; Turman had made weight.",
       {"Striking": "Muay Thai base. Calf kicks and a straight right; his best work comes in the clinch with short elbows, which "
                    "bloodied Randy Brown's nose and swelled his eye in R3 (Cageside). Was knocked out in R1 twice in 2020-21 "
                    "(Andrew Sanchez, Bruno Silva).",
        "Grappling": "A submission threat: eight career submissions (six in R1), including an R2 armbar of Misha Cirkunov "
                     "in the UFC (Wikipedia). Offensive wrestling is poor (30% takedowns, 0-for-10 against Silva and 0-for-5 against Brown in our "
                     "data). Defensively, Andre Petroski took him down 8 times in 11 attempts.",
        "Defense": "The weak spot: 51% striking defense, absorbs 4.2 strikes a minute, 49% takedown defense. Gooden hurt him with a "
                   "right hook in R2, dropped him to his knees, then mounted him and finished with an RNC (MMA Junkie).",
        "Pace & cardio": "Starts better than he finishes in recent fights: won or split R1 against Gooden and Brown, then lost R2 "
                         "both times (MMA Junkie; Cageside). Rallied late in R3 against Brown. Stoppage losses came in R1 (two KOs) "
                         "and R2 (one sub). His regional finishes were mostly R1-R2.",
        "Fight IQ": "Gets drawn into wrestling exchanges he loses. Unknown after a near-three-year layoff and four shoulder "
                    "surgeries."},
       ["Clinch elbows and calf kicks",
        "Opportunistic submissions off scrambles",
        "Recent pattern: competitive R1, loses R2",
        "Can be taken down and held"],
       ["Ring rust: no fight since Dec. 2023",
        "Shoulder after four surgeries, against a judo/sambo grappler",
        "Durability: two R1 KO losses and a hurt-then-submitted R2 loss"],
       ["Take him down and keep him there",
        "Pressure him in R2 when his output has dropped in recent fights",
        "Avoid his clinch elbows; take the clinch to the mat"],
       [n("2026-09-09", "Booked against Ko Seok-hyeon at welterweight for Nov. 7.", "rotowire_turman"),
        n("2026-07-25", "His return against Islam Dulatov was cancelled on fight day when Dulatov was hospitalized with an "
                        "infection; Turman had weighed in at 170. Reported to have had four shoulder surgeries during the layoff.",
          "lowkick_dulatov")],
       ["wiki_turman", "lowkick_dulatov", "rotowire_turman", "cage_rbrown", "mmaj_gooden", "cage_igor", "wiki_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Mantas Kondratavicius",
       "A Lithuanian middleweight (9-1, age 26-27; 1-0 UFC) from the 2025 Contender Series, where he knocked out Djani Barbir in "
       "66 seconds. A powerful finisher (six KO/TKOs) who dropped Antonio Trocoli with an elbow in his UFC debut, then faded so "
       "badly in R3 that LowKick said he ran out of steam. Now faces Andre Petroski, a grinding wrestler who joined the card on "
       "short notice.",
       {"Striking": "Heavy hands and elbows: a jab-right finished Barbir; a short right elbow dropped Trocoli early in R2 and cut "
                    "him badly (Cageside; LowKick). Knockdowns in both his DWCS and UFC fights (about 1.1 per 15 in our data). He "
                    "out-landed Trocoli 75-17 in significant strikes (our data), with some wild overhands.",
        "Grappling": "Says he has rebuilt his wrestling and grappling with the best wrestlers in Lithuania since his only loss "
                     "(UFC.com). Reversed clinch positions on the fence against Trocoli, landed a takedown and ground strikes, and "
                     "nearly finished an RNC at the end of R2. Regional subs in R1 and R2.",
        "Defense": "Was clinched and kneed on the fence early by Trocoli and taken down once in R3, but got straight up (Cageside). "
                   "Trocoli tried 12 takedowns and landed one (our data). His one loss was an R2 submission to Virgil Augen in 2023.",
        "Pace & cardio": "Fast starter, clear late fade. Wins: KOs in R1 (four) and R2 (two), subs in R1 and R2; his only decision "
                         "is the Trocoli fight, where both men were exhausted in R3 and he did little (Cageside; LowKick). His only loss came in R2. He has never shown he can keep the pace for 15 minutes.",
        "Fight IQ": "Aggressive by nature; says he always goes in 'prepared for a war' and doesn't plan particular finishes "
                    "(UFC.com). Had a groin strike in R2 against Trocoli."},
       ["R1-R2 power: elbows and right hands",
        "Fast start; all eight stoppage wins in R1-R2",
        "Faded hard in R3 of his only 15-minute fight",
        "Takes the back when opponents are hurt"],
       ["Cardio past 10 minutes",
        "A grinding wrestler on short notice (Petroski) is the worst style for a fader",
        "Only one UFC fight"],
       ["Survive R1, clinch and wrestle, and drag him into R3",
        "Keep him on the fence to drain him",
        "Don't trade with him early"],
       [n("2026-10-26", "His opponent is now Andre Petroski. EssentiallySports reports that Petroski's Oct. 31 bout with Azamat "
                        "Bekoev was scrapped after Bekoev had an anaphylactic reaction and passed out in a CVS (MiddleEasy has the "
                        "same account), and that Petroski was moved to this fight. Wikipedia instead says Kondratavicius's original "
                        "opponent, Wesley Schultz, pulled out and was replaced by Petroski. Sources disagree on what happened to "
                        "Schultz.", "es_bekoev"),
        n("2026-03-21", "Won his UFC debut over Antonio Trocoli by decision (30-27, 29-27, 29-27) after dropping him in R2.",
          "cage_trocoli")],
       ["cage_trocoli", "lowkick_trocoli", "ufc_mantas", "es_bekoev", "middleeasy_bekoev", "wiki_event"],
       "moderate")


out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
