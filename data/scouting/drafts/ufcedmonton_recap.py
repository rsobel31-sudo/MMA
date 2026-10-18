"""Card review for UFC Fight Night 291: Buckley vs. Malott (UFC Edmonton, 2026-10-17).

What happened in every bout (our own words, from Sherdog's and MMA Mania's play-by-play and the outlets' recaps),
the pre-fight claims checked against the fights, judged performances for data/scouting/fight_notes.json, and the
review text for recap_reviews/<id>. Written Sunday 2026-10-18; the owner's fight-night notes are worked in.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = "2026-10-17-ufc-fight-night-291-buckley-vs-malott"
EVENT, DATE, WRITTEN = "UFC Fight Night 291 - Buckley vs. Malott", "2026-10-17", "2026-10-18"
SHERDOG = "https://www.sherdog.com/news/news/UFC-Edmonton-Buckley-vs-Malott-playbyplay-results-round-scoring-203257"
MANIA = "https://www.mmamania.com/ufc-results/478559/ufc-edmonton-live-results-highlights-play-by-play-malott-vs-buckley"


def chk(by, claim, tag, favoured, verdict, note):
    return {"by": by, "claim": claim, "tag": tag, "favoured": favoured, "verdict": verdict, "note": note}


STORIES = {
    "mike-malott-joaquin-buckley": dict(
        summary="A tight first round at range: Malott's body kicks and one-twos against Buckley's lunging right hooks, scored 2-1 "
                "Buckley by Sherdog's panel. Buckley clinched early in round 2 and Malott turned him on the fence and kneed the body; "
                "when they separated Buckley ducked in to throw and Malott timed a knee to the head that sent the mouthpiece flying, "
                "and a final right hand ended it at 2:32.",
        turning_point="Round 2: Buckley changed levels into the knee; Malott had been landing knees in the clinch moments earlier.",
        verdict="right, other reasons",
        checks=[
            chk("pick", "Malott's length and kicking at range, Buckley loses when he can't land the big shot", "style", "Mike Malott", "mixed",
                "Range was even in round 1 (Buckley took it on two of three cards); the fight was won in the clinch and on a counter knee."),
            chk("pick", "Decision: Malott's cardio past round three unproven", "durability", "Mike Malott", "failed",
                "Malott finished it in round 2; the five-round cardio question never came up."),
            chk("read", "Buckley's mid-fight power", "power", "Joaquin Buckley", "failed", "Buckley's best moments were round 1 right hooks; he was out in round 2."),
            chk("read", "Malott's five-round cardio (against)", "cardio", "Joaquin Buckley", "untested", "Over in round 2."),
            chk("model", "Fresher body favours Malott", "wear_and_tear", "Mike Malott", "held",
                "Buckley, with far more cage time and damage, was the one who couldn't take the shot."),
            chk("model", "Striking rating favours Buckley", "striking_rating", "Joaquin Buckley", "failed", "Malott landed the cleaner, fight-ending strikes."),
            chk("model", "Height favours Malott", "height", "Mike Malott", "held", "The knee came from Malott's height against a ducking opponent."),
            chk("model", "Fight Matrix rating favours Buckley", "outside_rating", "Joaquin Buckley", "failed", "The lower-rated fighter won clearly."),
            chk("model", "Grappling rating favours Malott", "grappling_rating", "Mike Malott", "untested", "Never went to the floor."),
        ]),
    "jasmine-jasudavicius-erin-blanchfield": dict(
        summary="Jasudavicius won the wrestling Blanchfield was supposed to own: she took Blanchfield down twice in round 1, took the back "
                "with a body triangle and cranked the neck to the horn, then did it again in round 2 after a single leg, finishing the round "
                "in mount. Blanchfield won round 3 on the feet with combinations before Jasudavicius dragged her down late: 29-28 on all three "
                "Sherdog cards and a unanimous decision.",
        turning_point="Round 1: Jasudavicius's second takedown and back take; from there the bigger woman controlled every grappling exchange.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Blanchfield's back takes punish the wrestling exchanges Jasudavicius needs", "wrestling_edge", "Erin Blanchfield", "failed",
                "Jasudavicius won every grappling exchange and took Blanchfield's back twice."),
            chk("read", "Blanchfield's grappling edge", "grappling", "Erin Blanchfield", "failed", "Out-grappled for two rounds."),
            chk("read", "Blanchfield's layoff and injury (against)", "inactivity", "Jasmine Jasudavicius", "mixed",
                "Blanchfield looked sharp standing in round 3; it was the size and grappling, not rust, that beat her."),
            chk("read", "Jasudavicius's disrupted camp", "camp", "Erin Blanchfield", "failed", "Jasudavicius looked prepared and strong for three rounds."),
            chk("model", "Overall rating favours Blanchfield", "overall", "Erin Blanchfield", "failed", "Lost two of three rounds clearly."),
            chk("model", "Fresher body favours Blanchfield", "wear_and_tear", "Erin Blanchfield", "untested", "No sign either fighter faded."),
            chk("model", "Age favours Blanchfield", "age_curve", "Erin Blanchfield", "failed", "The older fighter won the physical battle."),
            chk("model", "Fight Matrix rating favours Blanchfield", "outside_rating", "Erin Blanchfield", "failed", "Lost."),
            chk("model", "Striking rating favours Blanchfield", "striking_rating", "Erin Blanchfield", "held", "Blanchfield won the only round on the feet."),
        ]),
    "cristian-perez-kyle-nelson": dict(
        summary="Pérez opened with a rolling leglock attempt, stood up into a hard Nelson right hand that dropped him to a knee, and "
                "came straight back firing: a knee and a four-punch combination on the fence put Nelson down and hammerfists finished it at 0:27.",
        turning_point="Pérez absorbed Nelson's right hand and answered immediately instead of resetting.",
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Nelson stopped in round one in both recent losses; Pérez's chance and Nelson's worst both fall early", "durability", "Cristian Perez", "held",
                "Stopped in 27 seconds."),
            chk("read", "Nelson's recent first-round stoppages", "durability", "Cristian Perez", "held", "A third straight first-round stoppage loss."),
            chk("read", "Age", "age", "Cristian Perez", "held", "The 27-year-old took the bigger shot and recovered first."),
            chk("read", "Perez's late cardio (against)", "cardio", "Kyle Nelson", "untested", "Over in under half a minute."),
            chk("model", "Fresher body favours Pérez", "wear_and_tear", "Cristian Perez", "held", "Nelson couldn't take the follow-up."),
            chk("model", "Wrestling edge favours Pérez", "wrestling_edge", "Cristian Perez", "untested", "No wrestling."),
            chk("model", "Striking defence favours Nelson", "striking_defense", "Kyle Nelson", "failed", "Nelson was hit cleanly and finished."),
            chk("model", "Overall rating favours Pérez", "overall", "Cristian Perez", "held", "Won inside 30 seconds."),
            chk("model", "Age favours Pérez", "age_curve", "Cristian Perez", "held", "See the read."),
        ]),
    "marc-andre-barriault-kyle-daukaus": dict(
        summary="Daukaus took Barriault down, reached mount and the back with a body triangle and hunted the choke for two minutes, but "
                "Barriault broke the triangle and stood. When Daukaus shot again Barriault met him with a knee, then a second knee that "
                "dropped him, and elbows and punches on the turtled Daukaus brought the stoppage at 4:28 of round 1.",
        turning_point="Barriault's escape to his feet; Daukaus kept shooting into knees instead of resetting at range.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Daukaus's chokes against a forward-pressing brawler: SUB R1", "style", "Kyle Daukaus", "mixed",
                "He got the takedown and the back exactly as expected but couldn't finish, and Barriault escaped."),
            chk("read", "Daukaus's chokes vs Barriault's pressure", "grappling", "Kyle Daukaus", "mixed", "The chokes came close; Barriault survived them."),
            chk("read", "Daukaus's durability (against)", "durability", "Marc-Andre Barriault", "held",
                "Stopped by knees and ground strikes again, his second straight stoppage loss."),
            chk("read", "Barriault 1-5 in his last six", "form", "Kyle Daukaus", "failed", "Barriault won in round 1."),
            chk("model", "Fresher body favours Daukaus", "wear_and_tear", "Kyle Daukaus", "failed", "The more worn fighter absorbed the grappling and the fresher one was stopped."),
            chk("model", "Overall rating favours Daukaus", "overall", "Kyle Daukaus", "failed", "Lost in round 1."),
            chk("model", "Striking rating favours Barriault", "striking_rating", "Marc-Andre Barriault", "held", "The knees decided it."),
            chk("model", "Grappling rating favours Daukaus", "grappling_rating", "Kyle Daukaus", "held", "Daukaus dominated the ground for two minutes."),
            chk("model", "Wrestling rating favours Daukaus", "wrestling_rating", "Kyle Daukaus", "held", "Took Barriault down at will."),
        ]),
    "timothy-cuamba-louis-jourdain": dict(
        summary="After an even first two minutes of kicks, Cuamba took Jourdain down, survived a loose guillotine and dragged him back "
                "down every time he stood, ending round 1 with elbows from side control. In round 2 he worked the body, caught a kick for "
                "another takedown, trapped the wrist and punched until Jourdain gave his back, then finished with a choke at 2:48.",
        turning_point="Cuamba's first takedown; Jourdain never stopped one after that.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Cuamba has been taken down and choked recently and struggles going backwards", "style", "Louis Jourdain", "failed",
                "Cuamba was the one taking the back; Jourdain never got him moving backwards."),
            chk("read", "Cuamba's back-take defence", "grappling", "Louis Jourdain", "untested", "Jourdain never got a takedown or the back."),
            chk("read", "Jourdain's range and counters", "style", "Louis Jourdain", "failed", "Kicks early, then taken down repeatedly."),
            chk("read", "Jourdain's layoff (against)", "inactivity", "Timothy Cuamba", "held", "Looked flat and was out-wrestled after a year out."),
            chk("model", "Fight Matrix rating favours Cuamba", "outside_rating", "Timothy Cuamba", "held", "The UFC-tested fighter won clearly."),
            chk("model", "Submission threat favours Jourdain", "submission_threat", "Louis Jourdain", "failed", "His guillotine and kimura went nowhere; he was submitted."),
            chk("model", "Overall rating favours Cuamba", "overall", "Timothy Cuamba", "held", "Won every minute after the first two."),
            chk("model", "Striking rating favours Cuamba", "striking_rating", "Timothy Cuamba", "held", "Cleaner combinations and body shots."),
        ]),
    "mandel-nallo-nate-landwehr": dict(
        summary="Nallo controlled range from the opening exchange with his jab, front kicks and calf kicks, wobbled Landwehr with a "
                "straight right, battered him along the fence and hobbled his lead leg: a 10-8 round on every Sherdog card, ending with "
                "Nallo on the back. Two more leg kicks in round 2 dropped Landwehr and the referee stopped it at 0:47.",
        turning_point="The calf kicks late in round 1: Landwehr could barely stand on the leg by the bell.",
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Landwehr, 38 and moving up, has been knocked out three straight times walking forward: KO R1", "durability", "Mandel Nallo", "held",
                "Hurt badly in round 1 and stopped early in round 2 (the round was off by one)."),
            chk("read", "Landwehr's three straight KO losses", "durability", "Mandel Nallo", "held", "A fourth straight stoppage loss."),
            chk("read", "Landwehr moving up at 38", "age", "Mandel Nallo", "held", "Out-sized and out-reached all fight."),
            chk("read", "Nallo's chin (against)", "durability", "Nate Landwehr", "untested", "Landwehr landed almost nothing clean."),
            chk("model", "Fresher body favours Nallo", "wear_and_tear", "Mandel Nallo", "held", "Landwehr's accumulated damage showed."),
            chk("model", "Power vs chin favours Nallo", "power_vs_chin", "Mandel Nallo", "held", "Hurt early and stopped."),
        ]),
    "tanner-boser-jhonata-diniz": dict(
        summary="Boser, the smaller man, took Diniz down with a single leg in every round and Diniz never stopped one. Round 1 was side "
                "control and knees, round 2 a crucifix with elbows and punches (10-8 on every card), and in round 3 Boser mounted, took the "
                "back and kept punching until Herzog stopped it at 4:26.",
        turning_point="Boser's first takedown in round 1 showed Diniz had no answer on the floor.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "The bigger, rangier striker against an undersized heavyweight; trading early: KO R1", "size", "Jhonata Diniz", "failed",
                "Boser wrestled instead of trading and the size never mattered on the floor."),
            chk("read", "Size and reach", "size", "Jhonata Diniz", "failed", "Taken down at will."),
            chk("read", "Diniz's layoff and withdrawal (against)", "inactivity", "Tanner Boser", "held", "Diniz looked unprepared for the wrestling."),
            chk("read", "Boser at home", "home", "Tanner Boser", "held", "Won at home."),
            chk("model", "Size gap favours Diniz", "size_gap", "Jhonata Diniz", "failed", "The smaller heavyweight controlled him for three rounds."),
            chk("model", "Fresher body favours Diniz", "wear_and_tear", "Jhonata Diniz", "failed", "The older, more worn fighter won every round."),
            chk("model", "Reach favours Diniz", "reach", "Jhonata Diniz", "failed", "Never got to use it."),
            chk("model", "Wrestling rating favours Diniz", "wrestling_rating", "Jhonata Diniz", "failed", "Taken down in every round, stopped nothing."),
            chk("model", "Experience favours Boser", "experience", "Tanner Boser", "held", "The veteran's game plan won."),
        ]),
    "nick-galanti-julien-leblanc": dict(
        summary="Galanti shot inside 15 seconds, took Leblanc down, dragged him back when he stood, took the back with both hooks and "
                "forced the tap with a face crank at 1:26 of round 1.",
        turning_point=None,
        verdict="right, for our reasons",
        checks=[
            chk("pick", "A submission grappler against a 35-year-old off a damaged knee, choked in round one of his debut: SUB R1", "grappling", "Nick Galanti", "held",
                "Taken down, back taken and submitted in 86 seconds."),
            chk("read", "Leblanc's knee injury", "injury", "Nick Galanti", "untested", "Over before the knee was tested on the feet."),
            chk("read", "Galanti's grappling vs Leblanc's ground defence", "grappling", "Nick Galanti", "held", "No defence to the takedown or the back."),
            chk("read", "Leblanc's late opponent switch", "short_notice", "Nick Galanti", "untested", "Can't tell from 86 seconds."),
            chk("model", "Overall rating favours Galanti", "overall", "Nick Galanti", "held", "Won easily."),
            chk("model", "Wrestling rating favours Galanti", "wrestling_rating", "Nick Galanti", "held", "Two easy takedowns."),
        ]),
    "joel-faglier-javad-mahjoub": dict(
        summary="Mahjoub surprised everyone with his hands: he dropped Faglier with a one-two, swarmed him on the fence and floored him "
                "again with a straight right, a 10-8 round on every card. But he was exhausted by the bell; Faglier went to the body in "
                "round 2, and once Mahjoub's punches lost their steam a big right hand put him down and hammerfists ended it at 2:11.",
        turning_point="The end of round 1: Mahjoub punched himself out trying to finish, and Faglier survived.",
        verdict="right, other reasons",
        checks=[
            chk("pick", "Faglier, 25 and heavier, against a 35-year-old judoka: Faglier's hands early, R1", "age", "Joel Faglier", "mixed",
                "Faglier won late, on the older man's cardio, after nearly being finished himself in round 1."),
            chk("read", "Faglier on short notice", "short_notice", "Javad Mahjoub", "failed", "Faglier lasted; Mahjoub was the one who faded."),
            chk("read", "Mahjoub's Olympic judo", "grappling", "Javad Mahjoub", "untested", "Mahjoub won round 1 with his hands, not judo."),
            chk("read", "Mahjoub's age and inexperience (against)", "cardio", "Joel Faglier", "held", "Gassed after one round and stopped in the second."),
            chk("model", "Overall rating favours Faglier", "overall", "Joel Faglier", "held", "Won."),
            chk("model", "Age favours Faglier", "age_curve", "Joel Faglier", "held", "The younger man's gas tank decided it."),
        ]),
    "katlyn-cerminara-mackenzie-stiller": dict(
        summary="Stiller started fast with combinations and low kicks, but Cerminara settled behind her jab, check hooks and knees, and "
                "Stiller's punches started falling short. When Stiller shot a single leg late in round 1 Cerminara sprawled and punched, "
                "Stiller hit the mat under fire and the referee stopped it at 4:46: Cerminara's first finish in more than a decade.",
        turning_point="Stiller's desperation single leg at the fence, which put her on the mat under punches.",
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "A strawweight moving up on short notice, much smaller, against a long volume striker: decision", "size", "Katlyn Cerminara", "mixed",
                "Size and range won it as expected, but by stoppage, not on the cards."),
            chk("read", "Stiller on short notice and moving up", "short_notice", "Katlyn Cerminara", "held", "Came up short on her punches after a fast start."),
            chk("read", "Size and range", "reach", "Katlyn Cerminara", "held", "The jab and knees controlled the fight."),
            chk("read", "Cerminara's age and layoff (against)", "inactivity", "Mackenzie Stiller", "failed", "Looked sharper than before the layoff."),
            chk("model", "Fresher body favours Stiller", "wear_and_tear", "Mackenzie Stiller", "failed", "The fresher fighter faded and was stopped."),
            chk("model", "Fight Matrix rating favours Cerminara", "outside_rating", "Katlyn Cerminara", "held", "Won."),
            chk("model", "Overall rating favours Cerminara", "overall", "Katlyn Cerminara", "held", "Won."),
            chk("model", "Age favours Stiller", "age_curve", "Mackenzie Stiller", "failed", "The 38-year-old won in round 1."),
            chk("model", "Striking rating favours Cerminara", "striking_rating", "Katlyn Cerminara", "held", "Won it standing."),
        ]),
    "steven-koslow-chad-anheliger": dict(
        summary="Anheliger landed the cleaner leg kicks and right hands at range, but Koslow took him down midway through every round and "
                "won the first two from top position with punches and elbows. In round 3 he got a body-lock takedown, moved through mount "
                "to the back with a body triangle and finished with a rear-naked choke at 4:31.",
        turning_point="Koslow's takedown in round 1: from then on Anheliger spent most of the fight underneath him.",
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "Six of Anheliger's eight losses are submissions and he defends few takedowns; Koslow's chance is early: SUB R1", "grappling", "Steven Koslow", "mixed",
                "The grappling read held, but Koslow lasted three rounds and finished late, not early."),
            chk("read", "Anheliger's takedown defence", "td_def", "Steven Koslow", "held", "Taken down in all three rounds."),
            chk("read", "Koslow's four-year layoff (against)", "inactivity", "Chad Anheliger", "failed", "Koslow showed no rust or cardio problem over three rounds."),
            chk("read", "Anheliger's age and knee", "age", "Steven Koslow", "held", "Close to 40 and it showed."),
            chk("model", "Striking rating favours Anheliger", "striking_rating", "Chad Anheliger", "held", "Won the exchanges on the feet."),
            chk("model", "Age favours Koslow", "age_curve", "Steven Koslow", "held", "The younger man was stronger late."),
            chk("model", "Wrestling edge favours Koslow", "wrestling_edge", "Steven Koslow", "held", "Took him down every round."),
            chk("model", "Layoff favours Anheliger", "layoff", "Chad Anheliger", "failed", "The four-year layoff didn't show."),
            chk("model", "Fight Matrix rating favours Anheliger", "outside_rating", "Chad Anheliger", "failed", "Lost every round."),
        ]),
    "chelsea-chandler-melissa-croden": dict(
        summary="Croden was winning round 1 clearly: she stalked, landed the one-two, elbows and knees to the body, and Chandler kept "
                "clinching to survive. With seconds left Croden tripped her in the clinch, Chandler rolled into top position and caught a "
                "kimura that she cranked until the arm gave, a submission at 4:52.",
        turning_point="Croden's trip takedown in the last 20 seconds put her arm where Chandler could catch it.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Croden builds late and has never been finished; Chandler is dangerous early: Croden KO R3", "durability", "Melissa Croden", "failed",
                "Croden was out-striking her, but Chandler's early danger (the grappling, not the power) finished it in round 1."),
            chk("read", "Chandler's weight cut and injuries", "weight_cut", "Melissa Croden", "untested", "Chandler looked fine and the fight lasted under five minutes."),
            chk("read", "Croden's durability and late pressure", "durability", "Melissa Croden", "failed", "Finished for the first time, by submission."),
            chk("read", "Chandler's early finishes (against)", "style", "Chelsea Chandler", "held", "Exactly the danger: a round-1 submission off a scramble."),
            chk("model", "Wrestling rating favours Chandler", "wrestling_rating", "Chelsea Chandler", "held", "Won the scramble that mattered."),
            chk("model", "Striking exchange favours Croden", "striking_exchange", "Melissa Croden", "held", "Croden was landing at will before the finish."),
            chk("model", "Wrestling edge favours Croden", "wrestling_edge", "Melissa Croden", "mixed", "She got the takedown, and it cost her the arm."),
            chk("model", "Striking rating favours Croden", "striking_rating", "Melissa Croden", "held", "Won the striking."),
        ]),
    "su-young-you-cody-chovancek": dict(
        summary="You out-wrestled the unbeaten Chovancek for three rounds: single legs and mat returns in round 1, a leglock sweep and "
                "mount with punches in round 2, and in round 3 he took the back, chased the arm triangle and wrenched a kimura from side "
                "control for the tap at 4:19.",
        turning_point="Round 1: You's first mat return; Chovancek never found a way back to his feet that lasted.",
        single_source=True,
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "The unbeaten finisher at home, but You's chain wrestling and durability make it a grind: Chovancek DEC", "wrestling_edge", "Cody Chovancek", "failed",
                "The grind was all You's; Chovancek was controlled on the floor for three rounds and submitted."),
            chk("read", "You's wrestling volume", "wrestling", "You Su-young", "held", "Took him down whenever he wanted."),
            chk("read", "Chovancek's finishing and cardio", "style", "Cody Chovancek", "failed", "Never threatened a finish."),
            chk("read", "Chovancek's layoff", "inactivity", "You Su-young", "held", "Flat and out-wrestled after 13 months out."),
            chk("model", "Wrestling edge favours You", "wrestling_edge", "You Su-young", "held", "Decisive."),
            chk("model", "Fresher body favours Chovancek", "wear_and_tear", "Cody Chovancek", "failed", "The more experienced fighter won comfortably."),
            chk("model", "Striking defence favours You", "striking_defense", "You Su-young", "untested", "Little striking happened."),
            chk("model", "Striking rating favours Chovancek", "striking_rating", "Cody Chovancek", "untested", "Little striking happened."),
        ]),
}

# Judged performances (two outlets agree: Sherdog's play-by-play and MMA Mania, plus the named recaps)
SRC = f"{SHERDOG}; {MANIA}"
NOTES = [
    ("Mike Malott", "Joaquin Buckley", "striking", 1.5, ["clinch", "timing", "power"],
     "Neutralised Buckley in the clinch with knees, then timed a level change with a knee for a round-2 KO."),
    ("Jasmine Jasudavicius", "Erin Blanchfield", "grappling", 2.0, ["back_take", "control", "td_off"],
     "Took Blanchfield down and took her back with a body triangle in two straight rounds; controlled every grappling exchange."),
    ("Jasmine Jasudavicius", "Erin Blanchfield", "striking", -0.5, ["strike_def"],
     "Lost round 3 on the feet to Blanchfield's combinations."),
    ("Marc-Andre Barriault", "Kyle Daukaus", "striking", 1.5, ["clinch", "knees", "gnp"],
     "Escaped Daukaus's back control, met his shots with knees and finished with ground strikes in round 1."),
    ("Marc-Andre Barriault", "Kyle Daukaus", "grappling", -1.0, ["td_def"],
     "Taken down, mounted and back-controlled for two minutes before escaping."),
    ("Timothy Cuamba", "Louis Jourdain", "wrestling", 2.0, ["td_off", "chain_wrestling", "back_take"],
     "Took Jourdain down repeatedly, kept him down and choked him out from the back in round 2."),
    ("Mandel Nallo", "Nate Landwehr", "striking", 2.0, ["jab", "leg_kicks", "range"],
     "Controlled range with the jab, front kick and calf kicks, a 10-8 round, then stopped Landwehr with leg kicks."),
    ("Tanner Boser", "Jhonata Diniz", "wrestling", 2.0, ["td_off", "control", "gnp"],
     "Took the bigger man down at will in all three rounds and finished from a crucifix and mount."),
    ("Nick Galanti", "Julien Leblanc", "grappling", 1.5, ["td_off", "back_take", "submission"],
     "Takedown in 15 seconds, back take and face-crank submission at 1:26."),
    ("Joel Faglier", "Javad Mahjoub", "striking", 0.5, ["durability", "body_work"],
     "Survived two knockdowns in round 1, then broke the tired Mahjoub with body shots in round 2."),
    ("Katlyn Cerminara", "Mackenzie Stiller", "striking", 1.5, ["jab", "knees", "range"],
     "Settled behind the jab and knees after Stiller's fast start and stopped her late in round 1."),
    ("Steven Koslow", "Chad Anheliger", "wrestling", 1.5, ["td_off", "control", "back_take"],
     "Took Anheliger down in every round and finished with a rear-naked choke in round 3."),
    ("Chelsea Chandler", "Melissa Croden", "grappling", 1.0, ["scramble", "submission"],
     "Out-struck for most of round 1, then reversed a trip takedown into a fight-ending kimura."),
    ("You Su-young", "Cody Chovancek", "wrestling", 2.0, ["td_off", "control", "submission"],
     "Out-wrestled the unbeaten Chovancek for three rounds and finished with a kimura."),
]

REVIEW = """A record-tying night of finishes (12 of 13) and a bad one for the favourites: the model picked 8 of 13 winners with a log loss of 0.770, the market 7 of 13 at 0.717 and the blend 7 of 13 at 0.745. On the season the market still leads (0.580 log loss on 418 priced bouts, the model 0.636 on the same bouts). AI Picks scored 21 points to the model's 22; the AI Bets plays on Croden by KO and Daukaus both lost.

The misses that matter were clear ones, not judging coin flips. Jasudavicius beat Blanchfield (73% on both the model and the market) by winning the grappling Blanchfield was supposed to own; Boser beat Diniz (the model gave Diniz 71%) by taking him down in every round; Barriault stopped Daukaus after surviving two minutes of back control; and Chandler submitted Croden (the market's 75% favourite) off a late scramble in a round Croden was winning. The size claims failed twice: the model's size_gap and reach for Diniz, and our read of Blanchfield's grappling edge against the bigger woman. Malott and Faglier were wins for the right side but not for our reasons: both came from a moment (a counter knee, an opponent's empty gas tank) rather than the range battle we expected.

The hits were the durability reads: Nelson, Landwehr and Leblanc were all finished early exactly as their records said, and the picks on Pérez (KO R1) and Galanti (SUB R1) scored the full four points.

Your fight-night notes line up with the fights. "Jasmine uses her size really well in grappling" is the whole story of the co-main, and it is the thing our read got backwards; that goes into her report. "Diniz falls down when you touch his legs" matches every outlet; it goes into his report as the first thing to check against any wrestler. "Kyle just has too shaky a chin" agrees with the read's own warning (durability against) that we didn't weigh enough. "Javad... essentially lost via exhaustion" is the Faglier fight exactly: Mahjoub punched himself out in round 1. Your reads that Landwehr is shot, Leblanc isn't UFC level, Cuamba is a good athlete becoming a decent fighter and You is a good grappler all hold up and go into the reports; "Chad should retire" stays a note, since Koslow's win says as much about Koslow."""


def main():
    f = ROOT / "recaps" / f"{ID}.json"
    doc = json.loads(f.read_text())
    cov = doc["coverage"]
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
    notes += [{"date": DATE, "fighter": a, "opponent": b, "category": cat, "rating": r, "skills": sk, "note": nt, "source": SRC}
              for a, b, cat, r, sk, nt in NOTES]
    fn.write_text(json.dumps(notes, ensure_ascii=False, indent=1) + "\n")

    out = Path(__file__).resolve().parents[3] / ".cache" / "recap_review.json"
    out.write_text(json.dumps({"event": EVENT, "date": DATE, "review": REVIEW, "notes_used": True, "written": WRITTEN,
                               "stories": doc["stories"]}, ensure_ascii=False))
    print(len(doc["stories"]), "stories;", len(NOTES), "fight notes; review ->", out)


if __name__ == "__main__":
    main()
