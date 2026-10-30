from mma_predictor.picks_cli import _card_bout

CARD = [{"a": "Zachary Reese", "b": "Mickey Gall"}, {"a": "Julian Erosa", "b": "Lee Jeong-yeong"},
        {"a": "Renato Moicano", "b": "Tom Nolan"}]


def test_card_bout_matches_short_first_names_and_reordered_names():
    assert _card_bout({"a": "Mickey Gall", "b": "Zach Reese"}, CARD) is CARD[0]
    assert _card_bout({"a": "Jeongyeong Lee", "b": "Julian Erosa"}, CARD) is CARD[1]
    assert _card_bout({"a": "Renato Moicano", "b": "Tom Nolan"}, CARD) is CARD[2]


def test_card_bout_needs_both_fighters():
    assert _card_bout({"a": "Someone Else", "b": "Tom Nolan"}, CARD) is None
