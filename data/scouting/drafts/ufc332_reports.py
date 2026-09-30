"""Scouting reports for the UFC 332 card (written 2026-09-30 from the sources in sources_ufc332.json).

Run: python data/scouting/drafts/ufc332_reports.py  -> data/scouting/reports/<slug>.json
Facts (records, recent results, methods) are checked against our verified fight data; claims only
one outlet makes are attributed to it.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = json.loads((ROOT / "sources_ufc332.json").read_text())
UPDATED = "2026-09-30T23:00:00+00:00"


def slug(name):
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


R = {}


def report(name, summary, how, patterns, concerns, keys, news, sources, depth):
    R[name] = {
        "name": name, "updated": UPDATED, "event": "UFC 332", "summary": summary,
        "how_they_fight": how, "patterns": patterns, "concerns": concerns, "keys_to_beat": keys,
        "news": news, "sources": [SRC[k] for k in sources], "depth": depth,
    }


report("Natalia Silva",
       "A movement-first striker who wins by never being where the return fire lands: layered kicks, stance switches and angles, "
       "with grappling held in reserve. Eight UFC wins, 14 straight overall, the last three over former champions, all by decision.",
       {"Striking": "Taekwondo base. Fights at kicking range and punishes forward movement: circles off, counters, and mixes kicks to every level "
                    "with short hand combinations. Changes stance mid-exchange, so opponents struggle to read her lead. The coach's read: she "
                    "'layers' offense, mixing kicks, stance changes and grappling so one feeds the next.",
        "Grappling": "Seven career submission wins and a takedown threat she uses sparingly: enough to make strikers respect the level change. "
                     "Stops 90% of takedowns in the UFC.",
        "Defense": "Among the hardest women in the division to hit cleanly: absorbs about 2.1 significant strikes a minute. Distance and "
                   "footwork, not a high guard, are the defense.",
        "Pace & cardio": "Has won rounds 3 in all her recent decisions and doesn't fade; can reset against the cage or on the mat to breathe. "
                         "Never been past three rounds, though: this is her first five-rounder, at altitude.",
        "Fight IQ": "Patient, efficient decision-maker: takes what's offered and rarely over-commits. Wins rounds more than she hurts people "
                    "(the last five wins all went to the cards)."},
       ["Circles off the cage the moment her back foot touches it", "Leads with kicks to draw a reaction, counters the reply",
        "Mixes in a takedown attempt when a striker starts timing her"],
       ["First five-round fight, and at altitude", "Low finishing rate lately: close rounds can go either way against a busier striker",
        "Hasn't faced a volume puncher as accurate as Wang"],
       ["Cut off the cage and trap her against it (her exits are the whole defense)", "Throw long combinations: first shots miss, the third and fourth land",
        "Stay at boxing range, out of her kicks and out of her clinch"],
       [{"date": "2026-09-28", "text": "Fights Wang Cong for the flyweight title Valentina Shevchenko vacated through injury.", "source": SRC["bjp_wang"]["url"]}],
       ["coach", "ufc_preview", "bjp_wang"], "good")

report("Cong Wang",
       "A pressure boxer-kickboxer from a Sanda base, the most accurate striker in the division's history per UFC.com: busy, "
       "clean and composed, winning with volume rather than one-shot power.",
       {"Striking": "Sanda and pro kickboxing background. Sound boxing fundamentals at middle range; throws about 6.4 significant strikes a "
                    "minute. Pressure is the engine: she walks opponents down, cuts the cage and lands in combination rather than loading up.",
        "Grappling": "Willing to clinch and has shown top position, but the one loss on her record (2024) was a submission to Gabriella "
                     "Fernandes: the ground is the least-proven part of her game.",
        "Defense": "Stops about 85% of takedowns. Hard to hurt standing; her last four fights all went the distance.",
        "Pace & cardio": "Holds a high pace for three rounds; five rounds and a championship weight cut are unknowns. Per the coach's "
                         "breakdown, she missed weight earlier this year: the cut is a real question for a five-round fight.",
        "Fight IQ": "Composed; fights to a plan. Says she'll 'fight smart' and take a finish only if it's offered (BJPenn.com)."},
       ["Walks forward behind a jab and cuts the cage", "Scores in combinations of three or four", "Accurate counter when opponents lead into her"],
       ["Weight cut for a five-round title fight", "Submission defense (her only loss)", "Chasing an elusive opponent can leave her missing and reaching"],
       ["Keep changing range so she has to chase", "Kick at range and exit at angles; don't box with her",
        "Threaten takedowns to make her stand taller"],
       [{"date": "2026-09-28", "text": "Says Silva is 'the toughest I've ever faced' and that she'll finish her if given an opening; underdog for the vacant title.", "source": SRC["bjp_wang"]["url"]}],
       ["coach", "ufc_preview", "bjp_wang"], "good")

report("Deiveson Figueiredo",
       "A two-time flyweight champion now at bantamweight and 39, with 1-4 in his last five. The power and submission threat remain; "
       "the speed and durability to deliver them look like they're going.",
       {"Striking": "Heavy hands and a counter left hook built his flyweight run, but at 135 he's been out-landed by bigger, longer men "
                    "(about 2.6 significant strikes landed a minute against 3.2 absorbed).",
        "Grappling": "Leans more on grappling since moving up (UFC.com): chokes from front headlocks and scrambles are his best finishing "
                     "routes now.",
        "Defense & durability": "Stopped by Cory Sandhagen (a knee injury, 2025) and submitted by Song Yadong (May 2026). "
                                "Decision losses to Petr Yan and Umar Nurmagomedov were clear.",
        "Pace & cardio": "Starts fast; historically fades when fights go long, and he's older now.",
        "Fight IQ": "Experienced and dangerous early; lacks answers for length and volume."},
       ["Explodes early with power punches", "Hunts chokes when opponents duck in or shoot"],
       ["Age (39) and wear", "1-4 in his last five", "Size at bantamweight"],
       ["Stay long, jab and kick", "Don't shoot carelessly into his front headlock", "Push the pace into the second and third rounds"],
       [],
       ["ufc_preview", "sherdog_odds"], "moderate")

report("Payton Talbott",
       "A long, rangy, high-output striker from Reno with slick lines of attack; his one loss (Raoni Barcelos) came when he was "
       "wrestled and made to work. Coming off a clear win over Henry Cejudo.",
       {"Striking": "Tall for bantamweight with the length to keep opponents on the end of his punches. Lands about 5.9 significant strikes "
                    "a minute; flowing combinations and unorthodox angles, with finishing power (two first- and second-round KOs in 2024).",
        "Grappling": "Defensive grappling has improved since the Barcelos loss; he beat Cejudo, an Olympic champion wrestler, over three rounds.",
        "Defense": "Stops about 72% of takedowns. Can be hit while he's attacking.",
        "Pace & cardio": "Keeps a high pace for three rounds; ten-month layoff since December.",
        "Fight IQ": "Confident, creative; handles veteran pressure better than a year ago."},
       ["Works behind length and volume", "Punishes flat-footed opponents with combinations"],
       ["Layoff since December 2025", "Can be taken down by strong wrestlers"],
       ["Close distance and wrestle", "Make him carry weight", "Counter as he extends"],
       [{"date": "2026-09-29", "text": "A heavy betting favorite (around -575 to -650) over Figueiredo.", "source": SRC["sherdog_odds"]["url"]}],
       ["ufc_preview", "sherdog_odds"], "moderate")

report("King Green",
       "A 40-year-old Philly-shell counter boxer on the best run of his career (four straight, three finishes in 2026). Hands low, "
       "chin tucked, reads patterns, leads opponents into heavy counters, and wrestles when it's the smart play.",
       {"Striking": "One of the savviest boxers in the UFC (MMA Mania): pops the jab, draws the lead, counters hard. Defends with distance, "
                    "the shoulder roll and pattern recognition rather than a high guard, and talks constantly to bait exchanges.",
        "Grappling": "Still an excellent wrestler when he chooses to be; catches kicks and turns them into takedowns. Submitted Jeremy "
                     "Stephens in May.",
        "Defense": "Hard to hit cleanly; the risk is off-beat timing and same-side doubles that land while he's leaning.",
        "Pace & cardio": "This would be his fifth fight in under 12 months at 40: the wear is the concern, not the gas tank.",
        "Fight IQ": "Elite ring IQ; happy to win a fight ugly with takedowns."},
       ["Hands low, baiting exchanges", "Counter right hand/cross up the middle", "Catch-kick takedowns"],
       ["Age and a heavy 2026 schedule", "Off-beat timing and same-side kick/punch doubles can find him"],
       ["Break rhythm: chop a kick then explode into punches", "Double up on the same side to catch him leaning",
        "Don't lead predictably into his counters"],
       [],
       ["mania_green", "ufc_preview"], "good")

report("Esteban Ribovics",
       "A high-volume Argentine kickboxer with power in hands and shins and a granite chin; all-action, bonus-magnet fights. "
       "Two of his three UFC losses came through takedowns.",
       {"Striking": "About 6.1 significant strikes a minute. Builds combinations well, uses kicks to finish combinations and to set up "
                    "punches; off-beat timing (chop a kick, then punches) is his natural rhythm. Knocked out Edson Barboza in August.",
        "Grappling": "The weak side: submitted by Mateusz Gamrot in April; takedowns decided two of his three UFC losses.",
        "Defense": "Absorbs a lot (about 5.3 a minute) and trusts his chin to walk through it.",
        "Pace & cardio": "Keeps up a torrid pace for three rounds.",
        "Fight IQ": "Wants a firefight; less comfortable when an opponent refuses to engage on his terms."},
       ["Kick-punch combinations with off-beat timing", "Pressure and volume", "Walks through shots"],
       ["Takedown defense", "Hittable: aggression runs him onto counters"],
       ["Wrestle him, especially off caught kicks", "Counter up the middle as he comes in"],
       [],
       ["mania_green", "ufc_preview"], "good")

report("Roberto Soldic",
       "Former two-division KSW champion and a knockout artist (18 KO/TKO wins) making his UFC debut; power puncher with "
       "championship experience, coming off a first-round KO in February 2025.",
       {"Striking": "Heavy, compact power punching and aggressive finishing instincts; beat Mamed Khalidov by knockout in 2021.",
        "Grappling": "Can wrestle but prefers to strike; his ONE run (2022-23) included a KO loss to Zebaztian Kadestam and a no contest.",
        "Defense & durability": "Has been stopped (Kadestam, 2023); chin is good but not untouchable.",
        "Pace & cardio": "About 20 months out of the cage before this debut.",
        "Fight IQ": "Experienced in big fights; the unknown is his first UFC fight and its adrenaline."},
       ["Pressure and heavy combinations", "Looks for the finish early"],
       ["Long layoff", "Debut nerves in the Octagon", "Fighting a fast starter with his own power"],
       ["Beat him to the punch early", "Make it a technical, long fight"],
       [],
       ["ufc_preview", "soldic_debut"], "moderate")

report("Kalinn Williams",
       "'Khaos' Williams: a fast-starting power puncher whose UFC identity is heavy hands in the first minutes; KO'd Nikolay "
       "Veretennikov in May. His losses came to fighters who survived the start and grappled or outworked him.",
       {"Striking": "Fight-ending power in both hands; explosive early. Long reach for the division.",
        "Grappling": "Minimal offense (few takedowns); submitted by Gabriel Bonfim in 2025.",
        "Defense": "Absorbs nearly 5 significant strikes a minute: the output drops if he doesn't get the early finish.",
        "Pace & cardio": "Front-loaded: the danger window is round one.",
        "Fight IQ": "Wants the knockout; less effective when a fight becomes a grind."},
       ["Fast starts and heavy first-round power", "Counter right hand"],
       ["Grappling and submission defense", "Output in later rounds"],
       ["Survive the first round, then wrestle or outwork him"],
       [],
       ["ufc_preview", "soldic_debut"], "moderate")

report("Ateba Abega Gautier",
       "A 24-year-old, 6-foot-4 knockout puncher with an 81-inch reach: 5-0 in the UFC, four by knockout. The one test that went "
       "long, Andrey Pulyaev in January, was a grind he won on the cards.",
       {"Striking": "Big, powerful and increasingly composed; finishes with punches in combination once he's hurt someone.",
        "Grappling": "Hard to take down (stops about 82%); size makes him hard to hold.",
        "Defense": "The Pulyaev fight showed he can be frustrated at range by a durable, lanky opponent.",
        "Pace & cardio": "Unproven in hard three-round fights beyond Pulyaev.",
        "Fight IQ": "Still developing; a UFC.com feature calls him 'a changed man' two years on, more patient than in his early career."},
       ["Explosive power punching", "Uses size to push opponents back"],
       ["Experience against seasoned veterans", "Can be made to work at range"],
       ["Wrestle him and make him carry weight", "Stay durable and drag him into round three"],
       [],
       ["ufc_preview", "gautier_feature"], "moderate")

report("Roman Kopylov",
       "A Russian southpaw pressure striker and a classic measuring stick: too skilled for most newcomers, but beaten on points by "
       "the better middleweights (Paulo Costa, Gregory Rodrigues). Stops 94% of takedowns.",
       {"Striking": "Aggressive southpaw with kicks and volume (about 4.3 significant strikes a minute); finished Chris Curtis in 2025.",
        "Grappling": "Solid wrestling defense and a willingness to wrestle himself: previewers see takedowns as his best route against "
                     "Gautier.",
        "Defense": "Absorbs about as much as he lands; beaten over three rounds by bigger, better strikers.",
        "Pace & cardio": "Steady for three rounds.",
        "Fight IQ": "Experienced; knows how to make fights ugly."},
       ["Southpaw kicks and pressure", "Mixes in wrestling"],
       ["Size and power disadvantage here", "Plateaued against top-15 opposition"],
       ["Out-size and out-power him", "Keep him on the outside"],
       [],
       ["ufc_preview"], "moderate")

report("Imanol Rodriguez",
       "'Himan': an elite flyweight athlete with power and a strong striking-plus-grappling mix; 7-0 and a TUF semifinalist who "
       "went to a coin-flip decision with eventual winner Joseph Morales.",
       {"Striking": "Horsepower is the calling card: aggressive, powerful for 125, can be wild. Got caught by sharp shots from Kevin "
                    "Borjas in his UFC debut but regrouped and finished him in round two.",
        "Grappling": "Uses takedowns and scrambles as a second weapon.",
        "Defense": "Can be hit when he over-commits to pressure.",
        "Pace & cardio": "Explosive; most wins came early.",
        "Fight IQ": "Showed composure recovering against Borjas."},
       ["Aggressive, powerful pressure", "Wrestling in the mix"],
       ["Wildness under pressure", "Few rounds of UFC experience"],
       ["Counter his pressure with accurate shots", "Make it a technical fight"],
       [],
       ["sd1", "ufc_preview"], "moderate")

report("Alden Coria",
       "An accurate, dogged counter-striker: 3-0 in the UFC, with a short-notice stoppage of Alessandro Costa and two clear but "
       "unspectacular decisions in 2026. Sharp when opponents lead; less able to break open a slow fight.",
       {"Striking": "Accurate counter-striking; can do real damage when opponents get wild.",
        "Grappling": "Threatens submissions (about 1.2 attempts per 15 minutes) but his takedown defense (about 45%) is a question.",
        "Defense": "Composed; absorbs about 2.4 significant strikes a minute.",
        "Pace & cardio": "Goes three rounds comfortably.",
        "Fight IQ": "Patient; waits for the opponent to lead."},
       ["Counters opponents who lead", "Stands his ground under pressure"],
       ["Takedown defense", "Doesn't force the action in slow fights"],
       ["Wrestle him", "Don't give him easy counters: feint and take him down"],
       [],
       ["sd1", "ufc_preview"], "moderate")

report("Damian Pinas",
       "The 'death touch' middleweight: 25, with a long frame, a 200-cm reach and one-punch power; five straight first-round "
       "knockouts, including Cesar Almeida, a kickboxer never stopped before.",
       {"Striking": "Not much happens until it does: picks spots, then lands shots that end fights.",
        "Grappling": "Largely untested.",
        "Defense": "Raw; hasn't needed defense in short fights.",
        "Pace & cardio": "Never been past the first round in his current run.",
        "Fight IQ": "Improving shot selection (Sherdog)."},
       ["One-punch knockouts", "Patient until he finds the shot"],
       ["Unproven beyond round one", "Raw defensively"],
       ["Survive early and drag him long", "Wrestle"],
       [],
       ["sd2", "ufc_preview"], "moderate")

report("Andrey Pulyaev",
       "A lanky, durable range fighter who makes talented opponents' nights ugly by picking at range; lost three straight "
       "(decision to Gautier, submission to Nursulton Ruziboev).",
       {"Striking": "Stays long and picks shots; frustrating rather than dangerous.",
        "Grappling": "Takedown defense about 53%; submitted in June.",
        "Defense": "Durable, but hasn't faced this level of power.",
        "Pace & cardio": "Fine over three rounds.",
        "Fight IQ": "Crafty but can't turn it into wins against top opposition."},
       ["Range and jab", "Makes fights ugly"],
       ["Three-fight skid", "Low finishing threat"],
       ["Close the distance", "Land clean power"],
       [],
       ["sd2", "ufc_preview"], "moderate")

report("Marcus McGhee",
       "An elite athlete and late starter who feels fights out and changes approach round to round until he finds what works; "
       "5-1 in the UFC, with the loss to champion Petr Yan. Now faces a newcomer on three days' notice.",
       {"Striking": "Powerful and athletic, three UFC finishes, but not a game-planner (Sherdog).",
        "Grappling": "Can wrestle; scrambles well.",
        "Defense": "Solid; absorbs about 3.3 a minute.",
        "Pace & cardio": "Better late than early; adjusts across rounds.",
        "Fight IQ": "Reactive: solves fights in-fight rather than coming in with a plan."},
       ["Starts measured, builds through the fight"],
       ["Opponent swap three days out (new style to prepare for)", "Can be neutralized by a thoughtful opponent"],
       ["Take the early rounds before he figures you out"],
       [{"date": "2026-09-30", "text": "Benardo Sopaj withdrew; McGhee now faces promotional newcomer Anthony Romero on three days' notice.", "source": SRC["mania_mcghee"]["url"]}],
       ["sd3", "mania_mcghee", "mmaf_mcghee"], "moderate")

report("Anthony Romero",
       "A short-notice UFC newcomer from Black House MMA with a two-fight win streak, most recently a 25-second knockout of "
       "Yuma Horiuchi. Sources disagree on his record (13-3 on Sherdog, 7-2 per MMA Mania); the Horiuchi knockout matches "
       "our records, so it's the same fighter, but thin regional data means the model knows little about him.",
       {"Striking": "Finisher: four KOs and two submissions in seven wins (per MMA Mania).",
        "Grappling": "Two submission wins.",
        "Defense": "Unknown at UFC level.",
        "Pace & cardio": "Took the fight on three days' notice.",
        "Fight IQ": "Unknown."},
       ["Early finishing threat"],
       ["Three days' notice for a debut against a ranked opponent", "Record differs between sources (13-3 vs 7-2)"],
       ["Test his conditioning late"],
       [{"date": "2026-09-30", "text": "Steps in for Benardo Sopaj on three days' notice against No. 15 Marcus McGhee.", "source": SRC["mania_mcghee"]["url"]}],
       ["mania_mcghee", "mmaf_mcghee"], "thin")

report("Anthony Wint",
       "A former FIU linebacker (a season in the NFL) with high-school wrestling: 8-0, running through opponents on horsepower. "
       "Undersized for heavyweight; fighting for the second time in about seven weeks.",
       {"Striking": "Explosive power; wins by overwhelming opponents early.",
        "Grappling": "Wrestling base; submitted Terrance Chatman in round one in his UFC debut.",
        "Defense": "Lacks defensive awareness (Sherdog).",
        "Pace & cardio": "Never been tested late.",
        "Fight IQ": "Hasn't had to overcome adversity yet."},
       ["Bull-rush pressure and takedowns", "Early finishes"],
       ["Undersized at heavyweight", "Defensive holes", "Quick turnaround"],
       ["Survive the storm and hit him as he comes in"],
       [],
       ["sd4", "ufc_preview"], "moderate")

report("Lucas Armand",
       "An unbeaten (6-0) Michigan heavyweight debuting in the UFC; finished his last five, including UFC veteran Braxton Smith, but "
       "against a poor level of regional competition.",
       {"Striking": "Heavyweight size and power; film is unconvincing (Sherdog).",
        "Grappling": "Unknown.",
        "Defense": "Untested against a UFC-level athlete.",
        "Pace & cardio": "Unknown; one four-round finish.",
        "Fight IQ": "Unknown."},
       ["Size and early finishes"],
       ["Level of opposition", "Debut"],
       ["Pressure and wrestle him"],
       [],
       ["sd4", "ufc_preview"], "thin")

report("Johnny Walker",
       "A huge, awkward, explosive Brazilian moving up to heavyweight after a confused few years at light heavyweight: the wild "
       "aggression that made him was coached out, leaving a fighter who freezes at range and gets knocked out when opponents force the issue.",
       {"Striking": "Long (208-cm reach) and dangerous when he lets go; recent fights have been tentative (the Dominick Reyes split "
                    "decision saw neither man lead).",
        "Grappling": "Was outwrestled by Nikita Krylov years ago; wrestling defense about 56%.",
        "Defense & durability": "Stopped by Volkan Oezdemir and Magomed Ankalaev (2024): chin is a concern, now against heavier punchers.",
        "Pace & cardio": "Should be better without the cut to 205.",
        "Fight IQ": "Indecisive lately; the hope is heavyweight frees him up."},
       ["Waits at range; flashes of explosive offense"],
       ["Chin against heavyweight power", "Freezes under pressure"],
       ["Apply consistent pressure and make him fight going backward"],
       [],
       ["sd5", "ufc_preview"], "good")

report("Mick Parkin",
       "An underrated, durable English heavyweight who plugs away with solid power at a steady pace, with decent wrestling behind it; "
       "10-1, the only loss a decision to Marcin Tybura, and back after 18 months out.",
       {"Striking": "Not pretty or dynamic, but a surprisingly deft striker for his size (Sherdog).",
        "Grappling": "Decent wrestling to fall back on.",
        "Defense": "Fairly hittable.",
        "Pace & cardio": "Steady three-round pace.",
        "Fight IQ": "Sensible; needs to commit to pressure here."},
       ["Steady pressure", "Mixes in wrestling"],
       ["Layoff since March 2025", "Hittable against a long, explosive striker"],
       ["Use length and counters as he walks in"],
       [],
       ["sd5", "ufc_preview"], "moderate")

report("Rafael dos Anjos",
       "A former lightweight champion and one of the great pressure fighters, now 42, back from a two-year layoff and three knee "
       "surgeries (torn ACL and meniscus) and on a three-fight losing streak, cutting back to 155 where his cardio has faltered before.",
       {"Striking": "Southpaw pressure: body kicks and relentless forward movement.",
        "Grappling": "Strong top game when he gets there.",
        "Defense & durability": "Durable, but finished by Geoff Neal in 2024 (the fight where the knee went).",
        "Pace & cardio": "The central question: at lightweight, the cut has drained him before.",
        "Fight IQ": "Elite experience and doggedness."},
       ["Southpaw pressure and body kicks"],
       ["Age, layoff and knee surgery", "Weight cut to 155"],
       ["Move and counter; make him chase"],
       [{"date": "2026-08-21", "text": "Returns after two years out following three knee surgeries.", "source": SRC["rda_injury"]["url"]}],
       ["sd6", "rda_injury", "ufc_preview"], "good")

report("Alexander Hernandez",
       "A powerful pot-shotting counter striker who rebuilt his career after confidence problems: four straight wins (knockouts of "
       "Chase Hooper and Diego Ferreira) until Rafa Garcia's bull-headed pressure beat him in April.",
       {"Striking": "Powerful, well-timed shots from range; feels in control when opponents don't pressure.",
        "Grappling": "Good takedown defense (about 81%).",
        "Defense": "Pressure fighters are his problem (Garcia).",
        "Pace & cardio": "Fine for three rounds.",
        "Fight IQ": "Has historically folded under sustained pressure, but fixed much of that."},
       ["Counter power from range"],
       ["Sustained pressure"],
       ["Walk him down and make him fight off the back foot"],
       [],
       ["sd6", "ufc_preview"], "good")

report("Jacobe Smith",
       "A former collegiate wrestler and elite athlete, 12-0, with ground-and-pound finishes and some dynamic striking; overconfident "
       "and with defensive holes, but still getting overmatched opponents.",
       {"Striking": "Dynamic, athletic; knocked out Josiah Harrell in round one in February.",
        "Grappling": "Heavy wrestling (about 4.9 takedowns per 15 minutes) and ground-and-pound.",
        "Defense": "Holes (Sherdog); doesn't know what he doesn't know.",
        "Pace & cardio": "Rarely needed.",
        "Fight IQ": "Overconfident; hasn't been tested."},
       ["Takedowns and ground-and-pound", "Early finishes"],
       ["Defensive holes against a puncher"],
       ["Land something big early"],
       [{"date": "2026-09-24", "text": "Added to UFC 332 on about nine days' notice against newcomer Bruce Whitehead.", "source": SRC["smith_notice"]["url"]}],
       ["sd9", "smith_notice", "ufc_preview"], "good")

report("Bruce Whitehead",
       "A powerfully built Fury FC regular with knockout power, taking a UFC debut on about nine days' notice, a week after a 48-second "
       "TKO; knocked out quickly by Victor Valenzuela in 2025.",
       {"Striking": "Power puncher; best work against weak opposition (Sherdog).",
        "Grappling": "Unknown against a high-level wrestler.",
        "Defense": "Quick KO loss raises firefight concerns.",
        "Pace & cardio": "Short notice.",
        "Fight IQ": "Unknown."},
       ["Early power"],
       ["Short notice", "Level of opposition", "Wrestling defense"],
       ["Take him down"],
       [],
       ["sd9", "smith_notice"], "thin")

report("Marvin Vettori",
       "A granite-chinned pressure middleweight and former title challenger who lost himself trying to become a slicker, lower-output "
       "fighter; four straight losses, all on the cards, and a camp change back to California under Beneil Dariush.",
       {"Striking": "At his best as a relentless, high-output pressure fighter; not enough power to win on selective shots.",
        "Grappling": "Can wrestle and grind.",
        "Defense & durability": "Never been finished in the UFC stretch; the chin is intact.",
        "Pace & cardio": "Can go hard for five rounds.",
        "Fight IQ": "'Paralysis by analysis' lately (Sherdog)."},
       ["Pressure and volume when he's right"],
       ["Four-fight skid, confidence", "Camp change"],
       ["Make him think; stay long and score"],
       [{"date": "2026-09-30", "text": "Left American Top Team to train in California with Beneil Dariush as head coach.", "source": SRC["vettori_camp"]["url"]}],
       ["sd7", "vettori_camp", "ufc_preview"], "good")

report("Ismail Naurdiev",
       "A sharp, busy kickboxer back in the UFC at middleweight, 2-1 since his return with a first-round KO of Ryan Loder; "
       "throws plenty of good strikes but can look aimless against a focused opponent.",
       {"Striking": "Throws a lot of sharp strikes; absorbs only about 2.5 a minute.",
        "Grappling": "Uses takedowns occasionally.",
        "Defense": "Good distance management.",
        "Pace & cardio": "Solid.",
        "Fight IQ": "'Throwing out ideas and hoping for the best' (Sherdog)."},
       ["Volume kickboxing"],
       ["Aimlessness against a clear game plan"],
       ["Pressure him with a plan"],
       [],
       ["sd7", "ufc_preview"], "moderate")

report("Court McGee",
       "The TUF 11 winner in his hometown retirement fight: technically sound, naturally strong, durable in his prime, without "
       "knockout power. Now 42 with some recent KO losses.",
       {"Striking": "Steady, workmanlike volume.",
        "Grappling": "Strong grappler; submitted Tim Means in round one in Utah in 2024.",
        "Defense & durability": "KO'd by Matt Brown and Jeremiah Wells (2022-23).",
        "Pace & cardio": "Three rounds of hard work.",
        "Fight IQ": "Veteran; emotional night."},
       ["Grinding pace, early grappling"],
       ["Age and durability", "Emotion of a farewell fight"],
       ["Keep it standing and hit him clean"],
       [],
       ["sd8", "ufc_preview"], "good")

report("Eric Nolan",
       "A solid welterweight prospect fed two hard assignments (Baisangur Susurkaev on short notice, Farman Hasanov in Baku) and 0-2 in "
       "the UFC; his regional run was built on knockouts.",
       {"Striking": "KO power (three straight first- or second-round KOs before the UFC).",
        "Grappling": "Submitted by Susurkaev.",
        "Defense": "Takedown defense about 47%.",
        "Pace & cardio": "Went three rounds with Hasanov.",
        "Fight IQ": "Solid (Sherdog)."},
       ["Power striking"],
       ["Grappling defense early"],
       ["Wrestle him early"],
       [],
       ["sd8", "ufc_preview"], "moderate")

out = ROOT / "reports"
out.mkdir(parents=True, exist_ok=True)
for name, doc in R.items():
    (out / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(len(R), "reports")
