"""Scouting reports (part B) for UFC Fight Night: Bonfim vs. Brady (UFC Vegas 124 / Fight Night 293, 2026-11-07),
first pass written 2026-10-27.

Covers Elekana vs. Fernando, Karine Silva vs. Gabriella Fernandes, Delano vs. Magomedov and Nakamura vs. Schmid.
Fight-week previews aren't out yet: these draw on recent-fight recaps, booking news, interviews and our verified
records. Round/method counts are taken from data/verified/fights.csv. Later runs should refresh them with the
Sherdog/MMA Mania/UFC.com previews and weigh-in news.
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
    "bn_card": src("Boxing News", "UFC Vegas 124 Fight Card Set For November",
                   "https://boxingnews.com/news/ufc-vegas-124-fight-card-bonfim-brady", "2026-09-29"),
    # Elekana
    "wiki_elekana": src("Wikipedia", "Billy Elekana", "https://en.wikipedia.org/wiki/Billy_Elekana", "2026-10-27"),
    "sucka_elekana": src("MMA Sucka", "Lucas Fernando vs. Billy Elekana set for UFC Vegas 124",
                         "https://mmasucka.com/news/lucas-fernando-vs-billy-elekana-set-for-ufc-vegas-124/", "2026-09-15",
                         "Felipe Castello Branco"),
    "cage_guskov": src("Cageside Press", "UFC 311: Bogdan Guskov Pummels, Submits Newcomer Billy Elekana",
                       "https://cagesidepress.com/2025/01/18/ufc-311-bogdan-guskov-pummels-submits-newcomer-billy-elekana",
                       "2025-01-18", "Shawn Bitter"),
    "cage_aslan": src("Cageside Press", "UFC Abu Dhabi: Billy Elekana Claims Win Over Ibo Aslan in Low-Action Affair",
                      "https://cagesidepress.com/2025/07/26/ufc-abu-dhabi-billy-elekana-claims-win-over-ibo-aslan-in-low-action-affair",
                      "2025-07-26"),
    "cage_christian": src("Cageside Press", "UFC Vegas 110: Billy Elekana Rocks, Chokes Out Kevin Christian",
                          "https://cagesidepress.com/2025/11/01/ufc-vegas-110-billy-elekana-rocks-chokes-out-kevin-christian",
                          "2025-11-01", "Shawn Bitter"),
    "lowkick_tafa": src("LowKick MMA", "Billy Elekana Survives Early Scare, Chokes Out Junior Tafa - UFC 325 Highlights",
                        "https://www.lowkickmma.com/junior-tafa-vs-billy-elekana-ufc-325/", "2026-01-31", "Craig Pekios"),
    "cage_v118_next": src("Cageside Press", "What's Next: UFC Vegas 118 Losers",
                          "https://cagesidepress.com/2026/06/08/whats-next-ufc-vegas-118-losers/", "2026-06-08"),
    # Lucas Fernando
    "cage_tobias": src("Cageside Press", "UFC 330: Lucas Fernando On Point, Stops Rafael Tobias in Immensely Impressive Debut",
                       "https://cagesidepress.com/2026/08/15/ufc-330-lucas-fernando-on-point-stops-rafael-tobias-in-immensely-impressive-debut/",
                       "2026-08-15", "Shawn Bitter"),
    "lowkick_tobias": src("LowKick MMA", "UFC 330: Lucas Fernando Shines In Debut With Body-Kick Assault On Rafael Tobias",
                          "https://www.lowkickmma.com/ufc-330-lucas-fernando-stops-rafael-tobias/", "2026-08-15",
                          "Pranav Pandey"),
    "bn_fernando": src("Boxing News", "Fernando Credits Wife After Nearly Quitting MMA",
                       "https://boxingnews.com/news/fernando-wife-quit-ufc-330/", "2026-08-17", "Tom Rashid"),
    "rotowire_fernando": src("Rotowire", "Lucas Fernando MMA Stats & News",
                             "https://www.rotowire.com/mma/player/lucas-fernando-2802", "2026-10-27"),
    "cage_lfa234": src("Cageside Press", "LFA 234: Fernando vs. Soares Full Results",
                       "https://cagesidepress.com/2026/05/29/lfa-234-fernando-vs-soares-full-results/", "2026-05-29"),
    # Karine Silva
    "wiki_karine": src("Wikipedia", "Karine Silva", "https://en.wikipedia.org/wiki/Karine_Silva", "2026-10-27"),
    "cage_jasud": src("Cageside Press", "Jasmine Jasudavicius Overcomes Karine Silva's Submission Attempts in Key Win",
                      "https://cagesidepress.com/2026/04/18/jasmine-jasudavicius-overcomes-karine-silvas-submission-attempts-in-key-win/",
                      "2026-04-18", "Eddie Law"),
    "cage_barber": src("Cageside Press", "UFC 323: Maycee Barber Outlasts Karine Silva After Foul",
                       "https://cagesidepress.com/2025/12/06/ufc-323-maycee-barber-outlasts-karine-silva-after-foul",
                       "2025-12-06", "Gabriel Gonzalez"),
    "cage_winnipeg_next": src("Cageside Press", "What's Next: UFC Winnipeg Losers",
                              "https://cagesidepress.com/2026/04/20/whats-next-ufc-winnipeg-losers/", "2026-04-20"),
    # Gabriella Fernandes
    "cage_wang": src("Cageside Press", "UFC Macau: Gabriella Fernandes Shocks with Upset Submission of Wang Cong",
                     "https://cagesidepress.com/2024/11/23/ufc-macau-gabriella-fernandes-shocks-with-upset-submission-of-wang-cong",
                     "2024-11-23", "Bryson Hester"),
    "cage_oneill": src("Cageside Press", "UFC Seattle: Casey O'Neill Makes Emphatic Statement in Return, Stops Gabriella Fernandes",
                       "https://cagesidepress.com/2026/03/28/ufc-seattle-casey-oneill-makes-emphatic-statement-in-return-stops-gabriella-fernandes",
                       "2026-03-28", "Jay Anderson"),
    "bjp_seattle": src("BJPenn.com", "UFC Seattle: 'Adesanya vs. Pyfer' Live Results and Highlights",
                       "https://www.bjpenn.com/mma-news/ufc-seattle/ufc-seattle-adesanya-vs-pyfer-live-results-and-highlights/",
                       "2026-03-28"),
    "bjp_v109": src("BJPenn.com", "UFC Vegas 109: 'Dolidze vs. Hernandez' Live Results and Highlights",
                    "https://www.bjpenn.com/mma-news/ufc-vegas-109/ufc-vegas-109-dolidze-vs-hernandez-live-results-and-highlights/",
                    "2025-08-09"),
    # Delano
    "cage_ruchala": src("Cageside Press", "UFC Vegas 115: Jose Delano Makes Successful Debut Against Robert Ruchala",
                        "https://cagesidepress.com/2026/04/04/ufc-vegas-115-jose-delano-makes-successful-debut-against-robert-ruchala/",
                        "2026-04-04", "Shawn Bitter"),
    "cage_delano_dwcs": src("Cageside Press", "DWCS Winner Jose Delano Wants on UFC Rio Card",
                            "https://cagesidepress.com/2025/08/20/jose-delano-dwcs-ufc-rio/", "2025-08-20",
                            "Patrick Danna, Jay Anderson"),
    "tribuna_delano": src("Tribuna do Sertao (Esporte News Mundo)",
                          "Jose Delano projeta duelo contra quirguiz no UFC: 'ele nao se entrega'",
                          "https://tribunadosertao.com.br/esportes/2026/10/15/998354-jose-delano-projeta-duelo-contra-quirguiz-no-ufc-ele-nao-se-entrega",
                          "2026-10-15"),
    # Magomedov
    "cage_twister": src("Cageside Press", "UFC Vegas 119: Murtazali Magomedov Hits Rare Twister on Melsik Baghdasaryan",
                        "https://cagesidepress.com/2026/06/20/ufc-vegas-119-murtazali-magomedov-hits-rare-twister-on-melsik-baghdasaryan/",
                        "2026-06-20", "Shawn Bitter"),
    "cage_askarov": src("Cageside Press", "UFC Vegas 119: Murtazali Magomedov Learned Twister A Month Ago From Ex-UFC Star",
                        "https://cagesidepress.com/2026/06/20/ufc-vegas-119-murtazali-magomedov-learned-twister-month-ago/",
                        "2026-06-20", "Destiny McCubbin, Jay Anderson"),
    "ufc_magomedov": src("UFC.com", "Murtazali Magomedov's Wait Is Finally Over",
                         "https://www.ufc.com/news/murtazali-magomedovs-wait-finally-over-ufc-vegas-119", "2026-06-19",
                         "Simon Head"),
    # Nakamura
    "cage_szalay": src("Cageside Press",
                       "UFC 325: Keiichiro Nakamura Makes Massive Comeback, Finishes Sebastian Szalay in Road to UFC 4 Win",
                       "https://cagesidepress.com/2026/01/31/ufc-325-keiichiro-nakamura-makes-massive-comeback-finishes-sebastian-szalay-in-road-to-ufc-4-win/",
                       "2026-01-31", "Shawn Bitter"),
    "ufc_rtu_final": src("UFC.com", "Road to UFC Season 4 Finale Preview",
                         "https://www.ufc.com/news/road-ufc-season-4-finale-preview", "2026-01-26", "E. Spencer Kyte"),
    "cage_rtu_sf": src("Cageside Press", "Road to UFC 4 Episode 6 Full Results",
                       "https://cagesidepress.com/2025/08/22/road-to-ufc-4-episode-6-full-results", "2025-08-22"),
    # Schmid
    "lowkick_schmid": src("LowKick MMA", "UFC Perth Main Card Sees Last-Minute Twist As Debutant Steps In On Three Days' Notice",
                          "https://www.lowkickmma.com/ufc-perth-ollie-schmid-short-notice/", "2026-04-30", "Pranav Pandey"),
    "cage_rahiki": src("Cageside Press", "Marwan Rahiki Remains Undefeated With Devastating KO Over Schmid",
                       "https://cagesidepress.com/2026/05/02/marwan-rahiki-remains-undefeated-with-devastating-ko-over-schmid/",
                       "2026-05-02", "Eddie Law"),
    "cage_perth_next": src("Cageside Press", "What's Next: UFC Perth Losers",
                           "https://cagesidepress.com/2026/05/04/whats-next-ufc-perth-losers-2/", "2026-05-04"),
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
report("Billy Elekana",
       "A long American light heavyweight (10-2; 3-1 UFC; Uprising MMA, Las Vegas; about 6-foot-3) with a jiu-jitsu base and "
       "a patient counter-striking game. After a short-notice debut loss to Bogdan Guskov he has won three straight, the last "
       "two by rear-naked choke after hurting the opponent first. He has been dropped and nearly choked, and his cardio broke "
       "on one week's notice, so the profile is 'dangerous opportunist with questions in a hard pace'.",
       {"Striking": "Patient and economical (about 3 significant strikes landed per minute). He lets opponents lead, eats some "
                    "calf kicks, and waits for a counter: he dropped Kevin Christian with a right hand when Christian overextended "
                    "(Cageside Press), and hurt Junior Tafa with a combination in R2 (LowKick). Can be very low-output: the Ibo "
                    "Aslan win was a cautious 15-minute kickboxing match Cageside called a 'low-action affair', with his best shot "
                    "coming in the final 90 seconds. Three career KO/TKO wins, all in R1 and all on the regional scene (2021, "
                    "2022, 2024).",
        "Grappling": "The finishing weapon. Six of his ten wins came inside the distance, three by submission (R2 regional, R1 "
                     "Christian RNC, R2 Tafa RNC). His pattern in the UFC is strike-to-hurt, then follow to the mat and take the back "
                     "immediately. Against Guskov he had back control and a body triangle for much of R1 (220 seconds of control in "
                     "our data) but couldn't finish. Takedown entries are not a strength (1 for 5 against Tafa, 0 for 3 against Aslan).",
        "Defense": "Durability has been tested. Tafa landed a big right in the opening minute and our data credits Tafa with a "
                   "knockdown in R1; Elekana recovered and won R2. Guskov nearly choked him at the end of R1 (he tapped after the "
                   "bell, per Cageside) and then broke him down with body shots in R2. He absorbs about as much as he lands "
                   "(roughly 3.1 per minute each way).",
        "Pace & cardio": "Finishes come in R1-R2: all six career stoppages were in the first two rounds (four in R1, two in R2). "
                         "Four of his wins went the full 15 minutes, including two split decisions (one PFL, one regional loss to "
                         "Daniel Compton by split). His only stoppage loss came in R2 when his gas tank emptied after a grappling-heavy "
                         "R1 on about a week's notice (Cageside). In longer fights he slows down rather than speeds up; he has never "
                         "finished anyone in R3.",
        "Fight IQ": "Composed under fire: he survived Tafa's early onslaught and turned it, and stayed calm while losing the leg-kick "
                    "battle to Christian. Willing to take short-notice fights. Withdrew from a June 2026 bout with Iwo Baraniewski "
                    "for undisclosed reasons."},
       ["Patient counter-puncher who waits for an opponent to overcommit",
        "Hurt-then-take-the-back sequence; two straight RNC finishes (R1, R2)",
        "All six career stoppages in R1-R2; never finished anyone in R3",
        "Slow, cautious decisions when nothing opens up (Aslan)"],
       ["Was dropped by Tafa in R1 and broken down by Guskov's body work in R2",
        "Cardio after a grappling-heavy first round",
        "Low output can cost him rounds against a busy, rangy striker",
        "Age differs by source: Wikipedia gives a 1995 birth date (31); MMA Sucka says 33"],
       ["Out-work him at range with kicks to the legs and body; don't overextend into his right hand",
        "Make him grapple and carry weight early, then push the pace in R2-R3",
        "Defend the back in every scramble when hurt"],
       [n("2026-09-15", "Booked against Lucas Fernando at UFC Vegas 124 on Nov. 7, his first fight since January.", "sucka_elekana"),
        n("2026-06-08", "Withdrew from a June 6 bout with Iwo Baraniewski (undisclosed reasons per Wikipedia); Junior Tafa replaced "
                        "him and was knocked out in R1.", "cage_v118_next"),
        n("2026-01-31", "Submitted Junior Tafa with a rear-naked choke at 3:18 of R2 after surviving an early right hand.", "lowkick_tafa")],
       ["wiki_elekana", "sucka_elekana", "cage_guskov", "cage_aslan", "cage_christian", "lowkick_tafa", "cage_v118_next",
        "wiki_event", "bn_card"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Lucas Fernando",
       "A tall Brazilian light heavyweight (14-3, age 30; about 6-foot-4) and former two-division LFA champion, on a five-fight "
       "win streak with four straight stoppages. He debuted in August with a third-round TKO of Rafael Tobias in which he "
       "out-landed him heavily with kicks at every level. Very active: November 7 will be his third fight in about five months.",
       {"Striking": "Range kickboxer with power. Against Tobias he used the jab to control distance and set up heavy calf kicks, "
                    "body kicks and right hands, dropped Tobias with a jab-right sequence in R2, and threw wheel and head kicks "
                    "(Cageside Press, LowKick). Rotowire counted a 69-13 significant-strike edge. Eight KO/TKO wins: six in R1, "
                    "one in R3 (Tobias, knee to the body then elbows), one in R4 of a five-round LFA middleweight title fight.",
        "Grappling": "Mostly defensive. Got back up quickly when Tobias caught a kick and took him down (LowKick). Two early "
                     "regional submission wins (2018, 2019). On the Contender Series in 2023 he went 3 for 10 on takedowns and "
                     "split control time evenly with Cesar Almeida, but lost the striking 28-71.",
        "Defense": "Never stopped: all three losses were decisions (Diego Dias 2020, Cesar Almeida on DWCS 2023, Azamat Bekoev over "
                   "five rounds in LFA in 2023). The Almeida loss, at middleweight, is the template for beating him: out-volume "
                   "him and stay busy.",
        "Pace & cardio": "Early finisher who can also close late. Ten of 14 wins were stoppages: eight in R1, one in R3, one in R4; "
                         "his last two LFA wins took 63 and 88 seconds. He went 25 minutes with Bekoev (a loss) and won another "
                         "five-rounder by R4 TKO, so his gas tank is proven. Against Tobias he was more patient in R3, waited after "
                         "buckling him with a leg kick, then finished with a body knee.",
        "Fight IQ": "Patient once ahead; picks strikes rather than rushing. Said he nearly quit after the Contender Series loss and "
                    "credits his wife for keeping him in the sport (Boxing News, citing Sherdog and MMA Fighting). Spent a month in "
                    "the US before his debut."},
       ["Jab and calf kicks to set up body kicks, right hands and knees",
        "Seven R1 stoppages; last two LFA wins inside 90 seconds",
        "Can finish late too: R3 TKO in UFC debut, R4 TKO in an LFA title fight",
        "Never finished; all three losses on the cards"],
       ["Only one UFC fight, against a winless opponent",
        "Lost the volume battle badly to Almeida (2023)",
        "Short turnaround: third fight since late May",
        "Record differs by source: LowKick said the debut win made him 9-1; our data and most outlets have 14-3"],
       ["Take away his range: pressure him, clinch, and wrestle",
        "Out-volume him, as Almeida did",
        "Check the calf kicks early so he can't build from them"],
       [n("2026-09-15", "Booked against Billy Elekana for Nov. 7 at UFC Vegas 124.", "sucka_elekana"),
        n("2026-08-15", "Debuted with a TKO (knee to the body and elbows) of Rafael Tobias at 1:10 of R3 at UFC 330.", "cage_tobias"),
        n("2026-05-29", "Defended the LFA light heavyweight title with a 1:28 R1 TKO of Leon Soares before signing.", "cage_lfa234"),
        n("2026-08-17", "Said he considered quitting after his 2023 Contender Series loss.", "bn_fernando")],
       ["cage_tobias", "lowkick_tobias", "rotowire_fernando", "bn_fernando", "cage_lfa234", "sucka_elekana", "wiki_event",
        "bn_card"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Karine Silva",
       "A Brazilian flyweight grappler (19-7; 5-3 UFC; Fighting Nerds) and BJJ black belt who opened her UFC run with three "
       "first-round submissions but has gone 1-3 in her last four, all decisions. She is always dangerous off her back and in "
       "scrambles, but ranked opponents have held her down or out-struck her for 15 minutes.",
       {"Striking": "A support tool for her grappling. Calf kicks, overhand rights and stance switches at range, plus a sharp "
                    "elbow up the middle against Jasudavicius (Cageside Press). Low volume (about 2.4 significant strikes per "
                    "minute) and was out-landed 55-21 by Maycee Barber. Started in sanda, per Wikipedia.",
        "Grappling": "Her weapon. Three UFC submissions, all in R1: a brabo choke (Botelho), kneebar (Ketlen Souza) and guillotine "
                     "(Moroz), plus an R2 submission on the Contender Series. Very active off her back: triangles from guard and a "
                     "guillotine on Jasudavicius's single leg; back take and RNC attempt plus heel-hook and leg-lock attempts against "
                     "Barber. She'll also wrestle offensively (5 for 6 on takedowns against Ariane Lipski).",
        "Defense": "Not easy to stop: her only stoppage losses were long ago (TKO in 2013, two R1 submissions in 2014 and 2017). "
                   "Takedown defense is the problem (about 41%): Jasudavicius held her down for over eight minutes, Barber had more "
                   "than six minutes of control, and her submission attempts from the bottom have not been converting into finishes "
                   "or reversals against good top players.",
        "Pace & cardio": "Front-loaded. Every UFC finish came in R1 (three) and her DWCS submission came in R2; she hasn't finished "
                         "anyone since August 2023. Her last five fights all went to decision, and in the losses the later rounds "
                         "slipped away: Barber came on after Silva won R1 with back control, and Jasudavicius finished R3 on top with "
                         "ground-and-pound. Still active late (Barber R3 leg locks), but not winning late rounds against ranked "
                         "opposition.",
        "Fight IQ": "Comfortable fighting off her back and will gamble on submissions, which costs rounds when they fail. Landed an "
                    "illegal upkick on a downed Barber in R2; no point was taken (Cageside)."},
       ["Submission threat from every position, especially off the bottom",
        "All UFC finishes in R1; five straight decisions since",
        "Wins R1 with a takedown or back take, then loses ground in R2-R3 against strong opposition",
        "Last three losses all unanimous decisions"],
       ["1-3 in her last four",
        "Takedown defense and getting held down",
        "Low striking output",
        "Age differs by source: Wikipedia gives a December 1993 birth date (32); our data says 33"],
       ["Stay out of her guard and scramble zones; don't hand her the back or a neck on a lazy single leg",
        "Out-strike her at range: she lands little",
        "Bank R2-R3 with volume or top control once the early submission threat is past"],
       [n("2026-04-18", "Lost a unanimous decision (29-28 x3) to Jasmine Jasudavicius; threatened triangles and a guillotine but "
                        "spent long stretches on her back.", "cage_jasud"),
        n("2026-04-20", "Cageside noted she has lost three of her last four and fell to 5-3 in the UFC.", "cage_winnipeg_next"),
        n("2025-12-06", "Lost a decision to Maycee Barber after winning R1 with back control; an illegal upkick drew a warning.",
          "cage_barber")],
       ["wiki_karine", "cage_jasud", "cage_barber", "cage_winnipeg_next", "wiki_event", "bn_card"],
       "good")

# ---------------------------------------------------------------------------------------------------------------
report("Gabriella Fernandes",
       "A Brazilian flyweight kickboxer (11-4; 3-3 UFC; MMA Masters, per our data) who had won three straight, including a big "
       "upset submission of Wang Cong, before being knocked out by Casey O'Neill in R1 in March. She does her best work in "
       "the middle and late rounds; her other UFC losses came against wrestlers.",
       {"Striking": "Volume kickboxing with head kicks and body work. Head kick then left hand to drop Wang in R2 (Cageside Press); "
                    "body shots, a cut and a knee in the Stoliarenko decision. Throws a lot (119 significant strikes against Carli "
                    "Judice), but absorbs about 5 per minute. Three KO/TKO wins, all regional: one in R1, two in R3.",
        "Grappling": "Mostly defensive. Stuffed all six of Stoliarenko's takedown attempts. Will jump on the back of a hurt opponent "
                     "(RNC on Wang after the knockdown). Two regional R2 submissions. Doesn't wrestle much herself (2 for 8 against "
                     "Judice, 0 for 2 against Wang).",
        "Defense": "Two clear holes. First, wrestlers: Jasudavicius beat her in her UFC debut and Tereza Bleda held her down for "
                   "nearly 11 minutes in 2023. Second, chin and hands-down exchanges: O'Neill hurt her with a clean shot to the jaw "
                   "and finished her at 3:11 of R1, the only stoppage loss of her career.",
        "Pace & cardio": "A slow burner. Her finishes come later: of six stoppage wins, one was in R1, three in R2 and two in R3. In the "
                         "Wang fight she lost R1 clearly (Wang landed body kicks and side kicks) and turned it in R2. Five of her six UFC "
                         "fights went the distance. Late-round strength, early-round vulnerability.",
        "Fight IQ": "Patient; adjusts after a slow first round. Pulled off a roughly 6-to-1 upset over Wang, so she can win as a "
                    "big underdog. Coming off a knockout loss and seven months out."},
       ["Kickboxer who builds through rounds; finishes skew to R2-R3",
        "Head kick / left hand, then jumps on the back of a hurt opponent",
        "Good defensive wrestling against a non-wrestler (6 for 6 against Stoliarenko)",
        "Tends to lose R1 against fast starters"],
       ["Coming off an R1 knockout loss",
        "Gets held down by real wrestlers (Bleda, Jasudavicius)",
        "Absorbs a lot of strikes"],
       ["Take her down and hold her there; she doesn't threaten much off her back",
        "Win R1 early before she settles",
        "Counter her head-kick attempts"],
       [n("2026-03-28", "Knocked out by Casey O'Neill (punches) at 3:11 of R1 at UFC Seattle.", "cage_oneill"),
        n("2025-08-09", "Beat Julija Stoliarenko by unanimous decision (30-27, 29-28 x2).", "bjp_v109")],
       ["cage_oneill", "bjp_seattle", "cage_wang", "bjp_v109", "wiki_event", "bn_card"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Jose Mauro Delano",
       "A high-volume Brazilian featherweight (17-3; 1-0 UFC; Brazilian Top Team) from Pernambuco, on a five-fight win streak. "
       "He earned his contract with a 100-plus-strike decision on the 2025 Contender Series and beat Robert Ruchala on the "
       "cards in his April debut. A clean boxer who builds his lead and gets stronger as fights go on.",
       {"Striking": "The engine. Very high output and accuracy in his two UFC-promoted fights (146 of 222 against Exposito, 107 of "
                    "172 against Ruchala, per our data). One-two, a strong left hand, right-left into a leg kick, body-head "
                    "combinations; he takes angles and slips well (Cageside Press). Four career KO/TKO wins (R1 x2, R2, R3).",
        "Grappling": "Rarely shoots (0 for 5 against Ruchala). Shrugged off Ruchala's tie-ups and kneed him on the way in "
                     "(Cageside). Five regional submissions (R1 x3, R2, R3) show a real back-up game, but he hasn't needed it lately.",
        "Defense": "Solid: strikes defense about 64% in our numbers. Three career losses: a 2014 decision, a 2015 R1 submission, "
                   "and an R3 TKO to Gabriel Santos in LFA in January 2023, his last loss. Takedown defense has held up in the UFC, "
                   "but has not yet been tested by a strong chain wrestler.",
        "Pace & cardio": "A late-round fighter. He finished the Ruchala fight with heavy body work and a clean "
                         "one-two in the last minute (Cageside) and out-landed him 107-67 overall; won two five-round LFA decisions "
                         "in 2022. Eight wins on the cards. His finishes are spread out "
                         "(R1 x5, R2 x2, R3 x2) but his last two fights went 15 minutes. Admitted to nerves early in the rounds of his "
                         "debut (Esporte News Mundo).",
        "Fight IQ": "Composed and disciplined. Plans to fight a patient, planned game against Magomedov, arguing Magomedov's "
                    "previous opponents all went all-or-nothing against him (Esporte News Mundo, Oct. 15). Calls Magomedov a fighter who "
                    "never gives up."},
       ["Very high-volume, accurate boxing with body work",
        "Gets stronger as the fight goes; proven over five rounds",
        "Decision-heavy lately: last two fights went the distance",
        "Rarely takes the fight to the mat himself"],
       ["Hasn't faced a finisher of Magomedov's type in the UFC",
        "Takedown defense untested against a strong wrestler",
        "One stoppage loss in R3 (Santos, 2023)"],
       ["Take him down and keep him there; he doesn't wrestle offensively",
        "Hurt him early before his volume piles up",
        "Make him defend the back in scrambles"],
       [n("2026-10-15", "Said he'll fight a patient, planned game against Magomedov and feels calmer without debut pressure.",
          "tribuna_delano"),
        n("2026-04-04", "Beat Robert Ruchala by unanimous decision (30-26, 29-27, 29-27) in his UFC debut; Ruchala lost a point for "
                        "grabbing the fence.", "cage_ruchala")],
       ["cage_ruchala", "cage_delano_dwcs", "tribuna_delano", "wiki_event", "bn_card"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Murtazali Magomedov",
       "An unbeaten Kyrgyz featherweight (11-0, age 27; 1-0 UFC; about 180 cm) and former Octagon League champion who has "
       "finished every opponent: five KO/TKOs and six submissions. He won his contract with a 97-second TKO on the 2025 "
       "Contender Series and submitted Melsik Baghdasaryan with a twister in 77 seconds on his UFC debut, earning a bonus.",
       {"Striking": "Has knockout power (five KO/TKO wins). Dropped Brahyam Zurcher with a jab on the Contender Series and finished "
                    "with punches at 1:37 of R1. Little UFC tape: 14 significant strikes landed across his two UFC-promoted fights.",
        "Grappling": "Scrambler and back-taker. He took Baghdasaryan down when Baghdasaryan got too aggressive, hooked both legs, "
                     "rolled to the back and locked up a modified twister he'd learned from Askar Askarov a month before (Cageside "
                     "Press). Six submission wins, four in R1. Describes himself as rounded: 'I know wrestling, I know striking' "
                     "(UFC.com).",
        "Defense": "Never lost, never been to a decision, so almost nothing is known about how he handles being hurt or behind.",
        "Pace & cardio": "A very fast starter, but not only that. Of 11 finishes, seven came in R1, two in R2 and two in R3 (a TKO and "
                         "a submission). He has never gone 15 minutes, and the deepest he has gone is about 13 minutes. Three of "
                         "his wins came on one night in a 2022 regional grand prix.",
        "Fight IQ": "Confident and opportunistic; capitalises immediately on an opponent's mistake. Wants to fight every three to "
                    "four months; his debut came about nine months after earning his contract."},
       ["Finished all 11 opponents: 5 KO/TKO, 6 submissions",
        "Seven of 11 finishes in R1",
        "Punishes aggression with a takedown and a back take",
        "Has finished in R3 twice, so the threat doesn't disappear late"],
       ["Never been past R3 or to the judges",
        "Untested when hurt or behind",
        "Only 2:54 of UFC-promoted cage time in total",
        "Record differs by source: Esporte News Mundo said ten wins; our data and Cageside have 11-0"],
       ["Don't overcommit to exchanges or shots early; he punishes mistakes",
        "Drag him into R3 with volume and see how he holds up",
        "Defend the back in scrambles"],
       [n("2026-06-20", "Debuted with a twister submission of Melsik Baghdasaryan at 1:17 of R1 and a Performance of the Night bonus.",
          "cage_twister"),
        n("2026-06-20", "Said Askar Askarov showed him the twister about a month before the fight.", "cage_askarov")],
       ["cage_twister", "cage_askarov", "ufc_magomedov", "tribuna_delano", "wiki_event", "bn_card"],
       "thin")

# ---------------------------------------------------------------------------------------------------------------
report("Keiichiro Nakamura",
       "A Japanese featherweight (8-1, age 28; EXFIGHT) and the Road to UFC Season 4 featherweight "
       "tournament winner. Seven of his eight wins are KO/TKOs, and he has won eight straight since losing his pro "
       "debut. He came from two rounds down to stop Sebastian Szalay with a knee in R3 of the final.",
       {"Striking": "Power striker who uses knees as a finisher. Knee up the middle on Eoh Jin Park's takedown attempt in R2 of "
                    "the quarterfinal; knee to the chin to drop Szalay in R3 (Cageside Press). Works from range with front kicks "
                    "early, then turns to pressure. Five straight R1 KO/TKOs on the Japanese regional scene before Road to UFC.",
        "Grappling": "Defensive. Park went 0 for 6 on takedowns against him. Szalay got a takedown in R2 of the final. His only loss "
                     "was an R3 submission in his 2022 pro debut.",
        "Defense": "Was out-struck 79-45 by Szalay and hurt by a head clash in R2; Cageside described him as wild and off-balance "
                   "in that round. He absorbs about 4.4 significant strikes per minute.",
        "Pace & cardio": "A slow starter in his best tests, then dangerous late. Against Szalay he was down two rounds on all "
                         "cards before the R3 finish; Park went into R2; his semifinal with Kaiwen Li went 15 minutes. Against "
                         "regional opposition his finishes came in R1. Showed he can raise his pace in R3 when behind.",
        "Fight IQ": "Composed when behind. UFC.com describes him as a confident heel who smirks at partisan crowds. Coming off a "
                    "nine-month layoff since the final."},
       ["Seven KO/TKO wins; knees are his signature finisher",
        "Slow start against good opposition, strong R3 (came from two rounds down to stop Szalay)",
        "Punishes level changes with knees",
        "Good takedown defense"],
       ["Gave away rounds against Szalay and was out-struck",
        "Can look wild and off-balance under pressure",
        "Nine-month layoff"],
       ["Win R1-R2 with volume and pressure, but don't change levels carelessly into his knees",
        "Wrestle him; he's rarely been put on his back",
        "Expect him to come forward in R3"],
       [n("2026-01-31", "Won the Road to UFC Season 4 featherweight final with an R3 TKO (knee, then punches) of Sebastian Szalay "
                        "at UFC 325.", "cage_szalay"),
        n("2025-08-22", "Beat Kaiwen Li by unanimous decision (29-27, 29-28, 29-28) in the semifinal.", "cage_rtu_sf")],
       ["cage_szalay", "ufc_rtu_final", "cage_rtu_sf", "wiki_event"],
       "thin")

# ---------------------------------------------------------------------------------------------------------------
report("Oliver Schmid",
       "Ollie Schmid (4-3, age 26; City Kickboxing; a New Zealander, per LowKick) is an aggressive young featherweight who took "
       "his UFC debut on three days' notice in May and was knocked out by Marwan Rahiki in R1. This is his first UFC fight "
       "with a full camp. His record is thin and mostly from Australian and New Zealand regional shows.",
       {"Striking": "Aggressive starter: opened with kicks against Rahiki, surged forward with a flurry, and found some success "
                    "with straight punches before being dropped by a left hand (Cageside Press). Three R1 KO/TKO regional wins, "
                    "including a 15-second finish of Jeff Mesa in March.",
        "Grappling": "Little evidence either way. Was submitted in R3 of his 2023 pro debut.",
        "Defense": "The chin and defensive responsibility in exchanges are the concern: stopped by strikes in his last two losses "
                   "(Dimps Gillies, R3 TKO in 2024; Rahiki, R1 KO in 2026). Got trapped against the fence by Rahiki before the "
                   "finish.",
        "Pace & cardio": "Wins early, loses late or to power. All three stoppage wins came in R1; his one decision win went 15 "
                         "minutes. Two of his three losses came in R3 (submission 2023, TKO 2024). A fast starter whose tank and "
                         "durability later in fights are the question.",
        "Fight IQ": "Brave and willing (took the UFC fight on three days' notice while preparing for a regional bout), but still "
                    "very inexperienced: seven pro fights since 2023."},
       ["Aggressive, kick-led first-round starter",
        "Three R1 KO/TKO wins",
        "Two of three losses came in R3; the other was an R1 KO by a heavy hitter"],
       ["Durability: stopped by strikes in his last two losses",
        "Thin experience (seven pro fights)",
        "Late-fight cardio and grappling unknown at this level"],
       ["Weather his early aggression, then counter as he presses",
        "Make it a long fight; he has lost twice in R3",
        "Pressure him to the fence"],
       [n("2026-04-30", "Replaced the injured Jack Jenkins against Marwan Rahiki at UFC Perth on three days' notice.", "lowkick_schmid"),
        n("2026-05-02", "Knocked out by Rahiki at 2:47 of R1.", "cage_rahiki"),
        n("2026-05-04", "Cageside noted he had been preparing for a HEX Fight Series bout when the UFC called.", "cage_perth_next")],
       ["lowkick_schmid", "cage_rahiki", "cage_perth_next", "wiki_event"],
       "thin")


out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
