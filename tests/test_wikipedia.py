from mma_predictor.sources.wikipedia import match_key, parse_roster, propagate_gender, resolve

ROSTER = """
<html><body>
<h2 id="Debuted_fighters">Debuted fighters</h2>
<h3 id="Lightweights">Lightweights (155 lb, 70 kg)</h3>
<table class="wikitable sortable"><tr><th>Name</th></tr>
<tr><td><span class="fn"><a href="/wiki/A">Arman Tsarukyan</a></span></td></tr>
<tr><td><span class="fn"><a href="/wiki/B">Ian Machado Garry</a></span></td></tr></table>
<h3 id="LHW">Light heavyweights (205 lb, 93 kg)</h3>
<table class="wikitable"><tr><td><span class="fn">Magomed Ankalaev</span></td></tr></table>
<h3 id="WFly">Women's flyweights (125 lb, 56 kg)</h3>
<table class="wikitable"><tr><td><span class="fn">Valentina Shevchenko</span></td></tr></table>
<h2 id="See_also">See also</h2>
<table class="wikitable"><tr><td><span class="fn">Not A Fighter</span></td></tr></table>
</body></html>
"""


def test_parse_roster_divisions_and_gender():
    r = parse_roster(ROSTER)
    assert r["Arman Tsarukyan"] == ("Lightweight", "M")
    assert r["Magomed Ankalaev"] == ("Light Heavyweight", "M")
    assert r["Valentina Shevchenko"] == ("Flyweight", "F")
    assert "Not A Fighter" not in r


def test_resolve_handles_order_accents_and_extra_names():
    r = parse_roster(ROSTER)
    got = resolve(["Ian Garry", "tsarukyan arman", "Valentína Shevchenko", "Nobody Here"], r)
    assert got["Ian Garry"] == ("Lightweight", "M")
    assert got["tsarukyan arman"] == ("Lightweight", "M")
    assert got["Valentína Shevchenko"] == ("Flyweight", "F")
    assert "Nobody Here" not in got
    assert match_key("Song Yadong") == match_key("Yadong Song")


def test_gender_spreads_from_nearest_seed_and_survives_a_bad_edge():
    # Two women's and two men's chains, joined by one bad edge (name collision).
    bouts = [("W1", "W2"), ("W2", "W3"), ("M1", "M2"), ("M2", "M3"), ("W3", "M3")]
    got = propagate_gender(bouts, {"W1": "F", "M1": "M"})
    assert got["W2"] == "F" and got["M2"] == "M"
    assert got["W3"] == "F" and got["M3"] == "M"  # nearest seed wins near the bad edge
