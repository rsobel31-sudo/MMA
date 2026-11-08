"""Card review for UFC Fight Night 293: Cortes-Acosta vs. Walker (UFC Vegas 124, 2026-11-07).

What happened in every bout (our own words, from Sherdog's and MMA Mania's play-by-play, MMA Junkie's live updates
through Yahoo, and Cageside Press, MMA Fighting and BJPenn.com where they covered a bout), the pre-fight claims checked
against the fights, judged performances for data/scouting/fight_notes.json where two outlets agree, and a dated note
in both fighters' scouting reports. Written Sunday 2026-11-08; the review text is left empty for the main session to
write.

The collected coverage needed two corrections, applied in main() before the stories are written (the next
`fight-recaps` run rebuilds the coverage from the outlets, so they live here):
- Petersen vs Lourenco: every outlet but Sherdog spells the Brazilian "Lorenco", so only Sherdog was matched. MMA
  Mania's prelim paragraph, MMA Junkie's live updates and its recap (through Yahoo) and Cageside Press's recap all
  describe the fight; they are added, so the bout is not single-source;
- Petersen vs Lourenco: no label. Sherdog's three scorers had it 1-1 after two rounds, but two of the official judges
  scored round 1 10-8 for Lourenco (MMA Junkie), so Petersen was behind on two cards when he finished it 13 seconds
  from the end: 'from behind'.
MMA Mania's prelim paragraph has Souza's knockout in round 2; it was round 1 (4:16) by every other outlet and the
official result. MMA Junkie lists Souza as "Jose Henrique".
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = "2026-11-07-ufc-fight-night-293-cortes-acosta-vs-walker"
EVENT, DATE, WRITTEN = "UFC Fight Night 293 - Cortes-Acosta vs. Walker", "2026-11-07", "2026-11-08"
UPDATED = "2026-11-08T20:00:00+00:00"
SHERDOG = "https://www.sherdog.com/news/news/UFC-Vegas-124-CortesAcosta-vs-Walker-playbyplay-results-round-scoring-203525"
MANIA = "https://www.mmamania.com/ufc-results/483615/ufc-vegas-124-live-results-highlights-play-by-play-cortes-acosta-vs-walker"
JUNKIE = "https://sports.yahoo.com/articles/ufc-fight-night-293-live-210057052.html"
CAGESIDE_PETERSEN = "https://cagesidepress.com/2026/11/07/ufc-vegas-124-thomas-petersen-survives-foul-filled-first-frame-stops-gabriel-lorenco-late/"
JUNKIE_PETERSEN = "https://sports.yahoo.com/articles/ufc-vegas-124-video-thomas-004820248.html"
CAGESIDE_FERNANDO = "https://cagesidepress.com/2026/11/07/lucas-fernando-shuts-down-billy-elekanas-wrestling-in-impressive-victory/"
CAGESIDE_RAPOSO = "https://cagesidepress.com/2026/11/07/mitch-raposo-stuns-marcos-degli-snaps-impressive-win-streak/"
MMAF_SUAREZ = "https://www.mmafighting.com/ufc/519960/ufc-vegas-124-results-tatiana-suarez-grinds-her-way-to-decision-win-over-virna-jandiroba"
MANIA_WALKER = "https://www.mmamania.com/ufc-results/484919/ufc-vegas-124-results-biggest-winners-losers-from-cortes-acosta-vs-walker-last-night"
MANIA_SMITH = "https://www.mmamania.com/ufc-bonuses-and-awards/484643/official-ufc-vegas-124-post-fight-bonus-winners-results-paramount-waldo-walker"


def chk(by, claim, tag, favoured, verdict, note):
    return {"by": by, "claim": claim, "tag": tag, "favoured": favoured, "verdict": verdict, "note": note}


def sc(rnd, who, n=3):
    return [rnd] + [who] * n


WALKER, WCA = "Johnny Walker", "Waldo Cortes-Acosta"
SUAREZ, JAND = "Tatiana Suarez", "Virna Jandiroba"
SMITH, GRANT = "Elijah Smith", "Davey Grant"
FERN, ELEK = "Lucas Fernando", "Billy Elekana"
NINA, CACH = "Nina Nikolija Milosevic", "Priscila Cachoeira"
RAPOSO, DEGLI = "Mitch Raposo", "Marcos Degli"
SCHMID, NAKA = "Oliver Schmid", "Keiichiro Nakamura"
PET, LOUR = "Thomas Petersen", "Gabriel Lourenco"
KSILVA, GFERN = "Karine Silva", "Gabriella Fernandes"
MAGO, DELANO = "Murtazali Magomedov", "Jose Mauro Delano"
BASHI, CALD = "Austin Bashi", "Carlos Calderon"
PETRO, MANTAS = "Andre Petroski", "Mantas Kondratavicius"
KO, TURMAN = "Seok Hyeon Ko", "Wellington Turman"
SOUZA, PARSONS = "Jose Henrique Souza", "Jonny Parsons"

# Coverage corrections (see the module docstring): outlets to add, labels to set.
COVERAGE_FIX = {
    "thomas-petersen-gabriel-lourenco": dict(
        outlets=[{"outlet": "MMA Mania", "kind": "play-by-play", "url": MANIA},
                 {"outlet": "MMA Junkie", "kind": "play-by-play", "url": JUNKIE},
                 {"outlet": "Cageside Press", "kind": "recap", "url": CAGESIDE_PETERSEN},
                 {"outlet": "MMA Junkie", "kind": "recap", "url": JUNKIE_PETERSEN}],
        round_scores=[sc(1, "10-9 Lourenco"), sc(2, "10-9 Petersen")], closeness="from behind"),
}
NOT_RECAPS = set()

STORIES = {
    "johnny-walker-waldo-cortes-acosta": dict(
        summary="On nine days' notice, Walker circled and chopped Cortes-Acosta's lead leg with low kicks from the opening "
                "bell, while the much heavier man pinned him on the fence, put him down briefly and kneed him in the clinch; "
                "Sherdog's three scorers gave Walker round 1 on the kicks. Both were tired in round 2, and Cortes-Acosta took "
                "it with right hands and by finishing the round on top after Walker went down. Early in round 3 an overhand "
                "right wobbled Walker, but off a separation he landed a question-mark kick and a backfist, then dropped "
                "Cortes-Acosta with a right hand and finished him at 2:27, the first stoppage loss of Cortes-Acosta's career.",
        turning_point="Round 3: Walker's question-mark kick and backfist off Herzog's break, a minute after he had been "
                      "wobbled himself.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Walker gets knocked out when opponents press; the bigger, never-stopped Cortes-Acosta weathers R1 "
                "and walks him down: KO/TKO, R2", "durability", WCA, "failed",
                "Cortes-Acosta pressed, won round 2 and wobbled Walker in round 3, but Walker stayed up and stopped him."),
            chk("read", "Walker's chin against heavyweight power", "durability", WCA, "failed",
                "Took clean right hands in rounds 2 and 3, was wobbled once, and was never in real danger of going."),
            chk("read", "Walker freezes under pressure", "style", WCA, "failed",
                "Kept kicking with his back to the fence and landed the finishing sequence straight off a clinch break."),
            chk("read", "Walker's reach and explosiveness (against)", "explosiveness", WALKER, "held",
                "Won round 1 on low kicks at range and ended it with a spinning kick, backfist and right hand."),
            chk("model", "Fresher body favours Cortes-Acosta", "wear_and_tear", WCA, "mixed",
                "Walker slowed in round 2 and Cortes-Acosta looked the fresher man early in round 3, but Walker had the "
                "finish left in him."),
            chk("model", "Size gap favours Cortes-Acosta", "size_gap", WCA, "mixed",
                "The 23-pound edge told in the clinch and from top in round 2; it did not stop Walker."),
            chk("model", "Power vs chin favours Cortes-Acosta", "power_vs_chin", WCA, "failed",
                "His power wobbled Walker without dropping him; Walker's power stopped a man who had never been stopped."),
            chk("model", "Wrestling rating favours Cortes-Acosta", "wrestling_rating", WCA, "untested",
                "No takedown attempts; his top time in round 2 came when Walker went down in an exchange."),
            chk("model", "Overall rating favours Cortes-Acosta", "overall", WCA, "failed", "Knocked out in round 3."),
        ]),
    "tatiana-suarez-virna-jandiroba": dict(
        summary="Suarez went for single legs from the first exchange, but Jandiroba stayed upright on the fence, landing "
                "knees and elbows while hopping on one leg, and caught her with the cleaner right hands early in round 2. "
                "Suarez's top time came late in round 2, when she sprawled on a Jandiroba shot, and in round 3 off a takedown "
                "against the fence; she controlled from half guard with short elbows and got out of kneebars at the end of "
                "both rounds. Suarez won 30-27, 30-27, 29-28; all three Sherdog scorers had it 30-27.",
        turning_point="Late in round 2: Suarez's sprawl on Jandiroba's takedown attempt put her on top for the first time.",
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Suarez's wrestling against a grappler who has mostly been the one shooting; Jandiroba's guard keeps "
                "it on the cards: decision", "wrestling", SUAREZ, "held",
                "Won the fight from top position in rounds 2 and 3; Jandiroba's guard stopped any finish."),
            chk("read", "Suarez's wrestling vs Jandiroba's takedown defence", "wrestling", SUAREZ, "mixed",
                "Jandiroba stuffed nearly every single leg for seven minutes; Suarez got top position off a sprawl and one "
                "late takedown, and that won the rounds."),
            chk("read", "Jandiroba's submissions (against)", "submission", JAND, "mixed",
                "Kneebars at the end of round 2 and in round 3 and a near back take, but Suarez escaped each."),
            chk("read", "Suarez's injury history (against)", "injury", JAND, "failed",
                "No sign of it; she was the stronger fighter in round 3."),
            chk("model", "Fresher body favours Suarez", "wear_and_tear", SUAREZ, "held",
                "Controlled the last round; Jandiroba could not sweep her."),
            chk("model", "Wrestling edge favours Jandiroba", "wrestling_edge", JAND, "mixed",
                "Jandiroba won the clinch battles early; Suarez won the positions that decided the rounds."),
            chk("model", "Age favours Suarez", "age_curve", SUAREZ, "held", "The 38-year-old could not keep her off late."),
            chk("model", "Experience favours Jandiroba", "experience", JAND, "failed",
                "Lost every round on Sherdog's cards."),
        ]),
    "elijah-smith-davey-grant": dict(
        summary="Grant came forward with low kicks and they traded right hands, until Smith answered a left hand with a "
                "power shot that staggered Grant backward. Smith followed him and knocked him unconscious with a final right "
                "hand on the way down at 1:00 of round 1, the first knockout loss of Grant's 27-fight career. It earned "
                "Smith a $100,000 bonus.",
        turning_point=None,
        verdict="right, other reasons",
        checks=[
            chk("pick", "Grant has never been knocked out but has been submitted five times, so a Smith finish is a choke, "
                "after Grant's volume takes R1: submission, R2", "durability", SMITH, "failed",
                "Smith knocked Grant out in 60 seconds."),
            chk("read", "Age gap", "age", SMITH, "held", "The 40-year-old was out cold from the first real exchange."),
            chk("read", "Grant's durability and volume (against)", "durability", GRANT, "failed",
                "Knocked out for the first time, before his volume could start."),
            chk("model", "Fresher body favours Smith", "wear_and_tear", SMITH, "held",
                "The chin that had lasted 26 fights went at once."),
            chk("model", "Age favours Smith", "age_curve", SMITH, "held", "As the read's age gap."),
            chk("model", "Submission threat favours Smith", "submission_threat", SMITH, "untested",
                "Over by punches in a minute."),
            chk("model", "Striking exchange favours Grant", "striking_exchange", GRANT, "failed",
                "Grant pressed with leg kicks and lost the first exchange that mattered."),
            chk("model", "Wrestling edge favours Smith", "wrestling_edge", SMITH, "untested", "Never went to the mat."),
        ]),
    "lucas-fernando-billy-elekana": dict(
        summary="Fernando out-worked Elekana for two rounds with the jab, kicks to every level and knees and hooks to the "
                "body in the clinch, hurting him with a right hand and a knee in round 1 and turning him onto the fence "
                "every time Elekana went for the body lock. A tiring Fernando gave up a trip takedown in round 3 and spent "
                "most of it in closed guard, where Elekana won the round with elbows but did little damage. Fernando won "
                "29-28 on all three cards and all three of Sherdog's.",
        turning_point=None,
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "Override: Fernando's kicks to every level break down Elekana, who was hurt by body work before: "
                "KO/TKO, R2", "body_work", FERN, "mixed",
                "The body work hurt and slowed Elekana and won the first two rounds, but there was no stoppage and "
                "Fernando faded in round 3."),
            chk("read", "Fernando's volume vs Elekana's output", "volume", FERN, "held",
                "Out-landed him clearly in rounds 1 and 2."),
            chk("read", "Elekana's body-work problem", "body_work", FERN, "held",
                "Knees and hooks to the midsection had Elekana covering up late in round 1."),
            chk("read", "Fernando's turnaround (against)", "activity", ELEK, "mixed",
                "Fernando tired and lost round 3 to a takedown, but the fight was won by then."),
            chk("model", "Fight Matrix rating favours Elekana", "outside_rating", ELEK, "failed", "Lost the first two rounds clearly."),
            chk("model", "Striking rating favours Fernando", "striking_rating", FERN, "held", "Won the striking in every round he stood."),
            chk("model", "Overall rating favours Fernando", "overall", FERN, "held", "Won."),
        ]),
    "nina-nikolija-milosevic-priscila-cachoeira": dict(
        summary="Milosevic crashed in behind a jumping kick, took Cachoeira down in the first seconds and jumped to her back, "
                "then punched her from the back and mount for the rest of round 1, with a look at an arm-triangle; two of "
                "Sherdog's scorers had it 10-8. Cachoeira swung back early in round 2 and landed a combination, but Milosevic "
                "took her down again, went to mount and the back and finished her with elbows and punches at 3:40.",
        turning_point=None,
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "Cachoeira has been submitted five times after being dropped or taken down; Milosevic finishes "
                "early: submission, R1", "grappling", NINA, "mixed",
                "Taken down and on her back at once, as expected, but finished by ground strikes in round 2, not a choke."),
            chk("read", "Cachoeira's form and bottom game", "bottom_game", NINA, "held",
                "Offered almost no defence from underneath in either round."),
            chk("read", "Cachoeira's R1 power (against)", "power", CACH, "failed",
                "Taken down before she could throw in round 1; her round-2 flurry landed but did not trouble Milosevic."),
            chk("model", "Fresher body favours Milosevic", "wear_and_tear", NINA, "held", "Cachoeira had nothing left in round 2."),
            chk("model", "Overall rating favours Milosevic", "overall", NINA, "held", "Won every minute."),
            chk("model", "Fight Matrix rating favours Milosevic", "outside_rating", NINA, "held", "Won."),
            chk("model", "Wrestling rating favours Milosevic", "wrestling_rating", NINA, "held", "A takedown in each round."),
            chk("model", "Power vs chin favours Milosevic", "power_vs_chin", NINA, "held",
                "Stung Cachoeira with counters standing and stopped her with ground strikes."),
        ]),
    "mitch-raposo-marcos-degli": dict(
        summary="The debuting Degli won round 1 on the counter, staggering Raposo with a left hook and landing an elbow, "
                "and all three Sherdog scorers gave it to him. From round 2 Raposo took the center and out-threw him with "
                "one-twos, leg kicks and body shots while Degli waited; in round 3 an elbow opened a cut on Raposo's head, "
                "but he kept up the volume, hurt Degli to the body and reversed his late takedown attempt. Raposo won 29-28 "
                "on all three cards, ending Degli's 13-fight streak.",
        turning_point="Round 2: Degli stopped throwing and Raposo took the center for good.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Degli's finishing streak beats Raposo, who goes the distance and gets back up: decision", "overall",
                DEGLI, "failed", "It went to the cards as picked, but Raposo won the last two rounds on every card."),
            chk("read", "Degli's debut", "debut", DEGLI, "failed",
                "Sharp in round 1, then quiet: out-thrown in rounds 2 and 3 by a UFC veteran."),
            chk("read", "Raposo's durability (against)", "durability", RAPOSO, "held",
                "Took Degli's left hooks and a cutting elbow and kept coming for 15 minutes."),
            chk("model", "Overall rating favours Degli", "overall", DEGLI, "failed", "Lost the decision."),
            chk("model", "Fight Matrix rating favours Degli", "outside_rating", DEGLI, "failed",
                "The regional streak did not carry over."),
            chk("model", "Striking rating favours Degli", "striking_rating", DEGLI, "mixed",
                "Degli landed the harder single shots, but Raposo out-landed him in rounds 2 and 3."),
        ]),
    "oliver-schmid-keiichiro-nakamura": dict(
        summary="Schmid out-boxed Nakamura for two rounds, answering his inside leg kicks with cleaner combinations, left "
                "hooks and spinning kicks to the body, and won both on every Sherdog card; a low blow paused round 2. "
                "Nakamura came on in round 3 and floored Schmid with a left hook, nearly finishing him with punches, but "
                "Schmid got up, caught a kick for a takedown and saw out the round. Schmid won 29-28 on all three cards.",
        turning_point="Round 3: Nakamura's knockdown, and Schmid's takedown off a caught kick that bought him time.",
        verdict="wrong, close fight",
        checks=[
            chk("pick", "Nakamura gives away early exchanges and grows into fights; Schmid's losses came late: KO/TKO, R2",
                "slow_start", NAKA, "mixed",
                "The pattern was right: he lost rounds 1 and 2 and nearly finished Schmid late, but a round too late."),
            chk("read", "Nakamura's power", "power", NAKA, "mixed", "One knockdown in round 3; Schmid survived it."),
            chk("read", "Nakamura's layoff and slow starts (against)", "inactivity", SCHMID, "held",
                "Lost the first two rounds on every card."),
            chk("model", "Overall rating favours Nakamura", "overall", NAKA, "failed", "Lost the decision."),
            chk("model", "Striking rating favours Nakamura", "striking_rating", NAKA, "failed",
                "Schmid's boxing was the cleaner for two rounds."),
            chk("model", "Wrestling rating favours Nakamura", "wrestling_rating", NAKA, "untested",
                "One stuffed shot and one takedown off a caught kick; a kickboxing fight."),
            chk("model", "Power vs chin favours Nakamura", "power_vs_chin", NAKA, "mixed",
                "Dropped Schmid and nearly finished him; Schmid's chin held up enough."),
        ]),
    "thomas-petersen-gabriel-lourenco": dict(
        summary="Petersen took the debuting Lourenco down early and reached his back, but Lourenco escaped and turned the "
                "round: an illegal knee to the grounded Petersen that the referee missed, then a left hook and a right hand "
                "that floored him twice and knees and elbows against the fence; Petersen survived, and two judges scored it "
                "10-8. Lourenco had emptied his tank, and Petersen dropped him with a left hook in the first minute of round "
                "2 and nearly finished him; in round 3 he took him down, worked from half guard with elbows and punches, and "
                "the referee stopped it at 4:47, 13 seconds from what would likely have been a majority draw.",
        turning_point="The opening of round 2: Petersen's left hook that dropped an exhausted Lourenco.",
        verdict="wrong, close fight",
        checks=[
            chk("model", "Fresher body favours Lourenco", "wear_and_tear", LOUR, "failed",
                "Lourenco was the one who tired: gassed by the end of round 1 and spent in round 3."),
            chk("model", "Wrestling edge favours Petersen", "wrestling_edge", PET, "held",
                "Takedowns in rounds 1 and 3; the finish came from top position."),
            chk("model", "Overall rating favours Lourenco", "overall", LOUR, "failed",
                "Nearly stopped Petersen in round 1, then lost the next two rounds and was finished."),
        ]),
    "karine-silva-gabriella-fernandes": dict(
        summary="Most of the fight was clinch work on the fence, where the bigger Fernandes kept reversing position and "
                "kneeing the body; Silva took round 1 on Sherdog's cards by countering a takedown into top position at the "
                "horn. Fernandes swept Silva off her feet with a low kick in round 2 and won it, and Silva took round 3 with "
                "the busier boxing. Silva won 29-28 on all three cards and all three of Sherdog's; the outlets called it "
                "flat.",
        turning_point=None,
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "Silva wins the grappling exchanges over 15 minutes against a fighter held down by grapplers: "
                "decision", "grappling", KSILVA, "mixed",
                "Decision right, but Fernandes was the stronger in the clinch; Silva's one takedown came at the end of "
                "round 1 and she won round 3 standing."),
            chk("read", "Fernandes's bottom game", "bottom_game", KSILVA, "untested",
                "Fernandes was on her back only in the last seconds of round 1."),
            chk("read", "Silva's recent form (against)", "form", GFERN, "failed", "Won, if narrowly."),
            chk("model", "Overall rating favours Silva", "overall", KSILVA, "held", "Won two rounds of three."),
            chk("model", "Fight Matrix rating favours Silva", "outside_rating", KSILVA, "held", "Won."),
            chk("model", "Striking rating favours Silva", "striking_rating", KSILVA, "mixed",
                "The busier striker, which won her round 3, though Fernandes's low kick dropped her in round 2."),
        ]),
    "murtazali-magomedov-jose-mauro-delano": dict(
        summary="Delano won round 1 with leg kicks and volume until he slipped on a kick and Magomedov landed on top. "
                "Magomedov took him down twice in round 2 and landed a head kick, but Delano got up each time and finished "
                "the round strongly to the body, and he was the fresher man in round 3, buckling Magomedov with a leg kick. "
                "Magomedov's late takedown and an overhand left that dropped Delano in the closing seconds won him 29-28 on "
                "all three official cards; all three Sherdog scorers had Delano 29-28.",
        turning_point="The knockdown in the last seconds of round 3, which by MMA Mania's account swung the round.",
        verdict="right on the cards, wrong on the fight",
        checks=[
            chk("pick", "Magomedov finishes before Delano's volume builds: KO/TKO, R1", "finishing", MAGO, "failed",
                "His first decision: Delano out-landed him in rounds 1 and 3."),
            chk("read", "Magomedov untested late", "cardio", DELANO, "held",
                "Slowed in round 3, where Delano was the fresher man, though he found a late knockdown."),
            chk("read", "Magomedov's finishing (both ways)", "finishing", MAGO, "failed",
                "No finish either way; the knockdown came too late."),
            chk("model", "Wrestling edge favours Magomedov", "wrestling_edge", MAGO, "held",
                "Takedowns in rounds 2 and 3 are what won him the official cards."),
            chk("model", "Striking exchange favours Delano", "striking_exchange", DELANO, "held",
                "Out-struck him in rounds 1 and 3, and late in round 2."),
            chk("model", "Fresher body favours Magomedov", "wear_and_tear", MAGO, "failed", "Delano was the fresher in round 3."),
        ]),
    "austin-bashi-carlos-calderon": dict(
        summary="Calderon, on four days' notice, came out aggressive and they traded wildly before Bashi drove through for "
                "a takedown. Bashi shed a guillotine, scrambled to the back and finished with a rear-naked choke at 1:07 of "
                "round 1.",
        turning_point=None,
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Bashi's wrestling and back takes on a full camp tell once the short-notice man tires: submission, R2",
                "wrestling", BASHI, "held",
                "Takedown, back, choke, as picked; it came in round 1, before tiring could matter."),
            chk("read", "Calderon on four days' notice", "short_notice", BASHI, "untested", "Over in 67 seconds."),
            chk("read", "Calderon's thin data", "competition", BASHI, "held",
                "Taken down and back-taken at once by his first UFC opponent; the market's 81% was the better number."),
            chk("read", "Bashi's late fade (against)", "cardio", CALD, "untested", "Over in round 1."),
            chk("read", "Calderon's submissions (against)", "submission", CALD, "failed",
                "His guillotine was shed at once."),
            chk("model", "Wrestling edge favours Bashi", "wrestling_edge", BASHI, "held", "Got the takedown he needed."),
            chk("model", "Submission threat favours Bashi", "submission_threat", BASHI, "held", "Finished with the choke."),
            chk("model", "Height favours Calderon", "height", CALD, "untested", "Over before range mattered."),
        ]),
    "andre-petroski-mantas-kondratavicius": dict(
        summary="Kondratavicius hit Petroski hard every time he came in during round 1, stuffing his early shots, and won "
                "it on all three Sherdog cards despite Petroski's late takedown to side control. In round 2 Petroski took him "
                "down again, smothered him in half guard, moved to the back and mount and broke him with punches and "
                "elbows until the stoppage at 4:39, ending a three-fight skid.",
        turning_point="Petroski's single-leg takedown early in round 2; Kondratavicius never got up.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Petroski is caught by a clean shot as he closes distance; Kondratavicius, a front-loaded puncher, "
                "finishes early: KO/TKO, R1", "durability", MANTAS, "failed",
                "Kondratavicius landed hard in round 1 and won it, but Petroski took the shots and got his takedowns."),
            chk("read", "Kondratavicius's cardio past 10 minutes", "cardio", PETRO, "held",
                "Wilting under top pressure in the second half of round 2."),
            chk("read", "Petroski's takedowns and control", "wrestling", PETRO, "held",
                "A takedown late in round 1 and the fight-winning one in round 2."),
            chk("read", "Petroski's chin (against)", "durability", MANTAS, "failed",
                "Ate several big shots in round 1 and was never dropped."),
            chk("model", "Fresher body favours Kondratavicius", "wear_and_tear", MANTAS, "failed",
                "The worn veteran was the stronger man in round 2."),
            chk("model", "Striking rating favours Kondratavicius", "striking_rating", MANTAS, "mixed",
                "Won round 1 standing; it counted for nothing once Petroski had him down."),
            chk("model", "Power vs chin favours Kondratavicius", "power_vs_chin", MANTAS, "failed",
                "Landed his power shots without dropping Petroski."),
            chk("model", "Overall rating favours Kondratavicius", "overall", MANTAS, "failed", "Stopped in round 2."),
            chk("model", "Fight Matrix rating favours Kondratavicius", "outside_rating", MANTAS, "failed", "Lost."),
        ]),
    "seok-hyeon-ko-wellington-turman": dict(
        summary="Ko threw Turman with a judo throw midway through round 1 and slammed him down again late. Turman had his "
                "best spell in round 2 with the jab, right hands and a spinning backfist (one Sherdog scorer gave him the "
                "round) until Ko took him down again. In round 3 Ko took him down in the first 30 seconds, passed to mount, "
                "attacked a von Flue choke and an arm-triangle and punched him to the bell: 30-27 on all three cards.",
        turning_point=None,
        verdict="right, for our reasons",
        checks=[
            chk("model", "Wrestling rating favours Ko", "wrestling_rating", KO, "held",
                "A throw or takedown in every round and long spells on top."),
            chk("model", "Layoff favours Ko", "layoff", KO, "mixed",
                "Turman, out since 2023, slowed early in round 2 but then had his best spell of the fight."),
            chk("model", "Overall rating favours Ko", "overall", KO, "held", "Won every round on the official cards."),
            chk("model", "Striking rating favours Ko", "striking_rating", KO, "held",
                "Landed the better single shots; Turman's striking won him only part of round 2."),
            chk("model", "Fight Matrix rating favours Ko", "outside_rating", KO, "held", "Won."),
        ]),
    "jose-henrique-souza-jonny-parsons": dict(
        summary="Parsons, back after more than three years out, threw low kicks and head kicks but could not get past the "
                "6-foot-3 Souza's jab, and landed little. Souza built on the jab with straight lefts and hooks and flattened "
                "him with a right uppercut and left hook at 4:16 of round 1.",
        turning_point=None,
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Override: Parsons's rust shows once the pace rises against Souza's jab and knees: KO/TKO, R2",
                "inactivity", SOUZA, "held",
                "Parsons was out-ranged and barely landed; the knockout came a round early and off the jab, not the knees."),
            chk("read", "Parsons's 40-month layoff and injuries", "inactivity", SOUZA, "held",
                "Low output and no answer to the range."),
            chk("read", "Age 35", "age", SOUZA, "held", "Slow to close distance, though hard to separate from the layoff."),
            chk("read", "Parsons's Muay Thai (against)", "style", PARSONS, "failed",
                "A few hard low kicks, and never got the clinch where he does his work."),
            chk("model", "Layoff favours Souza", "layoff", SOUZA, "held", "As the read."),
            chk("model", "Fresher body favours Souza", "wear_and_tear", SOUZA, "untested", "Barely touched; over in round 1."),
            chk("model", "Height favours Souza", "height", SOUZA, "held", "His length and jab decided the fight."),
            chk("model", "Overall rating favours Souza", "overall", SOUZA, "held", "Won inside a round."),
        ]),
}

# Judged performances, only where two outlets agree (Sherdog's play-by-play plus MMA Mania, MMA Junkie, Cageside Press,
# MMA Fighting or BJPenn.com). (bout key, fighter, opponent, domain, rating, skills, note); the source is the bout's outlets.
NOTES = [
    ("johnny-walker-waldo-cortes-acosta", WALKER, WCA, "striking", 1.5, ["leg_kicks", "spinning", "power", "durability"],
     "Chopped the lead leg from range, took Cortes-Acosta's right hands, and finished him with a question-mark kick, "
     "backfist and right hand in round 3."),
    ("johnny-walker-waldo-cortes-acosta", WALKER, WCA, "wrestling", -0.5, ["clinch", "td_def"],
     "Pinned on the fence in the clinch by the heavier man and ended round 2 under him in half guard."),
    ("tatiana-suarez-virna-jandiroba", SUAREZ, JAND, "wrestling", 1.0, ["td_off", "sprawl", "control"],
     "Most single legs were stopped on the fence, but she got top position late in rounds 2 and 3 and kept it."),
    ("tatiana-suarez-virna-jandiroba", SUAREZ, JAND, "grappling", 1.0, ["control", "sub_def", "gnp"],
     "Held a dangerous guard down in half guard with short elbows and escaped the kneebar attempts."),
    ("tatiana-suarez-virna-jandiroba", SUAREZ, JAND, "striking", -0.5, ["defense"],
     "Took Jandiroba's cleaner right hands and elbows in the first round and a half."),
    ("elijah-smith-davey-grant", SMITH, GRANT, "striking", 2.0, ["power", "counter"],
     "Knocked out a never-stopped veteran with the first power exchange, inside a minute."),
    ("lucas-fernando-billy-elekana", FERN, ELEK, "striking", 1.5, ["body_kicks", "knees", "jab", "volume"],
     "Out-landed Elekana for two rounds with kicks to every level and clinch knees to the body, and hurt him in round 1."),
    ("lucas-fernando-billy-elekana", FERN, ELEK, "wrestling", 0.5, ["clinch", "td_def"],
     "Turned Elekana on the fence for two rounds, but gave up a trip takedown when tired in round 3."),
    ("nina-nikolija-milosevic-priscila-cachoeira", NINA, CACH, "wrestling", 2.0, ["td_off", "control"],
     "A takedown in the first seconds and another in round 2, both straight to dominant position."),
    ("nina-nikolija-milosevic-priscila-cachoeira", NINA, CACH, "grappling", 1.5, ["back_take", "mount", "gnp"],
     "Took the back and mount at will and punched from there for most of two rounds until the stoppage."),
    ("mitch-raposo-marcos-degli", RAPOSO, DEGLI, "striking", 1.0, ["volume", "pressure", "body_shots"],
     "Lost round 1 to Degli's counters, then out-threw him in rounds 2 and 3 and hurt him to the body."),
    ("oliver-schmid-keiichiro-nakamura", SCHMID, NAKA, "striking", 0.5, ["boxing", "body_kicks", "spinning"],
     "Out-boxed Nakamura for two rounds with spinning kicks to the body; dropped and nearly finished in round 3."),
    ("thomas-petersen-gabriel-lourenco", PET, LOUR, "wrestling", 1.0, ["td_off", "control"],
     "Took Lourenco down in rounds 1 and 3 and finished him from half guard."),
    ("thomas-petersen-gabriel-lourenco", PET, LOUR, "striking", -0.5, ["durability", "power", "gnp"],
     "Dropped twice and badly hurt in round 1; dropped Lourenco back early in round 2 and finished with ground strikes."),
    ("karine-silva-gabriella-fernandes", KSILVA, GFERN, "wrestling", -0.5, ["clinch"],
     "Out-muscled on the fence for long spells; her one takedown came at the round-1 horn."),
    ("murtazali-magomedov-jose-mauro-delano", MAGO, DELANO, "wrestling", 1.0, ["td_off", "trips"],
     "Took Delano down in each round, though he got back up every time."),
    ("murtazali-magomedov-jose-mauro-delano", MAGO, DELANO, "striking", -1.0, ["leg_kick_def", "volume", "cardio"],
     "Out-landed in rounds 1 and 3 and buckled by a leg kick; dropped Delano only in the closing seconds."),
    ("austin-bashi-carlos-calderon", BASHI, CALD, "grappling", 2.0, ["sub_def", "back_take", "rnc"],
     "Shed a guillotine, took the back and finished with a rear-naked choke in 67 seconds."),
    ("andre-petroski-mantas-kondratavicius", PETRO, MANTAS, "wrestling", 1.5, ["td_off", "control"],
     "Kept shooting after being hit in round 1 and held Kondratavicius down for almost all of round 2."),
    ("andre-petroski-mantas-kondratavicius", PETRO, MANTAS, "grappling", 1.5, ["gnp", "back_take", "mount"],
     "Advanced to the back and mount and finished with punches and elbows."),
    ("andre-petroski-mantas-kondratavicius", PETRO, MANTAS, "striking", -1.0, ["defense"],
     "Hit hard on the way in throughout round 1 and lost it on every Sherdog card."),
    ("seok-hyeon-ko-wellington-turman", KO, TURMAN, "wrestling", 2.0, ["judo_throw", "td_off", "control"],
     "A judo throw, a slam and a takedown in every round, with long top control."),
    ("seok-hyeon-ko-wellington-turman", KO, TURMAN, "grappling", 1.0, ["mount", "back_take", "gnp"],
     "Passed to mount in round 3, threatened chokes and punched to the bell."),
    ("jose-henrique-souza-jonny-parsons", SOUZA, PARSONS, "striking", 2.0, ["jab", "range", "uppercut", "power"],
     "Kept Parsons on the end of his jab for four minutes and knocked him out with an uppercut and left hook."),
]

# What each fight showed, folded into both fighters' scouting reports: a dated news item, and small edits to patterns
# and concerns only where the fight clearly showed something. replace: {old line: new line} in patterns or concerns.
REPORTS = {
    "johnny-walker": dict(
        src=MANIA_WALKER,
        text="Knocked out Waldo Cortes-Acosta at 2:27 of R3 (question-mark kick, backfist, right hand) on nine days' notice, "
             "after winning R1 on leg kicks, losing R2, and being wobbled early in R3; Fight of the Night. Cortes-Acosta's "
             "first stoppage loss.",
        add_patterns=["Took heavyweight power and finished a bigger, never-stopped man in R3 (Cortes-Acosta)"],
        add_concerns=["Slowed in R2 at heavyweight and ended the round under Cortes-Acosta"]),
    "waldo-cortes-acosta": dict(
        src=SHERDOG,
        text="Knocked out by Johnny Walker at 2:27 of R3, his first stoppage loss: lost R1 to leg kicks, won R2 with right "
             "hands and top position, wobbled Walker early in R3, then was caught by a question-mark kick, backfist and "
             "right hand off a clinch break.",
        replace={"Never finished; all four losses on the cards":
                 "Stopped for the first time by Walker (R3, Nov. 2026); his other four losses went the distance"},
        add_concerns=["Loading up and missing big; Walker said he waited for the miss to counter"]),
    "tatiana-suarez": dict(
        src=MMAF_SUAREZ,
        text="Beat Virna Jandiroba by unanimous decision (30-27, 30-27, 29-28): Jandiroba stuffed most of her single legs "
             "for a round and a half, but Suarez got on top late in R2 and R3, held her in half guard and escaped kneebar "
             "attempts. Called for a title shot.",
        add_patterns=["Neutralises a dangerous guard from half guard over full rounds (Jandiroba)"]),
    "virna-jandiroba": dict(
        src=SHERDOG,
        text="Lost to Tatiana Suarez by unanimous decision (30-27, 30-27, 29-28). Defended Suarez's single legs on the fence "
             "with knees and elbows and landed the cleaner right hands early, but was held in half guard late in R2 and "
             "for most of R3; her kneebars came close without finishing.",
        add_patterns=["Strong single-leg defence on the fence, with elbows and knees; kneebar attacks off her back"]),
    "elijah-smith": dict(
        src=MANIA_SMITH,
        text="Knocked out Davey Grant at 1:00 of R1, the first knockout loss of Grant's career, and earned a $100,000 bonus.",
        add_patterns=["One-punch power: knocked out the never-stopped Grant in the first exchange"]),
    "davey-grant": dict(
        src=SHERDOG,
        text="Knocked out by Elijah Smith at 1:00 of R1, the first knockout loss of his career, after opening with low kicks.",
        replace={"Very durable to strikes": "Very durable to strikes until Smith knocked him out in 60 seconds at age 40 (Nov. 2026)"}),
    "lucas-fernando": dict(
        src=CAGESIDE_FERNANDO,
        text="Beat Billy Elekana by unanimous decision (29-28 x3): won R1-R2 with kicks to every level and clinch knees to "
             "the body, turning Elekana on the fence, then tired and gave up a trip takedown in R3.",
        add_patterns=["Strong in the clinch: turns opponents onto the fence and knees the body"],
        add_concerns=["Tired in R3 and was taken down (Elekana)"]),
    "billy-elekana": dict(
        src=CAGESIDE_FERNANDO,
        text="Lost to Lucas Fernando by unanimous decision (29-28 x3): hurt by a right hand and body knees in R1 and "
             "out-worked for two rounds, then won R3 with a trip takedown and elbows from the guard.",
        add_patterns=["Turns to body locks and trips when behind; won R3 from top against Fernando"]),
    "nina-nikolija-milosevic": dict(
        src=SHERDOG,
        text="Stopped Priscila Cachoeira with elbows and punches at 3:40 of R2: took her down in the first seconds and rode "
             "her back for all of R1 (10-8 on two Sherdog cards), then took her down again to mount in R2.",
        add_patterns=["Immediate takedown to the back or mount and sustained ground-and-pound (Cachoeira)"]),
    "priscila-cachoeira": dict(
        src=SHERDOG,
        text="Stopped by Nina Milosevic's ground strikes at 3:40 of R2: taken down in the first seconds and controlled from "
             "the back for all of R1; landed one combination early in R2 before being taken down again.",
        add_patterns=["Taken down and back-taken at once by Milosevic; little defence from underneath"]),
    "mitch-raposo": dict(
        src=CAGESIDE_RAPOSO,
        text="Beat the debuting Marcos Degli by unanimous decision (29-28 x3), ending his 13-fight streak: lost R1 to Degli's "
             "counters, then out-threw him with one-twos, leg kicks and body shots in R2-R3 despite a bad cut, and reversed "
             "his late takedown.",
        add_patterns=["Out-worked a finisher with volume and body shots in R2-R3 and stayed strong late (Degli)"]),
    "marcos-degli": dict(
        src=CAGESIDE_RAPOSO,
        text="Lost his UFC debut to Mitch Raposo by unanimous decision (29-28 x3), ending a 13-fight streak: won R1 with a "
             "left hook and an elbow, then threw too little in R2-R3 and was out-landed.",
        replace={"No information yet on how he handles adversity at this level":
                 "Output dropped after R1 against a busy veteran (Raposo); out-thrown over 15 minutes"}),
    "oliver-schmid": dict(
        src=SHERDOG,
        text="Beat Keiichiro Nakamura by unanimous decision (29-28 x3): out-boxed him with left hooks and spinning body kicks "
             "in R1-R2, then was dropped and nearly finished in R3 before a takedown off a caught kick saw him through.",
        add_patterns=["Clean boxing and spinning body kicks won the early rounds against a puncher (Nakamura)"],
        replace={"Durability: stopped by strikes in his last two losses":
                 "Durability: stopped by strikes in his last two losses; dropped and nearly finished in R3 by Nakamura"}),
    "keiichiro-nakamura": dict(
        src=SHERDOG,
        text="Lost his UFC debut to Oliver Schmid by unanimous decision (29-28 x3): out-boxed in R1-R2, then dropped Schmid "
             "with a left hook in R3 and nearly finished him, but tired in the last minute.",
        add_concerns=["Gave away R1-R2 again at UFC level; the late rally fell short (Schmid)"]),
    "thomas-petersen": dict(
        src=CAGESIDE_PETERSEN,
        text="Stopped Gabriel Lourenco with ground strikes at 4:47 of R3, from behind: dropped twice and hit with an illegal "
             "knee in R1 (two judges scored it 10-8), then dropped an exhausted Lourenco early in R2 and took him down "
             "and finished him from half guard in R3.",
        replace={"Clinch and wrestling control; UFC wins all by decision":
                 "Clinch and wrestling control; first UFC finish was ground-and-pound from half guard (Lourenco, R3)"},
        add_patterns=["Survived a bad first round and won late on pressure and takedowns (Lourenco)"]),
    "gabriel-lourenco": dict(
        src=CAGESIDE_PETERSEN,
        text="Lost his UFC debut to Thomas Petersen by TKO at 4:47 of R3: dropped Petersen twice in R1 (with an illegal "
             "knee and elbows to the back of the head the referee missed), but gassed, was dropped early in R2 and was "
             "taken down and finished in R3.",
        replace={"Untested past R1": "Cardio: emptied his tank in R1 and was finished in R3 in his UFC debut (Petersen)",
                 "Takedown defense unknown": "Taken down in R1 and R3 by Petersen"}),
    "karine-silva": dict(
        src=SHERDOG,
        text="Beat Gabriella Fernandes by unanimous decision (29-28 x3) in a clinch-heavy fight: took R1 with a takedown at "
             "the horn, lost R2 (swept by a low kick), and won R3 with the busier boxing.",
        add_concerns=["Loses clinch position on the fence to a stronger flyweight (Fernandes)"]),
    "gabriella-fernandes": dict(
        src=SHERDOG,
        text="Lost to Karine Silva by unanimous decision (29-28 x3): the stronger in the clinch and won R2 with low kicks, "
             "but was taken down at the end of R1 and out-boxed in R3.",
        add_patterns=["Strong in the clinch; reverses position on the fence"]),
    "murtazali-magomedov": dict(
        src=SHERDOG,
        text="Beat Jose Delano by unanimous decision (29-28 x3), his first fight to go the distance; all three Sherdog "
             "scorers had Delano 29-28. Took him down in R2 and R3, but was out-landed and buckled by a leg kick; a "
             "knockdown in the closing seconds likely won him R3. Taken to hospital for precautionary checks afterward.",
        replace={"Never been past R3 or to the judges":
                 "First decision (Delano): slowed in R3 and Sherdog's scorers had him losing"}),
    "jose-mauro-delano": dict(
        src=SHERDOG,
        text="Lost to Murtazali Magomedov by unanimous decision (29-28 x3), though all three Sherdog scorers had him winning "
             "29-28: out-landed him with leg kicks and body work and got up from every takedown, but was dropped in the "
             "closing seconds.",
        replace={"Takedown defense untested against a strong wrestler":
                 "Taken down repeatedly by Magomedov, though he got up each time"}),
    "austin-bashi": dict(
        src=SHERDOG,
        text="Submitted short-notice debutant Carlos Calderon with a rear-naked choke at 1:07 of R1, off a takedown and a "
             "back take after shedding a guillotine."),
    "carlos-calderon": dict(
        src=SHERDOG,
        text="Submitted by Austin Bashi (rear-naked choke) at 1:07 of R1 in his short-notice UFC debut: taken down after a "
             "wild exchange, his guillotine failed and Bashi took his back.",
        replace={"Taken down and submitted by the one UFC-calibre prospect he has faced (Montes)":
                 "Taken down and submitted by both UFC-calibre opponents he has faced (Montes; Bashi in 67 seconds)"}),
    "andre-petroski": dict(
        src=SHERDOG,
        text="Stopped Mantas Kondratavicius with punches at 4:39 of R2, ending a three-fight skid: hit hard and lost R1, "
             "then took him down early in R2 and broke him down from half guard, the back and mount.",
        add_patterns=["Keeps shooting after being hit; once on top, finishes a striker (Kondratavicius, R2)"]),
    "mantas-kondratavicius": dict(
        src=SHERDOG,
        text="Stopped by Andre Petroski's punches at 4:39 of R2: won R1 landing hard every time Petroski came in, then was "
             "taken down early in R2 and could not get up.",
        add_patterns=["Could not get up from bottom against a wrestler; wilted under top pressure in R2 (Petroski)"]),
    "ko-seok-hyeon": dict(
        src=SHERDOG,
        text="Beat Wellington Turman by unanimous decision (30-27 x3): a judo throw and a slam in R1, a takedown late in R2 "
             "after Turman's best spell, and mount, choke attempts and ground strikes in R3.",
        replace={"All three UFC fights went to decision": "All four UFC fights went to decision"}),
    "wellington-turman": dict(
        src=SHERDOG,
        text="Lost to Ko Seok-hyeon by unanimous decision (30-27 x3) in his first fight since 2023: thrown and taken down "
             "in every round; had his best spell on the feet in R2."),
    "jose-henrique-souza": dict(
        src=SHERDOG,
        text="Knocked out Jonny Parsons with a right uppercut and left hook at 4:16 of R1, after keeping him at the end of "
             "the jab all round.",
        add_patterns=["Long jab sets up an uppercut-hook finish (Parsons, R1)"]),
    "jonny-parsons": dict(
        src=SHERDOG,
        text="Knocked out by Jose Henrique Souza at 4:16 of R1 in his first fight in about 40 months: out-ranged by Souza's "
             "jab and landed little besides low kicks."),
}

REVIEW = """A card where the market was only a little ahead: it picked 8 of 11 priced winners (log loss 0.589), the model 10 of 14 (0.694, 0.629 on the priced bouts), and the blend did best (0.578). On the season the market still leads, 0.581 on 454 priced bouts against the model's 0.640 on the same bouts. AI Picks scored 28 points, level with the model again; both AI Bets lost, Cortes-Acosta on the moneyline and Smith by submission, on the two fights where the durability read was most wrong.

The lesson of the night is durability, in both directions. Walker, stopped six times before, absorbed Cortes-Acosta's pressure and knocked him out in round 3 with a kick, backfist and right hand; Petroski, knocked out in his last two, survived Kondratavicius's early power and stopped him in round 2. Meanwhile Davey Grant, never knocked out in 26 fights, was out in 60 seconds. The model's two biggest 'fresher body' leans (Kondratavicius and Cortes-Acosta) both lost. The one read that went against the model and the market on durability, Petroski over the fading Kondratavicius, was the right one.

The grappling and layoff reads held: Suarez out-wrestled Jandiroba for a clear decision, Bashi choked out the short-notice Calderon in round 1, Ko controlled the long-absent Turman, and Souza knocked out Parsons in his first fight in over three years. The model overrated two regional prospects: Degli lost a clear decision to Raposo and Nakamura dropped a close one to Schmid. Two misses were coin flips: Petersen came from behind (two judges had round 1 10-8 for Lourenco) to stop him late in round 3, and Magomedov's decision over Delano was disputed, with all three Sherdog scorers having Delano.

A data note: the card score uses the model's first logged number for each bout, made a month before the card (it gives the model 85% on Raposo where it had Degli at 72% on fight week), so these card numbers flatter the model slightly. No owner's notes for this card."""


def main():
    f = ROOT / "recaps" / f"{ID}.json"
    doc = json.loads(f.read_text())
    cov = doc["coverage"]
    for k, fix in COVERAGE_FIX.items():
        c = cov[k]
        seen = {(o["outlet"], o["url"]) for o in c["outlets"]}
        c["outlets"] = c["outlets"] + [o for o in fix.get("outlets", []) if (o["outlet"], o["url"]) not in seen]
        if "round_scores" in fix:
            c["round_scores"] = fix["round_scores"]
            c["closeness"] = fix["closeness"]
    for c in cov.values():
        c["outlets"] = [o for o in c["outlets"] if o["url"] not in NOT_RECAPS]
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
        before = rep.get("patterns", []) + rep.get("concerns", [])
        missing = [old for old, new in r.get("replace", {}).items() if old not in before and new not in before]
        assert not missing, (slug, missing)
        for field in ("patterns", "concerns"):
            lines = [r.get("replace", {}).get(x, x) for x in rep.get(field, [])]
            lines += [x for x in r.get(f"add_{field}", []) if x not in lines]
            rep[field] = lines
        rep["updated"] = UPDATED
        # keep each file's own convention: raw non-ASCII if it had any, escaped otherwise
        rf.write_text(json.dumps(rep, ensure_ascii=raw.isascii(), indent=1) + "\n")

    out = Path(__file__).resolve().parents[3] / ".cache" / "recap_review.json"
    out.write_text(json.dumps({"event": EVENT, "date": DATE, "review": REVIEW, "notes_used": False, "written": WRITTEN,
                               "stories": doc["stories"]}, ensure_ascii=False))
    print(len(doc["stories"]), "stories;", len(NOTES), "fight notes;", len(REPORTS), "reports; review ->", out)


if __name__ == "__main__":
    main()
