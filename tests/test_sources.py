from datetime import date
from pathlib import Path

from mma_predictor.data import Method, load_dataset
from mma_predictor.history import FightHistory
from mma_predictor.sources import common, sherdog, tapology
from mma_predictor.sources.merge import merge_datasets

FIX = Path(__file__).parent / "fixtures"


def test_sherdog_parses_pro_record_and_skips_amateur():
    page = sherdog.parse_fighter((FIX / "sherdog_fighter.html").read_text(), "https://www.sherdog.com/fighter/Testy-1")
    assert page.name == "Testy McTestface"
    assert page.dob == date(1990, 7, 22)
    assert page.height_cm == 193.04
    assert [b.opponent for b in page.bouts] == ["Other Guy", "Third Person", "Regional Rick"]
    loss = page.bouts[0]
    assert (loss.result, loss.method, loss.round, loss.time, loss.date) == ("loss", Method.KO, 2, "4:21", date(2024, 4, 13))
    assert loss.opponent_url == "https://www.sherdog.com/fighter/Other-Guy-1001"
    assert loss.title_fight
    assert page.bouts[1].method is Method.SPLIT_DEC
    assert page.bouts[2].method is Method.SUB


def test_tapology_parses_pro_record_and_bio():
    page = tapology.parse_fighter((FIX / "tapology_fighter.html").read_text(), "https://www.tapology.com/fightcenter/fighters/testy")
    assert page.name == "Testy McTestface"
    assert page.dob == date(1990, 7, 22)
    assert (page.height_cm, page.reach_cm, page.stance) == (193.0, 203.0, "Southpaw")
    assert [b.opponent for b in page.bouts] == ["Other Guy", "Third Person", "NC Nick"]
    first = page.bouts[0]
    assert (first.result, first.method, first.round, first.time) == ("loss", Method.KO, 2, "4:21")
    assert first.scheduled_rounds == 5 and first.title_fight
    assert page.bouts[1].result == "win" and page.bouts[1].method.is_decision
    assert page.bouts[2].result == "nc"


def test_pages_to_rows_dedupes_bouts_seen_from_both_sides(tmp_path):
    a = common.FighterPage("u/a", "Alpha", bouts=[
        common.CareerBout(date(2024, 1, 1), "Beta", "u/b", "win", Method.KO, 1, "1:00"),
    ])
    b = common.FighterPage("u/b", "Beta", bouts=[
        common.CareerBout(date(2024, 1, 1), "Alpha", "u/a", "loss", Method.KO, 1, "1:00"),
        common.CareerBout(date(2023, 1, 1), "Gamma", None, "draw", Method.DEC, 3, "5:00"),
    ])
    fighters, fights = common.pages_to_rows([a, b], "test")
    assert len(fights) == 2
    assert {f["name"] for f in fighters} == {"Alpha", "Beta", "Gamma"}
    common.write_dataset(tmp_path, fighters, fights)
    bios, loaded = load_dataset(tmp_path)
    h = FightHistory(bios, loaded)
    assert h.snapshot("Alpha").wins == 1
    assert loaded[0].winner is None  # the draw


def test_merge_prefers_row_with_stats_and_matches_across_dates(tmp_path):
    career, stats = tmp_path / "career", tmp_path / "stats"
    common.write_dataset(career, [{"name": "Alpha", "dob": "1990-01-01"}, {"name": "Beta"}], [
        {"date": "2024-01-02", "fighter_a": "Beta", "fighter_b": "Alpha", "winner": "Alpha", "method": "KO/TKO", "round": "1", "time": "1:00"},
        {"date": "2020-05-05", "fighter_a": "Alpha", "fighter_b": "Local Guy", "winner": "Alpha", "method": "SUB", "round": "1", "time": "2:00"},
    ])
    common.write_dataset(stats, [{"name": "Alpha", "reach_cm": "190"}], [
        {"date": "2024-01-01", "fighter_a": "Alpha", "fighter_b": "Beta", "winner": "Alpha", "method": "KO/TKO", "round": "1", "time": "1:00",
         "a_sig_landed": "10", "a_sig_attempted": "20", "b_sig_landed": "3", "b_sig_attempted": "9"},
    ])
    nf, nb = merge_datasets([stats, career], tmp_path / "out")
    assert nb == 2
    bios, fights = load_dataset(tmp_path / "out")
    assert bios["Alpha"].reach_cm == 190 and bios["Alpha"].dob == date(1990, 1, 1)
    ufc = [f for f in fights if f.fighter_b == "Beta"][0]
    assert ufc.stats_a is not None and ufc.stats_a.sig_landed == 10
