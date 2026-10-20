"""Scouting reports (part A) for UFC Fight Night: Moicano vs. Nolan (UFC Vegas 123 / Fight Night 292, 2026-10-31),
first pass written 2026-10-20.

Fight-week previews aren't out yet: these draw on recent-fight recaps, earlier previews, booking news and our
verified records. Round/method counts are taken from data/verified/fights.csv. Later runs should refresh them
with the Sherdog/MMA Mania/UFC.com previews and weigh-in news.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATED = "2026-10-20T18:00:00+00:00"
EVENT = "UFC Fight Night: Moicano vs. Nolan"


def src(outlet, title, url, date, author=""):
    return {"outlet": outlet, "author": author, "title": title, "url": url, "date": date}


SRC = {
    # card / booking
    "ufc_event": src("UFC.com", "UFC Fight Night: Moicano vs. Nolan (event page)",
                     "https://www.ufc.com/event/ufc-fight-night-october-31-2026", "2026-10-20"),
    "wiki_event": src("Wikipedia", "UFC Fight Night: Moicano vs. Nolan",
                      "https://en.wikipedia.org/wiki/UFC_Fight_Night:_Moicano_vs._Nolan", "2026-10-19"),
    "sbn_card": src("Yahoo Sports (SB Nation)", "Latest UFC Vegas 123 fight card, start time, date and location",
                    "https://sports.yahoo.com/articles/latest-ufc-vegas-123-fight-174019350.html", "2026-09-24",
                    "Jesse Holland"),
    "cage_main": src("Cageside Press", "With Brian Ortega Out, Renato Moicano Gets Tom Nolan in UFC Vegas 123 Headliner",
                     "https://cagesidepress.com/2026/09/14/brian-ortega-out-renato-moicano-gets-tom-nolan-in-ufc-vegas-123/",
                     "2026-09-14", "Jay Anderson"),
    "mmaw_ortega": src("Yahoo Sports (MMA Weekly)", "Brian Ortega out of UFC 331 fight with injury, Renato Moicano gets new opponent",
                       "https://sports.yahoo.com/articles/brian-ortega-ufc-331-fight-013215642.html", "2026-09-15",
                       "Joshua Ryan"),
    "unc_moicano": src("Yahoo Sports (Uncrowned)",
                       "Renato Moicano blasts Brian Ortega for ruining 'easy paycheck' at UFC 331, cautions future Ortega opponents",
                       "https://sports.yahoo.com/mma/article/renato-moicano-blasts-brian-ortega-for-ruining-easy-paycheck-at-ufc-331-cautions-future-ortega-opponents-222910887.html",
                       "2026-09-15", "Drake Riggs"),
    "mmaw_topuria": src("MMA Weekly", "Renato Moicano volunteers to be Ilia Topuria's UFC return tune-up fight",
                        "https://www.mmaweekly.com/news/renato-moicano-volunteers-to-be-ilia-topurias-ufc-return-tune-up-fight",
                        "2026-10-03"),
    "cage_331_next": src("Cageside Press", "What's Next: UFC 331 Losers",
                         "https://cagesidepress.com/2026/09/21/whats-next-ufc-331-losers/", "2026-09-21"),
    # Moicano
    "sherdog_duncan_prev": src("Sherdog", "Preview: UFC Vegas 115 'Moicano vs. Duncan'",
                               "https://www.sherdog.com/news/articles/1/Preview-UFC-Vegas-115-Moicano-vs-Duncan-200695",
                               "2026-04-01", "Ben Duffy"),
    "sherdog_duncan": src("Sherdog", "Renato 'Moicano' submits Chris Duncan in UFC Vegas 115 headliner",
                          "https://www.sherdog.com/news/news/Renato-Moicano-submits-Chris-Duncan-in-UFC-Vegas-115-headliner-200716",
                          "2026-04-04", "Tristen Critchfield"),
    "lowkick_duncan": src("LowKick MMA", "Renato Moicano Dominates! RNC Ends Chris Duncan's Night In Round 2",
                          "https://www.lowkickmma.com/renato-moicano-vs-chris-duncan-ufc-vegas-115/", "2026-04-04"),
    "cage_dariush": src("Cageside Press", "Beneil Dariush Dominates Moicano In Return From 2-Year Layoff",
                        "https://cagesidepress.com/2025/06/28/beneil-dariush-dominates-moicano-in-return-from-2-year-layoff/",
                        "2025-06-28"),
    # Nolan
    "sherdog_ziam_prev": src("Sherdog", "Preview: UFC Vegas 118 'Muhammad vs. Bonfim' - Ziam vs. Nolan",
                             "https://www.sherdog.com/news/articles/3/Preview-UFC-Vegas-118-Muhammad-vs-Bonfim-201430",
                             "2026-06-04", "Ben Duffy"),
    "cage_ziam": src("Cageside Press", "UFC Vegas 118: Tom Nolan Snaps Fares Ziam's Win Streak, Extends Own",
                     "https://cagesidepress.com/2026/06/06/ufc-vegas-118-tom-nolan-snaps-fares-ziams-win-streak-extends-own/",
                     "2026-06-06", "Brett Cagle"),
    "cage_nolan_int": src("Cageside Press", "UFC Vegas 118: Tom Nolan Wants to Fight \"Awesome,\" \"Scary\" Moicano",
                          "https://cagesidepress.com/2026/06/08/ufc-vegas-118-tom-nolan-moicano/", "2026-06-08",
                          "Destiny McCubbin, Jay Anderson"),
    "lowkick_v118": src("LowKick MMA", "UFC Vegas 118 Power Rankings: Rating The Night's Big Winners At The Meta APEX",
                        "https://www.lowkickmma.com/ufc-vegas-118-power-rankings-rating-the-nights-big-winners-at-the-meta-apex/",
                        "2026-06-08"),
    "cage_borshchev": src("Cageside Press", "UFC 312: Tom Nolan Stops Slava Claus From Delivering in Australia",
                          "https://cagesidepress.com/2025/02/08/ufc-312-tom-nolan-stops-slava-claus-from-delivering-in-australia/",
                          "2025-02-08"),
    "bjp_perth": src("BJPenn.com", "UFC Perth: 'Ulberg vs. Reyes' Live Results and Highlights",
                     "https://www.bjpenn.com/mma-news/ufc-perth/ufc-perth-ulberg-vs-reyes-live-results-and-highlights/",
                     "2025-09-27"),
    # Yana Santos
    "cage_chiasson": src("Cageside Press", "UFC 320: Yana Santos Gets Last Laugh Over Overweight Macy Chiasson",
                         "https://cagesidepress.com/2025/10/04/ufc-320-yana-santos-gets-last-laugh-over-overweight-macy-chiasson/",
                         "2025-10-04"),
    "cage_tate": src("Cageside Press", "UFC Des Moines: Yana Santos Fends Off Late Surge, Beats Miesha Tate",
                     "https://cagesidepress.com/2025/05/03/ufc-des-moines-yana-santos-fends-off-late-surge-beats-miesha-tate/",
                     "2025-05-03"),
    "sherdog_tate": src("Sherdog", "UFC Des Moines Prelims: Yana Santos Quells Miesha Tate Rally to Procure Decision",
                        "https://www.sherdog.com/news/news/UFC-Des-Moines-Prelims-Yana-Santos-Quells-Miesha-Tate-Rally-to-Procure-Decision-196842",
                        "2025-05-03"),
    "cage_yana_weight": src("Cageside Press", "Yana Santos Calls for Harsher Penalties After Chiasson Weight Miss",
                            "https://cagesidepress.com/2025/10/06/yana-santos-calls-for-harsher-penalties-after-chiasson-weight-miss/",
                            "2025-10-06"),
    "cage_v116_next": src("Cageside Press", "What's Next: UFC Vegas 116 Losers",
                          "https://cagesidepress.com/2026/04/27/whats-next-ufc-vegas-116-losers/", "2026-04-27"),
    "rotowire_yana": src("Rotowire", "Yana Santos MMA Stats & News", "https://www.rotowire.com/mma/player/yana-santos-1507",
                         "2026-08-20"),
    "middleeasy_yana": src("MiddleEasy", "Yana Santos Signs UFC Fight Contract, Luana Santos Matchup Reported For Oct. 31",
                           "https://middleeasy.com/mma-news/yana-santos-luana-santos-ufc-fight-night-292-contract",
                           "2026-08-20", "Jake Blend"),
    "cage_v121_next": src("Cageside Press", "What's Next: UFC Vegas 121 Losers",
                          "https://cagesidepress.com/2026/09/28/whats-next-ufc-vegas-121-losers/", "2026-09-28"),
    # Luana Santos
    "cage_rosa": src("Cageside Press", "UFC Vegas 119: Luana Santos Sails Past Karol Rosa",
                     "https://cagesidepress.com/2026/06/20/ufc-vegas-119-luana-santos-sails-past-karol-rosa/", "2026-06-20"),
    "cage_luana_gold": src("Cageside Press", "Luana Santos Eyes UFC Gold in 2027 After Statement Win",
                           "https://cagesidepress.com/2026/06/23/luana-santos-eyes-ufc-gold-in-2027-after-statement-win/",
                           "2026-06-23", "Destiny McCubbin, Eddie Law"),
    "cage_croden": src("Cageside Press", "Luana Santos Outgrinds Melissa Croden to Earn Decision Win",
                       "https://cagesidepress.com/2025/12/13/luana-santos-outgrinds-melissa-croden-to-earn-decision-win/",
                       "2025-12-13"),
    "bjp_lisboa": src("BJPenn.com", "UFC Vegas 106: 'Burns vs. Morales' Live Results and Highlights",
                      "https://www.bjpenn.com/mma-news/ufc-vegas-106/ufc-vegas-106-burns-vs-morales-live-results-and-highlights/",
                      "2025-05-17"),
    # Lebosnoyani / Hasanov
    "cage_ko": src("Cageside Press", "UFC Oklahoma City: Jean-Paul Lebosnoyani Claims Decision Over Seok Hyeon Ko",
                   "https://cagesidepress.com/2026/07/18/ufc-oklahoma-city-jean-paul-lebosnoyani-claims-decision-over-seok-hyeon-ko/",
                   "2026-07-18", "Nick Holt"),
    "cage_rowe": src("Cageside Press", "UFC Houston: Jean-Paul Lebosnoyani Takes Split Over Phil Rowe in Debut",
                     "https://cagesidepress.com/2026/02/21/ufc-houston-jean-paul-lebosnoyani-takes-split-over-phil-rowe-in-debut/",
                     "2026-02-21", "Shawn Bitter"),
    "rotowire_jp": src("Rotowire", "Jean-Paul Lebosnoyani MMA Stats & News",
                       "https://www.rotowire.com/mma/player/jean-paul-lebosnoyani-2701", "2026-09-01"),
    "kherald_ko": src("The Korea Herald", "Ko Seok-hyun suffers first UFC loss", "https://www.koreaherald.com/article/10812773",
                      "2026-07-19"),
    "idman_hasanov": src("Idman.biz", "Farman Hasanov learns opponent for second UFC fight",
                         "https://www.idman.biz/en/news/mma/153907", "2026-09-01"),
    "lowkick_hasanov": src("LowKick MMA", "Farman Hasanov Grinds Out Eric Nolan To Remain Undefeated At UFC Baku",
                           "https://www.lowkickmma.com/farman-hasanov-defeats-eric-nolan-ufc-baku/", "2026-06-27",
                           "Pranav Pandey"),
    "mmamania_rookies": src("MMA Mania", "Rookie Report Card: Grading all Octagon newcomers UFC Baku post-mortem",
                            "https://www.mmamania.com/latest-news/453399/rookie-report-card-grading-all-octagon-newcomers-ufc-baku-post-mortem",
                            "2026-06-29"),
    # Bekoev
    "sherdog_gore_prev": src("Sherdog", "Preview: UFC Vegas 115 prelims - Bekoev vs. Gore",
                             "https://www.sherdog.com/news/articles/6/Preview-UFC-Vegas-115-prelims-200690", "2026-04-01",
                             "Ben Duffy"),
    "cage_gore": src("Cageside Press", "UFC Vegas 115: Tresean Gore Upsets Azamat Bekoev With Nasty Guillotine",
                     "https://cagesidepress.com/2026/04/04/ufc-vegas-115-tresean-gore-upsets-azamat-bekoev-with-nasty-guillotine/",
                     "2026-04-04", "Patrick Danna"),
    "cage_belgaroui": src("Cageside Press", "Yousri Belgaroui Breaks Down Bekoev for Late Finish in Violent UFC Debut",
                          "https://cagesidepress.com/2025/10/18/yousri-belgaroui-breaks-down-bekoev-for-late-finish-in-violent-ufc-debut/",
                          "2025-10-18", "Shawn Bitter"),
    "wiki_bekoev": src("Wikipedia", "Azamat Bekoev", "https://en.wikipedia.org/wiki/Azamat_Bekoev", "2026-10-19"),
    "gidstats_bekoev": src("GidStats", "Andre Petroski vs Azamat Bekoev (bout page)",
                           "https://gidstats.com/events/ufc_fight_night-2026-11-01/andre_petroski_vs_azamat_bekoev.html",
                           "2026-10-20"),
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
report("Renato Carneiro",
       "Renato 'Moicano' Carneiro (21-7-1, age 37) is a veteran Brazilian lightweight and former title challenger: a "
       "high-level opportunistic jiu-jitsu player with better boxing than his record suggests. He's back in the win column "
       "after submitting Chris Duncan in round two in April, and takes Tom Nolan on about six weeks' notice after Brian "
       "Ortega pulled out of their UFC 331 rematch. Every one of his losses at lightweight has come against an elite "
       "wrestler or a big puncher.",
       {"Striking": "Long, accurate jab (50% significant accuracy) with a straight right behind it. Against Duncan he worked the "
                    "jab and clinch in round one and dropped him with a left hook in round two (per Sherdog; our verified fight data "
                    "doesn't record that knockdown). He also dropped Beneil Dariush with a straight right late in round one at UFC 317 "
                    "(Cageside Press). Sherdog's Ben Duffy rates him a better striker than his record suggests. His two TKO wins "
                    "(Jalin Turner, Benoit Saint-Denis) both came in 2024, both in round two.",
        "Grappling": "This is his real weapon. Eleven of his 21 wins are submissions. He hunts the back quickly when an opponent "
                     "is hurt or scrambling (Duncan, face crank or RNC depending on the outlet, 3:14 of R2; Sherdog says face crank, "
                     "LowKick says rear-naked choke). Duffy calls his ground-and-pound 'underratedly nasty' and says he does his best "
                     "work on top; he wrestles better offensively than his frame suggests (about 1.6 takedowns per 15 minutes).",
        "Defense": "Takedown defense is the hole (about 55%). Makhachev, Dariush and Rafael dos Anjos all beat him by putting him on "
                   "his back: Dariush went 5-for-5 on takedowns with almost six minutes of control, and dos Anjos held him down for "
                   "over 13 minutes across five rounds. He was knocked out three times at 145/155 (Chan Sung Jung R1, Rafael Fiziev "
                   "R1, Jose Aldo R2), all against high-level strikers, the last in 2020.",
        "Pace & cardio": "A front-to-middle-round finisher. His 13 stoppage wins came 4 in R1, 8 in R2 and only 1 in R3 (2010); "
                         "his last seven finishes all came in R1 or R2. His five stoppage losses: three in R1 (Jung KO, Fiziev TKO, "
                         "Makhachev sub), one in R2 (Aldo TKO), one in R3 (Brian Ortega guillotine, 2017, a fight he was winning). "
                         "His only five-round fight was the 2022 decision loss to dos Anjos, where he was controlled for most of it. "
                         "Against Dariush he won R1, then got taken down and lost R2-R3. At 37, how he holds up in rounds 4-5 is an open "
                         "question.",
        "Fight IQ": "Experienced and opportunistic, and quick to pounce on a hurt opponent. Brash outside the cage. Took this "
                    "fight calling Nolan the harder opponent than Ortega and saying 'it is what it is' (Uncrowned)."},
       ["Jab-led boxing to set up takedowns and scrambles",
        "Jumps on the back the moment an opponent is hurt; 11 career submissions",
        "Finishes come early: 12 of 13 stoppage wins in R1-R2, the last seven all inside two rounds",
        "Loses when out-wrestled and held down (dos Anjos, Makhachev, Dariush) or caught by elite punchers (Jung, Fiziev, Aldo)",
        "Strong first round, fades when he spends time on his back (Dariush won R2-R3)"],
       ["Age 37, with a long career's worth of wear (Sherdog)",
        "Takedown defense against a big, strong opponent",
        "One career five-round fight, and he lost it on the mat",
        "Short-notice change of opponent: he'd prepared for Ortega, a different body type and style from the 6-foot-3 Nolan"],
       ["Wrestle him and hold top position; make him carry weight into the later rounds",
        "Respect his scrambles: don't give up the back when getting up",
        "Survive his first two rounds, then push the pace in the championship rounds"],
       [n("2026-09-14", "Brian Ortega withdrew from their UFC 331 rematch with a cut over his left eye, the second time he'd pulled out "
                        "of the fight this year. Moicano was moved to headline this card against Tom Nolan.", "cage_main"),
        n("2026-09-15", "Moicano said Nolan will be a harder fight than Ortega would have been, and that he won't book Ortega again "
                        "(Uncrowned).", "unc_moicano"),
        n("2026-10-03", "MMA Weekly headline: Moicano volunteered to be Ilia Topuria's tune-up fight when Topuria returns.", "mmaw_topuria"),
        n("2026-04-04", "Submitted Chris Duncan at 3:14 of R2 (Sherdog: face crank) to end a two-fight losing streak.", "sherdog_duncan")],
       ["cage_main", "mmaw_ortega", "unc_moicano", "mmaw_topuria", "sherdog_duncan_prev", "sherdog_duncan", "lowkick_duncan",
        "cage_dariush", "ufc_event", "wiki_event"],
       "good")

# ---------------------------------------------------------------------------------------------------------------
report("Tom Nolan",
       "A huge Australian lightweight (11-1, age 27; about 188 cm) from Contender Series 2023, on a five-fight win streak capped "
       "by an upset decision over Fares Ziam in June as roughly a 3-to-1 underdog. He uses his size in the clinch, has real "
       "power, and has improved his grappling. This is his first main event and first scheduled five-rounder.",
       {"Striking": "Big power for 155 (5 KO/TKO wins, about 0.35 knockdowns per 15 minutes). Sherdog's Ben Duffy says he has added "
                    "range management to his power: he met Victor Martinez's entries with uppercuts and knees, and a knee set up "
                    "the finish. Spinning elbows were a weapon against Ziam (Cageside Press). Throws about 4.2 significant strikes a "
                    "minute, but absorbs 3.5.",
        "Grappling": "Duffy calls him 'a solid grappler' who likes back control and chokes that suit his long frame. He submitted "
                     "Charlie Campbell with an RNC off a takedown in R1, and against Ziam he won key exchanges from top position and "
                     "out-controlled him (about 6:47 to 5:07 in our data). He 'embraces the clinch' to cancel out faster opponents. "
                     "Threatened with upkicks off his back against Borshchev (Cageside).",
        "Defense": "The weak spot. Duffy flags his limited speed and 'tall-man defensive habits' and expects good overhand rights to "
                   "find him. Nikolas Motta knocked him out in 63 seconds in his UFC debut, his only loss. Takedown defense is "
                   "middling (about 55%); Ziam took him down and got to his back in R3.",
        "Pace & cardio": "Early finisher, late decision winner. All six stoppage wins came in R1 or R2 (five in R1: four KOs and the "
                         "Campbell submission; one KO in R2). His other five wins went the full 15 minutes, and he has won late "
                         "rounds and close fights (29-28 x3 over Ziam; 29-28, 29-28, 30-27 over Borshchev). His only stoppage loss "
                         "was in R1 (Motta). He has never fought past three rounds. Said in June that he used to come in too light and "
                         "now does a proper water cut, which left him feeling 'normal' on fight night (Cageside).",
        "Fight IQ": "Builds a specific plan for each opponent (a 'boxing camp approach', per Cageside) and said he borrowed ideas "
                    "from Moicano's win over Benoit Saint-Denis for the Ziam fight. Has worked with a mental performance coach. "
                    "Called Moicano out by name after beating Ziam and praised his 'scary' striking and grappling."},
       ["Uses height and length in the clinch, with knees and elbows",
        "Finishes come early: six of six stoppages in R1-R2",
        "Grinds out close decisions when he can't finish (five three-round wins)",
        "Hittable early; his only loss was an R1 KO",
        "Wins scrambles and takes the back"],
       ["Never been past three rounds",
        "Defensive habits and hand speed against a sharp boxer",
        "Bottom position against an elite jiu-jitsu player: Moicano finishes from the back and from scrambles",
        "First main event"],
       ["Beat him to the punch with straight shots and overhands as he comes in upright",
        "Make him defend takedowns early, then attack the neck in scrambles",
        "Stay off the fence and out of his clinch"],
       [n("2026-09-14", "Booked for his first UFC main event, replacing Brian Ortega as Renato Moicano's opponent. Cageside notes he "
                        "was ranked No. 11 at the time; the UFC.com event page now shows the pair at No. 12 and No. 14.",
          "cage_main"),
        n("2026-06-08", "After beating Ziam he called out Moicano, saying he'd admired him since childhood.", "cage_nolan_int"),
        n("2026-06-06", "Beat Fares Ziam by unanimous decision (29-28 x3) as roughly a +270 underdog, snapping Ziam's win streak.",
          "cage_ziam")],
       ["cage_main", "mmaw_ortega", "sherdog_ziam_prev", "cage_ziam", "cage_nolan_int", "lowkick_v118", "cage_borshchev",
        "bjp_perth", "cage_331_next", "ufc_event"],
       "good")

# ---------------------------------------------------------------------------------------------------------------
report("Yana Santos",
       "A veteran Russian bantamweight striker (17-8, 1 NC; 7-5 UFC; age 37), formerly Yana Kunitskaya and once a title challenger "
       "against Cris Cyborg. She has won three straight decisions (Chandler, Tate, Chiasson), but hasn't fought since October 2025 "
       "after pulling out of an April 2026 bout with Norma Dumont.",
       {"Striking": "Busy, accurate kickboxer: about 4.8 significant strikes a minute at 54%. Jab, straight cross, leg kicks and front "
                    "kicks. She bloodied Chiasson in R1 and landed a front kick to the face in R2 (Cageside), and chopped Tate's legs. "
                    "Cageside notes she threw over 150 total strikes in the first ten minutes against Chiasson.",
        "Grappling": "Little offense on the mat (0.4 takedowns per 15, rarely tries a submission). She has some clinch takedowns and "
                     "control time (Lansberg, Chiasson), but grappling is mostly defense for her.",
        "Defense": "Solid striking defense (57%). Her takedown defense (about 59%) holds early and cracks late: Tate took her down in "
                   "R3 and she survived a deep rear-naked choke at the bell, and Chiasson got to her back in R3 and hunted a choke "
                   "(Cageside, Sherdog). She has been stopped five times: by strikes three times (Cyborg R1, Aldana R1, Ladd R3) and "
                   "by submission twice (Dishekova R1, Evinger R2; both before 2018).",
        "Pace & cardio": "Every UFC win (7) has been a decision. All nine finishes came before 2017: eight in R1, one in R2. The pattern "
                         "in her recent fights is to win R1-R2 on the feet, then get taken down and lose R3, without being finished. "
                         "Stoppage losses: three in R1, one in R2, one in R3 (Aspen Ladd TKO, 2019). Not a fader in output, but "
                         "vulnerable to late wrestling.",
        "Fight IQ": "Disciplined; knows she's winning the striking and banks the early rounds. A veteran who has seen everything, "
                    "though she has historically lost the grappling-heavy fights (Holm controlled her for nearly ten minutes)."},
       ["Wins on volume and accuracy at range, all by decision in the UFC",
        "Takes R1 and R2, then gets taken down in R3 (Tate, Chiasson)",
        "Hasn't been finished since 2021 (Aldana)",
        "Loses to bigger punchers and to wrestlers who hold her down"],
       ["A year out of action and age 37",
        "Late-round takedown defense against a grappler who controls opponents for most of the fight",
        "Withdrew from her April bout; Dumont said Santos was injured, other outlets list the reason as undisclosed"],
       ["Close distance and take her down; she gives little from bottom",
        "Win the third round on the mat",
        "Don't stand at range and trade with her for 15 minutes"],
       [n("2026-04-27", "Pulled out of her April 25 fight with Norma Dumont at UFC Vegas 116; Cageside refers to an injury, Rotowire lists "
                        "the reason as undisclosed.", "cage_v116_next"),
        n("2026-08-20", "Announced a signed fight contract against what she called her highest-ranked UFC opponent yet, later "
                        "confirmed as Luana Santos.", "middleeasy_yana"),
        n("2026-09-28", "Rankings disagree: Cageside lists Yana at No. 6 and Luana at No. 3; the UFC.com event page shows the two at "
                        "No. 6 and No. 7.", "cage_v121_next")],
       ["cage_chiasson", "cage_tate", "sherdog_tate", "cage_yana_weight", "cage_v116_next", "rotowire_yana", "middleeasy_yana",
        "cage_v121_next", "ufc_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Luana Santos",
       "A 27-year-old Brazilian grappler (11-2; 6-1 UFC) who moved up from flyweight and has won three straight at bantamweight. "
       "Most recently she shut out Karol Rosa 30-27 on all three cards with more than 12 minutes of control. She has never been "
       "finished, and calls herself a 'suffocating' fighter.",
       {"Striking": "Low volume (about 2.4 significant strikes a minute) but efficient and hard to hit. Mainly a leg kick and a "
                    "sharp 1-2 to enter, plus overhand rights on the way to the clinch (Cageside, on Croden and Rosa). Has one TKO in "
                    "the UFC (Juliana Miller, R1).",
        "Grappling": "The core of her game: judo, takedowns in open space and against the fence, long top control (51% control share), "
                     "back takes. Kept Rosa down for 741 seconds and Croden for 561 seconds. Five submissions, including an Americana "
                     "of Tainara Lisboa at 4:59 of R2 and an R1 finish of Mariya Agapova.",
        "Defense": "Very good: 70% striking defense, absorbs only 1.6 a minute, 77% takedown defense. Never stopped. Both losses were "
                   "decisions (a split to Jena Bishop in LFA, and Casey O'Neill out-landing her 83-41 at UFC 305).",
        "Pace & cardio": "Steady three-round grinder. Six finishes: four in R1 (three submissions plus the Miller TKO), one at 4:59 "
                         "of R2 (Lisboa) and one early in R3 (regional, 2022). Her last two fights went the distance with control in every "
                         "round, so she doesn't fade. Has never been stopped in any round.",
        "Fight IQ": "Patient and disciplined: picks her entries, then stays heavy on top. She loses when out-worked at range by a "
                    "volume striker who stays upright (O'Neill)."},
       ["Takedown, then long top control and back takes",
        "Low-volume, efficient striking to set up entries",
        "Never finished; both losses were decisions",
        "Finishes come early (four of six in R1) or not at all; her last two wins were 15-minute grinds"],
       ["Out-landed badly by a high-volume striker (O'Neill 83-41)",
        "Low striking output means she can drop rounds where she doesn't get the takedown",
        "Smaller frame than a natural bantamweight"],
       ["Keep her at range and out-volume her",
        "Defend the first takedown and make her strike",
        "Punish her entries with counters"],
       [n("2026-06-20", "Beat Karol Rosa by unanimous decision (30-27 x3), controlling most of the fight.", "cage_rosa"),
        n("2026-06-23", "Said her goal is to be UFC champion in 2027 and called herself a fighter who can suffocate anyone in the "
                        "division (Cageside).", "cage_luana_gold"),
        n("2026-09-28", "Rankings disagree: Cageside lists her at No. 3; the UFC.com event page shows the pair at No. 6 and No. 7.",
          "cage_v121_next")],
       ["cage_rosa", "cage_luana_gold", "cage_croden", "bjp_lisboa", "cage_v121_next", "middleeasy_yana", "ufc_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Jean-Paul Lebosnoyani",
       "A 28-year-old California welterweight (11-2; 2-0 UFC) out of the 2025 Contender Series, nicknamed 'Mufasa'. An explosive, "
       "aggressive wrestle-boxer and front-end finisher on the regional scene (seven R1 stoppages) who has won two close UFC "
       "decisions over Phil Rowe and Seok Hyeon Ko.",
       {"Striking": "Throws first and likes chaotic exchanges: explosive entries, leg kick into overhand, clubbing hooks (Cageside). "
                    "About 4.1 significant strikes a minute at 55%, with real power (0.63 knockdowns per 15). Rowe and Ko both landed "
                    "heavier shots on him at range.",
        "Grappling": "Sharp, well-timed double legs in open space and against the fence. He floats on top and threatens the neck in "
                     "scrambles: d'Arce against Rowe, two tight guillotines against Ko. Five of his eight finishes are submissions. "
                     "Ko went to judges after Lebosnoyani's takedown in the final 40 seconds sealed R3 (Korea Herald).",
        "Defense": "Hittable: absorbs about 3.6 a minute, and he took visible facial damage against Rowe (Cageside). Both losses "
                   "were knockouts by strikes: Spike Carlyle R1 (2019) and JaCobi Jones R2 (2023). Takedown defense is about 62%.",
        "Pace & cardio": "Front-loaded finisher on the regionals: seven of eight stoppage wins came in R1, the other in R2. Has had three "
                         "decisions, all 3-round fights (Kuiks 2024, Rowe, Ko). Didn't fade in either UFC fight: he won R3 against "
                         "both Rowe and Ko with takedowns (Cageside). Note: in the Rowe fight, Rotowire credits him with three "
                         "takedowns, 5:17 of control and a 66-54 striking edge, while our verified table has those numbers on Rowe's "
                         "side, so treat that fight's per-fighter stats with care. Stopped twice, in R1 and R2, both by strikes.",
        "Fight IQ": "Aggressive and willing to scramble. Makes close rounds count late with a takedown. Slow to find his range early "
                    "(Cageside, on Rowe)."},
       ["Fast starter: seven R1 stoppages before the UFC",
        "Wrestle-boxing: overhands into double legs",
        "Guillotine and d'Arce threats in scrambles",
        "Won R3 with a late takedown in both UFC fights",
        "Both losses were knockouts by strikes"],
       ["Gets hit; both losses by KO",
        "Both UFC wins were close (one split decision)",
        "A pure chain wrestler could take his takedown game away"],
       ["Counter his entries; he comes in on straight lines",
        "Make him wrestle off his back, or out-wrestle him and stay heavy",
        "Win exchanges at range"],
       [n("2026-09-01", "Announced his booking against Farman Hasanov himself; Azerbaijani outlets note his Armenian heritage "
                        "against an Azerbaijani opponent.", "idman_hasanov"),
        n("2026-07-18", "Beat Seok Hyeon Ko by unanimous decision (29-28 x3), handing Ko his first UFC loss.", "cage_ko"),
        n("2026-09-24", "Card placement varies: UFC.com and Wikipedia list the bout on the main card, while SB Nation's card list "
                        "puts it on the prelims.", "sbn_card")],
       ["cage_ko", "cage_rowe", "rotowire_jp", "kherald_ko", "idman_hasanov", "sbn_card", "ufc_event", "wiki_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Farman Hasanov",
       "An undefeated Azerbaijani welterweight wrestler ('The Lion', Renzo Gracie Academy) who made his UFC debut at home in Baku "
       "in June. He took Eric Nolan down 17 times (a welterweight single-round record of nine in R1) on the way to a 30-27 x3 "
       "decision. He was visibly tired from R2 on and did little damage. One UFC fight and long gaps between bouts.",
       {"Striking": "Limited sample: only 21 significant strikes landed against Nolan. Regionally, three of his wins were knockouts "
                    "(R1 0:47, R2, R1 4:58), mostly off top pressure, though there's little footage-based detail on his striking.",
        "Grappling": "Relentless chain wrestling: leg attacks, re-shots and level changes in scrambles (LowKick). He held Nolan for "
                     "about 11 minutes of 15 in our data, but rarely advanced position or threatened submissions. MMA Mania said he was "
                     "dominant with his wrestling but didn't do much with it.",
        "Defense": "Not hit much against Nolan, because the fight was on the ground. His defense on the feet is untested at UFC level. "
                   "Never been stopped or beaten.",
        "Pace & cardio": "Huge output early, then a fade. He was 'awfully gassed' in R2 (MMA Mania) and visibly exhausted in R3 "
                         "(LowKick), though he kept shooting through the horn. His finishes came in R1 (two) and R2 (one); his two "
                         "decisions went 15 minutes. Long layoffs (2022 to 2024, 2024 to 2025) make his conditioning harder to read.",
        "Fight IQ": "Single-minded: wrestle, wrestle again. Keeps re-shooting when stood up. It's unclear what his plan B is against a "
                    "fighter who can stop the shot."},
       ["Chain wrestling from the first minute",
        "Long top control, light damage",
        "Fades in R2-R3 but keeps shooting",
        "Undefeated; regional KOs came in R1-R2"],
       ["Cardio after the R1 takedown burst",
        "Thin striking and finishing game at UFC level",
        "Record and age differ by source: our data has him 5-0 and age 31 (Idman.biz agrees on 31); LowKick and Idman list 6-0, "
        "and LowKick says 25",
        "Only one UFC fight"],
       ["Survive R1, defend and scramble, then hunt him in R2-R3 when he's tired",
        "Threaten guillotines and front headlocks on his shots",
        "Make him strike with you"],
       [n("2026-06-27", "Debuted in Baku with a 30-27 x3 decision over Eric Nolan; credited with nine takedowns in R1, a welterweight "
                        "single-round record.", "lowkick_hasanov"),
        n("2026-09-01", "Booked against Jean-Paul Lebosnoyani for his second UFC fight.", "idman_hasanov")],
       ["lowkick_hasanov", "mmamania_rookies", "idman_hasanov", "sbn_card", "ufc_event", "wiki_event"],
       "thin")

# ---------------------------------------------------------------------------------------------------------------
report("Azamat Bekoev",
       "A Russian middleweight from Vladikavkaz (20-5; 2-2 UFC; American Top Team) and former LFA champion. He opened his UFC run "
       "with two R1 TKOs, then was stopped in R3 in back-to-back fights as a heavy favourite: by Yousri Belgaroui (TKO) and "
       "Tresean Gore (guillotine). Very dangerous early, with a clear late-fight problem.",
       {"Striking": "Utilitarian, pressure-first kickboxing: hard kicks and basic combinations that land when opponents worry about "
                    "his wrestling (Sherdog). Real power (1.1 knockdowns per 15); dropped Gore with right hands in R2. His overhands "
                    "get wild, which leaves him open to counters (Cageside, on Belgaroui).",
        "Grappling": "Straightforward single and double legs from the outside, finished decisively. Prefers ground-and-pound to "
                     "advancing position; will take the back or look for an arm-triangle (Sherdog). Eight career submission wins, all "
                     "before the UFC.",
        "Defense": "The problem. He absorbs about 5.9 significant strikes a minute and has 41% striking defense. Belgaroui out-landed "
                   "him 102-24. Duffy (Sherdog) points to defensive lapses that power and durability had been covering. All three "
                   "stoppage losses came in R3: Rafal Haratyk sub (2021), Belgaroui TKO (2025), Gore guillotine (2026).",
        "Pace & cardio": "A clear fast starter who fades. Sixteen stoppage wins: ten in R1, five in R2, one in R3 (2016). Both UFC "
                         "wins were R1 TKOs. All three stoppage losses were in R3, the last two after he was visibly exhausted: "
                         "'exhausted and retreating' against Belgaroui, and against Gore his leg was compromised by kicks and Gore was "
                         "the fresher man (Cageside). He has gone 25 minutes twice in LFA title fights, but both were decisions.",
        "Fight IQ": "Front-loads everything. Has been a big favourite in all four UFC fights and lost the last two."},
       ["R1 finisher: ten R1 stoppages, two R1 TKOs in the UFC",
        "Pressure kickboxing into takedowns and ground-and-pound",
        "Fades badly in R3; all three stoppage losses came in R3",
        "Absorbs a lot of volume"],
       ["Cardio and durability in the third round",
        "Striking defense",
        "Bout status: UFC.com and Wikipedia list it, but one stats site (GidStats) marks it cancelled with no reason given; "
        "unconfirmed"],
       ["Survive the first five minutes, then drag him into a deep fight",
        "Leg kicks and volume; he slows and gets hit late",
        "Counter his overhand"],
       [n("2026-08-21", "Booked against Andre Petroski (per Wikipedia, citing a regional Russian report).", "wiki_bekoev"),
        n("2026-10-20", "GidStats labels the Petroski bout cancelled, with no reason given; UFC.com still lists it. Unconfirmed; "
                        "re-check at fight week.", "gidstats_bekoev"),
        n("2026-04-04", "Submitted by Tresean Gore (guillotine, 3:27 R3) as roughly an 8-to-1 favourite.", "cage_gore")],
       ["sherdog_gore_prev", "cage_gore", "cage_belgaroui", "wiki_bekoev", "gidstats_bekoev", "ufc_event", "sbn_card"],
       "moderate")


out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
