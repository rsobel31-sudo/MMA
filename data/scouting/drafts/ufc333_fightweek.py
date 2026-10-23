"""Fight-week news update for UFC 333: Volkanovski vs. Evloev (Abu Dhabi, 2026-10-24).

Run: python data/scouting/drafts/ufc333_fightweek.py  -> updates data/scouting/reports/<slug>.json in place.
Written Friday 2026-10-23 after the official weigh-ins. Adds dated news items (official weights, the one
weight miss, media-day quotes, the UFC.com Fight By Fight Preview and Sherdog preview notes with their odds),
plus a concern only where clearly warranted. Items already present (same text) are not added again, so the
script can be re-run safely. No bout changes since 2026-10-13: the only change to the card in fight week is
Lucindo vs. Caliari becoming a catchweight after Caliari's miss (Allen -> Keita happened on 2026-09-18).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
UPDATED = "2026-10-23T18:00:00+00:00"
WI = "2026-10-23"

# Sources
UFC_WI = "https://www.ufc.com/news/official-weigh-results-ufc-333-volkanovski-vs-evloev"
SHERDOG_WI = "https://www.sherdog.com/news/news/UFC-333-weighin-results-Title-fights-set-Fighter-heavy-by-45-pounds-203308"
YAHOO_WI_LIVE = ("https://sports.yahoo.com/mma/live/"
                 "ufc-333-weigh-in-results-video-title-bouts-set-undercard-fighter-badly-misses-weight-071551485.html")
MIDDLEEASY_WI = "https://middleeasy.com/mma-news/ufc333-official-weighin-results-volkanovski-evloev-yan-caliari/"
UFC_FBF = "https://www.ufc.com/news/fight-fight-preview-ufc-333-volkanovski-vs-evloev"
CAGESIDE_INVICTA37 = "https://cagesidepress.com/2019/10/04/invicta-fc-37-official-weigh-photo-video-highlights"


def sherdog_main(page):
    return f"https://www.sherdog.com/news/articles/{page}/Preview-UFC-333-Volkanovski-vs-Evloev-203278"


def sherdog_prelims(page):
    return f"https://www.sherdog.com/news/articles/{page}/Preview-UFC-333-prelims-203277"


def item(date, text, source):
    return {"date": date, "text": text, "source": source}


def made(weight, opp, opp_weight, extra=""):
    return item(WI, f"Made weight at the official weigh-ins: {weight} lb ({opp} {opp_weight}).{extra}", UFC_WI)


NEWS = {
    "alexander-volkanovski": [
        made("144.5", "Evloev", "145", " Featherweight title fight confirmed."),
        item("2026-10-22", "Sherdog preview lists the fight a pick'em (-110 each) and picks him by decision: the swing factor is "
             "whether he keeps enough of it standing, with his age (38) and recent KO losses the doubts.", sherdog_main(1)),
        item("2026-10-21", "Media day: calls Evloev's wrestling 'incredible' and the best in the division, but 'just not enough for me'; "
             "expects to win any grappling exchanges and get straight back up from bottom (MMA Fighting via BoxingNews/Yardbarker).",
             "https://www.yardbarker.com/mma/articles/volkanovski_on_evloevs_wrestling_ahead_of_ufc_333/s1_17349_44456371"),
        item("2026-10-19", "Says Evloev can't outgrapple him for 25 minutes, that his only route is to 'catch me', and predicts a "
             "'wild' finish.", "https://www.sherdog.com/news/news/Alexander-Volkanovski-predicts-wild-finish-of-200-Movsar-Evloev-203269"),
    ],
    "movsar-evloev": [
        made("145", "Volkanovski", "144.5", " Featherweight title fight confirmed."),
        item("2026-10-22", "Sherdog preview: pick'em at -110 each; Sherdog picks Volkanovski by decision but warns Evloev's lack of "
             "UFC finishes is no guarantee of safety; notes he can be overly patient and short on striking variety when the "
             "takedowns aren't landing.", sherdog_main(1)),
        item("2026-10-22", "Says this camp was harder than any before ('I pushed more than ever') and that Volkanovski 'hasn't beaten "
             "anyone like me'.", "https://www.sherdog.com/news/news/Movsar-Evloev-warns-Alexander-Volkanovski-He-hasnt-beaten-anyone-like-me-203290"),
        item("2026-10-22", "Media day: called it the moment he had waited seven years for; rejected the age angle ('he's old enough to "
             "be in his prime'); conceded Jose Aldo's point that he doesn't sell fights.",
             "https://cagesidepress.com/2026/10/22/ufc-333-movsar-evloev-feels-volk-still-dangerous-responds-aldo/"),
        item("2026-10-21", "His coach says they have drilled the kimura, arm-triangle and an undisclosed choke, and expects more kimura "
             "attempts than usual (MMA Sucka).",
             "https://mmasucka.com/news/movsar-evloevs-coach-refuses-to-reveal-the-choke-they-have-been-preparing-for-alexander-volkanovski/"),
        item("2026-10-17", "Now says he wants to win over five rounds rather than chase a finish, to prove Volkanovski can be beaten "
             "over 25 minutes (MMA Sucka): reverses his September talk of a first UFC finish.",
             "https://mmasucka.com/news/movsar-evloev-makes-big-adjustment-ahead-of-ufc-333-title-fight-against-alexander-volkanovski/"),
        item("2026-10-19", "UFC.com Fight By Fight Preview: struck for two rounds against Murphy then landed 9 of 10 takedowns over the "
             "final three; still no finish in 10 UFC starts.", UFC_FBF),
    ],
    "merab-dvalishvili": [
        made("135", "Yan", "135"),
        item(WI, "Posted that he regained 19 lb in five hours after weighing in (per Middle Easy).", MIDDLEEASY_WI),
        item("2026-10-21", "Mid-week update: had cut 7 kg and had 5 kg left, which he said 'will be tough'; stopped drinking water "
             "two days before the scale (MMA Sucka). He made weight without trouble.",
             "https://mmasucka.com/news/this-5kg-will-be-tough-merab-dvalishvili-looks-shredded-ahead-of-petr-yan-trilogy/"),
        item("2026-10-22", "Sherdog preview: +145 underdog (Yan -175); expects Yan's improved takedown defence to blunt his attrition "
             "wrestling again and picks Yan by decision.", sherdog_main(2)),
        item("2026-10-20", "Says Yan's trash talk no longer bothers him and calls the trilogy the biggest fight of his career "
             "(MMA Fighting via Yahoo).", "https://sports.yahoo.com/articles/merab-dvalishvili-explains-suprising-demeanor-130000415.html"),
        item("2026-10-19", "UFC.com Fight By Fight Preview: links his December loss to a busy 2025 schedule, after which he "
             "'appeared to get deflated', something he has admitted.", UFC_FBF),
    ],
    "petr-yan": [
        made("135", "Dvalishvili", "135", " Bantamweight title fight confirmed."),
        item("2026-10-22", "Sherdog preview: -175 favourite (Dvalishvili +145); picks him by decision, crediting his improved "
             "takedown defence and late pressure.", sherdog_main(2)),
        item("2026-10-22", "Media day: 'I have a plan, and my plan is to come out there and win'; wants to finish the rivalry and "
             "'turn the page'. Also criticised the UFC's push of Sean O'Malley. No new health news.",
             "https://cagesidepress.com/2026/10/22/petr-yan-rips-ufc-over-sean-omalley-push-ahead-of-merab-dvalishvili-trilogy-at-ufc-333/"),
    ],
    "lone-er-kavanagh": [
        made("125.5", "Temirov", "126"),
        item("2026-10-22", "Sherdog preview: pick'em (-110 each); expects him to control the pace against Temirov's intermittent "
             "power and picks him by decision.", sherdog_main(3)),
        item("2026-10-22", "Media day: impressed by Temirov's 13 first-round finishes; says a spectacular win 'puts me right back at "
             "the top'.", "https://cagesidepress.com/2026/10/22/ufc-333-loneer-kavanagh-top/"),
        item("2026-10-19", "UFC.com Fight By Fight Preview: his third fight of 2026, about three and a half months after the July "
             "Royval war that ended in a R3 submission.", UFC_FBF),
    ],
    "ramazonbek-temirov": [
        made("126", "Kavanagh", "125.5"),
        item("2026-10-22", "Sherdog preview: pick'em (-110 each); calls his power dangerous against a fighter who has been knocked "
             "out, but his offence intermittent; picks Kavanagh by decision.", sherdog_main(3)),
        item("2026-10-21", "Media day: says he chose Kavanagh because he is ranked above him and expects a striking fight "
             "(MMA Junkie via Yahoo).", "https://sports.yahoo.com/articles/ramazan-temirov-ufc-333-win-143018988.html"),
    ],
    "alexander-volkov": [
        made("256", "Kuniev", "265"),
        item("2026-10-22", "Sherdog preview: -120 favourite (Kuniev +100); expects his height and movement to keep Kuniev at range "
             "and picks him by decision.", sherdog_main(4)),
        item("2026-10-19", "UFC.com Fight By Fight Preview frames it as a possible title eliminator, and a trap fight for him given "
             "his ranking.", UFC_FBF),
    ],
    "rizvan-kuniev": [
        made("265", "Volkov", "256", " Nine pounds heavier than Volkov."),
        item("2026-10-22", "Sherdog preview: +100 underdog (Volkov -120); says he needs sustained pressure to close distance and "
             "picks Volkov by decision.", sherdog_main(4)),
        item("2026-10-21", "Media day: says he will dictate the pace, 'can dominate him everywhere' and is not afraid of Volkov's "
             "size or reach.",
             "https://www.bjpenn.com/mma-news/rizvan-kuniev/rizvan-kuniev-not-afraid-of-alexander-volkov-ahead-of-ufc-333-i-can-dominate-him-everywhere/"),
    ],
    "aaron-pico": [
        made("145.5", "Keita", "146"),
        item("2026-10-22", "Sherdog preview: -115 (Keita -105); thinks he becomes hittable when he attacks and that 'old habits will "
             "resurface'; picks Keita by first-round KO.", sherdog_main(5)),
        item("2026-10-22", "Media day: says he has changed his mindset after the Murphy loss and wants to 'cook the fight a little' "
             "rather than rush the finish; no injury news.", "https://cagesidepress.com/2026/10/22/ufc-333-aaron-pico-cook/"),
    ],
    "losene-keita": [
        made("146", "Pico", "145.5", " No repeat of his 2025 UFC Paris miss."),
        item("2026-10-22", "Sherdog preview: -105 (Pico -115); picks him by first-round KO, expecting Pico's defensive lapses to "
             "resurface.", sherdog_main(5)),
        item(WI, "Media day: says he asked for any Abu Dhabi fight, that every shot he throws is meant to hurt Pico, and that he "
             "is the better martial artist.", "https://cagesidepress.com/2026/10/23/ufc-333-losene-keita-better-martial-artist/"),
        item("2026-10-19", "UFC.com Fight By Fight Preview: back about seven weeks after his Paris KO of Naimov.", UFC_FBF),
    ],
    "azamat-murzakanov": [
        made("206", "Reyes", "205"),
        item("2026-10-21", "Sherdog preview: -225 favourite (Reyes +185); expects a slow, low-volume start followed by a sudden "
             "finish and picks him by first-round KO.", sherdog_prelims(1)),
    ],
    "dominick-reyes": [
        made("205", "Murzakanov", "206"),
        item("2026-10-21", "Sherdog preview: +185 underdog (Murzakanov -225); calls him still dangerous but vulnerable to clean "
             "power; picks Murzakanov by first-round KO.", sherdog_prelims(1)),
    ],
    "abdul-rakhman-yakhyaev": [
        made("206", "Krylov", "206"),
        item("2026-10-21", "Sherdog preview: -520 favourite (Krylov +390); picks him by first-round KO, doubting Krylov gets the "
             "time to grind as he did against Bukauskas.", sherdog_prelims(2)),
    ],
    "nikita-krylov": [
        made("206", "Yakhyaev", "206"),
        item("2026-10-21", "Sherdog preview: +390 underdog (Yakhyaev -520); says he has looked more vulnerable since his 2023-25 "
             "layoff and picks Yakhyaev by first-round KO.", sherdog_prelims(2)),
        item("2026-10-19", "UFC.com Fight By Fight Preview: third fight of 2026, three months after being stopped by Whittaker.",
             UFC_FBF),
    ],
    "abus-magomedov": [
        made("185.5", "Rowston", "185"),
        item("2026-10-21", "Sherdog preview: -120 favourite (Rowston +100); expects him to be dangerous early and wrestle, with "
             "the risk that he fades; picks him by first-round submission.", sherdog_prelims(3)),
    ],
    "cameron-rowston": [
        made("185", "Magomedov", "185.5"),
        item("2026-10-21", "Sherdog preview: +100 underdog (Magomedov -120); says he can start slowly and that surviving round "
             "one would help him; picks Magomedov by first-round submission.", sherdog_prelims(3)),
        item("2026-10-22", "UFC.com feature: trains at City Kickboxing alongside Carlos Ulberg; calls Magomedov an awkward "
             "'puzzle' and says his team found holes to build a plan around.",
             "https://www.ufc.com/news/decade-as-a-pro-cam-rowston-is-in-his-prime-ufc-333-abu-dhabi"),
    ],
    "grant-dawson": [
        made("156", "Aliev", "155", " On weight despite his history of misses."),
        item("2026-10-21", "Sherdog preview: -125 favourite (Aliev +105) but Sherdog picks Aliev by decision, warning that "
             "wrestling exchanges may favour Aliev.", sherdog_prelims(4)),
    ],
    "nurullo-aliev": [
        made("155", "Dawson", "156"),
        item("2026-10-21", "Sherdog preview: +105 underdog (Dawson -125) but picked by decision, on the view that he can beat Dawson "
             "in the wrestling exchanges.", sherdog_prelims(4)),
    ],
    "asaf-chopurov": [
        made("136", "Thicknesse", "135.5"),
        item("2026-10-21", "Sherdog preview: -550 favourite (Thicknesse +410); picks him by first-round submission.",
             sherdog_prelims(5)),
        item("2026-10-19", "UFC.com Fight By Fight Preview notes he is a training partner of Petr Yan.", UFC_FBF),
    ],
    "colby-thicknesse": [
        made("135.5", "Chopurov", "136"),
        item("2026-10-21", "Sherdog preview: +410 underdog (Chopurov -550); points to his debut loss to Aleksandre Topuria against "
             "a stronger grappler and picks Chopurov by first-round submission.", sherdog_prelims(5)),
    ],
    "abubakar-vagaev": [
        made("185.5", "Malkoun", "186", " First cut to middleweight done without trouble."),
        item("2026-10-21", "Sherdog preview: -165 favourite (Malkoun +140); notes he tired in his July debut, says the move to 185 "
             "may help his cardio, and picks him by decision.", sherdog_prelims(6)),
    ],
    "jacob-malkoun": [
        made("186", "Vagaev", "185.5"),
        item("2026-10-21", "Sherdog preview: +140 underdog (Vagaev -165); thinks he goes back to wrestling even when striking "
             "would work and picks Vagaev by decision.", sherdog_prelims(6)),
    ],
    "bolaji-oki": [
        made("146", "Santos", "146", " First featherweight cut done."),
        item("2026-10-21", "Sherdog preview: +100 underdog (Santos -120); sees his size as an edge if he wrestles but doubts his "
             "defence under a high pace; picks Santos by second-round stoppage.", sherdog_prelims(7)),
        item("2026-10-19", "UFC.com Fight By Fight Preview expects an early Fight of the Night contender.", UFC_FBF),
    ],
    "daniel-santos": [
        made("146", "Oki", "146", " No weight trouble this time."),
        item("2026-10-21", "Sherdog preview: -120 favourite (Oki +100); picks him by second-round stoppage, while noting the Choi "
             "body-shot loss showed limits to his durability.", sherdog_prelims(7)),
    ],
    "kody-steele": [
        made("156", "Gugnon", "156"),
        item("2026-10-21", "Sherdog preview: -155 favourite (Gugnon +130); says Gugnon is the better puncher but Steele's grappling "
             "is the more reliable path; picks Steele by first-round submission.", sherdog_prelims(8)),
    ],
    "noah-gugnon": [
        made("156", "Steele", "156"),
        item("2026-10-21", "Sherdog preview: +130 underdog (Steele -155); credits his power but picks Steele by first-round "
             "submission.", sherdog_prelims(8)),
    ],
    "iasmin-lucindo": [
        item(WI, "Made weight at 115 lb. Caliari missed by 4.5 lb (120.5), forfeits 30% of her purse to Lucindo, and the bout "
             "goes ahead at catchweight.", UFC_WI),
        item("2026-10-21", "Sherdog preview: -380 favourite (Caliari +300); picks her by decision unless the 14-month layoff "
             "shows.", sherdog_prelims(9)),
    ],
    "nicolle-caliari": [
        item(WI, "Missed weight: 120.5 lb on her first attempt, 4.5 lb over the 116-lb non-title strawweight limit. Fined 30% of "
             "her purse (to Lucindo); the bout proceeds at catchweight. The only miss of the 28 fighters.", UFC_WI),
        item(WI, "Live weigh-in coverage (Uncrowned via Yahoo) logged the miss on her first trip to the scale; the bout was "
             "confirmed about half an hour later.", YAHOO_WI_LIVE),
        item("2026-10-21", "Sherdog preview: +300 underdog (Lucindo -380); expects her defensive grappling to survive but Lucindo "
             "to win on the cards.", sherdog_prelims(9)),
    ],
}

CONCERNS = {
    "nicolle-caliari": [
        "Badly missed weight for UFC 333 (120.5 lb, 4.5 over); also missed at Invicta FC 37 in 2019 (116.2 for a 116 limit)",
    ],
}
CONCERN_SOURCES = {"nicolle-caliari": [CAGESIDE_INVICTA37]}


def main():
    for slug, items in NEWS.items():
        path = REPORTS / f"{slug}.json"
        doc = json.loads(path.read_text())
        have = {n["text"] for n in doc["news"]}
        new = [n for n in items if n["text"] not in have]
        # Newest first, ahead of the existing items.
        doc["news"] = sorted(new, key=lambda n: n["date"], reverse=True) + doc["news"]
        for c in CONCERNS.get(slug, []):
            if c not in doc["concerns"]:
                doc["concerns"].append(c)
        for s in CONCERN_SOURCES.get(slug, []):
            if isinstance(doc.get("sources"), list) and not any(
                    (x.get("url") if isinstance(x, dict) else x) == s for x in doc["sources"]):
                doc["sources"].append({"outlet": "Cageside Press", "author": "",
                                       "title": "Invicta FC 37 Official Weigh-In Photo and Video Highlights",
                                       "url": s, "date": "2019-10-04"})
        doc["updated"] = UPDATED
        path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
        print(f"{slug}: +{len(new)} news")


if __name__ == "__main__":
    main()
