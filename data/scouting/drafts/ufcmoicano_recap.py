"""Card review for UFC Fight Night 292: Moicano vs. Nolan (UFC Vegas 123, 2026-10-31).

What happened in every bout (our own words, from Sherdog's and MMA Mania's play-by-play, MMA Junkie's live updates
through Yahoo and Cageside Press on the main event), the pre-fight claims checked against the fights, and judged
performances for data/scouting/fight_notes.json where two outlets agree. Written Sunday 2026-11-01; the review text
is left empty for the main session to write.

The collected coverage needed five corrections, applied in main() before the stories are written (the next
`fight-recaps` run rebuilds the coverage from the outlets, so they live here):
- the main event: the results list Moicano under his legal name (Renato Carneiro), so no outlet matched it;
- Hope vs Marshall: Sherdog's section ("Francis Marshall (148)*") was not matched, and its round scores were
  attached to Sezinando vs Berggren, which keeps only its own round 1;
- Reese vs Gall: round 1 was 9-9 on all three Sherdog cards (Reese docked a point), not two cards named after scorers;
- Luana vs Yana Santos: labelled 'disputed' because both surnames are Santos; Sherdog had it 2-1 for Luana: close;
- two outlet items matched to bouts are pre-fight pieces (Cageside on Erosa's retirement, MMA Fighting on Luana
  Santos's title hopes), not recaps, and are left out of the sources.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = "2026-10-31-ufc-fight-night-292-moicano-vs-nolan"
EVENT, DATE, WRITTEN = "UFC Fight Night 292 - Moicano vs. Nolan", "2026-10-31", "2026-11-01"
SHERDOG = "https://www.sherdog.com/news/news/UFC-Vegas-123-Moicano-vs-Nolan-playbyplay-results-round-scoring-203430"
MANIA = "https://www.mmamania.com/ufc-results/481538/ufc-vegas-123-live-results-highlights-play-by-play-moicano-vs-nolan"
JUNKIE = "https://sports.yahoo.com/articles/ufc-fight-night-292-live-200107511.html"
CAGESIDE_MAIN = "https://cagesidepress.com/2026/10/31/tom-nolan-stuns-renato-moicano-with-third-round-tko/"


def chk(by, claim, tag, favoured, verdict, note):
    return {"by": by, "claim": claim, "tag": tag, "favoured": favoured, "verdict": verdict, "note": note}


def sc(rnd, who, n=3):
    return [rnd] + [who] * n


NOLAN, MOI = "Tom Nolan", "Renato Carneiro"  # Moicano, listed under his legal name
SMITH, BROWN = "Jacobe Smith", "Randy Brown"
DURDEN, OSB = "Cody Durden", "Ode Osbourne"
LUANA, YANA = "Luana Santos", "Yana Santos"
JPL, HAS = "Jean-Paul Lebosnoyani", "Farman Hasanov"
HOPE, MARSH = "Dakota Hope", "Francis Marshall"
SEZ, BERG = "Rodrigo Sezinando", "Theodor Berggren"
EROSA, LEE = "Julian Erosa", "Jeong Yeong Lee"
REESE, GALL = "Zachary Reese", "Mickey Gall"
KROP, KLEIN = "Joseph Kropschot", "Nick Klein"
PIERA, ALEN = "Piera Rodriguez", "Talita Alencar"
SZAB, LIS = "Lucia Szabova", "Tainara Lisboa"

# Coverage corrections (see the module docstring): outlets to add, round scores to set, links to leave out.
COVERAGE_FIX = {
    "tom-nolan-renato-carneiro": dict(
        outlets=[{"outlet": "Sherdog", "kind": "play-by-play", "url": SHERDOG},
                 {"outlet": "MMA Mania", "kind": "play-by-play", "url": MANIA},
                 {"outlet": "MMA Junkie", "kind": "play-by-play", "url": JUNKIE},
                 {"outlet": "Cageside Press", "kind": "recap", "url": CAGESIDE_MAIN}],
        round_scores=[sc(1, "10-9 Moicano"), sc(2, "10-9 Nolan")], closeness=None),
    "dakota-hope-francis-marshall": dict(
        outlets=[{"outlet": "Sherdog", "kind": "play-by-play", "url": SHERDOG}],
        round_scores=[sc(1, "10-9 Marshall"), sc(2, "10-9 Hope"), sc(3, "10-9 Hope")], closeness="close"),
    "rodrigo-sezinando-theodor-berggren": dict(round_scores=[sc(1, "10-9 Sezinando")], closeness=None),
    # every scorer 29-27 Reese, round by round alike: clear
    "zachary-reese-mickey-gall": dict(round_scores=[sc(1, "9-9"), sc(2, "10-9 Reese"), sc(3, "10-9 Reese")], closeness="clear"),
    # both are "Santos": the label read every round as the loser's; the rounds split 1-2 for the winner, so close
    "luana-santos-yana-santos": dict(round_scores=[sc(1, "10-9 Yana"), sc(2, "10-9 Luana"), sc(3, "10-9 Luana")], closeness="close"),
}
NOT_RECAPS = {
    "https://cagesidepress.com/2026/10/31/ufc-vegas-123s-julian-erosa-explains-retirement-timing-decision/",
    "https://www.mmafighting.com/ufc/518290/luana-santos-ufc-title-shot-definitely-possible-with-win-over-yana-santos",
}

STORIES = {
    "tom-nolan-renato-carneiro": dict(
        summary="Moicano took Nolan down inside the first two minutes, took his back with a body triangle and rode him for the "
                "rest of round 1, hunting the choke. In round 2 he did it again after Nolan stung him with a head kick, until "
                "Miragliotta stood them up from back control, a reset the commentary team, the outlets and other fighters called "
                "wrong. Back on the feet Nolan dropped him with a knee and battered him to the horn; in round 3 he hurt him again "
                "with knees and punches, reversed Moicano's takedown and finished him with punches and elbows at 1:28.",
        turning_point="Round 2: Miragliotta's stand-up out of Moicano's back control, followed at once by Nolan's knee that "
                      "dropped him.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Moicano takes the back once the pace drops and finishes it: submission, R2", "back_take", MOI, "mixed",
                "He took the back with a body triangle in rounds 1 and 2, as expected, but never came close to the finish, and "
                "lost the position to the referee's stand-up."),
            chk("read", "Moicano's back takes in scrambles", "back_take", MOI, "held",
                "Took the back straight off each of his first two takedowns and held it for long stretches of both rounds."),
            chk("read", "Nolan untested past R3", "five_rounds", MOI, "untested", "Over early in round 3."),
            chk("read", "Nolan's size and clinch (against)", "clinch", NOLAN, "held",
                "His knees dropped Moicano in round 2 and hurt him again in round 3."),
            chk("read", "Age 37 (against)", "age", NOLAN, "held",
                "Moicano broke once he was hurt and was finished early in round 3, though the turn came straight after the reset."),
            chk("model", "Fresher body favours Nolan", "wear_and_tear", NOLAN, "held",
                "Nolan was the stronger man from late in round 2; Moicano had nothing left to stop the round-3 reversal."),
            chk("model", "Overall rating favours Moicano", "overall", MOI, "failed", "Stopped in round 3."),
            chk("model", "Submission threat favours Nolan", "submission_threat", NOLAN, "failed",
                "Moicano was the one hunting chokes; Nolan never attempted one."),
            chk("model", "Age favours Nolan", "age_curve", NOLAN, "held", "As the read: the older man faded and was finished."),
            chk("model", "Fight Matrix rating favours Moicano", "outside_rating", MOI, "failed", "Lost by stoppage."),
        ]),
    "jacobe-smith-randy-brown": dict(
        summary="Brown kept Smith at the end of his jab for most of round 1 until Smith blasted through for a takedown late in "
                "the round. Smith took him down again in rounds 2 and 3, got through Brown's armbar attempts and opened a deep "
                "cut with elbows in round 2; Brown spent round 3 surviving on his back. Smith won 30-26 on all three cards, "
                "the first decision of his unbeaten career.",
        turning_point="Smith's elbows in round 2, which opened Brown up and took the fight out of him.",
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "Smith's wrestling and ground strikes are what beat Brown: KO/TKO, R2", "wrestling", SMITH, "mixed",
                "Takedowns in every round and the cut came in round 2, as picked, but Brown's guard saw him to the final bell."),
            chk("read", "Smith's wrestling vs Brown's takedown defence", "wrestling", SMITH, "held",
                "A takedown in each round; Brown never kept him off."),
            chk("read", "Brown's guard and range (against)", "guard", BROWN, "mixed",
                "The jab won him the first three minutes and his guard stopped a finish, but neither won a round."),
            chk("read", "Short notice for Smith", "short_notice", BROWN, "failed", "Strong for all 15 minutes."),
            chk("model", "Fresher body favours Smith", "wear_and_tear", SMITH, "held",
                "Brown was gun-shy and surviving by round 3."),
            chk("model", "Wrestling edge favours Smith", "wrestling_edge", SMITH, "held", "Won the fight with it."),
            chk("model", "Reach favours Brown", "reach", BROWN, "failed", "Kept Smith out for a round at most."),
            chk("model", "Height favours Brown", "height", BROWN, "failed", "As with the reach."),
            chk("model", "Age favours Smith", "age_curve", SMITH, "held", "The 36-year-old faded; the younger man did not."),
        ]),
    "cody-durden-ode-osbourne": dict(
        summary="Durden ate an early shot, took Osbourne down, escaped a guillotine and spent round 1 on his back with a body "
                "triangle, then in mount with heavy punches. He took him down three more times in round 2. A tired Durden "
                "lost round 3 when Osbourne reversed him and rode his back without threatening: 29-28 on all three cards and "
                "on all three of Sherdog's.",
        turning_point=None,
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Durden's takedowns and control against a fighter who loses when held down: decision", "wrestling",
                DURDEN, "held", "Took the first two rounds on takedowns and control and won 29-28, as picked."),
            chk("read", "Osbourne's takedown defence", "td_def", DURDEN, "held", "Taken down five times."),
            chk("read", "Durden's control", "control", DURDEN, "held",
                "Rounds 1 and 2 almost all on top or on the back; lost position only in round 3."),
            chk("read", "Osbourne's counter power (against)", "power", OSB, "failed",
                "Landed one clean shot early and nothing that hurt Durden."),
            chk("read", "Durden's submission defence (against)", "sub_def", OSB, "failed",
                "Got out of Osbourne's tight round-1 guillotine calmly."),
            chk("model", "Wrestling edge favours Durden", "wrestling_edge", DURDEN, "held", "Five takedowns."),
            chk("model", "Fresher body favours Osbourne", "wear_and_tear", OSB, "mixed",
                "Durden tired visibly and lost round 3, but by then the fight was his."),
            chk("model", "Reach favours Osbourne", "reach", OSB, "untested", "Most of the fight was on the mat."),
            chk("model", "Wrestling rating favours Durden", "wrestling_rating", DURDEN, "held", "As the wrestling edge."),
        ]),
    "luana-santos-yana-santos": dict(
        summary="Yana stuffed Luana's trips and throws and held her on the fence for most of round 1, adding knees and a "
                "right hand, and won it on every Sherdog card. From round 2 Luana got her takedowns: a double leg, the back, "
                "mount, and in round 3 a takedown straight to the back with both hooks, riding out most of the round. "
                "Luana won 29-28 on all three cards, a fight the outlets agreed was more control than damage.",
        turning_point="Round 2: Luana's first clean takedown and back take; Yana could not keep her off after that.",
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Luana's takedowns and top control over 15 minutes against a striker taken down late: decision",
                "wrestling", LUANA, "held", "Lost round 1, then won rounds 2 and 3 on takedowns and back control: 29-28."),
            chk("read", "Luana's top control", "control", LUANA, "held", "Rounds 2 and 3 were mostly on Yana's back."),
            chk("read", "Yana's late takedown defence", "td_def", LUANA, "held",
                "Stopped the trips in round 1, gave up takedowns in rounds 2 and 3."),
            chk("read", "Yana's layoff", "inactivity", LUANA, "mixed", "Sharp enough to win round 1; no sign of it after."),
            chk("model", "Fresher body favours Luana", "wear_and_tear", LUANA, "held", "The stronger fighter late."),
            chk("model", "Wrestling edge favours Luana", "wrestling_edge", LUANA, "held", "Took rounds 2 and 3 with it."),
            chk("model", "Age favours Luana", "age_curve", LUANA, "held", "The 37-year-old faded after round 1."),
            chk("model", "Striking rating favours Yana", "striking_rating", YANA, "mixed",
                "Yana did the better work standing and in the clinch, but there was little of it."),
            chk("model", "Striking defence favours Luana", "striking_defense", LUANA, "untested", "Neither did much damage."),
        ]),
    "jean-paul-lebosnoyani-farman-hasanov": dict(
        summary="Hasanov took Lebosnoyani down early in each of the first two rounds, but he stood up at once every time and "
                "out-landed him at range with low kicks, body kicks and the jab. Hasanov was wilting by the end of round 2, "
                "badly hurt and opened up over the left eye (one Sherdog scorer had it 10-8); early in round 3 the cut ran the "
                "length of his eyebrow and the doctor stopped it at 2:11.",
        turning_point="The body kick midway through round 2 that doubled Hasanov over; from then he was backing up.",
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Override: Hasanov fades from R2 and does little damage; Lebosnoyani wins the late rounds: decision",
                "cardio", JPL, "held", "Hasanov was spent from midway through round 2; the stoppage came on a cut, not on the cards."),
            chk("read", "Hasanov's cardio after R1", "cardio", JPL, "held", "Wilting late in round 2, backing up in round 3."),
            chk("read", "Lebosnoyani's guillotine in scrambles", "guillotine", JPL, "mixed",
                "Jumped one off Hasanov's first takedown; it was defended."),
            chk("read", "Hasanov's chain wrestling (against)", "wrestling", HAS, "failed",
                "Completed takedowns but Lebosnoyani was up within seconds each time."),
            chk("model", "Wrestling edge favours Hasanov", "wrestling_edge", HAS, "failed", "His takedowns got him nothing."),
            chk("model", "Overall rating favours Lebosnoyani", "overall", JPL, "held", "Won every round."),
            chk("model", "Wrestling rating favours Lebosnoyani", "wrestling_rating", JPL, "held", "Stood from every takedown."),
            chk("model", "Experience favours Lebosnoyani", "experience", JPL, "held", "Paced it and broke the unbeaten man late."),
            chk("model", "Fresher body favours Hasanov", "wear_and_tear", HAS, "failed", "Hasanov was the one who tired."),
        ]),
    "dakota-hope-francis-marshall": dict(
        summary="Marshall, two pounds over the featherweight limit, chopped Hope's lead leg with calf kicks in round 1, swept "
                "him once and added a takedown. Hope came back in round 2 behind pressure, and in round 3 he staggered Marshall "
                "with an overhand right, sprawled on his desperation shot, took the back and kept hitting him to the bell. Hope "
                "won a split decision (29-28, 28-29, 29-28), as Sherdog's three scorers had it; MMA Junkie had Marshall.",
        turning_point="Round 3: Hope's overhand right, and his sprawl and back take on Marshall's takedown attempt.",
        verdict="wrong, claim failed",
        checks=[
            chk("pick", "Hope is a front-loaded striker who faded in his debut; Marshall's top control grows as he tires: decision",
                "cardio", MARSH, "failed", "Hope was the stronger man in rounds 2 and 3 and won the last one clearly."),
            chk("read", "Hope's R2-R3 cardio", "cardio", MARSH, "failed", "His best round was the third."),
            chk("read", "Marshall's top control", "control", MARSH, "mixed",
                "One takedown off a caught kick in round 1, then nothing; Hope took his back in round 3."),
            chk("read", "Hope's short notice and weight cut", "short_notice", MARSH, "failed", "No sign of it; Marshall was the one who missed weight."),
            chk("read", "Hope's early power (against)", "power", HOPE, "mixed",
                "Stung Marshall late in round 1, but the power that decided it came in round 3."),
            chk("model", "Striking rating favours Hope", "striking_rating", HOPE, "held", "Won rounds 2 and 3 standing."),
            chk("model", "Wrestling edge favours Marshall", "wrestling_edge", MARSH, "failed",
                "Hope stopped his shots in rounds 2-3 and took his back off one."),
        ]),
    "rodrigo-sezinando-theodor-berggren": dict(
        summary="A grappling-heavy first round was close until Sezinando, whose takedowns kept being reversed or stuffed, "
                "dropped Berggren at the horn with a spinning backfist and a left hook. In round 2 he got his takedowns, took the "
                "back, then mount, and landed punches and elbows to the bell; the cageside doctor stopped it before round 3 "
                "because of a severe cut on Berggren's lip (TKO, 5:00 of round 2).",
        turning_point="The spinning backfist at the end of round 1.",
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Sezinando's clinch and takedowns; Berggren is stopped later in fights: KO/TKO, R2", "wrestling", SEZ, "held",
                "Takedowns and ground strikes in round 2, stopped at the end of it: method and round right."),
            chk("read", "Sezinando's clinch and takedowns", "wrestling", SEZ, "held", "Took round 2 entirely on them."),
            chk("read", "Berggren's defence vs kicks and body work", "strike_def", SEZ, "mixed",
                "Hurt by a spinning backfist and ground strikes, not by body work."),
            chk("read", "Sezinando's layoff (against)", "inactivity", BERG, "failed", "No rust after 13 months."),
            chk("model", "Wrestling rating favours Sezinando", "wrestling_rating", SEZ, "mixed",
                "Berggren reversed or stuffed him in round 1; Sezinando dominated round 2."),
            chk("model", "Overall rating favours Sezinando", "overall", SEZ, "held", "Won both rounds."),
            chk("model", "Fight Matrix rating favours Sezinando", "outside_rating", SEZ, "held", "Won."),
        ]),
    "julian-erosa-jeong-yeong-lee": dict(
        summary="Lee hit Erosa straight off the glove touch and floored him with a left hook, then jumped on a guillotine that "
                "nearly ended it in the opening seconds. Erosa got free, clinched, and as Lee kept swinging wildly, dropped him "
                "with an overhand right and finished him with punches at 1:31 of round 1, in what he had said would be his "
                "last fight. It earned him a $100,000 bonus.",
        turning_point="Erosa's overhand right in the middle of a wild exchange, a minute after he had been dropped.",
        verdict="wrong, close fight",
        checks=[
            chk("pick", "Override: Erosa has five R1 knockout losses to fast punchers; Lee lands the right hand early: KO/TKO, R1",
                "durability", LEE, "mixed",
                "Lee did drop Erosa in the opening seconds, as the pick said; Erosa survived and knocked Lee out instead."),
            chk("read", "Erosa's chin against early power", "durability", LEE, "mixed", "Dropped early, but got up and recovered."),
            chk("read", "Lee's layoff and weight cut (against)", "inactivity", EROSA, "untested", "Lee was sharp; over in 91 seconds."),
            chk("read", "Erosa's late scrambles (against)", "cardio", EROSA, "untested", "Over in round 1."),
            chk("model", "Fresher body favours Lee", "wear_and_tear", LEE, "failed", "The worn veteran took Lee's best and won."),
            chk("model", "Overall rating favours Erosa", "overall", EROSA, "held", "Won."),
            chk("model", "Striking exchange favours Erosa", "striking_exchange", EROSA, "mixed",
                "Lost the first exchange and won the last."),
            chk("model", "Age favours Lee", "age_curve", LEE, "failed", "The 37-year-old won."),
            chk("model", "Experience favours Erosa", "experience", EROSA, "held",
                "Survived the knockdown and guillotine calmly before turning it."),
        ]),
    "zachary-reese-mickey-gall": dict(
        summary="Reese out-struck Gall in all three rounds with body kicks, knees and combinations, but was docked a point "
                "for an eye poke in round 1, which left that round 9-9 on Sherdog's cards. Gall, back after almost two "
                "years, was more competitive than expected with overhand rights and left hooks against Reese's open chin, "
                "though the body kicks hurt him in round 3. Reese won 29-27 on all three cards.",
        turning_point=None,
        verdict="right, other reasons",
        checks=[
            chk("pick", "Gall is rusty and was knocked out in R1 in two of his last three; Reese finishes early: KO/TKO, R1",
                "durability", REESE, "failed", "Gall lasted 15 minutes and landed his own shots; Reese won on volume."),
            chk("read", "Gall's layoff and medical flag", "inactivity", REESE, "failed", "Competitive for three rounds."),
            chk("read", "Reese's R1 finishing", "power", REESE, "failed", "Never had Gall in serious trouble early."),
            chk("read", "Reese's early defensive lapses (against)", "strike_def", GALL, "mixed",
                "His chin was there to hit and Gall landed overhands, but nothing hurt him."),
            chk("model", "Striking rating favours Reese", "striking_rating", REESE, "held", "Won every round standing."),
            chk("model", "Overall rating favours Reese", "overall", REESE, "held", "Clear decision despite the point deduction."),
            chk("model", "Fight Matrix rating favours Reese", "outside_rating", REESE, "held", "Won."),
            chk("model", "Fresher body favours Reese", "wear_and_tear", REESE, "mixed",
                "Gall slowed under the body kicks in round 3, but was still swinging at the end."),
            chk("model", "Wrestling rating favours Reese", "wrestling_rating", REESE, "untested", "Fought entirely standing."),
        ]),
    "joseph-kropschot-nick-klein": dict(
        summary="Klein was the busier striker early and took Kropschot down in round 1, but Kropschot, in his UFC debut, "
                "stood, attacked a choke from the front headlock, and ended the round on Klein's back with a body triangle and a "
                "rear-naked choke attempt. Klein took him down again early in round 2 and even reached the back; Kropschot "
                "turned into him and finished with an inverted triangle and armbar at 1:25.",
        turning_point="Kropschot's reversal off Klein's round-2 takedown, straight into the inverted triangle.",
        verdict="right, partly for our reasons",
        checks=[
            chk("pick", "Klein fades after his first-round burst and is stopped in R2: KO/TKO, R2", "cardio", KROP, "mixed",
                "Round 2 was right but it came from Kropschot's grappling off Klein's own takedown, not from a fade."),
            chk("read", "Klein's R2 fade", "cardio", KROP, "mixed", "Klein was still taking him down when he was caught."),
            chk("read", "Kropschot's debut (against)", "debut", KLEIN, "failed", "Composed off his back and finished in round 2."),
            chk("model", "Overall rating favours Kropschot", "overall", KROP, "held", "Won."),
            chk("model", "Wrestling edge favours Klein", "wrestling_edge", KLEIN, "mixed",
                "Klein got both of his takedowns, and lost the position after each."),
            chk("model", "Wrestling rating favours Kropschot", "wrestling_rating", KROP, "mixed",
                "Taken down twice, reversed twice."),
            chk("model", "Fight Matrix rating favours Klein", "outside_rating", KLEIN, "failed", "Submitted."),
            chk("model", "Power vs chin favours Kropschot", "power_vs_chin", KROP, "untested",
                "Swept Klein's leg with a calf kick, but no shot to the head decided anything."),
        ]),
    "piera-rodriguez-talita-alencar": dict(
        summary="Alencar won rounds 1 and 2 on Sherdog's cards with her grappling: a trip and a long spell on Rodriguez's back "
                "in round 1 (fought through a partial power cut in the arena), and a takedown, elbows from half guard and an "
                "armbar attempt late in round 2. Rodriguez out-struck her on the feet throughout, most clearly in round 3, "
                "and all three judges gave her every round, 30-27; Sherdog's three scorers all had Alencar 29-28.",
        turning_point=None,
        verdict="right on the cards, wrong on the fight",
        checks=[
            chk("pick", "Rodriguez's pressure, body knees and late takedowns win three-round fights: decision", "pressure", PIERA,
                "mixed", "Won the striking and the official cards, but no takedowns of her own and lost two rounds on Sherdog's."),
            chk("read", "Rodriguez's pressure and volume", "pressure", PIERA, "held", "Out-landed Alencar standing in every round."),
            chk("read", "Alencar's submissions (against)", "submission", ALEN, "mixed",
                "Took the back in round 1 and attacked an armbar in round 2, without a real finish threat."),
            chk("model", "Striking rating favours Rodriguez", "striking_rating", PIERA, "held", "Clearly the better striker."),
            chk("model", "Wrestling edge favours Rodriguez", "wrestling_edge", PIERA, "failed", "Alencar got the takedowns."),
            chk("model", "Striking exchange favours Rodriguez", "striking_exchange", PIERA, "held", "As the striking rating."),
        ]),
    "lucia-szabova-tainara-lisboa": dict(
        summary="In her UFC debut Szabova clinched, kneed the body and tripped Lisboa down repeatedly in round 1, though Lisboa "
                "twice scrambled to her back and attacked a rear-naked choke at the end of it. Szabova took round 2 from top "
                "and back with ground strikes, and in round 3 she passed to mount, took the back and punched until Tognoni "
                "stopped it at 3:20.",
        turning_point=None,
        verdict="right, for our reasons",
        checks=[
            chk("pick", "Szabova finishes from the clinch and mount; Lisboa breaks late: KO/TKO, R2", "durability", SZAB, "held",
                "Broken by ground strikes as picked, a round later."),
            chk("read", "Lisboa's late durability", "durability", SZAB, "held", "Stopped in round 3, as in her last two fights."),
            chk("read", "Szabova's competition level (against)", "competition", LIS, "failed",
                "Lisboa's back takes in round 1 were the only trouble she had."),
            chk("model", "Overall rating favours Szabova", "overall", SZAB, "held", "Won every round and stopped her."),
            chk("model", "Wrestling rating favours Szabova", "wrestling_rating", SZAB, "held", "Took her down at will."),
            chk("model", "Fight Matrix rating favours Szabova", "outside_rating", SZAB, "held", "Won."),
            chk("model", "Fresher body favours Szabova", "wear_and_tear", SZAB, "held", "Lisboa had nothing left by round 3."),
            chk("model", "Striking rating favours Szabova", "striking_rating", SZAB, "mixed",
                "Won with ground strikes; little was decided standing."),
        ]),
}

# Judged performances, only where two outlets agree (Sherdog's play-by-play plus MMA Mania, MMA Junkie or Cageside Press).
# (bout key, fighter, opponent, domain, rating, skills, note); the source is the bout's outlets.
NOTES = [
    ("tom-nolan-renato-carneiro", NOLAN, MOI, "striking", 1.5, ["head_kick", "knees", "gnp"],
     "Stung Moicano with a head kick, dropped him with a knee after the round-2 restart and finished him with ground strikes."),
    ("tom-nolan-renato-carneiro", NOLAN, MOI, "grappling", -1.0, ["back_escape"],
     "Spent most of rounds 1-2 with Moicano on his back in a body triangle and could not shake him off."),
    ("tom-nolan-renato-carneiro", NOLAN, MOI, "wrestling", -0.5, ["td_def", "reversal"],
     "Taken down easily in rounds 1-2; reversed the round-3 takedown into top position for the finish."),
    ("jacobe-smith-randy-brown", SMITH, BROWN, "wrestling", 2.0, ["td_off", "control"],
     "A takedown in every round against a long, rangy opponent, and kept him down."),
    ("jacobe-smith-randy-brown", SMITH, BROWN, "striking", 1.0, ["gnp", "elbows"],
     "Cut Brown badly with elbows from top in round 2."),
    ("cody-durden-ode-osbourne", DURDEN, OSB, "wrestling", 1.5, ["td_off", "control"],
     "Took Osbourne down repeatedly and controlled rounds 1-2."),
    ("cody-durden-ode-osbourne", DURDEN, OSB, "grappling", 0.5, ["sub_def", "back_take", "gnp"],
     "Escaped a tight guillotine, took the back and mounted in round 1; gave up his own back when tired in round 3."),
    ("luana-santos-yana-santos", LUANA, YANA, "wrestling", 1.0, ["td_off"],
     "Trips denied in round 1, then a takedown in each of rounds 2 and 3."),
    ("luana-santos-yana-santos", LUANA, YANA, "grappling", 1.0, ["back_take", "control"],
     "Rode Yana's back for most of rounds 2 and 3, with little damage."),
    ("jean-paul-lebosnoyani-farman-hasanov", JPL, HAS, "striking", 2.0, ["leg_kicks", "body_kicks", "jab", "cardio"],
     "Out-landed the unbeaten Hasanov at range in every round, broke him with body kicks and cut him up for the stoppage."),
    ("jean-paul-lebosnoyani-farman-hasanov", JPL, HAS, "wrestling", 1.0, ["get_up", "td_def"],
     "Gave up takedowns in rounds 1 and 2 but was back up at once every time."),
    ("dakota-hope-francis-marshall", HOPE, MARSH, "striking", 1.0, ["pressure", "power", "cardio"],
     "Lost round 1 to calf kicks, then out-struck Marshall in rounds 2 and 3 and staggered him with an overhand right."),
    ("dakota-hope-francis-marshall", HOPE, MARSH, "wrestling", 0.5, ["td_def", "back_take"],
     "Sprawled on Marshall's later shots and took his back off one in round 3."),
    ("rodrigo-sezinando-theodor-berggren", SEZ, BERG, "wrestling", 1.0, ["td_off", "clinch"],
     "Stuffed or reversed in round 1, then took Berggren down at will in round 2."),
    ("rodrigo-sezinando-theodor-berggren", SEZ, BERG, "striking", 1.0, ["spinning", "gnp", "elbows"],
     "Dropped him with a spinning backfist at the end of round 1 and cut him open with elbows from mount in round 2."),
    ("julian-erosa-jeong-yeong-lee", EROSA, LEE, "striking", 1.0, ["power", "durability"],
     "Dropped in the opening seconds, recovered and knocked Lee out with an overhand right."),
    ("zachary-reese-mickey-gall", REESE, GALL, "striking", 1.0, ["body_kicks", "knees", "volume"],
     "Won every round standing with body kicks and knees, though his chin was there for Gall's overhands."),
    ("joseph-kropschot-nick-klein", KROP, KLEIN, "grappling", 2.0, ["reversal", "back_take", "triangle", "armbar"],
     "Reversed both of Klein's takedowns, took the back in round 1 and finished with an inverted triangle armbar."),
    ("joseph-kropschot-nick-klein", KROP, KLEIN, "wrestling", -0.5, ["td_def"],
     "Taken down by Klein in rounds 1 and 2."),
    ("piera-rodriguez-talita-alencar", PIERA, ALEN, "striking", 1.5, ["pressure", "combinations", "jab"],
     "Out-landed Alencar standing in every round, most clearly in round 3."),
    ("piera-rodriguez-talita-alencar", PIERA, ALEN, "wrestling", -1.0, ["td_def"],
     "Tripped and taken down in rounds 1 and 2, with Alencar on her back or in half guard."),
    ("lucia-szabova-tainara-lisboa", SZAB, LIS, "wrestling", 2.0, ["trips", "clinch", "td_off"],
     "Took Lisboa down from the clinch whenever she chose, in every round."),
    ("lucia-szabova-tainara-lisboa", SZAB, LIS, "striking", 1.0, ["gnp", "knees"],
     "Knees in the clinch and ground strikes from mount and the back for the round-3 stoppage."),
]

REVIEW = """A card the market read far better than the model: the market picked 9 of 11 priced winners with a log loss of 0.455, the model 7 of 12 (0.636 on the priced bouts). On the season the market still leads (0.580 on 443 priced bouts, the model 0.639 on the same bouts). AI Picks scored 27 points, level with the model, and both AI Bets lost on the method: Lebosnoyani won but by a doctor's stoppage, and Kropschot won but by submission.

The reads that held were the grappling ones. Durden took Osbourne down from the first minute as the read said, Luana Santos took over once her takedowns landed from round 2, and Lebosnoyani beat Hasanov exactly the way the read expected, standing up from every takedown and wearing him down until the cut ended it in round 3. Szabova's clinch and mount game finished Lisboa, as her report said, though in round 3 rather than round 2.

The misses were close or chaotic. Moicano was winning the main event from Nolan's back until a contested stand-up in round 2, and Nolan's knee then turned it; the read on Nolan's untested five-round game never got tested. Hope beat Marshall on a split decision by rallying late, the opposite of the read that he fades. Lee dropped Erosa first and then got knocked out swinging wildly, in Erosa's farewell fight. Rodriguez over Alencar is a disputed decision: all three Sherdog scorers had Alencar. And Klein's R2 fade did come, but Kropschot finished it with a triangle and armbar rather than strikes, which is the bet's lesson: Kropschot's own record (six of nine wins by submission) was the better guide than Klein's losses.

No fight-night notes for this card."""


def main():
    f = ROOT / "recaps" / f"{ID}.json"
    doc = json.loads(f.read_text())
    cov = doc["coverage"]
    for k, fix in COVERAGE_FIX.items():
        c = cov[k]
        seen = {o["url"] for o in c["outlets"]}
        c["outlets"] = [o for o in fix.get("outlets", []) if o["url"] not in seen] + c["outlets"]
        if "round_scores" in fix:
            c["round_scores"] = fix["round_scores"]
            c["closeness"] = fix["closeness"]
    for c in cov.values():
        c["outlets"] = [o for o in c["outlets"] if o["url"] not in NOT_RECAPS]
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
