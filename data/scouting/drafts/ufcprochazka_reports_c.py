"""Scouting reports (part C) for UFC Fight Night: Procházka vs. Stirling (UFC Fight Night 294, Doha, 2026-11-21),
plus a late replacement on UFC 334: Gane vs. Hokit (2026-11-14). First pass written 2026-11-10.

Fight-week previews aren't out yet: these draw on recent-fight recaps, booking news and our verified records.
Round/method counts are taken from data/verified/fights.csv. Later runs should refresh them with the
Sherdog/Cageside previews and weigh-in news. Three of the Doha bouts (Sousa, Motta vs. Mar Fan, Nurgozhay vs.
Lorenz) are not yet on the UFC.com event page as of 2026-11-10.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATED = "2026-11-10T18:00:00+00:00"
EVENT = "UFC Fight Night: Procházka vs. Stirling"
EVENT_334 = "UFC 334: Gane vs. Hokit"


def src(outlet, title, url, date, author=""):
    return {"outlet": outlet, "author": author, "title": title, "url": url, "date": date}


SRC = {
    # card / booking
    "ufc_event": src("UFC.com", "UFC Fight Night: Procházka vs. Stirling (event page)",
                     "https://www.ufc.com/event/ufc-fight-night-november-21-2026", "2026-11-10"),
    "wiki_event": src("Wikipedia", "UFC Fight Night: Procházka vs. Stirling",
                      "https://en.wikipedia.org/wiki/UFC_Fight_Night:_Proch%C3%A1zka_vs._Stirling", "2026-11-10"),
    # Matthews
    "wiki_matthews": src("Wikipedia", "Jake Matthews (fighter)", "https://en.wikipedia.org/wiki/Jake_Matthews_(fighter)",
                         "2026-11-10"),
    "cage_harris": src("Cageside Press", "Jake Matthews Dominates Harris, Takes Decision Victory In Macau",
                       "https://cagesidepress.com/2026/05/30/jake-matthews-dominates-harris-takes-decision-victory-in-macau/",
                       "2026-05-30", "Eddie Law"),
    "sherdog_magny_appeal": src("Sherdog", "Australian Commission Denies Jake Matthews' Appeal of Loss to Neil Magny",
                                "https://www.sherdog.com/news/news/Australian-Commission-Denies-Jake-Matthews-Appeal-of-Loss-to-Neil-Magny-198884",
                                "2025-10-29", "Tristen Critchfield"),
    "sherdog_lebo": src("Sherdog", "Jean-Paul Lebosnoyani calls out Jake Matthews after UFC Vegas 123 TKO",
                        "https://www.sherdog.com/news/news/JeanPaul-Lebosnoyani-calls-out-Jake-Matthews-after-UFC-Vegas-123-TKO-203445",
                        "2026-11-01", "Sourav Chakraborty"),
    # Abdullayev
    "cage_nascimento": src("Cageside Press", "Tahir Abdullayev Stops Jefferson Nascimento in Controversial UFC Baku Debut",
                           "https://cagesidepress.com/2026/06/27/tahir-abdullayev-stops-jefferson-nascimento-in-controversial-ufc-baku-debut/",
                           "2026-06-27", "Shawn Bitter"),
    "lowkick_nascimento": src("LowKick MMA", "UFC Baku: Tahir Abdullayev Spoils Jefferson Nascimento's Perfect Record In Debated Stoppage",
                              "https://www.lowkickmma.com/tahir-abdullayev-controversial-tko-ufc-baku/", "2026-06-27",
                              "Pranav Pandey"),
    # Sousa
    "heavy_sousa": src("Heavy", "UFC Qatar Gets Lightweight Banger Fight",
                       "https://heavy.com/sports/ufc/ufc-qatar-gets-lightweight-banger-fight/", "2026-09-26", "Adam Martin"),
    "sportscape_zaynukov": src("Sportscape Magazine",
                               "Magomed Zaynukov Withdraws From Reported UFC Qatar Fight With Manoel Sousa Due to Physical Issues",
                               "https://www.sportscapemagazine.com/blog/magomed-zaynukov-withdraws-from-reported-ufc-qatar-fight-with-manoel-sousa-due-to-physical-issues",
                               "2026-09-27", "Rohit Gupta"),
    "cage_miranda": src("Cageside Press", "UFC Vegas 120: Hard-Hitting Manoel Sousa Prevails Over Richie Miranda",
                        "https://cagesidepress.com/2026/08/08/ufc-vegas-120-hard-hitting-manoel-sousa-prevails-over-richie-miranda/",
                        "2026-08-08", "Shawn Bitter"),
    "bjp_v114_bonus": src("BJPenn.com", "UFC Vegas 114 Bonus Report: Manoel Sousa one of four 'POTN' winners",
                          "https://www.bjpenn.com/mma-news/ufc-vegas-114/ufc-vegas-114-bonus-report-manoel-sousa-one-of-four-potn-winners/",
                          "2026-03-15"),
    "yahoo_oki": src("Yahoo Sports (MMA Junkie)",
                     "UFC Vegas 114 video: Manoel Sousa flattens Bolaji Oki with devastating 1-punch knockout",
                     "https://sports.yahoo.com/articles/ufc-vegas-114-video-manoel-231234168.html", "2026-03-14"),
    # Motta / Mar Fan
    "cage_qatar_two": src("Cageside Press", "Two Fights Officially Announced for UFC Qatar",
                          "https://cagesidepress.com/2026/10/30/two-fights-officially-announced-for-ufc-qatar/", "2026-10-30"),
    "cage_sadykhov": src("Cageside Press", "Nazim Sadykhov Goes To War With Motta, Takes R2 TKO Win",
                         "https://cagesidepress.com/2025/06/21/nazim-sadykhov-goes-to-war-with-motta-takes-r2-tko-win/",
                         "2025-06-21"),
    "si_motta_jaw": src("Sports Illustrated (FanNation)", "UFC Baku fighter details grisly injury sustained in epic 'Fight of the Night'",
                        "https://www.si.com/fannation/mma/news/ufc-jaw-injury-fight-nikolas-motta", "2025-07-02",
                        "Drew Beaupre"),
    "cage_nolan_ko": src("Cageside Press", "UFC Vegas 84: Nikolas Motta Floors Tom Nolan Early",
                         "https://cagesidepress.com/2024/01/13/ufc-vegas-84-nikolas-motta-floors-tom-nolan-early/", "2024-01-13"),
    "cage_maheshate": src("Cageside Press", "Nikolas Motta Kicks Off UFC Macau with Decision Over Maheshate",
                          "https://cagesidepress.com/2024/11/23/nikolas-motta-kicks-off-ufc-macau-with-decision-over-maheshate/",
                          "2024-11-23"),
    "sherdog_325_prev": src("Sherdog", "Preview: UFC 325 Prelims - Mar Fan vs. Kim",
                            "https://www.sherdog.com/news/articles/6/Preview-UFC-325-Prelims-199909", "2026-01-28", "Tom Feely"),
    "cage_kim": src("Cageside Press", "UFC 325: Dom Mar Fan Tops Sangwook Kim in Road to UFC 4 Lightweight Final",
                    "https://cagesidepress.com/2026/01/31/ufc-325-dom-mar-fan-tops-sangwook-kim-in-road-to-ufc-4-lightweight-final/",
                    "2026-01-31", "Jay Anderson"),
    "lowkick_perth": src("LowKick MMA", "UFC Perth: Della Maddalena vs. Prates – Full Results and Highlights",
                         "https://www.lowkickmma.com/ufc-perth-results-highlights/", "2026-05-02"),
    # Nurgozhay / Lorenz
    "yahoo_nur_lorenz": src("Yahoo Sports (MMA Junkie)", "Diyar Nurgozhay vs. Alik Lorenz booked for UFC Qatar",
                            "https://sports.yahoo.com/articles/diyar-nurgozhay-vs-alik-lorenz-184019443.html", "2026-10-15",
                            "Danny Segura, Nolan King"),
    "yahoo_lopes": src("Yahoo Sports (MMA Junkie)", "UFC Vegas 120 video: Diyar Nurgozhay's TKO of Bruno Lopes beats Round 1 buzzer",
                       "https://sports.yahoo.com/articles/ufc-vegas-120-video-diyar-232050516.html", "2026-08-08", "Mike Bohn"),
    "cage_tobias": src("Cageside Press", "UFC 326: Diyar Nurgozhay Finally Picks Up First UFC Win, Over Rafael Tobias",
                       "https://cagesidepress.com/2026/03/07/ufc-326-diyar-nurgozhay-finally-picks-up-first-ufc-win-over-rafael-tobias/",
                       "2026-03-07", "Shawn Bitter"),
    "sherdog_nur_fans": src("Sherdog", "Diyar Nurgozhay reveals some fans deserted him after early UFC losses",
                            "https://www.sherdog.com/news/news/Diyar-Nurgozhay-reveals-some-fans-deserted-him-after-early-UFC-losses-200374",
                            "2026-03-08", "Sayan Nag"),
    "cage_satybaldiev": src("Cageside Press", "UFC Shanghai: Uran Satybaldiev Hits Rarely Seen Ezekiel Choke on Diyar Nurgozhay",
                            "https://cagesidepress.com/2025/08/23/ufc-shanghai-uran-satybaldiev-hits-rarely-seen-ezekiel-choke-on-diyar-nurgozhay/",
                            "2025-08-23"),
    "cage_ribeiro": src("Cageside Press", "UFC Vegas 104: Brendson Ribeiro Submits Overweight Diyar Nurgozhay",
                        "https://cagesidepress.com/2025/03/15/ufc-vegas-104-brendson-ribeiro-submits-overweight-diyar-nurgozhay-takes-0/",
                        "2025-03-15"),
    "cage_lorenz_redemption": src("Cageside Press", "Redemption: Second Chances on Dana White's Contender Series — Alik Lorenz",
                                  "https://cagesidepress.com/2026/08/18/redemption-second-chances-on-dana-whites-contender-series-alik-lorenz/",
                                  "2026-08-18"),
    "cage_lorenz_int": src("Cageside Press", "Alik Lorenz Finds Strength in Prior DWCS Experience",
                           "https://cagesidepress.com/2026/08/17/alik-lorenz-finds-strength-in-prior-dwcs-experience/",
                           "2026-08-17", "Daniel Vreeland"),
    "cage_dwcs_w2": src("Cageside Press", "Dana White's Contender Series Season 10, Week 2 Results",
                        "https://cagesidepress.com/2026/08/18/dana-whites-contender-series-season-10-week-2-results/",
                        "2026-08-18"),
    # Heili (UFC 334)
    "wiki_334": src("Wikipedia", "UFC 334", "https://en.wikipedia.org/wiki/UFC_334", "2026-11-10"),
    "wiki_heili": src("Wikipedia", "Alateng Heili", "https://en.wikipedia.org/wiki/Alateng_Heili", "2026-11-10"),
    "yahoo_heili": src("Yahoo Sports (MMA Junkie)", "Hot prospect gets new UFC 334 opponent",
                       "https://sports.yahoo.com/articles/hot-prospect-gets-ufc-334-004029780.html", "2026-11-06",
                       "Nolan King"),
    "heavy_heili": src("Yahoo Sports (Heavy)", "UFC 334 Card Gets Late Booking",
                       "https://sports.yahoo.com/articles/ufc-334-card-gets-booking-053805923.html", "2026-11-07",
                       "Adam Martin"),
    "middleeasy_heili": src("MiddleEasy", "Juan Diaz vs. Alatengheili Reported For UFC 334 In New York",
                            "https://middleeasy.com/mma-news/juan-diaz-alatengheili-reported-ufc334-new-york/", "2026-11-06",
                            "Jake Blend"),
    "cage_castaneda": src("Cageside Press", "UFC Vegas 121: Alateng Heili Claims Split Decision In Close Fight with John Castaneda",
                          "https://cagesidepress.com/2026/09/26/ufc-vegas-121-alateng-heili-claims-split-decision-in-close-fight-with-john-castaneda/",
                          "2026-09-26", "Jay Anderson"),
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
report("Jake Matthews",
       "An Australian welterweight veteran (23-8; 16-8 UFC; age 32), a jiu-jitsu black belt who has been in the UFC since "
       "2014. He comes off a one-sided decision over Carlston Harris in May (30-25, 30-27, 30-27). His opponent changed from "
       "Akbar Abdullaev to Tahir Abdullayev after what Wikipedia describes as a matchmaking mistake by the promotion.",
       {"Striking": "Pressure boxer who walks opponents to the fence and lands in bursts, then exits (Cageside, on Harris). "
                    "Modest output (about 3.6 significant strikes a minute at 42%) but enough pop to drop people: he dropped "
                    "Harris in R3, and our data has knockdowns in his wins over Li, Meek, Sanchez and Fialho. Five KO/TKO wins, "
                    "the last a R2 stoppage of Andre Fialho in 2022.",
        "Grappling": "His best area. Nine submission wins, the most recent a R1 rear-naked choke of Chidi Njokuani (2025). "
                     "Against Harris he stuffed takedowns, took mount, chained a mounted triangle, arm triangle and kimura, then took "
                     "the back after the knockdown (Cageside). He had Neil Magny in a guillotine at the end of R1 at UFC Perth. "
                     "About 0.7 takedowns per 15; he prefers to win positions in scrambles over shooting from range.",
        "Defense": "Solid on the feet (60% striking defense, 2.9 absorbed a minute) and only stopped by strikes once (Kevin Lee, "
                   "R1, 2016). His weak point is the late submission: three of his four submission losses came in R3 (Anthony "
                   "Rocco Martin 2018, Sean Brady 2021, Magny 2025). Matthew Semelsberger dropped him three times in their 2022 "
                   "decision, per our data. Takedown defense around 66%.",
        "Pace & cardio": "A front-half finisher who otherwise goes the distance. Of 14 stoppage wins, 5 came in R1, 7 in R2 and "
                         "2 in R3 (the last R3 finish was 2016). Nine of his 23 wins are decisions, including five of his last eight. "
                         "His late fades show up as R3 submission losses: he won the first two rounds against Magny before being "
                         "choked at 3:08 of R3. Six of his eight losses went to R3 (three submissions, three decisions).",
        "Fight IQ": "Experienced and composed; against Harris he picked his power shots once openings came (Cageside). He has "
                    "had to deal with bad luck: the referee briefly stopped the Magny fight on his guillotine at the end of R1, "
                    "then let it continue, and the commission denied his appeal (Sherdog)."},
       ["Pressure to the fence, boxing in bursts",
        "Top control and submission chains from mount and the back",
        "Twelve of 14 stoppage wins came in R1-R2",
        "Three R3 submission losses, including Magny after winning R1-R2",
        "Rarely knocked out: one KO loss, in 2016"],
       ["Fading or getting caught in R3 scrambles",
        "Opponent changed from Akbar Abdullaev to Tahir Abdullayev; a different body type to prepare for",
        "Facing a heavy-handed, finishing-minded opponent"],
       ["Survive his R1-R2 pressure and grappling, then push the pace in R3",
        "Attack the neck in late scrambles; he has been submitted three times in R3",
        "Take the centre and keep him off the fence"],
       [n("2026-11-10", "First announced against Akbar Abdullaev; Wikipedia says that pairing was a matchmaking mistake by the "
                        "promotion, and he now meets Tahir Abdullayev. UFC.com lists Matthews vs. Abdullayev on the prelims.",
          "wiki_event"),
        n("2026-11-01", "Jean-Paul Lebosnoyani called him out after his UFC Vegas 123 win, telling him to finish his Doha fight "
                        "first.", "sherdog_lebo"),
        n("2026-05-30", "Beat Carlston Harris by unanimous decision (30-25, 30-27, 30-27), with a R3 knockdown; Harris had taken "
                        "the fight on short notice.", "cage_harris"),
        n("2025-10-29", "Australia's Combat Sports Commission upheld his R3 submission loss to Neil Magny despite the referee's "
                        "brief stoppage in R1; a UFC executive had called it a mistake.", "sherdog_magny_appeal")],
       ["wiki_event", "ufc_event", "wiki_matthews", "cage_harris", "sherdog_magny_appeal", "sherdog_lebo"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Tahir Abdullayev",
       "An Azerbaijani welterweight nicknamed 'Tank' (20-3 in our data; LowKick lists 22-3; age 30) who debuted in the UFC "
       "in June in Baku with a R3 TKO of the previously unbeaten Jefferson Nascimento. A stoppage-heavy regional record: 18 "
       "of his 20 wins are finishes. He replaced Akbar Abdullaev as Jake Matthews's opponent after a reported matchmaking "
       "mix-up.",
       {"Striking": "Forward-walking pressure fighter. Against Nascimento he struggled to cut off the cage and kept biting on feints, "
                    "and was outlanded in R2 as he came forward (Cageside, LowKick). Eleven KO/TKO wins, seven of them in R1, but "
                    "UFC sample is one fight: 37 of 87 significant strikes landed against 35.",
        "Grappling": "The UFC finish came from wrestling: an early R3 takedown, then well-timed takedowns whenever Nascimento opened "
                     "up, and heavy punches and hammerfists from top (Cageside). Seven submission wins on the regional scene. About "
                     "1.7 takedowns per 15 at 35%.",
        "Defense": "Takes some counters on the way in (Nascimento's right hands and leg kicks, per LowKick). Never stopped by strikes. "
                   "His three losses: a 2018 R2 submission to Roman Bogatov (M-1) and two five-round decisions at UAE Warriors "
                   "(Josh Togo 2022, Khotam Boynazarov 2024). Takedown defense about 67%.",
        "Pace & cardio": "Mostly an early finisher: of 18 stoppage wins, 10 came in R1, 6 in R2 and 2 in R3. The UFC debut was a "
                         "slow build, though, with a quiet R1 and a finish at 4:28 of R3, so he can keep pressing for 15 minutes. "
                         "Both five-round fights went to the judges and he lost both, which hints he is less effective over long fights.",
        "Fight IQ": "Patient enough to switch to wrestling once striking wasn't working (Cageside). Footwork and range control were "
                    "the weak points in his debut. The stoppage was criticised as early: Cageside said only a few hammerfists were "
                    "landing, and Nascimento protested right away (LowKick)."},
       ["Pressure forward, then shoots when the opponent opens up",
        "Heavy ground-and-pound from top",
        "18 of 20 wins by stoppage; 10 in R1",
        "Lost both of his five-round fights on points"],
       ["Only one UFC fight, and its stoppage was disputed",
        "Struggled to cut off a mobile opponent and bit on feints",
        "Record differs by source (20-3 in our data, 22-3 per LowKick)",
        "Short build-up: booked in place of Akbar Abdullaev"],
       ["Move and counter as he walks in; he has trouble cutting off the cage",
        "Defend the takedown when throwing combinations; he times shots off opponents' offense",
        "Threaten from bottom; his ground-and-pound leaves openings for submissions"],
       [n("2026-11-10", "Replaces Akbar Abdullaev against Jake Matthews; Wikipedia says the first pairing was the promotion's "
                        "mistake. Listed on the UFC.com prelims.", "wiki_event"),
        n("2026-06-27", "UFC debut in Baku: TKO of Jefferson Nascimento at 4:28 of R3 after takedowns and hammerfists; Cageside "
                        "called the stoppage early.", "cage_nascimento")],
       ["wiki_event", "ufc_event", "cage_nascimento", "lowkick_nascimento"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Manoel Sousa",
       "A Brazilian lightweight knockout artist nicknamed 'Manumito' (15-1; 2-0 UFC; age 29). He won his contract with a R3 "
       "KO on the 2025 Contender Series, knocked out Bolaji Oki in R3 of his March debut for a performance bonus, and outpointed "
       "LFA champion Richie Miranda (29-28 x3) in August. His reported Doha opponent Magomed Zaynukov said he never signed "
       "and is out for the year after surgery; as of November 10 no replacement has been named and the bout is not on the "
       "UFC.com card.",
       {"Striking": "Heavy hitter: about 0.8 knockdowns per 15 and nine KO/TKO wins. He finished Oki with a straight right at 4:12 "
                    "of R3 after earlier knockdowns (Yahoo/MMA Junkie). Against Miranda he chopped the lead leg with kicks, dropped "
                    "him with a body shot in R2, and landed heavy hooks (Cageside). Tends to overswing: an overcommitted punch gave "
                    "Miranda his R1 takedown.",
        "Grappling": "Mostly defensive. Three submission wins, all on the regional scene. He rarely shoots (0.5 per 15) and his "
                     "control share is low.",
        "Defense": "Takedown defense is the question. Cristian Perez held him down for about 7:46 in their Contender Series fight "
                   "and Oki about 3:23, per our data, and Miranda took his back in R1. He fought off submissions, got up, and "
                   "stuffed the rest of Miranda's shots (Cageside). Never stopped: his only loss was a 2024 Bellator decision to "
                   "Archie Colgan.",
        "Pace & cardio": "A late finisher at UFC level. His 12 stoppage wins came 5 in R1, 5 in R2 and 2 in R3, but both R3 KOs "
                         "are his two most recent finishes (Perez, Oki), and he won R2-R3 against Miranda after losing R1. He gets "
                         "stronger as fights go on rather than fading.",
        "Fight IQ": "Adjusts in-fight: switched to leg kicks after losing R1 to Miranda (Cageside). Can get loose and wild with "
                    "power shots early."},
       ["Power punching and hard leg kicks",
        "Finishes late: last two finishes were R3 knockouts",
        "Gets taken down early, survives and comes back",
        "Never stopped; one career loss, on points"],
       ["No confirmed opponent eleven days out",
        "Gives up takedowns and control time when he overcommits",
        "Little offensive grappling"],
       ["Wrestle early and stay on top; he has been held down in all three of his UFC/DWCS fights",
        "Win R1-R2 clearly and avoid trading late",
        "Make him miss and counter the overswing"],
       [n("2026-09-27", "Magomed Zaynukov, reported as his Doha opponent on Sept. 26, said he had not signed and needs surgery, and "
                        "would not fight again in 2026.", "sportscape_zaynukov"),
        n("2026-11-10", "Wikipedia lists the bout as Sousa vs. TBD and says it is unclear whether a replacement will be found; "
                        "UFC.com does not list Sousa on the card. No replacement has been named.", "wiki_event"),
        n("2026-08-08", "Beat Richie Miranda by unanimous decision (29-28 x3) after losing R1 on the mat.", "cage_miranda"),
        n("2026-03-15", "Earned a Performance of the Night bonus for his R3 KO of Bolaji Oki on debut.", "bjp_v114_bonus")],
       ["wiki_event", "ufc_event", "heavy_sousa", "sportscape_zaynukov", "cage_miranda", "yahoo_oki", "bjp_v114_bonus"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Nikolas Motta",
       "A Brazilian lightweight brawler (15-6, 1 NC; 3-3, 1 NC UFC; age 34) with real power and a habit of exchanging. He "
       "hasn't fought since June 2025, when Nazim Sadykhov stopped him in R2 of a Fight of the Night war that left him with "
       "a jaw broken badly enough to need titanium plates. Faces Road to UFC winner Dom Mar Fan in his return.",
       {"Striking": "Aggressive, all-in puncher: ten KO/TKO wins, eight in R1, and about 0.9 knockdowns per 15. He dropped Tom "
                    "Nolan with a right hand and finished him at 1:03 of R1 as an underdog (Cageside), and floored Maheshate twice "
                    "with left hooks (Cageside). Low accuracy (36%).",
        "Grappling": "Little: no submission wins in our data and almost no takedown offense. Went for a rear-naked choke against "
                     "Maheshate but couldn't finish (Cageside).",
        "Defense": "The big issue. He absorbs about 5.6 significant strikes a minute with 45% defense. Five of his six losses are "
                   "knockouts (three in R1, two in R2), including three in the UFC (Jim Miller R2, Manuel Torres R1, Sadykhov R2). "
                   "Maheshate dropped him with a knee in R1. Takedown defense is decent (about 68%), though Trey Ogden held him "
                   "down for about 4:28 before their no contest.",
        "Pace & cardio": "Front-loaded. Of ten stoppage wins, eight came in R1, one in R2, one in R3. He rushed Sadykhov in R1 and "
                         "may have punched himself out (Cageside); he looked tired late against Maheshate but still won R3. Five "
                         "decision wins, one a four-round fight. Stoppage losses: three in R1, three in R2 (two KOs, one 2013 sub).",
        "Fight IQ": "Willing to brawl, which brings wins and losses. Opponents who weather the first burst tend to catch him."},
       ["Fast starter: eight of ten stoppage wins in R1",
        "Throws heavy hooks and right hands in exchanges",
        "Hittable; five KO losses",
        "Fades after an all-out first round"],
       ["17 months out of action after a broken jaw that needed titanium plates",
        "Age 34 and chin wear",
        "Faces a grappler; Motta has little ground game"],
       ["Survive his opening burst, then make him work in R2-R3",
        "Wrestle and control; he offers little off his back",
        "Body work: Sadykhov broke him down with body shots"],
       [n("2026-10-30", "Booked against Dom Mar Fan at UFC Qatar; both are coming off losses. Not yet on the UFC.com event page.",
          "cage_qatar_two"),
        n("2025-07-02", "Said his jaw was fractured in the Sadykhov fight and fixed with titanium plates.", "si_motta_jaw"),
        n("2025-06-21", "Lost to Nazim Sadykhov by R2 TKO (4:17) after a heavy right hand.", "cage_sadykhov")],
       ["cage_qatar_two", "wiki_event", "cage_sadykhov", "si_motta_jaw", "cage_nolan_ko", "cage_maheshate"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Dom Mar Fan",
       "An Australian lightweight (9-3; 1-1 UFC; age 27; about 183 cm) who won the Road to UFC season 4 lightweight tournament, "
       "beating Sang Wook Kim 30-27 x3 at UFC 325. He was then heel-hooked by Kody Steele in R1 in May. Sherdog calls his "
       "grappling-based style 'funky and aggressive'.",
       {"Striking": "Secondary but usable: his jab was his best weapon in R2 against Kim, he used elbows in R1, and he fought "
                    "on the outside in R3 (Cageside). One KO/TKO win. Low knockdown rate (0.07 per 15). Lands about 4.0 a minute "
                    "at 50% and absorbs 2.7.",
        "Grappling": "His base: wrestling and scrambles. He reversed Kim's takedowns and back take twice, and his best round "
                     "came from a reversal into a top position against the cage (Cageside). In the Road to UFC rounds he controlled "
                     "Yuji Ephoevi-Ga for about 8 minutes and Jae Hyun Park for about 10, per our data. Three submission wins.",
        "Defense": "All three losses are submissions: twice to Quillan Salkilld on the regionals (both R2) and a R1 leg lock to "
                   "Kody Steele (LowKick lists a heel hook; a UFC post called it a kneebar). He let Kim back him onto the fence in "
                   "R3 (Cageside). Never knocked out. Sherdog's Tom Feely said he 'reads as somewhat unathletic'.",
        "Pace & cardio": "A grinder who goes the distance: five of his nine wins are decisions, including his last three wins. His "
                         "four finishes came in R1 (two subs) and R2 (one sub, one TKO). Kim tired in R2 while Mar Fan kept going "
                         "(Cageside). Submission losses: one in R1, two in R2.",
        "Fight IQ": "Patient and positional; wins by staying busy in scrambles. Can be drawn into leg-lock exchanges."},
       ["Wrestling, reversals and top control",
        "Goes to decision: his last three wins all went 15 minutes",
        "All three losses by submission",
        "Uses the jab on the outside when the wrestling stalls"],
       ["Leg locks and submission defense",
        "Athleticism against quicker opponents (Sherdog)",
        "Coming off a R1 submission loss"],
       ["Attack submissions in scrambles, especially legs",
        "Out-athlete him early and keep him off the fence",
        "Strike in open space; he has little power"],
       [n("2026-10-30", "Booked against Nikolas Motta at UFC Qatar; not yet on the UFC.com event page.", "cage_qatar_two"),
        n("2026-05-02", "Submitted by Kody Steele at 3:56 of R1 at UFC Perth.", "lowkick_perth"),
        n("2026-01-31", "Won the Road to UFC lightweight final over Sang Wook Kim, 30-27 x3.", "cage_kim")],
       ["cage_qatar_two", "wiki_event", "sherdog_325_prev", "cage_kim", "lowkick_perth"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Diyar Nurgozhay",
       "A Kazakh light heavyweight (12-2; 2-2 UFC; age 30) from the 2024 Contender Series. He entered the UFC 10-0, was "
       "submitted in his first two UFC fights (after missing weight in his debut), then rebounded with a decision over Rafael "
       "Tobias in March and a R1 TKO of Bruno Lopes at the buzzer in August.",
       {"Striking": "The strength. About 4.7 significant strikes a minute at 57%, and 0.9 knockdowns per 15. Against Tobias, teeps "
                    "and leg kicks kept him at range and his left hand landed repeatedly; Cageside called his counter timing sharp. "
                    "Knocked Lopes down several times before stopping him at 4:59 of R1 (Yahoo/MMA Junkie).",
        "Grappling": "Two submission wins, both early in his regional career. Wrestles a little (1.3 takedowns per 15) and has "
                     "reversed bottom position, as he did against Tobias in R2 (Cageside).",
        "Defense": "Both losses came after he was dropped and then submitted: Brendson Ribeiro hit him with a straight right in "
                   "R1 and kimura'd him in R2, and Uran Satybaldiev dropped him and finished an Ezekiel choke in R1 (Cageside). "
                   "Tobias took him down, mounted him, and had a Suloev stretch at the horn. Takedown defense around 72%, but "
                   "the bottom game is a clear weak spot.",
        "Pace & cardio": "Fast finisher. Of nine stoppage wins, eight came in R1 and one in R2. Three decision wins, one over five "
                         "rounds (Eagle FC 2022). Against Tobias both men tired in R2 and he had to survive a late submission. Both "
                         "losses were early (R1 and R2).",
        "Fight IQ": "Has calmed down since his early UFC losses; said 'we figured out a way to move forward' (Sherdog). Grabbed the "
                    "fence against Tobias without a warning (Cageside)."},
       ["Range kickboxing: teeps, leg kicks, left hand",
        "R1 finisher: eight of nine stoppages in R1",
        "Gets dropped, then submitted (both losses)",
        "Weak once on his back"],
       ["Submission defense off his back",
        "Missed weight by 4.5 lb in his debut (Cageside)",
        "Faces a debutant whose fights almost all end in R1"],
       ["Take him down and attack submissions",
        "Crowd him so he can't use teeps and range",
        "Look for a knockdown to start a scramble"],
       [n("2026-10-15", "Booked against Contender Series winner Alik Lorenz for UFC Qatar, per MMA Junkie's sources.",
          "yahoo_nur_lorenz"),
        n("2026-08-08", "TKO of Bruno Lopes at 4:59 of R1 after several knockdowns.", "yahoo_lopes"),
        n("2026-03-08", "Said many Kazakh fans gave up on him after his first two UFC losses.", "sherdog_nur_fans")],
       ["yahoo_nur_lorenz", "wiki_event", "yahoo_lopes", "cage_tobias", "sherdog_nur_fans", "cage_satybaldiev", "cage_ribeiro"],
       "moderate")

# ---------------------------------------------------------------------------------------------------------------
report("Alik Lorenz",
       "A light heavyweight prospect (8-2; UFC debut; about 6-foot-2 with a 77.5-inch reach) who won a contract on his second "
       "try on the Contender Series, knocking out Mahamed Aly at 2:23 of R1 in August. Nearly every fight he has had ended in "
       "R1, in either direction. Thin footage-based scouting available.",
       {"Striking": "Power puncher: seven of eight wins are R1 KO/TKOs. A big right hand dropped Aly before hammerfists ended it, "
                    "and he stopped Gabriel Thimoteo in LFA in under 30 seconds with a right hook and ground-and-pound (Cageside).",
        "Grappling": "One submission win (Ryan Parker, R3, LFA 2024). Little detail available on his wrestling.",
        "Defense": "Both losses are fast knockouts: Darion Abbey at 0:33 of R1 (2021) and Abdul-Rakhman Yakhyaev at 0:30 of R1 "
                   "on the 2025 Contender Series, where he landed 1 significant strike to 16 (our data). Cageside's write-up "
                   "suggests he is vulnerable to fast, high-volume attackers.",
        "Pace & cardio": "Largely unknown. Nine of his ten fights ended in R1; the exception was the R3 submission of Parker at 4:46. "
                         "He has never gone to a decision.",
        "Fight IQ": "Finish-minded: said before the Aly fight it would 'definitely' end in a finish and he wouldn't let it go to "
                    "the judges (Cageside)."},
       ["R1 knockout puncher: seven R1 KO/TKOs",
        "Never been to a decision",
        "Both losses were R1 knockouts inside 35 seconds"],
       ["Untested past R1; cardio unknown",
        "Defense against a fast, accurate starter",
        "UFC debut"],
       ["Be careful early, test his chin and pace, and take him into R2-R3",
        "Wrestle him; little is known about his ground defense",
        "Lead with volume rather than trading single power shots"],
       [n("2026-10-15", "Booked to debut against Diyar Nurgozhay at UFC Qatar.", "yahoo_nur_lorenz"),
        n("2026-08-18", "Won a UFC contract with a R1 KO of Mahamed Aly on the Contender Series.", "cage_dwcs_w2")],
       ["yahoo_nur_lorenz", "cage_lorenz_redemption", "cage_lorenz_int", "cage_dwcs_w2", "wiki_event"],
       "thin")

# ---------------------------------------------------------------------------------------------------------------
report("Alateng Heili",
       "A Chinese bantamweight from Inner Mongolia ('The Mongolian Knight', also listed as Heili Alateng or Alatengheili; "
       "18-10-2; 6-3-1 UFC; age 34) with a freestyle wrestling base. He replaced the injured Adrian Yanez against unbeaten "
       "prospect Juan Diaz at UFC 334. The booking was first reported on November 6, eight days before the fight; he will be fighting seven weeks "
       "after his split-decision win over John Castaneda.",
       {"Striking": "Pressure striker who marches forward with a jab and heavy right hands and goes to the body (Cageside, on "
                    "Castaneda). About 3.8 significant strikes landed and absorbed per minute. Five KO/TKO wins, the most recent a "
                    "47-second TKO of Kevin Croom in 2022.",
        "Grappling": "Wrestling is his base (Wikipedia). He mixes body shots with level changes. Against Castaneda he took him down "
                     "in R3, kneed his thighs from top and stayed on him through escape attempts (Cageside). About 1.4 takedowns "
                     "per 15 at 36%. Three submission wins, none since 2015.",
        "Defense": "Durable: he hasn't been stopped since Kai Asakura knocked him out in 29 seconds in 2017. All three UFC losses "
                   "were decisions (Casey Kenney, Chris Gutierrez, Da'Mon Blackshear). Takedown defense around 62%. He lost a point "
                   "for repeatedly grabbing the fence against Gustavo Lopez (Wikipedia).",
        "Pace & cardio": "A decision fighter: ten of his 18 wins and six of his ten losses went to the judges, and nine of his ten "
                         "UFC fights went the distance. Stoppage wins: four in R1, four in R2; none in R3. Stoppage losses: two in "
                         "R1, two in R2, all before 2018. He was still pressing at the end of R2 and wrestling hard in R3 against "
                         "Castaneda, so his late-round output holds up.",
        "Fight IQ": "Experienced and steady. Has alternated wins and losses over his last four fights (2-2), and his last two "
                    "wins came on split decisions."},
       ["Forward pressure with jab, right hand and body work",
        "Level changes and late takedowns to steal close rounds",
        "Goes the distance: 9 of 10 UFC fights",
        "Not stopped since 2017"],
       ["Eight days' notice against a younger, unbeaten opponent",
        "Close fights: two of his last three results were split decisions or losses",
        "Juan Diaz is a strong wrestler (about 3.7 takedowns per 15, per our data) who could take Heili's takedown game away",
        "Sources disagree on his recent form: MiddleEasy says three straight wins, but our data and MMA Junkie have him losing "
        "to Blackshear in 2025"],
       ["Win the wrestling exchanges and keep him off top position",
        "Use range and kicks rather than standing in his pocket",
        "Push the pace early; he is on short notice"],
       [n("2026-11-06", "Reported as Juan Diaz's new opponent at UFC 334, replacing Adrian Yanez (injured, withdrew in mid-October). "
                        "Heavy reported it first and both fighters confirmed on social media, per MMA Junkie. That is eight days "
                        "before the Nov. 14 card.", "yahoo_heili"),
        n("2026-11-07", "Heavy called him a late-notice opponent with plenty of UFC experience and expects Diaz to be the favourite.",
          "heavy_heili"),
        n("2026-09-26", "Beat John Castaneda by split decision (29-28, 28-29, 29-28) after a R3 takedown and top control.",
          "cage_castaneda")],
       ["yahoo_heili", "heavy_heili", "middleeasy_heili", "wiki_334", "wiki_heili", "cage_castaneda"],
       "moderate", event=EVENT_334)


out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
