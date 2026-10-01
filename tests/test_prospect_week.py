"""Prospect fights this week: Sherdog event pages -> bouts."""

from mma_predictor.prospect_week import event_bouts, listing

EVENT = """<h1 itemprop="name"><span itemprop="name">Fury FC 125 - Meck vs. Taylor</span></h1>
<div class="fight_card"><a href="/fighter/Nicholas-Meck-374777">Meck</a><a href="/fighter/Nicholas-Meck-374777">x</a>
<a href="/fighter/Dilano-Taylor-332083">Taylor</a></div>
<table><tr><td><a href="/fighter/Carlos-Calderon-247279">C</a></td><td><a href="/fighter/Lorram-Esteves-183397">E</a></td></tr>
<tr><td><a href="/fighter/Yehia-Riles-381468">R</a></td><td><a href="/fighter/JaCobi-Jones-326955">J</a></td></tr></table>"""

LISTING = """<table><tr><td><a href="/events/Fury-FC-125-114025">Fury FC 125</a></td><td>Oct 02, 2026</td></tr>
<tr><td><a href="/events/LUX-063-112992">LUX 063</a></td><td>Oct 02, 2026</td></tr></table>"""


def test_event_bouts_main_event_then_rows():
    name, bouts = event_bouts(EVENT)
    assert name == "Fury FC 125 - Meck vs. Taylor"
    assert [tuple(u.rsplit("/", 1)[-1] for u in b) for b in bouts] == [
        ("Nicholas-Meck-374777", "Dilano-Taylor-332083"), ("Carlos-Calderon-247279", "Lorram-Esteves-183397"),
        ("Yehia-Riles-381468", "JaCobi-Jones-326955")]


def test_listing_dates():
    rows = listing(LISTING)
    assert len(rows) == 2 and rows[0][0].isoformat() == "2026-10-02" and rows[0][1].endswith("Fury-FC-125-114025")
