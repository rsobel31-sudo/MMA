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
        s = sd(n_l=losses)
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
