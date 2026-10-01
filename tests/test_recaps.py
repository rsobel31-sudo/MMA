"""Card recaps: model vs market vs result per card, live picks preferred over the backtest."""

from datetime import date

from mma_predictor.analysis import card_recaps
from mma_predictor.data import Fight, Method


def test_card_recaps_scores_each_source_and_prefers_live_picks():
    d = date(2026, 9, 26)
    fights = [Fight(d, f"A{i}", f"B{i}", f"A{i}" if i % 2 == 0 else f"B{i}", Method.KO, 1, 0, event="UFC X") for i in range(4)]
    preds = [(f, 0.7, None) for f in fights]                        # model always likes A
    market = {f"{d}|A{i}|B{i}": {"a_close": -150, "b_close": 130} for i in range(4)}
    live = {"2026-09-26|a0|b0": {"a": "A0", "first": {"p_a": 0.9}}}
    out = card_recaps(preds, market, {"model": 0.4, "market": 0.8}, live)
    ev = out["events"][0]
    assert ev["live"] == 1 and ev["summary"]["model"]["correct"] == 2
    b0 = next(b for b in ev["bouts"] if b["a"] == "A0")
    assert b0["source"] == "live" and b0["model"] == 0.9
    assert out["season"]["cards"] == 1 and out["season"]["market"]["n"] == 4


def test_page_ids_match_the_page_slug():
    from mma_predictor.recap_cli import bout_key, page_slug, recap_id
    assert recap_id({"date": "2026-09-26", "event": "UFC Fight Night 289 - Rosas Jr. vs. Barcelos"}) == "2026-09-26-ufc-fight-night-289-rosas-jr-vs-barcelos"
    assert bout_key({"a": "Raoni Barcelos", "b": "Raul Rosas Jr."}) == "raoni-barcelos-raul-rosas-jr"
    assert page_slug("Mário") == "ma-rio"   # same quirk as the page's slug(): lowercase before NFKD
