"""Scouting reports (part A) for UFC 334: Gane vs. Hokit (Madison Square Garden, 2026-11-14), plus the
UFC Fight Night: Cortes-Acosta vs. Walker headliner (UFC Vegas 124 / Fight Night 293, Meta APEX, 2026-11-07).
First pass written 2026-11-03.

EVENT varies per fighter here: Waldo Cortes-Acosta and Johnny Walker are on the 2026-11-07 card, the rest on
UFC 334. report() takes the event explicitly; pass it on every call.

The Johnny Walker report replaces the thin 2026-09-30 version (written for UFC 332). It keeps that version's two
sources (Sherdog and UFC.com UFC 332 previews) and adds his UFC 332 result and the new booking.

Fight-week previews aren't out yet: these draw on recent-fight recaps, booking and injury news, and our verified
records. Round/method counts are taken from data/verified/fights.csv. Later runs should refresh them with the
Sherdog/MMA Mania/UFC.com previews and weigh-in news.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATED = "2026-11-03T18:00:00+00:00"
EVENT = "UFC 334: Gane vs. Hokit"
EVENT_WCA = "UFC Fight Night: Cortes-Acosta vs. Walker"


def src(outlet, title, url, date, author=""):
    return {"outlet": outlet, "author": author, "title": title, "url": url, "date": date}


SRC = {
    # ---- UFC Fight Night: Cortes-Acosta vs. Walker (Nov. 7) card / booking
    "cage_v124_main": src("Cageside Press", "UFC Vegas 124 Loses Bonfim vs. Brady, Heavyweight Scrap In As Headliner",
                          "https://cagesidepress.com/2026/10/29/ufc-vegas-124-loses-bonfim-vs-brady-heavyweight-headliner/",
                          "2026-10-29"),
    "sherdog_v124": src("Sherdog", "Report: Johnny Walker lands UFC Vegas 124 main event after late shake-up",
                        "https://www.sherdog.com/news/news/Report-Johnny-Walker-lands-UFC-Vegas-124-main-event-after-late-shakeup-203417",
                        "2026-10-30", "Sayan Nag"),
    "sbn_v124": src("Yahoo Sports (SB Nation)", "Report: Waldo Cortes-Acosta vs Johnny Walker now headlines UFC Vegas 124",
                    "https://sports.yahoo.com/articles/report-waldo-cortes-acosta-vs-211254449.html", "2026-10-29",
                    "Alexander Behunin"),
    "mmaj_v124": src("Yahoo Sports (MMA Junkie)", "UFC Fight Night 293: Make predictions for Waldo Cortes-Acosta vs. Johnny Walker",
                     "https://sports.yahoo.com/articles/ufc-fight-night-293-predictions-203054010.html", "2026-11-02",
                     "Matt Erickson"),
    # ---- Cortes-Acosta
    "wiki_wca": src("Wikipedia", "Waldo Cortes-Acosta", "https://en.wikipedia.org/wiki/Waldo_Cortes-Acosta", "2026-11-03"),
    "cage_blaydes": src("Cageside Press", "Noche UFC: Curtis Blaydes Defeats Waldo Cortes-Acosta in Fight That Leaves Crowd Frustrated",
                        "https://cagesidepress.com/2026/09/12/noche-ufc-curtis-blaydes-defeats-waldo-cortes-acosta-in-fight-that-leaves-crowd-frustrated/",
                        "2026-09-12", "Jay Anderson"),
    "bjp_noche": src("BJPenn.com", "Noche UFC 4: 'Silva vs. Delgado' Live Results and Highlights",
                     "https://www.bjpenn.com/mma-news/noche-ufc/noche-ufc-4-silva-vs-delgado-live-results-and-highlights/",
                     "2026-09-12"),
    "cage_volkov": src("Cageside Press", "Alexander Volkov Beats Waldo Cortes-Acosta, Calls for Title Shot Saying Pereira \"Not a Heavyweight\"",
                       "https://cagesidepress.com/2026/05/09/alexander-volkov-beats-waldo-cortes-acosta-calls-for-title-shot-saying-pereira-not-a-heavyweight/",
                       "2026-05-09", "Jay Anderson"),
    "cage_wca_md": src("Cageside Press", "UFC 328's Waldo Cortes-Acosta: How You Win As Important As Winning Itself",
                       "https://cagesidepress.com/2026/05/06/ufc-328-waldo-cortes-acosta-winning/", "2026-05-06",
                       "Patrick Danna, Jay Anderson"),
    "cage_328_wi": src("Cageside Press", "UFC 328: Chimaev vs. Strickland Weigh-In Results — One Veteran Heavy",
                       "https://cagesidepress.com/2026/05/08/ufc-328-chimaev-vs-strickland-weigh-in-results/", "2026-05-08"),
    "cage_lewis": src("Cageside Press", "UFC 324: Waldo Cortes-Acosta \"Not Surprised\" as He Stops Derrick Lewis",
                      "https://cagesidepress.com/2026/01/24/ufc-324-waldo-cortes-acosta-not-surprised-stops-derrick-lewis",
                      "2026-01-24", "Jay Anderson"),
    # ---- Walker (first two kept from the 2026-09-30 report)
    "sherdog_332_prev": src("Sherdog", "Preview: UFC 332 prelims (Walker vs. Parkin)",
                            "https://www.sherdog.com/news/articles/5/Preview-UFC-332-prelims-203006", "2026-09-30",
                            "Tom Feely"),
    "ufc_332_prev": src("UFC.com", "Fight By Fight Preview | UFC 332: Silva vs Wang",
                        "https://www.ufc.com/news/fight-fight-preview-ufc-332-silva-vs-wang-salt-lake-city", "2026-09-28",
                        "E. Spencer Kyte"),
    "cage_parkin": src("Cageside Press", "UFC 332: Johnny Walker Impressive in Heavyweight Debut, Stops Mick Parkin With Knees",
                       "https://cagesidepress.com/2026/10/03/ufc-332-johnny-walker-impressive-in-heavyweight-debut-stops-mick-parkin-with-knees/",
                       "2026-10-03", "Jay Anderson"),
    "bjp_332": src("BJPenn.com", "UFC 332: 'Silva vs. Wang' Live Results and Highlights",
                   "https://www.bjpenn.com/mma-news/ufc/ufc-332-silva-vs-wang-live-results-and-highlights/", "2026-10-03"),
    "lowkick_parkin_prev": src("LowKick MMA", "Johnny Walker vs Mick Parkin – Heavyweight debut brings risk at UFC 332",
                               "https://www.lowkickmma.com/johnny-walker-vs-mick-parkin-heavyweight-debut-brings-risk-at-ufc-332/",
                               "2026-09-24", "Timothy Wheaton"),
    "sherdog_tybura": src("Sherdog", "Johnny Walker calls out UFC veteran following explosive heavyweight debut",
                          "https://www.sherdog.com/news/news/Johnny-Walker-calls-out-UFC-veteran-following-explosive-heavyweight-debut-203125",
                          "2026-10-08", "Sourav Chakraborty"),
    "sherdog_valter": src("Sherdog", "Johnny Walker refuses to fight brother Valter: 'My own blood'",
                          "https://www.sherdog.com/news/news/Johnny-Walker-refuses-to-fight-brother-Valter-My-own-blood-203462",
                          "2026-11-02", "Sourav Chakraborty"),
    # ---- UFC 334 card
    "wiki_334": src("Wikipedia", "UFC 334", "https://en.wikipedia.org/wiki/UFC_334", "2026-11-03"),
    "cage_334_card": src("Cageside Press", "Ciryl Gane vs. Josh Hokit Headlines UFC 334, Kayla Harrison vs. Amanda Nunes Co-Main at MSG",
                         "https://cagesidepress.com/2026/09/19/ciryl-gane-vs-josh-hokit-headlines-ufc-334-kayla-harrison-vs-amanda-nunes-co-main-at-msg/",
                         "2026-09-19", "Eddie Law"),
    "sherdog_334_odds": src("Sherdog", "UFC 334 odds: Amanda Nunes returns as underdog at MSG",
                            "https://www.sherdog.com/news/news/UFC-334-odds-Amanda-Nunes-returns-as-underdog-at-MSG-203400",
                            "2026-10-29", "Sayan Nag"),
    # ---- Gane / Hokit
    "cage_pereira": src("Cageside Press", "UFC Freedom 250: Ciryl Gane Lights Up, Devastates Alex Pereira, Spoiling Heavyweight Debut",
                        "https://cagesidepress.com/2026/06/15/ufc-freedom-250-ciryl-gane-lights-up-devastates-alex-pereira-spoiling-heavyweight-debut/",
                        "2026-06-15", "Jay Anderson"),
    "mmaj_cruz": src("Yahoo Sports (MMA Junkie)", "Dominick Cruz says UFC champion Ciryl Gane not to blame for fouls",
                     "https://sports.yahoo.com/articles/dominick-cruz-says-ufc-champion-175027536.html", "2026-10-29"),
    "mmaj_lopez": src("Yahoo Sports (MMA Junkie)", "Ciryl Gane's coach compares 'huge challenge' Josh Hokit to UFC legend",
                      "https://sports.yahoo.com/articles/ciryl-ganes-coach-compares-huge-193023554.html", "2026-10-19",
                      "Farah Hannoun"),
    "mmaj_masvidal": src("Yahoo Sports (MMA Junkie)", "Jorge Masvidal: Josh Hokit 'could break' Ciryl Gane at UFC 334",
                         "https://sports.yahoo.com/articles/jorge-masvidal-josh-hokit-could-212027942.html", "2026-11-02",
                         "Farah Hannoun"),
    "sherdog_jones": src("Sherdog", "Jon Jones says Josh Hokit can beat Ciryl Gane, but there's a catch",
                         "https://www.sherdog.com/news/news/Jon-Jones-says-Josh-Hokit-can-beat-Ciryl-Gane-but-theres-a-catch-203194",
                         "2026-10-13", "Sourav Chakraborty"),
    "cage_hokit_blaydes": src("Cageside Press", "Josh Hokit Takes Decision Over Blaydes In FOTY Candidate",
                              "https://cagesidepress.com/2026/04/11/josh-hokit-takes-decision-over-blaydes-in-foty-candidate",
                              "2026-04-11", "Eddie Law"),
    "cage_hokit_lewis": src("Cageside Press", "UFC Freedom 250: Josh Hokit Does It Again, Fells Derrick Lewis",
                            "https://cagesidepress.com/2026/06/14/ufc-freedom-250-josh-hokit-does-it-again-fells-derrick-lewis/",
                            "2026-06-14", "Jay Anderson"),
    # ---- Harrison / Nunes
    "cage_334_backup": src("Cageside Press", "UFC 334 Title Fight Gets Unexpected Back-Up Fighter",
                           "https://cagesidepress.com/2026/10/29/ufc-334-title-fight-gets-unexpected-back-up-fighter/",
                           "2026-10-29"),
    "sherdog_kh_neck": src("Sherdog", "Kayla Harrison questioned her recovery after neck surgery: 'But I'm back'",
                           "https://www.sherdog.com/news/news/Kayla-Harrison-questioned-her-recovery-after-neck-surgery-But-Im-back-203188",
                           "2026-10-13", "Sourav Chakraborty"),
    "unc_kh_year": src("Yahoo Sports (Uncrowned)",
                       "Kayla Harrison opens up on brutal year that nearly drove her into retirement: 'I wasn't even crawling'",
                       "https://sports.yahoo.com/mma/article/kayla-harrison-opens-up-on-brutal-year-that-nearly-drove-her-into-retirement-i-wasnt-even-crawling-ufc-334-amanda-nunes-213847981.html",
                       "2026-10-16", "Drake Riggs"),
    "cage_kh_pena": src("Cageside Press", "Kayla Harrison Fulfills Destiny, Takes Title via Kimura Submission",
                        "https://cagesidepress.com/2025/06/08/kayla-harrison-fulfills-destiny-takes-title-via-kimura-submission",
                        "2025-06-08", "Eddie Law"),
    "lowkick_kh_cut": src("LowKick MMA", "Kayla Harrison Hospitalized for 'Peeing Blood' Before UFC 307 Due to Brutal Weight Cut",
                          "https://www.lowkickmma.com/kayla-harrison-hospitalized-peeing-blood/", "2024-10-08",
                          "Craig Pekios"),
    "lowkick_kh_spar": src("LowKick MMA", "Kayla Harrison sparring Amanda Nunes",
                           "https://www.lowkickmma.com/kayla-harrison-sparring-amanda-nunes/", "2025-04-22", "Craig Pekios"),
    "mmaj_nunes": src("Yahoo Sports (MMA Junkie)", "Amanda Nunes reveals surprising decision about comeback before UFC 334",
                      "https://sports.yahoo.com/articles/amanda-nunes-reveals-surprising-decision-184030083.html",
                      "2026-10-20", "Simon Samano"),
    "cage_aldana": src("Cageside Press", "UFC 289: Amanda Nunes Dominates Irene Aldana, Retires",
                       "https://cagesidepress.com/2023/06/11/ufc-289-amanda-nunes-irene-aldana/", "2023-06-11", "Val Dewar"),
    # ---- Borralho / Belgaroui
    "cage_rdr": src("Cageside Press", "UFC 326: Caio Borralho Bounces Back, Beats Reinier de Ridder",
                    "https://cagesidepress.com/2026/03/07/ufc-326-caio-borralho-bounces-back-beats-reinier-de-ridder/",
                    "2026-03-07", "Nick Holt"),
    "cage_imavov": src("Cageside Press", "UFC Paris: Nassourdine Imavov Looks Strong in Decision Win Over Caio Borralho",
                       "https://cagesidepress.com/2025/09/06/ufc-paris-nassourdine-imavov-looks-strong-in-decision-win-over-caio-borralho",
                       "2025-09-06", "Jay Anderson"),
    "lowkick_caio_rib": src("LowKick MMA", "Caio Borralho Details Scary Injury That Ended Planned UFC 330 Joe Pyfer Clash",
                            "https://www.lowkickmma.com/caio-borralho-details-scary-injury-that-ended-planned-ufc-330-joe-pyfer-clash/",
                            "2026-06-06", "Subham"),
    "bn_caio": src("Boxing News (citing Sherdog)", "Borralho Explains Accepting Risky Belgaroui Matchup",
                   "https://boxingnews.com/news/borralho-explains-belgaroui-matchup/", "2026-09-23"),
    "wiki_caio": src("Wikipedia", "Caio Borralho", "https://en.wikipedia.org/wiki/Caio_Borralho", "2026-11-03"),
    "sherdog_glover": src("Sherdog", "Glover Teixeira: 3-0 UFC finisher Yousri Belgaroui is evolving on ground",
                          "https://www.sherdog.com/news/news/Glover-Teixeira-30-UFC-finisher-Yousri-Belgaroui-is-evolving-on-ground-203276",
                          "2026-10-20", "Marcelo Alonso"),
    "ufc_belgaroui": src("UFC.com", "Yousri Belgaroui | Middleweight's New Boogeyman",
                         "https://www.ufc.com/news/yousri-belgaroui-middleweights-new-boogeyman-noche-ufc", "2026-09-09",
                         "E. Spencer Kyte"),
    "cage_santos": src("Cageside Press", "Noche UFC: Yousri Belgaroui Shuts Down Djorden Santos",
                       "https://cagesidepress.com/2026/09/12/noche-ufc-yousri-belgaroui-shuts-down-djorden-santos/",
                       "2026-09-12", "Patrick Danna"),
    "cage_abdulmalik": src("Cageside Press", "UFC Seattle: Yousri Belgaroui Pieces Up, Puts Away Mansur Abdul-Malik",
                           "https://cagesidepress.com/2026/03/28/ufc-seattle-yousri-belgaroui-pieces-up-puts-away-mansur-abdul-malik",
                           "2026-03-28", "Brett Cagle"),
    "cage_bekoev": src("Cageside Press", "Yousri Belgaroui Breaks Down Bekoev for Late Finish in Violent UFC Debut",
                       "https://cagesidepress.com/2025/10/18/yousri-belgaroui-breaks-down-bekoev-for-late-finish-in-violent-ufc-debut/",
                       "2025-10-18", "Shawn Bitter"),
}


def slug(name):
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


R = {}


def report(name, event, summary, how, patterns, concerns, keys, news, sources, depth):
    """event varies per fighter in this file (EVENT for UFC 334, EVENT_WCA for the Nov. 7 card): always pass it."""
    R[name] = {"name": name, "updated": UPDATED, "event": event, "summary": summary, "how_they_fight": how,
               "patterns": patterns, "concerns": concerns, "keys_to_beat": keys, "news": news,
               "sources": [SRC[k] for k in sources], "depth": depth}


def n(date, text, key):
    return {"date": date, "text": text, "source": SRC[key]["url"]}


# ---------------------------------------------------------------------------------------------------------------
report("Waldo Cortes-Acosta", EVENT_WCA,
       "A Dominican heavyweight (17-4, age 35) and former pro baseball pitcher who started boxing and MMA at 24. He went "
       "on a run of three straight knockouts (Delija, Gaziev, Lewis) between November 2025 and January 2026, then lost "
       "decisions to Alexander Volkov and Curtis Blaydes. He now headlines a five-round main event against Johnny Walker on "
       "about nine days' notice after Sean Brady pulled out of the original headliner. He has never been stopped.",
       {"Striking": "A boxer first (Wikipedia lists a 6-4 pro boxing record). He works a jab and short, fast combinations, "
                    "and calls himself a high-volume fighter (Cageside media day). Power is real: knockdowns against "
                    "Brzeski, Spann, Delija, Gaziev (two) and Lewis in our data. Against Lewis he hurt him with a knee to the "
                    "body, then dropped him with a short punch (Cageside). He likened the Lewis knockdown punch to a "
                    "baseball change-up.",
        "Grappling": "Mostly a striker. He has one submission win (2021) and a blue belt per Wikipedia, which also notes he "
                     "had no wrestling background. He can wrestle when he wants: he took Robelis Despaigne down 3 of 4 times "
                     "and held him for almost ten minutes (our data), and caught a Lewis kick for a takedown (Cageside).",
        "Defense": "Never stopped in 21 pro MMA fights. All four losses were decisions. Two of them came against wrestlers who "
                   "held him down: Marcos Rogerio de Lima (3 of 7 takedowns, about five minutes of control) and Blaydes, who "
                   "took him down in R1 and twice in R2 and took his back (Cageside). Volkov out-landed him 88 to 54 in "
                   "significant strikes, used his reach and low kicks, landed a head kick, and left damage around his eye.",
        "Pace & cardio": "Finishes come early. Ten stoppage wins: five in R1, four in R2, one in R3 (2022). His last three "
                         "UFC knockouts were R1, R1, R2. Seven wins went the full 15 minutes. He has never fought a "
                         "five-round bout, and this is one. Against Volkov he seemed to slow late in R2, then found a second "
                         "wind in R3 (Cageside).",
        "Fight IQ": "Calm, measured jab work when ahead. Against tall, rangy strikers (Volkov) he struggled to close distance; "
                    "against Blaydes he couldn't land much in R3 while chasing (Cageside). Active: five fights in 2025, "
                    "including a two-day-notice win over Gaziev (Wikipedia)."},
       ["Jab and fast combinations; looks for the knockout in R1-R2 (nine of ten stoppages came in R1-R2)",
        "Never finished; all four losses on the cards",
        "Loses to wrestlers who hold him down (de Lima, Blaydes) and to a longer striker who kept him at range (Volkov)",
        "Will catch kicks and take the fight down if it's offered"],
       ["First five-round fight",
        "Two straight losses; he was the favourite against Blaydes",
        "Facing a longer opponent: Walker has a listed 82-inch reach to his 78 (LowKick, Wikipedia)",
        "Short-notice camp for a main event"],
       ["Use range and kicks like Volkov did; make him reach",
        "Take him down and hold him there, as Blaydes and de Lima did",
        "Drag him into rounds 4-5, where he has never been"],
       [n("2026-10-29", "Booked against Johnny Walker as the new main event of the Nov. 7 card after Sean Brady withdrew injured "
                        "from his fight with Gabriel Bonfim (first reported by Laerte Viana).", "cage_v124_main"),
        n("2026-10-29", "SB Nation calls it a five-round main event and lists him as the No. 8 heavyweight.", "sbn_v124"),
        n("2026-09-12", "Lost a unanimous decision to Curtis Blaydes (29-28 x3) at Noche UFC; Blaydes won with takedowns and "
                        "back control. The crowd booed the low-action fight.", "cage_blaydes"),
        n("2026-05-09", "Lost a unanimous decision to Alexander Volkov at UFC 328 (30-27, 29-28, 29-28). He weighed 264 lbs.",
          "cage_volkov")],
       ["cage_v124_main", "sherdog_v124", "sbn_v124", "mmaj_v124", "wiki_wca", "cage_blaydes", "bjp_noche", "cage_volkov",
        "cage_wca_md", "cage_328_wi", "cage_lewis", "lowkick_parkin_prev"],
       "deep")

# ---------------------------------------------------------------------------------------------------------------
report("Johnny Walker", EVENT_WCA,
       "A tall, awkward Brazilian (23-10, 1 NC, age 34) who moved up to heavyweight this year after cutting hard to 205. His "
       "heavyweight debut went well: he knocked out Mick Parkin with clinch knees at 3:35 of R1 at UFC 332 and earned a "
       "bonus. Now he headlines against Waldo Cortes-Acosta on short notice, in a five-round fight, only his second at "
       "heavyweight. He is dangerous early and has been stopped six times.",
       {"Striking": "Long (6-foot-5, 82-inch reach per LowKick) with real power: 18 of his 23 wins are KO/TKO. Against Parkin "
                    "he chopped the lead leg with inside and outside kicks, went to the body, then landed an elbow, a jumping "
                    "knee and a second knee in the clinch to end it (Cageside). He said afterward that he doesn't train that "
                    "knee. Sherdog's Tom Feely wrote before UFC 332 that the wild aggression of his early UFC run has been "
                    "coached out of him and that he now tries to strike from range, which has left him looking frozen.",
        "Grappling": "BJJ brown belt (LowKick); three submission wins, all in R1 (most recently Ion Cutelaba, 2022). Submitted "
                     "only once, in 2015. His wrestling defense is the issue: Nikita Krylov took him down 3 of 8 times and held "
                     "him for over 11 minutes in 2020 (our data).",
        "Defense": "Chin and defense are the big question. Six KO/TKO losses: four in R1 (Henrique Silva Lopes 2016, Corey "
                   "Anderson, Jamahal Hill, Volkan Oezdemir) and two in R2 (Wagner Prado 2014, Magomed Ankalaev). Feely says he "
                   "gets knocked out when opponents press forward. He did take a clean right hand from Parkin well (Cageside), "
                   "but that is one heavyweight fight.",
        "Pace & cardio": "Front-loaded. Of his 21 stoppage wins, 18 came in R1, two in R2, one in R3 (2015). Only two wins went "
                         "the distance. He is 1-3 in scheduled five-rounders: a decision loss to Thiago Santos, R1 and R2 KO "
                         "losses to Hill and Ankalaev, and the R2 TKO of Zhang Mingyang in 2025. UFC.com framed the move up as a "
                         "way to compete without the big cut; he weighed 242 for Parkin, who came in at 265 (BJPenn.com).",
        "Fight IQ": "Inconsistent. The April split-decision loss to Dominick Reyes was a slow fight where neither man led "
                    "(Sherdog). After UFC 332 he asked for 40-year-old Marcin Tybura, saying he wanted more experience before "
                    "facing higher-ranked heavyweights (Sherdog). This booking skips that step."},
       ["Leg kicks and body work at range, then explodes in the clinch (knees, elbows)",
        "Early finisher: 18 of 21 stoppage wins in R1",
        "Stopped six times, four of them in R1",
        "Can be wrestled and held down (Krylov)",
        "Goes passive when he can't find the opening (Reyes)"],
       ["Durability against heavyweight punchers; Cortes-Acosta has dropped five UFC opponents",
        "Gives up about 20 lbs (he weighed 242 for UFC 332; Cortes-Acosta weighed 264 for UFC 328)",
        "Second heavyweight fight, first heavyweight five-rounder, on short notice",
        "1-3 in scheduled five-round fights"],
       ["Press him and make him fight going backward (Feely's key for Parkin)",
        "Stay out of the clinch along the fence, where he finished Parkin",
        "Take him down; he has struggled with wrestlers",
        "Survive the first round; his finishes almost all come early"],
       [n("2026-10-03", "Knocked out Mick Parkin with clinch knees at 3:35 of R1 at UFC 332 in his heavyweight debut and earned "
                        "a Performance of the Night bonus.", "cage_parkin"),
        n("2026-10-08", "Asked the UFC for Marcin Tybura in December, saying he didn't want to get ahead of himself.",
          "sherdog_tybura"),
        n("2026-10-30", "Reportedly booked to face Waldo Cortes-Acosta in a short-notice heavyweight main event on Nov. 7 after "
                        "Sean Brady withdrew injured nine days before the event.", "sherdog_v124"),
        n("2026-10-29", "SB Nation lists him at No. 12 at heavyweight and describes the bout as a five-round main event.",
          "sbn_v124"),
        n("2026-11-02", "Said he will not fight his half-brother Valter Walker in the UFC.", "sherdog_valter")],
       ["sherdog_332_prev", "ufc_332_prev", "cage_parkin", "bjp_332", "lowkick_parkin_prev", "sherdog_tybura", "sherdog_v124",
        "sbn_v124", "cage_v124_main", "mmaj_v124", "sherdog_valter"],
       "deep")

# ---------------------------------------------------------------------------------------------------------------
report("Ciryl Gane", EVENT,
       "The French heavyweight champion (14-2, 1 NC, age 36): a long, light-footed kickboxer who controls distance and "
       "wins most of his fights standing. He won the interim belt by stopping Alex Pereira in R2 at UFC Freedom 250 in June, "
       "and was promoted when Tom Aspinall vacated in September; Aspinall's eyes had been damaged by Gane's pokes at UFC 321. "
       "He opens as a solid favourite over unbeaten wrestler Josh Hokit. Both of his losses came on the mat.",
       {"Striking": "High-volume and accurate (about 61% significant accuracy in our numbers). Against Pereira he jabbed, "
                    "kicked the inside of the leg, dropped him with a jab early in R2 and swarmed for the finish at 1:27 "
                    "(Cageside). He out-landed Pereira 54 to 12. His coach Fernand Lopez says his game is creating space "
                    "between himself and the opponent (MMA Junkie).",
        "Grappling": "Three submission wins, all from his first five fights (2018-2019). He rarely wrestles offensively: 0 for 2 "
                     "on takedowns against Pereira.",
        "Defense": "Hard to hit standing (absorbs about 2.2 significant strikes a minute). The ground is the problem. Francis "
                   "Ngannou took him down 4 of 5 times and held him for over eight minutes in their five-rounder; Jon Jones took "
                   "him down twice and submitted him in R1 (2:04). In the 2024 Volkov rematch Volkov landed 3 of 4 takedowns and "
                   "out-controlled him (272 to 220 seconds) in a split decision. Jorge Masvidal pointed to both losses coming on "
                   "the ground (MMA Junkie).",
        "Pace & cardio": "Goes deep comfortably. Ten stoppage wins: three in R1, four in R2, three in R3. He is 4-2, 1 NC in "
                         "five-round fights, with five-round decision wins over Rozenstruik and Volkov, R3 stoppages of Lewis and "
                         "Tuivasa, the decision loss to Ngannou and the R1 loss to Jones.",
        "Fight IQ": "Patient and disciplined at range. Fouls are a running theme: the Aspinall eye pokes ended UFC 321 as a "
                    "no contest and led Aspinall to vacate, and Pereira says Gane hit him on the back of the head in the "
                    "finishing sequence. Dominick Cruz and T.J. Dillashaw argued the pokes weren't deliberate (MMA Junkie)."},
       ["Jab, inside leg kicks, footwork; wins at range",
        "Finishes hurt opponents quickly (Pereira) or wears them down late (Lewis, Tuivasa in R3)",
        "Both losses came from being taken down and controlled (Ngannou, Jones)",
        "Extended fingers and eye pokes have cost opponents and drawn scrutiny"],
       ["Takedown defense against a wrestler who lands about three takedowns per 15 minutes",
        "Age 36",
        "Referee attention on eye pokes after the Aspinall no contest"],
       ["Close distance and get to the body lock; don't trade at range",
        "Wrestle early and often; make him carry weight",
        "Keep hands up to defend extended fingers"],
       [n("2026-06-14", "Stopped Alex Pereira by R2 TKO (1:27) at UFC Freedom 250 to win the interim heavyweight title.",
          "cage_pereira"),
        n("2026-09-14", "Promoted to undisputed champion after Tom Aspinall vacated due to eye complications from Gane's illegal "
                        "pokes at UFC 321.", "wiki_334"),
        n("2026-10-29", "Opening line at BetOnline: Gane -243, Hokit +203.", "sherdog_334_odds"),
        n("2026-10-29", "Dominick Cruz and T.J. Dillashaw defended him against cheating claims over eye pokes and Pereira's "
                        "back-of-the-head complaint.", "mmaj_cruz")],
       ["wiki_334", "cage_334_card", "sherdog_334_odds", "cage_pereira", "mmaj_cruz", "mmaj_lopez", "mmaj_masvidal",
        "sherdog_jones"],
       "deep")

# ---------------------------------------------------------------------------------------------------------------
report("Josh Hokit", EVENT,
       "An unbeaten American heavyweight (10-0, 4-0 UFC, age 29) out of Jackson-Wink who came through the 2025 Contender "
       "Series. He wrestles, strikes in volume, and finishes with ground-and-pound. He beat Curtis Blaydes in a Fight of the "
       "Night brawl in April and stopped Derrick Lewis in June. Gane is a big step up in size and skill, and this is his first "
       "five-round fight.",
       {"Striking": "Very high volume: 177 significant strikes landed against Blaydes, which Gane's coach called a heavyweight "
                    "record (MMA Junkie). He rocked Blaydes with right hands in R1 and R2 but was hurt himself in R1 "
                    "(Cageside). Against Lewis he used a jab and punches to set up takedowns, then dropped him with a "
                    "combination off the fence.",
        "Grappling": "Wrestling is his base (about 3 takedowns per 15 minutes). Lewis: double-leg in R1, ground-and-pound that "
                     "cut him, a brief mount and an armbar attempt, then the R2 finish; about four minutes of control (our "
                     "data). Denzel Freeman: almost four minutes of control and 37 strikes to none. Contender Series: 6 of 13 "
                     "takedowns. Fernand Lopez describes him as a wrestler who strikes, changes levels, and goes back to "
                     "wrestling when the striking isn't working.",
        "Defense": "Absorbs a lot when he trades: Blaydes landed 174 significant strikes on him and took him down twice in R1 "
                   "(Cageside; our data). Never beaten, never stopped. Reach is a problem here: listed at 185 cm against "
                   "Gane's 206 cm in our data.",
        "Pace & cardio": "Nine stoppages: six in R1, two in R2, one in R3. Went 15 hard minutes with Blaydes and kept "
                         "throwing in R3. Has never fought past three rounds.",
        "Fight IQ": "Loud and provocative outside the cage (diss tracks, run-ins with Bruce Buffer and Alex Pereira). Inside, he "
                    "has been willing to brawl when he could wrestle (Blaydes). Lopez expects him to wrestle, but not "
                    "right away, and expects a lot of exchanges on the feet."},
       ["Jab and punches to set up level changes",
        "Ground-and-pound finishes (Lewis, Freeman, Contender Series)",
        "Huge striking volume, but takes a lot back",
        "Six of nine stoppages in R1"],
       ["Gives up about 21 cm of reach to Gane",
        "Has never gone past 15 minutes",
        "Defensive striking; was hurt by Blaydes in R1",
        "Has not faced a striker of Gane's level at range"],
       ["Keep him at the end of the jab and kicks; punish his entries",
        "Stuff the first takedowns; he goes back to wrestling when the striking isn't working",
        "Take him into rounds 4-5"],
       [n("2026-09-19", "Booked for the heavyweight title against Ciryl Gane in the UFC 334 main event at Madison Square Garden.",
          "cage_334_card"),
        n("2026-10-19", "Gane's head coach Fernand Lopez compared him to Cain Velasquez.", "mmaj_lopez"),
        n("2026-10-13", "Jon Jones, who trained at Jackson-Wink, said Hokit 'very well could win'.", "sherdog_jones"),
        n("2026-11-02", "Jorge Masvidal picked him to take Gane down and break him on the mat. MMA Junkie's page also links "
                        "reports that he sparred after being pepper-sprayed to prepare for eye pokes.", "mmaj_masvidal"),
        n("2026-10-29", "Opens as a +203 underdog at BetOnline.", "sherdog_334_odds")],
       ["cage_334_card", "wiki_334", "sherdog_334_odds", "mmaj_lopez", "mmaj_masvidal", "sherdog_jones", "cage_hokit_blaydes",
        "cage_hokit_lewis"],
       "deep")

# ---------------------------------------------------------------------------------------------------------------
report("Kayla Harrison", EVENT,
       "The UFC women's bantamweight champion (19-1, age 36): two-time Olympic judo gold medallist and two-time PFL "
       "champion. She won the title by kimura over Julianna Peña in June 2025 and has not fought since. Neck surgery for "
       "herniated discs forced her out of the January date with Amanda Nunes. She says she feels 'awesome' now. The cut to "
       "135 is a known strain on her.",
       {"Striking": "Functional, used mainly to get to the clinch. Six KO/TKO wins, all in the PFL or Invicta; four came in R1. "
                    "Opponents have landed little on her in the UFC: Holm 2, Vieira 24, Peña 9 significant strikes (our data).",
        "Grappling": "Elite. Body-lock takedowns into top control and submissions. Against Peña she took her down with a body "
                     "lock in each round and finished with a kimura from side control at 4:55 of R2 (Cageside). Eight "
                     "submission wins. In three UFC fights she held top position for about 5, 8 and 6 minutes.",
        "Defense": "Her one loss was a five-round decision to Larissa Pacheco in 2022. She has never been finished.",
        "Pace & cardio": "Fourteen stoppages: nine in R1, four in R2, one in R3. She is 1-1 in five-round fights, both against "
                         "Pacheco. The weight cut is a recurring concern: she was hospitalised the week before UFC 307 after "
                         "seeing blood in her urine, and said she is 'just not built to weigh 135 pounds' (LowKick).",
        "Fight IQ": "Conservative and control-first. After Vieira she said it 'definitely wasn't my best night'. She has said "
                    "she could walk away from the sport now and be at peace (Uncrowned)."},
       ["Body lock, trip, top control, submission",
        "Front-loaded finisher: 13 of 14 stoppages in R1-R2",
        "Wins rounds through control time even when she can't finish (Vieira)"],
       ["About 17 months out of the cage",
        "Neck surgery: five herniated discs, eight weeks in a neck brace, and two discs still to address after her career "
        "(Uncrowned)",
        "Hard cut to 135",
        "Only one five-round win, and she lost the other"],
       ["Defend the body lock and keep the fight at range",
        "Make her work late in a five-round fight",
        "Punish her entries with counters"],
       [n("2026-10-13", "Says she questioned whether she would feel like herself again after neck surgery, but 'I'm back' and "
                        "feels 'awesome'.", "sherdog_kh_neck"),
        n("2026-10-16", "Told Uncrowned she probably would not have come back if Nunes had not returned from retirement.",
          "unc_kh_year"),
        n("2026-10-29", "Joselyne Edwards is the backup for the title fight.", "cage_334_backup"),
        n("2026-10-29", "BetOnline: Harrison -190, Nunes +161.", "sherdog_334_odds")],
       ["wiki_334", "cage_334_card", "cage_334_backup", "sherdog_334_odds", "sherdog_kh_neck", "unc_kh_year", "cage_kh_pena",
        "lowkick_kh_cut", "lowkick_kh_spar"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Amanda Nunes", EVENT,
       "The former two-division UFC champion (23-5, age 38) returns from retirement for her first fight since June 2023, "
       "when she beat Irene Aldana and laid her gloves down. She is a former American Top Team teammate of Kayla Harrison. "
       "Powerful striker, strong top game, proven over five rounds. She is an underdog for the first time since she knocked "
       "out Cris Cyborg in 2018.",
       {"Striking": "Heavy hands and kicks. Thirteen KO/TKO wins, including 51 seconds against Cyborg and 48 against Rousey. "
                    "Against Aldana she used her jab and kicks, staggered her with an overhand right and a knee in R3, and "
                    "landed a big elbow in R4 (Cageside).",
        "Grappling": "Strong wrestler and top player. At least six takedowns against Aldana, including a rear body lock in R3 and "
                     "an early R5 takedown into ground strikes and a mount (Cageside). In the Peña rematch she landed 6 of 8 "
                     "takedowns with almost 12 minutes of control (our data). Four submission wins.",
        "Defense": "Can be hurt: Aldana caught her with a counter right at the end of R1 (Cageside). Peña out-landed her 79 to "
                   "46 and submitted her in R2 in 2021. Other losses: a 2014 R3 TKO to Cat Zingano, a 2011 R2 TKO to "
                   "Alexis Davis, a 2013 decision and a 2008 submission in her debut.",
        "Pace & cardio": "Seventeen stoppages: fourteen in R1, two in R2, one in R5 (Pennington). Six five-round decision or "
                         "late wins and no losses in fights that went past three rounds. Against Aldana she was still "
                         "landing takedowns and ground strikes in R5.",
        "Fight IQ": "Mixes striking and wrestling well; against Aldana all three judges gave her every round. Comes in after more than three "
                    "years out. Says she plans to defend the belt if she wins (MMA Junkie)."},
       ["Fast starter with knockout power: 14 of 17 stoppages in R1",
        "Wrestles to top position and grinds in title fights",
        "Gets stronger late in five-round fights"],
       ["More than three years out of competition; age 38",
        "Has to stop Harrison's body lock and grappling",
        "Has been hurt and lost to pressure (Peña 2021)"],
       ["Clinch and take her down early, before the power lands",
        "Test her cardio after the layoff",
        "Avoid open exchanges in R1"],
       [n("2026-10-20", "Says she will defend the belt if she wins: 'And then we're going to see'.", "mmaj_nunes"),
        n("2026-10-29", "Opens as a +161 underdog at BetOnline, her first time as an underdog since UFC 232 in 2018.",
          "sherdog_334_odds"),
        n("2026-10-29", "Joselyne Edwards is the backup for the title fight.", "cage_334_backup")],
       ["wiki_334", "cage_334_card", "cage_334_backup", "sherdog_334_odds", "mmaj_nunes", "cage_aldana", "unc_kh_year",
        "lowkick_kh_spar"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Caio Borralho", EVENT,
       "A Brazilian middleweight (18-2, 1 NC, age 34) from Fighting Nerds, 8-1 in the UFC. He bounced back from his first "
       "UFC loss (a five-round decision to Nassourdine Imavov) with a clean decision over Reinier de Ridder in March. Then a "
       "rib injury that needed surgery cancelled his August fight with Joe Pyfer. He takes on unranked Yousri Belgaroui to "
       "stay active, and has said the fight has more downside than upside for him.",
       {"Striking": "Measured and accurate (about 55% significant accuracy, 66% defence). Against de Ridder his straights and "
                    "hooks dropped him to a knee in R1 and wobbled him again in R3; he also worked the lead leg (Cageside). "
                    "Against Imavov he was out-landed 81 to 66 and outpaced in the exchanges.",
        "Grappling": "Black belt in BJJ and Muay Thai, brown in judo (Wikipedia). Strong top game early in his UFC run: about "
                     "ten minutes of control against both Omargadzhiev and Petrosyan. Against de Ridder he took him down in "
                     "R3 and threatened a triangle. But his shots lacked explosiveness against Imavov, who stuffed all five "
                     "(Cageside; our data).",
        "Defense": "Never stopped in 21 pro fights. De Ridder cut him with a straight in R1 and landed 2 of 8 takedowns. Imavov "
                   "clipped him and left him reeling in R3 in Paris.",
        "Pace & cardio": "A decision fighter in the UFC: only two finishes in eight UFC wins (Oleksiejczuk sub R2, Craig KO R2). "
                         "Nine stoppages overall: six in R1, two in R2, one in R3. He beat Jared Cannonier over five rounds, "
                         "but tired in R4 against Imavov (Cageside).",
        "Fight IQ": "Patient, mixes striking and grappling, wins rounds. Has said he wants to stay active and prove he is one "
                    "of the best in the world against whoever he's given (Sherdog, via Boxing News)."},
       ["Measured striking with straight punches and hooks",
        "Mixes in takedowns and top control when the opening is there",
        "Wins on the cards: six of eight UFC wins went to decision",
        "Lost when he couldn't get the takedown and was out-struck (Imavov)"],
       ["Rib surgery; about eight months out since March",
        "Gives up height and reach to a 196-cm kickboxer",
        "Takedowns didn't work against a strong defensive opponent (Imavov 0 for 5)"],
       ["Keep him on the end of long strikes; don't let him set his feet",
        "Stuff the first takedowns and he struggles to change plans",
        "Out-work him on the feet like Imavov did"],
       [n("2026-06-06", "Said the rib didn't heal and was displaced, and that it could have punctured his lung; surgery cancelled "
                        "his UFC 330 fight with Joe Pyfer.", "lowkick_caio_rib"),
        n("2026-09-23", "Told Sherdog he took the Belgaroui fight to stay active after almost six months out (via Boxing News).",
          "bn_caio"),
        n("2026-10-29", "Closest line on the main card: Borralho -120, Belgaroui +103 (BetOnline).", "sherdog_334_odds")],
       ["wiki_334", "cage_334_card", "sherdog_334_odds", "cage_rdr", "cage_imavov", "lowkick_caio_rib", "bn_caio", "wiki_caio",
        "sherdog_glover"],
       "deep")

# ---------------------------------------------------------------------------------------------------------------
report("Yousri Belgaroui", EVENT,
       "A tall Dutch-Tunisian middleweight kickboxer (11-3, 3-0 UFC, age 34) and former Glory title challenger, now training "
       "with Glover Teixeira and his former rival Alex Pereira. He has stopped all three UFC opponents, two of them as an "
       "underdog. This is a big step up: Borralho is his first ranked opponent. He went to the Contender Series twice: "
       "he lost in 2023, and won in 2024 but was not offered a contract.",
       {"Striking": "Long and composed (196 cm, 201-cm reach in our data). Jab, heavy leg and calf kicks, body work and knees. "
                    "Against Djorden Santos he rocked him with a head kick and jab, then dropped him with two overhand rights "
                    "on the fence (R1, 4:25). Against Abdul-Malik he picked him apart from range, hurt him late in R2, and "
                    "finished him with a clinch knee in R3 (Cageside). Nine of his 11 wins are KO/TKO.",
        "Grappling": "Mostly defensive. Teixeira says he loves training on the ground and is getting more confident in his "
                     "grappling (Sherdog). He hasn't shown much offensive wrestling.",
        "Defense": "Never stopped. His three losses were all decisions; on the 2023 Contender Series Marco Tulio held him for "
                   "over six minutes. UFC opponents can take him down: Bekoev 4 of 8, Abdul-Malik 3 of 8, including back "
                   "control. But he got back up each time and made them pay with elbows and knees (Cageside).",
        "Pace & cardio": "Gets better as fights go on. Nine stoppages: four in R1, two in R2, three in R3, and his first two UFC "
                         "wins were both R3 finishes after he wore opponents down. He won a five-round decision on the regional "
                         "scene (2024).",
        "Fight IQ": "Calm under pressure, a good sense of distance (Teixeira). Has said ranked opponents turned him down."},
       ["Range kickboxing with leg kicks and a jab",
        "Breaks opponents down and finishes late (two straight R3 stoppages before the R1 win over Santos)",
        "Gets taken down, gets back up",
        "Knees in the clinch"],
       ["First ranked opponent, and a much better grappler than he has faced",
        "Gives up control time to wrestlers",
        "Limited offensive grappling"],
       ["Take him down early and keep him there; don't just get him down for a few seconds",
        "Close the distance behind feints; don't stand at the end of his kicks",
        "Avoid the clinch knee on the way out"],
       [n("2026-09-12", "Stopped Djorden Santos (a replacement for Kelvin Gastelum) by TKO at 4:25 of R1 at Noche UFC.",
          "cage_santos"),
        n("2026-09-09", "Told UFC.com he wanted to fight at Madison Square Garden in November against a ranked opponent.",
          "ufc_belgaroui"),
        n("2026-10-20", "Glover Teixeira said he often stays after sessions for extra wrestling and jiu-jitsu.", "sherdog_glover"),
        n("2026-10-29", "Opens as a slight underdog: Borralho -120, Belgaroui +103.", "sherdog_334_odds")],
       ["wiki_334", "cage_334_card", "sherdog_334_odds", "sherdog_glover", "ufc_belgaroui", "cage_santos", "cage_abdulmalik",
        "cage_bekoev"],
       "deep")


out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
