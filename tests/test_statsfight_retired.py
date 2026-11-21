"""StatsFight went behind a bot check on 2026-11-17: no health check, no refresh crawl."""

from mma_predictor import health
from mma_predictor.sources import statsfight


def test_health_has_no_statsfight_check():
    assert not any("statsfight" in name.lower() for name, _, _ in health.checks())


def test_bot_check_page_detected():
    assert statsfight.is_bot_check('<a href="https://statsfight.com/.within.website/?redir=x">')
    assert not statsfight.is_bot_check("<urlset><url><loc>https://statsfight.com/schedule/ufc/a/b/</loc></url></urlset>")


def test_retired_note_names_the_reason():
    assert "bot check" in statsfight.RETIRED
