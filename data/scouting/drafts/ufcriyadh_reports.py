"""Scouting reports for UFC Fight Night: Adesanya vs. Magomedov (UFC Saudi Arabia, Riyadh, 2026-12-05).
First pass written Tuesday 2026-11-17, three weeks out: the card was announced Nov 7-16 and no previews are out yet.

These draw on our verified fight records (data/verified/fights.csv: methods and rounds below are counted from it), the
booking and odds coverage indexed by `scout news`, and the outlets cited per fighter. Round counts cover the fights in
our data. Fight-week runs should refresh them with the previews, odds and weigh-in news.

Data caveats, noted in the reports concerned:
- Bruno Gustavo da Silva: our records merge several Brazilian "Bruno Silva"s (the 41-36 total is wrong). Only the
  flyweight's UFC fights are used here.
- Ivan Gnizditskiy: our data has one of his seven pro fights; the record and finishes come from Sherdog's news story.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATED = "2026-11-17T21:00:00+00:00"
EVENT = "UFC Fight Night: Adesanya vs. Magomedov"


def src(outlet, title, url, date, author=""):
    return {"outlet": outlet, "author": author, "title": title, "url": url, "date": date}


SRC = {
    "mmaf_card": src("MMA Fighting", "UFC Saudi Arabia: Several new bouts added to Israel Adesanya vs. Shara Magomedov fight card",
                     "https://www.mmafighting.com/ufc/520917/ufc-saudi-arabia-several-new-bouts-added-to-israel-adesanya-vs-shara-magomedov-fight-card",
                     "2026-11-16", "Mike Heck"),
    "cage_main": src("Cageside Press", "Israel Adesanya vs. Shara Bullet Headlines UFC Saudi Arabia, Ian Garry vs. Yaroslav Amosov Co-Main",
                     "https://cagesidepress.com/2026/11/07/israel-adesanya-vs-shara-bullet-headlines-ufc-saudi-arabia-ian-garry-vs-yaroslav-amosov-co-main/",
                     "2026-11-07"),
    "sherdog_odds": src("Sherdog", "UFC Saudi Arabia odds: Israel Adesanya's odds take a major hit",
                        "https://www.sherdog.com/news/news/UFC-Saudi-Arabia-odds-Israel-Adesanyas-odds-take-a-major-hit-203550",
                        "2026-11-09", "Sayan Nag"),
    "be_corner": src("Bloody Elbow", "Israel Adesanya reveals who will corner him for UFC Saudi Arabia fight after leaving City Kickboxing",
                     "https://bloodyelbow.com/2026/11/12/israel-adesanya-reveals-who-will-corner-him-for-ufc-saudi-arabia-fight-after-leaving-city-kickboxing/",
                     "2026-11-12", "Jamie Theodosi"),
    "mmaf_adesanya": src("MMA Fighting", "Israel Adesanya ready to end slump after City Kickboxing departure: 'Best I've felt in a very long time'",
                         "https://www.mmafighting.com/ufc/519612/israel-adesanya-ready-to-end-slump-after-city-kickboxing-departure-best-ive-felt-in-a-very-long-time",
                         "2026-11-05"),
    "sherdog_bullet_bribe": src("Sherdog", "Shara Bullet says he rejected 100 million rubles to throw UFC fight",
                                "https://www.sherdog.com/news/news/Shara-Bullet-says-he-rejected-100-million-rubles-to-throw-UFC-fight-203652",
                                "2026-11-16"),
    "sherdog_bullet_eye": src("Sherdog", "Shara Bullet recalls putting off an eye doctor visit before a rematch",
                              "https://www.sherdog.com/news/news/Shara-Bullet-recalls-putting-off-an-eye-doctor-visit-before-a-rematch-203646",
                              "2026-11-16"),
    "be_garry_amosov": src("Bloody Elbow", "Ian Machado Garry and Yaroslav Amosov react to UFC Saudi Arabia co-main event announcement",
                           "https://bloodyelbow.com/2026/11/09/ian-machado-garry-and-yaroslav-amosov-react-to-ufc-saudi-arabia-co-main-event-announcement/",
                           "2026-11-09"),
    "junkie_garry_amosov": src("MMA Junkie (via Yahoo)", "UFC Fight Night 295: Yaroslav Amosov vs. Ian Machado Garry odds, what to know",
                               "https://sports.yahoo.com/articles/ufc-fight-night-295-yaroslav-235029688.html", "2026-11-08"),
    "sherdog_dulatov": src("Sherdog", "23-second UFC finisher reportedly draws Islam Dulatov in Saudi Arabia",
                           "https://www.sherdog.com/news/news/23second-UFC-finisher-reportedly-draws-Islam-Dulatov-in-Saudi-Arabia-203300",
                           "2026-10-22", "Sourav Chakraborty"),
    "bjp_abdullaev": src("BJPenn.com", "REPORT: Akbar Abdullaev's UFC debut booked after Dana White called him 'greatest talent' in DWCS history",
                         "https://www.bjpenn.com/mma-news/akbar-abdullaev/report-akbar-abdullaev-ufc-debut-booked-greatest-talent-dwcs-history/",
                         "2026-11-03"),
    "sherdog_gnizd": src("Sherdog", "7-0 finisher Ivan Gnizditskiy joins UFC despite missing DWCS",
                         "https://www.sherdog.com/news/news/70-finisher-Ivan-Gnizditskiy-joins-UFC-despite-missing-DWCS-203246",
                         "2026-10-16", "Sourav Chakraborty"),
    "sherdog_osmanli": src("Sherdog", "Mehemmedali Osmanli reportedly books UFC debut despite 'TUF 34' loss",
                           "https://www.sherdog.com/news/news/Mehemmedali-Osmanli-reportedly-books-UFC-debut-despite-TUF-34-loss-203515",
                           "2026-11-06", "Sayan Nag"),
    "knockout_prospects": src("MMA Knockout (via Yahoo)", "UFC Reportedly Books Top Prospects for Massive Fight on Israel Adesanya Card",
                              "https://sports.yahoo.com/articles/ufc-reportedly-books-top-prospects-112638474.html", "2026-11-06"),
    "data": src("Fight Lab verified records", "data/verified/fights.csv (Sherdog, UFCStats and Wikipedia, cross-checked)",
                "https://www.sherdog.com/", "2026-11-17"),
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


# ---------------------------------------------------------------- main event: Adesanya vs. Magomedov (middleweight)
report("Israel Adesanya",
       "The former two-time UFC middleweight champion (24-6, age 37) is on a four-fight losing streak: Strickland "
       "(decision, 2023), Du Plessis (R4 submission, 2024), Imavov (R2 TKO, 2025) and Joe Pyfer (R2 TKO, March 2026). He "
       "left City Kickboxing after 16 years and says this camp, run by his long-time wrestling coach Andrei Paulet and "
       "Tristam Apikotoa out of Unity MMA in Auckland, is the best he has had. He opened about -205 against Magomedov and "
       "has drifted to around -150.",
       {"Striking": "A long, switch-stance kickboxer who fights from range with feints, calf and teep kicks and counters. "
                    "Sixteen of his 24 wins are knockouts: seven in R1 and nine in R2 in our data.",
        "Grappling": "Defensive. Strickland and Du Plessis beat him by pressuring and grappling; Du Plessis submitted him in R4.",
        "Defense": "Never stopped before 2022; since then stopped three times (Pereira R5, Imavov R2, Pyfer R2). The last two "
                   "came quickly once he was hurt, a sign his punch resistance has dropped.",
        "Pace & cardio": "Built for five rounds: seven decision wins, five of them in title fights. Starts slowly and reads "
                         "opponents early.",
        "Fight IQ": "Elite at range and timing, but has struggled against forward pressure and with letting his hands go. "
                    "He says the last three years 'have not been fun' and that he was 'lost'."},
       ["Feints, kicks and counters at range; finishes in R1-R2 when he finds the timing (16 KO/TKO wins)",
        "Starts patiently and builds over five rounds"],
       ["Four straight losses, the last two by R2 stoppage",
        "Age 37; durability looks reduced",
        "First camp without City Kickboxing"],
       ["Pressure him onto the fence and make him exchange",
        "Hurt him early: he has not recovered once hurt in his last two fights"],
       [n("2026-11-12", "Revealed his new corner: Andrei Paulet and Tristam Apikotoa, training out of Unity MMA in Auckland.",
          "be_corner"),
        n("2026-11-05", "Says he feels better than in a very long time after leaving City Kickboxing.", "mmaf_adesanya"),
        n("2026-11-09", "Opened -205; money on Magomedov moved it to about -150 (BetOnline).", "sherdog_odds")],
       ["cage_main", "sherdog_odds", "be_corner", "mmaf_adesanya", "data"], "moderate")

report("Sharabutdin Magomedov",
       "'Shara Bullet' (17-1, age 32), a Dagestani middleweight from GOR MMA known for spinning attacks and flashy "
       "striking. He is 6-1 in the UFC; his only loss was a decision to Michael Page in February 2025. He has since won "
       "decisions over Marc-Andre Barriault and Michel Pereira. This is his first fight against a former champion.",
       {"Striking": "A kickboxer with spinning back kicks and fists, knees and a lot of feints. Twelve of his 17 wins are "
                    "knockouts: seven in R1, three in R2 and two in R3 in our data.",
        "Grappling": "Rarely wrestles (about 0.2 takedowns per 15 minutes in our data) and has never been submitted; "
                     "he keeps fights standing.",
        "Defense": "Never stopped. Page out-pointed him at range in his only loss.",
        "Pace & cardio": "His last three wins all went the distance (Oleksiejczuk, Barriault, Pereira). He has never "
                         "fought five rounds.",
        "Fight IQ": "Patient when he can't find the finish; has struggled against a long, elusive counter-striker (Page)."},
       ["Spinning kicks and fists, knees; most knockouts come early",
        "Goes the distance against durable opponents (three of his last four)"],
       ["Struggled against Michael Page's length and movement, a style Adesanya shares",
        "First five-round fight",
        "Says he once put off an eye doctor visit before a rematch (Sherdog)"],
       ["Stay long and make him reach; counter his entries",
        "Take him into the later rounds"],
       [n("2026-11-16", "Says he rejected 100 million rubles to throw his 2024 fight with Michal Oleksiejczuk.",
          "sherdog_bullet_bribe"),
        n("2026-11-09", "Money has come in on him: from about +170 to +130 (BetOnline).", "sherdog_odds")],
       ["cage_main", "sherdog_odds", "sherdog_bullet_bribe", "sherdog_bullet_eye", "data"], "moderate")

# ---------------------------------------------------------------- co-main: Garry vs. Amosov (welterweight, 5 rds)
report("Ian Garry",
       "An Irish welterweight (17-2, age 28) coming off a five-round decision loss to Islam Makhachev for the title at "
       "UFC 330 in August, four months before this fight. Before that he beat Carlos Prates and Belal Muhammad by "
       "decision. Both losses are five-round decisions (Rakhmonov, Makhachev). He opened about -185 and has drifted to "
       "around -145.",
       {"Striking": "A long, upright kickboxer with a sharp jab, kicks and good footwork. Eight knockouts in our data (three "
                    "in R1, three in R2, one in R3), but recently he wins on points: his last five wins include four "
                    "decisions.",
        "Grappling": "Defensive wrestling has held up against strikers; Makhachev and Rakhmonov out-grappled him over five "
                     "rounds.",
        "Defense": "Never stopped; never knocked down in the UFC in our data.",
        "Pace & cardio": "Has gone five rounds three times (Rakhmonov, Prates, Makhachev) and stays busy.",
        "Fight IQ": "Disciplined; manages range and rounds."},
       ["Jab and kicks at range; wins on points against good opponents",
        "Has gone five rounds three times"],
       ["Both losses came to elite grapplers over five rounds",
        "Quick turnaround after a five-round title loss"],
       ["Wrestle him: chain takedowns and hold him down",
        "Close distance behind feints and pressure"],
       [n("2026-11-09", "Opened -185 against Amosov and moved to about -145 (BetOnline).", "sherdog_odds")],
       ["cage_main", "sherdog_odds", "be_garry_amosov", "junkie_garry_amosov", "data"], "moderate")

report("Yaroslav Amosov",
       "The former Bellator welterweight champion from Ukraine (30-1, age 33), training at American Top Team. He is 2-0 "
       "in the UFC with submissions of Neil Magny (R1, December 2025) and Joel Alvarez (R2, May 2026). His only loss was a "
       "R3 knockout by Jason Jackson in 2023.",
       {"Striking": "Functional and heavy-handed; nine knockouts in our data (six in R1).",
        "Grappling": "A chain wrestler and sambo player who controls from top. Thirteen submissions in our data, nine of "
                     "them in R1.",
        "Defense": "Stopped once, by strikes (Jackson, R3).",
        "Pace & cardio": "Has gone five rounds twice (Lima, Storley) and won both.",
        "Fight IQ": "Patient; takes the fight where he wants it."},
       ["Takedowns and top control; submissions mostly in R1",
        "Has won five-round fights"],
       ["Only stopped by a striker who could keep it standing (Jackson)",
        "First fight against a top-five welterweight"],
       ["Keep it standing with footwork and takedown defence",
        "Make him pay on entries"],
       [n("2026-11-09", "About +125 after opening near +155 (BetOnline).", "sherdog_odds")],
       ["cage_main", "sherdog_odds", "be_garry_amosov", "data"], "moderate")

# ---------------------------------------------------------------- Spivac vs. Pinto (heavyweight)
report("Serghei Spivac",
       "A Moldovan heavyweight grappler (18-7, age 31) who has alternated wins and losses: a decision win over Ante Delija "
       "in February and a decision loss to Vitor Petrino in August.",
       {"Striking": "Serviceable boxing; seven knockouts in our data, five of them in R1.",
        "Grappling": "His weapon: takes opponents down and finishes with arm-triangles and ground strikes. Eight submissions "
                     "(six in R1).",
        "Defense": "Stopped four times by strikes, three of them in R1 (Gane in R2).",
        "Pace & cardio": "Fades in long exchanges; recent fights have gone the distance (Delija, Petrino, Cortes-Acosta).",
        "Fight IQ": "Wins when he gets an early takedown; struggles against heavy strikers who stuff the first shot."},
       ["Early takedowns and R1 submissions", "Recent fights going to decision"],
       ["Stopped by strikes four times, mostly in R1", "Against a long, unbeaten knockout puncher"],
       ["Stuff the first takedown and make him strike", "Punish his level changes"],
       [],
       ["mmaf_card", "data"], "moderate")

report("Mario Pinto",
       "An unbeaten Portuguese heavyweight (13-0, age 28), tall and long (196 cm, 201 cm reach), from Urban Warriors. He "
       "is 4-0 in the UFC since the 2024 Contender Series: TKOs of Austen Lane, Jhonata Diniz and Ryan Spann (R2 in "
       "September), and a decision over Felipe Franco.",
       {"Striking": "A long, heavy puncher; eight knockouts in our data (four in R1, three in R2, one in R3).",
        "Grappling": "Little evidence either way in our data.",
        "Defense": "Never stopped.",
        "Pace & cardio": "Has gone five rounds once on the regional scene (Aras) and three rounds once in the UFC.",
        "Fight IQ": "Patient; picks his shots behind his length."},
       ["Length and power; finishes mostly in R1-R2"],
       ["Untested against a heavyweight grappler of Spivac's level"],
       ["Take him down early and keep him there"],
       [],
       ["mmaf_card", "data"], "moderate")

# ---------------------------------------------------------------- Chokheli vs. Dulatov (welterweight)
report("Levan Chokheli",
       "A Georgian welterweight (15-4, 1 NC, age 30) out of Kassel, Germany, a Bellator veteran. He knocked out Leon "
       "Shahbazyan in 23 seconds in his UFC debut in June.",
       {"Striking": "A power puncher: twelve of 15 wins by knockout, eleven of them in R1 in our data.",
        "Grappling": "Decision wins in Bellator came from pressure and some wrestling.",
        "Defense": "Stopped twice in R1: by Lorenz Larkin (KO) and Goiti Yamauchi (submission).",
        "Pace & cardio": "Three decisions in Bellator; most fights are short.",
        "Fight IQ": "Front-runner who looks for the early knockout."},
       ["Explosive starts; nearly all finishes in R1"],
       ["Stopped twice in R1 himself", "Against another R1 finisher"],
       ["Survive his first two minutes", "Counter as he rushes in"],
       [],
       ["sherdog_dulatov", "mmaf_card", "data"], "moderate")

report("Islam Dulatov",
       "A German welterweight (12-1, age 28) from Triple One Gym, signed off the 2024 Contender Series. He knocked out Adam "
       "Fugitt in R1 in his UFC debut in July 2025; a July 2026 bout with Wellington Turman was cancelled when he fell ill.",
       {"Striking": "A finisher: seven knockouts and five submissions in our data, eleven of the twelve in R1.",
        "Grappling": "Five R1 submissions, most of them very fast (under a minute).",
        "Defense": "Only loss a decision; never stopped.",
        "Pace & cardio": "Barely tested past R1.",
        "Fight IQ": "Patient enough to set up a left hook (Fugitt)."},
       ["Finishes in R1 by strikes or submission"],
       ["Almost no evidence past R1", "Sixteen months between UFC fights"],
       ["Take him past R1"],
       [n("2026-10-22", "Booked against Levan Chokheli after his July bout with Wellington Turman was cancelled because he fell "
          "ill.", "sherdog_dulatov")],
       ["sherdog_dulatov", "mmaf_card", "data"], "moderate")

# ---------------------------------------------------------------- Santos vs. Abdullaev (lightweight)
report("Mairon Santos",
       "A Brazilian (17-1, age 26) from Xtreme Couture, winner of The Ultimate Fighter 32 at featherweight. He is 4-0 in "
       "the UFC and moves to lightweight after missing weight for his win over Muhammadjon Naimov in December 2025.",
       {"Striking": "Busy, with power: nine knockouts in our data (four in R1, two in R2, three in R3).",
        "Grappling": "Wins on the cards against strikers who can't wrestle him (Yusuff, Marshall split).",
        "Defense": "Stopped once, by Dan Argueta (R3, 2022).",
        "Pace & cardio": "Finishes late as well as early; three R3 knockouts.",
        "Fight IQ": "Steady; won a split over Marshall."},
       ["Late finishes as well as early (three R3 knockouts)"],
       ["First fight at lightweight", "Against the most dangerous striker he has faced"],
       ["Out-hit him early before he settles"],
       [n("2026-11-03", "Moves to lightweight for this fight after missing the featherweight limit for the Naimov fight.",
          "bjp_abdullaev")],
       ["bjp_abdullaev", "mmaf_card", "data"], "moderate")

report("Akbar Abdullaev",
       "An unbeaten Kyrgyz lightweight (14-0, age 29), formerly of ONE Championship, who knocked out Ednilson Barros Santos in "
       "19 seconds on the Contender Series in September; Dana White called him one of the greatest talents in the show's "
       "history. This is his UFC debut.",
       {"Striking": "A knockout puncher: thirteen of 14 wins by knockout in our data, nine in R1.",
        "Grappling": "One submission win.",
        "Defense": "Never beaten.",
        "Pace & cardio": "Has finished in R3 twice and in R5 once (ONE), so he can go long.",
        "Fight IQ": "Calm power puncher."},
       ["One-punch power; most finishes in R1"],
       ["UFC debut", "Has not faced a fighter of Santos's level"],
       ["Wrestle him and take him late"],
       [n("2026-11-03", "UFC debut booked against Mairon Santos (first reported by Ag.Fight).", "bjp_abdullaev")],
       ["bjp_abdullaev", "mmaf_card", "data"], "moderate")

# ---------------------------------------------------------------- Tuchalov vs. Cutelaba (light heavyweight)
report("Magomed Tuchalov",
       "An unbeaten Russian light heavyweight (6-0, age 26) from Dagestan Fighter, 1-0 in the UFC after a decision win over "
       "Brendson Ribeiro in July. He built his record in UAE Warriors.",
       {"Striking": "Four knockouts in our data (two in R1, two in R2).",
        "Grappling": "One R1 submission.",
        "Defense": "Never beaten.",
        "Pace & cardio": "Went three rounds in his UFC debut.",
        "Fight IQ": "Thin record to judge."},
       ["Early finishes on the regional scene"],
       ["Only one UFC fight"],
       ["Test his cardio and chin"],
       [],
       ["mmaf_card", "data"], "thin")

report("Ion Cutelaba",
       "A Moldovan light heavyweight veteran (20-14 in our data, age 32) known for explosive starts. He was knocked out by "
       "Navajo Stirling in R2 in June after a R1 submission of Oumar Sy in March.",
       {"Striking": "Explosive and wild; thirteen knockouts in our data, twelve in R1.",
        "Grappling": "Powerful takedowns; five submissions, four in R1.",
        "Defense": "Stopped eight times in our data, mostly in R1-R2.",
        "Pace & cardio": "Fades badly after R1.",
        "Fight IQ": "All-in early."},
       ["Explosive R1; nearly all finishes in R1"],
       ["Fades after R1", "Stopped often"],
       ["Survive his first round, then pressure him"],
       [],
       ["mmaf_card", "data"], "moderate")

# ---------------------------------------------------------------- Bruno Gustavo da Silva vs. Jafel Filho (flyweight)
report("Bruno Gustavo da Silva",
       "A Brazilian flyweight from American Top Team (age 36) on a 1-4 run in the UFC: stopped by Manel Kape (R3, 2024) and "
       "Joshua Van (R3, 2025), a R3 submission of Hyun Sung Park (October 2025), a split-decision loss to Charles Johnson "
       "(March 2026) and a R1 submission loss to Edgar Chairez (June). Our records merge him with other Bruno Silvas, so "
       "only his UFC fights are used here.",
       {"Striking": "A power puncher by reputation, with most of his career finishes by knockout.",
        "Grappling": "Can wrestle; has been submitted (Chairez, R1).",
        "Defense": "Stopped in three of his last five fights.",
        "Pace & cardio": "Two of his recent stoppage losses came late (R3).",
        "Fight IQ": "Aggressive."},
       ["Power punching"],
       ["1-4 in his last five UFC fights", "Age 36 at flyweight", "Submitted in R1 last time"],
       ["Take his back in scrambles"],
       [],
       ["mmaf_card", "data"], "thin")

report("Jafel Filho",
       "A Brazilian flyweight from Nova Uniao (17-5, age 33). He is 4-3 in the UFC: three R1 submissions (Barez, Osbourne, "
       "Carpenter) and decision losses to Allan Nascimento and Cody Durden (April).",
       {"Striking": "Secondary; five knockouts in our data.",
        "Grappling": "A back-taker: eleven submissions, eight in R1.",
        "Defense": "Never knocked out; submitted twice in R3.",
        "Pace & cardio": "Loses on the cards when he can't finish early.",
        "Fight IQ": "Scrambles for the back."},
       ["R1 submissions off scrambles"],
       ["Two straight losses on the cards to grinders"],
       ["Keep it standing or win the grappling exchanges"],
       [],
       ["mmaf_card", "data"], "moderate")

# ---------------------------------------------------------------- Satybaldiev vs. Gnizditskiy (light heavyweight)
report("Uran Satybaldiev",
       "A Kyrgyz light heavyweight (9-1, age 32), tall at 193 cm with a 201 cm reach. He lost a decision to Martin Buday in "
       "his UFC debut and then submitted Diyar Nurgozhay in R1 in August 2025.",
       {"Striking": "Long and powerful; five knockouts in our data, including one in R4.",
        "Grappling": "Three submissions (R1 and R3).",
        "Defense": "Only loss a decision.",
        "Pace & cardio": "Has gone five rounds (split decision, 2022) and finished in R4.",
        "Fight IQ": "Uses his length."},
       ["Can win late; has gone five rounds"],
       ["Out of action since August 2025"],
       ["Pressure him inside his reach"],
       [],
       ["sherdog_dulatov", "data"], "moderate")

report("Ivan Gnizditskiy",
       "An unbeaten Russian light heavyweight (7-0, age 30) who signed directly with the UFC after visa problems kept him "
       "off his Contender Series bout. He has finished all seven wins, six by knockout, and fought twice in ONE in 2025. Our "
       "data has only one of his fights.",
       {"Striking": "A finisher: six knockouts in seven wins (Sherdog).",
        "Grappling": "One submission win.",
        "Defense": "Never beaten.",
        "Pace & cardio": "Untested late.",
        "Fight IQ": "Thin record."},
       ["Finishes every win"],
       ["UFC debut; very little film or data"],
       ["Take him past R1"],
       [n("2026-10-16", "Signed directly with the UFC after visa issues kept him off the Contender Series.", "sherdog_gnizd")],
       ["sherdog_gnizd", "sherdog_dulatov"], "thin")

# ---------------------------------------------------------------- Tulio vs. Park (middleweight)
report("Marco Tulio",
       "A Brazilian middleweight from Chute Boxe Diego Lima (14-3, age 32), 2-2 in the UFC: TKOs of Ihor Potieria and "
       "Tresean Gore, then a R2 knockout loss to Christian Leroy Duncan and a decision loss to Roman Kopylov (May).",
       {"Striking": "Aggressive puncher; ten knockouts in our data (six in R1, four in R2).",
        "Grappling": "Little used.",
        "Defense": "Stopped twice in R2.",
        "Pace & cardio": "Early finisher.",
        "Fight IQ": "Front-foot."},
       ["Finishes in R1-R2"],
       ["Two straight losses"],
       ["Wrestle him and drag him into R3"],
       [],
       ["sherdog_dulatov", "data"], "moderate")

report("Park Jun-yong",
       "A South Korean middleweight from World Top Team (19-7, age 35), a UFC veteran who lost a decision to Ikram Aliskerov "
       "in October 2025 after decision wins over Brad Tavares and Ismail Naurdiev.",
       {"Striking": "Volume boxing.",
        "Grappling": "Wrestles and takes the back; six submissions in our data.",
        "Defense": "Stopped once by strikes (Gregory Rodrigues, R2).",
        "Pace & cardio": "Goes the distance often (eight decisions and splits).",
        "Fight IQ": "Grinds out close fights; three split-decision wins."},
       ["Grinds decisions; strong late"],
       ["Age 35", "Over a year out"],
       ["Hurt him early with power"],
       [],
       ["sherdog_dulatov", "data"], "moderate")

# ---------------------------------------------------------------- Andrusca vs. Osmanli (bantamweight)
report("Pavel Andrusca",
       "An unbeaten Moldovan (9-0, age 24) who beat Nathaniel Wood by decision on short notice in his UFC debut in September, "
       "up at featherweight; he returns to bantamweight here.",
       {"Striking": "Six knockouts in our data (four in R1, two in R2).",
        "Grappling": "One submission.",
        "Defense": "Never beaten.",
        "Pace & cardio": "Went three rounds with Wood.",
        "Fight IQ": "Took a short-notice debut against a veteran and won it."},
       ["Early finishes on the regional scene; can win on the cards"],
       ["Second UFC fight"],
       ["Drag him into scrambles"],
       [n("2026-11-06", "Drops back to bantamweight against Mehemmedali Osmanli.", "sherdog_osmanli")],
       ["sherdog_osmanli", "data"], "moderate")

report("Mehemmedeli Osmanli",
       "An Azerbaijani bantamweight (11-2, age 22) and TUF 34 finalist who lost the final to Ilimbek Akylbek Uulu by "
       "disqualification for an illegal knee, a finish many saw as controversial. He had won nine straight before that.",
       {"Striking": "Three knockouts in our data.",
        "Grappling": "A submission grappler: six submissions, finishes in R1, R2, R3 and R5.",
        "Defense": "Submitted once (R1).",
        "Pace & cardio": "Can finish late, including a R5 submission.",
        "Fight IQ": "Young and aggressive (the illegal knee)."},
       ["Submissions in later rounds as well as early"],
       ["Discipline (the TUF final DQ)", "Age 22"],
       ["Keep it standing"],
       [n("2026-11-06", "Booked for his UFC debut against Pavel Andrusca despite the TUF 34 final loss.", "sherdog_osmanli")],
       ["sherdog_osmanli", "data"], "moderate")

# ---------------------------------------------------------------- Rodrigues vs. Letho Duclos (middleweight)
report("Modestino Rodrigues",
       "A Brazilian middleweight (8-1, age 23) who knocked out Brandon Holmes in 15 seconds on the Contender Series in "
       "September. This is his UFC debut.",
       {"Striking": "All eight wins by knockout, six in R1.",
        "Grappling": "Unknown.",
        "Defense": "Knocked out once in R1 (2024).",
        "Pace & cardio": "Has never needed more than two rounds.",
        "Fight IQ": "Very thin record."},
       ["Finishes in R1"],
       ["Knocked out in R1 once himself", "UFC debut"],
       ["Survive his first minutes; take him to R2-R3"],
       [],
       ["mmaf_card", "data"], "thin")

report("Matthieu Letho Duclos",
       "A French middleweight from Venum Training Camp Paris (11-3, age 31), long at 191 cm with a 196 cm reach. He knocked "
       "out Luis Felipe Dias in R1 in his UFC debut in September; he was stopped by Marco Tulio on the 2024 Contender Series.",
       {"Striking": "Nine knockouts in our data (five in R1, four in R2).",
        "Grappling": "Has been submitted once (R1).",
        "Defense": "Stopped three times, all in R1-R2.",
        "Pace & cardio": "Went five rounds once (HXMMA, 2025).",
        "Fight IQ": "Uses his length."},
       ["Finishes in R1-R2"],
       ["Stopped three times early"],
       ["Close the distance and land first"],
       [],
       ["mmaf_card", "data"], "moderate")

# ---------------------------------------------------------------- Hussein vs. Sosa (bantamweight)
report("Abdul Hussein",
       "A Finnish bantamweight (16-2, age 29) who submitted Cody Gibson in R3 in his UFC debut in July after a long UAE "
       "Warriors run.",
       {"Striking": "Five knockouts in our data.",
        "Grappling": "A submission specialist: ten submissions, eight in R1.",
        "Defense": "Submitted once (R1); one decision loss.",
        "Pace & cardio": "Found the finish in R3 in his debut.",
        "Fight IQ": "Patient grappler."},
       ["Submissions, mostly in R1"],
       ["Second UFC fight"],
       ["Stay off the mat"],
       [],
       ["knockout_prospects", "data"], "moderate")

report("Hecher Sosa",
       "A Spanish bantamweight from Animal Fight Center (14-1, age 31), 1-0 in the UFC after a decision over Luan Lacerda in "
       "March; he won a contract on the 2025 Contender Series.",
       {"Striking": "Six knockouts in our data (four in R1, two in R3).",
        "Grappling": "Two submissions.",
        "Defense": "Stopped once (R1).",
        "Pace & cardio": "His last three wins went the distance.",
        "Fight IQ": "Steady."},
       ["Goes the distance against good opponents"],
       ["Against a strong submission grappler"],
       ["Take him down and hunt the back"],
       [],
       ["knockout_prospects", "bjp_abdullaev", "data"], "moderate")

# ---------------------------------------------------------------- Rebecki vs. Brener (lightweight)
report("Mateusz Rebecki",
       "A Polish lightweight from American Top Team (21-5, age 34), 5-4 in the UFC. He knocked out Kyle Prepolec in R1 in "
       "August after three straight losses: decisions to Chris Duncan and Ludovit Klein (split) and a R3 submission by Grant "
       "Dawson in May.",
       {"Striking": "Short, powerful and aggressive; ten knockouts in our data (five in R1).",
        "Grappling": "A strong wrestler with seven submissions (six in R1).",
        "Defense": "Stopped twice late: Diego Ferreira (R3 KO) and Dawson (R3 submission).",
        "Pace & cardio": "Fast starter; his stoppage losses both came in R3.",
        "Fight IQ": "Pressure fighter."},
       ["Fast starts; R1 finishes by strikes or submission", "Stopped late (both stoppage losses in R3)"],
       ["Three losses in his last five", "Fades late"],
       ["Survive his early pressure and take over in R3"],
       [],
       ["sherdog_dulatov", "data"], "moderate")

report("Elves Brener",
       "A Brazilian lightweight from Chute Boxe Diego Lima (17-6, age 29), 4-3 in the UFC. He knocked out Josiah Harrell in "
       "R1 in September after a three-fight skid (Orolbai, Joel Alvarez R3 KO, Ribovics).",
       {"Striking": "Four knockouts in our data, two of them in R3.",
        "Grappling": "A submission threat: eleven submissions, eight in R1.",
        "Defense": "Stopped once (Alvarez, R3); five decision losses.",
        "Pace & cardio": "Has late finishes and has gone the distance often.",
        "Fight IQ": "Scrambly; finds chokes."},
       ["R1 submissions; can finish late"],
       ["Five decision losses: gets out-pointed by busier fighters"],
       ["Out-work him over three rounds"],
       [],
       ["sherdog_dulatov", "data"], "moderate")


out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
