from mma_predictor.dwcs import _same, parse_season

RAW = """== Week 8 – September 29 ==
{{Infobox MMA event
|name=Dana White's Contender Series 94
}}
{{MMAevent bout
|Lightweight
|George Staines
|def.
|Loai Abushaar
|KO (punches)
|1
|2:10
|
}}
<ref>{{Cite web |url=https://www.sherdog.com/events/Dana-Whites-Contender-Series-Contender-Series-2026-Week-8-112634 }}</ref>
== Week 10 – October 13 ==
{{MMAevent bout
|Women's Bantamweight
|[[Aline Pereira]]
|vs.
|[[Smilla Sundell]]
|
|
|
|
}}
{{MMAevent bout
|Flyweight
|Jarrett Betancourt
|vs.
|TBA
|
}}
"""


def test_parse_season_reads_finished_and_upcoming_weeks():
    w8, w10 = parse_season(RAW)
    assert (w8["week"], w8["date"], w8["name"]) == (8, "2026-09-29", "Dana White's Contender Series 94")
    assert w8["sherdog_url"].endswith("Week-8-112634")
    assert w8["bouts"] == [{"weight_class": "Lightweight", "a": "George Staines", "b": "Loai Abushaar", "decided": True}]
    assert [b["a"] for b in w10["bouts"]] == ["Aline Pereira"]  # links unwrapped; the TBA bout left out


def test_same_fighter_across_spellings():
    assert _same("Greg Foster", "Gregory Foster") and _same("Douglas da Lapa", "Douglas Lapa")
    assert not _same("Jason Asher", "Greg Foster")
