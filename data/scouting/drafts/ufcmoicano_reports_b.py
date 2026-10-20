"""Scouting reports (batch B) for UFC Fight Night: Moicano vs. Nolan (UFC Vegas 123, 2026-10-31), written 2026-10-20.

Fight-week previews aren't out yet. These draw on recent-fight coverage, booking news and our verified records;
round-by-round counts come from data/verified/fights.csv. The Friday run should refresh them with previews and
weigh-in news.

Fighters: Andre Petroski, Rodrigo Sezinando, Theodor Berggren, Julian Erosa, Lee Jeong-yeong, Nick Klein.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports"
UPDATED = "2026-10-20T18:00:00+00:00"
EVENT = "UFC Fight Night: Moicano vs. Nolan"


def slug(name):
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def src(outlet, author, title, url, date):
    return {"outlet": outlet, "author": author, "title": title, "url": url, "date": date}


SRC = {
    # card / bookings
    "ufc_event": src("UFC.com", "", "UFC Fight Night: Moicano vs Nolan", "https://www.ufc.com/event/ufc-fight-night-october-31-2026", "2026-10-20"),
    "heavy_welter": src("Heavy", "Marcel Dorff", "Intriguing Welterweight Clash Booked for UFC Vegas 123",
                        "https://heavy.com/sports/ufc/intriguing-welterweight-clash-ufc-vegas-123/", "2026-09-25"),
    "heavy_erosa_lee": src("Heavy", "Marcel Dorff", "UFC Books First Fight for UFC Vegas 123 Event",
                           "https://heavy.com/sports/ufc/ufc-books-fight-ufc-vegas-123/", "2026-08-14"),
    "bn_kropschot": src("BoxingNews", "MMA News Staff", "Kropschot Books UFC Debut Against Klein",
                        "https://boxingnews.com/news/kropschot-ufc-debut-klein-october", "2026-08-26"),
    "rotowire_petroski": src("Rotowire", "", "Andre Petroski MMA Stats & News", "https://www.rotowire.com/mma/player/andre-petroski-2201", "2026-08-20"),
    "yakima_erosa": src("Yakima Herald-Republic", "Luke Thompson", "Yakima's Erosa set to fight on Halloween",
                        "https://www.yakimaherald.com/sports/mma/yakimas-erosa-set-to-fight-on-halloween/article_303a3b5f-6f20-4dca-91c7-5dd3e1cb97a3.html",
                        "2026-08-15"),
    "starnews_lee": src("Star News Korea", "Park Geon-do", "Korean Fighters Duo Set to Restore UFC Honor",
                        "https://www.starnewskorea.com/en/sports/2026/10/08/2026100809530534759", "2026-10-08"),
    "nate_lee": src("Nate Sports", "", "Lee Jeong-yeong returns to the UFC after a year and a half, faces Erosa on Nov. 1 (KST)",
                    "https://sports.news.nate.com/view/20260918n14119", "2026-09-18"),
    # Petroski
    "cage_brundage": src("Cageside Press", "Eddie Law", "Cody Brundage TKO's Petroski, Snaps Losing Streak",
                         "https://cagesidepress.com/2026/05/16/cody-brundage-tkos-petroski-snaps-losing-streak/", "2026-05-16"),
    "sherdog_v117": src("Sherdog", "Tristen Critchfield", "UFC Vegas 117 'Allen vs. Costa' play-by-play, results & round scoring",
                        "https://www.sherdog.com/news/news/UFC-Vegas-117-Allen-vs-Costa-playbyplay-results-round-scoring-201198", "2026-05-16"),
    "cage_rowston": src("Cageside Press", "", "UFC Perth: \"Battle Giraffe\" Cam Rowston Makes Splash in Debut, Stops Andre Petroski",
                        "https://cagesidepress.com/2025/09/27/ufc-perth-battle-giraffe-cam-rowston-makes-splash-in-debut-stops-andre-petroski/", "2025-09-27"),
    "cage_atl_losers": src("Cageside Press", "", "What's Next: UFC Atlanta Losers",
                           "https://cagesidepress.com/2025/06/16/whats-next-ufc-atlanta-losers/", "2025-06-16"),
    "lowkick_serbia": src("LowKick MMA", "", "UFC Serbia: Matchmaking for All of Saturday's Winners",
                          "https://www.lowkickmma.com/matchmaking-for-all-of-saturdays-winners/", "2026-08-04"),
    # Sezinando
    "sherdog_sez_qf": src("Sherdog", "Brian Knapp", "Rodrigo Sezinando Tames Rival Diego Bianchini, Advances to 'TUF 33' Semifinals",
                          "https://www.sherdog.com/news/news/Rodrigo-Sezinando-Tames-Rival-Diego-Bianchini-Advances-to-TUF-33-Semifinals-197710", "2025-07-15"),
    "sherdog_sez_sf": src("Sherdog", "Brian Knapp", "Ground Superiority Carries Rodrigo Sezinando into 'TUF 33' Welterweight Final",
                          "https://www.sherdog.com/news/news/Ground-Superiority-Carries-Rodrigo-Sezinando-into-TUF-33-Welterweight-Final-197875", "2025-07-29"),
    "cage_sez_final": src("Cageside Press", "Shawn Bitter", "Daniil Donchenko Makes Quick Work Of Sezinando, Wins TUF 33",
                          "https://cagesidepress.com/2025/09/13/daniil-donchenko-makes-quick-work-of-sezinando-wins-tuf-33/", "2025-09-13"),
    "sherdog_noche": src("Sherdog", "", "Noche UFC 'Lopes vs. Silva' Play-by-Play, Results & Round Scoring",
                         "https://www.sherdog.com/news/news/Noche-UFC-Lopes-vs-Silva-PlaybyPlay-Results-Round-Scoring-198365", "2025-09-13"),
    "cage_tuf_ep8": src("Cageside Press", "", "The Ultimate Fighter 33 Ep. 8: The Time For Talk is Over",
                        "https://cagesidepress.com/2025/07/16/the-ultimate-fighter-33-ep-8-the-time-for-talk-is-over/", "2025-07-16"),
    "mmanews_sez_inj": src("MMA News", "", "Rodrigo Sezinando Injured, TUF Welterweight Finale Moved From UFC 319 To Noche UFC 3",
                           "https://www.mmanews.com/article/rodrigo-sezinando-injured-tuf-welterweight-finale-moved-from-ufc-319-to-noche-ufc-3", "2025-08-14"),
    # Berggren
    "ufc_berggren": src("UFC.com", "Simon Head", "Theodor Berggren Answered The Call",
                        "https://www.ufc.com/news/theodor-berggren-answered-call-ufc-baku", "2026-06-25"),
    "yahoo_berggren_pick": src("Yahoo Sports (ClutchPoints)", "Dominik Zawartko", "Daniil Donchenko vs. Theodor Berggren prediction, odds, pick for UFC Baku",
                               "https://sports.yahoo.com/articles/daniil-donchenko-vs-theodor-berggren-175655714.html", "2026-06-25"),
    "yahoo_sherdog_baku": src("Sherdog (via Yahoo Sports)", "", "UFC Baku 'Fiziev vs. Torres' play-by-play, results & round scoring",
                              "https://sports.yahoo.com/articles/ufc-baku-fiziev-vs-torres-164808677.html", "2026-06-27"),
    "yardbarker_baku": src("Yardbarker (BoxingNews)", "Tom Rashid", "Daniil Donchenko flatlines UFC newcomer with head kick TKO at UFC Baku",
                           "https://www.yardbarker.com/mma/articles/daniil_donchenko_flatlines_ufc_newcomer_with_head_kick_tko_at_ufc_baku/s1_17349_44001412", "2026-06-27"),
    "mmauk_berggren": src("MMA UK", "Myles Painter", "Across The Pond Profile: Cage Warriors fighter Theodor Berggren",
                          "https://mmauk.net/2025/09/22/across-the-pond-profile-cage-warriors-fighter-theodor-berggren/", "2025-09-22"),
    "cage_baku_bonus": src("Cageside Press", "", "Four Including Headliner Fiziev Earn Performance Bonuses at UFC Baku",
                           "https://cagesidepress.com/2026/06/27/four-including-headliner-fiziev-earn-performance-bonuses-at-ufc-baku/", "2026-06-27"),
    # Erosa
    "cage_douglas": src("Cageside Press", "Shawn Bitter", "UFC Seattle: Lerryan Douglas Silences Crowd, Finishes Local Hero Julian Erosa",
                        "https://cagesidepress.com/2026/03/28/ufc-seatte-lerryan-douglas-silences-crowd-finishes-local-hero-julian-erosa/", "2026-03-28"),
    "cage_seattle_winners": src("Cageside Press", "", "What's Next: UFC Seattle Winners",
                                "https://cagesidepress.com/2026/03/30/whats-next-ufc-seattle-winners-2/", "2026-03-30"),
    "cage_costa": src("Cageside Press", "", "Melquizael Costa Decisions Julian Erosa to Kick Off UFC Vegas 106 Main Card",
                      "https://cagesidepress.com/2025/05/17/melquizael-costa-decisions-julian-erosa-to-kick-off-ufc-vegas-106-main-card/", "2025-05-17"),
    "mania_costa_hosp": src("MMA Mania", "", "Both fighters from UFC Vegas 106's 'Fight of the Night' transported to hospital after wicked brawl",
                            "https://www.mmamania.com/2025/5/18/24432439/julian-erosa-costa-ufc-vegas-106-fight-of-the-night-transported-to-hospital-after-wicked-brawl",
                            "2025-05-18"),
    # Lee
    "cage_santos_lee": src("Cageside Press", "Eddie Law", "Daniel Santos Puts It All Together, Takes Decision vs Lee",
                           "https://cagesidepress.com/2025/05/10/daniel-santos-puts-it-all-together-takes-decision-vs-lee/", "2025-05-10"),
    "cage_amil_lee": src("Cageside Press", "Bryson Hester", "Hyder Amil Scores Highlight Reel TKO With 38-Punch Combo",
                         "https://cagesidepress.com/2024/07/20/hyder-amil-scores-highlight-reel-tko-with-38-punch-combo/", "2024-07-20"),
    "cage_lee_zha": src("Cageside Press", "", "UFC Vegas 68: Jeong-Yeong Lee Takes Close Decision Over Yi Zha in Road to UFC Featherweight Final",
                        "https://cagesidepress.com/2023/02/05/ufc-vegas-68-lee-jeong-yeong-vs-yi-zha/", "2023-02-05"),
    "cage_ufc326_weight": src("Cageside Press", "", "\"Weight Management Issues\" Cause Fight to Fall Off UFC 326",
                              "https://cagesidepress.com/2026/03/06/weight-management-issues-cause-fight-to-fall-off-ufc-326/", "2026-03-06"),
    # Klein
    "cage_abdulmalik": src("Cageside Press", "Shawn Bitter", "Mansur Abdul-Malik Survives Scare, Puts Away Nick Klein at UFC Seattle",
                           "https://cagesidepress.com/2025/02/22/mansur-abdul-malik-survives-scare-puts-away-nick-klein-at-ufc-seattle/", "2025-02-22"),
    "cage_pulyaev": src("Cageside Press", "Eddie Law", "Andrey Pulyaev Turns It Around In Round 2, Scores TKO Victory",
                        "https://cagesidepress.com/2025/08/02/andrey-pulyaev-turns-it-around-in-round-2-scores-tko-victory/", "2025-08-02"),
    "cage_v109_losers": src("Cageside Press", "", "What's Next: UFC Vegas 109 Losers",
                            "https://cagesidepress.com/2025/08/11/whats-next-ufc-vegas-109-losers/", "2025-08-11"),
}

R = {}


def report(name, summary, how, patterns, concerns, keys, news, sources, depth):
    R[name] = {"name": name, "updated": UPDATED, "event": EVENT, "summary": summary, "how_they_fight": how,
               "patterns": patterns, "concerns": concerns, "keys_to_beat": keys, "news": news,
               "sources": [SRC[k] for k in sources], "depth": depth}


# ---------------------------------------------------------------- Andre Petroski
report("Andre Petroski",
       "A 35-year-old Renzo Gracie Philly grappler (13-6, 8-5 UFC) who built an 8-2 UFC start on takedowns and long top control, "
       "but has now lost three straight, the last two by knockout. Wins by grinding; loses when someone lands clean on him.",
       {"Striking": "Functional at best: about 2.9 significant strikes landed a minute against 3.8 absorbed. Uses calf kicks and pressure "
                    "mainly to set up level changes (Cageside Press, Sherdog on the Brundage fight). Out-struck at range by Edmen Shahbazyan "
                    "over 15 minutes (34-53 in our data).",
        "Grappling": "The engine of every win: about 2.4 takedowns per 15 minutes, 48% accuracy, and huge control numbers in his decision wins "
                     "(12:50 of control vs Josh Fremd, 9:20 vs Dylan Budka, 8:00 vs Wellington Turman). Works elbows from side control, "
                     "looks for cradles and mount (R1 vs Brundage). Submitted Yaozong Hu and Nick Maximov in the UFC. Against a better "
                     "grappler (Rodolfo Vieira) he kept it standing and won 55-58 on strikes by decision, so he can adapt.",
        "Defense": "Takedown defense is good (~79%), but the chin and the entry are the problem. Five of his six losses are KO/TKOs and three "
                   "of the last four losses came from a single clean shot as he closed distance or exchanged: Michel Pereira (R1, 1:06), "
                   "Cam Rowston (counter left hook on his entry, R1 2:41) and Cody Brundage (left hook after a feint, R2 0:44). Also knocked "
                   "down by Shahbazyan in the decision loss.",
        "Pace & cardio": "Slow burner. Of his 13 wins, five are decisions; two of his three UFC finishes came in R3 "
                         "(Micheal Gillmore TKO R3, Yaozong Hu SUB R3 at 4:46). Career finishes: R1 4, R2 2, R3 2. His losses come early: "
                         "KO/TKO losses in R1 (Pereira, Rowston) and R2 (Aaron Jeffery, Jacob Malkoun 0:39, Brundage 0:44); his only decision "
                         "loss went the distance. He doesn't fade; he gets caught before his grinding pays off. Won R1 on all three Sherdog "
                         "cards vs Brundage and was stopped 44 seconds into R2.",
        "Fight IQ": "Knows his path (take it down, ride, elbow) and stuck to it in the win streak. Adapted against a BJJ ace in Vieira. "
                    "His entries, though, have become predictable and he keeps walking into counters."},
       ["Grinds decisions with takedowns and long top control (5 of his 8 UFC wins went the distance)",
        "UFC finishes came late: R3 TKO and R3 submission; R1 sub of Maximov the exception",
        "Stopped early: all five KO/TKO losses in R1 or the first minute of R2 (Malkoun 0:39, Brundage 0:44)",
        "Three straight losses (Shahbazyan dec, Rowston R1 TKO, Brundage R2 TKO); two straight knockouts"],
       ["Durability: KO'd in three of his last four losses and dropped in the fourth",
        "Age 35, three-fight skid; LowKick noted he went 8-2 to start his UFC run and then lost three straight",
        "Opponent Azamat Bekoev is also on a two-fight skid, so both men's jobs may be on the line"],
       ["Counter his entries: he telegraphs the level change behind calf kicks and pressure",
        "Hurt him early; he's never been stopped late",
        "Stay off the fence and get up fast; don't concede the long top-control rounds that win him decisions"],
       [{"date": "2026-08-20", "text": "Booked against Azamat Bekoev (20-5) at middleweight for Oct. 31; Rotowire notes Petroski is on a three-fight skid and Bekoev on a two-fight skid.",
         "source": SRC["rotowire_petroski"]["url"]},
        {"date": "2026-05-16", "text": "Lost to Cody Brundage by R2 TKO (0:44) after winning R1 with a takedown and mount; dropped by a left hook after a feint (Sherdog, Cageside Press).",
         "source": SRC["sherdog_v117"]["url"]}],
       ["cage_brundage", "sherdog_v117", "cage_rowston", "cage_atl_losers", "lowkick_serbia", "rotowire_petroski", "ufc_event"],
       "moderate")

# ---------------------------------------------------------------- Rodrigo Sezinando
report("Rodrigo Sezinando",
       "A Nova Uniao-trained Brazilian welterweight based in Canada (8-2) and the TUF 33 welterweight runner-up, a former BFL and Samourai "
       "MMA champion per Cageside Press. A front-running finisher who won his TUF fights on clinch work and takedowns, then was stopped in "
       "R1 of the final by Daniil Donchenko. Hasn't fought in 13 months.",
       {"Striking": "Aggressive and willing, with a counter left hook (staggered Diego Bianchini) and lots of close-range elbows (cut Bianchini, "
                    "per Sherdog). In the TUF semifinal Jefferson Creighton was the better striker at range, per Sherdog and coach Daniel "
                    "Cormier. Against Donchenko he kept charging forward into exchanges and was out-landed 10-39 in our data.",
        "Grappling": "His most reliable path. Took Creighton down in all three rounds, reversed on the mat, took the back and threatened the neck "
                     "(Sherdog); against Bianchini he sprawled and powered into top position with heavy ground strikes. Three submission "
                     "wins on the regional scene, all in R1. Donchenko stuffed most of his shots (1 of 4) and took him down twice.",
        "Defense": "The concern. Opened up badly by elbows against Donchenko (cut and bleeding heavily, doctor check), then dropped by a right "
                   "hand after a stuffed takedown and finished on the ground (Sherdog, Cageside Press). Absorbs about 4.9 significant "
                   "strikes a minute on our small UFC sample.",
        "Pace & cardio": "Fast starter. Of his seven finishes, five came in R1 (three subs, two KOs) and two in R2 (KOs); only one win went to "
                         "a decision. His two losses: a 15-minute decision on the Brazilian regionals (Willker Lemos, 2022) and the R1 TKO "
                         "to Donchenko (4:27). On TUF he went the distance twice and finished strong (\"hit the accelerator\" in R2 vs "
                         "Bianchini; landed a takedown and back take in R3 vs Creighton, per Sherdog), so the gas tank looked fine. Coaches "
                         "on the show expected him to burn energy chasing an early finish (Cageside Press).",
        "Fight IQ": "Emotional and aggressive; when his takedowns weren't landing against Donchenko he kept charging into exchanges rather than "
                    "resetting. Clever about clinching when an opponent overextends (Cormier, via Sherdog)."},
       ["Finishes early: five of seven stoppage wins in R1, the other two in R2",
        "Turns the fight into clinch and takedowns when out-struck at range",
        "Stopped once, in R1, by punches after taking heavy elbows and a stuffed shot",
        "TUF exhibition wins went 2 and 3 rounds (decisions), not on his pro record"],
       ["13 months out; the TUF final was postponed from UFC 319 by an injury on his side (reported as an ankle in some outlets)",
        "Defense in open exchanges and against elbows",
        "Takedown accuracy against a good defender (1 of 4 vs Donchenko)"],
       ["Stuff the first takedowns and make him reset in open space",
        "Elbows and counters as he charges in; he bleeds and gets reckless",
        "Survive the first round; most of his finishes come early"],
       [{"date": "2026-09-25", "text": "Booked against Theodor Berggren at welterweight for Oct. 31 (Heavy). Both men lost to Daniil Donchenko in their last fight.",
         "source": SRC["heavy_welter"]["url"]},
        {"date": "2025-08-14", "text": "The TUF 33 final was moved from UFC 319 to Noche UFC after Sezinando was injured; MMA News reported the injury, the specific nature was not confirmed by the UFC.",
         "source": SRC["mmanews_sez_inj"]["url"]},
        {"date": "2026-10-20", "text": "Record disagreement: our verified data has him 8-2; one betting listing shows 9-2. TUF exhibition bouts are not counted in our record.",
         "source": SRC["ufc_event"]["url"]}],
       ["sherdog_sez_qf", "sherdog_sez_sf", "cage_sez_final", "sherdog_noche", "cage_tuf_ep8", "mmanews_sez_inj", "heavy_welter", "ufc_event"],
       "moderate")

# ---------------------------------------------------------------- Theodor Berggren
report("Theodor Berggren",
       "A 27-year-old Swedish southpaw (8-4) from Fight Club Rush and Cage Warriors who has never won a decision: all eight wins are "
       "stoppages, six in R1. Took his UFC debut on about three weeks' notice in Baku and was stopped in R2 by Daniil Donchenko.",
       {"Striking": "Aggressive, forward striker who wants to win with strength, range and output (UFC.com). ClutchPoints' preview credits him "
                    "with good timing, head/body/leg kicks and fast pressure. Against Donchenko he landed a step-in knee and a clean left hand "
                    "but was out-landed 23-71 and hurt by a right hook in R1 (Sherdog play-by-play).",
        "Grappling": "Three R1 submission wins on the regional scene (rear-naked chokes per MMA UK). Barely grappled in Baku (no takedown attempts). "
                     "Tapped to an arm-triangle in R3 against Justin Burlinson at Cage Warriors 181.",
        "Defense": "Leaky in his debut: kept a high guard but ate leg kicks and body shots, then a right head kick through the guard dropped him "
                   "and two hooks finished it (Sherdog via Yahoo). Absorbed 5.4 significant strikes a minute on our small UFC sample.",
        "Pace & cardio": "Fast starter whose results get worse the longer fights go. Finishes: R1 6, R2 1 (Battaglia, 4:44), R3 1 (Samedov TKO). "
                         "Losses: two 15-minute decisions (Christian Stigenberg 2022, Leonardo Damiani 2025), an R3 submission (Burlinson, 2:44) "
                         "and the R2 TKO to Donchenko (1:35). So three of his four losses came late or on the cards, and he is 0-2 in "
                         "fights that reached the judges. Durability: stopped once by strikes (head kick plus punches), once by submission.",
        "Fight IQ": "Confident and aggressive, says he has a 100% finish rate and expects a war (UFC.com). The short-notice debut against a "
                    "rising TUF winner was a big step; his more recent two regional wins came later in fights (R2, R3), which ClutchPoints "
                    "credited to better preparation."},
       ["Every win is a finish; six of eight in R1",
        "Never won a decision (0-2 on the cards)",
        "Late losses: R3 submission, two decisions, and an R2 TKO in his UFC debut"],
       ["Defense against kicks and body work; dropped twice in his debut",
        "Grappling defense late in fights (arm-triangle loss in R3)",
        "Big jump in competition: 1-1 in Cage Warriors before the UFC call"],
       ["Weather his early burst, then take over in R2 and R3",
        "Chop the lead leg and body (Donchenko's blueprint)",
        "Wrestle him late; he has been submitted in R3 and lost both fights that went the distance"],
       [{"date": "2026-09-25", "text": "Booked against Rodrigo Sezinando at welterweight for Oct. 31 (Heavy).",
         "source": SRC["heavy_welter"]["url"]},
        {"date": "2026-06-27", "text": "UFC debut on short notice (replacing Andreas Gustafsson, who withdrew with a medical issue): lost to Daniil Donchenko by R2 TKO (head kick and punches, 1:35).",
         "source": SRC["yahoo_sherdog_baku"]["url"]},
        {"date": "2026-06-25", "text": "Sources disagree on his last regional fight: ClutchPoints (via Yahoo) listed a TKO loss to Abdulatip Samedov, while our verified data records an R3 TKO win over Samedov at FCR 27 (Feb. 2026).",
         "source": SRC["yahoo_berggren_pick"]["url"]}],
       ["ufc_berggren", "yahoo_berggren_pick", "yahoo_sherdog_baku", "yardbarker_baku", "cage_baku_bonus", "mmauk_berggren", "heavy_welter"],
       "moderate")

# ---------------------------------------------------------------- Julian Erosa
report("Julian Erosa",
       "A 37-year-old Xtreme Couture veteran from Yakima (31-13, 9-9 UFC) who wins high-volume brawls and scrambles but has been knocked out "
       "often: two straight losses, the last a three-knockdown R1 KO by Lerryan Douglas in March. Has never been submitted.",
       {"Striking": "Volume brawler: about 6.3 significant strikes landed and 5.7 absorbed per minute. Long (188 cm reach) and busy with one-twos, "
                    "knees, kicks and spinning backfists; content to trade in the pocket. Cageside Press: \"Defense has never been a staple\" of "
                    "his game.",
        "Grappling": "A real finishing threat: 14 of his 31 wins are submissions, including UFC finishes of Ricardo Ramos and Christian Rodriguez in "
                     "R1 and come-from-behind R3 subs of Sean Woodson and Charles Jourdain after being knocked down in both. Hunts takedowns "
                     "when the stand-up gets bad (3 of 10 vs Melquizael Costa).",
        "Defense": "The weak point. Eight KO/TKO losses, five of them in R1 inside the UFC (Devonte Smith, Seung Woo Choi, Alex Caceres, Fernando "
                   "Padilla, Douglas). Douglas dropped him three times in 3:33 (Cageside Press). Broke an orbital and his nose in the Costa "
                   "fight, per MMA Mania. Never submitted.",
        "Pace & cardio": "Tank is excellent; he gets better as a fight turns into a mess. Finishes by round across his career: R1 9, R2 10, R3 6, "
                         "R4 1 (12 KO/TKO, 14 SUB, 5 decisions). Losses: eight KO/TKO (R1 6, R2 1, R3 1) and five decisions. The danger "
                         "window is early: if he survives R1, he usually ends up in a high-output decision or a late scramble finish. His "
                         "three-fight win streak (Ramos, Rodriguez, Darren Elkins) were all R1 finishes, though.",
        "Fight IQ": "Experienced and opportunistic; rarely panics on the ground. Takes a lot of damage to land his own, and doesn't adjust his "
                    "defense against faster, harder punchers."},
       ["Volume plus scrambles; submissions from front-headlocks and back takes",
        "Comebacks: submitted Woodson and Jourdain in R3 after being dropped",
        "R1 KO losses to fast power punchers (five in the UFC)",
        "Never submitted; decision losses come against technical strikers (Costa) or wrestlers (Grant Dawson)"],
       ["Age 37, two straight losses, the last a brutal R1 KO seven months ago",
        "Chin and defense against an aggressive early puncher",
        "Accumulated damage (orbital fracture vs Costa, May 2025)"],
       ["Land clean early: most of his losses come in R1",
        "Don't grapple loosely with him; avoid scrambles and front-headlock exchanges",
        "Use speed and counters rather than a volume trade"],
       [{"date": "2026-08-14", "text": "Booked against Lee Jeong-yeong at featherweight for Oct. 31; both on two-fight skids (Heavy).",
         "source": SRC["heavy_erosa_lee"]["url"]},
        {"date": "2026-03-28", "text": "Lost to Lerryan Douglas by R1 KO (3:33) in Seattle after three knockdowns.",
         "source": SRC["cage_douglas"]["url"]},
        {"date": "2026-10-20", "text": "Record disagreement: our verified data and the Yakima Herald have him 31-13; UFC.com lists 31-14.",
         "source": SRC["yakima_erosa"]["url"]}],
       ["cage_douglas", "cage_seattle_winners", "cage_costa", "mania_costa_hosp", "heavy_erosa_lee", "yakima_erosa", "ufc_event"],
       "good")

# ---------------------------------------------------------------- Lee Jeong-yeong
report("Lee Jeong-yeong",
       "The Road to UFC season-one featherweight winner and a former Road FC champion (11-3, 2-2 UFC including the RTU final), "
       "a heavy-handed striker with a taekwondo and jiu-jitsu base per Korean outlets. Hasn't fought since May 2025 and missed weight "
       "so badly in March 2026 that his UFC 326 bout was scrapped.",
       {"Striking": "Hard right hand; Cageside Press credited him with a R1 knockdown of Daniel Santos and a hard right that stunned Yi Zha "
                    "(our verified data records no knockdowns in the Santos fight). Out-landed Blake Bilder 49-19. Wants to trade in the pocket "
                    "and loads up for knockouts, which leaves him open to counters and level changes.",
        "Grappling": "Seven regional finishes include three submissions (R1-R2), and Korean outlets list him as a jiu-jitsu black belt. "
                     "Defensively shaky against strong wrestlers: Zha controlled much of the RTU final, Santos took him down repeatedly "
                     "(six-plus minutes of control in our data, back takes in R2 and R3).",
        "Defense": "Stopped once: Hyder Amil swarmed him with about 30 unanswered punches on the fence in 65 seconds (Cageside Press), out-landed "
                   "4-42. Takedown defense ~72% on paper but poor against the two wrestlers he's faced recently.",
        "Pace & cardio": "Early finisher on the regionals: KOs R1 3, R2 1; subs R1 2, R2 1; plus four decisions. His three UFC-era fights went "
                         "the full 15 (split win vs Zha, decision wins vs Bilder, decision loss vs Santos) and he faded into being ridden "
                         "late vs Santos (taken down in R2 and R3). Losses: decision (2017 Road FC), R1 TKO (Amil) and a 30-27 x3 decision "
                         "(Santos). Durable over three rounds except for the Amil blitz.",
        "Fight IQ": "Aggressive and heavy-handed, but over-commits to the right hand (missed one in R2 vs Santos and was taken down straight "
                    "away, per Cageside Press). Weight management is a real question after UFC 326."},
       ["Looks for the KO with the right hand early",
        "Regional finishes in R1-R2; UFC fights go the distance",
        "Stopped once, in R1, by an all-out early blitz",
        "Taken down and ridden by wrestlers in the later rounds"],
       ["Weight cut: did not weigh in for UFC 326 (\"weight management issues\") in March 2026",
        "17 months out of competition by fight night",
        "Two straight losses; the UFC 326 scratch adds pressure on his roster spot"],
       ["Blitz him early; he has been overwhelmed when pinned on the fence",
        "Level-change behind his right hand and ride him in R2-R3",
        "Make him work through scrambles; his grappling defense has been the weak link in the UFC"],
       [{"date": "2026-03-06", "text": "His UFC 326 bout with Gaston Bolanos was cancelled at the weigh-ins over his \"weight management issues\"; Lee did not weigh in (Cageside Press). He had taken the fight as a late replacement.",
         "source": SRC["cage_ufc326_weight"]["url"]},
        {"date": "2026-09-18", "text": "Korean outlets report he moved to the United States in August 2025 and spent a year training there (gym not named).",
         "source": SRC["nate_lee"]["url"]},
        {"date": "2026-08-14", "text": "Booked against Julian Erosa at featherweight for Oct. 31 (Heavy).",
         "source": SRC["heavy_erosa_lee"]["url"]}],
       ["cage_santos_lee", "cage_amil_lee", "cage_lee_zha", "cage_ufc326_weight", "heavy_erosa_lee", "starnews_lee", "nate_lee"],
       "moderate")

# ---------------------------------------------------------------- Nick Klein
report("Nick Klein",
       "A Pura Vida BJJ middleweight (6-3, 0-2 UFC) and Contender Series winner who starts like a house on fire with kicks, takedowns "
       "and back takes, then has been stopped in R2 of both UFC fights. Hasn't fought since August 2025.",
       {"Striking": "Long (196 cm reach) and kicks a lot early; landed a spinning backfist/elbow that wobbled Mansur Abdul-Malik in R1 (Cageside "
                    "Press, MMA Mania). Striking is mostly a lead-in to wrestling; about 3.1 significant strikes a minute.",
        "Grappling": "Primary weapon: 3.6 takedowns per 15 minutes and 1.1 sub attempts per 15. Three of his six wins are submissions "
                     "(two in R1, including a 37-second finish on DWCS, one in R3). Took Andrey Pulyaev down three times in R1, forced his back and "
                     "threatened a neck crank before losing position (Cageside Press). Struggles to finish shots against a real wrestler: "
                     "1 of 9 vs Abdul-Malik.",
        "Defense": "Stopped in all three losses, all by strikes: Dorjan Dokaj (R3), Abdul-Malik (punches and knees from the back, R2) and Pulyaev "
                   "(body kick and punches, R2, per Cageside Press). Gives up position when scrambles go wrong.",
        "Pace & cardio": "Front-loaded. Finishes: R1 4 (two KOs inside 30 seconds, two subs), R3 1 (sub); one decision. Losses: R3 KO "
                         "(regional), then R2 TKOs in both UFC fights (3:24, 1:31). Cageside Press described him as visibly fatigued in R2 "
                         "against Abdul-Malik after a failed takedown-heavy R1; against Pulyaev he won R1 clearly and was stopped 91 seconds "
                         "into R2. Fair to call him a fader against durable opposition.",
        "Fight IQ": "Commits hard to the takedown, even when he had Abdul-Malik hurt on the feet (he shot instead of following up, per Cageside "
                    "Press). Needs to pace himself better."},
       ["Explosive R1: kicks, takedowns, back takes",
        "R2 stoppage losses in both UFC fights after big first rounds",
        "Finishes come early (four in R1) or by late submission"],
       ["Cardio and output in R2-R3",
        "14-month layoff; 0-2 in the UFC and likely fighting for his job",
        "Opponent Joseph Kropschot (9-3, five straight wins, DWCS) per BoxingNews"],
       ["Defend the R1 takedown flurry and stay off your back",
        "Body work and pressure early in R2 when his tank dips",
        "Punish failed shots; he's been finished off scrambles"],
       [{"date": "2026-08-26", "text": "Booked against Contender Series winner Joseph Kropschot (9-3) for Oct. 31, Kropschot's UFC debut (BoxingNews).",
         "source": SRC["bn_kropschot"]["url"]},
        {"date": "2025-08-02", "text": "Lost to Andrey Pulyaev by R2 TKO (1:31) after winning R1 with takedowns.",
         "source": SRC["cage_pulyaev"]["url"]}],
       ["cage_abdulmalik", "cage_pulyaev", "cage_v109_losers", "bn_kropschot", "ufc_event"],
       "moderate")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rep in R.items():
        p = OUT / f"{slug(name)}.json"
        p.write_text(json.dumps(rep, indent=1, ensure_ascii=False) + "\n")
        print("wrote", p.relative_to(ROOT.parent))
