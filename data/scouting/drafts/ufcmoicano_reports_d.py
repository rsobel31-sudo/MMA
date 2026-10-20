"""Scouting reports for UFC Fight Night: Moicano vs. Nolan (UFC Vegas 123, 2026-10-31), batch D, written 2026-10-20.

Fighters: Dakota Hope, Ode Osbourne, Cody Durden, Randy Brown, Mickey Gall, Zachary Reese.
Fight-week previews aren't out yet: these draw on recent-fight recaps, booking news and our verified records
(round-by-round counts below come from data/verified/fights.csv). Refresh with the previews on Tuesday/Friday.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports"
UPDATED = "2026-10-20T18:00:00+00:00"
EVENT = "UFC Fight Night: Moicano vs. Nolan"


def src(outlet, author, title, url, date):
    return {"outlet": outlet, "author": author, "title": title, "url": url, "date": date}


SRC = {
    # Card / bookings
    "junkie_card": src("MMA Junkie (via Yahoo Sports)", "Nolan King", "UFC books Mickey Gall vs. Zach Reese",
                       "https://sports.yahoo.com/articles/ufc-books-mickey-gall-vs-012533985.html", "2026-10-17"),
    "heavy_hope": src("Heavy", "Marcel Dorff", "Francis Marshall Draws New Opponent for UFC Halloween Event",
                      "https://heavy.com/sports/ufc/francis-marshall-new-opponent-ufc-halloween/", "2026-10-08"),
    "es_hope": src("EssentiallySports", "Jaideep R Unnithan",
                   "Matchmakers scramble for replacements as multiple fighters pull out from UFC 334 and Vegas 123",
                   "https://www.essentiallysports.com/ufc-mma-news-matchmakers-scramble-for-replacements-as-multiple-fighters-pull-out-from-ufc-334-and-vegas-123/",
                   "2026-10-09"),
    "heavy_smith": src("Heavy", "Marcel Dorff", "Jacobe Smith Accepts Short Notice Fight for UFC Vegas 123",
                       "https://heavy.com/sports/ufc/jacobe-smith-accepts-ufc-vegas-123/", "2026-10-19"),
    "yahoo_smith": src("Yahoo Sports (republished from Heavy)", "Marcel Dorff", "Jacobe Smith Accepts Short Notice Fight for UFC Vegas 123",
                       "https://sports.yahoo.com/articles/jacobe-smith-accepts-short-notice-053421856.html", "2026-10-20"),
    "es_leal": src("EssentiallySports", "Biplob Chakraborty",
                   "Undisclosed injury results in first fight cancelation for Renato Moicano-headlined card",
                   "https://www.essentiallysports.com/ufc-mma-news-undisclosed-injury-results-in-first-fight-cancelation-for-renato-moicano-headlined-card/",
                   "2026-10-03"),
    "bn_osbourne_out": src("Boxing News", "Tom Rashid", "Alessandro Costa replaces injured Ode Osbourne at UFC 329",
                           "https://boxingnews.com/news/alessandro-costa-replaces-osbourne-ufc-329", "2026-07-02"),
    "bn_gall_med": src("Boxing News", "Tom Rashid", "UFC Pulls Mickey Gall From Return Over Medical Issue",
                       "https://boxingnews.com/news/ufc-pulls-mickey-gall-medical-issue/", "2026-09-25"),
    "cage_v121_losers": src("Cageside Press", "", "What's Next: UFC Vegas 121 Losers",
                            "https://cagesidepress.com/2026/09/28/whats-next-ufc-vegas-121-losers/", "2026-09-28"),
    "cage_perth_losers": src("Cageside Press", "", "What's Next: UFC Perth Losers",
                             "https://cagesidepress.com/2026/05/04/whats-next-ufc-perth-losers-2/", "2026-05-04"),
    # Hope
    "cage_hope": src("Cageside Press", "Shawn Bitter", "UFC Vegas 115: Kai Kamaka III Victorious in Return, Beats Dakota Hope",
                     "https://cagesidepress.com/2026/04/04/ufc-vegas-115-kai-kamaka-iii-victorious-in-return-beats-dakota-hope/", "2026-04-04"),
    # Osbourne
    "cage_idiris": src("Cageside Press", "Nick Holt", "UFC Houston: Alibi Idiris Notches First Octagon Win, Moves Past Ode Osbourne",
                       "https://cagesidepress.com/2026/02/21/ufc-houston-alibi-idiris-notches-first-octagon-win-moves-past-ode-osbourne", "2026-02-21"),
    "sherdog_houston": src("Sherdog", "", "Preview: UFC Houston Prelims",
                           "https://www.sherdog.com/news/articles/2/Preview-UFC-Houston-Prelims-200165", "2026-02-18"),
    "elbalad_idiris": src("El-Balad", "", "UFC Flyweight Alibi Idiris Suspended for One Year After Drug Test Failure",
                          "https://www.el-balad.com/16898399", "2026"),
    "cage_gurule": src("Cageside Press", "", "UFC Vegas 105: Ode Osbourne Stops Newcomer Luis Gurule",
                       "https://cagesidepress.com/2025/04/05/ufc-vegas-105-ode-osbourne-stops-newcomer-luis-gurule", "2025-04-05"),
    "cage_erceg": src("Cageside Press", "", "Steve Erceg Makes Adjustments, Takes Decision Over Osbourne",
                      "https://cagesidepress.com/2025/08/09/steve-erceg-makes-adjustments-takes-decision-over-osbourne", "2025-08-09"),
    # Durden
    "cage_costa": src("Cageside Press", "", "Alessandro Costa Submits Durden in Second Round at UFC 329",
                      "https://cagesidepress.com/2026/07/11/alessandro-costa-submits-durden-in-second-round-at-ufc-329/", "2026-07-11"),
    "cage_filho": src("Cageside Press", "", "UFC Vegas 116: Cody Durden Secures Much-Needed Win Over Jafel Filho",
                      "https://cagesidepress.com/2026/04/25/ufc-vegas-116-cody-durden-secures-much-needed-win-over-jafel-filho/", "2026-04-25"),
    "cage_v116_losers": src("Cageside Press", "", "What's Next: UFC Vegas 116 Losers",
                            "https://cagesidepress.com/2026/04/27/whats-next-ufc-vegas-116-losers/", "2026-04-27"),
    # Brown
    "sherdog_327": src("Sherdog", "Tom Feely", "Preview: UFC 327 Prelims",
                       "https://www.sherdog.com/news/articles/2/Preview-UFC-327-prelims-200764", "2026-04-08"),
    "cage_holland": src("Cageside Press", "Eddie Law", "Kevin Holland Takes Decision Win After Fun Scrap With Brown",
                        "https://cagesidepress.com/2026/04/11/kevin-holland-takes-decision-win-after-fun-scrap-with-brown", "2026-04-11"),
    "lowkick_bonfim": src("LowKick MMA", "", "UFC Vegas 111 Power Rankings: Rating The Main Card Winners In Las Vegas",
                          "https://www.lowkickmma.com/ufc-vegas-111-power-rankings-rating-the-main-card-winners-in-las-vegas/", "2025-11-10"),
    "cage_dalby": src("Cageside Press", "", "Randy Brown Shuts Nicolas Dalby's Lights Off at UFC Kansas City",
                      "https://cagesidepress.com/2025/04/26/randy-brown-shuts-nicolas-dalbys-lights-off-at-ufc-kansas-city", "2025-04-26"),
    # Gall
    "cage_brahimaj": src("Cageside Press", "Jay Anderson", "UFC 309: Ramiz Brahimaj KOs Mickey Gall Inside of a Round",
                         "https://cagesidepress.com/2024/11/16/ufc-309-ramiz-brahimaj-kos-mickey-gall-inside-of-a-round", "2024-11-16"),
    # Reese
    "cage_gandra": src("Cageside Press", "Nick Holt", "UFC 329: Ryan Gandra Puts Away Zach Reese Early, Violently",
                       "https://cagesidepress.com/2026/07/11/ufc-329-ryan-gandra-puts-away-zach-reese-early-violently/", "2026-07-11"),
    "lowkick_pereira": src("LowKick MMA", "", "Michel Pereira Bloodies Zachary Reese for 32nd Career Victory - UFC Houston Highlights",
                           "https://www.lowkickmma.com/michel-pereira-bloodies-zachary-reese/", "2026-02-21"),
    "lowkick_mcvey": src("LowKick MMA", "", "Zach Reese Taps Out Jackson McVey on Short Notice - UFC Vegas 111 Highlights",
                         "https://www.lowkickmma.com/jackson-mcvey-vs-zach-reese-highlights/", "2025-11-08"),
    "bjpenn_329bets": src("BJPenn.com", "", "UFC 329 Best Bets: Paddy Pimblett bounceback, quick finishes lead cash-ins",
                          "https://www.bjpenn.com/mma-news/paddy-pimblett/ufc-329-best-bets-paddy-pimblett/", "2026-07-08"),
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


report("Dakota Hope",
       "Aggressive, powerful regional finisher (11-2; former Peak Fighting featherweight champion) whose UFC debut was a short-notice "
       "split-decision loss to Kai Kamaka III at lightweight in April. Back down to featherweight and again on short notice, replacing "
       "Gaston Bolanos against Francis Marshall. Never been stopped.",
       {"Striking": "Front-foot pressure: backs opponents to the cage with short punches, body knees and clinch elbows (Cageside Press). "
                    "Dropped Kamaka with a right hand in R1 and stunned him with a right hook in R2. Busy (106 of 258 significant strikes "
                    "against Kamaka) but loose: Kamaka landed 105 of 159, so he gets hit a lot for the volume he throws. "
                    "Five R1 knockouts on the regionals; Heavy calls it \"vicious power\".",
        "Grappling": "Mostly a striker who clinches. Has a fifth-round submission (Patrick Connors, Peak Fighting title fight) and "
                     "landed a late takedown on Kamaka, but takedowns are not his main route.",
        "Defense": "Durability is good: 13 pro fights and never stopped (both losses are decisions). Defense is the issue: he walks "
                   "through return fire, and Kamaka out-worked him on the body and with counters late.",
        "Pace & cardio": "Fast starter. All five KO wins came in R1 (0:15 to 1:59); his only submission came in R5. The other five wins "
                         "and both losses went the distance. He has gone 25 minutes three times on the regionals, yet against Kamaka "
                         "his pace dipped in R2 and he was visibly tired in R3, leaning on the clinch and overreaching (Cageside Press) - "
                         "he won R1 and lost the fight over R2-R3. Short notice twice in a row is worth keeping in mind for R3.",
        "Fight IQ": "Commits to pressure and finishing; when the early storm doesn't land, he hasn't shown a plan B beyond more of the "
                    "same. Took both UFC fights on short notice."},
       ["Early pressure and power: wins R1, five R1 KO wins",
        "If it goes long he tends to fade; decision record 5-2",
        "Never finished: both losses are decisions (Bosnick, Kamaka split)",
        "Clinch work against the fence: knees to the body, elbows"],
       ["R2-R3 cardio at UFC pace (faded vs Kamaka)",
        "Absorbs a lot of strikes: 4.95 absorbed a minute",
        "Second short-notice booking, and a cut back down to featherweight after debuting at lightweight"],
       ["Survive the first five minutes; make him work at range",
        "Body work and counters as he comes forward - Kamaka's recipe",
        "Bank R2 and R3 once his pace drops"],
       [n("2026-10-08", "Steps in for Gaston Bolanos (eyebrow cut in training) against Francis Marshall at featherweight; the official "
                        "UFC page still listed Bolanos on Oct 20. Sources disagree on weight class (featherweight per Heavy, "
                        "bantamweight in some listings).", "heavy_hope"),
        n("2026-04-04", "Lost UFC debut to Kai Kamaka III by split decision (29-28, 28-29, 29-28) at lightweight after dropping him in R1.",
          "cage_hope")],
       ["heavy_hope", "es_hope", "cage_hope", "junkie_card"], "moderate")

report("Ode Osbourne",
       "Long, explosive Jamaican flyweight (13-9, 2 NC; 5-7, 1 NC in the UFC) with real one-punch power (three UFC knockouts) but chronic trouble once he's taken down. 1-3 (1 NC) in his last five; his February "
       "decision loss to Alibi Idiris was overturned to a no contest after Idiris tested positive for a diuretic.",
       {"Striking": "Sharp, fast counter-puncher with a 185 cm reach (very long for 125). Fight-ending left hand: dropped and finished "
                    "Luis Gurule in R2 with a counter left, KO'd Jerome Rivera in 26 seconds and Zarrukh Adashev in 61. Low volume "
                    "(about 2.7 significant strikes a minute) and waits for one big shot; Cageside Press said he got overeager with power "
                    "shots against Idiris and lost his rhythm.",
        "Grappling": "The hole. Taken down in all three rounds by Idiris (5 of 15), out-controlled by Erceg (nearly 5 minutes, ended in "
                     "mount and a back-take), Ronaldo Rodriguez (over 9 minutes of control) and Gurule in R1. Four submission losses "
                     "(Calvo, Kelleher, Almabayev, Filho). Offensive submissions mostly on the regionals.",
        "Defense": "Stopped six times: four submissions and two knockouts (Kape, Tyson Nam). Hard to hit cleanly at range, but takedown "
                   "defense is about 61% and he's poor from his back.",
        "Pace & cardio": "Front-loaded. Ten stoppage wins: eight in R1, two in R2 (Lee, Gurule) - none later. Six stoppage losses: five in R1 "
                         "(Calvo, Kelleher, Kape, Nam, Filho), one in R2 (Almabayev). Decisions: 3-3. Against Erceg he hurt him early "
                         "(Erceg took a knee) and then lost the later rounds to grappling; vs Idiris he was best in R2 then got taken down again "
                         "in R3. Danger is highest for both men in the first 7-8 minutes; if it goes late, the grappler usually takes it.",
        "Fight IQ": "Frustrating by reputation: Sherdog calls him one of the UFC's more frustrating fighters, with top-15 tools but too many "
                    "losses. Flexible with weight (has fought at 125, 135 and 145) and takes short-notice fights (Erceg)."},
       ["Counter left hand: three UFC KOs, two in R1 and Gurule in R2",
        "Loses when wrestled: repeated takedowns and long control in the Rodriguez, Erceg and Idiris fights",
        "All stoppages either way have come in R1-R2",
        "Slow starts in some fights (Idiris put him on a knee early) but dangerous until the fight goes to the mat"],
       ["Takedown defense and bottom game against a wrestler like Durden",
        "Age 35 and a July withdrawal through injury (undisclosed)",
        "Submission losses: four, including Filho and Almabayev"],
       ["Shoot early and often; chain takedowns even if the first few fail",
        "Keep him on the fence and in the clinch, away from the counter left",
        "Take his back in scrambles - he gives it up under pressure (Erceg)"],
       [n("2026-07-02", "Withdrew from his UFC 329 bout with Cody Durden through an undisclosed injury after an eight-week camp; Alessandro "
                        "Costa replaced him (Boxing News, citing Sherdog).", "bn_osbourne_out"),
        n("2026-02-21", "Lost a unanimous decision to Alibi Idiris at UFC Houston; the result was later overturned to a no contest after "
                        "Idiris tested positive for hydrochlorothiazide (our data records NC).", "elbalad_idiris"),
        n("2026-10-17", "Rebooked against Cody Durden at flyweight for Oct 31.", "junkie_card")],
       ["sherdog_houston", "cage_idiris", "elbalad_idiris", "cage_gurule", "cage_erceg", "bn_osbourne_out", "junkie_card",
        "cage_perth_losers"], "good")

report("Cody Durden",
       "Grinding ATT Atlanta wrestler (18-11-1; 7-9-1 UFC) who wins by takedowns and top control and loses when caught in scrambles or "
       "out-struck. 1-4 in his last five: snapped a four-fight skid by out-grinding Jafel Filho on six days' notice, then was "
       "choked out by Alessandro Costa in R2 at UFC 329 after Ode Osbourne withdrew.",
       {"Striking": "Functional, not dangerous: about 3.5 significant strikes landed a minute and 3.9 absorbed, with just one UFC knockdown "
                    "(J.P. Buys). Out-landed 165-70 by Joshua Van. His striking exists to get to the clinch; a mistimed high kick set up "
                    "the Costa loss (Cageside Press).",
        "Grappling": "The weapon: about 3.1 takedowns per 15 minutes and 51% accuracy. Long control wins over Carlos Mota (12+ min), "
                     "Charles Johnson (11 of 18 takedowns) and Jake Hadley; went 5 for 5 on Filho. But his scrambles are leaky: submitted "
                     "six times (Hollis, Flick, Mokaev, Ulanbekov, Nascimento, Costa); Costa took his back after he slipped on a missed kick.",
        "Defense": "Stopped eight times: six submissions and two knockouts (Bruno Silva, Jose Ochoa). Takedown defense about 55%; "
                   "Tumendemberel went 4 for 4 on him in March.",
        "Pace & cardio": "Slow burner who wins late but is finished in R2. Twelve stoppage wins (nine R1, two R2, one R3), but in the UFC "
                         "only two (Buys R1, Schnell R2); five of his seven UFC wins are decisions, and he took R3 against Filho as "
                         "Filho faded (Cageside Press; Rotowire also credits his conditioning). Of eight stoppage losses, six came in R2 "
                         "(Hollis, Ulanbekov, Silva, Ochoa, Nascimento, Costa) and two in R1 (Flick, Mokaev). Every UFC stoppage loss "
                         "since 2023 has come in R2.",
        "Fight IQ": "Knows his lane and sticks to wrestling when it works, but gets drawn into exchanges and loose scrambles. Busy "
                    "(takes short-notice fights) and announced a new four-fight UFC deal on Instagram in June 2026 (per the Covington News)."},
       ["Wins on volume of takedowns and control; decisions are his UFC win path (5 of 7)",
        "Gets stronger as opponents tire (Filho R3)",
        "Six of eight stoppage losses in R2, including the last five",
        "Gives up the back/neck in scrambles"],
       ["Age 36 and 1-4 in his last five",
        "Submission defense in scrambles",
        "Chin against hard counter-punchers (Silva, Ochoa)"],
       ["Defend the first takedown and punish the re-shot with counters",
        "Hunt the neck and back when he shoots or scrambles",
        "Make R2 hurt - that's where he breaks"],
       [n("2026-07-11", "Submitted by Alessandro Costa (RNC, 2:19 of R2) after Costa replaced the injured Ode Osbourne.", "cage_costa"),
        n("2026-04-25", "Beat Jafel Filho by unanimous decision on six days' notice, snapping a four-fight losing streak.", "cage_filho"),
        n("2026-10-17", "Rebooked against Ode Osbourne at flyweight for Oct 31 - the bout scrapped at UFC 329.", "junkie_card")],
       ["cage_costa", "cage_filho", "cage_v116_losers", "cage_perth_losers", "bn_osbourne_out", "junkie_card"], "good")

report("Randy Brown",
       "Long (198 cm reach), versatile Jamaican-American welterweight veteran (20-8; 14-8 UFC), age 36, on a two-fight skid (Bonfim TKO, "
       "Holland decision). Was booked against Carlos Leal, who withdrew injured; now faces unbeaten Jacobe Smith on less than two weeks' "
       "notice for Smith.",
       {"Striking": "Rangy kickboxer with real power: dropped Dalby face-first in R2 after breaking his nose in R1 (Cageside Press), "
                    "buckled Kevin Holland with a left hook in R1. About 4.6 significant strikes a minute at 45%. Sherdog calls him "
                    "\"capable of anything\" but says he can cycle through ideas without committing to one.",
        "Grappling": "Dangerous off his back (elbows, triangle threat and up-kicks vs Holland; submissions of Warlley Alves and Alex Oliveira). "
                     "Takedown offense is poor (0 for 4 vs Holland; about 26% career), and he has spent long stretches under wrestlers "
                     "(Battle, Zaleski, Belal).",
        "Defense": "Durability is the worry (Sherdog). Stopped five times: three KO/TKOs (Price, Luque, Bonfim - all R2) and two submissions "
                   "(Graves R2, Della Maddalena R1). Dropped twice by Luque, once each by Della Maddalena, Dalby, Bonfim and Kalinn Williams, "
                   "and Holland dropped him in R1 (Cageside Press; our data records no knockdown in that fight). Calf kicks have hurt "
                   "him lately (Bonfim, Holland). Sources disagree on the Bonfim finish: a knee as he dipped to change levels (LowKick), "
                   "off the clinch exit (Cageside), or a flying knee (Heavy).",
        "Pace & cardio": "Middle-rounds finisher. Thirteen stoppage wins: four R1, seven R2, two R3 (Montano, Barberena). Of five stoppage "
                         "losses, four were in R2 and one in R1. Decisions: 7-3 (lost to Belal, Battle split, Holland). Can go 15 minutes "
                         "at a decent pace but R3 against Holland was a tired clinch battle (LowKick). The pattern: feels it out in R1, "
                         "the fight swings in R2 either way.",
        "Fight IQ": "Experienced and patient at his best (the Dalby range game). Can lose focus or wander between game plans; was warned "
                    "for grabbing the fence vs Holland."},
       ["Range kickboxing with a long jab and right hand",
        "R2 is the swing round: 7 of 13 stoppage wins and 4 of 5 stoppage losses",
        "Dangerous guard: up-kicks, elbows and triangles off his back",
        "Struggles against wrestlers who can hold him down (Battle, Belal)"],
       ["Durability at 36: stopped in R2 by Bonfim and dropped by Holland",
        "Two straight losses; hasn't won since April 2025",
        "Late opponent change: prepared for Leal, now a younger undefeated finisher"],
       ["Kick the lead leg early - Holland and Bonfim both did",
        "Close the distance and hold him on the fence or mat rather than kickbox at his range",
        "Push the pace in R2, where he's most vulnerable"],
       [n("2026-10-02", "Carlos Leal withdrew from their Oct 31 bout with an undisclosed injury (AG Fight, via EssentiallySports).", "es_leal"),
        n("2026-10-19", "Unbeaten Jacobe Smith (13-0) replaces Leal, 28 days after his Oct 3 KO of Bruce Whitehead; Heavy says it's on the "
                        "main card.", "heavy_smith"),
        n("2026-04-11", "Lost a unanimous decision to Kevin Holland (30-27 x3) at UFC 327 after buckling him early.", "cage_holland")],
       ["sherdog_327", "cage_holland", "lowkick_bonfim", "cage_dalby", "es_leal", "heavy_smith", "yahoo_smith"], "good")

report("Mickey Gall",
       "Jiu-jitsu-first veteran (7-7; 6-7 UFC), 34-35, on a four-fight losing streak with no win since July 2021 and no fight since a R1 "
       "knockout loss to Ramiz Brahimaj in November 2024. Was pulled from a September return for failing medicals; now cleared and "
       "moving up to middleweight against Zach Reese.",
       {"Striking": "Upright and hittable: absorbs about 5.5 significant strikes a minute and lands about 4.3. Will throw a jab-right "
                    "(stung Brahimaj with one per Cageside Press) but loses most kickboxing exchanges with real strikers.",
        "Grappling": "All six of his stoppage wins are submissions (five in R1, Northcutt in R2), mostly rear-naked chokes off scrambles "
                     "or a back-take. Takedown entries are weak (about 36%), so he needs opponents to grapple with him or give up "
                     "a position.",
        "Defense": "Stopped three times, all by strikes: Diego Sanchez (R2, after being taken down and controlled), Mike Malott (R1), "
                   "Brahimaj (R1). Never submitted. Takedown defense about 45%.",
        "Pace & cardio": "Early or not at all: every finish win came by R2 (five R1). Once past R1 he's 1-4 in decisions (beat Touahri; lost to "
                         "Brown, Perry, Morono, Hafez). His KO losses came R1 (2) and R2 (1). Not a late-rounds fighter.",
        "Fight IQ": "Reads submission chances quickly, but has tended to stand and trade when takedowns aren't there."},
       ["Back-takes and rear-naked chokes in R1",
        "Loses decisions when he can't get the fight down",
        "Knocked out in R1 in two of his last three"],
       ["Nearly two years out, a medical flag in September, and a first fight at middleweight",
        "Chin and defense: three KO losses, two in R1",
        "Four straight losses"],
       ["Stay on the feet and throw at volume; he gets hit a lot",
        "Don't give up the back in scrambles; stay heavy on top or stand",
        "Pressure early - he has not looked better as fights go on"],
       [n("2026-09-24", "Pulled from his UFC Vegas 121 return against Sedriques Dumas after pre-fight medicals flagged an undisclosed issue; "
                        "Gall called the fix a simple procedure.", "bn_gall_med"),
        n("2026-09-28", "Cageside Press said the Dumas bout would have been his first at middleweight; Boxing News listed it at welterweight.",
          "cage_v121_losers"),
        n("2026-10-17", "Cleared and booked against Zach Reese at middleweight for Oct 31 (MMA Junkie, two sources).", "junkie_card")],
       ["junkie_card", "bn_gall_med", "cage_v121_losers", "cage_brahimaj"], "moderate")

report("Zachary Reese",
       "Tall Texan finisher (10-4, 1 NC; 4-4 UFC) who lives in the first round: seven R1 stoppage wins and all three of his losses "
       "by stoppage came in R1. Comes off back-to-back losses - a disputed split decision to Michel Pereira and a 75-second TKO by "
       "Ryan Gandra.",
       {"Striking": "Long middleweight (196 cm reach) with explosive early offense: 20-second KO of Julian Marquez; mixes body kicks and "
                    "hooks (Cageside Press). Out-landed Pereira 74-63 and Todorovic 50-35. Hands can drop as he throws - Gandra's dipping "
                    "left hook over his guard ended it.",
        "Grappling": "Opportunistic submissions: rear-naked choke of Jackson McVey in R2 on less than a week's notice (3 for 3 on takedowns), "
                     "R1 subs of Aronov (DWCS) and Phillips. Gets taken down and controlled when he can't keep separation (Todorovic, "
                     "Bekoev, Brundage).",
        "Defense": "The weakness. Takedown defense about 47%; finished by Brundage (R1, after a takedown) and Bekoev (R1, ground strikes after "
                   "over two minutes of control), and dropped by Gandra (R1). Sources say Pereira scored an early knockdown in February; "
                   "our data records none.",
        "Pace & cardio": "Fast starter, both ways. Eight stoppage wins: seven R1, one R2 (McVey). Three stoppage losses, all R1 (Brundage "
                         "1:49, Bekoev 3:04, Gandra 1:15). Has gone the distance three times (2-1), finishing strongly against Pereira "
                         "per Rotowire, so the tank holds up when he survives R1. BJPenn.com: \"tendency to get off to fast starts\".",
        "Fight IQ": "Takes short-notice fights and accepts exchanges early; has been caught by counters when aggressive."},
       ["R1 is decisive either way: 7 R1 stoppage wins, 3 R1 stoppage losses",
        "Rear-naked choke finishes after takedowns",
        "Competitive over 15 minutes when it gets there (Todorovic win, Pereira split)"],
       ["Defensive lapses early: finished in R1 three times",
        "Two straight losses",
        "Taken down and held by wrestlers (Bekoev, Todorovic)"],
       ["Counter his early aggression with a hook as he comes in",
        "Take him down and stay heavy in R1",
        "If he survives R1, keep pace with him - he doesn't fade"],
       [n("2026-07-11", "TKO'd by Ryan Gandra at 1:15 of R1 (dropped by a left hook, then ground strikes) at UFC 329.", "cage_gandra"),
        n("2026-02-21", "Lost a split decision to Michel Pereira in Houston that drew boos and robbery claims.", "lowkick_pereira"),
        n("2026-10-17", "Booked against Mickey Gall at middleweight for Oct 31 (MMA Junkie).", "junkie_card")],
       ["cage_gandra", "lowkick_pereira", "lowkick_mcvey", "bjpenn_329bets", "junkie_card"], "moderate")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rep in R.items():
        path = OUT / f"{slug(name)}.json"
        path.write_text(json.dumps(rep, indent=1, ensure_ascii=False) + "\n")
        print("wrote", path.relative_to(ROOT.parent))
