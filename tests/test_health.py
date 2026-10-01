"""Crawler health: every source has a check, and thresholds read sensibly."""

from mma_predictor.health import _at_least, checks


def test_every_source_has_a_check():
    names = [c[0] for c in checks()]
    for must in ("Sherdog fighter pages", "Fight Matrix rankings", "BestFightOdds events", "Wikipedia UFC roster", "StatsFight", "Kaggle UFCStats dump"):
        assert must in names
    assert len(names) == len(set(names))


def test_at_least():
    assert _at_least(3, 5, "rows") == (True, "5 rows")
    ok, detail = _at_least(400, 371, "fighters")
    assert not ok and "expected at least 400" in detail
