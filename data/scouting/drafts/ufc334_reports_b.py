"""Scouting reports (batch B) for UFC 334: Gane vs. Hokit (Madison Square Garden, New York, 2026-11-14),
written 2026-11-03.

Fight-week previews aren't out yet. These draw on recent-fight recaps, booking news, interviews and our verified
records; round/method counts come from data/verified/fights.csv. The fight-week run should refresh them with
previews and weigh-in news.

Fighters: Uroš Medić, Kevin Holland, Bilal Hasan, Luis Gurule, Stephen Thompson, Charles Radtke, Drew Dober,
Chris Duncan, Jim Miller.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATED = "2026-11-03T18:00:00+00:00"
EVENT = "UFC 334: Gane vs. Hokit"


def src(outlet, title, url, date, author=""):
    return {"outlet": outlet, "author": author, "title": title, "url": url, "date": date}


SRC = {
    # card / booking
    "wiki_event": src("Wikipedia", "UFC 334", "https://en.wikipedia.org/wiki/UFC_334", "2026-11-03"),
    "forbes_card": src("Yahoo Sports (Forbes)", "UFC 334 Card Announced With 2 Title Fights And A Retirement Bout",
                       "https://sports.yahoo.com/articles/ufc-334-card-announced-2-023127330.html", "2026-09-20",
                       "Brian Mazique"),
    "nyp_card": src("Yahoo Sports (New York Post)",
                    "UFC 334 brings Ciryl Gane vs. Josh Hokit, Kayla Harrison vs. Amanda Nunes title fights to MSG",
                    "https://sports.yahoo.com/articles/ufc-334-brings-ciryl-gane-025322315.html", "2026-09-20",
                    "Scott Fontana"),
    # Medic
    "unc_medic_islam": src("Yahoo Sports (Sherdog)", "Uros Medic is 'tired' of watching Islam Makhachev win",
                           "https://sports.yahoo.com/articles/uros-medic-tired-watching-islam-024346455.html", "2026-11-03",
                           "Sayan Nag"),
    "cage_edm_losers": src("Cageside Press", "What's Next: UFC Edmonton Losers",
                           "https://cagesidepress.com/2026/10/19/whats-next-ufc-edmonton-losers-2/", "2026-10-19"),
    "lowkick_belgrade": src("LowKick MMA", "UFC Serbia: Matchmaking for All of Saturday's Winners",
                            "https://www.lowkickmma.com/matchmaking-for-all-of-saturdays-winners/", "2026-08-04"),
    "cage_belgrade_win": src("Cageside Press", "What's Next: UFC Belgrade Winners",
                             "https://cagesidepress.com/2026/08/04/whats-next-ufc-belgrade-winners/", "2026-08-04"),
    "bjp_belgrade": src("BJPenn.com", "UFC Belgrade: 'Medić vs. Rodriguez' Live Results and Highlights",
                        "https://www.bjpenn.com/mma-news/ufc-belgrade/ufc-belgrade-medic-vs-rodriguez-live-results-and-highlights/",
                        "2026-08-01"),
    "cage_houston_win": src("Cageside Press", "What's Next: UFC Houston Winners",
                            "https://cagesidepress.com/2026/02/23/whats-next-ufc-houston-winners/", "2026-02-23"),
    "cage_houston_los": src("Cageside Press", "What's Next: UFC Houston Losers",
                            "https://cagesidepress.com/2026/02/23/whats-next-ufc-houston-losers/", "2026-02-23"),
    # Holland
    "sherdog_smith_scared": src("Sherdog", "Jacobe Smith says Kevin Holland is 'scared' after UFC Vegas 123 win",
                                "https://www.sherdog.com/news/news/Jacobe-Smith-says-Kevin-Holland-is-scared-after-UFC-Vegas-123-win-203441",
                                "2026-11-01", "Sourav Chakraborty"),
    "sherdog_smith_alter": src("Sherdog", "Jacobe Smith predicts altercation with Kevin Holland outside UFC cage",
                               "https://www.sherdog.com/news/news/Jacobe-Smith-predicts-altercation-with-Kevin-Holland-outside-UFC-cage-203406",
                               "2026-10-29", "Sayan Nag"),
    "lowkick_holland_goal": src("LowKick MMA", "Kevin Holland sets a goal for himself for the remainder of his UFC career",
                                "https://www.lowkickmma.com/kevin-holland-sets-goal-ufc-career/", "2026-07-10", "Ian Shutts"),
    "cage_holland_brown": src("Cageside Press", "Kevin Holland Takes Decision Win After Fun Scrap With Brown",
                              "https://cagesidepress.com/2026/04/11/kevin-holland-takes-decision-win-after-fun-scrap-with-brown/",
                              "2026-04-11", "Eddie Law"),
    "sherdog_327_prev": src("Sherdog", "Preview: UFC 327 prelims - Brown vs. Holland",
                            "https://www.sherdog.com/news/articles/2/Preview-UFC-327-prelims-200764", "2026-04-08",
                            "Tom Feely"),
    # Hasan
    "unc_hasan": src("Yahoo Sports (Sherdog)", "Bilal Hasan wanted to take it slow; UFC put him on a 'rocket ship'",
                     "https://sports.yahoo.com/articles/bilal-hasan-wanted-slow-ufc-035105643.html", "2026-10-21",
                     "Sayan Nag"),
    "cage_hasan_rojas": src("Cageside Press", "UFC Shanghai: Bilal Hasan Arrives in Style, KOs Nilson Rojas",
                            "https://cagesidepress.com/2026/08/29/ufc-shanghai-bilal-hasan-arrives-in-style-kos-nilson-rojas/",
                            "2026-08-29"),
    "cage_dwcs": src("Cageside Press", "Dana White's Contender Series Season 10, Week 1 Results",
                     "https://cagesidepress.com/2026/08/11/dana-whites-contender-series-season-10-week-1-results/",
                     "2026-08-11"),
    "cage_dwcs_wi": src("Cageside Press", "Dana White's Contender Series Season 10, Week 1 Weigh-In Results",
                        "https://cagesidepress.com/2026/08/10/dana-whites-contender-series-season-10-week-1-weigh-in-results/",
                        "2026-08-10"),
    "ufc_hasan_rise": src("UFC.com", "Fighters on the Rise | UFC Shanghai",
                          "https://www.ufc.com/news/fighters-on-the-rise-ufc-shanghai-bilal-hasan-namsrai-batbayar-rei-tsuruya",
                          "2026-08-24", "E. Spencer Kyte"),
    "ufc_hasan_dwcs": src("UFC.com", "Bilal Hasan: Here to impress and enjoy the journey along the way",
                          "https://www.ufc.com/news/bilal-hasan-here-impress-and-enjoy-journey-along-way-dwcs",
                          "2026-08-21", "Zac Pacleb"),
    "cage_shanghai_win": src("Cageside Press", "What's Next: UFC Shanghai Winners",
                             "https://cagesidepress.com/2026/08/31/whats-next-ufc-shanghai-winners-2/", "2026-08-31"),
    # Gurule
    "cage_shanghai_los": src("Cageside Press", "What's Next: UFC Shanghai Losers",
                             "https://cagesidepress.com/2026/08/31/whats-next-ufc-shanghai-losers-2/", "2026-08-31"),
    "cage_coria": src("Cageside Press", "Alden Coria Improves to 2-0 in UFC With Win Over Luis Gurule",
                      "https://cagesidepress.com/2026/02/21/alden-coria-improves-to-2-0-in-ufc-with-win-over-luis-gurule/",
                      "2026-02-21", "Jay Anderson"),
    "cage_barez": src("Cageside Press", "Luis Gurule Overwhelms Barez with Pressure, Earns Clear Decision Win",
                      "https://cagesidepress.com/2026/05/16/luis-gurule-overwhelms-barez-with-pressure-earns-clear-decision-win/",
                      "2026-05-16", "Eddie Law"),
    "cage_tsuruya": src("Cageside Press", "UFC Macau: Rei Tsuruya Returns, Subs Luis Gurule",
                        "https://cagesidepress.com/2026/05/30/ufc-macau-rei-tsuruya-returns-subs-luis-gurule/",
                        "2026-05-30", "Nick Holt"),
    "bjp_noche3": src("BJPenn.com", "Noche UFC 3: 'Lopes vs. Silva' Live Results and Highlights",
                      "https://www.bjpenn.com/mma-news/noche-ufc/noche-ufc-3-lopes-vs-silva-live-results-and-highlights/",
                      "2025-09-13"),
    # Thompson
    "sherdog_wb_radtke": src("Sherdog", "Stephen Thompson explains why he chose Charles Radtke for final UFC fight",
                             "https://www.sherdog.com/news/news/Stephen-Thompson-explains-why-he-chose-Charles-Radtke-for-final-UFC-fight-203029",
                             "2026-10-01", "Sayan Nag"),
    "cage_bonfim": src("Cageside Press", "Gabriel Bonfim Battles With Thompson, Grinds Out Split Win",
                       "https://cagesidepress.com/2025/07/12/gabriel-bonfim-battles-with-thompson-grinds-out-split-win/",
                       "2025-07-12", "Eddie Law"),
    "lowkick_wb_shin": src("LowKick MMA", "Stephen Thompson Provides Update On Nasty Leg Injury From UFC Nashville",
                           "https://www.lowkickmma.com/stephen-thompson-nasty-leg-injury/", "2025-07-14", "William Goodson"),
    "cage_nash_los": src("Cageside Press", "What's Next: UFC Nashville Losers",
                         "https://cagesidepress.com/2025/07/14/whats-next-ufc-nashville-losers-2/", "2025-07-14"),
    "bjp_edmonton": src("BJPenn.com", "UFC Edmonton: 'Buckley vs. Malott' Live Results and Highlights",
                        "https://www.bjpenn.com/mma-news/ufc-edmonton/ufc-edmonton-buckley-vs-malott-live-results-and-highlights/",
                        "2026-10-17"),
    # Radtke
    "cage_radtke_prado": src("Cageside Press",
                             "Charles Radtke Survives Eye Poke, Choke, Claims Victory Over Francisco Prado at UFC 327",
                             "https://cagesidepress.com/2026/04/11/charles-radtke-survives-eye-poke-choke-claims-victory-over-francisco-prado-at-ufc-327/",
                             "2026-04-11", "Brett Cagle"),
    "cage_radtke_quote": src("Cageside Press",
                             "Charles Radtke Outlasts Francisco Prado, Says \"I'm About That Life\" After Gritty Win",
                             "https://cagesidepress.com/2026/04/13/charles-radtke-outlasts-francisco-prado-says-im-about-that-life-after-gritty-win/",
                             "2026-04-13", "Patrick Danna, Eddie Law"),
    "lowkick_radtke_frunza": src("LowKick MMA", "Charles Radtke Dominates Daniel Frunza, Locks In Third-Round RNC - UFC Vegas 110 Highlights",
                                 "https://www.lowkickmma.com/charles-radtke-vs-daniel-frunza-highlights/", "2025-11-01",
                                 "Craig Pekios"),
    "cage_vancouver_win": src("Cageside Press", "What's Next: UFC Vancouver Winners",
                              "https://cagesidepress.com/2025/10/20/whats-next-ufc-vancouver-winners/", "2025-10-20"),
    # Dober
    "sherdog_dober_crawford": src("Sherdog", "Terence Crawford's advice helped Drew Dober find the finish at UFC 277",
                                  "https://www.sherdog.com/news/news/Terence-Crawfords-advice-helped-Drew-Dober-find-the-finish-at-UFC-277-203420",
                                  "2026-10-30", "Sayan Nag"),
    "cage_dober_betting": src("Cageside Press", "Drew Dober Reacts to Betting Concerns with UFC 326 Fight",
                              "https://cagesidepress.com/2026/03/08/drew-dober-ufc-326-betting/", "2026-03-08",
                              "Gabriel Gonzalez"),
    "cage_326_los": src("Cageside Press", "What's Next: UFC 326 Losers",
                        "https://cagesidepress.com/2026/03/09/whats-next-ufc-326-losers/", "2026-03-09"),
    "cage_baku_card": src("Cageside Press", "Fiziev vs. Torres Headlines UFC Baku",
                          "https://cagesidepress.com/2026/05/05/fiziev-vs-torres-headlines-ufc-baku/", "2026-05-05"),
    # Duncan
    "sherdog_duncan": src("Sherdog", "Renato 'Moicano' submits Chris Duncan in UFC Vegas 115 headliner",
                          "https://www.sherdog.com/news/news/Renato-Moicano-submits-Chris-Duncan-in-UFC-Vegas-115-headliner-200716",
                          "2026-04-04", "Tristen Critchfield"),
    "sherdog_duncan_prev": src("Sherdog", "Preview: UFC Vegas 115 'Moicano vs. Duncan'",
                               "https://www.sherdog.com/news/articles/1/Preview-UFC-Vegas-115-Moicano-vs-Duncan-200695",
                               "2026-04-01", "Ben Duffy"),
    "bjp_duncan_next": src("BJPenn.com", "What's next for Renato Moicano and Chris Duncan after UFC Vegas 115?",
                           "https://www.bjpenn.com/mma-news/renato-moicano/whats-next-for-renato-moicano-and-chris-duncan-after-ufc-vegas-115/",
                           "2026-04-06"),
    "bjp_323": src("BJPenn.com", "UFC 323: 'Dvalishvili vs. Yan 2' Live Results and Highlights",
                   "https://www.bjpenn.com/mma-news/ufc-323/ufc-323-dvalishvili-vs-yan-2-live-results-and-highlights/",
                   "2025-12-06"),
    "lowkick_duncan_odds": src("LowKick MMA", "UFC Vegas 115 Odds: Why Chris Duncan Opens as Favorite Over Renato Moicano",
                               "https://www.lowkickmma.com/ufc-vegas-115-odds-why-chris-duncan-opens-as-favorite-over-renato-moicano/",
                               "2026-03-30"),
    # Miller
    "cage_miller_gordon": src("Cageside Press", "Jim Miller Does It Again, Submits Jared Gordon With Guillotine",
                              "https://cagesidepress.com/2026/05/09/jim-miller-does-it-again-submits-jared-gordon-with-guillotine/",
                              "2026-05-09", "Eddie Law"),
    "nyp_miller": src("Yahoo Sports (New York Post)",
                      "New Jersey's Jim Miller wins UFC 328 Hudson River battle following son's 'really difficult' cancer battle",
                      "https://sports.yahoo.com/articles/jersey-jim-miller-wins-ufc-003638970.html", "2026-05-10",
                      "Scott Fontana"),
    "cage_328_bonus": src("Cageside Press", "Van vs. Taira Earns FOTN, Miller Cashes In at UFC 328",
                          "https://cagesidepress.com/2026/05/10/van-vs-taira-earns-fotn-miller-cashes-in-at-ufc-328/",
                          "2026-05-10"),
    "lowkick_seattle": src("LowKick MMA", "UFC Seattle Power Rankings: Rating The Night's Big Winners At Climate Pledge Arena",
                           "https://www.lowkickmma.com/ufc-seattle-power-rankings-rating-the-nights-big-winners-at-climate-pledge-arena/",
                           "2026-03-31"),
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
report("Uroš Medić",
       "A Serbian welterweight finisher (14-3; 8-3 UFC) on a four-fight run of first-round stoppages. He headlined the UFC's "
       "first card in Belgrade in August and stopped Daniel Rodriguez in 30 seconds. Every one of his 14 wins is a stoppage, and "
       "he has never been to the judges. Cageside lists him at No. 9 and Holland at No. 14.",
       {"Striking": "Heavy, accurate power punching: about 4.6 significant strikes a minute at 58%, and 2.7 knockdowns per 15 "
                    "minutes in our data. He flattened Geoff Neal with a left hook in 79 seconds (Cageside) and finished Rodriguez "
                    "with a soccer kick to the body and punches at 0:30 of R1 (BJPenn.com). Twelve of his 14 wins are KO/TKO.",
        "Grappling": "Rarely used on offense: about 0.8 takedowns per 15 minutes and a 9% control share. His two submission wins "
                     "both came on the Alaska regional scene in 2018, in R1.",
        "Defense": "The open question. Two of his three losses are submissions: Jalin Turner (R1, 2021) and Myktybek Orolbai "
                   "(neck crank, R2, 2023; Cageside). Orolbai landed 7 of 10 takedowns and held him down for about 7.5 minutes in "
                   "our data. His third loss was a 31-second knockout by Punahele Soriano in January 2025. Takedown defense is about "
                   "59%. He has also been knocked down in three of his last eight UFC fights (Semelsberger, Soriano, Urbina).",
        "Pace & cardio": "Almost entirely a first-round fighter. Of his 14 wins, 11 came in R1, two in R2 and one in R3 (Matthew "
                         "Semelsberger, 2:36 of R3, 2023). His losses came in R1 (two) and R2 (one). He has never gone to a decision "
                         "and has never fought 15 minutes. Cageside noted in February that he had only got out of the first round four "
                         "times in his career. His last four fights all ended inside 90 seconds (LowKick), so his late-round "
                         "conditioning at UFC level is unknown.",
        "Fight IQ": "Aggressive from the opening bell. Has repeatedly called for Leon Edwards (LowKick). Outspoken: this week he said "
                    "he is tired of watching Islam Makhachev win and that the champion should retire if he is considering it (Sherdog)."},
       ["Fast starter: 11 of 14 wins in R1, the last four all inside 90 seconds",
        "Power punches; 12 KO/TKO wins",
        "Never been to a decision",
        "Losses: submitted by Turner and Orolbai (who held him down), and a fast KO by Soriano"],
       ["Holland is much longer: our data lists Holland's reach at about 206 cm against Medić's 180 cm",
        "Submission defense against a fighter with nine career submission wins",
        "No evidence of how he fights in rounds two and three against a durable opponent"],
       ["Survive the first round: don't trade with him early",
        "Use length and kicks to keep him at range",
        "Take him down or clinch and attack the neck; two of his three losses are submissions",
        "Drag him into the second half of the fight"],
       [n("2026-11-03", "Said on a podcast that he is tired of watching Islam Makhachev win and that Makhachev should retire if he "
                        "is thinking about it.", "unc_medic_islam"),
        n("2026-10-19", "Cageside lists the bout as (#9) Medić vs. (#14) Holland.", "cage_edm_losers"),
        n("2026-08-01", "Headlined UFC Belgrade and stopped Daniel Rodriguez by TKO (soccer kick to the body and punches) at 0:30 of R1.",
          "bjp_belgrade"),
        n("2026-09-20", "Booked against Kevin Holland on the UFC 334 main card at Madison Square Garden.", "nyp_card")],
       ["unc_medic_islam", "cage_edm_losers", "lowkick_belgrade", "cage_belgrade_win", "bjp_belgrade", "cage_houston_win",
        "cage_houston_los", "forbes_card", "nyp_card", "wiki_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Kevin Holland",
       "A long, talkative welterweight veteran (29-15, 1 NC; 16-12, 1 NC in the UFC) from Phalanx MMA Academy. He beat Randy Brown "
       "by decision in April to end a two-fight skid, then withdrew from two bookings against Jacobe Smith (July and October) "
       "because of injuries, per Sherdog. This will be his first fight in seven months. He is dangerous everywhere but has been "
       "out-wrestled and out-grappled by top opponents.",
       {"Striking": "Rangy kickboxer: about 4.5 significant strikes a minute at 51%, absorbing 3.1. Against Brown his calf kicks "
                    "damaged the lead leg and a left hand dropped Brown in R1, though Brown buckled him with a left hook and cut him "
                    "(Cageside). Sherdog's Tom Feely wrote in April that at welterweight he has leaned on his size to hunt knockouts, "
                    "with 'less flashes of his prior technical craft'. Fourteen KO/TKO wins.",
        "Grappling": "A real submission threat: nine submission wins, including Vicente Luque (R2, 2025), Michal Oleksiejczuk (R1, "
                     "2024) and Michael Chiesa (R1, 2023). He locked an anaconda choke on Brown in R2 and threatened guillotines "
                     "(Cageside). Rarely shoots himself (about 0.8 takedowns per 15).",
        "Defense": "Hard to knock out: only two KO/TKO losses, both against top opposition (Stephen Thompson after R4 in 2022; "
                   "Roman Dolidze at the end of R1 in 2024). The hole is being held down. Derek Brunson and Marvin Vettori controlled "
                   "him for about 17 and 20 minutes in five-round fights in 2021, Khamzat Chimaev and Reinier de Ridder submitted him "
                   "in R1, and Gunnar Nelson held him for over nine minutes in a fight Holland still won. Feely notes takedown defense "
                   "has been a recurring problem.",
        "Pace & cardio": "Finishes come throughout the fight: of 23 stoppage wins, 13 came in R1, five in R2 and five in R3. He has "
                         "gone the distance in nine of his 15 losses (seven three-rounders, two five-rounders); his other losses were "
                         "submissions (three in R1, one in R2) and the two TKOs (R1, R4). His last three fights all went to decisions "
                         "(losses to Daniel Rodriguez and Mike Malott, the win over Brown). Feely noted Malott beat him while he was "
                         "still affected by a low blow.",
        "Fight IQ": "Loose and chatty in the cage. Keeps a busy schedule; he said in July he usually fights two or three times a year "
                    "and wants to reach about 38 UFC fights before retiring (LowKick). His activity has slipped in 2026 because of the "
                    "two withdrawals."},
       ["Kicks the legs and body from long range",
        "Dangerous submission game in scrambles (anaconda, guillotine)",
        "Rarely knocked out; two KO/TKO losses in 45 fights",
        "Loses to wrestlers who hold him down for long stretches",
        "Last three fights went 15 minutes"],
       ["Seven months out and two injury withdrawals since April",
        "Gets hit while hunting his own shots: Brown buckled and cut him in R1",
        "Medić's early power: he has to get through R1 cleanly",
        "Lost three of his last five before the Brown win"],
       ["Wrestle him and hold top position; long control has beaten him repeatedly",
        "Be careful in scrambles; don't give him the neck",
        "Pressure him and make him exchange inside, rather than letting him kick from range"],
       [n("2026-10-29", "Withdrew from bouts against Jacobe Smith at UFC Oklahoma City in July and UFC 332 in October; Sherdog says "
                        "both were because of injuries.", "sherdog_smith_alter"),
        n("2026-11-01", "After beating Randy Brown, Jacobe Smith called Holland out again and said he is 'scared' of him. No response "
                        "from Holland was reported.", "sherdog_smith_scared"),
        n("2026-04-11", "Beat Randy Brown by unanimous decision (30-27 x3) at UFC 327, with a knockdown and an anaconda choke attempt.",
          "cage_holland_brown"),
        n("2026-09-20", "Booked against Uroš Medić on the UFC 334 main card.", "forbes_card")],
       ["sherdog_smith_alter", "sherdog_smith_scared", "lowkick_holland_goal", "cage_holland_brown", "sherdog_327_prev",
        "cage_edm_losers", "forbes_card", "nyp_card", "wiki_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Bilal Hasan",
       "An unbeaten 25-year-old flyweight (10-0, 1 NC), nicknamed 'The IndoNinja', and a former Cage Fury FC champion. He was "
       "born in Hawaii to parents who emigrated from Indonesia, grew up in Washington and looks to Demetrious Johnson for guidance "
       "(UFC.com). He won his contract with a 45-second TKO on the Contender Series on August 11, then knocked out Nilson Rojas in "
       "R2 18 days later at UFC Shanghai. He gets a main-card spot in his second UFC fight.",
       {"Striking": "A former Team USA junior taekwondo competitor (UFC.com). Against Rojas he kicked while Rojas boxed, hurt him "
                    "with a body shot in R1, and finished him in R2 with a fully extended straight right as Rojas leaned in "
                    "(Cageside). His Contender Series win came from a counter right hand (UFC.com). Eight KO/TKO wins.",
        "Grappling": "Some, but little seen: he took Rojas down about two minutes into R1 and briefly got his back (Cageside). One "
                     "submission win (R2, 2024, regional).",
        "Defense": "Barely tested. He has never lost, and his UFC-level sample is about eight minutes of cage time across two fights, "
                   "so his defensive numbers mean little yet. Rojas kept coming forward after being hurt.",
        "Pace & cardio": "Finishes come early: four KO/TKOs in R1, three in R2, a submission in R2, and a KO in R4 of a five-round "
                         "CFFC title fight (2025). His only decision was a split in his 2022 pro debut; Cageside notes he has not gone "
                         "to the scorecards since. His other result was a no contest stopped after seven seconds (UFC.com).",
        "Fight IQ": "Has been a very heavy favourite: UFC.com called him the biggest favourite in "
                    "Contender Series history. He said he wanted to 'take it super slow' but the UFC 'put me on a rocket ship' "
                    "(Sherdog)."},
       ["Counter right hand and straight right finishes",
        "Kicks from a taekwondo base",
        "Finishes early: hasn't been to the judges since his debut",
        "Fast turnarounds: three fights in about three months"],
       ["Thin sample against UFC-level opposition",
        "Third fight in roughly three months (Aug 11, Aug 29, Nov 14)",
        "Has gone past R2 only twice: the R3 debut decision and the R4 title-fight KO",
        "A 15-minute pressure fighter like Gurule is a different test from short fights"],
       ["Make him work for three rounds; he has rarely needed to",
        "Pressure and clinch to take away his range kicking and counters",
        "Test his takedown defense and his back-foot defense"],
       [n("2026-10-21", "Said he had wanted to take it slow, but the UFC 'put me on a rocket ship'.", "unc_hasan"),
        n("2026-08-29", "Debuted 18 days after his Contender Series win and knocked out Nilson Rojas with a straight right at 2:28 of R2.",
          "cage_hasan_rojas"),
        n("2026-08-11", "Won a UFC contract on the Contender Series with a 45-second TKO of Mridul Saikia.", "cage_dwcs"),
        n("2026-09-20", "Booked against Luis Gurule on the UFC 334 main card.", "nyp_card")],
       ["unc_hasan", "cage_hasan_rojas", "cage_dwcs", "cage_dwcs_wi", "ufc_hasan_rise", "ufc_hasan_dwcs", "cage_shanghai_win",
        "nyp_card", "wiki_event"],
       "thin")

# ---------------------------------------------------------------------------------------------------------------
report("Luis Gurule",
       "A 33-year-old flyweight (11-4; 1-4 UFC) who came through the 2024 Contender Series with a split decision over Nick "
       "Piccininni. A high-volume, forward-moving pressure fighter. His one UFC win was a clear decision over Daniel Barez in May; "
       "two weeks later he was submitted in R1 by Rei Tsuruya in a bout moved up to bantamweight. He has lost three of his last "
       "four.",
       {"Striking": "Throws a lot and takes a lot: about 5.3 significant strikes a minute at 41%, absorbing 5.6. He landed 149 of "
                    "299 against Barez in our data. He holds the centre, crashes forward with two-punch combinations and covers up "
                    "on the way in (Cageside, on Coria). Very little knockdown power at UFC level (0.05 per 15); his five KO/TKO wins "
                    "were all regional.",
        "Grappling": "Opportunistic: he locked a D'Arce from half guard and hit a suplex against Barez (Cageside). But takedown "
                     "accuracy is only about 22%. Alden Coria reversed his clinches, stuffed his late takedown and took him down "
                     "'with ease' in R3. Piccininni landed 10 of 20 takedowns on him on the Contender Series in our data.",
        "Defense": "Hittable and vulnerable on the mat. Ode Osbourne knocked him out in R2 (2025), and Tsuruya took him down, landed "
                   "ground-and-pound, took his back against the cage and choked him out at 3:19 of R1 (Cageside). The other two UFC "
                   "losses were decisions (Jesús Aguilar, Coria).",
        "Pace & cardio": "Built for 15 minutes. Five of his 11 wins are decisions, and he has five finishes: KO/TKO three times in R1, "
                         "once in R2 and once in R3, plus an R4 submission in a five-round Fury FC fight (2024). Losses: two "
                         "decisions, an R2 KO and an R1 submission. He took over late against Barez and controlled R3 (Cageside).",
        "Fight IQ": "Comes forward no matter the odds (Cageside called him a guy who isn't 'afraid to come forward'). Took the "
                    "Tsuruya fight soon after beating Barez when Aguilar withdrew."},
       ["Relentless forward pressure and volume",
        "Grinds out late rounds",
        "Gets reversed and taken down by better grapplers",
        "Little one-shot power"],
       ["Defensive responsibility while pressing: he covers up and walks onto shots",
        "Takedown defense against a fighter who can mix grappling in",
        "Facing a big puncher after an R1 submission loss",
        "1-4 in the UFC"],
       ["Counter him as he crashes in",
        "Reverse him on the fence and take him down",
        "Hurt him early; he wins long fights on volume"],
       [n("2026-05-30", "Submitted by Rei Tsuruya at 3:19 of R1 at UFC Macau, in a bout moved up to bantamweight after Jesús Aguilar "
                        "withdrew.", "cage_tsuruya"),
        n("2026-05-16", "Beat Daniel Barez by unanimous decision (30-27 x3), his first UFC win.", "cage_barez"),
        n("2026-09-20", "Booked against Bilal Hasan at flyweight on the UFC 334 main card.", "nyp_card")],
       ["cage_coria", "cage_barez", "cage_tsuruya", "bjp_noche3", "cage_shanghai_los", "nyp_card", "wiki_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Stephen Thompson",
       "'Wonderboy' (17-9-1 in our data), the karate-based welterweight and two-time title challenger against Tyron Woodley, "
       "fights for the last time. He picked the unranked Charles Radtke himself, to give a younger fighter a chance to climb "
       "(Sherdog). He is on a three-fight losing streak, his last win came in December 2022, and he has not fought since July 2025, "
       "when his shin was split to the bone in a split-decision loss to Gabriel Bonfim.",
       {"Striking": "Long-range karate: side kicks, spinning kicks and straight punches from a side-on stance. About 4.3 significant "
                    "strikes a minute at 53%, absorbing 3.0. Against Bonfim he rocked him with a head kick in R2 (Cageside). He "
                    "out-landed Geoff Neal 171-85 over five rounds and Kevin Holland 163-119 in our data.",
        "Grappling": "Almost none on offense (about 0.3 takedowns per 15). One submission win, back in 2010.",
        "Defense": "Hard to hit cleanly at range, but wrestlers beat him. Belal Muhammad (7 of 9 takedowns, about 12 minutes of control), "
                   "Gilbert Burns and Shavkat Rakhmonov (R2 submission) all held him down, and Bonfim took him down in all three rounds "
                   "(Cageside). Joaquin Buckley stopped him in R3 in October 2024 after four takedowns. His other stoppage loss was "
                   "an R2 knockout by Anthony Pettis (2019).",
        "Pace & cardio": "Comfortable over 25 minutes: five of his five-round fights went the distance (two wins, two losses, a draw). His "
                         "finishes: five KO/TKOs in R1, two in R2, one stoppage after R4 (Holland) and the 2010 submission in R2. Eight "
                         "wins are decisions. His three stoppage losses came in R2 (two) and R3 (one).",
        "Fight IQ": "Patient and distance-aware. Thompson said veterans gave him early chances and he wants to do the same, adding "
                    "that Radtke has 'tremendous potential' (Sherdog)."},
       ["Kicks and counters from long range in a karate stance",
        "Outworks strikers who stay at distance",
        "Loses to opponents who take him down and hold him",
        "Three straight losses, two by stoppage"],
       ["Age: Cageside noted he was 42 at the time of the Bonfim fight",
        "About 16 months out of action after a shin injury",
        "Radtke's recent wins came from long top control",
        "Lost the grappling exchanges in all three of his recent losses"],
       ["Close the distance and take him down early",
        "Hold top position for long stretches",
        "Don't stay at kicking range"],
       [n("2026-10-01", "Said he chose Radtke for his retirement fight so a younger fighter could get a chance to climb the rankings.",
          "sherdog_wb_radtke"),
        n("2026-09-20", "UFC 334 announced with Thompson vs. Radtke billed as his final fight.", "forbes_card"),
        n("2025-07-14", "Said his shin was 'split to the bone' after the Bonfim loss and that he would focus on healing.",
          "lowkick_wb_shin")],
       ["sherdog_wb_radtke", "forbes_card", "cage_bonfim", "lowkick_wb_shin", "cage_nash_los", "bjp_edmonton", "nyp_card",
        "wiki_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Charles Radtke",
       "A 36-year-old welterweight (12-5; 5-2 UFC), unranked, who has won two straight by grappling: an R3 rear-naked choke of "
       "Daniel Frunza in November 2025 and a 30-26 x3 decision over Francisco Prado at UFC 327. Both UFC losses were knockouts "
       "against strikers (Carlos Prates, Mike Malott). Stephen Thompson picked him for his retirement fight.",
       {"Striking": "Low output (about 2.2 significant strikes a minute) but real power: R1 TKOs of Gilbert Urbina (two knockdowns) "
                    "and Matthew Semelsberger (0:51). Prado stunned him with a left hook early in R1 (Cageside).",
        "Grappling": "His main weapon in recent fights. Against Frunza he took him down, took the back, nearly finished in R1, then "
                     "choked him out at the end of R3 (LowKick); our data has nearly 12 minutes of control. Against Prado he landed 4 "
                     "of 5 takedowns, held him down for about four minutes in R1, took the back in R2 and opened a cut with elbows "
                     "(Cageside).",
        "Defense": "Takes damage against good strikers: Carlos Prates stopped him at 4:47 of R1 (2024) and Mike Malott 26 seconds "
                   "into R2 (2025). Prado also caught him in a very deep guillotine on a takedown attempt in R3 before he escaped "
                   "(Cageside).",
        "Pace & cardio": "Goes the distance well. Of his 12 wins, four are decisions; his eight finishes came in R1 (three KO/TKOs, two "
                         "submissions), R2 (two KO/TKOs) and R3 (one submission, Frunza). Losses: two decisions and KO/TKOs in R1 (one) "
                         "and R2 (two). He kept wrestling through R3 against Prado after an eye poke that drew a point "
                         "deduction; the cards read 30-26 x3 (Cageside).",
        "Fight IQ": "Has shifted toward a wrestling-first plan. Tough: 'I can actually say I'm about that life,' he said after Prado "
                    "(Cageside)."},
       ["Takedowns, long top control and back takes in his last two fights",
        "Real power in the hands when he stands",
        "Knocked out by both strikers who beat him in the UFC"],
       ["A rangy striker who keeps him at distance",
        "Gets hit when he stands and trades",
        "Being caught on his shots (deep Prado guillotine)"],
       ["Stay at range and strike; don't get pinned on the fence",
        "Punish his level changes with knees or front headlocks",
        "Make him strike for 15 minutes"],
       [n("2026-10-01", "Chosen by Stephen Thompson for his retirement fight; Thompson said Radtke has 'tremendous potential'.",
          "sherdog_wb_radtke"),
        n("2026-04-11", "Beat Francisco Prado by unanimous decision (30-26 x3) after surviving an eye poke and a deep guillotine.",
          "cage_radtke_prado")],
       ["sherdog_wb_radtke", "cage_radtke_prado", "cage_radtke_quote", "lowkick_radtke_frunza", "cage_vancouver_win", "forbes_card",
        "wiki_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Drew Dober",
       "A veteran southpaw lightweight (29-15, 1 NC) and the division's knockout leader with 11 (Cageside). He has won two "
       "straight by stoppage: Kyle Prepolec in R3 (October 2025) and Michael Johnson with a left hand in R2 (March 2026). Before "
       "that he lost three of four, two by knockout. Our data lists him at 38.",
       {"Striking": "Southpaw power puncher: about 4.5 significant strikes a minute at 44%, absorbing 4.3, with 0.65 knockdowns per 15. "
                    "Seventeen KO/TKO wins. He works the body: he finished Rafael Alves with a liver shot in R3 at UFC 277 after "
                    "Terence Crawford told him from ringside to go to the body (Sherdog).",
        "Grappling": "Rarely shoots (about 0.5 takedowns per 15 at 23%). Five submission wins, the last in 2014.",
        "Defense": "Hittable: Matt Frevola (R1, 2023), Jean Silva (R3, 2024) and Manuel Torres (R1, 2025) all stopped him. Grapplers "
                   "beat him on the mat: Islam Makhachev (R3) and Beneil Dariush (R2) submitted him, and Renato Moicano held him "
                   "down for over ten minutes in our data. Takedown defense is about 63%.",
        "Pace & cardio": "Dangerous in every round: of his 17 KO/TKO wins, six came in R1, seven in R2 and four in R3; his five "
                         "submissions came in R1 (four) and R2 (one). Seven wins are decisions. Losses: seven decisions, four KO/TKOs "
                         "(three in R1, one in R3) and four submissions (R1, R2 twice, R3).",
        "Fight IQ": "Experienced and adaptable mid-fight (the Alves body attack). Said he was nervous about Johnson's power and had "
                    "his 'hands full' (Cageside)."},
       ["Southpaw left hand and body shots",
        "Knockouts come in any round",
        "Out-wrestled and submitted by high-level grapplers",
        "Stopped three times since 2023"],
       ["Duncan's front-headlock chokes and takedowns",
        "Durability: three KO/TKO losses since 2023",
        "Age and long career"],
       ["Take him down and attack the neck; grapplers have beaten him",
        "Don't trade with his left hand at range",
        "Push the pace in close"],
       [n("2026-10-30", "Explained how Terence Crawford's advice to go to the body helped him finish Rafael Alves; booked against "
                        "Chris Duncan.", "sherdog_dober_crawford"),
        n("2026-03-08", "Betting on his UFC 326 fight with Michael Johnson was halted over unusual odds movement; Dober said he "
                        "doesn't follow betting and the UFC had not contacted him. He knocked Johnson out in R2.",
          "cage_dober_betting")],
       ["sherdog_dober_crawford", "cage_dober_betting", "cage_326_los", "cage_baku_card", "nyp_card", "wiki_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Chris Duncan",
       "A Scottish lightweight (15-3; 6-2 UFC) from American Top Team, out of the Contender Series. He won four straight before "
       "Renato Moicano dropped and submitted him in R2 of their April main event, a fight Duncan entered as the betting favourite. "
       "His best weapon is his front headlock series: three of the four wins in that streak came by guillotine or anaconda choke "
       "(Sherdog).",
       {"Striking": "Busy and forward: about 5.0 significant strikes a minute at 48%, absorbing 4.3, with some power (0.56 knockdowns "
                    "per 15). LowKick describes a pressure-heavy style built on forward movement and power combinations. Moicano "
                    "out-jabbed him and dropped him with a left hook (Sherdog).",
        "Grappling": "About 2.3 takedowns per 15. Recent submission wins: Bolaji Oki (R1), Jordan Vucenic (R2) "
                     "and Terrance McKinney (anaconda choke, 2:22 of R1, a comeback win per BJPenn.com). He also controlled Omar Morales for "
                     "about 6.5 minutes in a split-decision win.",
        "Defense": "Sherdog's Ben Duffy notes his losses come after he gets clubbed and then finished: Viacheslav Borshchev (KO, R2, "
                   "Contender Series 2021), Manuel Torres (sub, R1, 2024) and Moicano, who took his back after the knockdown and "
                   "finished with a face crank at 3:14 of R2. Takedown defense is about 66%.",
        "Pace & cardio": "Steady over three rounds. Of his 15 wins, four are decisions; finishes: KO/TKO four times in R1, twice in R2, "
                         "once in R3; submissions twice in R1 and twice in R2. All three losses were stoppages, in R1 (one) and R2 "
                         "(two). He won three UFC decisions (Morales, Yanal Ashmouz, Mateusz Rebecki).",
        "Fight IQ": "A scrapper; Duffy says that mindset has 'only truly cost him twice'. Against Moicano a backward elbow he threw "
                    "gave Moicano his opening (Sherdog)."},
       ["Forward pressure with power combinations",
        "Front headlock: guillotines and anacondas off opponents' shots and level changes",
        "Gets clubbed and then finished in his losses",
        "Wins scrappy three-round decisions"],
       ["Chin against a big puncher: Dober has 17 KO/TKO wins",
        "Seven months since a stoppage loss",
        "Gets drawn into wild exchanges"],
       ["Land a clean power shot early; his losses start with him getting hurt",
        "Don't shoot into his front headlock",
        "Counter his forward pressure"],
       [n("2026-04-04", "Dropped by a left hook and submitted by Renato Moicano (face crank, 3:14 of R2) in the UFC Vegas 115 main event.",
          "sherdog_duncan"),
        n("2026-04-06", "BJPenn.com expected him to get an unranked opponent next after the loss.", "bjp_duncan_next"),
        n("2026-10-30", "Booked against Drew Dober.", "sherdog_dober_crawford")],
       ["sherdog_duncan", "sherdog_duncan_prev", "bjp_duncan_next", "bjp_323", "lowkick_duncan_odds", "sherdog_dober_crawford",
        "nyp_card", "wiki_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Jim Miller",
       "A veteran lightweight (39-19, 1 NC), who holds the records for UFC fights (47) and UFC wins (28) "
       "(New York Post). He returned in May after more than a year away and choked out Jared Gordon in R1 for a Performance of the "
       "Night bonus. He faces Terrance McKinney, a fast-starting finisher. Miller has said his target is 50 UFC fights.",
       {"Striking": "Southpaw who presses forward (Cageside). Lower output (about 3.6 significant strikes a minute at 48%) and he "
                    "absorbs more than he lands (4.3). King Green out-landed him 186-57 at UFC 300 in our data.",
        "Grappling": "Elite and still sharp: 22 submission wins, 15 of them in R1. He caught Gordon in a guillotine when Gordon shot "
                     "off a caught body kick, at 3:29 of R1 (Cageside); the New York Post counted it as his sixth guillotine finish. "
                     "About 1.25 submission attempts per 15 minutes. Takedown defense is weaker (about 47%): Chase Hooper landed 8 of "
                     "14 takedowns and held him for about ten minutes in their 2025 fight.",
        "Defense": "Rarely stopped: two KO/TKO losses (Donald Cerrone, R2, 2014; Dan Hooker, R1, 2018) and three submission losses "
                   "(Nate Diaz, Michael Chiesa, Charles Oliveira; the last in 2018). Fourteen of his 19 losses are three-round "
                   "decisions.",
        "Pace & cardio": "Most of his finishes come early: of 22 submissions, 15 in R1, four in R2 and three in R3; of seven KO/TKOs, "
                         "two in R1, four in R2, one in R3. Ten wins are decisions. When fights go long against younger opponents he "
                         "tends to lose on the cards (Alexander Hernandez 2023, Green 2024, Hooper 2025).",
        "Fight IQ": "Very experienced and opportunistic, especially against opponents who shoot or scramble carelessly."},
       ["Snatches the neck on opponents' takedown attempts",
        "Most finishes in R1",
        "Loses decisions to busier strikers and to wrestlers who hold him down",
        "Rarely finished"],
       ["Age: he is 43 in our data",
        "McKinney's speed: all 18 of McKinney's wins are stoppages, 17 in R1, in our data",
        "Takedown defense and output over 15 minutes"],
       ["Out-work him on the feet for three rounds",
        "Don't shoot carelessly or give up the neck in scrambles",
        "Wrestle and hold him down only if your grappling defense is sound"],
       [n("2026-05-09", "Submitted Jared Gordon with a guillotine at 3:29 of R1 at UFC 328.", "cage_miller_gordon"),
        n("2026-05-10", "Won a Performance of the Night bonus for the Gordon finish.", "cage_328_bonus"),
        n("2026-05-10", "Said his son Wyatt, diagnosed with rhabdomyosarcoma, is cancer free. The Post notes his long-stated target "
                        "of 50 UFC fights.", "nyp_miller"),
        n("2026-09-20", "Booked against Terrance McKinney on the UFC 334 prelims.", "nyp_card"),
        n("2026-03-31", "LowKick on McKinney: 'when he's on, he's almost unstoppable', but he can also get caught.",
          "lowkick_seattle")],
       ["cage_miller_gordon", "nyp_miller", "cage_328_bonus", "lowkick_seattle", "nyp_card", "wiki_event"],
       "moderate")


out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
