from datetime import date

from mma_predictor import regional as R


def test_promotion_names():
    assert R.promotion("Fury FC 103 - Fury Fighting Championship 103") == "Fury FC"
    assert R.promotion("Pancrase - Blood.9") == "Pancrase"
    assert R.promotion("UFC - Road to UFC Season 4: Shanghai") == "Road to UFC"


def test_replay_moves_winner_up_and_skips_self_bouts():
    bs = [R.Bout(date(2024, 1, 1), "a", "b", 1.0, "KO", "x"), R.Bout(date(2024, 2, 1), "a", "a", 1.0, "KO", "x")]
    ps = R.replay(bs)
    assert ps["a"].r > 1500 > ps["b"].r and ps["a"].n == 1
    # A firmer prior moves a single result less.
    assert R.replay(bs, rd0=200)["a"].r < ps["a"].r


def test_ufc_feeder_shows_are_not_minor_leagues():
    from mma_predictor import minor_leagues as ML

    assert {"Dana White's Contender Series", "Road to UFC"} <= ML.FEEDERS


def test_a_promotions_old_event_names_count_with_its_new_ones():
    from mma_predictor import minor_leagues as ML

    orgs = {"CW": {"org_url": "https://www.sherdog.com/organizations/Cage-Warriors-186", "org_name": "Cage Warriors",
                   "events": [["2013-07-06", "CWFC 56 - Cage Warriors Fighting Championship 56", ""],
                              ["2018-02-24", "CW 90 - Cage Warriors 90", ""]]}}
    canon = ML.canonicalizer(orgs)
    assert canon("CWFC 60 - Cage Warriors Fighting Championship 60") == "CW"
    assert canon("UFC 300 - Pereira vs. Hill") == "UFC"


def test_roster_moves_parse_wikipedia_tables():
    from mma_predictor import roster_moves as RM

    html = """<h2 id="Recent_releases_and_retirements">x</h2><table><tr><th>Date</th><th>Country</th><th>Name</th><th>Nickname</th>
    <th>Reason</th><th>Division</th><th>Ref</th></tr><tr><td>Sep 16, 2026</td><td></td><td>Lyman Good</td><td>Cyborg</td>
    <td>Released</td><td>Welterweight</td><td><a href="#cite_note-2">[2]</a></td></tr></table>
    <h2 id="Recent_signings">y</h2><table><tr><th>Date</th><th>ISO</th><th>Name</th><th>Nickname</th><th>Division</th>
    <th>Status / next fight / Info</th><th>Ref</th></tr><tr><td>October 6, 2026</td><td></td><td>Preston LaGrange</td>
    <td>One Shot</td><td>Light Heavyweight</td><td></td><td><a href="#cite_note-9">[9]</a></td></tr></table><h2 id="z">z</h2>
    <ol><li id="cite_note-2"><a rel="nofollow" class="external text" href="https://www.mmamania.com/cuts">a</a></li>
    <li id="cite_note-9"><a rel="nofollow" class="external text" href="https://cagesidepress.com/dwcs">b</a></li></ol>"""
    got = RM.parse(html)
    assert got["releases"] == [{"name": "Lyman Good", "date": "2026-09-16", "division": "Welterweight",
                                "refs": ["https://www.mmamania.com/cuts"], "reason": "Released"}]
    assert got["signings"][0]["name"] == "Preston LaGrange" and got["signings"][0]["date"] == "2026-10-06"
    assert got["signings"][0]["refs"] == ["https://cagesidepress.com/dwcs"]
