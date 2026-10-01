"""Owner's prospect suggestions -> calls credited to the commentator, merged per caller per day."""

from datetime import date

from mma_predictor.suggestions import call_list
from mma_predictor.tapology_import import add_list


def test_suggestion_becomes_a_call_by_the_commentator():
    s = {"name": " Abdi Iniestra ", "commentator": "Hellowhosthat", "where": "Sherdog forums", "said_on": "2026-09-30",
         "background": "Slick striker"}
    lst = call_list(s, date(2026, 10, 1))
    assert lst["names"] == ["Abdi Iniestra"] and lst["person"] == "Hellowhosthat" and lst["kind"] == "forum"
    assert lst["outlet"] == "Sherdog Forums" and lst["date"] == "2026-09-30" and lst["background"] == "Slick striker"


def test_two_suggestions_same_caller_same_day_merge():
    noted = {"lists": []}
    for n in ("A One", "B Two"):
        add_list(noted, call_list({"name": n, "commentator": "Koala", "where": "Other", "said_on": "2026-10-01"}, date(2026, 10, 1)))
    assert len(noted["lists"]) == 1 and noted["lists"][0]["names"] == ["A One", "B Two"]
