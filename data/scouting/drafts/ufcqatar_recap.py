"""Card review for UFC Fight Night 294: Prochazka vs. Stirling (ABHA Arena, Doha, 2026-11-21).

What happened in every bout (our own words, from Sherdog's play-by-play and round scoring, MMA Junkie's live updates
through Yahoo, and the recaps the sweep collected: MMA Mania, MMA Fighting, BJPenn.com, Cageside Press, LowKick MMA),
the pre-fight claims checked against the fights, judged performances for data/scouting/fight_notes.json where two
outlets agree, and a dated note in both fighters' scouting reports. Written Sunday 2026-11-22.

Sherdog's play-by-play skipped Albazi-Costa (its round scores for that bout landed inside the Matthews-Abdullayev
block), so that story rests on MMA Junkie's live updates and Cageside Press. Vallejos-Sterling is `disputed`: all three
Sherdog scorers had Sterling winning at least two rounds, and MMA Fighting quotes pros calling it a robbery.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = "2026-11-21-ufc-fight-night-294-prochazka-vs-stirling"
EVENT, DATE, WRITTEN = "UFC Fight Night 294 - Prochazka vs. Stirling", "2026-11-21", "2026-11-22"
UPDATED = "2026-11-22T19:00:00+00:00"
SHERDOG = "https://www.sherdog.com/news/news/UFC-Qatar-Prochazka-vs-Stirling-playbyplay-results-round-scoring-203707"
JUNKIE = "https://sports.yahoo.com/articles/ufc-qatar-live-updates-jiri-130212410.html"
CAGESIDE_ALBAZI = "Cageside Press: Amir Albazi Survives Knockdown, Point Deduction to Finish Alessandro Costa"


def chk(by, claim, tag, favoured, verdict, note):
    return {"by": by, "claim": claim, "tag": tag, "favoured": favoured, "verdict": verdict, "note": note}


STIRLING, JIRI = "Navajo Stirling", "Jiri Prochazka"
VALLEJOS, ALJO = "Kevin Vallejos", "Aljamain Sterling"
HOOKER, ORTEGA = "Dan Hooker", "Brian Ortega"
HORI, ASU = "Kyoji Horiguchi", "Asu Almabayev"
ALISK, CANN = "Ikram Aliskerov", "Jared Cannonier"
LUNA, TOPURIA = "Santiago Luna", "Aleksandre Topuria"
TEIX, GAZIEV = "Tallison Teixeira", "Shamil Gaziev"
ALBAZI, COSTA = "Amir Albazi", "Alessandro Costa"
TAHIR, MATTHEWS = "Tahir Abdullayev", "Jake Matthews"
FAN, MOTTA = "Dom Mar Fan", "Nikolas Motta"
DIYAR, LORENZ = "Diyar Nurgozhay", "Alik Lorenz"
MITCHELL, YOUSAF = "John Mitchell", "Shoaib Yousaf"

STORIES = {
    "navajo-stirling-jiri-prochazka": dict(
        summary="A patient first round in which Stirling chopped at Procházka's lead leg, though Procházka put him on his back "
                "with a counter overhand right late in the round and let him up; all three Sherdog scorers still gave Stirling "
                "the round. Round 2 was more of the same leg kicks until, with two seconds left, Stirling slipped a left hook "
                "and knocked Procházka out with a counter right hook against the fence.",
        turning_point="Procházka's knockdown in round 1: he chose not to follow Stirling to the floor.",
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Stirling the faster, cleaner striker; Procházka gets hit; finish in R2 once the exchanges open up",
                "durability", STIRLING, "held", "Knocked out at 4:58 of round 2 on a counter, exactly as written."),
            chk("read", "Procházka's recent knockout losses", "durability", STIRLING, "held",
                "His third knockout loss in four fights against top opposition."),
            chk("read", "Stirling's first five-rounder (against)", "cardio", JIRI, "untested", "Over inside 10 minutes."),
            chk("read", "Procházka's power (against)", "power", JIRI, "mixed",
                "He dropped Stirling in round 1 but did not follow up."),
            chk("model", "Fresher body", "wear_and_tear", STIRLING, "held",
                "The younger, less-worn fighter took the exchanges and the finish."),
            chk("model", "Power vs chin", "power_vs_chin", STIRLING, "held", "One clean counter ended it."),
            chk("model", "Experience", "experience", JIRI, "failed", "Procházka's experience did not show; he was out-thought at range."),
        ]),
    "kevin-vallejos-aljamain-sterling": dict(
        summary="Sterling jabbed, kicked the body and shot again and again; Vallejos stuffed 11 of 12 takedowns, landed the "
                "harder right hands on the counter and scrambled up at once from the one takedown Sterling got in round 2. "
                "The judges gave Vallejos all three rounds on two cards (30-27, 30-27, 29-28), while all three Sherdog scorers "
                "had Sterling ahead and MMA Fighting quoted pros calling it a robbery. UFC Stats had Vallejos ahead 37-32 in "
                "significant strikes.",
        verdict="right on the cards, wrong on the fight",
        checks=[
            chk("pick", "Sterling is 37, struggled on the cut and gets stopped by explosive strikers; Vallejos by KO in R1",
                "durability", VALLEJOS, "failed",
                "Sterling was never hurt badly and Vallejos fought a counter-striking decision."),
            chk("read", "Sterling's grappling", "wrestling", ALJO, "failed",
                "One takedown from 12 attempts, and Vallejos was up straight away."),
            chk("read", "Vallejos's power (against)", "power", VALLEJOS, "mixed",
                "His right hands landed cleanest but never dropped Sterling."),
            chk("read", "Sterling's age (against)", "age", VALLEJOS, "untested",
                "Sterling kept his pace for three rounds; no sign of decline beyond the failed shots."),
            chk("model", "Fresher body", "wear_and_tear", VALLEJOS, "mixed", "Won on the cards in a fight scorers split on."),
            chk("model", "Wrestling rating", "wrestling_rating", ALJO, "failed",
                "Sterling's wrestling advantage on paper produced one takedown in 12 tries."),
            chk("model", "Fight Matrix rating", "outside_rating", ALJO, "mixed", "Close fight; the judges went the other way."),
            chk("model", "Overall rating", "overall", ALJO, "mixed", "Close fight; the judges went the other way."),
            chk("model", "Power vs chin", "power_vs_chin", VALLEJOS, "untested", "No knockdowns."),
        ]),
    "dan-hooker-brian-ortega": dict(
        summary="Hooker kicked Ortega's legs and body from the opening seconds and doubled up his jab, and Ortega looked "
                "gun-shy; Hooker got straight back up from the one takedown and turned away the rest. By round 3 Ortega was "
                "marked up around the right eye and winging punches, and his last takedown and back take came too late. "
                "Hooker won 30-27 on all three cards, as all three Sherdog scorers had it, and Ortega announced his retirement.",
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Ortega out 15 months, two withdrawals, first walk at 155; Hooker's volume wins the rounds; a decision",
                "inactivity", HOOKER, "held", "Ortega was hesitant and outworked in every round; a clear 30-27."),
            chk("read", "Ortega's 15-month layoff and two withdrawals", "inactivity", HOOKER, "held",
                "Gun-shy early and never found a rhythm."),
            chk("read", "Ortega's first fight at 155", "weight_cut", HOOKER, "held",
                "Couldn't hold Hooker down or match his length."),
            chk("read", "Hooker's durability (against)", "durability", ORTEGA, "held",
                "Hooker took Ortega's best right hands and kept moving forward."),
            chk("model", "Fresher body", "wear_and_tear", ORTEGA, "failed", "The fresher-body edge did not show against a busier fighter."),
            chk("model", "Overall rating", "overall", ORTEGA, "failed", "Lost every round on every card."),
            chk("model", "Wrestling rating", "wrestling_rating", ORTEGA, "failed",
                "One brief takedown in round 1 and a late back take; Hooker stayed upright."),
        ]),
    "kyoji-horiguchi-asu-almabayev": dict(
        summary="Horiguchi landed the cleaner strikes standing, but Almabayev took him down repeatedly and held him for more "
                "than nine minutes in all. Horiguchi nearly finished him twice with guillotines, swept, and scored with "
                "elbows and body punches from the bottom, and Almabayev offered little on top. All three Sherdog scorers gave "
                "Horiguchi every round; the judges had it 30-27, 30-27, 29-28, and Horiguchi apologised for a boring fight.",
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "Horiguchi's speed and takedown defence keep the grinder at bay; a decision", "td_defence", HORI,
                "mixed", "Right result and method, but his takedown defence did not hold: he won from his back."),
            chk("read", "Horiguchi's takedown defence", "td_defence", HORI, "failed", "Taken down again and again."),
            chk("read", "Almabayev's grappling (against)", "grappling", ASU, "mixed",
                "Plenty of control time, almost no damage, and two near-guillotines against him."),
            chk("model", "Fresher body", "wear_and_tear", ASU, "failed", "Almabayev's pace did not tell over three rounds."),
            chk("model", "Striking rating", "striking_rating", HORI, "held", "Cleaner shots on the feet in every round."),
            chk("model", "Wrestling edge", "wrestling_edge", ASU, "mixed",
                "The takedowns came, but the judges did not reward the control."),
            chk("model", "Overall rating", "overall", HORI, "held", "Won every round on Sherdog's cards."),
            chk("model", "Age curve", "age_curve", ASU, "failed", "The 36-year-old outworked the younger man."),
        ]),
    "ikram-aliskerov-jared-cannonier": dict(
        summary="Cannonier pressed forward early, but Aliskerov dropped him in round 1 and was the busier striker. From "
                "round 2 Aliskerov took him down at will, mounted him several times, took his back and hunted face cranks, "
                "arm-triangles and a rear-naked choke without getting the finish. A 30-27 sweep on every card, Sherdog's "
                "included.",
        turning_point="Aliskerov's first takedown in round 2; Cannonier had no answer on the ground from then on.",
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Aliskerov wins by control; Cannonier rarely stopped; three rounds", "wrestling", ALISK, "held",
                "Control in rounds 2 and 3 and a clear decision."),
            chk("read", "Cannonier's age and form", "age", ALISK, "held", "The 42-year-old had no answer to the takedowns."),
            chk("read", "Aliskerov's wrestling", "wrestling", ALISK, "held", "Takedowns at will and repeated mounts."),
            chk("read", "Cannonier's power early (against)", "power", CANN, "failed",
                "Cannonier was the one dropped in round 1."),
            chk("model", "Fresher body", "wear_and_tear", ALISK, "held", "Aliskerov kept his pace; Cannonier slowed."),
            chk("model", "Age curve", "age_curve", ALISK, "held", "The age gap showed in the scrambles."),
            chk("model", "Wrestling rating", "wrestling_rating", ALISK, "held", "Dominant on the mat."),
            chk("model", "Wrestling edge", "wrestling_edge", ALISK, "held", "Dominant on the mat."),
            chk("model", "Overall rating", "overall", ALISK, "held", "Won every round."),
        ]),
    "santiago-luna-aleksandre-topuria": dict(
        summary="Luna pressured from the start and out-landed Topuria with four- to six-punch combinations, collar-tie "
                "uppercuts and body shots; Topuria dropped him with a clean right hand in round 1 and swept his legs with a "
                "kick in round 3, but never wrestled. Sherdog's three scorers gave Luna every round; the judges split "
                "(30-27, 28-29, 29-28) for Luna.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Topuria's Greco-Roman wrestling and BJJ against a 22-year-old submitted from his back; on the cards",
                "wrestling", TOPURIA, "failed", "Topuria tried one clinch takedown all fight and lost the striking."),
            chk("read", "Topuria's layoff (against)", "inactivity", LUNA, "held",
                "A year out, Topuria could not match Luna's pace."),
            chk("read", "Luna's bottom game", "grappling", TOPURIA, "untested", "The fight never went to the ground."),
            chk("model", "Overall rating", "overall", LUNA, "held", "Luna won on Sherdog's cards in every round."),
            chk("model", "Striking rating", "striking_rating", LUNA, "held", "Out-landed Topuria with combinations."),
        ]),
    "tallison-teixeira-shamil-gaziev": dict(
        summary="A low-output heavyweight fight. Gaziev took round 1 with a one-two that sat Teixeira down and pressure into "
                "the clinch, then barely threw; Teixeira won the last two rounds from range with leg kicks, front kicks to "
                "the body and jabs while retreating. The judges gave Teixeira a unanimous decision (30-27, 29-28, 29-28), "
                "and two of three Sherdog scorers agreed; the crowd booed.",
        verdict="right, other reasons",
        checks=[
            chk("pick", "Gaziev knocked out three straight times; all Teixeira's finishes in R1; an early KO",
                "durability", TEIX, "failed", "Nobody was finished; Teixeira won on points over 15 minutes."),
            chk("read", "Both chins", "durability", GAZIEV, "failed", "Gaziev dropped Teixeira once, and both lasted."),
            chk("read", "Teixeira's cardio past R1", "cardio", GAZIEV, "failed",
                "Teixeira won rounds 2 and 3; it was Gaziev whose output vanished."),
            chk("model", "Fresher body", "wear_and_tear", TEIX, "held", "Teixeira kept working after round 1; Gaziev did not."),
            chk("model", "Age curve", "age_curve", TEIX, "held", "The younger man won the late rounds."),
            chk("model", "Height", "height", TEIX, "held", "He won by keeping Gaziev at the end of his kicks."),
        ]),
    "amir-albazi-alessandro-costa": dict(
        summary="Costa dropped Albazi and battered him in round 2, and Albazi was docked a point for grabbing the fence, "
                "leaving him needing a finish in round 3. Late in the round he took Costa down after a slip, moved to half "
                "guard, took the back with a body triangle and squeezed out a one-armed rear-naked choke at 4:34.",
        turning_point="The takedown off Costa's slip in round 3, with Albazi behind on the cards.",
        verdict="right, other reasons",
        checks=[
            chk("pick", "A tight decision; Albazi's takedowns have dried up; Costa rarely finished", "wrestling", ALBAZI,
                "mixed", "Right winner, but by a comeback submission from a takedown in round 3, not on the cards."),
            chk("read", "Albazi's inactivity and health history", "inactivity", COSTA, "mixed",
                "He looked rusty and was hurt in round 2, but rallied."),
            chk("read", "Costa's form", "form", COSTA, "held", "Costa won rounds 1 and 2 clearly."),
            chk("read", "Albazi's previous knockout of Costa (against)", "history", ALBAZI, "mixed",
                "Albazi won again, this time on the ground."),
            chk("model", "Fresher body", "wear_and_tear", ALBAZI, "mixed", "Albazi lasted and finished, but was the one hurt."),
        ],
        single_source=False),
    "tahir-abdullayev-jake-matthews": dict(
        summary="Abdullayev, who missed weight by a pound, stung Matthews with a right hand in round 1 and took over on the "
                "mat, dropping elbows from side control and half guard. He took Matthews down in every round, landed a knee "
                "as Matthews stood in round 2, and shut down his triangle and kimura attempts. All three Sherdog scorers had "
                "it 30-27; the judges 30-27, 30-27, 29-28.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Abdullayev's record thin and inconsistent by source; Matthews grinds out rounds with jiu-jitsu",
                "experience", MATTHEWS, "failed", "Abdullayev out-grappled him from the first exchange."),
            chk("read", "Abdullayev's thin UFC data", "data", MATTHEWS, "failed",
                "The regional record the model trusted was right."),
            chk("read", "Matthews's experience", "experience", MATTHEWS, "failed", "Never got going."),
            chk("read", "Matthews's late fades (against)", "cardio", TAHIR, "untested",
                "He was losing from round 1; both were tired by round 3."),
            chk("model", "Fresher body", "wear_and_tear", TAHIR, "held", "Kept up the takedowns for three rounds."),
            chk("model", "Wrestling rating", "wrestling_rating", MATTHEWS, "failed", "Taken down in every round."),
        ]),
    "dom-mar-fan-nikolas-motta": dict(
        summary="Fan took Motta down inside 20 seconds and beat him up from top position for all of round 1. Motta dropped "
                "him with a left hook early in round 2, but Fan recovered and hurt him repeatedly with jabs, hooks and a "
                "clean head kick that Motta somehow walked through. The doctor checked Motta before round 3; Fan won "
                "30-26, 29-27, 29-27.",
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Motta 17 months out after a broken jaw, little ground game; Fan's grappling controls him; a decision",
                "grappling", FAN, "held", "A takedown in 20 seconds and a whole round of ground and pound."),
            chk("read", "Motta's layoff and jaw injury", "inactivity", FAN, "mixed",
                "His chin held up remarkably; the rust showed in his defence."),
            chk("read", "Fan's grappling", "grappling", FAN, "held", "Controlled round 1 and duplexed him late in round 3."),
            chk("read", "Fan's submission defence (against)", "grappling", MOTTA, "untested", "Motta never threatened one."),
            chk("model", "Fresher body", "wear_and_tear", FAN, "held", "Fan's pace never dropped much."),
            chk("model", "Striking rating", "striking_rating", MOTTA, "mixed",
                "Motta's left hook dropped Fan, but Fan won the striking overall."),
            chk("model", "Height", "height", FAN, "held", "The jab was his best weapon all night."),
        ]),
    "diyar-nurgozhay-alik-lorenz": dict(
        summary="Nurgozhay swept the debutant off his feet in the opening seconds, traded evenly for a while, then took him "
                "down with a single leg and landed elbows until late in round 1. Twenty-four seconds into round 2 a left "
                "head kick dropped Lorenz, and hammerfists finished it.",
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "An early finish, Nurgozhay's way, in R1", "finishing", DIYAR, "mixed",
                "The finish came 24 seconds into round 2, not round 1."),
            chk("read", "Lorenz's debut", "debut", DIYAR, "held", "Overmatched on the mat and on the feet."),
            chk("read", "Nurgozhay's submission defence (against)", "grappling", LORENZ, "untested",
                "Lorenz flirted with a triangle once."),
            chk("model", "Power vs chin", "power_vs_chin", DIYAR, "held", "One head kick ended it."),
            chk("model", "Fight Matrix rating", "outside_rating", DIYAR, "held", "Clearly the better fighter."),
            chk("model", "Wrestling rating", "wrestling_rating", DIYAR, "held", "Two takedowns at will in round 1."),
            chk("model", "Submission threat", "submission_threat", LORENZ, "untested", "Never threatened."),
            chk("model", "Overall rating", "overall", DIYAR, "held", "Won every exchange that mattered."),
        ]),
    "john-mitchell-shoaib-yousaf": dict(
        summary="Two debutants on three days' notice. Yousaf controlled the centre and rocked Mitchell with winging punches, "
                "but walked into knees; when Yousaf clinched, Mitchell turned him, landed an elbow and then a knee to the face "
                "that dropped him, and finished with punches at 3:50 of round 1.",
        turning_point="Mitchell's knee off the separation from the clinch, just as Yousaf seemed to be on top.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Yousaf never stopped, all losses on the cards; a decision", "durability", YOUSAF, "failed",
                "Knocked out in round 1, his first stoppage loss."),
            chk("read", "Both on short notice", "short_notice", MITCHELL, "untested", "Ended too early to show."),
            chk("read", "Yousaf's early power (against)", "power", YOUSAF, "mixed",
                "He hurt Mitchell early but was finished first."),
            chk("model", "Overall rating", "overall", YOUSAF, "failed", "Lost inside four minutes."),
        ]),
}

# (bout key, fighter, opponent, category, rating, skills, note): where two outlets agree.
NOTES = [
    ("navajo-stirling-jiri-prochazka", STIRLING, JIRI, "striking", 1.5, ["leg_kicks", "counter", "patience"],
     "Chopped the lead leg for two rounds and knocked him out with a slipped counter right hook; was dropped once in round 1."),
    ("kevin-vallejos-aljamain-sterling", VALLEJOS, ALJO, "wrestling", 1.5, ["td_def", "scramble"],
     "Stuffed 11 of 12 takedowns and scrambled straight up from the one Sterling got."),
    ("dan-hooker-brian-ortega", HOOKER, ORTEGA, "striking", 1.5, ["kicks", "jab", "volume"],
     "Leg and body kicks from the first seconds and a doubled jab; won every round on every card."),
    ("kyoji-horiguchi-asu-almabayev", ASU, HORI, "wrestling", 1.0, ["td", "control"],
     "Took Horiguchi down repeatedly and held him for more than nine minutes, with little damage done."),
    ("kyoji-horiguchi-asu-almabayev", HORI, ASU, "grappling", 1.0, ["guillotine", "sweep", "bottom_strikes"],
     "Two deep guillotines, sweeps and elbows from the bottom won him rounds he spent on his back."),
    ("ikram-aliskerov-jared-cannonier", ALISK, CANN, "wrestling", 2.0, ["td", "mount", "back_take"],
     "Takedowns at will from round 2, repeated mounts and the back; also dropped him in round 1."),
    ("santiago-luna-aleksandre-topuria", LUNA, TOPURIA, "striking", 1.0, ["combinations", "pressure", "clinch_uppercuts"],
     "Out-landed Topuria with long combinations and collar-tie uppercuts; was dropped once in round 1."),
    ("tahir-abdullayev-jake-matthews", TAHIR, MATTHEWS, "wrestling", 2.0, ["td", "top_control", "gnp"],
     "Took Matthews down in every round and landed elbows from side control and half guard."),
    ("dom-mar-fan-nikolas-motta", FAN, MOTTA, "wrestling", 1.5, ["td", "gnp"],
     "A takedown inside 20 seconds and a full round of ground and pound."),
    ("dom-mar-fan-nikolas-motta", FAN, MOTTA, "striking", 1.0, ["jab", "head_kick"],
     "Jab and hooks hurt Motta repeatedly in rounds 2 and 3, though Motta dropped him once."),
    ("diyar-nurgozhay-alik-lorenz", DIYAR, LORENZ, "striking", 2.0, ["head_kick", "finishing"],
     "Finished the debutant with a left head kick 24 seconds into round 2."),
    ("john-mitchell-shoaib-yousaf", MITCHELL, YOUSAF, "striking", 1.0, ["clinch", "knees", "finishing"],
     "Hurt early, then dropped Yousaf with a knee off the clinch and finished him in round 1."),
]

REPORTS = {
    "navajo-stirling": dict(src=SHERDOG,
        text="Knocked out Jiri Prochazka at 4:58 of R2 with a slipped counter right hook after two rounds of leg kicks; was "
             "dropped by an overhand right late in R1 and recovered when Prochazka let him up. Now 12-0, 7-0 UFC.",
        add_patterns=["Patient leg-kick work and a counter right hook that finishes when opponents commit"],
        add_concerns=["Dropped in R1 by Prochazka's counter overhand; hurt in three straight fights"]),
    "jiri-prochazka": dict(src=SHERDOG,
        text="Knocked out by Navajo Stirling at 4:58 of R2, his second straight knockout loss; fought uncharacteristically "
             "patient, dropped Stirling in R1 but did not follow him down. Several pros suggested a move to 185.",
        add_concerns=["Knocked out in three of his last four (Pereira twice, Ulberg, Stirling)"]),
    "kevin-vallejos": dict(src=SHERDOG,
        text="Beat Aljamain Sterling by unanimous decision (30-27, 30-27, 29-28), stuffing 11 of 12 takedowns and winning the "
             "counter right hands; a disputed result (all three Sherdog scorers had Sterling). Called for a title shot.",
        add_patterns=["Elite takedown defence and scrambling against a top wrestler (Sterling: 1 of 12)"]),
    "aljamain-sterling": dict(src=SHERDOG,
        text="Lost a disputed unanimous decision to Kevin Vallejos: landed 1 of 12 takedowns but out-jabbed him in R1 and R2 "
             "on Sherdog's cards; said he felt he had done enough.",
        add_concerns=["Takedowns no longer land against strong defenders at 145 (1 of 12 against Vallejos)"]),
    "dan-hooker": dict(src=SHERDOG,
        text="Beat Brian Ortega 30-27 x3 with leg and body kicks and a doubled jab, snapping a three-fight losing run; got "
             "straight up from the one takedown and stuffed the rest.",
        add_patterns=["Kicks to all levels and a doubled jab win rounds against slower starters"]),
    "brian-ortega": dict(src=SHERDOG,
        text="Lost to Dan Hooker 30-27 x3 in his first fight at 155 after 15 months out; gun-shy early, beaten to the punch "
             "and unable to hold Hooker down. Announced his retirement afterwards."),
    "kyoji-horiguchi": dict(src=SHERDOG,
        text="Beat Asu Almabayev by unanimous decision (30-27, 30-27, 29-28) despite more than nine minutes on his back: two "
             "deep guillotines, sweeps and elbows from the bottom; cleaner on the feet.",
        add_patterns=["Dangerous guillotine and active bottom game that wins rounds spent underneath"],
        add_concerns=["Taken down repeatedly by a flyweight grinder (Almabayev)"]),
    "asu-almabayev": dict(src=SHERDOG,
        text="Lost to Kyoji Horiguchi by unanimous decision despite repeated takedowns and over nine minutes of control; "
             "little damage on top and twice nearly caught in guillotines.",
        add_concerns=["Control without damage loses rounds against an active bottom player (Horiguchi)"]),
    "ikram-aliskerov": dict(src=SHERDOG,
        text="Beat Jared Cannonier 30-27 x3: dropped him in R1, then took him down at will in R2 and R3, mounted him "
             "repeatedly and took his back without finding the finish. Fourth straight win.",
        add_patterns=["Takedowns at will against veteran strikers; repeated mounts and back takes"]),
    "jared-cannonier": dict(src=SHERDOG,
        text="Lost to Ikram Aliskerov 30-27 x3 at 42: dropped in R1 and then taken down and controlled in R2 and R3; now "
             "1-5 in his last six.",
        add_concerns=["No answer to takedowns at 42 (Aliskerov)"]),
    "santiago-luna": dict(src=SHERDOG,
        text="Beat Aleksandre Topuria by split decision (30-27, 28-29, 29-28); all three Sherdog scorers had him winning "
             "every round on combinations, pressure and collar-tie uppercuts. Dropped once by a right hand in R1.",
        add_patterns=["High-volume combinations (four to six punches) and collar-tie uppercuts under pressure"]),
    "aleksandre-topuria": dict(src=SHERDOG,
        text="Lost a split decision to Santiago Luna after a year out: dropped him in R1 and kicked well, but out-landed in "
             "every round and attempted only one clinch takedown.",
        add_concerns=["Did not wrestle at all against a pressure striker after a year out (Luna)"]),
    "tallison-teixeira": dict(src=SHERDOG,
        text="Beat Shamil Gaziev by unanimous decision (30-27, 29-28, 29-28) on kicks from range after losing R1 and being "
             "sat down by a one-two.",
        add_patterns=["Can win a three-round decision from range with kicks and jabs (Gaziev)"]),
    "shamil-gaziev": dict(src=SHERDOG,
        text="Lost to Tallison Teixeira by unanimous decision: won R1 with a knockdown and clinch pressure, then threw very "
             "little in R2 and R3 and was warned for grabbing the fence.",
        add_concerns=["Output collapses after R1 (Teixeira)"]),
    "amir-albazi": dict(src=CAGESIDE_ALBAZI,
        text="Submitted Alessandro Costa with a rear-naked choke at 4:34 of R3 after being dropped in R2 and docked a point "
             "for grabbing the fence; his first win in three years.",
        add_patterns=["Back-take and one-armed choke from a takedown when behind late (Costa)"],
        add_concerns=["Hurt and out-struck for two rounds after a long layoff (Costa)"]),
    "alessandro-costa": dict(src=CAGESIDE_ALBAZI,
        text="Submitted by Amir Albazi at 4:34 of R3 while ahead: dropped Albazi in R2, then was taken down off a slip and "
             "choked from the back.",
        add_concerns=["Gave up the back and a late choke while ahead on the cards (Albazi)"]),
    "tahir-abdullayev": dict(src=SHERDOG,
        text="Beat Jake Matthews by unanimous decision (30-27, 30-27, 29-28) after missing weight by a pound: hurt him with a "
             "right hand in R1 and took him down in every round, with elbows from side control.",
        add_patterns=["Takedowns in every round and heavy top control against a veteran grappler (Matthews)"],
        add_concerns=["Missed weight by a pound for his second UFC fight"]),
    "jake-matthews": dict(src=SHERDOG,
        text="Lost to Tahir Abdullayev by unanimous decision: hurt in R1 and taken down in every round; his triangle and "
             "kimura attempts from the bottom went nowhere.",
        add_concerns=["Taken down and held in every round by a heavier grappler (Abdullayev)"]),
    "dom-mar-fan": dict(src=SHERDOG,
        text="Beat Nikolas Motta 30-26, 29-27, 29-27: a takedown inside 20 seconds and a full round of ground and pound, then "
             "the better striking in R2 and R3 despite a knockdown from Motta's left hook.",
        add_patterns=["Early takedowns and sustained ground and pound; good jab and head kick"],
        add_concerns=["Dropped by a left hook in R2 (Motta)"]),
    "nikolas-motta": dict(src=SHERDOG,
        text="Lost to Dom Mar Fan by unanimous decision after 17 months out: controlled through R1, dropped Fan in R2 but "
             "took heavy damage, including a clean head kick he walked through; checked by the doctor before R3.",
        add_patterns=["Durable chin after his jaw surgery (walked through Fan's head kick)"],
        add_concerns=["No answer off his back (Fan)"]),
    "diyar-nurgozhay": dict(src=SHERDOG,
        text="Stopped the debutant Alik Lorenz at 0:24 of R2 with a left head kick and hammerfists after taking him down "
             "twice in R1.",
        add_patterns=["Left head kick finish; takedowns against strikers"]),
    "alik-lorenz": dict(src=SHERDOG,
        text="Lost his UFC debut to Diyar Nurgozhay by TKO (head kick and punches) at 0:24 of R2 after spending most of R1 "
             "on his back."),
    "john-mitchell": dict(src=SHERDOG,
        text="Knocked out Shoaib Yousaf at 3:50 of R1 in his UFC debut on three days' notice: rocked early, then dropped him "
             "with a knee off the clinch and finished with punches.",
        add_patterns=["Knees and elbows from the clinch; finished after being hurt"]),
    "shoaib-yousaf": dict(src=SHERDOG,
        text="Knocked out by John Mitchell at 3:50 of R1 in his UFC debut on three days' notice, his first stoppage loss, "
             "after hurting Mitchell early.",
        add_concerns=["Walked into knees from the clinch (Mitchell)"]),
}

REVIEW = """A good card for the model: 8 of 12 winners with a log loss of 0.602, against the market's 8 of 12 at 0.655, and the blend picked 9. On the season the market still leads clearly: 0.584 on 478 priced bouts against the model's 0.640 on the same bouts. AI Picks scored 29 points to the model's 28, and the season stands at 213 to 201. AI Bets won $2.85: Aliskerov and Hooker by decision cashed and Matthews by decision lost. The bankroll is $87.34.

The card's lesson was where the model's thin-data warnings were wrong. I overrode it on Topuria and Matthews because its numbers rested on short or patchy records, and both overrides lost. Luna out-landed Topuria in every round on Sherdog's cards, and Abdullayev took Matthews down in every round. The regional records the model trusted were right; the market (71% and 69%) and the pundits were wrong. The Hooker override, built on Ortega's layoff, withdrawals and move up in weight, was the one that worked: a clear 30-27 sweep and Ortega's retirement. The overrides are now 9 right in 15, still short of the 30 needed to judge them.

The finishes went to the fighters who were winning the exchanges, not to the ones with the bigger records. Stirling's counter right hook at 4:58 of round 2 matched the pick exactly. Vallejos-Sterling was a disputed decision: all three Sherdog scorers had Sterling, so the miss on method there is noise, not a model failure. The clear misses to learn from are Mitchell knocking out Yousaf, who had never been stopped, and Albazi's comeback choke while behind; neither was a decision, as we had them. Teixeira, the model's pick against the market, won on kicks from range, not with the early finish we expected; Gaziev's output after round 1 was the real story. Horiguchi won from his back with guillotine threats and bottom work; the read on his takedown defence failed, but the result held. No owner's notes for this card."""


def main():
    f = ROOT / "recaps" / f"{ID}.json"
    doc = json.loads(f.read_text())
    cov = doc["coverage"]
    assert set(STORIES) == set(cov), set(cov) ^ set(STORIES)
    for k, s in STORIES.items():
        c = cov[k]
        srcs = [{"outlet": o["outlet"], "url": o["url"], **({"round_scores": c["round_scores"]} if o["outlet"] == "Sherdog" and c.get("round_scores") else {})}
                for o in c["outlets"]]
        st = {"summary": s["summary"], **({"turning_point": s["turning_point"]} if s.get("turning_point") else {}), "sources": srcs,
              "written": WRITTEN, "verdict": s["verdict"], "checks": s["checks"]}
        if s.get("single_source"):
            st["single_source"] = True
        doc["stories"][k] = st
    assert len(doc["stories"]) == len(cov), (len(doc["stories"]), len(cov))
    f.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")

    fn = ROOT / "fight_notes.json"
    notes = [n for n in json.loads(fn.read_text()) if n.get("date") != DATE]
    for k, a, b, cat, r, sk, nt in NOTES:
        src = "; ".join(dict.fromkeys(o["url"] for o in cov[k]["outlets"]))
        notes.append({"date": DATE, "fighter": a, "opponent": b, "category": cat, "rating": r, "skills": sk, "note": nt, "source": src})
    fn.write_text(json.dumps(notes, ensure_ascii=False, indent=1) + "\n")

    albazi_src = next(o["url"] for o in cov["amir-albazi-alessandro-costa"]["outlets"] if o["outlet"] == "Cageside Press")
    for slug, r in REPORTS.items():
        rf = ROOT / "reports" / f"{slug}.json"
        raw = rf.read_text()
        rep = json.loads(raw)
        src = albazi_src if r["src"] == CAGESIDE_ALBAZI else r["src"]
        rep["news"] = [n for n in rep.get("news", []) if n.get("date") != DATE] + [{"date": DATE, "text": r["text"], "source": src}]
        for field in ("patterns", "concerns"):
            lines = list(rep.get(field, []))
            lines += [x for x in r.get(f"add_{field}", []) if x not in lines]
            rep[field] = lines
        rep["updated"] = UPDATED
        rf.write_text(json.dumps(rep, ensure_ascii=raw.isascii(), indent=1) + "\n")

    out = Path(__file__).resolve().parents[3] / ".cache" / "recap_review.json"
    out.write_text(json.dumps({"event": EVENT, "date": DATE, "review": REVIEW, "notes_used": False, "written": WRITTEN,
                               "stories": doc["stories"]}, ensure_ascii=False))
    print(len(doc["stories"]), "stories;", len(NOTES), "fight notes;", len(REPORTS), "reports; review ->", out)


if __name__ == "__main__":
    main()
