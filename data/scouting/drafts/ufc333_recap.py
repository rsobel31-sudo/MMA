"""Card review for UFC 333: Volkanovski vs. Evloev (2026-10-24).

What happened in every bout (our own words, from Sherdog's play-by-play and the outlets' recaps: MMA Mania and
Uncrowned on the main event, MMA Junkie and MMA Fighting on the co-main, Cageside Press on five more), the pre-fight
claims checked against the fights, and judged performances for data/scouting/fight_notes.json where two outlets agree.
Seven bouts were described only by Sherdog and are marked single_source. Written Sunday 2026-10-25; the review text
is left empty for the owner to write.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = "2026-10-24-ufc-333-volkanovski-vs-evloev"
EVENT, DATE, WRITTEN = "UFC 333 - Volkanovski vs. Evloev", "2026-10-24", "2026-10-25"


def chk(by, claim, tag, favoured, verdict, note):
    return {"by": by, "claim": claim, "tag": tag, "favoured": favoured, "verdict": verdict, "note": note}


VOLK, EVL = "Alexander Volkanovski", "Movsar Evloev"
YAN, MERAB = "Petr Yan", "Merab Dvalishvili"
KAV, TEM = "Lone'er Kavanagh", "Ramazonbek Temirov"
VOLKOV, KUN = "Alexander Volkov", "Rizvan Kuniev"
PICO, KEITA = "Aaron Pico", "Losene Keita"
REYES, MURZ = "Dominick Reyes", "Azamat Murzakanov"
YAKH, KRYL = "Abdul-Rakhman Yakhyaev", "Nikita Krylov"
ABUS, ROW = "Abus Magomedov", "Cameron Rowston"
DAW, ALIEV = "Grant Dawson", "Nurullo Aliev"
THICK, CHOP = "Colby Thicknesse", "Asaf Chopurov"
VAG, MALK = "Abubakar Vagaev", "Jacob Malkoun"
SANTOS, OKI = "Daniel Santos", "Bolaji Oki"
STEELE, GUG = "Kody Steele", "Noah Gugnon"
LUC, CAL = "Iasmin Lucindo", "Nicolle Caliari"

STORIES = {
    "alexander-volkanovski-movsar-evloev": dict(
        summary="Evloev won the first round on all three Sherdog cards with three takedowns, though Volkanovski stood up from each "
                "almost at once and kept landing low kicks and right hands. In round 2 Volkanovski reversed a takedown into top "
                "position, then rocked Evloev with a left hook and a combination; Evloev turned away to his back and Volkanovski "
                "poured on right hands until Goddard stopped it at 4:54, Evloev's first loss in 21 fights. Volkanovski said afterwards "
                "he had fought sick.",
        turning_point="Round 2: Volkanovski switched off Evloev's takedown and ended up on top; from then Evloev stopped wrestling "
                      "and was hurt standing.",
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "Evloev has never finished a UFC opponent; Volkanovski's takedown defence and output win the long fight: decision",
                "style", VOLK, "mixed",
                "Getting up and out-working Evloev held; the 'neither finishes' half failed, Volkanovski stopped him in round 2."),
            chk("read", "Evloev's lack of finishing power", "power", VOLK, "held", "Evloev landed little of note in two rounds."),
            chk("read", "Volkanovski's takedown defence and pace", "td_def", VOLK, "held",
                "Conceded three takedowns in round 1 but stood from every one and reversed the next in round 2."),
            chk("read", "Age 38 (against)", "age", EVL, "failed", "The 38-year-old was the stronger, sharper fighter by round 2."),
            chk("read", "Evloev's chain wrestling (against)", "wrestling", EVL, "mixed",
                "Won round 1 with it, but never held Volkanovski down."),
            chk("model", "Fresher body favours Evloev", "wear_and_tear", EVL, "failed",
                "The far more worn champion took Evloev's best and finished him."),
            chk("model", "Wrestling rating favours Evloev", "wrestling_rating", EVL, "mixed",
                "Evloev completed the takedowns but got no control from them."),
            chk("model", "Age favours Evloev", "age_curve", EVL, "failed", "See the read: the older man won clearly."),
            chk("model", "Wrestling edge favours Evloev", "wrestling_edge", EVL, "mixed",
                "Took round 1 on takedowns, lost the exchange in round 2 when Volkanovski reversed."),
            chk("model", "Striking rating favours Volkanovski", "striking_rating", VOLK, "held", "Won every striking exchange that mattered."),
        ]),
    "petr-yan-merab-dvalishvili": dict(
        summary="Dvalishvili took the first two rounds on every Sherdog card, ducking into takedown after takedown and forcing Yan "
                "to spend energy getting up. From round 3 Yan stopped the shots almost entirely, hurt Dvalishvili with body kicks "
                "and combinations and swept the last three rounds as the challenger tired: 48-47 on all three official cards. "
                "Dvalishvili was credited with a UFC-record 58 takedown attempts, only five of them successful.",
        turning_point="Round 3: Yan's crushing body kick and his takedown defence turned the fight; Dvalishvili was spent by round 5.",
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Yan's takedown defence beat Dvalishvili's chain wrestling in the rematch and Yan lands the heavier shots: decision",
                "td_def", YAN, "held",
                "Five takedowns from 58 attempts, and none in the last three rounds; Yan's shots were the heavier ones. Decision, as picked."),
            chk("read", "Yan's takedown defence in the rematch", "td_def", YAN, "held",
                "Gave up takedowns early but always stood, then stuffed everything from round 3."),
            chk("read", "Yan's back surgery and layoff (against)", "inactivity", MERAB, "failed",
                "Yan was the stronger fighter late in a five-round fight."),
            chk("read", "Dvalishvili's pace", "cardio", MERAB, "mixed",
                "Won rounds 1 and 2 on volume, but was spent by round 5."),
            chk("model", "Wrestling rating favours Dvalishvili", "wrestling_rating", MERAB, "mixed",
                "His takedowns won the first two rounds and then stopped working."),
        ]),
    "lone-er-kavanagh-ramazonbek-temirov": dict(
        summary="Temirov came out throwing a spinning back kick and big overhand rights, but swung and missed often while Kavanagh "
                "stuck to his jab, hit the body and slipped the return fire. By the late minutes Temirov's right eye was swelling "
                "shut; Kavanagh dazed him with a left uppercut, dropped him and finished with lefts on the floor at 4:28 of round 1.",
        turning_point="Kavanagh's jab closing Temirov's right eye, which set up the left uppercut.",
        verdict="wrong, claim failed",
        single_source=True,
        checks=[
            chk("pick", "Eleven of Temirov's wins came in round one; Kavanagh has been knocked out by one counter right: KO R1",
                "power", TEM, "failed", "A round-one knockout, but Kavanagh's."),
            chk("read", "Kavanagh's chin", "durability", TEM, "failed",
                "Kavanagh took several of Temirov's overhand rights without trouble."),
            chk("read", "Temirov's first-round power", "power", TEM, "failed", "Swung big and mostly missed."),
            chk("read", "Temirov's suspension layoff (against)", "inactivity", KAV, "mixed",
                "Temirov's timing looked off, but Kavanagh's movement made him miss too."),
            chk("model", "Fight Matrix rating favours Temirov", "outside_rating", TEM, "failed", "Stopped in round 1."),
            chk("model", "Striking rating favours Temirov", "striking_rating", TEM, "failed", "Out-jabbed, swollen and knocked down."),
            chk("model", "Overall rating favours Temirov", "overall", TEM, "failed", "Lost inside a round."),
            chk("model", "Power vs chin favours Temirov", "power_vs_chin", TEM, "failed", "Kavanagh's was the power that showed."),
            chk("model", "Striking defence favours Temirov", "striking_defense", TEM, "failed", "Hit with the jab all round and finished."),
        ]),
    "alexander-volkov-rizvan-kuniev": dict(
        summary="Volkov started slowly, then took over with his jab, body kicks and calf kicks, and won the clinch exchanges as well; "
                "Kuniev's best moments were a Superman punch in round 2 and a burst at the start of round 3. Volkov's kicks had "
                "Kuniev hobbling and switching stances, and late in round 3 he sprawled on a takedown, took the back and hunted a "
                "choke to the bell: a unanimous decision (29-28, 30-27, 30-27), 30-27 on every Sherdog card.",
        turning_point="The calf kicks in round 3, which took Kuniev's lead leg and his last push.",
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Volkov's range against a slow starter; Kuniev has never been finished: decision", "style", VOLKOV, "held",
                "Range won every round and it went the distance."),
            chk("read", "Kuniev's slow starts", "pace", VOLKOV, "mixed",
                "Kuniev lost round 1, but it was Volkov who started slowly; Kuniev's busiest spell was the start of round 3."),
            chk("read", "Volkov's range", "reach", VOLKOV, "held", "The jab and kicks decided it."),
            chk("read", "Kuniev's clinch and knees (against)", "clinch", KUN, "failed", "Volkov controlled the clinch."),
            chk("model", "Fresher body favours Kuniev", "wear_and_tear", KUN, "failed",
                "The 38-year-old veteran was the stronger man in round 3."),
            chk("model", "Overall rating favours Volkov", "overall", VOLKOV, "held", "Won all three rounds on Sherdog's cards."),
            chk("model", "Striking rating favours Volkov", "striking_rating", VOLKOV, "held", "Out-landed him at range."),
            chk("model", "Wrestling rating favours Volkov", "wrestling_rating", VOLKOV, "held",
                "Stopped Kuniev's shots and took his back late."),
            chk("model", "Fight Matrix rating favours Volkov", "outside_rating", VOLKOV, "held", "Won."),
        ]),
    "aaron-pico-losene-keita": dict(
        summary="Pico shot a high-crotch single straight away and took Keita down in open space. Keita stood and landed a left, "
                "but Pico answered with a one-two and dropped him with a right cross, finishing with punches on the floor at 1:14 of "
                "round 1: the first real stoppage loss of Keita's career.",
        turning_point=None,
        verdict="right, partly for our reasons",
        single_source=True,
        checks=[
            chk("pick", "Pico's wrestling against a striker who has never faced it; he builds the fight and keeps his chin out of Keita's power: decision",
                "wrestling", PICO, "mixed",
                "The takedown came first, as expected, but the fight ended on Pico's right hand inside 75 seconds."),
            chk("read", "Pico's wrestling vs Keita's untested defence", "wrestling", PICO, "held", "Took him down at the first attempt."),
            chk("read", "Keita's short turnaround", "short_notice", PICO, "untested", "Over in 74 seconds."),
            chk("read", "Pico's durability (against)", "durability", KEITA, "untested", "Keita landed one left hand."),
            chk("model", "Wrestling edge favours Pico", "wrestling_edge", PICO, "held", "An easy first takedown."),
            chk("model", "Fresher body favours Keita", "wear_and_tear", KEITA, "failed", "Keita was the one who couldn't take the shot."),
            chk("model", "Striking defence favours Keita", "striking_defense", KEITA, "failed", "Dropped by a straight right."),
        ]),
    "dominick-reyes-azamat-murzakanov": dict(
        summary="Reyes used his height and reach from the start, kicking Murzakanov's legs as he stalked forward. Murzakanov landed "
                "one sharp one-two, but Reyes staggered him with a head kick, dropped him with a left hand and finished with "
                "punches at 2:40 of round 1.",
        turning_point="The head kick at range, the weapon Murzakanov couldn't reach.",
        verdict="wrong, claim failed",
        single_source=True,
        checks=[
            chk("pick", "Reyes has been stopped four times, twice in round one; Murzakanov's one-shot power: KO R1",
                "durability", MURZ, "failed", "Decided early, as expected, but by Reyes."),
            chk("read", "Reyes's durability", "durability", MURZ, "untested", "Murzakanov landed only one clean combination."),
            chk("read", "Reach and kicks at range (against)", "reach", REYES, "held", "Leg kicks, then the head kick that ended it."),
            chk("read", "Murzakanov's first loss", "form", MURZ, "failed", "Stopped in round 1."),
            chk("model", "Fresher body favours Murzakanov", "wear_and_tear", MURZ, "failed", "The more worn Reyes won in round 1."),
            chk("model", "Power vs chin favours Murzakanov", "power_vs_chin", MURZ, "failed", "Murzakanov was the one knocked out."),
            chk("model", "Reach favours Reyes", "reach", REYES, "held", "See the read."),
            chk("model", "Height favours Reyes", "height", REYES, "held", "The head kick came from the taller man."),
        ]),
    "abdul-rakhman-yakhyaev-nikita-krylov": dict(
        summary="Krylov came forward behind stomps and a right hand and pinned the unbeaten Yakhyaev on the fence, hunting "
                "takedowns and trips. Yakhyaev held his balance, turned it around and jumped on a deep guillotine; when Krylov "
                "survived it he took the back, landed a knee to the head and punched until Herzog stopped it at 2:38 of round 1.",
        turning_point="Yakhyaev's guillotine: from there Krylov was defending, not attacking.",
        verdict="right, for our reasons",
        checks=[
            chk("pick", "All of Yakhyaev's UFC and Contender Series wins came in round one; Krylov was knocked out in round one twice in 2025: R1",
                "durability", YAKH, "held", "TKO at 2:38 of round 1."),
            chk("read", "Krylov's durability", "durability", YAKH, "held", "Stopped by a knee and punches."),
            chk("read", "Yakhyaev untested late", "cardio", KRYL, "untested", "Over in round 1."),
            chk("model", "Fresher body favours Yakhyaev", "wear_and_tear", YAKH, "held", "Krylov couldn't take the knee."),
            chk("model", "Submission threat favours Yakhyaev", "submission_threat", YAKH, "held", "The guillotine nearly ended it."),
            chk("model", "Power vs chin favours Yakhyaev", "power_vs_chin", YAKH, "held", "Finished with strikes."),
            chk("model", "Wrestling edge favours Yakhyaev", "wrestling_edge", YAKH, "held",
                "Stopped Krylov's takedowns on the fence and took the back."),
            chk("model", "Experience favours Krylov", "experience", KRYL, "failed", "The veteran was out-grappled and finished."),
        ]),
    "abus-magomedov-cameron-rowston": dict(
        summary="Magomedov walked Rowston down with wide hooks and chopped at his lead leg, and Rowston kept falling short with "
                "his punches. Rowston dived for a takedown, Magomedov caught the neck in a guillotine, held it through several "
                "scrambles and choked him unconscious at 1:44 of round 1.",
        turning_point="Rowston's takedown attempt into the guillotine.",
        verdict="wrong, claim failed",
        single_source=True,
        checks=[
            chk("pick", "Magomedov wins early and then breaks under pressure; if Rowston survives the early submissions he wins later: decision",
                "cardio", ROW, "failed",
                "Rowston didn't survive the early danger; the fade was never tested."),
            chk("read", "Magomedov's grappling", "grappling", ABUS, "held", "Choked him out from a guillotine."),
            chk("read", "Magomedov fades under pressure (against)", "cardio", ROW, "untested", "Over in 104 seconds."),
            chk("read", "Rowston's streak", "form", ROW, "failed", "The streak ended in round 1."),
            chk("model", "Fresher body favours Rowston", "wear_and_tear", ROW, "failed", "The fresher fighter was finished quickly."),
            chk("model", "Wrestling edge favours Magomedov", "wrestling_edge", ABUS, "held", "Rowston's shot was punished."),
            chk("model", "Wrestling rating favours Magomedov", "wrestling_rating", ABUS, "held", "See the wrestling edge."),
            chk("model", "Fight Matrix rating favours Magomedov", "outside_rating", ABUS, "held", "Won."),
            chk("model", "Age favours Rowston", "age_curve", ROW, "failed", "The older man won in round 1."),
        ]),
    "grant-dawson-nurullo-aliev": dict(
        summary="Aliev started fast, pressing Dawson to the fence, dropping him with a straight left and landing on top, but he lost "
                "a point for hammerfists to the back of the head. Dawson took him down late in round 1 and nearly caught a guillotine, "
                "then out-wrestled a tiring Aliev for two rounds, five takedowns in all, finishing in full mount with elbows: "
                "29-27 on every official and Sherdog card.",
        turning_point="Dawson's takedown late in round 1 after the point deduction; Aliev was labouring from round 2 on.",
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "Aliev finishes almost no one, so Dawson's chin is less exposed; Dawson's back takes in scrambles win the close rounds: decision",
                "style", DAW, "mixed",
                "A decision as picked, but Aliev dropped Dawson in round 1, and the rounds were won by takedowns and top control, not back takes."),
            chk("read", "Aliev's low finishing threat", "power", DAW, "mixed", "Aliev knocked him down but couldn't follow up."),
            chk("read", "Wrestler vs wrestler", "wrestling", DAW, "held", "Dawson won the wrestling clearly from late round 1."),
            chk("read", "Dawson's back takes", "grappling", DAW, "mixed", "Top control and mount did the work; no back take."),
            chk("model", "Fresher body favours Aliev", "wear_and_tear", ALIEV, "failed", "Aliev faded badly from round 2."),
            chk("model", "Overall rating favours Dawson", "overall", DAW, "held", "Won two rounds clearly plus a point."),
            chk("model", "Fight Matrix rating favours Dawson", "outside_rating", DAW, "held", "Won."),
            chk("model", "Grappling rating favours Dawson", "grappling_rating", DAW, "held", "Guillotine threat, mount and ground strikes."),
            chk("model", "Striking rating favours Aliev", "striking_rating", ALIEV, "mixed",
                "Aliev won the early exchanges and scored a knockdown, but was out-struck once tired."),
        ]),
    "colby-thicknesse-asaf-chopurov": dict(
        summary="A stop-start fight in the clinch. The unbeaten debutant Chopurov pressed and took round 1 while escaping two "
                "Thicknesse guillotines, Thicknesse won round 2 with elbows, knees and combinations, and Chopurov took him down "
                "repeatedly in round 3 but kept letting him back up. Sherdog's three scorers all had Chopurov 29-28; two judges gave "
                "it to Thicknesse, a split decision.",
        turning_point=None,
        verdict="wrong, close fight",
        checks=[
            chk("pick", "Chopurov's pressure should break Thicknesse once the early scrambles are over: KO R2", "durability", CHOP, "failed",
                "Thicknesse was never hurt; it went to a split decision."),
            chk("read", "Chopurov's pressure and finishing", "pressure", CHOP, "mixed",
                "Pressure and takedowns won rounds 1 and 3 on Sherdog's cards; no finish."),
            chk("read", "UFC debut (against)", "debut", THICK, "mixed",
                "Chopurov looked composed but kept letting Thicknesse up from takedowns."),
            chk("read", "Thicknesse's guard", "grappling", THICK, "held", "Guillotine threats and wrist control kept him safe underneath."),
            chk("model", "Overall rating favours Chopurov", "overall", CHOP, "mixed", "Won on Sherdog's cards, lost on the judges'."),
            chk("model", "Fight Matrix rating favours Chopurov", "outside_rating", CHOP, "mixed", "As above."),
            chk("model", "Striking rating favours Chopurov", "striking_rating", CHOP, "failed",
                "Thicknesse won the striking, clearly so in round 2."),
            chk("model", "Wrestling rating favours Chopurov", "wrestling_rating", CHOP, "held", "Took him down repeatedly in round 3."),
            chk("model", "Wrestling edge favours Chopurov", "wrestling_edge", CHOP, "held", "Thicknesse's own shots went nowhere."),
        ]),
    "abubakar-vagaev-jacob-malkoun": dict(
        summary="Malkoun boxed behind a stiff jab all fight and won rounds 1 and 3 on every Sherdog card with it. Vagaev landed the "
                "harder shots, rattling Malkoun with a left hook and adding takedowns in round 2 and again in round 3, but Malkoun "
                "stood quickly each time. Sherdog had Malkoun 29-28; all three judges had Vagaev 29-28.",
        turning_point=None,
        verdict="right on the cards, wrong on the fight",
        single_source=True,
        checks=[
            chk("pick", "Model, market and pundits all have Vagaev; both win on the mat over three rounds: decision", "consensus", VAG, "mixed",
                "The decision and the winner held, but Sherdog's scorers had Malkoun."),
            chk("read", "Vagaev moving up a division", "size", MALK, "mixed",
                "Malkoun's jab controlled the range, but Vagaev's power and takedowns carried up."),
            chk("read", "Vagaev's late-round fade", "cardio", MALK, "failed", "Vagaev was landing the heavier shots in round 3."),
            chk("read", "Malkoun's size (against)", "size", VAG, "mixed", "Vagaev hit harder; Malkoun still stood up from every takedown."),
            chk("model", "Fight Matrix rating favours Vagaev", "outside_rating", VAG, "mixed", "Won on the official cards, not on Sherdog's."),
            chk("model", "Fresher body favours Malkoun", "wear_and_tear", MALK, "mixed", "Neither faded."),
            chk("model", "Overall rating favours Vagaev", "overall", VAG, "mixed", "As the Fight Matrix rating."),
            chk("model", "Wrestling rating favours Vagaev", "wrestling_rating", VAG, "held",
                "Reversed Malkoun's single leg and took him down in two rounds."),
            chk("model", "Experience favours Vagaev", "experience", VAG, "mixed", "Nothing in the fight turned on it."),
        ]),
    "daniel-santos-bolaji-oki": dict(
        summary="Oki took round 1 with his jab, body work and a late takedown into side control after escaping a Santos guillotine. "
                "Santos won round 2 with a takedown and flurries, and kept chopping the legs in round 3, but Oki doubled him over "
                "with a body kick and took him down again. Sherdog had Oki 29-28; all three judges had Santos 29-28.",
        turning_point=None,
        verdict="right on the cards, wrong on the fight",
        single_source=True,
        checks=[
            chk("pick", "Santos's pressure, low kicks and clinch knees build through a fight; Oki fades after big first rounds: KO R2",
                "cardio", SANTOS, "failed", "Oki didn't fade; he won round 3 on Sherdog's cards and there was no finish."),
            chk("read", "Oki's first cut to 145", "weight_cut", SANTOS, "failed", "Oki looked strong for all three rounds."),
            chk("read", "Santos's weight-cut history", "weight_cut", OKI, "untested", "Nothing in the fight showed it."),
            chk("read", "Both coming off stoppage losses", "durability", SANTOS, "untested", "Neither was badly hurt."),
            chk("model", "Fight Matrix rating favours Santos", "outside_rating", SANTOS, "mixed", "Won on the official cards, not on Sherdog's."),
            chk("model", "Reach favours Oki", "reach", OKI, "held", "Oki's jab won him rounds 1 and 3 on Sherdog's cards."),
            chk("model", "Fresher body favours Oki", "wear_and_tear", OKI, "mixed", "Oki was the busier man late, but lost the decision."),
            chk("model", "Wrestling rating favours Santos", "wrestling_rating", SANTOS, "failed", "Oki out-wrestled him, two takedowns to one."),
            chk("model", "Wrestling edge favours Santos", "wrestling_edge", SANTOS, "failed", "As the wrestling rating."),
        ]),
    "kody-steele-noah-gugnon": dict(
        summary="Gugnon had the better of the opening minutes with a hard jab, leg kicks and a partly blocked head kick, and stopped "
                "Steele's early shots. Steele rocked him with a combination, finally got a takedown, and when Gugnon broke free "
                "Steele dropped him with a right hand and finished with punches at 3:54 of round 1.",
        turning_point="Steele's combination midway through the round, which left Gugnon hurt for the rest of it.",
        verdict="right, other reasons",
        checks=[
            chk("pick", "Gugnon has seen a third round once; Steele, a black belt, can grind if he doesn't get dragged into a brawl: decision",
                "style", STEELE, "failed", "Steele won the brawl in round 1; there was no grind."),
            chk("read", "Gugnon unproven over three rounds", "cardio", STEELE, "untested", "Over in round 1."),
            chk("read", "Steele's withdrawal and brawling habit", "style", GUG, "failed", "Steele brawled and won the brawl."),
        ]),
    "iasmin-lucindo-nicolle-caliari": dict(
        summary="Caliari missed weight by 4.5 lb, and Lucindo still out-muscled her: she took Caliari down in every round, "
                "smothered her from half guard and side control and cut her open with elbows and a spinning backfist. Caliari's "
                "leglock and armbar attempts got her back up a few times but never threatened: 30-27 on every card.",
        turning_point=None,
        verdict="right, for our reasons",
        single_source=True,
        checks=[
            chk("pick", "Lucindo's clinch strength and takedowns against a grappler who is out-landed on the feet: decision",
                "wrestling", LUC, "held", "Takedowns in every round and a clear decision."),
            chk("read", "Lucindo's strength and top control", "control", LUC, "held", "Held her down for most of three rounds."),
            chk("read", "Caliari out-landed on the feet", "striking", LUC, "mixed", "Little of the fight was standing; Caliari's best moments were there."),
            chk("read", "Lucindo's layoff (against)", "inactivity", CAL, "failed", "No sign of rust."),
            chk("read", "Caliari's weight miss", "weight_cut", LUC, "mixed", "The heavier woman was still out-muscled."),
            chk("model", "Wrestling rating favours Lucindo", "wrestling_rating", LUC, "held", "Won every wrestling exchange."),
            chk("model", "Overall rating favours Lucindo", "overall", LUC, "held", "Swept the cards."),
            chk("model", "Fight Matrix rating favours Lucindo", "outside_rating", LUC, "held", "Won."),
            chk("model", "Reach favours Lucindo", "reach", LUC, "untested", "Fought in the clinch and on the mat."),
        ]),
}

# Judged performances, only where two outlets agree (Sherdog's play-by-play plus MMA Mania, MMA Junkie or Cageside Press).
# (bout key, fighter, opponent, domain, rating, skills, note); the source is the bout's outlets.
NOTES = [
    ("alexander-volkanovski-movsar-evloev", VOLK, EVL, "striking", 2.0, ["combinations", "power", "gnp"],
     "Out-struck the unbeaten challenger, hurt him with a combination late in round 2 and finished him on the floor."),
    ("petr-yan-merab-dvalishvili", YAN, MERAB, "wrestling", 1.5, ["td_def", "get_up"],
     "Gave up takedowns in rounds 1-2 but always stood; Dvalishvili completed 5 of a record 58 attempts and none late."),
    ("petr-yan-merab-dvalishvili", YAN, MERAB, "striking", 1.0, ["body_kicks", "combinations", "pressure"],
     "Took over from round 3 with body kicks and combinations and won the last three rounds on every card."),
    ("alexander-volkov-rizvan-kuniev", VOLKOV, KUN, "striking", 1.5, ["jab", "leg_kicks", "range", "clinch"],
     "Controlled range with the jab, body and calf kicks; Kuniev was switching stances by round 3."),
    ("alexander-volkov-rizvan-kuniev", VOLKOV, KUN, "grappling", 0.5, ["back_take", "rnc"],
     "Took the back late in round 3 and threatened the rear-naked choke."),
    ("abdul-rakhman-yakhyaev-nikita-krylov", YAKH, KRYL, "wrestling", 1.0, ["td_def", "clinch"],
     "Kept his balance against Krylov's takedown and trip attempts on the fence."),
    ("abdul-rakhman-yakhyaev-nikita-krylov", YAKH, KRYL, "grappling", 1.5, ["guillotine", "back_take"],
     "Deep guillotine, then transitioned to the back when Krylov survived it."),
    ("abdul-rakhman-yakhyaev-nikita-krylov", YAKH, KRYL, "striking", 1.5, ["knees", "gnp"],
     "Knee to the head from the back and punches for the round-1 stoppage."),
    ("grant-dawson-nurullo-aliev", DAW, ALIEV, "wrestling", 2.0, ["td_off", "control", "cardio"],
     "Five takedowns on the unbeaten Aliev, the fresher man from round 2, ending in full mount."),
    ("grant-dawson-nurullo-aliev", DAW, ALIEV, "striking", -0.5, ["strike_def"],
     "Dropped by a straight left in round 1 before taking over."),
    ("colby-thicknesse-asaf-chopurov", THICK, CHOP, "striking", 0.5, ["elbows", "knees", "clinch"],
     "Won round 2 with elbows, knees and combinations in the clinch."),
    ("colby-thicknesse-asaf-chopurov", THICK, CHOP, "wrestling", -1.0, ["td_def", "td_off"],
     "His own shots went nowhere and Chopurov took him down repeatedly in round 3."),
    ("colby-thicknesse-asaf-chopurov", THICK, CHOP, "grappling", 0.5, ["guillotine", "scramble"],
     "Threatened two guillotines in round 1 and got back up from every takedown."),
    ("kody-steele-noah-gugnon", STEELE, GUG, "striking", 1.5, ["combinations", "power", "durability"],
     "Weathered Gugnon's early jab and kicks, rocked him with a combination and knocked him out with a right hand."),
]

REVIEW = """A card the model read badly and the market read well: the model picked 6 of 14 winners with a log loss of 0.790 (0.722 on the 13 priced bouts), the market 10 of 13 at 0.676 and the blend 9 of 13 at 0.692. On the season the market still leads (0.583 log loss on 431 priced bouts, the model 0.638 on the same bouts). AI Picks scored 32 points to the model's 26, helped by the two title-fight overrides; the AI Bets went 1-2 (Yan-Dvalishvili to the distance won, Volkanovski-Evloev to the distance and Pico by decision lost).

Both title fights went the way our reads said, though not always how. Yan's takedown defence held exactly as the read claimed: Dvalishvili landed 5 of a record 58 attempts, and Yan took rounds 3 to 5 after losing the first two. Volkanovski's takedown defence held too (up from all three round-one takedowns), and the model's age and wear-and-tear case against him failed; but "neither finishes the other" failed when he stopped Evloev late in round two, after losing round one and, he said, fighting sick.

The finishing calls split. Yakhyaev stopped Krylov in round one as both records said, and Steele won by knockout in the brawl the pick said he should avoid. The misses were the one-shot power reads: Temirov's first-round power lost to Kavanagh's in round one, Murzakanov was finished by the head kick at range that the read itself had flagged as the danger, and Magomedov choked Rowston in under two minutes, so the claim that he fades under pressure was never tested. Pico won by an early knockout rather than the decision the bet needed. Three decisions are disputed (Thicknesse over Chopurov, Vagaev over Malkoun and Santos over Oki: Sherdog's scorers had the loser in all three); none of them settles whether the reads behind those picks were right.

No fight-night notes for this card."""


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
    for k, a, b, cat, r, sk, nt in NOTES:
        src = "; ".join(dict.fromkeys(o["url"] for o in cov[k]["outlets"]))
        notes.append({"date": DATE, "fighter": a, "opponent": b, "category": cat, "rating": r, "skills": sk, "note": nt, "source": src})
    fn.write_text(json.dumps(notes, ensure_ascii=False, indent=1) + "\n")

    out = Path(__file__).resolve().parents[3] / ".cache" / "recap_review.json"
    out.write_text(json.dumps({"event": EVENT, "date": DATE, "review": REVIEW, "notes_used": False, "written": WRITTEN,
                               "stories": doc["stories"]}, ensure_ascii=False))
    print(len(doc["stories"]), "stories;", len(NOTES), "fight notes; review ->", out)


if __name__ == "__main__":
    main()
