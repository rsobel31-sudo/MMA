"""Scouting reports (part C) for UFC Fight Night: Bonfim vs. Brady (UFC Vegas 124 / Fight Night 293, 2026-11-07),
first pass written 2026-10-27.

Covers the lower prelims: Bashi vs. Brennan, Cachoeira vs. Milosevic, Parsons vs. Souza, Raposo vs. Degli and
Lourenco vs. Petersen (Petersen replaced Alvin Hines, who withdrew with vertigo). Fight-week previews aren't out yet:
these draw on recent-fight recaps, booking news, Contender Series coverage and our verified records. Round/method
counts are taken from data/verified/fights.csv. Later runs should refresh them with the Sherdog/MMA Mania/UFC.com
previews and weigh-in news.
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
    "si_change": src("Yahoo Sports (MMA Knockout, SI)", "First UFC Fight Night Event of November Hit With Late Change",
                     "https://sports.yahoo.com/articles/first-ufc-fight-night-event-151020968.html", "2026-10-26"),
    # Bashi
    "cage_delgado": src("Cageside Press", "Jose Delgado Earns Gritty Decision Victory Over Bashi",
                        "https://cagesidepress.com/2026/07/18/jose-delgado-earns-gritty-decision-victory-over-bashi/",
                        "2026-07-18", "Eddie Law"),
    "es_bashi_inj": src("EssentiallySports", "UFC OKC fighter reveals injuries after being rushed to hospital following loss",
                        "https://www.essentiallysports.com/ufc-mma-news-ufc-okc-fighter-reveals-injuries-after-being-rushed-to-hospital-following-loss/",
                        "2026-07-20", "Abhishek Kumar Das"),
    "cage_rodriguez": src("Cageside Press", "UFC Vegas 101: Christian Rodriguez Derails Another Prospect, Gives Austin Bashi First Loss",
                          "https://cagesidepress.com/2025/01/11/ufc-vegas-101-christian-rodriguez-derails-another-prospect-gives-austin-bashi-first-loss",
                          "2025-01-11", "Shawn Bitter"),
    "sherdog_v101_prev": src("Sherdog", "Preview: UFC Vegas 101 'Dern vs. Ribas 2'",
                             "https://www.sherdog.com/news/articles/5/Preview-UFC-Vegas-101-Dern-vs-Ribas-2-195860",
                             "2025-01-09", "Tom Feely"),
    "cage_okc_next": src("Cageside Press", "What's Next: UFC Oklahoma City Losers",
                         "https://cagesidepress.com/2026/07/20/whats-next-ufc-oklahoma-city-losers/", "2026-07-20"),
    "cage_ttp540": src("Cageside Press", "TTP Ep. 540: Tabatha Ricci, Alvin Hines, Austin Bashi, and UFC Oklahoma City",
                       "https://cagesidepress.com/2026/07/15/ttp-ep-540-tabatha-ricci-alvin-hines-austin-bashi-and-ufc-oklahoma-city/",
                       "2026-07-15"),
    # Brennan
    "cage_marshall": src("Cageside Press", "UFC Vegas 116: Francis Marshall Turns Back Bellator Standout Lucas Brennan",
                         "https://cagesidepress.com/2026/04/25/ufc-vegas-116-francis-marshall-turns-back-bellator-standout-lucas-brennan/",
                         "2026-04-25", "Shawn Bitter"),
    "wiki_brennan": src("Wikipedia", "Lucas Brennan", "https://en.wikipedia.org/wiki/Lucas_Brennan", "2026-10-27"),
    "sherdog_pfl1": src("Sherdog", "2024 PFL 1 Regular Season Play-by-Play, Results & Round Scoring",
                        "https://www.sherdog.com/news/news/2024-PFL-1-Regular-Season-PlaybyPlay-Results-Round-Scoring-193200",
                        "2024-04-04", "Tyler Treese"),
    "bjp_v116": src("BJPenn.com", "UFC Vegas 116: 'Sterling vs. Zalal' Live Results and Highlights",
                    "https://www.bjpenn.com/mma-news/ufc-vegas-116/ufc-vegas-116-sterling-vs-zalal-live-results-and-highlights/",
                    "2026-04-25"),
    # Cachoeira
    "cage_chandler": src("Cageside Press", "UFC Vegas 118: Returning Chelsea Chandler Taps Priscila Cachoeira",
                         "https://cagesidepress.com/2026/06/06/ufc-vegas-118-returning-chelsea-chandler-taps-priscila-cachoeira/",
                         "2026-06-06", "Jay Anderson"),
    "cage_sygula": src("Cageside Press", "UFC Vegas 113: Klaudia Sygula Outworks Priscila Cachoeira",
                       "https://cagesidepress.com/2026/02/07/ufc-vegas-113-klaudia-sygula-outworks-priscila-cachoeira",
                       "2026-02-07", "Jay Anderson"),
    "bjp_v109": src("BJPenn.com", "UFC Vegas 109: 'Dolidze vs. Hernandez' Live Results and Highlights",
                    "https://www.bjpenn.com/mma-news/ufc-vegas-109/ufc-vegas-109-dolidze-vs-hernandez-live-results-and-highlights/",
                    "2025-08-09"),
    "bjp_v104": src("BJPenn.com", "UFC Vegas 104: 'Vettori vs. Dolidze 2' Live Results and Highlights",
                    "https://www.bjpenn.com/mma-news/ufc/ufc-vegas-104-vettori-vs-dolidze-2-live-results-and-highlights/",
                    "2025-03-15"),
    "lowkick_ko2025": src("LowKick MMA", "Watch UFC's Greatest Knockouts of 2025 - Free Full Video",
                          "https://www.lowkickmma.com/watch-ufcs-greatest-knockouts-of-2025-free-full-video/", "2025-12-30"),
    "sucka_cach_nina": src("MMA Sucka", "Priscila Cachoeira set to face Nina Milosevic at UFC Vegas 124",
                           "https://mmasucka.com/news/priscila-cachoeira-set-to-face-nina-milosevic-at-ufc-vegas-124/",
                           "2026-09-25", "Felipe Castello Branco"),
    # Milosevic
    "cage_cowan": src("Cageside Press", "UFC Belgrade: Nina Nikolija Milosevic Uses Body Shots to End Hailey Cowan's Night",
                      "https://cagesidepress.com/2026/08/01/ufc-belgrade-nina-nikolija-milosevic-uses-body-shots-to-end-hailey-cowans-night/",
                      "2026-08-01", "Shawn Bitter"),
    "ufc_nina": src("UFC.com", "Back Home, Ready For The Big Stage",
                    "https://www.ufc.com/news/nina-milosevic-back-home-big-stage-ufc-belgrade", "2026-07-31",
                    "McKenzie Pavacich"),
    "immaf_nina": src("IMMAF", "Nina Nikolija Milosevic: From IMMAF Gold to the UFC",
                      "https://immaf.org/2026/08/01/nina-nikolija-milosevic-from-immaf-gold-to-the-ufc/", "2026-08-01"),
    "brave_104": src("BRAVE CF", "Luciano Palhano dominates Nikola Joksovic in BRAVE CF 104 main event: complete event results",
                     "https://www.bravecf.com/news/luciano-palhano-dominates-nikola-joksovi-in-brave-cf-104-main-event-complete-event-results",
                     "2026-02-15"),
    "cage_cowan_retire": src("Cageside Press", "Hailey Cowan Retires Following 0-4 UFC Run",
                             "https://cagesidepress.com/2026/08/04/hailey-cowan-retires-following-0-4-ufc-run/", "2026-08-04"),
    # Parsons
    "junkie_parsons": src("Yahoo Sports (MMA Junkie)", "'Sluggernaut' Jonny Parsons wonders: To slug, or not, in UFC return?",
                          "https://sports.yahoo.com/articles/sluggernaut-jonny-parsons-wonders-slug-234031324.html",
                          "2026-10-15", "Matt Erickson, George Garcia, Brian Garcia"),
    "sherdog_roberts": src("Sherdog", "UFC Fight Night 224 Prelims: Jonny Parsons Wins Wild Brawl, Stops Danny Roberts",
                           "https://www.sherdog.com/news/news/UFC-Fight-Night-224-Prelims-Jonny-Parsons-Wins-Wild-Brawl-Stops-Danny-Roberts-190563",
                           "2023-07-22", "Tristen Critchfield"),
    "cage_parsons_dwcs": src("Cageside Press", "A Pro Debut on 12 hrs Notice? DWCS' Jonny Parsons is Always Down to Scrap",
                             "https://cagesidepress.com/2021/10/14/a-pro-debut-on-12-hrs-notice-dwcs-jonny-parsons-is-always-down-to-scrap",
                             "2021-10-14", "Daniel Vreeland"),
    "sucka_medic": src("MMA Sucka", "Jonny Parsons Plans to Put Uros Medic's 'Lights Out' at UFC Vegas Event",
                       "https://mmasucka.com/news/jonny-parsons-plans-to-put-uros-medics-lights-out-at-ufc-vegas-event/",
                       "2023-11-06", "Michael DeSantis"),
    "cage_kinoshita_book": src("Cageside Press", "Jonny Parsons to Fight Against Yusaku Kinoshita at UFC Vegas 95",
                               "https://cagesidepress.com/2024/06/16/jonny-parsons-yusaku-kinoshita-ufc-vegas-95",
                               "2024-06-16", "Bryson Hester"),
    # Souza
    "cage_ding": src("Cageside Press", "UFC Macau: Jose Henrique Souza Takes Split Decision Over Ding Meng",
                     "https://cagesidepress.com/2026/05/30/ufc-macau-ding-meng-vs-jose-henrique-souza/", "2026-05-30",
                     "Jay Anderson"),
    "ufc_souza": src("UFC Espanol", "Jose Henrique (athlete profile)", "https://www.ufcespanol.com/athlete/jose-henrique",
                     "2026-10-27"),
    "sherdog_souza_sign": src("Sherdog", "UFC Signs 20-Year-Old DWCS Vet Jose Henrique Souza",
                              "https://www.sherdog.com/news/news/UFC-Signs-20YearOld-DWCS-Vet-Jose-Henrique-Souza-189508",
                              "2023-03-24", "Joao Baptista"),
    "cage_souza_usada": src("Cageside Press", "UFC: Jose de Souza Hit With Two-Year Ban by USADA Following Failed Drug Test",
                            "https://cagesidepress.com/2023/06/01/jose-de-souza-hit-two-year-ban-usada-following-failed-drug-test",
                            "2023-06-01", "Jay Anderson"),
    # Raposo
    "cage_nascimento": src("Cageside Press", "Mitch Raposo Holds Off Nascimento Rally, Calls Out Brandon Moreno",
                           "https://cagesidepress.com/2026/06/20/mitch-raposo-holds-off-nascimento-rally-calls-out-brandon-moreno/",
                           "2026-06-20", "Eddie Law"),
    "cage_raposo_chairez": src("Cageside Press", "UFC Vegas 119: Mitch Raposo Wants Edgar Chairez at Noche UFC",
                               "https://cagesidepress.com/2026/06/23/ufc-vegas-119-raposo-chairez-noche/", "2026-06-23",
                               "Destiny McCubbin, Jay Anderson"),
    "cage_maksum": src("Cageside Press", "Mitch Raposo Outworks Azat Maksum, Secures Breakthrough Victory at UFC 321",
                       "https://cagesidepress.com/2025/10/25/mitch-raposo-outworks-azat-maksum-secures-breakthrough-victory-at-ufc-321",
                       "2025-10-25", "Eddie Law"),
    "cage_raposo_demons": src("Cageside Press", "Mitch Raposo Wins at UFC 321, Says He 'Faced Demons' Before Breakthrough Victory",
                              "https://cagesidepress.com/2025/10/27/mitch-raposo-wins-at-ufc-321-says-he-faced-demons-before-breakthrough-victory",
                              "2025-10-27", "Dave Noseworthy, Eddie Law"),
    "cage_winnipeg_ill": src("Cageside Press", "UFC Winnipeg Loses Fight Day Before Weigh-Ins",
                             "https://cagesidepress.com/2026/04/16/ufc-winnipeg-loses-fight-day-before-weigh-ins/", "2026-04-16"),
    "br_nascimento": src("Bleacher Report", "UFC fighter Allan Nascimento dies at age 34",
                         "https://bleacherreport.com/articles/25461303-ufc-fighter-allan-nascimento-dies-age-34", "2026-08-03"),
    # Degli
    "ufc_dwcs_w7": src("UFC.com", "Dana White's Contender Series Season 10, Week 7 Results",
                       "https://www.ufc.com/news/dana-whites-contender-series-season-10-week-7-results", "2026-09-22"),
    "cage_degli": src("Cageside Press", "Marcos Degli earns UFC deal on Contender Series (Week 7)",
                      "https://cagesidepress.com/2026/09/23/marcos-degli-dwcs-rahiki/", "2026-09-23",
                      "Patrick Danna, Jay Anderson"),
    "bn_degli": src("Boxing News", "Degli Lands UFC Contract After Wild One-Arm Choke",
                    "https://boxingnews.com/news/degli-ufc-contract-one-arm-choke-dwcs/", "2026-09-23"),
    "sucka_degli_prates": src("MMA Sucka", "Marcos Degli wants to follow Carlos Prates' path to the UFC",
                              "https://mmasucka.com/news/marcos-degli-wants-to-follow-carlos-prates-path-to-the-ufc/",
                              "2026-09-22", "Felipe Castello Branco"),
    "sucka_degli_raposo": src("MMA Sucka", "Marcos Degli set for UFC debut against Mitch Raposo",
                              "https://mmasucka.com/news/marcos-degli-set-for-ufc-debut-against-mitch-raposo/",
                              "2026-10-06", "Felipe Castello Branco"),
    # Lourenco / Petersen
    "sherdog_hines": src("Sherdog", "Vertigo delays Alvin Hines' pursuit of first UFC victory",
                         "https://www.sherdog.com/news/news/Vertigo-delays-Alvin-Hines-pursuit-of-first-UFC-victory-203121",
                         "2026-10-08", "Sayan Nag"),
    "rotowire_lourenco": src("Rotowire", "Gabriel Lorenco MMA Stats & News",
                             "https://aws-prod-web9.rotowire.com/mma/player/gabriel-lorenco-2834", "2026-10-25"),
    "dk_lourenco": src("DraftKings Network", "Prediction, pick for Gabriel Lourenco vs. Charlie Cleveland at DWCS Season 10 Week 4",
                       "https://dknetwork.draftkings.com/2026/09/01/prediction-pick-for-gabriel-lourenco-vs-charlie-cleveland-at-dwcs-season-10-week-4/",
                       "2026-09-01", "Ryan Wohl"),
    "cage_pat": src("Cageside Press", "UFC Vegas 115: Thomas Petersen Turns It Up Late, Snags Majority Decision Over Undefeated Guilherme Pat",
                    "https://cagesidepress.com/2026/04/04/ufc-vegas-115-thomas-petersen-guilherme-pat/", "2026-04-04",
                    "Patrick Danna"),
    "lowkick_v115": src("LowKick MMA", "UFC Vegas 115: Moicano vs. Duncan - Prelim Results and Highlights",
                        "https://www.lowkickmma.com/ufc-vegas-115-prelim-results-highlights/", "2026-04-04"),
    "cage_petrino": src("Cageside Press", "UFC Rio: Vitor Petrino Turns Lights Out on Thomas Petersen",
                        "https://cagesidepress.com/2025/10/11/ufc-rio-vitor-petrino-turns-lights-out-on-thomas-petersen",
                        "2025-10-11"),
    "lowkick_walker": src("LowKick MMA", "\"I Have Not Cheated on Her in 6 Months.\" Valter Walker Makes Wild Claim About His Relationship",
                          "https://www.lowkickmma.com/not-cheated-on-her-in-6-months-valter-walker/", "2026-07-28"),
    "lowkick_ad_losers": src("LowKick MMA", "UFC Abu Dhabi: Matchmaking for All the Losers from Saturday",
                             "https://www.lowkickmma.com/ufc-abu-dhabi-matchmaking-for-all-the-losers/", "2026-07-28",
                             "Danny Podolsky"),
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
report("Austin Bashi",
       "A 25-year-old featherweight wrestler-grappler (14-2; 1-2 UFC) out of the 2024 Contender Series who was 13-0 before "
       "the UFC. He has lost both UFC decisions against opponents who could stop his shots and out-strike him (Christian "
       "Rodriguez, Jose Delgado). His one UFC win was a first-round RNC of short-notice opponent John Yannis. He comes off a "
       "fractured nose and orbital from the Delgado fight in July.",
       {"Striking": "Functional, mostly there to set up the shot. Willing to stand and swing heavy hooks, sometimes recklessly: "
                    "Cageside Press says he scored a knockdown on Delgado early, then got dropped twice in R1 (a punch, then a "
                    "flying knee). Our verified data credits only Delgado with a knockdown, so the outlets and our table disagree. "
                    "Low volume in the UFC (about 2.4 significant strikes a minute) and Rodriguez hurt him with a knee early.",
        "Grappling": "The core of his game: chain wrestling, single legs, lifts and slams, then back takes and chokes. Six career "
                     "submissions, including an RNC of Yannis off a takedown and back take, and he swept to mount from a "
                     "guillotine against Delgado late in R3 (Cageside). The UFC problem is efficiency: 3 of 18 takedowns vs "
                     "Rodriguez and 3 of 14 vs Delgado in our data, 7 of 33 across three UFC fights. He does control when he gets "
                     "there (5:41 of control vs Rodriguez).",
        "Defense": "Leaves his neck out on entries (Rodriguez had a guillotine opening, per Cageside). Hittable when he plants to "
                   "trade. Never stopped: both losses were unanimous decisions. Takedown defense has held up reasonably (about "
                   "66%).",
        "Pace & cardio": "Front-to-middle-round finisher who struggles late. Stoppage wins: four in R1, four in R2, one in R3 (a 2021 "
                         "regional sub). Decisions: five, including a five-round win in 2022 on the regional scene. In both UFC "
                         "losses he lost the later rounds: Cageside says his cardio faded and his shots got telegraphed in R3 against "
                         "Rodriguez, and that his gas tank looked to fade in R3 against Delgado even as he swept to mount. Sherdog's "
                         "Tom Feely flagged before his debut that he was on the small side for 145 after moving up from bantamweight, "
                         "and that his gas tank was the question.",
        "Fight IQ": "Persistent: keeps shooting after being stuffed and keeps coming forward after being hurt (recovered from two R1 "
                    "knockdowns against Delgado and kept wrestling through R2-R3). Trains alongside "
                    "Diego Lopes (Cageside's TTP podcast)."},
       ["Chain wrestling into back takes and chokes; nine of his 14 wins by finish",
        "Finishes come in R1-R2 (eight of nine stoppages); no UFC finish past 3:39 of R1",
        "Low takedown accuracy against UFC-level defense (7 of 33)",
        "Fades and gets telegraphed in R3 (Rodriguez, Delgado)",
        "Never stopped; both losses were decisions where he was out-struck"],
       ["Coming off fractures to the nose and orbital bone (July)",
        "Small for featherweight",
        "Reckless exchanges on the feet"],
       ["Stuff the first takedowns and make him wrestle tired by R3",
        "Punish the level change with knees and front-headlock threats",
        "Out-land him at range; he's lost on volume both times"],
       [n("2026-07-20", "Said on Instagram he suffered a small fracture in the nose and in the orbital bone in the Delgado loss, "
                        "and was taken to hospital after the fight.", "es_bashi_inj"),
        n("2026-07-18", "Lost a unanimous decision to Jose Delgado (30-27, 29-28, 29-28); Cageside counts knockdowns both ways.",
          "cage_delgado"),
        n("2026-10-26", "The Bashi vs. Lucas Brennan featherweight bout is on the UFC Vegas 124 prelims.", "si_change")],
       ["cage_delgado", "es_bashi_inj", "cage_rodriguez", "sherdog_v101_prev", "cage_okc_next", "cage_ttp540", "si_change"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Lucas Brennan",
       "A 26-year-old Texas grappler (11-3; 0-1 UFC), a BJJ black belt and the son of former fighter Chris Brennan, who went 9-0 "
       "in Bellator as a teen prospect, then lost three of his next five fights, all by decision. He debuted in April at lightweight against "
       "Francis Marshall a few days after signing (per Wikipedia) and lost 30-27 x3 without landing a takedown. He returns to "
       "featherweight here.",
       {"Striking": "Long, kick-heavy and feint-heavy rather than a pocket boxer: side kicks, leg kicks, spinning back kicks (Sherdog "
                    "PFL play-by-play) and a knee KO of Weber Almeida in 2023 (R3). Low output and little defense in the UFC debut: "
                    "out-landed 33-9 by Marshall, who cracked him with inside leg kicks and straight rights (Cageside).",
        "Grappling": "His real weapon. Eight of his 11 wins are submissions, every one of them in R1 (RNC, anaconda, assassin's "
                     "choke, forearm choke, neck crank, per Wikipedia's record). Takes the back off scrambles and hunts chokes; threatens heel "
                     "hooks and omoplatas off his back (deep heel hook vs Marshall in R1; omoplata vs Dimitre Ivy). His wrestling to "
                     "get there is the weak link: 0 of 6 takedowns vs Marshall, and he gets put on his back.",
        "Defense": "Never stopped. All three losses were decisions (Ivy UD as a -650 favourite in our odds data, Mauricio Gomez split, "
                   "Marshall UD). Gets out-struck and out-clinched: Ivy won R1 and R3 with clinch knees and body work, Marshall held "
                   "him down for 6:36.",
        "Pace & cardio": "An R1 submission artist: eight of nine stoppages came in R1, the other two (TKO R2 2020, KO R3 2023) were "
                         "strikes. When the early submission doesn't land he tends to lose the minutes: all three losses went the "
                         "full 15. His only decision win came in 2020 (Salas). Sherdog scored the Ivy fight R1 Ivy, R2 "
                         "Brennan (back control), R3 Ivy.",
        "Fight IQ": "Comfortable on his back and willing to give position to attack legs; that cost him rounds against Marshall. "
                    "The Bellator-era quality of opposition was modest; his two 2025 wins came on the Texas regional scene (XKO)."},
       ["Submission finisher: eight R1 submissions",
        "Back takes from scrambles, leg attacks off his back",
        "Never finished; all three losses were 15-minute decisions",
        "Struggles to land takedowns against good wrestlers",
        "Loses the striking minutes when he can't get the fight down"],
       ["0 for 6 on takedowns in his UFC debut",
        "Has lost three of his last five fights",
        "Weight change: debuted at lightweight, back down to featherweight",
        "Low striking output"],
       ["Win the striking minutes with straight shots and leg kicks",
        "Stay out of scrambles and don't give up the back",
        "Take him down and stay heavy; avoid his leg attacks from bottom"],
       [n("2026-04-25", "Lost his UFC debut to Francis Marshall by unanimous decision (30-27 x3) at lightweight.", "cage_marshall"),
        n("2026-10-27", "Wikipedia says he signed with the UFC on April 20 and debuted five days later; he is booked back at "
                        "featherweight against Austin Bashi.", "wiki_brennan")],
       ["cage_marshall", "wiki_brennan", "sherdog_pfl1", "bjp_v116", "si_change"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Priscila Cachoeira",
       "A 38-year-old Brazilian brawler (13-9; 5-9 UFC) on a three-fight losing streak and 1-5 since 2023 (per MMA Sucka and our "
       "data). She comes forward swinging, has one-punch power in R1, and is very tough on the feet, but she has been submitted "
       "five times in the UFC, each time after being taken down or dropped.",
       {"Striking": "Forward-pressure slugger with wide hooks and overhands; she leads the exchanges and is willing to eat shots to "
                    "land hers. Real early power: five of her eight KO/TKO wins came in R1, including the clinch uppercut on Josiane "
                    "Nunes (LowKick's best knockouts of 2025) and Ariane Lipski at 1:05. She loses the volume battle against busier "
                    "strikers: Sygula out-worked her over three rounds despite Cachoeira doing the visible damage (Cageside).",
        "Grappling": "Almost none offensively (one or two takedowns a fight at most; dumped Sygula off a caught kick in R3). On her "
                     "back she gives up position: Chandler took her back after dropping her and armbarred her at 3:42 of R1; "
                     "Maverick and Jasudavicius controlled her for about 9 and 11 minutes before finishing in R3.",
        "Defense": "Absorbs about 6.5 significant strikes a minute, the worst number in this group. Losses: five submissions (R1 x2, "
                   "R2, R3 x2), one KO (Joselyne Edwards, R1, 2025) and three decisions. Takedown defense is decent on paper (77%) "
                   "but everyone who wants to wrestle her eventually gets her down.",
        "Pace & cardio": "An R1-R2 finisher: all eight KO/TKO wins came in R1 (five) or R2 (three). Her last finish win was R1 (Nunes, "
                         "2025). When she loses she is often finished: R1 against Robertson, Edwards and Chandler; late R3 against "
                         "Maverick and Jasudavicius after long stretches on her back. She doesn't stop coming forward late, but she "
                         "doesn't win late rounds either.",
        "Fight IQ": "One gear: pressure and swing. Let Chandler back up after putting her down and was caught coming in (Cageside)."},
       ["Swings hard early; five R1 knockouts",
        "Loses volume battles over 15 minutes",
        "Five UFC submission losses after being taken down or dropped",
        "Six UFC stoppage losses: three in R1, one in R2, two in R3"],
       ["Age 38 and 1-5 since 2023",
        "Defense: absorbs 6.5 significant strikes a minute",
        "Bottom game against anyone who can take her back"],
       ["Survive the first two minutes and don't trade in the pocket",
        "Body shots and volume; she stays in front of you",
        "Take her down or take her back off a scramble"],
       [n("2026-06-06", "Submitted by Chelsea Chandler (armbar, 3:42 of R1) after being dropped by a short right.", "cage_chandler"),
        n("2026-09-25", "Booked against Nina Nikolija Milosevic; MMA Sucka notes she enters on a three-fight skid.",
          "sucka_cach_nina")],
       ["cage_chandler", "cage_sygula", "bjp_v109", "bjp_v104", "lowkick_ko2025", "sucka_cach_nina"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Nina Nikolija Milosevic",
       "A Swedish-born Serbian bantamweight (9-1; 1-0 UFC; age 30 in our data, 29 per UFC.com in July) trained by Renato "
       "Subotic in Sydney. A two-time IMMAF amateur gold medallist, karate black belt and BJJ brown belt. She won her UFC debut in "
       "Belgrade with body shots on Hailey Cowan (R1, 3:41) and a Performance of the Night bonus. Her regional opposition was thin.",
       {"Striking": "Patient early, then sharp: Cageside says she was content to let Cowan lead in the opening minutes, didn't move "
                    "her head much, then dropped Cowan with a straight right to the body and finished with a second one. "
                    "Out-landed Cowan 21-13. She says her plan is to wait for an opening and pounce (UFC.com).",
        "Grappling": "Real submission game: a Bernardino submission in R3 (2024) and a 52-second finish of Gina Gee (2025). Against "
                     "Dina Osman at BRAVE CF 104 she chained submission attempts in R1 and nearly finished an RNC in R3 on the way to "
                     "30-26 x3 (BRAVE CF). Stuffed both of Cowan's takedown attempts.",
        "Defense": "Untested at a high level. Hit a bit early against Cowan. Her only loss was a split decision in her 2023 pro debut "
                   "to Cecilie Bolander. Never stopped.",
        "Pace & cardio": "Mostly a first-round finisher: five of six stoppages came in R1 (four KO/TKO, one sub), plus the R3 "
                         "submission. Her three decisions all went 15 minutes, and IMMAF and BRAVE describe her as composed over three "
                         "rounds, increasing output in R2-R3 against Osman.",
        "Fight IQ": "Calm, counter-minded starter who adjusts mid-fight. Her pre-UFC opposition came from small regional "
                    "promotions; Cowan (0-4 in the UFC, retired afterwards) was arguably the best opponent of her career."},
       ["Patient first minutes, then a finishing burst",
        "Body attack (two body shots finished Cowan)",
        "Submission threats on the mat; finished in R1 five times",
        "Can go 15 minutes and build pace (Osman)"],
       ["Thin opposition; one UFC fight, against a fighter who then retired",
        "Head movement early (Cageside)",
        "Ages disagree (29 vs 30)"],
       ["Out-work her in the first two minutes before she settles",
        "Make her lead and counter her",
        "Wrestle her and test her bottom game, which nobody has done"],
       [n("2026-08-01", "Stopped Hailey Cowan with body shots at 3:41 of R1 in her UFC debut in Belgrade; earned Performance of the "
                        "Night.", "cage_cowan"),
        n("2026-08-04", "Cowan retired after the loss, finishing 0-4 in the UFC.", "cage_cowan_retire"),
        n("2026-09-25", "Booked against Priscila Cachoeira for her second UFC fight.", "sucka_cach_nina")],
       ["cage_cowan", "ufc_nina", "immaf_nina", "brave_104", "cage_cowan_retire", "sucka_cach_nina"],
       "thin")

# ---------------------------------------------------------------------------------------------------------------
report("Jonny Parsons",
       "A 35-year-old Las Vegas welterweight (9-3; 1-0 UFC), a former Muay Thai fighter and 2021 Contender Series winner, "
       "returning from about 40 months out. His only UFC fight was a Fight of the Night TKO of Danny Roberts in July 2023. Since "
       "then, bookings against Uros Medic (Nov 2023) and Yusaku Kinoshita (Aug 2024) didn't happen, and he told MMA Junkie that "
       "hip flexor and groin problems kept him out.",
       {"Striking": "A pressure kickboxer who likes to trade. Seven of nine wins by KO/TKO. Against Roberts he lost R1 at range, "
                    "then found a right hand in R2, pinned Roberts on the fence with knees and uppercuts, and dropped him with a "
                    "combination for a TKO at 4:57 (Sherdog). He calls himself more technical than his brawler reputation and "
                    "promises hard kicks (MMA Junkie).",
        "Grappling": "Defensive only. Solomon Renfro took him down twice and controlled him for almost two minutes on the Contender "
                     "Series, and Roberts shot on him late. Rarely looks for takedowns himself (0 of 3 on DWCS).",
        "Defense": "Takes shots to give them. Knocked down once by Renfro, out-landed by Roberts in R1. Stopped twice by strikes, both "
                   "in R2 and both long ago (2013 pro debut on a day's notice in Thailand, 2018). His one other loss was a five-round "
                   "decision in 2019.",
        "Pace & cardio": "A second-round finisher: KO/TKOs came in R1 three times and R2 four times; none in R3. His DWCS win went "
                         "15 minutes on a split. He tends to lose R1 and turn it up in R2 (Roberts). After more than three years out "
                         "at 35, his conditioning over 15 minutes is an unknown.",
        "Fight IQ": "Thinks the layoff may help and says he now trains with better habits. Says he'll be tricky and elusive, but his "
                    "own pre-fight talk has a way of turning into a slugfest."},
       ["Kickboxer who wins exchanges in close: knees and uppercuts on the fence",
        "Finishes in R1-R2; seven KO/TKOs, none in R3",
        "Slow first round, better in R2 (Roberts)",
        "Gets hit and has been knocked down"],
       ["About 40 months without a fight; repeated hip flexor and groin problems",
        "Age 35",
        "Takedown defense if Souza changes levels",
        "Two announced UFC bookings (Medic 2023, Kinoshita 2024) fell through"],
       ["Take the first round at range with the jab and kicks",
        "Wrestle him; he does nothing off his back",
        "Push the pace in R3 to test the layoff"],
       [n("2026-10-15", "Told MMA Junkie he has been out about 40 months, mainly with hip flexor and groin problems, and that "
                        "rehab at the UFC Performance Institute fixed them. He says he feels as strong as he has in five years.",
          "junkie_parsons"),
        n("2024-06-16", "A booking against Yusaku Kinoshita for August 2024 was announced but never took place.",
          "cage_kinoshita_book"),
        n("2023-11-06", "A November 2023 bout against Uros Medic was also announced but not fought.", "sucka_medic")],
       ["junkie_parsons", "sherdog_roberts", "cage_parsons_dwcs", "sucka_medic", "cage_kinoshita_book", "si_change"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Jose Henrique Souza",
       "A 24-year-old, 6-foot-3 Brazilian welterweight ('Canela', Nova Uniao, from Manaus; 9-1, 1-0 UFC). He signed with the UFC "
       "in 2023 after a Contender Series loss, then served a two-year USADA ban for nandrolone before winning his debut over Ding "
       "Meng in May on a split decision. A Muay Thai striker who likes knees and works behind a jab at range.",
       {"Striking": "Long jab and right hand, knees in the clinch (his favourite strike, per his UFC profile) and spinning attacks. "
                    "His UFC profile lists 99% of his strikes thrown standing. Against Ding he kept range, landed a clean knee in R2 "
                    "and cut Ding with a spinning strike early in R3 (Cageside). Our data has him out-landing Ding 72-63.",
        "Grappling": "BJJ brown belt, but no takedowns attempted by either man against Ding, and nothing on the mat in the UFC. He "
                     "has no submission wins; his fights are won and lost on the feet.",
        "Defense": "Hittable: absorbs about 4.3-4.9 significant strikes a minute depending on the source. Stopped once: Yusaku "
                   "Kinoshita knocked him down and finished him at 0:43 of R3 on the 2022 Contender Series, out-landing him 62-37. "
                   "Ding caught a kick and took him down in R2 (Cageside).",
        "Pace & cardio": "Not an early blitzer. KO/TKO wins: two in R1, three in R2, one in R3 (a knee with five seconds left, per "
                         "Sherdog). Three split decisions. He finishes stronger than he starts against Ding, winning R3 clearly after "
                         "looking a step slower late in R1, but his one loss came early in R3 after he was worn down.",
        "Fight IQ": "Happy to coast on a lead: retreated and showboated in the final seconds against Ding and was booed (Cageside). "
                    "Close fights tend to go to the cards."},
       ["Range striker: jab, right hand, knees",
        "Wins the third round late (Ding)",
        "Three of his last five wins were split decisions",
        "Stoppages spread across R1-R3; not a pure fast starter"],
       ["Two-year USADA sanction (nandrolone) in 2023-25",
        "Stopped in R3 on the Contender Series",
        "Coasts late; close rounds can slip away"],
       ["Close the distance and fight him in the pocket",
        "Wrestle him; he's had no takedown exchanges in the UFC",
        "Win R1 and R2 clearly so his R3 surge isn't enough"],
       [n("2026-05-30", "Won his UFC debut over Ding Meng by split decision; Cageside lists the cards as 30-27, 28-29, 29-28.",
          "cage_ding"),
        n("2023-06-01", "Accepted a two-year USADA sanction for nandrolone, backdated to a March 8, 2023 test; he was "
                        "eligible again from about March 2025.", "cage_souza_usada")],
       ["cage_ding", "ufc_souza", "sherdog_souza_sign", "cage_souza_usada", "junkie_parsons", "si_change"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Mitch Raposo",
       "A 28-year-old American flyweight (11-3; 2-2 UFC; Regiment Training Center) who has won two straight decisions after "
       "starting 0-2 in the UFC on split losses. Fast-handed and mobile, with good takedown defense and the ability to get back up. "
       "All four of his UFC fights went the distance, and three were split decisions.",
       {"Striking": "Fast starter on the feet: jab, quick combinations and a left hook that cut Nascimento in R1. Moves a lot to "
                    "avoid power, and can switch to standing in the pocket and timing exchanges (Cageside, on Nascimento R2). Says "
                    "he wants to 'throw hands', not wrestle. Low volume overall (about 2.8 significant strikes a minute).",
        "Grappling": "Defensive and scrambly. Stuffed takedowns with uppercuts against Nascimento (four stopped in our data). Maksum "
                     "landed 7 of 19 and controlled him for over five minutes, but Raposo kept standing up and threatened an omoplata "
                     "and a guillotine. Three career submissions, all regional.",
        "Defense": "Never knocked out. Jake Hadley submitted him in R2 on the 2021 Contender Series. Both UFC losses were split "
                   "decisions (Andre Lima, Su Mudaerji). He was dropped by Nascimento in R3 and survived under ground strikes by "
                   "tying him up.",
        "Pace & cardio": "Wins early rounds, gets tested late. Against Nascimento he won R1 and R2 and lost R3 after a knockdown; "
                         "Maksum's wrestling took over in R3 too. Stoppage wins: four in R1, one in R2, one in R3, one in R4 of a "
                         "five-rounder (2024 regional title fight). He hasn't finished anyone in the UFC.",
        "Fight IQ": "Fight-to-fight improvement, and he has talked openly about pre-fight nerves ('demons') before his first UFC win. "
                    "Tends to leave close fights with the judges."},
       ["Takes R1 with speed and movement",
        "Strong takedown defense and gets back up",
        "All four UFC fights went the distance; three split decisions",
        "Has been hurt or out-grappled in R3 (Nascimento, Maksum)"],
       ["Late-fight dips: dropped in R3 by Nascimento",
        "Low output against a busy finisher",
        "Pulled out of the April Nascimento date with a virus"],
       ["Survive his R1 speed and come on late",
        "Pressure him into the fence and go to the body",
        "Mix in takedowns late to steal R3"],
       [n("2026-06-20", "Beat Allan Nascimento by split decision (29-28, 29-28, 28-29) after being dropped in R3.",
          "cage_nascimento"),
        n("2026-04-16", "Pulled out of the original April date at UFC Winnipeg with a virus; the fight moved to June.",
          "cage_winnipeg_ill"),
        n("2026-08-03", "Nascimento, his last opponent, died in August at age 34 after an apparent heart attack in his sleep.",
          "br_nascimento"),
        n("2026-10-06", "Booked against Contender Series signee Marcos Degli (first reported by Ag Fight, per MMA Sucka).",
          "sucka_degli_raposo")],
       ["cage_nascimento", "cage_raposo_chairez", "cage_maksum", "cage_raposo_demons", "cage_winnipeg_ill", "br_nascimento",
        "sucka_degli_raposo"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Marcos Degli",
       "A 26-year-old Brazilian flyweight (15-3) from Vale Top Team, where he trains with Carlos Prates. Former LFA flyweight "
       "champion, on a 13-fight win streak with 14 of 15 wins by finish. He earned a contract on the Contender Series in "
       "September with a one-arm rear-naked choke of Paris Moran. UFC debut.",
       {"Striking": "Muay Thai base; calls himself an aggressive finisher with 'very heavy hands' (MMA Sucka). Nine KO/TKO wins, "
                    "six of them in R1. No footage-based breakdown of his striking is available in what we've read.",
        "Grappling": "Underrated, going by the Contender Series win. UFC.com says he pushed Moran to the fence, took him down, nearly "
                     "finished a standing guillotine, then took the back with a body triangle in R1; in R2 he took Moran down again, "
                     "tried a face crank and switched to a one-arm RNC at 4:46. Five career submissions.",
        "Defense": "Little information. Moran landed knees to his hamstrings early in R2 (UFC.com). His three losses all came in "
                   "2021-22, when he started 2-3: two decisions and an R3 submission.",
        "Pace & cardio": "Early finisher: eight stoppages in R1, five in R2, one in R3 (an LFA TKO in 2025). Only one decision win. "
                         "Went 15 minutes once in a win (LFA, 2023) and won an LFA main event by R3 TKO (2025).",
        "Fight IQ": "Adjusts when a submission doesn't land (face crank to one-arm choke). Debuting against a UFC veteran who has "
                    "never been knocked out."},
       ["Finishes fast: 13 of 14 stoppages in R1-R2",
        "Muay Thai power plus a back-take and choke game",
        "13-fight win streak; regional and LFA opposition",
        "Last loss in 2022"],
       ["UFC debut against a durable, mobile veteran",
        "No information yet on how he handles adversity at this level"],
       ["Survive the first round and drag him to the cards",
        "Use movement and takedown defense to deny the back",
        "Bank rounds on volume"],
       [n("2026-09-22", "Earned a UFC contract with a standing one-arm rear-naked choke of Paris Moran (4:46 R2) on the Contender "
                        "Series.", "ufc_dwcs_w7"),
        n("2026-09-23", "Had nearly fought Marwan Rahiki in Australia earlier in 2026, but a visa problem stopped it (Cageside).",
          "cage_degli"),
        n("2026-10-06", "Booked against Mitch Raposo for his UFC debut.", "sucka_degli_raposo")],
       ["ufc_dwcs_w7", "cage_degli", "bn_degli", "sucka_degli_prates", "sucka_degli_raposo", "si_change"],
       "thin")

# ---------------------------------------------------------------------------------------------------------------
report("Gabriel Lourenco",
       "A 27-year-old Brazilian heavyweight ('The Black Mamba', Chute Boxe; 8-1; 6-foot-2, 76-inch reach) who earned a contract in "
       "September with a first-round KO of Charlie Cleveland on the Contender Series as an underdog. Seven of his eight wins are "
       "first-round finishes. UFC debut, now against short-notice replacement Thomas Petersen after Alvin Hines withdrew.",
       {"Striking": "Aggressive starter who throws heavy combinations early (Rotowire). Cleveland timed him with counters early, then "
                    "Lourenco caught him with a combination and finished with an elbow and punches at 2:02 of R1. Rotowire's "
                    "analysts say he needs technical polish.",
        "Grappling": "One submission win (R1, 2025). No wrestling information available.",
        "Defense": "Got hit early by Cleveland's counters. His one loss was a R1 KO (1:20) in his 2021 pro debut.",
        "Pace & cardio": "Everything happens in R1: all seven finishes came in the first round, most of them inside two minutes. "
                         "His only fight that went past R1 was a 2024 decision. How he copes in R2-R3 against a heavyweight who "
                         "wrestles and clinches is unknown. (Our data lists a 0:00 finish time for one 2025 regional win, which is "
                         "probably a record-keeping error.)",
        "Fight IQ": "Little to judge. Debuting on a changed opponent: he'd prepared for Hines, a different fighter."},
       ["Seven R1 finishes; all his stoppages come early",
        "Heavy combinations and elbows when the opponent is hurt",
        "Only one fight past R1",
        "Was hit early by counters on DWCS"],
       ["Untested past R1",
        "Opponent change two weeks out",
        "Takedown defense unknown"],
       ["Clinch and wrestle him; make him carry weight",
        "Survive R1 and see what's left in R2-R3",
        "Counter his entries"],
       [n("2026-10-08", "Original opponent Alvin Hines withdrew citing vertigo.", "sherdog_hines"),
        n("2026-10-26", "Thomas Petersen stepped in as the replacement opponent.", "si_change"),
        n("2026-09-01", "Beat Charlie Cleveland by KO (elbow and punches) at 2:02 of R1 on the Contender Series to earn a "
                        "contract.", "rotowire_lourenco")],
       ["rotowire_lourenco", "dk_lourenco", "sherdog_hines", "si_change"],
       "thin")

# ---------------------------------------------------------------------------------------------------------------
report("Thomas Petersen",
       "A 32-year-old heavyweight wrestler (11-5; 3-4 UFC; Spartan MMA) taking this fight on about two weeks' notice, three-and-a-half "
       "months after Valter Walker submitted him with a calf slicer in 92 seconds. He alternates wins and losses in the UFC: he beats "
       "the lower tier with wrestling and clinch control and gets stopped by stronger strikers.",
       {"Striking": "Utility striking to close distance; better on the regional scene (seven KO/TKOs, six in R1). Against Pat he "
                    "dropped him twice in R3 (short right hook, uppercut) after two slow rounds (Cageside). Accurate (about 55%) but "
                    "low-volume.",
        "Grappling": "His main weapon: clinches against the fence, single legs, body locks, knees to the thighs. Went 9 for 9 with "
                     "nearly 14 minutes of control against Don'Tale Mayes; 0 for 5 against Pat but still had 8:36 of control. "
                     "Walker caught him in leg locks on the mat (heel hook, then calf slicer).",
        "Defense": "The problem: four of his five losses were stoppages. Waldo Cortes-Acosta TKO R3 (4:53, LFA 2022), "
                   "Shamil Gaziev TKO R1 (2025), Vitor Petrino KO R3 (0:26, after being dropped in R1, 2025), Walker sub R1 "
                   "(2026). He ducks his head into uppercuts (Cageside, on Petrino).",
        "Pace & cardio": "UFC wins are all decisions, built on control. Losses come either early to power (Gaziev R1, Walker R1) or "
                         "late after he's been worn down or dropped (Cortes-Acosta and Petrino in R3). Against Pat he got stronger in "
                         "R3. He's a lighter heavyweight (245 for Walker).",
        "Fight IQ": "Knows his lane: clinch, wrestle, grind. LowKick's view after Walker: good enough to beat the bottom of the "
                    "division, outmatched against ranked opposition."},
       ["Clinch and wrestling control; UFC wins all by decision",
        "Stopped by heavier hitters (Gaziev, Petrino, Cortes-Acosta)",
        "Two of four stoppage losses in R3, two in R1",
        "Can raise his output late (Pat, R3)"],
       ["Short notice, about 15 weeks after a submission loss",
        "Chin and defense against power punchers",
        "Leg-lock defense on the mat",
        "Our data has the Pat fight as a split decision; Cageside and LowKick report a majority decision (28-28, 29-27, 29-27)"],
       ["Stop the first takedowns and hit him on the way in",
        "Uppercuts as he ducks into the clinch",
        "Make him strike for 15 minutes"],
       [n("2026-10-26", "Stepped in on short notice to face Gabriel Lourenco after Alvin Hines withdrew.", "si_change"),
        n("2026-07-28", "Submitted by Valter Walker with a calf slicer in 92 seconds (first calf slicer win by a UFC heavyweight, "
                        "per LowKick).", "lowkick_walker"),
        n("2026-04-04", "Beat Guilherme Pat by majority decision (per Cageside; our data says split) after two R3 knockdowns.",
          "cage_pat")],
       ["si_change", "cage_pat", "lowkick_v115", "cage_petrino", "lowkick_walker", "lowkick_ad_losers", "sherdog_hines"],
       "moderate")


out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
