"""Scouting reports for UFC Fight Night: Allen vs. Duncan (UFC Vegas 122, 2026-10-10), first pass written 2026-09-30.

Fight-week previews aren't out yet: these draw on recent-fight coverage, booking news and our verified
records. The Tuesday/Friday runs should refresh them with the previews and fight-week news.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = json.loads((ROOT / "sources_ufcvegas122.json").read_text())
UPDATED = "2026-09-30T23:40:00+00:00"
EVENT = "UFC Fight Night: Allen vs. Duncan"


def slug(name):
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


R = {}


def report(name, summary, how, patterns, concerns, keys, news, sources, depth):
    R[name] = {"name": name, "updated": UPDATED, "event": EVENT, "summary": summary, "how_they_fight": how,
               "patterns": patterns, "concerns": concerns, "keys_to_beat": keys, "news": news,
               "sources": [SRC[k] for k in sources], "depth": depth}


report("Brendan Allen",
       "The No. 4 middleweight and a complete grappler: strong wrestling, excellent jiu-jitsu and a serviceable kickboxing game, "
       "on a three-fight run (Vettori, de Ridder, Edmen Shahbazyan). Wins by making opponents carry his weight and breaking them late.",
       {"Striking": "Varied and functional kickboxing (about 3.8 significant strikes a minute) used mostly to get to the clinch and the legs; "
                    "his decision losses to Nassourdine Imavov and Anthony Hernandez came when he couldn't impose grappling.",
        "Grappling": "The weapon. Against Reinier de Ridder he survived an early mount and back take, reversed him in rounds two and three, then "
                     "rode him for over 11 minutes of control with heavy ground-and-pound until de Ridder's corner stopped it after round four.",
        "Defense": "Takedown defense around 60% and he can be put on his back, but he's comfortable there and scrambles well.",
        "Pace & cardio": "Built for five rounds: the de Ridder fight was won by draining the other man's tank.",
        "Fight IQ": "Patient; picks the phase where he's strongest and stays there."},
       ["Clinch entries off strikes", "Top control with ground-and-pound", "Wins late rounds"],
       ["Out-struck at range by technical kickboxers (Imavov, Hernandez)"],
       ["Stay on the feet and at range", "Make him strike first; punish entries"],
       [{"date": "2026-09-01", "text": "Headlines UFC Vegas 122 against Christian Leroy Duncan, five rounds at the Meta Apex.", "source": SRC["cage_main"]["url"]}],
       ["sherdog_allen", "espn_allen", "cage_main"], "good")

report("Christian Leroy Duncan",
       "An awkward, long, switch-stance British striker (the former Cage Warriors champion) on a five-fight streak, latest a clear win over "
       "Jared Cannonier. Dangerous with knees, kicks and spinning strikes; his grappling defense is the question.",
       {"Striking": "About 4.2 significant strikes a minute while absorbing only 1.5. Kicks early, glides at angles, uses front kicks, jumping "
                    "and standing knees and spinning attacks; staggered Cannonier with a spinning elbow and dropped him with a kick.",
        "Grappling": "Little offensive grappling. Cannonier took him down and controlled him for about six minutes, and walked him to the fence "
                     "in round three.",
        "Defense": "Very hard to hit cleanly at range; the fence and clinch are where he's vulnerable.",
        "Pace & cardio": "Has never fought five rounds in the UFC.",
        "Fight IQ": "Creative, but can over-commit when he smells a finish (Cannonier landed back when he got too aggressive)."},
       ["Kicks and knees at range", "Spinning attacks", "Swarms a hurt opponent"],
       ["Takedown defense against an elite grappler", "First five-round fight"],
       ["Take him down and hold him there", "Pressure him to the fence and clinch"],
       [{"date": "2026-07-18", "text": "Beat Jared Cannonier by unanimous decision (30-27, 30-27, 29-28) for his fifth straight win.", "source": SRC["cage_cld"]["url"]}],
       ["cage_cld", "cage_main", "sherdog_main"], "good")

report("Jai Herbert",
       "A tall, rangy English striker and former Cage Warriors lightweight champion, now 38; ten knockout wins. Back in the win column with a "
       "first-round KO of Mandel Nallo in April.",
       {"Striking": "Long, straight punching from range; reach about 196 cm, big for lightweight.",
        "Grappling": "Defends takedowns well (about 78%) but offers little offense on the mat.",
        "Defense": "Decision losses when out-worked (Chris Padilla, Fares Ziam).",
        "Pace & cardio": "Steady three-round pace.",
        "Fight IQ": "Experienced; must keep a wrestler at range."},
       ["Long jab and straight right", "Power at range"],
       ["Age (38)", "Being out-worked or wrestled"],
       ["Close the distance and wrestle"],
       [], ["yahoo_camilo", "ufc_event"], "thin")

report("Matheus Camilo",
       "A 25-year-old Nova Uniao wrestler: 11-3, about three takedowns per 15 minutes in the UFC. Knocked out Nazim Sadykhov in 91 seconds in "
       "June after out-working Viacheslav Borshchev.",
       {"Striking": "Low UFC volume (about 1.7 significant strikes a minute) but showed power against Sadykhov.",
        "Grappling": "Wrestling-heavy: chains takedowns and controls; was submitted by Gabriel Green in 2025.",
        "Defense": "Hard to hit (about 70% striking defense).",
        "Pace & cardio": "Fine for three rounds.",
        "Fight IQ": "Says he respects Herbert's experience (Yahoo Sports)."},
       ["Level changes and control"],
       ["Submission defense (the Green loss)", "Long striker's range"],
       ["Keep it standing and long"],
       [], ["yahoo_camilo", "ufc_event"], "thin")

report("Lupita Godinez",
       "A busy Mexican strawweight who blends volume striking with wrestling (about 2.5 takedowns per 15 minutes); submitted by Tatiana Suarez in April, "
       "with decision losses to top grapplers Mackenzie Dern and Virna Jandiroba before that.",
       {"Striking": "Around 4 significant strikes a minute each way; forward pressure and combinations.",
        "Grappling": "Uses takedowns to score, but loses to elite grapplers.",
        "Defense": "Takedown defense about 71%.",
        "Pace & cardio": "High pace, fights often.",
        "Fight IQ": "Workrate first."},
       ["Volume and takedown mix"],
       ["Against top grapplers", "Absorbs a lot"],
       ["Out-grapple her or counter her pressure"],
       [], ["sucka_godinez", "ufc_event"], "thin")

report("Ketlen Souza",
       "A Brazilian strawweight on a two-fight win streak (a first-round KO of Ariane Carnelossi in June); 4-3 in the UFC, with two split-decision losses.",
       {"Striking": "Accurate (about 53%) and hits hard; three first-round finishes in her last five.",
        "Grappling": "Submitted Yazmin Jauregui in round one (2024).",
        "Defense": "Absorbs about 3.9 a minute; defense is middling.",
        "Pace & cardio": "Her close fights go to split decisions.",
        "Fight IQ": "Opportunistic finisher."},
       ["Early finishing threat"],
       ["Close rounds on the cards"],
       ["Take her down and win rounds"],
       [], ["sucka_godinez", "ufc_event"], "thin")

report("Andre Fili",
       "A long-serving Team Alpha Male featherweight (27 UFC fights), 36, who has lost two straight, including a TKO to Vinicius Oliveira in June. "
       "Many of his fights are close split decisions.",
       {"Striking": "Long, busy kickboxer; absorbs more than he lands lately (about 4.6 a minute).",
        "Grappling": "Good takedown defense (about 81%).",
        "Defense": "Durability showing wear.",
        "Pace & cardio": "Three solid rounds.",
        "Fight IQ": "Veteran."},
       ["Volume at range"], ["Age and recent stoppage"], ["Pressure and heavy shots"],
       [], ["bjp_fili", "ufc_event"], "thin")

report("Kai Kamaka III",
       "A Hawaiian featherweight back in the UFC in 2026: 1-1 since returning, most recently knocked out by Luke Riley in July. Accurate, high-volume "
       "striker (about 59% accuracy) who also absorbs a lot.",
       {"Striking": "About 5.3 significant strikes a minute at high accuracy.",
        "Grappling": "Moderate wrestling.",
        "Defense": "Absorbs about 5.8 a minute.",
        "Pace & cardio": "Has gone five rounds (split loss to Diego Brandao, 2025).",
        "Fight IQ": "Volume over power."},
       ["Accurate volume"], ["Defensive leaks; coming off a KO loss"], ["Counter his volume"],
       [], ["bjp_fili", "ufc_event"], "thin")

report("Julius Walker",
       "A 27-year-old light heavyweight on two straight knockout losses (Dustin Jacoby, Abdul-Rakhman Yakhyaev), with wrestling (about 3.3 takedowns "
       "per 15 minutes) as his best tool.",
       {"Striking": "Hittable; stopped twice in 2026.",
        "Grappling": "Wrestles and controls (44% control share).",
        "Defense": "Poor striking defense (about 49%).",
        "Pace & cardio": "Unremarkable.",
        "Fight IQ": "Needs to wrestle."},
       ["Takedowns and control"], ["Chin after two KO losses"], ["Strike with him"],
       [], ["si_gm", "ufc_event"], "thin")

report("Gerald Meerschaert",
       "A 39-year-old submission specialist (37 wins) moving up to light heavyweight after five straight losses, two by stoppage. Still dangerous off his back "
       "and in scrambles; the athleticism has faded.",
       {"Striking": "Serviceable, not a strength.",
        "Grappling": "Opportunistic submissions (about 1.2 attempts per 15 minutes); weak takedown defense (about 49%).",
        "Defense": "Stopped by Oleksiejczuk (KO) and Daukaus (sub) in 2025.",
        "Pace & cardio": "Veteran pace.",
        "Fight IQ": "Crafty; hunting a submission."},
       ["Submission hunting in scrambles"], ["Age, five-fight skid, moving up in weight"], ["Avoid scrambles; strike"],
       [{"date": "2026-09", "text": "Moves up to light heavyweight after five straight losses.", "source": SRC["si_gm"]["url"]}],
       ["si_gm", "ufc_event"], "thin")

report("Malcolm Wellmaker",
       "A bantamweight knockout puncher (three straight first-round KOs to start his UFC run), now on two straight losses and newly at American Top Team.",
       {"Striking": "One-punch power; early finisher.",
        "Grappling": "Takedown defense about 50%; submitted by Juan Diaz in May.",
        "Defense": "Vulnerable when taken down.",
        "Pace & cardio": "Lost a decision to Ethyn Ewing when the fight went long.",
        "Fight IQ": "Camp change after the losses."},
       ["Early power"], ["Grappling defense", "Two-fight skid"], ["Take him down"],
       [{"date": "2026-09", "text": "Switched camps to American Top Team after two losses.", "source": SRC["heavy_wellmaker"]["url"]}],
       ["heavy_wellmaker", "ufc_event"], "thin")

report("Otari Tanzilovi",
       "A Georgian featherweight-bantamweight wrestler (about 3.4 takedowns per 15 minutes) who lost his UFC debut to Shane Collins on the cards.",
       {"Striking": "Accurate (about 62%) in a small sample.",
        "Grappling": "Wrestling-first.",
        "Defense": "Takedown defense about 76%.",
        "Pace & cardio": "Three-round fighter.",
        "Fight IQ": "Unknown at UFC level."},
       ["Takedowns"], ["Small UFC sample"], ["Stuff takedowns and strike"],
       [], ["heavy_wellmaker", "ufc_event"], "thin")

report("Francisco Prado",
       "A 24-year-old ATT prospect on four straight losses at welterweight, all decisions, returning to lightweight; hasn't won since a first-round KO "
       "of Ottman Azaitar in 2023.",
       {"Striking": "Competitive volume; lost close fights.",
        "Grappling": "Weak takedown defense (about 44%).",
        "Defense": "Out-pointed rather than stopped.",
        "Pace & cardio": "Goes three rounds.",
        "Fight IQ": "Young; drop to 155 may help."},
       ["Volume"], ["Four-fight skid", "Takedown defense"], ["Wrestle him"],
       [{"date": "2026-09-13", "text": "Returns to lightweight after three defeats at welterweight.", "source": SRC["fightomic_week"]["url"]}],
       ["fightomic_week", "ufc_event"], "thin")

report("Ismael Bonfim",
       "A Brazilian lightweight striker on three straight losses, two by knockout and the latest a brabo choke from Axel Sola.",
       {"Striking": "Accurate (about 54%), powerful kickboxer.",
        "Grappling": "Submitted twice (St. Denis, Sola).",
        "Defense": "Stopped in three of his last four losses.",
        "Pace & cardio": "Fades under pressure.",
        "Fight IQ": "Needs a win to stay."},
       ["Kickboxing at range"], ["Durability and submission defense"], ["Pressure and grapple"],
       [], ["fightomic_week", "ufc_event"], "thin")

report("Niko Price",
       "A 37-year-old action fighter returning from a brief retirement for a last dance after four straight losses (Chiesa by submission, "
       "Veretennikov by KO); the knee injury and stoppage losses have taken their toll.",
       {"Striking": "Wild, high-volume power (about 5.2 a minute), famous for strange finishes.",
        "Grappling": "Scrambles; submitted twice in the recent skid.",
        "Defense": "Absorbs about 5 a minute; stopped repeatedly lately.",
        "Pace & cardio": "Brawling pace.",
        "Fight IQ": "Chaos by design."},
       ["Brawls and wild exchanges"], ["Age, knee, four losses"], ["Stay composed and pick him apart"],
       [{"date": "2026-09", "text": "Unretires for one final fight after his UFC Seattle exit was overshadowed.", "source": SRC["mania_price"]["url"]}],
       ["mania_price", "ufc_event"], "moderate")

report("Leon Shahbazyan",
       "Edmen Shahbazyan's younger brother, a submission-heavy regional fighter (four straight first-round submissions) knocked out in 23 seconds by "
       "Levan Chokheli in his UFC debut.",
       {"Striking": "Barely tested (debut lasted 23 seconds).",
        "Grappling": "Finishes by submission.",
        "Defense": "Chin question after the debut.",
        "Pace & cardio": "Unknown.",
        "Fight IQ": "Unknown."},
       ["Early submissions"], ["Durability", "Tiny UFC sample"], ["Strike early"],
       [], ["mania_price", "ufc_event"], "thin")

report("Felipe Franco",
       "A 26-year-old Brazilian light heavyweight wrestler (about three takedowns per 15 minutes, 87% takedown defense), 11-2 with a TKO of Levi Rodrigues in July.",
       {"Striking": "Accurate but low volume.",
        "Grappling": "Takedowns and control; submitted by Freddy Vidal in 2025.",
        "Defense": "Solid.",
        "Pace & cardio": "Went three rounds with Mario Pinto.",
        "Fight IQ": "Wrestle-first."},
       ["Takedowns"], ["Submission defense"], ["Stuff shots and strike"],
       [], ["ufc_event"], "thin")

report("Brendson Ribeiro",
       "A long (206-cm reach) Brazilian light heavyweight on four straight losses, three by stoppage; poor takedown defense (about 45%).",
       {"Striking": "Long-range striker, rarely wrestles.",
        "Grappling": "Submitted by Yakhyaev; weak defensive wrestling.",
        "Defense": "Stopped three times in a row.",
        "Pace & cardio": "Fades.",
        "Fight IQ": "Needs range."},
       ["Length"], ["Four-fight skid", "Takedown defense"], ["Take him down"],
       [], ["ufc_event"], "thin")

report("Allen Frye",
       "A heavyweight with four first- or second-round KOs before a decision loss to Guilherme Pat in his UFC debut (December 2025); back as a "
       "'heavyweight sophomore'.",
       {"Striking": "Power; finished his regional run early.",
        "Grappling": "Unknown.",
        "Defense": "Low striking defense in a small sample.",
        "Pace & cardio": "Went three rounds with Pat.",
        "Fight IQ": "Unknown."},
       ["Early power"], ["Small UFC sample"], ["Survive early"],
       [], ["yahoo_hw", "ufc_event"], "thin")

report("RJ Harris",
       "A heavyweight in his second UFC fight; not yet in our verified data. Treat any prediction for this bout as uninformed.",
       {"Striking": "Unknown.", "Grappling": "Unknown.", "Defense": "Unknown.", "Pace & cardio": "Unknown.", "Fight IQ": "Unknown."},
       [], ["No verified record in our data"], [],
       [], ["yahoo_hw", "ufc_event"], "thin")

report("Alice Pereira",
       "A 21-year-old Brazilian bantamweight (7-1) with two KO wins in her last four, including Hailey Cowan in April; lost a split decision to "
       "Montserrat Rendon.",
       {"Striking": "Power over accuracy (about 31%).", "Grappling": "Defends takedowns (about 73%).",
        "Defense": "Solid (61%).", "Pace & cardio": "Has gone five rounds regionally.", "Fight IQ": "Young and improving."},
       ["Power punches"], ["Accuracy"], ["Out-work her"],
       [], ["ufc_event"], "thin")

report("Darya Zheleznyakova",
       "A Russian bantamweight (10-3) whose UFC run has been up and down: submitted by Ailin Perez, a decision loss to Melissa Croden in April.",
       {"Striking": "Workmanlike.", "Grappling": "Can wrestle.", "Defense": "Submitted once in the UFC.",
        "Pace & cardio": "Three-round decisions.", "Fight IQ": "Steady."},
       ["Grinding decisions"], ["Two losses in three"], ["Finish her early"],
       [], ["ufc_event"], "thin")

report("Ernesta Kareckaite",
       "A Lithuanian flyweight brawler: very high volume (about 6.4 strikes a minute) and absorbs almost as much; most fights go to split decisions.",
       {"Striking": "Volume puncher.", "Grappling": "Good takedown defense (about 83%).",
        "Defense": "Takes a lot back.", "Pace & cardio": "Relentless.", "Fight IQ": "Brawl-first."},
       ["Volume brawling"], ["Absorbs a lot", "Close decisions"], ["Counter and wrestle"],
       [], ["heavy_gatto", "ufc_event"], "thin")

report("Melissa Gatto",
       "A Brazilian flyweight with a grappling base (about 1.5 takedowns per 15 minutes, 29% control), back for her second 2026 fight after a split "
       "decision loss to Dione Barbosa; two late KOs in her UFC wins.",
       {"Striking": "Can finish late (two round-three KOs).", "Grappling": "Control-heavy.",
        "Defense": "Solid.", "Pace & cardio": "Strong late.", "Fight IQ": "Measured."},
       ["Late finishes", "Control"], ["Inactivity (one fight 2024-25)"], ["Out-work her early"],
       [], ["heavy_gatto", "ufc_event"], "thin")

out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
