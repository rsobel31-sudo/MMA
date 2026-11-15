"""Card review for UFC 334: Gane vs. Hokit (Madison Square Garden, 2026-11-14).

What happened in every bout (our own words, from Sherdog's play-by-play and round scoring, and the recaps the sweep
collected: MMA Mania, LowKick MMA, BJPenn.com, Cageside Press, MMA Junkie and Uncrowned through Yahoo), the pre-fight
claims checked against the fights, judged performances for data/scouting/fight_notes.json where two outlets agree, and a
dated note in both fighters' scouting reports. Written Sunday 2026-11-15.

Uroš Medić vs Kevin Holland was a majority draw (Bruce Buffer first read the wrong scores, per Uncrowned and Cageside
Press); it is not in the recap or the scores, but both reports get a note. Diaz-Heili's read was written under
"Alateng Heili", so the packet did not attach it; its claims are checked here by hand.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = "2026-11-14-ufc-334-gane-vs-hokit"
EVENT, DATE, WRITTEN = "UFC 334 - Gane vs. Hokit", "2026-11-14", "2026-11-15"
UPDATED = "2026-11-15T19:00:00+00:00"
SHERDOG = "https://www.sherdog.com/news/news/UFC-334-Gane-vs-Hokit-playbyplay-results-round-scoring-203625"
CAGESIDE_DRAW = "https://cagesidepress.com/2026/11/14/kevin-holland-vs-uros-medic-ends-in-bizarre-majority-draw/"


def chk(by, claim, tag, favoured, verdict, note):
    return {"by": by, "claim": claim, "tag": tag, "favoured": favoured, "verdict": verdict, "note": note}


GANE, HOKIT = "Ciryl Gane", "Josh Hokit"
KAYLA, NUNES = "Kayla Harrison", "Amanda Nunes"
CAIO, YOUSRI = "Caio Borralho", "Yousri Belgaroui"
GURULE, HASAN = "Luis Gurule", "Bilal Hasan"
WONDER, RADTKE = "Stephen Thompson", "Charles Radtke"
DUNCAN, DOBER = "Chris Duncan", "Drew Dober"
TMCK, MILLER = "Terrance McKinney", "Jim Miller"
ALMEIDA, DJ = "Cesar Almeida", "Donte Johnson"
COSTA, GORDON = "Melquizael Costa", "Jared Gordon"
BIA, MACY = "Beatriz Mesquita", "Macy Chiasson"
DIAZ, HEILI = "Juan Diaz", "Heili Alateng"
ELDER, SANCHES = "Evan Elder", "Samuel Sanches"

STORIES = {
    "ciryl-gane-josh-hokit": dict(
        summary="Hokit shot in the first seconds and then marched forward through Gane's jabs and uppercuts, slamming him "
                "late in round 1; Sherdog's scorers still gave Gane the round on the cleaner shots. Gane stopped kicking for "
                "fear of the takedown and spent his energy moving, and Hokit took rounds 2 and 3 with right hands, clinch "
                "elbows and foot stomps. Hokit had little left from round 4; Gane's knees, uppercuts and body work took the "
                "last two rounds, and he won 48-47 on all three cards, as all three Sherdog scorers had it.",
        turning_point="Round 4: Hokit's shots lost their steam and Gane took over in the clinch with knees and short uppercuts.",
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "Gane's footwork and reach keep an undersized wrestler at range; Hokit has never gone past 15 "
                "minutes; Gane over five rounds", "cardio", GANE, "mixed",
                "Right result and method, but Gane did not keep him at range: Hokit won rounds 2 and 3 up close. What "
                "decided it was Hokit fading in his first five-rounder."),
            chk("read", "Gane's range and movement", "range", GANE, "mixed",
                "His jab and uppercuts landed all night, but he gave up kicks and the movement tired him by round 2."),
            chk("read", "Hokit's wrestling and power (against)", "wrestling", HOKIT, "held",
                "A takedown in the first seconds, a slam in round 1, and pressure that won him two rounds."),
            chk("read", "Hokit's first five-rounder", "cardio", GANE, "held",
                "Out of steam from round 4; lost the last two rounds on every card."),
            chk("model", "Overall rating favours Gane", "overall", GANE, "held", "Won, narrowly."),
            chk("model", "Fight Matrix rating favours Gane", "outside_rating", GANE, "held", "Won, narrowly."),
            chk("model", "Wrestling edge favours Hokit", "wrestling_edge", HOKIT, "held",
                "Two takedowns and a slam; Gane defended the late attempts once Hokit tired."),
            chk("model", "Striking rating favours Gane", "striking_rating", GANE, "mixed",
                "The cleaner striker, but out-landed in rounds 2 and 3."),
            chk("model", "Reach favours Gane", "reach", GANE, "mixed", "The jab worked; the range game didn't hold."),
        ]),
    "kayla-harrison-amanda-nunes": dict(
        summary="Nunes started fast, catching Harrison with both hands each time she reached for the clinch and sprawling "
                "on her first shot, before Harrison threw her and finished round 1 in a crucifix. Nunes chose to clinch and "
                "grapple in round 2 and was thrown into the same position again; in round 3 she took Harrison down and got "
                "her back before Harrison reversed and cut her with an elbow. Both were exhausted in round 4; Harrison "
                "caught a kick, tripped Nunes, took her back and choked her at 1:29.",
        turning_point="Round 4: Harrison caught Nunes's kick, tripped her and took her back for the choke within seconds.",
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "Harrison's body lock and top pressure win once Nunes's dangerous first round has passed: "
                "submission, R2", "grappling", KAYLA, "held",
                "Her throws and crucifix won rounds 1 to 3 and the choke came off a caught kick, but in round 4, not 2."),
            chk("read", "Nunes's layoff", "inactivity", KAYLA, "failed",
                "No rust on the feet: she hurt Harrison repeatedly in round 1 and again in round 4."),
            chk("read", "Harrison's neck surgery and layoff", "inactivity", NUNES, "mixed",
                "No sign of the neck, but Harrison was badly tired from round 3."),
            chk("read", "Harrison's grappling", "grappling", KAYLA, "held",
                "Throws, crucifix and a back take; Nunes only got on top once."),
            chk("model", "Fresher body favours Harrison", "wear_and_tear", KAYLA, "mixed",
                "Both were spent by round 4; Harrison's grappling, not freshness, won it."),
            chk("model", "Layoff favours Harrison", "layoff", KAYLA, "failed", "Nunes looked as sharp as ever standing."),
            chk("model", "Striking rating favours Nunes", "striking_rating", NUNES, "held",
                "Won every standing exchange; lost the fight by choosing to grapple."),
            chk("model", "Submission threat favours Harrison", "submission_threat", KAYLA, "held",
                "Rear-naked choke in round 4."),
        ]),
    "caio-borralho-yousri-belgaroui": dict(
        summary="Borralho closed behind one-twos and took the 6-foot-6 kickboxer down inside the first minute, took his "
                "back with a body triangle and hunted a neck crank and a guillotine. He did the same in rounds 2 and 3, "
                "taking a few hard body kicks and knees in between, and won 30-27 on every card and all three Sherdog "
                "scorers' cards.",
        turning_point=None,
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Belgaroui has never faced a grappler like this; Borralho wins by control for three rounds",
                "wrestling", CAIO, "held", "A takedown in every round and long spells on the back and in side control."),
            chk("read", "Borralho's wrestling", "wrestling", CAIO, "held", "Took him down in all three rounds."),
            chk("read", "Belgaroui's striking (against)", "striking", YOUSRI, "mixed",
                "His body kicks and knees landed in the open, but he spent most of the fight underneath."),
            chk("read", "Borralho's rib surgery (against)", "injury", YOUSRI, "failed",
                "Ate several hard body kicks and knees without slowing."),
            chk("model", "Fight Matrix rating favours Borralho", "outside_rating", CAIO, "held", "30-27 x3."),
            chk("model", "Wrestling rating favours Borralho", "wrestling_rating", CAIO, "held", "Takedowns at will."),
            chk("model", "Overall rating favours Borralho", "overall", CAIO, "held", "30-27 x3."),
        ]),
    "luis-gurule-bilal-hasan": dict(
        summary="Hasan won round 1 with spinning back kicks, head kicks and knees, though Gurule knocked him off balance "
                "with an overhand right. Gurule's pressure and a late double-leg took round 2 on two Sherdog cards, and in "
                "round 3 he took Hasan down inside the first minute and held him there with short punches and elbows, "
                "bleeding from an elbow cut, for the rest of the fight. Gurule won a split decision (28-29, 29-28, 29-28) as "
                "the night's biggest underdog.",
        turning_point="Round 3: Gurule's takedown inside the first minute, held for four minutes.",
        verdict="wrong, close fight",
        checks=[
            chk("pick", "Gurule's wrestling slows Hasan early; Hasan's kicks find him once the shots dry up: KO/TKO, R2",
                "wrestling", HASAN, "failed",
                "Gurule's shots never dried up: his takedowns won rounds 2 and 3."),
            chk("read", "Hasan's form", "form", HASAN, "mixed", "Dominant on the feet in round 1; no answer off his back."),
            chk("read", "Hasan's quick turnaround (against)", "activity", GURULE, "untested",
                "Nothing showed it; he lost on the mat, not from fatigue."),
            chk("model", "Overall rating favours Hasan", "overall", HASAN, "failed", "Lost a split decision."),
            chk("model", "Striking rating favours Hasan", "striking_rating", HASAN, "held",
                "Out-struck Gurule on the feet in every exchange."),
            chk("model", "Wrestling rating favours Hasan", "wrestling_rating", HASAN, "failed",
                "Taken down in rounds 2 and 3 and could not get up."),
            chk("model", "Fresher body favours Hasan", "wear_and_tear", HASAN, "untested", "No sign either way."),
            chk("model", "Striking exchange favours Gurule", "striking_exchange", GURULE, "failed",
                "Lost the standing exchanges; won on the mat."),
        ]),
    "stephen-thompson-charles-radtke": dict(
        summary="Radtke took round 1 with a double-leg and long clinch work against the fence, and took Thompson down again "
                "early in round 2, but his output dropped and Thompson finished the round with kicks and three-punch "
                "combinations. In round 3 Thompson landed a hook kick, combinations and body kicks against a tiring Radtke, "
                "then dropped him with a spinning wheel kick and the referee stopped it at 2:54, ending his career with a "
                "$100,000 bonus.",
        turning_point="Late in round 2: Radtke's output dropped after his second takedown and Thompson took over.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Thompson is 43, 16 months out and lost the grappling in his three recent losses; Radtke's "
                "takedowns and control win: decision", "wrestling", RADTKE, "failed",
                "Radtke's takedowns won round 1, but he faded by the end of round 2 and was knocked out in round 3."),
            chk("read", "Thompson's age and layoff", "inactivity", RADTKE, "failed",
                "Thompson was the fresher man from round 2 on."),
            chk("read", "Radtke's takedowns", "wrestling", RADTKE, "mixed",
                "Two early takedowns, but Thompson got up quickly each time and stuffed the late ones."),
            chk("read", "Radtke's chin against strikers (against)", "durability", WONDER, "held",
                "Knocked out by a striker for the third time in the UFC."),
            chk("model", "Fresher body favours Radtke", "wear_and_tear", RADTKE, "failed",
                "Radtke faded; the 43-year-old finished strong."),
            chk("model", "Age favours Radtke", "age_curve", RADTKE, "failed", "Knocked out by the older man."),
            chk("model", "Striking rating favours Thompson", "striking_rating", WONDER, "held", "Spinning wheel kick KO."),
            chk("model", "Fight Matrix rating favours Thompson", "outside_rating", WONDER, "held", "Won."),
            chk("model", "Overall rating favours Thompson", "overall", WONDER, "held", "Won."),
        ]),
    "chris-duncan-drew-dober": dict(
        summary="Duncan kicked Dober at every level, buckled him with a right hook in round 1 and marked up his right eye, "
                "then won round 2 with straight rights and kicks. Dober pressed in round 3 behind his left hand and won it "
                "on Sherdog's cards, but Duncan took him down late to see it out. Duncan won 30-27, 30-27, 29-28.",
        turning_point=None,
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "Duncan's front-headlock chokes catch Dober in a scramble: submission, R2", "submission", DUNCAN,
                "failed", "Won on kicks and right hands; no choke attempts, one late takedown."),
            chk("read", "Dober's power", "power", DOBER, "mixed",
                "Landed his left hand in round 3, but never hurt Duncan."),
            chk("read", "Duncan's form", "form", DUNCAN, "held", "Clear on two rounds and won the decision."),
            chk("model", "Fresher body favours Duncan", "wear_and_tear", DUNCAN, "mixed",
                "Duncan slowed in round 3 and Dober won it."),
            chk("model", "Wrestling rating favours Duncan", "wrestling_rating", DUNCAN, "mixed",
                "One late takedown; it was a striking fight."),
            chk("model", "Wrestling edge favours Duncan", "wrestling_edge", DUNCAN, "mixed", "Barely used."),
            chk("model", "Age favours Duncan", "age_curve", DUNCAN, "held", "Faster and busier for two rounds."),
            chk("model", "Experience favours Dober", "experience", DOBER, "failed", "Lost two rounds clearly."),
        ]),
    "terrance-mckinney-jim-miller": dict(
        summary="After a short feeling-out spell, McKinney landed a one-two and an uppercut, Miller answered with hooks and "
                "a counter left, and then McKinney dropped him with a straight left and finished him with follow-up shots at "
                "1:53 of round 1. McKinney had missed weight by 4.2 lb and said afterwards he is moving to welterweight.",
        turning_point=None,
        verdict="right, for our reasons",
        checks=[
            chk("pick", "McKinney wins in R1 or not at all; the model's decision pick doesn't fit him: KO/TKO, R1",
                "early_finish", TMCK, "held", "TKO at 1:53 of round 1."),
            chk("read", "McKinney's 4.2 lb miss and bad cut", "weight_cut", MILLER, "untested",
                "Ended before any fade could show; the weight may have helped his power."),
            chk("read", "McKinney's fade after round one", "cardio", MILLER, "untested", "Never got past round 1."),
            chk("read", "Miller's submissions in scrambles", "submission", MILLER, "untested", "No scramble happened."),
            chk("read", "McKinney's first-round power (against)", "power", TMCK, "held", "Dropped and finished him."),
            chk("read", "Miller's age (against)", "age", TMCK, "held", "Couldn't match McKinney's speed."),
            chk("model", "Fresher body favours McKinney", "wear_and_tear", TMCK, "untested", "Ended in round 1."),
            chk("model", "Age favours McKinney", "age_curve", TMCK, "held", "Faster and sharper."),
            chk("model", "Wrestling edge favours McKinney", "wrestling_edge", TMCK, "untested", "No grappling."),
            chk("model", "Overall rating favours Miller", "overall", MILLER, "failed", "Knocked out in round 1."),
            chk("model", "Submission threat favours Miller", "submission_threat", MILLER, "untested", "Never on the mat."),
        ]),
    "cesar-almeida-donte-johnson": dict(
        summary="The unbeaten Johnson charged forward with leg kicks, a Superman punch and big right hands, while Almeida "
                "circled and found his timing with hooks to the head and body. Almeida floored him with a straight right, "
                "let him back up, and dropped him again with a right hook to stop it at 3:20 of round 1: Johnson's first loss.",
        turning_point="The first knockdown: Johnson ran onto Almeida's straight right.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Almeida is 38 and was knocked out in R1 last time; the bigger, younger man walks him down: "
                "KO/TKO, R1", "durability", DJ, "failed",
                "Johnson walked him down and ran onto the counter; Almeida knocked him out instead."),
            chk("read", "Almeida's age and recent KO loss", "age", DJ, "failed",
                "Almeida's kickboxing timing beat Johnson's aggression."),
            chk("model", "Fresher body favours Johnson", "wear_and_tear", DJ, "untested", "Ended in round 1."),
            chk("model", "Age favours Johnson", "age_curve", DJ, "failed", "The 38-year-old won in round 1."),
            chk("model", "Overall rating favours Johnson", "overall", DJ, "failed", "Knocked out."),
            chk("model", "Wrestling edge favours Johnson", "wrestling_edge", DJ, "untested", "He never tried to wrestle."),
            chk("model", "Height favours Almeida", "height", ALMEIDA, "held", "Countered from range as Johnson came in."),
        ]),
    "melquizael-costa-jared-gordon": dict(
        summary="Costa kicked Gordon at every level in round 1 and stung him with a head kick and left hook. Gordon took "
                "round 2 with takedowns, surviving a triangle and an armbar from Costa's guard, and kept wrestling in round "
                "3, but Costa won the stand-up between takedowns with uppercuts and body shots and countered with a "
                "kneebar at the bell. Costa won 29-28 on every card.",
        turning_point="Round 3: Costa's uppercuts and body work between Gordon's takedowns.",
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "Costa's body kicks break the 38-year-old Gordon late: KO/TKO, R3", "body_work", COSTA, "mixed",
                "The kicks won round 1 and his body shots helped win round 3, but Gordon was never close to being stopped."),
            chk("read", "Gordon's form", "form", COSTA, "mixed", "Gordon won round 2 and made round 3 close."),
            chk("read", "Costa's move up in weight", "weight_class", GORDON, "mixed",
                "Taken down repeatedly by a lightweight, but never controlled for long."),
            chk("model", "Fresher body favours Costa", "wear_and_tear", COSTA, "held", "Stronger in the last two minutes."),
            chk("model", "Submission threat favours Costa", "submission_threat", COSTA, "mixed",
                "Triangle, armbar and kneebar attempts; none finished."),
            chk("model", "Fight Matrix rating favours Costa", "outside_rating", COSTA, "held", "Won."),
            chk("model", "Age favours Costa", "age_curve", COSTA, "held", "Won."),
            chk("model", "Overall rating favours Costa", "overall", COSTA, "held", "Won."),
        ]),
    "beatriz-mesquita-macy-chiasson": dict(
        summary="Mesquita walked down the much taller Chiasson, got behind her and took her down, then passed to mount, "
                "took the back, landed a heavy elbow and punches, and finished with a rear-naked choke inside a body "
                "triangle at 3:23 of round 1. Mesquita is now 9-0.",
        turning_point=None,
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Chiasson's height keeps R1 on the feet; Mesquita gets the back in R2: submission, R2",
                "grappling", BIA, "mixed", "Right about the grappling; wrong about the round: done in round 1."),
            chk("read", "Mesquita's grappling", "grappling", BIA, "held", "Takedown, mount, back, choke."),
            chk("read", "Chiasson's size (against)", "size", MACY, "failed", "The reach made no difference."),
            chk("model", "Wrestling rating favours Mesquita", "wrestling_rating", BIA, "held", "Took her down at will."),
            chk("model", "Height favours Chiasson", "height", MACY, "failed", "No effect."),
            chk("model", "Overall rating favours Mesquita", "overall", BIA, "held", "Won in round 1."),
            chk("model", "Fresher body favours Mesquita", "wear_and_tear", BIA, "untested", "Ended in round 1."),
            chk("model", "Submission threat favours Mesquita", "submission_threat", BIA, "held", "Rear-naked choke."),
        ]),
    "juan-diaz-heili-alateng": dict(
        summary="Diaz controlled all 15 minutes with his jab, one-twos and body work, mixing in knees and elbows from the "
                "clinch and piling damage on Heili's face. Heili had his only moment in the last minute, a right uppercut "
                "that staggered Diaz. Diaz won 30-27 on every card and all three Sherdog scorers' cards.",
        turning_point=None,
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Heili on eight days' notice; he is durable, so Diaz wins on the cards", "short_notice", DIAZ,
                "held", "Diaz won every round; Heili was never in danger of being stopped."),
            chk("read", "Heili's short notice", "short_notice", DIAZ, "held", "A step behind on the feet for three rounds."),
            chk("read", "Heili's durability (against)", "durability", HEILI, "held", "Took a lot and went the distance."),
            chk("model", "Fresher body favours Diaz", "wear_and_tear", DIAZ, "held", "Busier in round 3."),
            chk("model", "Overall rating favours Diaz", "overall", DIAZ, "held", "30-27 x3."),
            chk("model", "Wrestling edge favours Diaz", "wrestling_edge", DIAZ, "untested", "A striking fight."),
            chk("model", "Wrestling rating favours Diaz", "wrestling_rating", DIAZ, "mixed",
                "Defended Heili's one takedown attempt; never shot himself."),
            chk("model", "Fight Matrix rating favours Diaz", "outside_rating", DIAZ, "held", "Won."),
        ]),
    "evan-elder-samuel-sanches": dict(
        summary="Elder staggered Sanches with a left hook in the opening exchange, took him down, and dropped him with a "
                "right hand at the end of round 1. Sanches put Elder down with a straight right in round 2, but Elder "
                "answered and took him down again. In round 3 Elder took him down three more times, Sanches lost a point "
                "for grabbing the fence, and Elder won 30-26 on every card.",
        turning_point=None,
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Close; the younger, harder-hitting Sanches against Elder after 19 months out; Elder isn't "
                "stopped, so a decision", "inactivity", SANCHES, "failed",
                "Right that it went the distance; wrong winner. Elder's wrestling decided it."),
            chk("read", "Elder's layoff", "inactivity", SANCHES, "failed", "No rust: Elder won every round."),
            chk("read", "Sanches's debut", "debut", ELDER, "held", "Looked unsure against the takedowns."),
            chk("model", "Striking rating favours Sanches", "striking_rating", SANCHES, "mixed",
                "Dropped Elder once, but was dropped himself in round 1."),
            chk("model", "Power vs chin favours Sanches", "power_vs_chin", SANCHES, "mixed",
                "Put Elder down in round 2; Elder got up and won the round."),
            chk("model", "Wrestling edge favours Sanches", "wrestling_edge", SANCHES, "failed",
                "Taken down five times."),
        ]),
}

# (bout key, fighter, opponent, category, rating, skills, note): where two outlets agree.
NOTES = [
    ("ciryl-gane-josh-hokit", HOKIT, GANE, "wrestling", 1.0, ["td_off", "clinch", "pressure"],
     "Took Gane down early, slammed him in round 1 and won rounds 2 and 3 with clinch pressure, but faded from round 4."),
    ("ciryl-gane-josh-hokit", GANE, HOKIT, "striking", 1.0, ["jab", "uppercut", "body", "cardio"],
     "Jab and uppercuts landed all fight and he took the last two rounds with knees and body work once Hokit tired; gave up "
     "his kicks for fear of the takedown."),
    ("kayla-harrison-amanda-nunes", KAYLA, NUNES, "grappling", 2.0, ["throws", "crucifix", "back_take", "choke"],
     "Threw Nunes into a crucifix in rounds 1 and 2 and took her back for the choke in round 4."),
    ("kayla-harrison-amanda-nunes", NUNES, KAYLA, "striking", 1.0, ["boxing", "counters"],
     "Hurt Harrison with both hands every time she reached for the clinch in round 1, and again in round 4."),
    ("caio-borralho-yousri-belgaroui", CAIO, YOUSRI, "wrestling", 2.0, ["td", "back_take", "control"],
     "A takedown in every round, the back with a body triangle in round 1, side control in round 2."),
    ("stephen-thompson-charles-radtke", WONDER, RADTKE, "striking", 2.0, ["kicks", "combinations", "spinning"],
     "Took over from late in round 2 with kicks and combinations and knocked him out with a spinning wheel kick."),
    ("terrance-mckinney-jim-miller", TMCK, MILLER, "striking", 2.0, ["speed", "straight_left", "finishing"],
     "Faster from the start; dropped Miller with a straight left and finished him at 1:53."),
    ("cesar-almeida-donte-johnson", ALMEIDA, DJ, "striking", 2.0, ["counters", "timing", "power"],
     "Found his timing against the charging Johnson and knocked him down twice with right hands."),
]

REPORTS = {
    "ciryl-gane": dict(src=SHERDOG,
        text="Beat Josh Hokit by unanimous decision (48-47 x3) in his first title defence: won R1 on jabs and uppercuts, "
             "lost R2 and R3 to Hokit's pressure, then took over in R4 and R5 with knees, uppercuts and body work as Hokit "
             "faded. Gave up his kicks for fear of the takedown.",
        add_concerns=["Tires when made to move for long stretches; lost two rounds to a smaller pressure fighter (Hokit)"]),
    "josh-hokit": dict(src=SHERDOG,
        text="Lost to Ciryl Gane by unanimous decision (48-47 x3), his first pro loss: an early takedown and a slam in R1, "
             "won R2 and R3 with pressure, clinch elbows and foot stomps, then faded in his first five-round fight.",
        add_patterns=["Relentless forward pressure and clinch work that won two rounds from the heavyweight champion"],
        add_concerns=["Faded badly after R3 in his first five-round fight (Gane)"]),
    "kayla-harrison": dict(src=SHERDOG,
        text="Submitted Amanda Nunes with a rear-naked choke at 1:29 of R4 to defend her title: hurt on the feet in R1, "
             "then threw Nunes into a crucifix in R1 and R2, survived Nunes taking her back in R3, and caught a kick in "
             "R4 to take the back.",
        add_concerns=["Visibly exhausted from R3 in her second five-round fight; hurt repeatedly on the feet by Nunes"]),
    "amanda-nunes": dict(src=SHERDOG,
        text="Submitted by Kayla Harrison (rear-naked choke) at 1:29 of R4 in her first fight since 2023: won the stand-up "
             "and hurt Harrison in R1 and R4, but chose to clinch and grapple and was thrown into a crucifix in R1 and R2."),
    "caio-borralho": dict(src=SHERDOG,
        text="Beat Yousri Belgaroui by unanimous decision (30-27 x3): a takedown in every round, the back with a body "
             "triangle in R1, and side control in R2; no sign of the rib injury."),
    "yousri-belgaroui": dict(src=SHERDOG,
        text="Lost to Caio Borralho by unanimous decision (30-27 x3), his first UFC loss: taken down in every round and "
             "held on the mat; landed hard body kicks and knees in the open.",
        add_concerns=["Could not stop or get up from a ranked grappler's takedowns (Borralho, every round)"]),
    "luis-gurule": dict(src=SHERDOG,
        text="Upset Bilal Hasan by split decision (28-29, 29-28, 29-28): lost R1 on the feet, then took him down late in "
             "R2 and early in R3 and held him there with short punches and elbows."),
    "bilal-hasan": dict(src=SHERDOG,
        text="Lost to Luis Gurule by split decision, his first pro loss: won R1 with spinning kicks and head kicks, then "
             "was taken down in R2 and R3 and could not get up.",
        add_concerns=["No answer off his back to a wrestler's takedowns (Gurule, R2-R3)"]),
    "stephen-thompson": dict(src=SHERDOG,
        text="Knocked out Charles Radtke with a spinning wheel kick at 2:54 of R3 in his retirement fight, after losing R1 "
             "to Radtke's takedowns and clinch work; took over late in R2 as Radtke tired."),
    "charles-radtke": dict(src=SHERDOG,
        text="Knocked out by Stephen Thompson's spinning wheel kick at 2:54 of R3: won R1 with a takedown and clinch work, "
             "took him down again in R2, then faded.",
        add_concerns=["Output dropped sharply after R1 against a striker; knocked out by strikers in all three UFC losses"]),
    "chris-duncan": dict(src=SHERDOG,
        text="Beat Drew Dober by unanimous decision (30-27, 30-27, 29-28): buckled him with a right hook and kicked him at "
             "every level in R1 and R2, slowed in R3 and took him down late to see it out."),
    "drew-dober": dict(src=SHERDOG,
        text="Lost to Chris Duncan by unanimous decision (30-27, 30-27, 29-28): buckled and marked up in R1, out-kicked in "
             "R2, won R3 with his left hand."),
    "terrance-mckinney": dict(src=SHERDOG,
        text="Knocked out Jim Miller at 1:53 of R1 after missing weight by 4.2 lb (160.2); says he moves to welterweight "
             "next."),
    "jim-miller": dict(src=SHERDOG,
        text="Knocked out by Terrance McKinney at 1:53 of R1: dropped by a straight left after landing hooks of his own."),
    "cesar-almeida": dict(src=SHERDOG,
        text="Knocked out the unbeaten Donte Johnson at 3:20 of R1: timed him with a straight right as he charged, then "
             "dropped him again with a right hook.",
        add_patterns=["Counters an aggressive opponent from range; knocked down Johnson twice in R1"]),
    "donte-johnson": dict(src=SHERDOG,
        text="Knocked out by Cesar Almeida at 3:20 of R1, his first loss: charged in with big right hands and ran onto a "
             "counter.",
        add_concerns=["Charges in on a straight line and gets countered (Almeida, R1)"]),
    "melquizael-costa": dict(src=SHERDOG,
        text="Beat Jared Gordon by unanimous decision (29-28 x3) back at lightweight: kicked him at every level in R1, "
             "lost R2 to takedowns while attacking triangles and armbars, and won R3 on the feet between takedowns."),
    "jared-gordon": dict(src=SHERDOG,
        text="Lost to Melquizael Costa by unanimous decision (29-28 x3): out-kicked in R1, won R2 with takedowns and kept "
             "wrestling in R3."),
    "beatriz-mesquita": dict(src=SHERDOG,
        text="Submitted Macy Chiasson with a rear-naked choke at 3:23 of R1 to go 9-0: took her down, mounted, took the "
             "back and choked her inside a body triangle."),
    "macy-chiasson": dict(src=SHERDOG,
        text="Submitted by Beatriz Mesquita (rear-naked choke) at 3:23 of R1: her height didn't keep Mesquita off; taken "
             "down, mounted and choked."),
    "juan-diaz": dict(src=SHERDOG,
        text="Beat Heili Alateng by unanimous decision (30-27 x3) after missing weight by 0.4 lb: controlled every round "
             "with the jab, one-twos and body work; briefly staggered by an uppercut late in R3."),
    "alateng-heili": dict(src=SHERDOG,
        text="Lost to Juan Diaz by unanimous decision (30-27 x3) on about eight days' notice: a step behind on the feet "
             "throughout, took a lot of damage and went the distance."),
    "evan-elder": dict(src=SHERDOG,
        text="Beat debutant Samuel Sanches by unanimous decision (30-26 x3) in his first fight in about 19 months: dropped "
             "him late in R1, was dropped himself in R2, and won with five takedowns and top control."),
    "samuel-sanches": dict(src=SHERDOG,
        text="Lost his UFC debut to Evan Elder by unanimous decision (30-26 x3): dropped Elder in R2 but was dropped in R1, "
             "taken down five times, and lost a point for grabbing the fence in R3.",
        add_concerns=["Taken down repeatedly and grabbed the fence in his UFC debut (Elder)"]),
    "uros-medic": dict(src=CAGESIDE_DRAW,
        text="Fought Kevin Holland to a majority draw; Bruce Buffer first read the wrong scores. Several outlets felt Holland "
             "had done enough to win."),
    "kevin-holland": dict(src=CAGESIDE_DRAW,
        text="Fought Uros Medic to a majority draw in his first fight since April; several outlets felt he had done enough "
             "to win."),
}

REVIEW = """A close card for the numbers: the model and the market both picked 8 winners (the model 8 of 12, log loss 0.679; the market 8 of 11, 0.682), and the blend did slightly worse (7 of 11, 0.703). On the season the market still leads clearly: 0.583 on 465 priced bouts against the model's 0.641 on the same bouts. AI Picks scored 26 points to the model's 29. Following the model on round and method would have scored more: Duncan won on the feet, not by the choke I picked, and Mesquita finished in round 1, not round 2. Calling McKinney's knockout in round 1 got back two of those points. AI Bets won $2.78: Gane by decision at +390 and Duncan cashed, and both Radtke bets lost.

The night's theme was what the stats can't see about late rounds. Gane-Hokit was the clearest case: Hokit's pressure took rounds 2 and 3, and the bet on Gane by decision rested on Hokit never having gone past 15 minutes. That claim held: he had nothing left from round 4. Harrison won as expected, but not as written. Nunes showed no rust and won every standing exchange, then chose to grapple and was thrown into a crucifix twice before the round-4 choke. The layoff factor the model leaned on failed for Nunes.

The misses that matter: Thompson's retirement knockout, where the model's two biggest drivers (fresher body and age, both for Radtke) failed. Radtke faded after his early takedowns, and the 43-year-old finished him with a spinning wheel kick. Almeida's knockout of the unbeaten Johnson was the same lesson as last week: a 38-year-old with a recent KO loss is not finished as a striker. Gurule over Hasan was a split decision, with Sherdog's three scorers split as well. It is a judging coin flip, but it exposed Hasan's game off his back. Elder over the debutant Sanches was a clear miss: the model's small wrestling lean for Sanches was backwards, and Elder's 19-month layoff didn't show. Medić-Holland was a majority draw and isn't scored. No owner's notes for this card."""


def main():
    f = ROOT / "recaps" / f"{ID}.json"
    doc = json.loads(f.read_text())
    cov = doc["coverage"]
    assert set(STORIES) == set(cov), set(cov) ^ set(STORIES)
    for k, s in STORIES.items():
        c = cov[k]
        srcs = [{"outlet": o["outlet"], "url": o["url"], **({"round_scores": c["round_scores"]} if o["outlet"] == "Sherdog" and c.get("round_scores") else {})}
                for o in c["outlets"] if not (o["outlet"] == "MMA Junkie" and o["kind"] == "play-by-play")]
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

    for slug, r in REPORTS.items():
        rf = ROOT / "reports" / f"{slug}.json"
        raw = rf.read_text()
        rep = json.loads(raw)
        rep["news"] = [n for n in rep.get("news", []) if n.get("date") != DATE] + [{"date": DATE, "text": r["text"], "source": r["src"]}]
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
