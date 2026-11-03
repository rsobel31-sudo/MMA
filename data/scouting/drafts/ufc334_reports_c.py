"""Scouting reports (part C) for UFC 334: Gane vs. Hokit (Madison Square Garden, New York, 2026-11-14),
first pass written 2026-11-03.

Fight-week previews aren't out yet: these draw on recent-fight recaps, booking and withdrawal news and our
verified records. Round/method counts are taken from data/verified/fights.csv. Later runs should refresh them
with the Sherdog/MMA Mania/UFC.com previews and weigh-in news. Juan Diaz has no named opponent as of this pass.
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
    "ufc_event": src("UFC.com", "UFC 334: Gane vs. Hokit (event page)", "https://www.ufc.com/event/ufc-334", "2026-11-03"),
    # McKinney
    "cage_nelson": src("Cageside Press", "UFC Seattle: Terrance McKinney Refuses to Leave First Round, Stops Kyle Nelson",
                       "https://cagesidepress.com/2026/03/28/ufc-seattle-terrance-mckinney-refuses-to-leave-first-round-stops-kyle-nelson",
                       "2026-03-28", "Jay Anderson"),
    "lowkick_329": src("LowKick MMA", "UFC 329 Power Rankings: Rating The Night's Big Winners In Las Vegas",
                       "https://www.lowkickmma.com/ufc-329-power-rankings-rating-the-nights-big-winners-in-las-vegas/",
                       "2026-07-13"),
    "cage_329_losers": src("Cageside Press", "What's Next: UFC 329 Losers",
                           "https://cagesidepress.com/2026/07/13/whats-next-ufc-329-losers/", "2026-07-13"),
    "rotowire_mckinney": src("Rotowire", "Terrance McKinney MMA Stats & News",
                             "https://www.rotowire.com/mma/player/terrance-mckinney-2188", "2026-11-03"),
    "lowkick_serbia": src("LowKick MMA", "UFC Serbia: Matchmaking for All of Saturday's Winners",
                          "https://www.lowkickmma.com/matchmaking-for-all-of-saturdays-winners/", "2026-08-04"),
    "cage_miller_gordon": src("Cageside Press", "Jim Miller Does It Again, Submits Jared Gordon With Guillotine",
                              "https://cagesidepress.com/2026/05/09/jim-miller-does-it-again-submits-jared-gordon-with-guillotine/",
                              "2026-05-09", "Eddie Law"),
    # Donte Johnson / Almeida
    "sherdog_susurkaev": src("Sherdog", "UFC 334 gets new middleweight matchup after Baisangur Susurkaev withdraws",
                             "https://www.sherdog.com/news/news/UFC-334-gets-new-middleweight-matchup-after-Baisangur-Susurkaev-withdraws-203024",
                             "2026-09-30", "Sourav Chakraborty"),
    "cage_brundage": src("Cageside Press", "UFC 326: Donte Johnson Gets Nod Over Cody Brundage",
                         "https://cagesidepress.com/2026/03/07/ufc-326-donte-johnson-gets-nod-over-cody-brundage", "2026-03-07",
                         "Brett Cagle"),
    "ufc_johnson": src("UFC.com", "Donte Johnson Fixing Things That Weren't Quite Broken (UFC 330)",
                       "https://www.ufc.com/news/donte-johnson-fixing-things-werent-quite-broken-ufc-330", "2026-08-12",
                       "E. Spencer Kyte"),
    "cage_johnson_cut": src("Cageside Press", "UFC 330: Donte Johnson Believes Cut to 170 Possible, Apologizes to Ref",
                            "https://cagesidepress.com/2026/08/17/ufc-330-donte-johnson-ref-cut/", "2026-08-17",
                            "Eddie Law, Jay Anderson"),
    "bjp_330": src("BJPenn.com", "UFC 330: 'Makhachev vs. Garry' Live Results and Highlights",
                   "https://www.bjpenn.com/mma-news/ufc-330/ufc-330-makhachev-vs-garry-live-results-and-highlights/",
                   "2026-08-15"),
    "cage_pinas": src("Cageside Press", "Damian Pinas Flattens Almeida With Devastating KO At UFC 329",
                      "https://cagesidepress.com/2026/07/11/damian-pinas-flattens-almeida-with-devastating-ko-at-ufc-329/",
                      "2026-07-11", "Eddie Law"),
    "cage_oleksiejczuk": src("Cageside Press", "Cezary Oleksiejczuk Outgrapples Cesar Almeida in Dominant UFC Debut",
                             "https://cagesidepress.com/2025/12/14/cezary-oleksiejczuk-outgrapples-cesar-almeida-in-dominant-ufc-debut",
                             "2025-12-14", "Shawn Bitter"),
    "wiki_almeida": src("Wikipedia", "César Almeida (fighter)", "https://en.wikipedia.org/wiki/C%C3%A9sar_Almeida_(fighter)",
                        "2026-11-03"),
    "bjp_329_bets": src("BJPenn.com", "UFC 329 Best Bets: Paddy Pimblett bounceback, quick finishes lead cash-ins",
                        "https://www.bjpenn.com/mma-news/paddy-pimblett/ufc-329-best-bets-paddy-pimblett/", "2026-07-08"),
    # Chiasson / Mesquita
    "cage_perez": src("Cageside Press", "UFC Mexico City: Ailin Perez Beats Macy Chiasson for Sixth Straight Win",
                      "https://cagesidepress.com/2026/02/28/ufc-mexico-city-ailin-perez-beats-macy-chiasson-for-sixth-straight-win",
                      "2026-02-28", "Brett Cagle"),
    "rotowire_chiasson": src("Rotowire", "Macy Chiasson MMA Stats & News", "https://www.rotowire.com/mma/player/macy-chiasson-1807",
                             "2026-11-03"),
    "bjp_perez_booking": src("BJPenn.com", "Ailin Perez vs. Macy Chiasson bolsters UFC Mexico with clash of ranked bantamweights",
                             "https://www.bjpenn.com/mma-news/ufc-mexico/ailin-perez-vs-macy-chiasson-bolsters-ufc-mexico-with-clash-of-ranked-bantamweights/",
                             "2025-12-15"),
    "bjp_320_weighin": src("BJPenn.com", "UFC 320 weigh-in results: One fighter misses target",
                           "https://www.bjpenn.com/mma-news/ufc/ufc-320-weigh-in-results-one-fighter-misses-target-magomed-ankalaev-and-alex-pereira-make-title-fight-official/",
                           "2025-10-03"),
    "lowkick_perez": src("LowKick MMA", "UFC's Ailín Pérez Eyes \"Battle of the Butts\" Fight After Macy Chiasson Showdown",
                         "https://www.lowkickmma.com/ufc-ailin-perez-battle-of-the-butts-after-macy-chiasson/", "2026-01-29"),
    "cage_mullins": src("Cageside Press", "UFC Vegas 119: Bia Mesquita Overcomes Early Adversity, Subs Melissa Mullins",
                        "https://cagesidepress.com/2026/06/20/ufc-vegas-119-bia-mesquita-overcomes-early-adversity-subs-melissa-mullins/",
                        "2026-06-20", "Jay Anderson"),
    "wiki_mesquita": src("Wikipedia", "Beatriz Mesquita", "https://en.wikipedia.org/wiki/Beatriz_Mesquita", "2026-11-03"),
    # Gordon / Costa
    "heavy_gordon_costa": src("Heavy", "UFC Adds Lightweight Scrap for UFC 334 in New York",
                              "https://heavy.com/sports/ufc/ufc-lightweight-ufc-334-new-york/", "2026-10-01", "Marcel Dorff"),
    "cage_328_losers": src("Cageside Press", "What's Next: UFC 328 Losers",
                           "https://cagesidepress.com/2026/05/11/whats-next-ufc-328-losers/", "2026-05-11"),
    "wiki_gordon": src("Wikipedia", "Jared Gordon", "https://en.wikipedia.org/wiki/Jared_Gordon", "2026-11-03"),
    "cage_allen": src("Cageside Press", "UFC Vegas 117: Arnold Allen Returns to Win Column with Decision Over Melquizael Costa",
                      "https://cagesidepress.com/2026/05/16/ufc-vegas-117-arnold-allen-returns-to-win-column-with-decision-over-melquizael-costa/",
                      "2026-05-16", "Jay Anderson"),
    "cage_v117_losers": src("Cageside Press", "What's Next: UFC Vegas 117 Losers",
                            "https://cagesidepress.com/2026/05/18/whats-next-ufc-vegas-117-losers/", "2026-05-18"),
    "lowkick_v117": src("LowKick MMA", "UFC Vegas 117 Power Rankings: Rating The Night's Big Winners In Las Vegas",
                        "https://www.lowkickmma.com/ufc-vegas-117-power-rankings-rating-the-nights-big-winners-in-las-vegas/",
                        "2026-05-18"),
    # Elder / Sanches
    "rotowire_elder": src("Rotowire", "Evan Elder MMA Stats & News", "https://www.rotowire.com/mma/player/evan-elder-2288",
                          "2026-11-03"),
    "cage_young": src("Cageside Press", "Elder Beats Young in UFC Kansas City Prelim",
                      "https://cagesidepress.com/2025/04/26/elder-beats-young-in-ufc-kansas-city-prelim", "2025-04-26",
                      "Shawn Bitter"),
    "sherdog_kc_prev": src("Sherdog", "Preview: UFC Kansas City Prelims",
                           "https://www.sherdog.com/news/articles/2/Preview-UFC-Kansas-City-Prelims-196751", "2025-04-23",
                           "Tom Feely"),
    "rotowire_sanches": src("Rotowire", "Samuel Sanches MMA Stats & News", "https://www.rotowire.com/mma/player/samuel-sanches-2704",
                            "2026-11-03"),
    "cage_sanches_dwcs": src("Cageside Press", "DWCS Winner Samuel Sanches Eyeing UFC's Qatar, Abu Dhabi Cards for Debut",
                             "https://cagesidepress.com/2025/09/10/samuel-sanches-dwcs-qatar-abu-dhabi", "2025-09-10",
                             "Patrick Danna"),
    # Juan Diaz
    "si_yanez_out": src("Yahoo Sports (MMA Knockout / SI)",
                        "UFC 334 Loses \"Fight of the Night\" Contender Just Weeks Out From MSG Event",
                        "https://sports.yahoo.com/articles/ufc-334-loses-fight-night-172339565.html", "2026-10-19",
                        "Drew Beaupre"),
    "heavy_diaz_booking": src("Yahoo Sports (Heavy)", "Bantamweight Barnburner Added to UFC 334 in New York",
                              "https://sports.yahoo.com/articles/bantamweight-barnburner-added-ufc-334-171948504.html",
                              "2026-09-15", "Marcel Dorff"),
    "cage_wellmaker": src("Cageside Press", "UFC Vegas 117: Malcolm Wellmaker Suffers Shock Defeat, Subbed by Juan Díaz",
                          "https://cagesidepress.com/2026/05/16/ufc-vegas-117-malcolm-wellmaker-suffers-shock-defeat-subbed-by-juan-diaz/",
                          "2026-05-16", "Shawn Bitter"),
    "lowkick_wellmaker": src("LowKick MMA", "Juan Díaz Delivers Stunning Debut, Submits Malcolm Wellmaker – UFC Vegas 117 Highlights",
                             "https://www.lowkickmma.com/malcolm-wellmaker-vs-juan-diaz-ufc-vegas-117/", "2026-05-16",
                             "Craig Pekios"),
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
report("Terrance McKinney",
       "An explosive American lightweight (18-9; 8-6 UFC; age 32) and one of the fastest starters in the sport. Every one of "
       "his 27 pro fights in our data ended inside the distance. He has gone loss, win, loss in his last three: submitted by "
       "Chris Duncan, a 24-second TKO of Kyle Nelson, then stopped by King Green with one second left in R1 after "
       "dominating the early minutes. He meets 43-year-old Jim Miller on the UFC 334 prelims.",
       {"Striking": "Heavy, all-out pressure from the opening bell: about 6.9 significant strikes a minute at 57%, with real "
                    "power (0.59 knockdowns per 15). Against Nelson a partly blocked head kick put him down and McKinney finished "
                    "with right hammerfists at 0:24 (Cageside Press). He landed several big shots on Green early (LowKick MMA).",
        "Grappling": "A real finisher on the mat too: nine of his 18 wins are submissions, eight of them in R1. He mixes in "
                     "takedowns (about 2.3 per 15) and ground strikes; he took Green down and 'started to punish him on the mat' "
                     "before tiring (LowKick MMA).",
        "Defense": "The weak point. He absorbs about 4.3 a minute and has 47% striking defense. All nine losses were stoppages: six "
                   "by strikes (four in R1, two in R2) and three by submission (two in R1, one in R2). Duncan submitted him with an "
                   "anaconda choke at 2:30 of R1 in December 2025 (Rotowire).",
        "Pace & cardio": "Built for the first five minutes. 17 of his 18 wins came in R1; the only exception was an R3 submission in "
                         "2018. Cageside notes he has never won a UFC fight after the first round. Every loss came in R1 or R2. Against "
                         "Green he wore himself out on top and was stopped at 4:59 of R1 (LowKick MMA). He has never been to a "
                         "decision in our data.",
        "Fight IQ": "Goes for the finish immediately and keeps going. LowKick MMA calls him known for 'explosive starts and "
                    "relentless aggression'. The downside is that he can empty the tank chasing a stoppage and has little in "
                    "reserve if the opponent survives."},
       ["Sprint start: 17 of 18 wins in R1",
        "Head kicks and punches into ground-and-pound finishes",
        "R1 submissions when he gets on top or catches a scramble",
        "All nine losses were stoppages, all in R1-R2",
        "Fades fast if the opponent weathers the first few minutes (Green)"],
       ["Cardio once the opening burst is spent",
        "Striking defense and durability: six KO/TKO losses",
        "Jim Miller is a veteran submission threat; in May he caught Jared Gordon in a guillotine as Gordon finished a "
        "takedown (Cageside Press), which matters for a fighter who shoots and scrambles as McKinney does",
        "Two losses in his last three fights"],
       ["Survive the first three minutes; don't trade with him early",
        "Make him carry weight and work on the mat late in R1, then take over in R2",
        "Counter as he rushes in; he has been stopped six times by strikes",
        "Threaten the neck when he dives for takedowns"],
       [n("2026-07-11", "Stopped by King Green (TKO, punches) at 4:59 of R1 at UFC 329 after leading early. Cageside notes the loss "
                        "drops him to 8-6 in the UFC.", "cage_329_losers"),
        n("2026-03-28", "Beat Kyle Nelson by TKO (hammerfists) at 0:24 of R1 at UFC Seattle.", "cage_nelson"),
        n("2025-12-06", "Submitted by Chris Duncan (anaconda choke) at 2:30 of R1 at UFC 323.", "rotowire_mckinney"),
        n("2026-11-03", "Booked against Jim Miller on the UFC 334 prelims at Madison Square Garden. We have not found a detailed "
                        "booking report from our outlets yet.", "wiki_event")],
       ["cage_nelson", "lowkick_329", "cage_329_losers", "rotowire_mckinney", "lowkick_serbia", "cage_miller_gordon", "wiki_event",
        "ufc_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Donte Johnson",
       "An undefeated middleweight finisher from Wisconsin (9-0; 3-0 UFC; age 27 per UFC.com) who earned his contract on the "
       "Contender Series at heavyweight before dropping two divisions. He submitted Sedriques Dumas, edged Cody Brundage on a "
       "split decision, then knocked out Eric McConico at 1:38 of R1 at UFC 330. He was set to face fellow unbeaten prospect "
       "Baisangur Susurkaev, who withdrew; he now meets Cesar Almeida.",
       {"Striking": "Power puncher. Seven of his nine wins are R1 KO/TKOs. Against McConico a straight left dropped him and follow-up "
                    "strikes ended it (BJPenn.com). His plan for the southpaw McConico was to stay in close and take away the rear "
                    "kick (UFC.com). He lands about 3.8 significant strikes a minute and has 62% striking defense.",
        "Grappling": "Solid when it gets there. He went 3-for-3 on takedowns and submitted Dumas in R2. Against Brundage he was "
                     "taken down in R1 and held for about two minutes, but stuffed Brundage's later shots, reversed to top position "
                     "in R2 and landed heavy ground strikes (Cageside Press). About 73% takedown defense.",
        "Defense": "Never beaten. Brundage got the only takedown of their fight and landed a straight right and an inside left hook "
                   "(Cageside).",
        "Pace & cardio": "Mostly a quick finisher: seven R1 KOs, one R2 submission. His one decision (Brundage, split 29-28, 28-29, "
                         "29-28) is his only trip past R2. Cageside noted his activity and volume 'dropped sharply' in R3 of that "
                         "fight, though he still stopped Brundage's late takedown.",
        "Fight IQ": "Called the Brundage fight the toughest of his career and said it gave him 'the adjustments and the clarity' he "
                    "needed; he then moved full-time to Las Vegas to train at Xtreme Couture (UFC.com). Confident outside the cage: "
                    "after UFC 330 he said he wants belts at middleweight, welterweight and light heavyweight and thinks a cut to "
                    "170 is possible (Cageside)."},
       ["Fast KO power: seven R1 KOs in nine wins",
        "Hits hard on top once he reverses or takes position",
        "Undefeated; only one fight past R2",
        "Output dipped in the only R3 he has fought"],
       ["Limited film past the first round; one 15-minute fight, and it was close",
        "Was taken down and held early by Brundage",
        "Opponent change: prepared for Susurkaev, now faces a former elite kickboxer with a very different style"],
       ["Take him down early and make him work off his back, as Brundage did in R1",
        "Drag him into R3, where his output dropped against Brundage",
        "Avoid open exchanges in the first round"],
       [n("2026-09-30", "Baisangur Susurkaev withdrew from their UFC 334 bout for undisclosed reasons; Cesar Almeida reportedly "
                        "agreed to step in (Sherdog, citing AG Fight).", "sherdog_susurkaev"),
        n("2026-08-15", "Knocked out Eric McConico at 1:38 of R1 at UFC 330. After the stoppage his back elbow accidentally hit the "
                        "referee; he apologized afterwards.", "cage_johnson_cut"),
        n("2026-08-17", "Said he got down to 181 pounds the day before weigh-ins and believes a cut to welterweight is possible.",
          "cage_johnson_cut")],
       ["sherdog_susurkaev", "cage_brundage", "ufc_johnson", "cage_johnson_cut", "bjp_330", "wiki_event", "ufc_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Cesar Almeida",
       "A Brazilian middleweight (7-3; 3-3 UFC; age 38 per Wikipedia) who came to MMA after a long kickboxing career, including "
       "a 2013 tournament final win over Alex Pereira. He has lost two straight: out-wrestled by Cezary Oleksiejczuk in December "
       "2025 and knocked out by Damian Pinas at 4:44 of R1 in July. He replaces Baisangur Susurkaev against unbeaten Donte "
       "Johnson.",
       {"Striking": "Technical, efficient kickboxer: about 3.6 significant strikes a minute at 59%, absorbs only about 2.2. Works the "
                    "legs and body with kicks and a straight right. Against Pinas he stayed disciplined, avoided a long-range battle "
                    "and kept kicking the body (Cageside Press). BJPenn.com credits him with crisp striking in wins over Abdul Razak "
                    "Alhassan (R1 KO, left hook) and Ihor Potieria (decision).",
        "Grappling": "Little offense (about 0.5 takedowns per 15). He did reverse a caught-kick takedown attempt by Pinas and pinned "
                     "him on the fence (Cageside).",
        "Defense": "Takedown defense is the problem (about 50%). Oleksiejczuk took him down in every round and held top control for "
                   "most of the fight; Almeida showed 'strong get-up ability along the cage' but kept being taken back down "
                   "(Cageside). Roman Kopylov also took him down five times in our data and edged a split decision. Pinas "
                   "knocked him out with one right hand.",
        "Pace & cardio": "Five of his seven wins are KO/TKOs: four in R1, one in R2 (Dylan Budka, UFC debut). His two decision wins "
                         "and two decision losses all went the full 15 minutes. His only stoppage loss came in R1 (Pinas). Our data "
                         "has no sign of a late fade; his losses come from being wrestled or caught.",
        "Fight IQ": "Patient and composed on the feet; Cageside says he was reading Pinas and controlling the pace before the knockout. "
                    "He tends to lose fights where the opponent changes levels or brings more reach and power."},
       ["Kicks to the legs and body, straight right behind them",
        "Four R1 KOs; two UFC Performance of the Night bonuses (Budka, Alhassan)",
        "Taken down repeatedly by wrestlers (Kopylov, Oleksiejczuk)",
        "Both UFC decision losses came against opponents who controlled him on the mat"],
       ["Age 38 and two straight losses, the last by knockout",
        "Takedown defense",
        "Took the fight after Susurkaev withdrew in late September, about six weeks out"],
       ["Change levels and take him down; he has been held down for long stretches",
        "Close distance through his kicks instead of fighting at his range",
        "Look for the big right hand when he commits to body kicks"],
       [n("2026-09-30", "Reportedly agreed to replace Baisangur Susurkaev against Donte Johnson at UFC 334 (Sherdog, citing AG Fight).",
          "sherdog_susurkaev"),
        n("2026-07-11", "Knocked out by Damian Pinas (punch) at 4:44 of R1 at UFC 329.", "cage_pinas"),
        n("2025-12-13", "Lost a unanimous decision (30-27 x3) to Cezary Oleksiejczuk, who out-grappled him.", "cage_oleksiejczuk")],
       ["sherdog_susurkaev", "cage_pinas", "cage_oleksiejczuk", "wiki_almeida", "bjp_329_bets", "wiki_event", "ufc_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Macy Chiasson",
       "A tall veteran bantamweight (10-6; 8-6 UFC; age 35) and TUF 28 winner, listed at 180 cm. She is on a three-fight losing "
       "streak, all decisions: Ketlen Vieira, Yana Santos (after missing weight by 2.5 pounds) and Ailin Perez (29-28 x3). "
       "UFC.com lists her at No. 9, against No. 11 Beatriz Mesquita.",
       {"Striking": "Long-range jab and kicks with a big size edge over most of the division. Modest output (about 3.1 significant "
                    "strikes a minute at 46%). Against Perez she opened R2 with a body kick and a jab and walked through an overhand "
                    "right (Cageside Press).",
        "Grappling": "Dangerous in scrambles. Against Perez she threatened a leg lock, took the back and landed elbows in R1 "
                     "(Cageside). Three career submissions (R1, R2, R3) and about 1.6 takedowns per 15.",
        "Defense": "Takedowns are the recurring problem lately. Perez got inside her reach and took her down repeatedly (6 of 10 in "
                   "our data); Vieira held her down for about ten minutes. Takedown defense is about 65%. She has been stopped twice: "
                   "Raquel Pennington submission (R2) and Irene Aldana TKO (R3).",
        "Pace & cardio": "Her six finishes are spread out: R1 one KO and one submission; R2 two KOs and one submission; R3 one "
                         "submission (regional, 2017). Four of her six losses went to decision, and "
                         "her two stoppage losses came in R2 and R3. Her last three fights all went 15 minutes and she lost all three.",
        "Fight IQ": "Experienced and willing to grapple off her back, but she has been losing the positional battle to shorter, "
                    "faster wrestlers who get inside her range."},
       ["Uses length at range: jab, body kick",
        "Scramble threats: leg locks, back takes",
        "Three straight decision losses",
        "Taken down repeatedly by shorter opponents (Perez, Vieira)"],
       ["Weight: missed by 2.5 pounds for Yana Santos (137.5) and was fined 25% of her purse; BJPenn.com notes question marks "
        "over her history with the scale. She did make weight for Perez with a pound to spare (Rotowire)",
        "Three-fight skid",
        "Mesquita is an elite grappler, and Chiasson has lost the mat battle in recent fights"],
       ["Get inside her reach and take her down",
        "Stay heavy on top; don't give her room to scramble for the back or a leg",
        "Win the grappling rounds rather than trading at range"],
       [n("2026-02-28", "Lost to Ailin Perez by unanimous decision (29-28 x3) in Mexico City; Perez repeatedly took her down.",
          "cage_perez"),
        n("2026-02-28", "Made weight for Perez with a pound to spare (Rotowire).", "rotowire_chiasson"),
        n("2025-10-03", "Missed weight at 137.5 pounds for Yana Santos at UFC 320 and was fined 25% of her purse.", "bjp_320_weighin"),
        n("2026-11-03", "Rankings shown on the UFC.com event page: Chiasson No. 9, Mesquita No. 11.", "ufc_event")],
       ["cage_perez", "rotowire_chiasson", "bjp_perez_booking", "bjp_320_weighin", "lowkick_perez", "wiki_event", "ufc_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Beatriz Mesquita",
       "One of the most decorated jiu-jitsu competitors ever (record ten IBJJF black belt world titles, IBJJF Hall of Fame, 2017 "
       "ADCC gold per Wikipedia), now 8-0 in MMA and 3-0 in the UFC with three submissions. Age 35, fighting out of American Top "
       "Team, former LFA bantamweight champion. She is giving up a lot of height to Macy Chiasson (157.5 cm to 180 cm in our "
       "data).",
       {"Striking": "Functional, mostly used to close distance: about 3.6 significant strikes a minute. Against Melissa Mullins she "
                    "kicked and worked to close range, then got hurt in a scrappy exchange and had to clinch (Cageside Press). Her one "
                    "KO/TKO win was the LFA title fight with Sierra Dinwoodie (R2).",
        "Grappling": "Elite. Six of her eight wins are submissions: rear-naked chokes of Irina Alekseeva (R2) and Montserrat Rendon "
                     "(R1) and an armbar of Mullins from her guard (R1, 3:16) (Wikipedia, Cageside). She finishes from top and bottom, "
                     "and about 2 takedowns per 15.",
        "Defense": "Never beaten, but hittable on the feet: Mullins landed several clean shots and had her hurt before she found the "
                   "armbar (Cageside). Takedown defense is listed at about 53% in our data on a small sample.",
        "Pace & cardio": "She has never needed more than two rounds. Our data has her wins as R1: four submissions; R2: two "
                         "submissions, one TKO and one DQ win. She has never seen R3 in MMA, so her late-round cardio is untested.",
        "Fight IQ": "Calm under fire: she recovered from being hurt and finished Mullins off her back. Short MMA career (pro debut "
                    "June 2024) means limited film against a long, experienced opponent."},
       ["Gets the fight to the mat, then hunts the back or an arm",
        "Six submissions in eight wins; three straight in the UFC",
        "Comfortable attacking from her guard",
        "Never past R2"],
       ["Big height and reach gap against Chiasson",
        "Striking defense: was hurt by Mullins",
        "Untested in R3"],
       ["Use length and keep her at range with the jab and kicks",
        "Stay off the mat and out of her guard; don't throw lazy strikes from top",
        "Make it a three-round fight and test her conditioning"],
       [n("2026-06-20", "Submitted Melissa Mullins with an armbar at 3:16 of R1 after being hurt early.", "cage_mullins"),
        n("2026-11-03", "Wikipedia lists her at No. 11; the UFC.com event page shows the Chiasson bout as No. 9 vs No. 11.",
          "wiki_mesquita")],
       ["cage_mullins", "wiki_mesquita", "wiki_event", "ufc_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Jared Gordon",
       "A 38-year-old lightweight veteran from Queens, New York (21-9, 1 NC; 9-8 UFC), a former CFFC champion and BJJ black belt "
       "who now fights out of Florida. He has lost three of his last four: a split to Nasrat Haqparast, an R3 TKO to Rafa "
       "Garcia and a first-round guillotine to Jim Miller in May. He faces Melquizael Costa, who moves up from featherweight.",
       {"Striking": "Busy boxer and kicker: about 5.3 significant strikes a minute at 52%, but he absorbs about 4.8. Against Miller he "
                    "pushed him to the fence, went to the body with right hands and rocked him with a right over the top (Cageside "
                    "Press). Eight KO/TKO wins, most recently Thiago Moises in R1 (May 2025).",
        "Grappling": "Wrestles to control (about 1.6 takedowns per 15), but rarely submits anyone (two submissions, both regional). "
                     "He caught a Miller body kick for a takedown and was immediately caught in a guillotine (Cageside).",
        "Defense": "Durability has slipped. Five KO/TKO losses (two in R1, three in R3) and two submission losses (Miller R1, Grant "
                   "Dawson R3). Takedown defense is about 61%.",
        "Pace & cardio": "A grinder who goes the distance: 11 of his 21 wins are decisions, including two five-round regional fights. "
                         "His stoppage wins: eight KO/TKOs (four in R1, three in R2, one in R3) and two submissions (both R2). Three of his five KO/TKO losses came in R3, most recently Rafa Garcia in "
                         "2025, so he can be worn down late.",
        "Fight IQ": "Experienced and tough. Wikipedia notes many observers thought he beat Paddy Pimblett at UFC 282 despite losing "
                    "the decision. Has missed weight three times in his UFC career (Wikipedia), though not recently in our sources."},
       ["Pressure boxing with body work",
        "Takedowns for control rather than finishes",
        "Goes the distance often: 11 decision wins",
        "Three of five KO/TKO losses came in R3"],
       ["Age 38 and three losses in his last four",
        "Stopped in two straight fights (Garcia TKO, Miller submission)",
        "Neck exposure when he shoots",
        "Faces an opponent eight years younger who just went five rounds"],
       ["Make it a striking fight and press him in R3",
        "Punish his takedown entries with front headlocks or counters",
        "Use speed and variety; he absorbs a lot of strikes"],
       [n("2026-10-01", "Booked against Melquizael Costa at UFC 334 (Heavy, after an AG Fight report).", "heavy_gordon_costa"),
        n("2026-05-09", "Submitted by Jim Miller (guillotine) at 3:29 of R1 at UFC 328; Cageside notes it put him at 9-8 in the UFC "
                        "and three losses in four.", "cage_328_losers")],
       ["heavy_gordon_costa", "cage_miller_gordon", "cage_328_losers", "wiki_gordon", "wiki_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Melquizael Costa",
       "A 30-year-old Brazilian (26-8; 7-3 UFC; Chute Boxe) moving up from featherweight to lightweight for this fight (Heavy). "
       "His six-fight win streak ended in May when Arnold Allen beat him 50-45, 50-45, 49-46 in his first main event. Before "
       "that he stopped Dan Ige by TKO in R1 (Heavy).",
       {"Striking": "Varied, creative kickboxer: calf kicks, spinning attacks, high kicks and knees. His calf kicks began to land on "
                    "Allen in R2 and his kicks won exchanges in R3 (Cageside Press). Back-to-back R1 KO/TKO wins before Allen (Morgan "
                    "Charriere, Dan Ige). About 4.4 significant strikes a minute at 47%.",
        "Grappling": "Active off his back and opportunistic in scrambles. He reversed Allen to take his back in R1 (Cageside), and "
                     "has eight career submissions, including Andre Fili (R1) and Nuerdanbieke Shayilan (R3) in the UFC.",
        "Defense": "Takedown defense is the hole (about 58%). Allen took him down repeatedly, including 'repeatedly' in R5 (Cageside); "
                   "our data has Allen at 7-for-7 with over nine minutes of control. Thiago Moises (sub, R2) and Steve Garcia (TKO, "
                   "R2) are his two UFC stoppage losses, both in 2023.",
        "Pace & cardio": "Finishes come early but he can go long. 17 stoppage wins: R1 eleven (six KO, five sub), R2 two, R3 four. His "
                         "four stoppage losses: R1 one (2017), R2 two, R3 one (2018). He went 25 minutes with Allen but Cageside said he "
                         "looked tired in R5 and spent a lot of energy getting up after each takedown.",
        "Fight IQ": "Takes risks with spinning strikes, which has paid off (Ige). Kept pressing forward while bleeding against Allen. "
                    "Less clear how he handles a wrestler who can hold him down."},
       ["Calf kicks and spinning attacks",
        "Eleven R1 stoppages",
        "Back takes and submissions in scrambles",
        "Gets taken down by stronger grapplers"],
       ["First fight at lightweight in the UFC; size and strength against a natural 155er",
        "Takedown defense",
        "Coming off a five-round decision loss where he tired late"],
       ["Wrestle him and keep him on the mat",
        "Avoid open-range kicking exchanges",
        "Watch for spinning attacks; he threw them throughout the Allen fight"],
       [n("2026-10-01", "Booked against Jared Gordon at UFC 334, moving up to lightweight (Heavy).", "heavy_gordon_costa"),
        n("2026-05-16", "Lost a unanimous decision (50-45, 50-45, 49-46) to Arnold Allen in the UFC Vegas 117 main event, ending a "
                        "six-fight win streak.", "cage_allen"),
        n("2026-02-21", "Beat Dan Ige by first-round TKO at UFC Houston (per Heavy's recap of his recent run).", "heavy_gordon_costa")],
       ["heavy_gordon_costa", "cage_allen", "cage_v117_losers", "lowkick_v117", "wiki_event"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Evan Elder",
       "A 30-year-old lightweight (10-2; 3-2 UFC) on a three-fight win streak (Genaro Valdez, Darrius Flowers, Gauge Young). He "
       "hasn't fought since April 2025: a leg injury pulled him from a September 2025 bout with Tom Nolan (Rotowire). This is "
       "his first fight in about 19 months.",
       {"Striking": "Volume striker with leg kicks, body kicks, right hands and the odd spinning back kick (Cageside Press, on Young). "
                    "About 4.8 significant strikes a minute. Sherdog's Tom Feely called him an underrated, unflashy prospect who "
                    "'needs to continue developing some defensive comfort' and tends to get hit hard at least once a fight.",
        "Grappling": "Low takedown volume (about 0.7 per 15, 24% accuracy). Two submission wins, including Darrius Flowers in R2. "
                     "Preston Parsons took him down four times and controlled him in his UFC debut.",
        "Defense": "Takedown defense is the weak point (about 51%). Two losses: a decision to Parsons and a doctor stoppage for a cut "
                   "against Nazim Sadykhov in R3. Not finished by strikes in our data.",
        "Pace & cardio": "Goes the distance and wins late. Four of his ten wins are decisions; his six finishes: R1 four (three KO, one "
                         "sub), R2 one (sub), R3 one (KO). Both losses went into R3 or the full 15. Against Young, body shots slowed him "
                         "in R2 but he won R3 with heavier shots (Cageside).",
        "Fight IQ": "Steady and willing to brawl; Cageside noted he got drawn into more of a brawl in R2 against Young."},
       ["High-volume kickboxing with leg and body kicks",
        "Wins decisions: three straight",
        "Gets hit at least once a fight (Sherdog)",
        "Takedowns are a problem against wrestlers"],
       ["About 19 months out of action",
        "Leg injury in 2025 (Rotowire)",
        "Takedown defense against a powerful young opponent"],
       ["Take him down; wrestlers have had success",
        "Body work: it slowed him in R2 against Young",
        "Land the big shot early before his volume builds"],
       [n("2025-09-02", "Withdrew from a UFC Perth bout with Tom Nolan because of a leg injury.", "rotowire_elder"),
        n("2026-10-02", "Booked against Samuel Sanches at UFC 334.", "rotowire_elder"),
        n("2025-04-26", "Beat late-notice replacement Gauge Young by unanimous decision (30-27 x3).", "cage_young")],
       ["rotowire_elder", "cage_young", "sherdog_kc_prev", "wiki_event"],
       "thin")

# ---------------------------------------------------------------------------------------------------------------
report("Samuel Sanches",
       "A 23-year-old Brazilian lightweight (11-1) making his UFC debut. He earned his contract with a 2:01 R1 knockout of Chasen "
       "Blair on the Contender Series in September 2025, his eighth straight win. His planned debut against Tofiq Musayev in March "
       "2026 fell through when he withdrew for undisclosed reasons. He hasn't fought in about 14 months.",
       {"Striking": "Finisher: eight of his 11 wins are KO/TKOs. He finished Blair with a cross and a right hook after Blair was hurt "
                    "(Cageside Press). Our numbers on him (about 1.2 knockdowns per 15) rest mostly on one Contender Series fight.",
        "Grappling": "One submission win (R1). Little UFC-level information on his wrestling.",
        "Defense": "His only loss was an R1 submission in 2022 (Hugo Vargas). Little film against high-level opposition.",
        "Pace & cardio": "Early finisher: KO/TKOs six in R1, two in R2; one R1 submission; two decisions. Has gone 15 minutes twice "
                         "on the regional scene.",
        "Fight IQ": "Not enough evidence yet. He said after the Contender Series that he still has 'a lot of fire to burn' (Cageside)."},
       ["R1 knockouts: six of eight KO/TKOs",
        "Combinations to finish a hurt opponent",
        "Eight-fight win streak entering the UFC"],
       ["UFC debut on a big card",
        "14 months out; withdrew from his first booking (reason undisclosed; Rotowire's later note calls it an injury)",
        "Only loss was a submission"],
       ["Take him into deep water: he has gone 15 minutes only twice",
        "Grapple and test his submission defense",
        "Don't stand in front of him early"],
       [n("2026-03-05", "Withdrew from his March 28 UFC Seattle debut against Tofiq Musayev for undisclosed reasons; Ignacio Bahamondes "
                        "replaced him.", "rotowire_sanches"),
        n("2026-10-02", "Booked against Evan Elder at UFC 334 (Rotowire, citing Heavy).", "rotowire_sanches"),
        n("2025-09-09", "Knocked out Chasen Blair at 2:01 of R1 on the Contender Series to earn a UFC contract.", "cage_sanches_dwcs")],
       ["rotowire_sanches", "cage_sanches_dwcs", "wiki_event"],
       "thin")

# ---------------------------------------------------------------------------------------------------------------
report("Juan Diaz",
       "A 28-year-old Peruvian bantamweight (16-1-1; 1-0 UFC), former LUX Fighting League champion, on a nine-fight win streak. "
       "He won his contract with a second-round spinning back elbow KO of Won Il Kwon and submitted Malcolm Wellmaker in R2 of his "
       "debut for a Performance of the Night bonus. His scheduled opponent Adrian Yanez withdrew in mid-October after being "
       "hospitalized; no replacement has been named as of November 3.",
       {"Striking": "Kick-heavy, though he struggled to land clean against Wellmaker and seemed wary of his power (Cageside Press). He "
                    "dropped Wellmaker with a right hand after catching a kick in R1. Five KO/TKO wins, including the spinning elbow "
                    "on the Contender Series (Heavy).",
        "Grappling": "His main weapon. About 3.7 takedowns per 15. Against Wellmaker he took him down repeatedly, took the back as "
                     "Wellmaker stood up and finished with a rear-naked choke at 4:08 of R2 (Cageside, LowKick MMA). Three career "
                     "submissions.",
        "Defense": "Lost only once, a decision to Rodrigo Vera in 2021, plus a 2018 draw. Never stopped in our data. Wellmaker's body "
                   "kicks were the better strikes early in their fight (Cageside).",
        "Pace & cardio": "Proven over long fights: 8 of his 16 wins are decisions, and in LUX he won two five-round decisions and a "
                         "R4 stoppage in a five-round fight. Finishes: R1 three (one KO, two subs), R2 three (two KOs, one sub), R3 one, "
                         "R4 one.",
        "Fight IQ": "Patient; builds takedowns into back control. He landed a knee that appeared illegal on a downed Wellmaker in R1 "
                    "and was warned, with no point taken (LowKick MMA)."},
       ["Chain takedowns into back takes",
        "Rear-naked choke finishes",
        "Comfortable in long fights, including five-rounders",
        "Never stopped"],
       ["No confirmed opponent 11 days out",
        "Striking was tentative against a powerful opponent",
        "Only one UFC fight"],
       ["Stop the first takedowns and keep it standing",
        "Body kicks worked early for Wellmaker",
        "Don't give up the back when getting up"],
       [n("2026-10-19", "Adrian Yanez withdrew from their UFC 334 bout, saying on Instagram he had been hospitalized. No replacement "
                        "was announced, and SI said it was unclear whether the UFC could find one on short notice.", "si_yanez_out"),
        n("2026-11-03", "Wikipedia lists the bout as Juan Diaz vs. TBA and says it isn't known if a replacement will be sought. The "
                        "UFC.com event page still showed Yanez vs. Diaz when checked. No named replacement found.", "wiki_event"),
        n("2026-05-16", "Submitted Malcolm Wellmaker (rear-naked choke, 4:08 of R2) in his UFC debut; Cageside called it a huge "
                        "upset.", "cage_wellmaker")],
       ["si_yanez_out", "heavy_diaz_booking", "cage_wellmaker", "lowkick_wellmaker", "wiki_event", "ufc_event"],
       "thin")


out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
