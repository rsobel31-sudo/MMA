"""Scouting reports (part B) for UFC Fight Night: Procházka vs. Stirling (UFC Qatar / Fight Night 294, Doha,
2026-11-21), first pass written 2026-11-10.

Covers Cannonier vs. Aliskerov, Topuria vs. Luna, Gaziev vs. Teixeira and Albazi vs. Costa (a rematch). Fight-week
previews aren't out yet: these draw on recent-fight recaps, booking news and our verified records. Round/method
counts are taken from data/verified/fights.csv. Later runs should refresh them with the Sherdog/MMA Mania/UFC.com
previews and weigh-in news.
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
    "cage_card": src("Cageside Press", "9 Fights Revealed For UFC Qatar Event On November 21",
                     "https://cagesidepress.com/2026/09/29/full-ufc-qatar-card-revealed-for-november-21-event/",
                     "2026-09-29", "Eddie Law"),
    "wiki_event": src("Wikipedia", "UFC Fight Night: Procházka vs. Stirling",
                      "https://en.wikipedia.org/wiki/UFC_Fight_Night:_Proch%C3%A1zka_vs._Stirling", "2026-11-10"),
    # Cannonier
    "cage_duncan": src("Cageside Press",
                       "UFC Oklahoma City: Christian Leroy Duncan Claims Biggest Win Yet, Gets Past Jared Cannonier",
                       "https://cagesidepress.com/2026/07/18/ufc-oklahoma-city-christian-leroy-duncan-claims-biggest-win-yet-gets-past-jared-cannonier/",
                       "2026-07-18", "Jay Anderson"),
    "lowkick_duncan": src("LowKick MMA",
                          "Christian Leroy Duncan Hands Jared Cannonier Decision Loss in Back-and-Forth UFC Oklahoma City Fight",
                          "https://www.lowkickmma.com/christian-leroy-duncan-hands-jared-cannonier-decision-loss-in-back-and-forth-ufc-oklahoma-city-fight/",
                          "2026-07-18"),
    # Aliskerov
    "cage_ferreira": src("Cageside Press", "UFC Baku: Ikram Aliskerov Notches Third Straight Win, Beats Brunno Ferreira",
                         "https://cagesidepress.com/2026/06/27/ufc-baku-ikram-aliskerov-notches-third-straight-win-beats-brunno-ferreira/",
                         "2026-06-27", "Brett Cagle"),
    "lowkick_ferreira": src("LowKick MMA", "Ikram Aliskerov Puts On Grappling Clinic Against Brunno Ferreira At UFC Baku",
                            "https://www.lowkickmma.com/ikram-aliskerov-beats-brunno-ferreira-ufc-baku/", "2026-06-27",
                            "Pranav Pandey"),
    "cage_park": src("Cageside Press", "UFC 321: Ikram Aliskerov Outlasts Jun Yong Park In Grueling Test",
                     "https://cagesidepress.com/2025/10/25/ufc-321-ikram-aliskerov-outlasts-jun-yong-park-in-grueling-test",
                     "2025-10-25", "Patrick Danna"),
    "cage_park_corner": src("Cageside Press", "Ikram Aliskerov's Corner Wasn't Happy with UFC 321 Performance",
                            "https://cagesidepress.com/2025/10/27/ikram-aliskerovs-corner-wasnt-happy-with-ufc-321-performance",
                            "2025-10-27", "Dave Noseworthy, Jay Anderson"),
    # Topuria
    "wiki_topuria": src("Wikipedia", "Aleksandre Topuria", "https://en.wikipedia.org/wiki/Aleksandre_Topuria", "2026-11-10"),
    "cage_almakhan": src("Cageside Press", "UFC Qatar: Aleksandre Topuria Bloodies Bekzat Almakhan En Route to Decision Victory",
                         "https://cagesidepress.com/2025/11/22/ufc-qatar-aleksandre-topuria-bloodies-bekzat-almakhan-en-route-to-decision-victory",
                         "2025-11-22", "Jay Anderson"),
    "cage_thicknesse": src("Cageside Press", "UFC 312: Aleksandre Topuria Scores Victory In Much-Hyped Debut Against Colby Thicknesse",
                           "https://cagesidepress.com/2025/02/08/ufc-312-aleksandre-topuria-scores-victory-in-much-hyped-debut-against-colby-thicknesse",
                           "2025-02-08", "Shawn Bitter"),
    "sherdog_ilia": src("Sherdog", "Ilia Topuria says brother may have saved his career in Justin Gaethje loss",
                        "https://www.sherdog.com/news/news/Ilia-Topuria-says-brother-may-have-saved-his-career-in-Justin-Gaethje-loss-203540",
                        "2026-11-08", "Sourav Chakraborty"),
    # Luna
    "wiki_luna": src("Wikipedia", "Santiago Luna (fighter)", "https://en.wikipedia.org/wiki/Santiago_Luna_(fighter)", "2026-11-10"),
    "cage_mitchell": src("Cageside Press", "UFC Vegas 118: Bryce Mitchell Locks Up Late Sub On Santiago Luna",
                         "https://cagesidepress.com/2026/06/06/ufc-vegas-118-bryce-mitchell-locks-up-late-sub-on-santiago-luna/",
                         "2026-06-06", "Nick Holt"),
    "cage_pacheco": src("Cageside Press", "UFC Mexico City: Promising Santiago Luna Shines Against Angel Pacheco",
                        "https://cagesidepress.com/2026/02/28/ufc-mexico-city-promising-santiago-luna-shines-against-angel-pacheco",
                        "2026-02-28", "Nick Holt"),
    "cage_le": src("Cageside Press", "Santiago Luna Turns Short Notice Call Into Highlight Reel KO",
                   "https://cagesidepress.com/2025/09/13/santiago-luna-turns-short-notice-call-into-highlight-reel-ko",
                   "2025-09-13", "Shawn Bitter"),
    # Gaziev
    "wiki_gaziev": src("Wikipedia", "Shamil Gaziev", "https://en.wikipedia.org/wiki/Shamil_Gaziev", "2026-11-10"),
    "cage_nzechukwu": src("Cageside Press", "UFC Sacramento: Shamil Gaziev Floors Kennedy Nzechukwu with Single Punch",
                          "https://cagesidepress.com/2026/08/22/ufc-sacramento-shamil-gaziev-floors-kennedy-nzechukwu-with-single-punch/",
                          "2026-08-22"),
    "cage_pericic": src("Cageside Press", "Brando Pericic Stuns Gaziev, Earns Third Straight UFC Knockout",
                        "https://cagesidepress.com/2026/05/02/brando-pericic-stuns-gaziev-earns-third-straight-ufc-knockout/",
                        "2026-05-02", "Nick Holt"),
    "cage_wca": src("Cageside Press", "UFC Qatar: Short-Notice Waldo Cortes-Acosta Smokes Shamil Gaziev",
                    "https://cagesidepress.com/2025/11/22/ufc-qatar-short-notice-waldo-cortes-acosta-smokes-shamil-gaziev",
                    "2025-11-22", "Brett Cagle"),
    "cbs_rozenstruik": src("CBS Sports",
                           "UFC Fight Night results, highlights: Jairzinho Rozenstruik batters Shamil Gaziev for big bounce back win",
                           "https://www.cbssports.com/mma/news/ufc-fight-night-results-highlights-jairzinho-rozenstruik-batters-shamil-gaziev-for-big-bounce-back-win/",
                           "2024-03-02", "Shakiel Mahjouri"),
    # Teixeira
    "wiki_teixeira": src("Wikipedia", "Tallison Teixeira", "https://en.wikipedia.org/wiki/Tallison_Teixeira", "2026-11-10"),
    "cage_tuivasa": src("Cageside Press", "UFC 325: Tallison Teixeira Goes Distance for First Time, Beats Returning Tai Tuivasa",
                        "https://cagesidepress.com/2026/01/31/ufc-325-tallison-teixeira-goes-distance-for-first-time-beats-returning-tai-tuivasa",
                        "2026-01-31", "Jay Anderson"),
    "cage_pavlovich": src("Cageside Press", "UFC Macau: Sergei Pavlovich Scores Quick KO of Tallison Teixeira",
                          "https://cagesidepress.com/2026/05/30/ufc-macau-sergei-pavlovich-scores-quick-ko-of-tallison-teixeira/",
                          "2026-05-30", "Jay Anderson"),
    "post_lewis": src("POST Wrestling", "UFC Nashville results: Derrick Lewis hands Tallison Teixeira first loss in just 35 seconds",
                      "https://www.postwrestling.com/2025/07/13/ufc-nashville-results-derrick-lewis-hands-tallison-teixeira-first-loss-in-just-35-seconds/",
                      "2025-07-13", "Jack Wannan"),
    # Albazi
    "wiki_albazi": src("Wikipedia", "Amir Albazi", "https://en.wikipedia.org/wiki/Amir_Albazi", "2026-11-10"),
    "cage_horiguchi": src("Cageside Press", "UFC Vegas 113: Kyoji Horiguchi Far Too Quick for Amir Albazi",
                          "https://cagesidepress.com/2026/02/07/ufc-vegas-113-kyoji-horiguchi-far-too-quick-for-amir-albazi",
                          "2026-02-07", "Jay Anderson"),
    "cage_moreno": src("Cageside Press", "Brandon Moreno Puts On Clinic Against Albazi, Wants His Title Back",
                       "https://cagesidepress.com/2024/11/02/brandon-moreno-puts-on-clinic-against-albazi-wants-his-title-back",
                       "2024-11-02", "Eddie Law"),
    "cage_costa1": src("Cageside Press", "UFC Vegas 66: Amir Albazi Halts Newcomer Alessandro Costa In His Tracks",
                       "https://cagesidepress.com/2022/12/17/ufc-vegas-66-amir-albazi-vs-alessandro-costa",
                       "2022-12-17", "Shawn Bitter"),
    # Costa
    "cage_durden": src("Cageside Press", "Alessandro Costa Submits Durden in Second Round at UFC 329",
                       "https://cagesidepress.com/2026/07/11/alessandro-costa-submits-durden-in-second-round-at-ufc-329/",
                       "2026-07-11", "Nick Holt"),
    "cage_schnell": src("Cageside Press",
                        "Short-notice Opportunity Pays Off for Alessandro Costa, Who Finishes Matt Schnell at UFC Vegas 118",
                        "https://cagesidepress.com/2026/06/06/short-notice-opportunity-pays-off-for-alessandro-costa-who-finishes-matt-schnell-at-ufc-vegas-118/",
                        "2026-06-06", "Brett Cagle"),
    "cage_costa_int": src("Cageside Press", "Alessandro Costa Finishes Matt Schnell, Sets Sights On Ranked Opponent",
                          "https://cagesidepress.com/2026/06/08/alessandro-costa-finishes-matt-schnell-sets-sights-on-ranked-opponent/",
                          "2026-06-08", "Destiny McCubbin, Eddie Law"),
    "cage_coria": src("Cageside Press", "Alden Coria Stuns Alessandro Costa with Breakout Win at Noche UFC",
                      "https://cagesidepress.com/2025/09/13/alden-coria-stuns-alessandro-costa-with-breakout-win-at-noche-ufc",
                      "2025-09-13", "Shawn Bitter"),
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
report("Jared Cannonier",
       "A veteran American middleweight (18-10; MMA Lab; our data lists him at 43) and former title challenger who once "
       "fought at heavyweight and light heavyweight. He has lost four of his last five: Imavov (R4 TKO), Borralho, Michael "
       "Page and, in July, Christian Leroy Duncan by decision. His only win in that run was an R4 TKO of Gregory Rodrigues "
       "in February 2025. He faces the younger, ranked grappler Ikram Aliskerov on the main card.",
       {"Striking": "Heavy hands and leg kicks; he has 11 KO/TKO wins and about 0.3 knockdowns per 15 minutes, with 50% "
                    "significant accuracy. His output has dropped in recent three-rounders: our data has him out-landed 29-20 "
                    "by Page and 68-15 by Duncan. Cageside describes him being out-struck for most of the Duncan fight and "
                    "staggered by a spinning elbow in R2.",
        "Grappling": "Mostly a defensive wrestler; offense is a change-up. He walked Duncan to the fence, won underhooks and "
                     "held him in the clinch for the whole of R3 (Cageside). Our data credits him with 5 of 8 takedowns and over "
                     "six minutes of control in that fight, and 494 seconds of control against Page, but Cageside reports only "
                     "one early single-leg attempt against Duncan, so treat those control numbers with care. Two career "
                     "submission wins, both before 2014.",
        "Defense": "Takedown defense is good (about 70%), and he is hard to hold down. Stopped three times, all by strikes: "
                   "Shawn Jordan R1 (2015, at heavyweight), Dominick Reyes R1 (2018, at light heavyweight) and Nassourdine "
                   "Imavov R4 (2024). He has never been stopped at middleweight inside three rounds. Absorbs about 4.5 "
                   "significant strikes a minute, and Duncan left visible damage on his face (LowKick).",
        "Pace & cardio": "Early finisher in his prime, now a decision fighter. Of his 13 stoppage wins, 7 came in R1, 4 in R2, "
                         "1 in R3 (Roehrick, 2017) and 1 in R4 (Rodrigues, 2025). His last stoppage inside two rounds was "
                         "Brunson in 2022. Seven of his ten losses went to the judges. He is 5-3 in five-round fights in our data "
                         "(not counting the R2 Hermansson finish), so his gas tank has held up historically, but against Duncan "
                         "Cageside wrote that he 'had slowed, and was covering up as much as he was fighting back', and LowKick "
                         "said his output faded as the fight went on.",
        "Fight IQ": "Experienced and patient; slows the pace and uses the clinch and fence when hurt. He survived Duncan's R1 "
                    "pressure by slowing things down (Cageside). Tends to start slowly and has lost recent rounds on volume."},
       ["Power puncher whose finishes now come late, if at all (R4 TKO of Rodrigues his last stoppage)",
        "Loses decisions to faster, higher-volume strikers (Page, Duncan, Borralho)",
        "Good takedown defense; hard to hold down",
        "Uses the clinch and fence to slow a fight when he's behind"],
       ["Age and four losses in his last five",
        "Low striking output in his last two fights (20 and 15 significant strikes landed in our data)",
        "Facing a younger grappler who has held his last two opponents down for six and nine minutes"],
       ["Out-work him: volume and movement beat him in both 2025-26 losses",
        "Wrestle him late, when his output drops",
        "Avoid standing still in front of his right hand early"],
       [n("2026-09-29", "Booked against Ikram Aliskerov on the Qatar card; Wikipedia lists the bout on the main card.", "cage_card"),
        n("2026-07-18", "Lost a unanimous decision (30-27, 30-27, 29-28) to Christian Leroy Duncan at UFC Oklahoma City. "
                        "LowKick reports that he knocked Duncan down in R1; Cageside and our data do not record a knockdown.",
          "cage_duncan")],
       ["cage_card", "wiki_event", "cage_duncan", "lowkick_duncan"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Ikram Aliskerov",
       "A Dagestani middleweight (18-2; 5-1 UFC; age 34 in our data) and combat sambo world champion (Cageside) out of KHK "
       "MMA. His only losses are first-round knockouts to Khamzat Chimaev (Brave, 2019) and Robert Whittaker (2024, a short-"
       "notice main event in only his third UFC fight). He has won three straight since, the last two by wrestling-heavy "
       "30-27 decisions over Jun Yong Park and Brunno Ferreira.",
       {"Striking": "Accurate and powerful: about 5.2 significant strikes a minute at 57%, 0.65 knockdowns per 15, and "
                    "seven KO/TKO wins (three in the UFC, all in R1: Hawes, Alves, Muniz). Uses a jab, leg kicks, teeps and "
                    "straight punches; landed a knee before his R1 takedown of Ferreira and met Ferreira's R3 rush with "
                    "straight shots (Cageside).",
        "Grappling": "His base. About 3.3 takedowns per 15 at 59%. Our data has him at 5 of 7 takedowns and 367 seconds of "
                     "control against Park, and 5 of 6 with 533 seconds against Ferreira. He took Ferreira down in every round "
                     "and threatened several submissions (Cageside, LowKick), and ended the Park fight on the back with a body "
                     "triangle. Five career submission wins. Cageside noted he couldn't hold Park down after early takedowns "
                     "and 'didn't do much on top' in R2.",
        "Defense": "Solid takedown defense (about 72%). His defensive hole is on the feet against elite strikers: both losses "
                   "were R1 knockouts by strikes (Chimaev 2:26, Whittaker 1:49). Our data has Whittaker out-landing him 14-5 "
                   "before the finish. Absorbs about 3.7 a minute.",
        "Pace & cardio": "A fast starter who can also grind. Twelve stoppage wins: eight in R1, one in R2, three in R3 (all "
                         "pre-UFC). His last two fights went the full 15 minutes with takedowns late, including a key R3 "
                         "takedown under Park's pressure (Cageside), so he hasn't faded. Both losses came early in R1. Said "
                         "after the Park fight that he never gets tired in three-round sparring and that his plan was to feel "
                         "Park out rather than pressure him; his corner wasn't happy with how cautious it was (Cageside).",
        "Fight IQ": "Disciplined and game-plan driven; takes the low-risk route once ahead. Called for a top opponent after "
                    "Baku (Cageside)."},
       ["Takedowns in every round, long top control and back takes",
        "R1 finisher before the UFC and early in his UFC run; grinding decisions lately",
        "Both losses were R1 knockouts against elite strikers",
        "Wins late rounds with a timely takedown"],
       ["Chin against a big puncher early in R1",
        "Can get cautious; his corner wanted more urgency against Park",
        "Park got back up repeatedly early in their fight"],
       ["Hurt him early: both losses came inside the first 2:30",
        "Defend the first takedown and get up fast; make him work for every reset",
        "Pressure him and make him uncomfortable, as Park did"],
       [n("2026-09-29", "Booked against Jared Cannonier for the Qatar card; Wikipedia lists it on the main card.", "cage_card"),
        n("2026-06-27", "Beat Brunno Ferreira by unanimous decision (30-27 x3) for his third straight win; called for a top "
                        "opponent afterwards.", "cage_ferreira")],
       ["cage_card", "wiki_event", "cage_ferreira", "lowkick_ferreira", "cage_park", "cage_park_corner"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Aleksandre Topuria",
       "A Georgian bantamweight born in Germany and based in Spain (7-1; 2-0 UFC; age 30 per Wikipedia), the older brother of former two-division "
       "champion Ilia Topuria. A Greco-Roman wrestling background and BJJ black belt (Wikipedia). He has won both UFC fights "
       "by decision (Colby Thicknesse, Bekzat Almakhan) and hasn't fought since November 2025. Faces 22-year-old Santiago "
       "Luna on the prelims.",
       {"Striking": "Forward pressure behind a well-timed jab, body shots, leg kicks and an overhand right that hurt "
                    "Thicknesse (Cageside). Against Almakhan he found his range in R2 and bloodied him over the last two "
                    "rounds. Modest volume: about 3.2 significant strikes a minute at 47%; our data has him out-landing both "
                    "UFC opponents narrowly (41-38 and 47-39).",
        "Grappling": "Clinch throws and top control: a suplex on Thicknesse, and a throw straight to mount and a brief back "
                     "take on Almakhan in R1 (Cageside). Our data has 302 and 140 seconds of control in his UFC fights. His "
                     "takedown accuracy is low (about 21%; 1 of 2 and 2 of 7). Two submission wins in 2015.",
        "Defense": "Takedown defense is a strength: he stopped all eight of Thicknesse's attempts in our data. Leg kicks are "
                   "the clear problem: Almakhan hobbled him in R1-R2 and nearly dropped him with one (Cageside). His only "
                   "loss was an R3 TKO in 2015 (Ivo Ivanov), before a six-year break.",
        "Pace & cardio": "His five regional stoppages all came in R1 (two subs in 2015, three KOs in 2021-23). Both UFC wins "
                         "went 15 minutes, and he got better as the fights went on: he lost early exchanges to Almakhan and "
                         "won R2-R3 with pressure, and finished on top of Thicknesse in R3. His only stoppage loss came in R3.",
        "Fight IQ": "Patient pressure fighter who adjusts mid-fight. Has been criticised for single-shot striking at range "
                    "(Cageside on Thicknesse, R2)."},
       ["Pressure behind the jab; improves as the fight goes on",
        "Clinch throws into top position and back takes",
        "Strong takedown defense",
        "Both UFC wins by decision"],
       ["Leg kicks: Almakhan hobbled him",
        "Almost a year out of action",
        "Low output and takedown accuracy for a pressure fighter",
        "Luna's wrestling and submissions are a different test from his two UFC opponents"],
       ["Kick his lead leg early and often",
        "Win R1 at range before his pressure builds",
        "Scramble hard when he throws; don't give up the back"],
       [n("2026-09-29", "Booked against Santiago Luna on the Qatar card (bantamweight, prelims per Wikipedia).", "cage_card"),
        n("2026-11-08", "His brother Ilia said Aleksandre's decision to stop his June title fight with Justin Gaethje may have "
                        "saved his career.", "sherdog_ilia"),
        n("2025-11-22", "Beat Bekzat Almakhan by unanimous decision (30-27, 30-27, 29-28) at UFC Qatar, the same venue as this "
                        "card.", "cage_almakhan")],
       ["cage_card", "wiki_event", "wiki_topuria", "cage_almakhan", "cage_thicknesse", "sherdog_ilia"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Santiago Luna",
       "A 22-year-old bantamweight from Tijuana ('Border Boy', Entram Gym; 8-1, 2-1 UFC), born in San Diego and a three-time "
       "national Greco-Roman champion (Wikipedia). Took two of his three UFC fights as a late replacement: an R1 KO of Quang "
       "Le on under two weeks' notice, and a fight with Bryce Mitchell that he lost by arm-triangle eight seconds from the "
       "end. In between he beat Angel Pacheco 30-27 x3.",
       {"Striking": "Fast, with knees and body hooks as his main weapons; Cageside notes an 'obvious speed advantage' in the "
                    "pocket against Pacheco and his 'patented knee' (he ended that fight with a flying knee). Floored Quang Le "
                    "with a left hook; our data has two knockdowns in that fight. About 3.4 significant strikes a minute and "
                    "he absorbs only 2.4. Our data has him out-landing Pacheco 131-56.",
        "Grappling": "Wrestler with submissions: four submission wins (R1, R1, R2, R3) on the regional scene. 5 of 5 "
                     "takedowns against Pacheco in our data, and a jumping guillotine in R3 (Cageside). Threatened a d'arce "
                     "against Mitchell. Gets back up quickly from bottom (Pacheco).",
        "Defense": "Takedown defense is about 59%. Mitchell took him down twice, reversed him repeatedly and held him for 700 "
                   "seconds in our data, taking the back and mount before the R3 arm-triangle (4:52). Le buckled him early "
                   "with a punch and a head kick (Cageside). Never stopped by strikes.",
        "Pace & cardio": "Seven stoppage wins: four in R1, one in R2, two in R3 (both regional). His decision over Pacheco "
                         "was strongest in R3 against a tired opponent (Cageside). His one loss came at the very end of R3 after "
                         "being controlled for most of the fight, and he started R3 aggressively with a takedown, so no clear "
                         "fade, but he gives up position late in scrambles.",
        "Fight IQ": "Aggressive and willing to scramble; young and still learning. Gave up his back in R3 against Mitchell "
                    "while hunting a finish (Cageside)."},
       ["Knees and body hooks in the pocket, with speed",
        "Greco-Roman takedowns and guillotine/d'arce threats",
        "Two of three UFC fights on short notice",
        "Finishes come at any point: four R1, one R2, two R3"],
       ["Bottom position and scrambles against a strong top grappler (Mitchell)",
        "Young, with nine pro fights",
        "Low takedown defense number for a wrestler"],
       ["Win the clinch and get on top; ride him rather than scramble",
        "Make him strike at range, away from his knees",
        "Watch the neck when shooting on him"],
       [n("2026-09-29", "Booked against Aleksandre Topuria on the Qatar card; his first UFC fight with a full camp since "
                        "February.", "cage_card"),
        n("2026-06-06", "Lost to Bryce Mitchell by arm-triangle at 4:52 of R3, on short notice replacing Victor Henry. First "
                        "pro loss.", "cage_mitchell")],
       ["cage_card", "wiki_event", "wiki_luna", "cage_mitchell", "cage_pacheco", "cage_le"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Shamil Gaziev",
       "A Dagestan-born Bahraini heavyweight (15-3; KHK MMA; born 1990 per Wikipedia) who won the Contender Series in 2023. "
       "A big puncher who has been knocked out twice in his last three fights (Cortes-Acosta R1, Pericic R2), then put "
       "Kennedy Nzechukwu away with one right hand in August. All 13 of his stoppage wins came inside two rounds.",
       {"Striking": "Power over volume: ten KO/TKO wins and about 0.46 knockdowns per 15, but only 3.3 significant strikes a "
                    "minute at 44%. Finished Nzechukwu with a lunging right at 1:20 of R1 (Cageside). Traded heavily with "
                    "Pericic and kept throwing back when hurt in R1.",
        "Grappling": "Top-control wrestler when he gets there: three submission wins, and our data has 718 of 900 seconds of "
                     "control against Don'Tale Mayes. He took Pericic down in R1 (216 seconds of control in our data). Takedown "
                     "accuracy is only about 40%; against Rozenstruik he landed 1 of 7, and CBS called his takedowns a weak point.",
        "Defense": "The concern. He absorbs about 4.7 significant strikes a minute with 52% striking defense. Stopped three "
                   "times: Rozenstruik after R4 (2024; he told his corner he couldn't see out of one eye), Cortes-Acosta in R1 "
                   "(1:22; a flush right, 'out before he hit the floor', Cageside) and Pericic in R2 (3:44, right hand).",
        "Pace & cardio": "A front-loaded finisher. Stoppage wins: ten in R1, three in R2, none later. His two decision wins went "
                         "three rounds. In the five-round Rozenstruik fight his output collapsed: our data has him out-landed "
                         "127-22, and the fight was stopped after R4. Stoppage losses: one in R1, one in R2, one after R4. He "
                         "wins early or tends to lose.",
        "Fight IQ": "Straightforward: walk forward, land the big right, or clinch and wrestle. Said after Sacramento he wanted "
                    "to return later in the year after a break (Cageside)."},
       ["R1-R2 finisher: ten R1 and three R2 stoppages, none later",
        "One-punch right-hand power",
        "Clinch and top control when he can get the takedown",
        "Knocked out twice in his last three fights"],
       ["Chin: KO'd in R1 and R2 in his last three",
        "Gas tank past R2",
        "Low takedown accuracy against bigger or rangier opponents"],
       ["Survive R1 and push the pace into R3",
        "Jab and move; Rozenstruik broke him down with the jab",
        "Fast combinations; Pericic's speed beat him in exchanges"],
       [n("2026-09-29", "Booked against Tallison Teixeira on the Qatar prelims.", "cage_card"),
        n("2026-08-22", "Knocked out Kennedy Nzechukwu at 1:20 of R1, snapping a two-fight losing streak; his tenth career "
                        "knockout.", "cage_nzechukwu"),
        n("2026-05-02", "Knocked out by Brando Pericic at 3:44 of R2 at UFC Perth; both men earned Fight of the Night "
                        "(Wikipedia).", "cage_pericic")],
       ["cage_card", "wiki_event", "wiki_gaziev", "cage_nzechukwu", "cage_pericic", "cage_wca", "cbs_rozenstruik"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Tallison Teixeira",
       "A 6-foot-8 Brazilian heavyweight (9-2; 2-2 UFC; age 26, Team Lucas Mineiro per Wikipedia) and a pure first-round "
       "finisher: eight of his nine wins came in R1. He has been knocked out inside 40 seconds twice, by Derrick Lewis (0:35) "
       "and Sergei Pavlovich (0:39). His one decision was a messy win over Tai Tuivasa in which he faded badly.",
       {"Striking": "Long, heavy shots and a jab with real power: he wobbled Lewis with an early jab (POST Wrestling), and "
                    "finished Justin Tafa with a knee to the body and elbow in 35 seconds. About 0.9 knockdowns per 15. Seven "
                    "KO/TKO wins, all in R1.",
        "Grappling": "Will wrestle: our data has 3 of 9 takedowns and 420 seconds of control against Tuivasa. He took "
                     "Tuivasa to mount and the back in R1-R2 and looked for a rear-naked choke (Cageside). One submission win "
                     "(2021, R1).",
        "Defense": "Poor so far against UFC-level punchers: 46% striking defense. Lewis dropped him with a left hook; Pavlovich "
                   "hurt him with the first right hand and dropped him with the third (Cageside). He protested both stoppages "
                   "but was badly hurt in each. Tuivasa had him stumbling backwards and on his knees in R3.",
        "Pace & cardio": "All eight stoppage wins in R1. Both losses in R1 (0:35, 0:39). His only fight past R1 was Tuivasa, "
                         "where Cageside says he may have 'expended too much energy in round one', slowed in R2 and was nearly "
                         "finished in R3 (29-28 x3). He is a fast starter who fades.",
        "Fight IQ": "Aggressive starter. Mixed in wrestling against Tuivasa rather than trading, which won him the fight. "
                    "Had not faced an opponent with more than seven wins before Lewis (POST Wrestling)."},
       ["R1 finisher: eight of nine wins in R1",
        "Both losses: R1 knockouts inside 40 seconds",
        "Wrestles when the knockout isn't there",
        "Fades sharply after a big R1"],
       ["Chin against heavy hitters",
        "Cardio beyond R1",
        "Has spent less than 17 minutes in the cage across four UFC fights"],
       ["Make him miss early and drag him past R1",
        "Counter hard on his entries; he gets hit coming in",
        "Push the pace in R2-R3 when he slows"],
       [n("2026-09-29", "Booked against Shamil Gaziev on the Qatar prelims.", "cage_card"),
        n("2026-05-30", "Knocked out by Sergei Pavlovich at 0:39 of R1 at UFC Macau; he entered ranked No. 15 (Cageside).",
          "cage_pavlovich"),
        n("2026-01-31", "Beat Tai Tuivasa by unanimous decision (29-28 x3), his first fight past R1.", "cage_tuivasa")],
       ["cage_card", "wiki_event", "wiki_teixeira", "cage_tuivasa", "cage_pavlovich", "post_lewis"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Amir Albazi",
       "An Iraqi-born flyweight raised in Sweden and based in London (17-3; age 33 per Wikipedia), listed at No. 8 by Wikipedia, "
       "who has lost two straight decisions, to Brandon Moreno (2024) and Kyoji Horiguchi (February 2026). He had "
       "heart surgery in 2023 and spine surgery in 2024 and has fought once a year or less since. Now with Great Britain "
       "Top Team (Wikipedia). This is a rematch: he knocked Alessandro Costa out in R3 in 2022.",
       {"Striking": "Patient, counter-minded and low-volume (about 2.9 significant strikes a minute at 37%). Out-landed in "
                    "all three of his recent big fights in our data: 43-99 by Kara-France, 63-132 by Moreno, 16-73 by "
                    "Horiguchi. Speed was the issue against Horiguchi (Cageside). He does have finishing power: dropped Costa "
                    "twice, the second time with an uppercut.",
        "Grappling": "His best route: nine submission wins (six in R1) and long control when he gets on top, such as 354 "
                     "seconds against Costa and 370 against Kara-France. But recent takedown success is poor: 1 of 9 against "
                     "Kara-France, 1 of 4 against Moreno, 0 of 7 against Horiguchi in our data. Cageside says Horiguchi kept "
                     "escaping his clinches and body locks.",
        "Defense": "Never stopped; all three losses were decisions (Jose Torres 2019, Moreno, Horiguchi). Absorbs about 4.1 a "
                   "minute and took visible damage from both Moreno (right eye compromised) and Horiguchi (bloodied).",
        "Pace & cardio": "Early finisher who now goes to decisions. Fourteen stoppage wins: nine in R1, four in R2, one in R3 "
                         "(Costa, 2022). His last finish was that Costa fight. Since then: a disputed split over Kara-France "
                         "(Wikipedia says 19 of 21 media outlets scored it for Kara-France) and two clear decision losses. Cageside "
                         "notes he looked rusty early against Moreno and warmed up as it went on, and looked 'overwhelmed' by R3 "
                         "against Horiguchi.",
        "Fight IQ": "Smart, tactical, waits for openings. Layoffs (heart surgery complications, then a 15-month gap before "
                    "Horiguchi) have cost him sharpness."},
       ["Patient counter-striker; low volume",
        "Submissions and top control when he gets the takedown",
        "Never stopped; all losses on the cards",
        "Has been out-landed heavily in his last three big fights"],
       ["Two straight losses and long layoffs",
        "Recent takedown accuracy (2 of 20 across his last three fights in our data)",
        "Health history: heart surgery (2023) and spine surgery (2024)",
        "Several gym changes; now at Great Britain Top Team"],
       ["Out-work him at range; volume has beaten him every time recently",
        "Keep moving and don't let him settle into the clinch",
        "Defend the first takedown; his chain wrestling hasn't worked lately"],
       [n("2026-09-29", "Booked in a rematch with Alessandro Costa on the Qatar prelims.", "cage_card"),
        n("2026-02-07", "Lost a unanimous decision to Kyoji Horiguchi (30-27, 30-27, 29-28) after more than a year out.",
          "cage_horiguchi"),
        n("2026-11-10", "Wikipedia notes a withdrawal from a planned fight with Tatsuro Taira in August 2025 with an injury.",
          "wiki_albazi")],
       ["cage_card", "wiki_event", "wiki_albazi", "cage_horiguchi", "cage_moreno", "cage_costa1"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Alessandro Costa",
       "A flyweight who built his record on the Mexican regional scene (17-5; 5-3 UFC; age 31 in our data) and is on a three-fight "
       "finishing streak in 2026: R2 TKO of Stewart Nicoll, R1 TKO of Matt Schnell on nine days' notice, and an R2 rear-naked "
       "choke of Cody Durden at UFC 329. He now gets a rematch with Amir Albazi, who knocked him out in R3 in his 2022 UFC "
       "debut.",
       {"Striking": "Counter-puncher with power: overhand rights against Schnell and hooks against Durden (Cageside). About "
                    "0.8 knockdowns per 15; seven KO/TKO wins. Our data has him landing 19 of 23 against Schnell. Throws "
                    "spinning kicks. Output is moderate (about 3.5 a minute).",
        "Grappling": "Seven submission wins, six of them in R1 on the regional scene. Finishes from the back: body triangle "
                     "to RNC against Durden. Swept Alden Coria with a kimura and took his back (Cageside). Takedown defense "
                     "is strong (about 81%); Cageside noted it held up early against Albazi.",
        "Defense": "Stopped three times: Uriel Cossio R2 (2016), Albazi R3 (2022: dropped in R2 and R3, controlled for 354 "
                   "seconds in our data) and Coria R3 (2025, hampered by a foot injury per Cageside). Also lost a decision "
                   "to Steve Erceg, who held him for 389 seconds in our data.",
        "Pace & cardio": "Starts fast, struggles late. Fourteen stoppage wins: nine in R1, four in R2, one in R3 (2021). Both "
                         "UFC stoppage losses came in R3 after he'd lost the earlier rounds. His one five-round fight (2020) "
                         "was a decision win. His recent wins all ended inside two rounds.",
        "Fight IQ": "Opportunistic; says he knew the Durden finish was 'just a matter of time' once he got position. Wants "
                    "a ranked opponent next (Cageside). Willing to take short-notice fights."},
       ["R1-R2 finisher: 13 of 14 stoppage wins inside two rounds",
        "Counter right hand and hooks",
        "Back takes and rear-naked chokes",
        "Both UFC stoppage losses in R3"],
       ["Previous knockout loss to this opponent",
        "Late rounds against a patient grappler",
        "Bottom position when out-wrestled (Albazi, Erceg)"],
       ["Survive his first two rounds, then wrestle him in R3",
        "Stay patient and don't walk onto his counter right",
        "Clinch and control him against the fence"],
       [n("2026-09-29", "Booked in a rematch with Amir Albazi on the Qatar prelims.", "cage_card"),
        n("2026-07-11", "Submitted Cody Durden with a rear-naked choke at 2:19 of R2 at UFC 329.", "cage_durden"),
        n("2026-06-06", "Stopped Matt Schnell at 2:32 of R1 at a catchweight after taking the fight on nine days' notice.",
          "cage_schnell")],
       ["cage_card", "wiki_event", "cage_durden", "cage_schnell", "cage_costa_int", "cage_coria", "cage_costa1"],
       "moderate")


out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
