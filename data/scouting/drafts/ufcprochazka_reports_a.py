"""Scouting reports (part A) for UFC Fight Night: Procházka vs. Stirling (UFC Qatar / Fight Night 294, ABHA Arena,
Doha, 2026-11-21), first pass written 2026-11-10.

Fight-week previews aren't out yet: these draw on recent-fight recaps, booking news, early odds and our verified
records. Round/method counts are taken from data/verified/fights.csv. Later runs should refresh them with the
Sherdog/MMA Mania/UFC.com previews and weigh-in news.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATED = "2026-11-10T18:00:00+00:00"
EVENT = "UFC Fight Night: Procházka vs. Stirling"


def src(outlet, title, url, date, author=""):
    return {"outlet": outlet, "author": author, "title": title, "url": url, "date": date}


SRC = {
    # card / booking
    "ufc_event": src("UFC.com", "UFC Fight Night: Procházka vs. Stirling (event page)",
                     "https://www.ufc.com/event/ufc-fight-night-november-21-2026", "2026-11-10"),
    "cage_card": src("Cageside Press", "9 Fights Revealed For UFC Qatar Event On November 21",
                     "https://cagesidepress.com/2026/09/29/full-ufc-qatar-card-revealed-for-november-21-event/",
                     "2026-09-29", "Eddie Law"),
    "sherdog_card": src("Sherdog", "Jiri Prochazka vs. unbeaten Navajo Stirling headlines UFC Qatar",
                        "https://www.sherdog.com/news/news/Jiri-Prochazka-vs-unbeaten-Navajo-Stirling-headlines-UFC-Qatar-203016",
                        "2026-09-30", "Sourav Chakraborty"),
    "yahoo_odds": src("Yahoo Sports (MMA Junkie)", "UFC Fight Night 294: Jiri Prochazka vs. Navajo Stirling odds, what to know",
                      "https://sports.yahoo.com/articles/ufc-fight-night-294-jiri-185026074.html", "2026-11-05",
                      "Farah Hannoun"),
    # Prochazka
    "lowkick_ulberg_react": src("LowKick MMA",
                                "Jiri Prochazka Pays the Price for Showboating at UFC 327: Jon Jones, Aiemann Zahabi and others react",
                                "https://www.lowkickmma.com/jiri-prochazka-pays-the-price-for-showboating-at-ufc-327-jon-jones-aiemann-zahabi-and-others-react/",
                                "2026-04-12", "Subham"),
    "lowkick_ulberg_hl": src("LowKick MMA", "Carlos Ulberg KOs Jiří Procházka on One Leg to Claim Light Heavyweight Gold – UFC 327 Highlights",
                             "https://www.lowkickmma.com/jiri-prochazka-vs-carlos-ulberg-highlights/", "2026-04-12",
                             "Craig Pekios"),
    "cage_rountree": src("Cageside Press", "UFC 320: Jiri Prochazka Storms Back, Stops Khalil Rountree Jr in Third",
                         "https://cagesidepress.com/2025/10/04/ufc-320-jiri-prochazka-storms-back-stops-khalil-rountree-jr-in-third",
                         "2025-10-04"),
    "yahoo_hill": src("Yahoo Sports (MMA Junkie)", "UFC 311 results: Jiri Prochazka ends entertaining scrap with TKO of Jamahal Hill",
                      "https://sports.yahoo.com/ufc-311-results-jiri-prochazka-050124091.html", "2025-01-19",
                      "Simon Samano"),
    # Stirling
    "cage_cutelaba": src("Cageside Press", "Navajo Stirling Survives Scare, Finishes Cutelaba at UFC Vegas 119",
                         "https://cagesidepress.com/2026/06/20/navajo-stirling-survives-scare-finishes-cutelaba-at-ufc-vegas-119/",
                         "2026-06-20", "Eddie Law"),
    "cage_blachowicz": src("Cageside Press",
                           "UFC Belgrade: Navajo Stirling Capitalizes on Short-Notice Opportunity Against Jan Blachowicz",
                           "https://cagesidepress.com/2026/08/01/ufc-belgrade-navajo-stirling-capitalizes-on-short-notice-opportunity-against-jan-blachowicz/",
                           "2026-08-01", "Brett Cagle"),
    # Sterling / Vallejos
    "sherdog_vallejos_pay": src("Sherdog", "Kevin Vallejos stunned by new UFC contract pay ahead of Aljamain Sterling fight",
                                "https://www.sherdog.com/news/news/Kevin-Vallejos-stunned-by-new-UFC-contract-pay-ahead-of-Aljamain-Sterling-fight-203423",
                                "2026-10-30", "Sayan Nag"),
    "sherdog_vallejos_troll": src("Sherdog", "Kevin Vallejos trolls Aljamain Sterling with Dan Miragliotta joke",
                                  "https://www.sherdog.com/news/news/Kevin-Vallejos-trolls-Aljamain-Sterling-with-Dan-Miragliotta-joke-203471",
                                  "2026-11-03", "Sayan Nag"),
    "sherdog_volk": src("Sherdog", "Alexander Volkanovski says Aljamain Sterling can jump ahead of Jean Silva",
                        "https://www.sherdog.com/news/news/Alexander-Volkanovski-says-Aljamain-Sterling-can-jump-ahead-of-Jean-Silva-203403",
                        "2026-10-29", "Sayan Nag"),
    "heavy_sterling_hour": src("Heavy.com", "Aljamain Sterling: UFC Gave Me 1-Hour Deadline for UFC Qatar",
                               "https://heavy.com/sports/ufc/aljamain-sterling-1-hour-ufc-qatar/", "2026-09-30",
                               "Adam Martin"),
    "yardbarker_striking": src("Yardbarker (BoxingNews)", "Sterling accepts Vallejos' 'pure striking' challenge",
                               "https://www.yardbarker.com/mma/articles/sterling_accepts_vallejos_pure_striking_challenge/s1_17349_44365560",
                               "2026-09-29"),
    "lowkick_zalal": src("LowKick MMA", "Aljamain Sterling Puts on Grappling Masterclass Against Youssef Zalal – UFC Vegas 116 Highlights",
                         "https://www.lowkickmma.com/aljamain-sterling-vs-zalal-ufc-vegas-116/", "2026-04-25",
                         "Craig Pekios"),
    "cage_shanghai": src("Cageside Press", "UFC Shanghai: Aljamain Sterling Outworks Low-Output Brian Ortega",
                         "https://cagesidepress.com/2025/08/23/ufc-shanghai-aljamain-sterling-outworks-low-output-brian-ortega",
                         "2025-08-23"),
    "cage_emmett": src("Cageside Press", "Kevin Vallejos Dominates Emmett, Scores Violent First-Round Finish",
                       "https://cagesidepress.com/2026/03/14/kevin-vallejos-dominates-emmett-scores-violent-first-round-finish",
                       "2026-03-14", "Nick Holt"),
    "cage_chikadze": src("Cageside Press", "Kevin Vallejos Stuns Giga Chikadze With Spinning Backfist KO",
                         "https://cagesidepress.com/2025/12/14/kevin-vallejos-stuns-giga-chikadze-with-spinning-backfist-ko",
                         "2025-12-14", "Brett Cagle"),
    # Hooker / Ortega
    "unc_hooker": src("Yahoo Sports (Uncrowned)",
                      "Dan Hooker on rushing into UFC Qatar fight after third straight loss: 'Surely I can beat Brian Ortega'",
                      "https://sports.yahoo.com/mma/article/dan-hooker-on-rushing-into-ufc-qatar-fight-after-third-straight-loss-surely-i-can-beat-brian-ortega-002848187.html",
                      "2026-11-05", "Drake Riggs"),
    "sherdog_hooker": src("Sherdog", "Dan Hooker calls Brian Ortega 'old' while explaining quick UFC return",
                          "https://www.sherdog.com/news/news/Dan-Hooker-calls-Brian-Ortega-old-while-explaining-quick-UFC-return-203495",
                          "2026-11-05", "Sayan Nag"),
    "cage_parnasse": src("Cageside Press", "UFC Paris: Salahdine Parnasse Arrives with Electrifying Finish of Dan Hooker",
                         "https://cagesidepress.com/2026/09/05/ufc-paris-salahdine-parnasse-arrives-with-electrifying-finish-of-dan-hooker/",
                         "2026-09-05", "Shawn Bitter"),
    "cage_bsd": src("Cageside Press", "UFC 325: Benoit Saint-Denis Puts Away Dan Hooker",
                    "https://cagesidepress.com/2026/01/31/ufc-325-benoit-saint-denis-puts-away-dan-hooker", "2026-01-31",
                    "Brett Cagle"),
    "sherdog_moicano_worst": src("Sherdog", "Renato Moicano calls Ortega vs. Hooker 'worst fight in the UFC'",
                                 "https://www.sherdog.com/news/news/Renato-Moicano-calls-Ortega-vs-Hooker-worst-fight-in-the-UFC-203390",
                                 "2026-10-28", "Sayan Nag"),
    "cage_ortega_326": src("Cageside Press", "Brian Ortega Announces He's Out of UFC 326",
                           "https://cagesidepress.com/2026/01/30/brian-ortega-announces-out-ufc-326", "2026-01-30",
                           "Jay Anderson"),
    "cage_ortega_331": src("Cageside Press", "With Brian Ortega Out, Renato Moicano Gets Tom Nolan in UFC Vegas 123 Headliner",
                           "https://cagesidepress.com/2026/09/14/brian-ortega-out-renato-moicano-gets-tom-nolan-in-ufc-vegas-123/",
                           "2026-09-14", "Jay Anderson"),
    # Horiguchi / Almabayev
    "cage_kape_hori": src("Cageside Press", "UFC Vegas 119: Manel Kape Gets Revenge in Come-From-Behind TKO of Kyoji Horiguchi",
                          "https://cagesidepress.com/2026/06/20/ufc-vegas-119-manel-kape-gets-revenge-in-come-from-behind-tko-of-kyoji-horiguchi/",
                          "2026-06-20", "Jay Anderson"),
    "cage_albazi": src("Cageside Press", "UFC Vegas 113: Kyoji Horiguchi Far Too Quick for Amir Albazi",
                       "https://cagesidepress.com/2026/02/07/ufc-vegas-113-kyoji-horiguchi-far-too-quick-for-amir-albazi",
                       "2026-02-07", "Jay Anderson"),
    "heavy_flyweight": src("Heavy.com", "High-Level Flyweight Bout Added to UFC Qatar",
                           "https://heavy.com/sports/ufc/high-level-flyweight-added-ufc-qatar/", "2026-09-24",
                           "Marcel Dorff"),
    "cage_baku": src("Cageside Press", "UFC Baku: Asu Almabayev Caps Off Stellar Showing Against Charles Johnson with Rare Submission",
                     "https://cagesidepress.com/2026/06/27/ufc-baku-asu-almabayev-caps-off-stellar-showing-against-charles-johnson-with-rare-submission/",
                     "2026-06-27", "Jay Anderson"),
    "cage_kape_alma": src("Cageside Press", "UFC Vegas 103: Eye Poke Undetected by Ref, Manel Kape Gets Stoppage Over Asu Almabayev",
                          "https://cagesidepress.com/2025/03/01/ufc-vegas-103-eye-poke-undetected-by-ref-manel-kape-gets-stoppage-over-asu-almabayev",
                          "2025-03-01", "Jay Anderson"),
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


# ---------------------------------------------------------------------------------------------------------------
report("Jiri Prochazka",
       "Former UFC light heavyweight champion from the Czech Republic (32-6-1, 6-3 UFC, age 34). A wild, high-output "
       "striker with huge finishing power: 31 of his 32 wins are stoppages. He headlines against unbeaten Navajo Stirling "
       "seven months after a first-round knockout loss to Carlos Ulberg for the vacant title. He opened as a slight "
       "underdog (+110 to -138, per MMA Junkie).",
       {"Striking": "Throws a lot (about 5.3 significant strikes a minute) with unusual angles, kicks and knees, and hits "
                    "very hard: 28 KO/TKO wins and about 0.75 knockdowns per 15 minutes. Against Ulberg he went after the "
                    "lead leg early and hurt it badly (LowKick MMA). Against Rountree he threw body kicks and a jump knee "
                    "early, then won a firefight in round three with knees, elbows and punches against the fence "
                    "(Cageside Press). Dropped Jamahal Hill with a left in round one and again in round three before the "
                    "finish (MMA Junkie).",
        "Grappling": "Rarely wrestles (about 0.6 takedowns per 15 minutes). Has three submission wins, the most famous a "
                     "submission of Glover Teixeira with 28 seconds left in their five-round title fight (R5, 4:32). "
                     "Off his back he is vulnerable: Teixeira landed 5 of 17 takedowns and had nearly ten minutes of "
                     "control in that fight.",
        "Defense": "The big hole. He absorbs about 4.6 significant strikes a minute and leaves openings when he attacks. "
                   "All three UFC losses were knockouts by counter-strikers: Alex Pereira R2 (2023), Pereira R2 at 0:13 "
                   "(2024) and Ulberg R1 (2026). Against Ulberg he had the champion compromised on one leg, chose to "
                   "trade instead of staying patient, and was dropped by a counter right and finished with ground strikes "
                   "(LowKick MMA). Career stoppage losses: five KO/TKO (three in R1, two in R2) and one R1 submission "
                   "(2013). He has never been stopped past round two.",
        "Pace & cardio": "A first-round finisher early in his career (21 R1 KO/TKO wins, mostly outside the UFC), but in the "
                         "UFC he has become a slow burner. All six UFC wins were stoppages: three in R2 (Oezdemir, Reyes, "
                         "Rakic), two in R3 (Hill, Rountree) and one in R5 (Teixeira). His last two wins were R3 "
                         "comebacks: against Rountree he lost R1-R2 and looked tired in R2 before stopping him at 3:04 of "
                         "R3 (Cageside). He keeps his power late. The danger for him is early: his losses come in R1-R2.",
        "Fight IQ": "Instinctive and unorthodox, comfortable taking risks to land. That cuts both ways: LowKick's reaction "
                    "piece blamed showboating and a choice to brawl for the Ulberg loss."},
       ["Volume striker with knockout power in all four limbs",
        "Slow burner in the UFC: all six UFC wins came in R2 or later, the last two in R3",
        "Wins firefights late against tired opponents (Hill, Rountree)",
        "Loses to sharp counter-punchers early: three UFC KO losses, all in R1-R2",
        "Wrestles little and can be held down by a strong grappler (Teixeira)"],
       ["Defensive gaps against a fast, accurate striker",
        "Coming off a first-round KO loss, his third KO loss in four fights against top opposition",
        "Age 34 with a lot of wear from wars",
        "Opponent is younger, unbeaten and favoured"],
       ["Counter him as he comes in; make him pay for wide shots",
        "Bank the first two rounds, then survive his R3 surge",
        "Mix in takedowns and top control; he does little wrestling himself"],
       [n("2026-09-29", "Booked to headline UFC Qatar in a five-round light heavyweight bout against Navajo Stirling.",
          "sherdog_card"),
        n("2026-11-05", "Opened as a +110 underdog to Stirling (-138), per MMA Junkie.", "yahoo_odds"),
        n("2026-04-11", "Knocked out by Carlos Ulberg at 3:45 of R1 at UFC 327 in a fight for the vacant title, after "
                        "badly hurting Ulberg's lead leg.", "lowkick_ulberg_hl")],
       ["sherdog_card", "cage_card", "yahoo_odds", "ufc_event", "lowkick_ulberg_react", "lowkick_ulberg_hl",
        "cage_rountree", "yahoo_hill"],
       "deep")

# ---------------------------------------------------------------------------------------------------------------
report("Navajo Stirling",
       "Unbeaten New Zealand light heavyweight (11-0, 6-0 UFC, age 29) from City Kickboxing and the Contender Series. "
       "He has stopped his last three opponents, including former champion Jan Blachowicz in round one in August. This is "
       "his first UFC main event and first scheduled five-rounder in the UFC; he opened as a -138 favourite.",
       {"Striking": "Clean, efficient kickboxer: about 5.9 significant strikes landed a minute against 2.7 absorbed, at 53% "
                    "accuracy. Works a sharp jab and one-twos, knees and spinning elbows (Cageside Press on the Cutelaba "
                    "fight). Dropped Blachowicz with a straight right and finished with elbows and punches at 2:56 of R1 "
                    "after being bloodied and hurt early (Cageside).",
        "Grappling": "Mainly a striker, but he can wrestle when needed: he out-controlled Ivan Erslan and Rodolfo Bellato in "
                     "decision wins (3 and 1 takedowns). Against Cutelaba he was taken down 5 of 7 times and caught in a "
                     "guillotine and a kimura, but reversed to top position and finished with ground strikes (R2, 3:23).",
        "Defense": "Hard to hit cleanly (about 62% striking defense) and solid takedown defense (74%), though Cutelaba showed "
                   "a strong wrestler can get him down repeatedly. He has never lost or been stopped, but he has been hurt: Blachowicz bloodied his nose and stunned him in R1.",
        "Pace & cardio": "Gets better as fights go on. Seven stoppage wins: three R1, three R2, one R3. In the UFC: R2 TKOs of "
                         "Bruno Lopes and Cutelaba, an R1 TKO of Blachowicz, and three clear three-round decisions earlier "
                         "(Tokkos, Erslan, Bellato). He lost R1 to Cutelaba and came back to finish him in R2. His only "
                         "five-round fight was a regional decision win in 2022; he has never gone past 15 minutes in the UFC.",
        "Fight IQ": "Patient; stays at range when in trouble instead of rushing (Cageside on Cutelaba). Took the Blachowicz "
                    "fight as a late replacement and won."},
       ["Patient jab-and-cross kickboxer who builds into finishes",
        "Three straight stoppages, two in R2 and one in R1",
        "Recovers well after a bad first round (Cutelaba, Blachowicz)",
        "Can be taken down by a strong wrestler but reverses and gets up"],
       ["Never been past three rounds in the UFC",
        "First main event and big step up in opponent power",
        "Has been hurt and taken down in his last two fights"],
       ["Take him down and make him work off his back early",
        "Pressure and land big in the first round, before he settles",
        "Drag him into rounds four and five, where he is unproven"],
       [n("2026-09-29", "Booked to headline UFC Qatar against former champion Jiri Prochazka.", "cage_card"),
        n("2026-11-05", "Opened as a -138 favourite over Prochazka (+110), per MMA Junkie.", "yahoo_odds"),
        n("2026-08-01", "Stopped Jan Blachowicz at 2:56 of R1 at UFC Belgrade as a replacement for Bogdan Guskov.",
          "cage_blachowicz"),
        n("2026-11-10", "UFC.com lists the main-event pair at No. 2 and No. 5 at light heavyweight.", "ufc_event")],
       ["sherdog_card", "cage_card", "yahoo_odds", "ufc_event", "cage_cutelaba", "cage_blachowicz"],
       "deep")

# ---------------------------------------------------------------------------------------------------------------
report("Aljamain Sterling",
       "Former UFC bantamweight champion (26-5, age 37), now 3-1 at featherweight after wins over Brian Ortega and Youssef "
       "Zalal. An elite back-taking grappler who wins mostly on the scorecards. Featherweight champion Alexander Volkanovski "
       "says Sterling deserves the next title shot if he beats Kevin Vallejos (Sherdog).",
       {"Striking": "Long, kick-heavy outside game. Used leg kicks to chop Ortega's lead leg and won almost every exchange in a "
                    "low-output fight (Cageside Press). He is accurate (58%) but not powerful: only three KO/TKO wins and about "
                    "0.04 knockdowns per 15 minutes. Mostly uses striking to set up takedowns.",
        "Grappling": "The main weapon. About 2.8 takedowns per 15 minutes and a third of total fight time in control. Against "
                     "Zalal he went 6 for 11 on takedowns with almost 14 minutes of control, took the back, used a body "
                     "triangle and won 49-45 x3 (LowKick MMA). Against Kattar: 8 of 13 takedowns and almost 11 minutes of "
                     "control. Eight submission wins, but none since 2020 (Sandhagen).",
        "Defense": "Both knockout losses came against fast power punchers: Marlon Moraes R1 (2017) and Sean O'Malley R2 (2023). "
                   "His other three losses were decisions (Caraway, Assuncao, Movsar Evloev). He was caught in a tight "
                   "guillotine by Zalal in R3 and lost top position that round (LowKick). Takedown defense is average (60%).",
        "Pace & cardio": "A grinder who goes the distance: 14 of 26 wins are decisions, and he is 6-1 in five-round fights "
                         "(the loss was the O'Malley KO). His last stoppage win was in 2022 (Dillashaw, R2). At featherweight "
                         "all three wins went 15 or 25 minutes. He holds his pace into rounds four and five (dominant R4-R5 "
                         "against Zalal), but in the Ortega fight he faded into R5, where Ortega clipped him and he was "
                         "warned for retreating (Cageside).",
        "Fight IQ": "Smart, patient, takes few risks. Gave Ortega a pause after a disputed eye poke when he might have pushed "
                    "for a finish (Cageside). Has publicly accepted Vallejos's call for a 'pure striking' fight, which "
                    "would mean leaving his best weapon behind if he means it."},
       ["Leg kicks and range work to set up takedowns",
        "Back-taker: body triangle and hand-fighting for the choke",
        "Wins on the cards: 14 decisions in 26 wins, no finish since 2022",
        "Loses when caught by fast power punchers (Moraes, O'Malley)"],
       ["Age 37",
        "Little power at 145 against a heavy hitter",
        "Knocked out twice by explosive strikers",
        "Guillotine risk on takedown entries"],
       ["Keep it standing and make him eat counters on entries",
        "Defend the first takedown and get back up fast; do not give the back",
        "Punish level changes with knees and front headlock threats"],
       [n("2026-09-30", "Says the UFC gave him one hour to accept Vallejos; he turned down Aaron Pico because Vallejos made "
                        "more sense for his title case (Heavy.com).", "heavy_sterling_hour"),
        n("2026-09-29", "Replied 'Can't wait!' to Vallejos predicting a 'pure striking' fight.", "yardbarker_striking"),
        n("2026-10-29", "Volkanovski said Sterling deserves the next shot at 145 if he beats Vallejos, and Jean Silva if not.",
          "sherdog_volk"),
        n("2026-11-03", "Criticised referee Dan Miragliotta's stand-up in the Moicano-Nolan main event; Vallejos joked he'd "
                        "been promised Miragliotta as referee.", "sherdog_vallejos_troll")],
       ["cage_card", "sherdog_card", "ufc_event", "heavy_sterling_hour", "yardbarker_striking", "sherdog_volk",
        "sherdog_vallejos_troll", "lowkick_zalal", "cage_shanghai"],
       "deep")

# ---------------------------------------------------------------------------------------------------------------
report("Kevin Vallejos",
       "Argentine featherweight (18-1, 4-0 UFC, age 25) and one of the hardest punchers in the division. He has finished "
       "three of four UFC opponents, most recently knocking out Josh Emmett in round one in March. This is a big step up "
       "against a former champion and an elite grappler. He signed a new UFC contract in October.",
       {"Striking": "Heavy, compact power: 13 KO/TKO wins and about 1.4 knockdowns per 15 minutes. Against Emmett he stepped "
                    "into the pocket with short hooks, uppercuts and elbows, slipped punches well, dropped him with a right "
                    "and finished with knees at 3:33 of R1 (Cageside Press). Knocked out Giga Chikadze with a spinning "
                    "backfist and elbows in R2 after Chikadze won much of R1 with kicks (Cageside).",
        "Grappling": "Rarely looks for takedowns (about 1 per 15 minutes). Two submission wins on the regional scene. Uses "
                     "the clinch against the fence to slow kickers (Chikadze).",
        "Defense": "Good takedown defense so far (81%; Danny Silva went 1 for 9). He gets hit a fair amount (about 3.5 "
                   "significant strikes absorbed a minute). Never stopped: his only loss is a three-round decision to Jean "
                   "Silva on the Contender Series in 2023. He has not yet faced a high-level wrestler or back-taker in the UFC.",
        "Pace & cardio": "Early finisher. Of 15 stoppage wins, 9 came in R1, 5 in R2 and 1 in R3 (a 2023 regional "
                         "submission). Three wins went the full 15 minutes, including a UFC decision over Danny Silva. He has "
                         "never fought past round three; his one scheduled five-rounder (Emmett) ended in R1. Can lose R1 "
                         "on volume and still finish in R2 (Chikadze).",
        "Fight IQ": "Confident and talkative: called for a 'pure striking' fight with Sterling and says a win earns him a "
                    "shot at Volkanovski (Sherdog)."},
       ["Pressure into the pocket with hooks, uppercuts and elbows",
        "Finishes early: 14 of 15 stoppage wins in R1-R2",
        "Good head movement on the way in",
        "Comes back from losing R1 on volume"],
       ["Untested against an elite wrestler and back-taker",
        "Never been past three rounds",
        "Absorbs a fair amount of strikes"],
       ["Take him down early and often; force him to defend the back",
        "Use range and kicks; avoid the pocket",
        "Drag him into deep water and see how he handles control time"],
       [n("2026-10-30", "Announced a new UFC contract and said he was stunned by the pay; said a win over Sterling gets him "
                        "Volkanovski.", "sherdog_vallejos_pay"),
        n("2026-09-29", "Predicted his fight with Sterling will be 'pure striking'; Sterling accepted.", "yardbarker_striking"),
        n("2026-03-14", "Knocked out Josh Emmett at 3:33 of R1 at UFC Vegas 114.", "cage_emmett")],
       ["cage_card", "sherdog_card", "ufc_event", "sherdog_vallejos_pay", "sherdog_vallejos_troll", "yardbarker_striking",
        "cage_emmett", "cage_chikadze", "sherdog_volk"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Dan Hooker",
       "New Zealand lightweight veteran (24-15, age 37) from City Kickboxing, on a three-fight losing streak, all three by "
       "stoppage inside two rounds. He returns 77 days after a first-round body-kick TKO loss to Salahdine Parnasse, "
       "having asked for Brian Ortega himself.",
       {"Striking": "Tall, rangy kickboxer with a varied kicking game and a good front kick (snapped Benoit Saint-Denis's head "
                    "back, per Cageside Press). Eleven KO/TKO wins, but only two since 2019 (James Vick 2019, Claudio Puelles 2022). Throws about 4.8 "
                    "significant strikes a minute and absorbs about the same. Parnasse checked most of his kicks.",
        "Grappling": "Dangerous guillotine and opportunistic submissions (seven sub wins, six in R1). Does not wrestle much "
                     "(about 0.6 takedowns per 15 minutes).",
        "Defense": "Durability is now the worry. Nine stoppage losses: five KO/TKO (R1 x3, R2, R3) and four submissions (R1, "
                   "R2 x3). The last three: Arman Tsarukyan sub R2 (2025), Saint-Denis TKO R2 after being mounted and taking "
                   "25 unanswered strikes (2026), and Parnasse TKO R1 from a body kick then a left hook (2026; Cageside). "
                   "Good wrestlers hold him down: Saint-Denis and Tsarukyan each controlled him for about six minutes.",
        "Pace & cardio": "Historically a fast starter as a finisher: 16 of 18 stoppage wins came in R1 or R2 (six R1 KOs, six R1 "
                         "subs, four R2 KOs). His wins in recent years have been close decisions (split wins over Jalin Turner "
                         "2023 and Mateusz Gamrot 2024). His last win was in August 2024. Lately he has been stopped early "
                         "rather than fading late.",
        "Fight IQ": "Experienced and outspoken. Says he had a strong camp for Parnasse he never got to show and took the quick "
                    "turnaround because he believes Ortega is beatable (Uncrowned, Sherdog)."},
       ["Kicks from range, front kicks up the middle",
        "Guillotine threat when opponents shoot",
        "Close decision winner in recent years",
        "Recently stopped early: three straight losses inside two rounds"],
       ["Durability after back-to-back stoppage losses in 2026",
        "Quick 77-day turnaround after a body-shot TKO",
        "Age 37, three straight losses"],
       ["Attack the body; Parnasse finished him with a body kick",
        "Take him down and work from top; he has been mounted and finished there",
        "Avoid shooting lazy takedowns into his guillotine"],
       [n("2026-11-05", "Returns 77 days after the Parnasse loss; said he took no serious injury from the body kick and asked "
                        "for Ortega himself.", "sherdog_hooker"),
        n("2026-11-05", "Said he expects Ortega, who has pulled out of two fights this year, to show up.", "unc_hooker"),
        n("2026-09-05", "Lost to UFC debutant Salahdine Parnasse by TKO at 2:35 of R1 in the UFC Paris main event.",
          "cage_parnasse")],
       ["cage_card", "sherdog_card", "ufc_event", "unc_hooker", "sherdog_hooker", "cage_parnasse", "cage_bsd",
        "sherdog_moicano_worst"],
       "deep")

# ---------------------------------------------------------------------------------------------------------------
report("Brian Ortega",
       "Two-time featherweight title challenger (16-5, 1 NC, age 36) making his UFC lightweight debut. He has lost four of his "
       "last five and has not fought since a lopsided decision loss to Aljamain Sterling in August 2025, about 15 months "
       "before this fight. He pulled out of two bouts with Renato Moicano this year (injuries in January, a cut over the "
       "eye in September).",
       {"Striking": "Low output and hittable: about 3.9 significant strikes landed a minute at 37% accuracy, and about 5.0 "
                    "absorbed. Against Sterling he landed single digits in R1 and took heavy leg kicks before finally landing "
                    "in R5 (Cageside Press). Has knocked out good fighters late (Frankie Edgar R1, Clay Guida and Thiago "
                    "Tavares R3).",
        "Grappling": "Elite jiu-jitsu, especially the guillotine. Eight submission wins, including Renato Moicano (2017, R3 "
                     "guillotine) and Cub Swanson. Takedown offense is poor (29%).",
        "Defense": "Takedown defense is weak (51%). Stopped twice: Max Holloway (TKO at the end of R4, 2018) and Yair "
                   "Rodriguez (R1, 2022). Three decision losses (Volkanovski, Diego Lopes, Sterling). Has taken a lot of "
                   "damage in long fights.",
        "Pace & cardio": "A late finisher: of 11 stoppage wins, six came in R3 (four subs, two KOs), one in R2 and four in R1. "
                         "He often loses early rounds and finds something late (R5 against Sterling, per Cageside). His wins have all come against tiring opponents, and he hasn't won since "
                         "February 2024.",
        "Fight IQ": "Patient to a fault; low early output costs him rounds. Weight and health are real concerns: he missed "
                    "featherweight for Sterling (153-pound catchweight; Cageside noted rumours he had been hospitalised) and "
                    "now moves up to 155."},
       ["Slow starter, dangerous late: six of 11 stoppage wins in R3",
        "Guillotine off opponents' takedown attempts",
        "Low striking output; loses rounds on volume",
        "Weak takedown defense"],
       ["Ring rust: about 15 months out by fight night",
        "Withdrew from two bouts in 2026",
        "First fight at 155 after a weight-cut problem at 145",
        "Four losses in last five"],
       ["Out-work him early with volume and leg kicks",
        "Don't shoot carelessly into his guillotine",
        "Keep pace high to bank rounds before his late push"],
       [n("2026-10-28", "Will make his UFC lightweight debut against Hooker (Sherdog).", "sherdog_moicano_worst"),
        n("2026-09-14", "Withdrew from the UFC 331 lightweight rematch with Moicano after a cut; his second withdrawal from "
                        "that fight.", "cage_ortega_331"),
        n("2026-01-30", "Pulled out of UFC 326 with accumulated injuries; said no surgery was needed.", "cage_ortega_326")],
       ["cage_card", "sherdog_card", "ufc_event", "sherdog_moicano_worst", "cage_ortega_326", "cage_ortega_331",
        "cage_shanghai", "unc_hooker", "sherdog_hooker"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Kyoji Horiguchi",
       "Japanese flyweight veteran (36-6, 1 NC, age 36) and former Bellator and Rizin champion, 2-1 since his UFC return. "
       "Fast, explosive karate-based striker. Lost his last fight to Manel Kape by R3 TKO in June after leading for most "
       "of it. UFC.com lists the pair at No. 5 and No. 7; Heavy.com has Horiguchi No. 5 in the media rankings.",
       {"Striking": "Very fast in-and-out blitzer with stance switches, an overhand right and a sharp left, and leg and body "
                    "kicks. Out-landed Amir Albazi 73-16 with jumping knees in R3 (Cageside Press). 15 KO/TKO wins.",
        "Grappling": "Takes down opponents late in rounds and grinds from top: put Kape on his back in R1 and R2 and landed "
                     "elbows (Cageside). Six submission wins, most recently Tagir Ulanbekov (R3, 2025).",
        "Defense": "Hard to hit (about 67% striking defense) and tough to take down (76%): stopped all seven Albazi takedown "
                   "attempts. But he has been knocked out three times since 2019: Kai Asakura R1 (2019), Sergio Pettis R4 "
                   "(2021) and Kape R3 (2026), where a right hand hurt him and an uppercut finished "
                   "him (Cageside).",
        "Pace & cardio": "Keeps a high pace for 15 minutes. Of 21 stoppage wins, 10 came in R1, 4 KOs and 3 subs in R2, 3 "
                         "subs in R3 and one R5 KO. Fifteen wins were decisions. Five-round record is mixed: 2-4 counting the "
                         "Kape fight. His three recent KO losses came in R1, R3 and R4, so the danger stays live late.",
        "Fight IQ": "Experienced at the top level. Fights in bursts and resets well. Against Kape he was clearly winning and "
                    "got caught in an exchange."},
       ["Explosive blitzes with stance switches",
        "Late-round takedowns to steal rounds",
        "Excellent takedown defense",
        "Recent KO losses to counter-punchers when trading"],
       ["Three KO losses since 2019",
        "Age 36 at flyweight",
        "Coming off a stoppage loss"],
       ["Counter his blitz entries",
        "Chain wrestle; he defends single attempts well",
        "Keep it close into R3"],
       [n("2026-09-24", "Booked against Asu Almabayev in a three-round flyweight fight at UFC Qatar.", "heavy_flyweight"),
        n("2026-06-20", "Lost to Manel Kape by TKO at 2:42 of R3 after controlling R1-R2.", "cage_kape_hori")],
       ["cage_card", "sherdog_card", "ufc_event", "heavy_flyweight", "cage_kape_hori", "cage_albazi"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Asu Almabayev",
       "Kazakh flyweight (24-3, 7-1 UFC, age 33) and one of the heaviest grapplers in the division. He has won three "
       "straight since his only UFC loss, a short-notice main-event TKO by Manel Kape in 2025, and submitted Charles "
       "Johnson with a rare Suloev stretch in June.",
       {"Striking": "Functional, not a weapon: about 2.7 significant strikes a minute. Uses inside leg kicks and overhand "
                    "rights to close distance (Cageside Press).",
        "Grappling": "Elite chain wrestler: about 4.2 takedowns per 15 minutes and control for more than 40% of fight time. "
                     "Had about nine and a half minutes of control against CJ Vergara, over 11 against Jose Johnson and "
                     "almost 9 against Charles Johnson. Takes the back and finishes there: 11 submission wins. Against Johnson he took him down "
                     "in R2 and R3, took the back and finished with a Suloev stretch at 3:33 of R3 (Cageside).",
        "Defense": "Takedown defense is only average (55%); Alex Perez took him down three times. Both career stoppage losses "
                   "were R3 TKOs: Tagir Ulanbekov (2017) and Kape (2025). Against Kape his takedowns were stuffed (0 for 6 in "
                   "our data), he took knees and elbows on entries, and he was stopped after turning away with an eye problem "
                   "(Cageside).",
        "Pace & cardio": "A grinder who gets stronger. Of 14 stoppage wins, 4 came in R1, 7 in R2 and 3 in R3; his last two "
                         "UFC finishes were both R3 submissions (Perez, Johnson). Ten wins went the distance. His only "
                         "losses came in R3 or on the cards, so he tends to fade only when he can't get the fight down.",
        "Fight IQ": "Patient and methodical. When the takedown isn't there (Kape), he has no strong plan B on the feet."},
       ["Chain wrestling into back control",
        "Late finisher: last two UFC finishes in R3",
        "Huge control time",
        "Struggles when takedowns are stuffed"],
       ["Facing a fighter with strong takedown defense",
        "Striking is limited",
        "Both stoppage losses came in R3"],
       ["Stuff the first takedowns and punish entries with knees",
        "Make him strike for long spells",
        "Get up fast if taken down"],
       [n("2026-09-24", "Booked against Kyoji Horiguchi at UFC Qatar; Heavy.com lists him No. 7 in the media rankings and on a "
                        "three-fight win streak.", "heavy_flyweight"),
        n("2026-06-27", "Submitted Charles Johnson with a Suloev stretch at 3:33 of R3 at UFC Baku.", "cage_baku")],
       ["cage_card", "sherdog_card", "ufc_event", "heavy_flyweight", "cage_baku", "cage_kape_alma"],
       "moderate")


out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
