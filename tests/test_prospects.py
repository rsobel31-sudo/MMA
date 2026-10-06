"""Prospects: eligibility screen, two-source check and scoring."""

from datetime import date

from mma_predictor import prospects as PR

TODAY = date(2026, 10, 1)


def row(**kw):
    r = {"division": "Lightweight", "rank": 300, "name": "Young Gun", "fm_url": "u", "age": 23, "wins": 8, "losses": 0, "draws": 0,
         "rating": 900, "last_fight": "2026-06-01", "last_org": "LFA", "country": "US"}
    r.update(kw)
    return r


def test_major_promotions():
    for org in ("UFC", "PFL", "PFL MENA", "Bellator", "OneFC", "ONE Championship", "ACA", "Rizin Fighting Federation"):
        assert PR.is_major(org), org
    for org in ("LFA", "Cage Warriors", "Dana Whites Contender Series", "Road to UFC", "Oktagon MMA", "KSW", "UAE Warriors"):
        assert not PR.is_major(org), org


def test_screen():
    assert PR.screen(row(), TODAY)
    assert not PR.screen(row(age=28), TODAY)
    assert not PR.screen(row(wins=10, losses=4), TODAY)          # 14 fights
    assert not PR.screen(row(last_org="UFC"), TODAY)
    assert not PR.screen(row(last_fight="2024-06-01"), TODAY)    # inactive


def sd(dob="2003-01-01", n_w=8, n_l=0, events=("LFA 200",)):
    bouts = [{"date": "2026-0%d-01" % (i % 9 + 1), "result": "win", "event": events[i % len(events)], "method": "KO/TKO", "opponent": "x", "round": 1}
             for i in range(n_w)]
    bouts += [{"date": "2025-01-01", "result": "loss", "event": "LFA 150", "method": "DEC", "opponent": "y", "round": 3}] * n_l
    return {"dob": dob, "bouts": bouts, "url": "s"}


def test_two_source_verify():
    ok = PR.verify(row(), {"stats": {"Birth Date": "2003-01-01"}, "bouts": []}, sd(), TODAY)
    assert ok["eligible"] and ok["verified"]
    major = PR.verify(row(), {"stats": {}, "bouts": [{"event": "UFC Fight Night 200"}]}, sd(), TODAY)
    assert not major["eligible"]
    disagree = PR.verify(row(), {"stats": {"Birth Date": "1995-01-01"}, "bouts": []}, sd(), TODAY)
    assert not disagree["eligible"] and any("birth dates" in i for i in disagree["issues"])
    old = PR.verify(row(), {"stats": {}, "bouts": []}, sd(dob="1990-01-01"), TODAY)
    assert not old["eligible"]
    assert not PR.verify(row(), {"stats": {}, "bouts": []}, None, TODAY)["eligible"]


def test_build_and_score():
    cands = []
    for i, (name, rating, losses) in enumerate([("Alpha One", 1200, 0), ("Beta Two", 800, 2), ("Gamma Three", None, 0)]):
        r = row(name=name, rating=rating, losses=losses, wins=8)
        s = dict(sd(n_l=losses), url="sd/" + name)
        cands.append(dict(r, fm={"stats": {}, "bouts": []}, sherdog=s, check=PR.verify(r, {"stats": {}, "bouts": []}, s, TODAY)))
    noted = {"lists": [{"outlet": "X", "title": "t", "url": "u", "names": ["Gamma Three"]}]}
    out = PR.build(cands, noted, TODAY)
    assert [p["name"] for p in out][0] == "Alpha One"
    g = next(p for p in out if p["name"] == "Gamma Three")
    assert g["components"]["rating"] == 0.5 and g["noted_by"] and g["components"]["buzz"] == 0.5
    assert all(0 <= p["score"] <= 100 for p in out) and out[0]["p4p_rank"] == 1 and out[0]["div_rank"] == 1


def test_source_track_grades_calls_and_holds_weights_until_enough():
    good = [{"date": f"2026-0{m}-01", "result": "win"} for m in (2, 3, 4)]
    bad = [{"date": f"2026-0{m}-01", "result": "loss"} for m in (2, 3, 4)]
    cands = [{"name": f"Good {i}", "sherdog": {"bouts": good}} for i in range(30)] + [{"name": f"Bad {i}", "sherdog": {"bouts": bad}} for i in range(30)]
    noted = {"lists": [
        {"kind": "creator", "outlet": "X", "author": "@sharp", "date": "2026-01", "names": [f"Good {i}" for i in range(25)]},
        {"kind": "forum", "outlet": "Forum", "author": "wrongway", "date": "2026-01", "names": [f"Bad {i}" for i in range(25)]},
        {"kind": "outlet", "outlet": "Few", "author": "", "date": "2026-01", "names": ["Good 25", "Bad 25"]},
        {"kind": "outlet", "outlet": "Late", "author": "", "date": "2026-09", "names": ["Good 26"]},
    ]}
    t = {x["author"] or x["outlet"]: x for x in PR.source_track(noted, cands, TODAY)}
    assert t["@sharp"]["hits"] == 25 and t["@sharp"]["weight"] == 2.0
    assert t["wrongway"]["weight"] == 0.0
    assert t["Few"]["graded"] == 2 and t["Few"]["weight"] == 1.0      # too few calls to judge
    assert t["Late"]["graded"] == 0                                   # no fights since the call yet


def test_match_name_handles_loose_list_names():
    hits = [("Caleb Lally", "a"), ("Maximus Lally", "b"), ("Sean Clancy Jr.", "c"), ("Ben Clancy", "d"),
            ("Daniyar Toychubek Uulu", "e"), ("Mehemmedali Osmanli", "f"), ("Kemal Osmanli", "g"), ("Kazbek Esembaev", "h")]
    assert PR.match_name("Max Lally", hits) == "b"
    assert PR.match_name("Sean Clancy", hits) == "c"
    assert PR.match_name("Daniyar Toychubek", hits) == "e"
    assert PR.match_name("Mehemmedeli Osmanli", hits) == "f"
    assert PR.match_name("Yusuf Esembaev", hits) == ""          # different person
    assert PR.match_name("Lally", hits) == ""
    assert PR.match_name("M Lally", hits + [("Mike Lally", "z")]) == ""   # ambiguous


def test_initials_fold_the_same_way_everywhere():
    from mma_predictor import news
    from mma_predictor.data import normalise_name
    from mma_predictor.sources.wikipedia import match_key
    for fn in (PR.fold, normalise_name, match_key, lambda s: news.fold(s).strip()):
        keys = {fn(n) for n in ("RJ Harris", "R.J. Harris", "R.J Harris", "R. J. Harris", "rj harris")}
        assert len(keys) == 1, (fn, keys)
    assert PR.fold("Mark O. Madsen") == "mark o madsen"      # a lone middle initial stays put


def test_two_spellings_are_one_prospect_credited_to_both_callers():
    r = row(name="Tommy Morrisson")
    s = dict(sd(), url="sd/morrison")
    cands = [dict(r, fm={"stats": {}, "bouts": []}, sherdog=s, check=PR.verify(r, {"stats": {}, "bouts": []}, s, TODAY))]
    noted = {"aliases": {"Tommy Morrisson": "Tommy Morrison"},
             "lists": [{"outlet": "A", "title": "t", "url": "u", "names": ["Tommy Morrisson"]},
                       {"outlet": "B", "title": "t", "url": "v", "names": ["Tommy Morrison"]}]}
    out = PR.build(cands, noted, TODAY)
    assert len(out) == 1 and {n["outlet"] for n in out[0]["noted_by"]} == {"A", "B"}
    assert out[0]["name"] == "Tommy Morrison"


def test_signing_is_a_hit_and_pre_signed_calls_are_not_graded():
    regional = {"date": "2025-03-01", "result": "win", "event": "LFA 200", "method": "KO/TKO"}
    ufc = {"date": "2026-05-16", "result": "loss", "event": "UFC Fight Night 276 - Allen vs. Costa", "method": "DEC"}
    assert PR.grade_call([regional, ufc], "2026-01-01") is True        # signed after the call, even with a loss
    assert PR.grade_call([regional, ufc], "2026-06-01") is None        # already in the UFC when named
    assert PR.promotion_of(ufc["event"]) == "UFC"
    assert PR.promotion_of("Professional Fighters League - PFL Dubai") == "PFL"


def test_signings_credit_first_caller():
    sd = {"url": "sd/minev", "bouts": [{"date": "2025-03-01", "result": "win", "event": "Fury FC 90", "method": "SUB"},
                                       {"date": "2026-05-16", "result": "win", "event": "UFC Fight Night 276", "method": "DEC"}]}
    cands = [{"name": "Artur Minev", "sherdog": sd, "check": {}}]
    noted = {"lists": [{"outlet": "B", "title": "t", "url": "v", "date": "2026-01", "names": ["Artur Minev"]},
                       {"outlet": "A", "title": "t", "url": "u", "date": "2025-12-16", "names": ["Artur Minev"]}]}
    out = PR.signings(noted, cands, {}, {"sd/minev": {"source": "BestFightOdds"}})
    assert len(out) == 1 and out[0]["first_call"]["outlet"] == "A" and out[0]["lead_days"] == 151
    assert out[0]["promotion"] == "UFC" and out[0]["confirmed_by"]


def test_left_a_major_is_eligible_again_but_not_the_ufc():
    aca = [{"date": "2023-03-09", "result": "win", "event": "ACA 153 - Dzhanaev vs. Pessoa", "method": "DEC", "opponent": "x", "round": 3},
           {"date": "2024-08-16", "result": "win", "event": "ACA 178", "method": "KO/TKO", "opponent": "y", "round": 1}]
    regional = {"date": "2026-01-31", "result": "win", "event": "Black Combat 16", "method": "KO/TKO", "opponent": "z", "round": 1}
    assert PR.major_status(aca) == ("in", ["ACA"])
    assert PR.major_status(aca + [regional]) == ("left", ["ACA"])
    assert PR.major_status([dict(aca[0], event="UFC 300")] + [regional])[0] == "ufc"
    s = dict(sd(), bouts=sd()["bouts"] + aca + [regional])
    chk = PR.verify(row(wins=11), {"stats": {}, "bouts": []}, s, TODAY)
    assert chk["eligible"] and chk["former"] == ["ACA"]
    # A call made while he was in ACA isn't graded; one made after he left is, and re-signing is a hit.
    assert PR.grade_call(aca + [regional], "2024-01-01") is None
    assert PR.grade_call(aca + [regional, dict(regional, date="2026-06-01", event="PFL 5")], "2026-02-01") is True


def test_winning_record_required():
    s = dict(sd(n_w=2, n_l=2))
    chk = PR.verify(row(wins=2, losses=2), {"stats": {}, "bouts": []}, s, TODAY)
    assert not chk["eligible"] and any("winning record" in i for i in chk["issues"])
    assert PR.verify(row(wins=2, losses=0), {"stats": {}, "bouts": []}, sd(n_w=2), TODAY)["eligible"]


def test_unrated_ladder_grows_with_experience():
    from mma_predictor.prospects import unrated_pct
    assert [unrated_pct(n) for n in (1, 2, 3, 4, 5, 6, 12)] == [0.15, 0.15, 0.15, 0.25, 0.40, 0.50, 0.50]
