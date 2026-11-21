"""The GitHub UFCStats scrape (Greco1899/scrape_ufc_stats): per-round rows summed into Kaggle-schema bouts."""

from pathlib import Path

from mma_predictor.sources import greco_ufcstats as G

FIX = Path(__file__).parent / "fixtures" / "greco"


def test_convert_sums_rounds_and_reads_the_result():
    fighters, fights = G.convert(FIX)
    (b,) = fights
    assert (b["date"], b["fighter_a"], b["fighter_b"], b["winner"]) == ("2026-11-14", "Ciryl Gane", "Josh Hokit", "Josh Hokit")
    assert (b["weight_class"], b["title_fight"], b["scheduled_rounds"], b["method"]) == ("Heavyweight", "1", "5", "Decision - Unanimous")
    assert (b["a_sig_landed"], b["a_sig_attempted"], b["a_knockdowns"], b["a_ctrl_seconds"]) == ("51", "85", "1", "93")
    assert (b["a_td_landed"], b["a_td_attempted"], b["a_sub_attempts"], b["a_ground_landed"]) == ("1", "2", "1", "3")
    assert (b["b_sig_landed"], b["b_td_landed"], b["b_ctrl_seconds"]) == ("20", "2", "120")
    assert fighters[0] == {"name": "Ciryl Gane", "dob": "1990-04-12", "height_cm": "193.0", "reach_cm": "205.7",
                           "stance": "Orthodox", "source": "ufcstats", "url": "http://ufcstats.com/fighter-details/aaaa"}


def test_merge_adds_only_bouts_after_our_last_date():
    have = [{"date": "2026-08-08", "fighter_a": "A B", "fighter_b": "C D", "a_sig_attempted": "1"}]
    new = [dict(have[0]),
           {"date": "2025-01-01", "fighter_a": "Old Spelling", "fighter_b": "X Y", "a_sig_attempted": "5"},
           {"date": "2026-11-14", "fighter_a": "Ciryl Gane", "fighter_b": "Josh Hokit", "a_sig_attempted": "85"}]
    fighters, fights, added = G.merge([], have, [{"url": "u1", "name": "Ciryl Gane"}], new)
    assert [a["date"] for a in added] == ["2026-11-14"]
    assert len(fights) == 2 and fighters == [{"url": "u1", "name": "Ciryl Gane"}]


def test_weight_class_names():
    assert G._weight_class("UFC Women's Flyweight Title Bout") == ("Women's Flyweight", "1")
    assert G._weight_class("Lightweight Bout") == ("Lightweight", "0")
    assert G._weight_class("UFC Interim Lightweight Title Bout") == ("Lightweight", "1")
