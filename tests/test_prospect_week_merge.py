from mma_predictor.prospect_week import merge_bouts


def _b(date, result=None, event="e1"):
    b = {"date": date, "event_url": event, "prospect_url": "p", "opponent_url": "o"}
    if result:
        b["result"] = result
    return b


def test_rescheduled_bout_moves_instead_of_duplicating():
    known, new = merge_bouts([_b("2026-11-11")], [_b("2026-11-07")])
    assert new == [] and [b["date"] for b in known] == ["2026-11-07"]


def test_old_duplicate_collapses_to_the_graded_bout():
    known, _ = merge_bouts([_b("2026-11-07", "loss"), _b("2026-11-11")], [])
    assert len(known) == 1 and known[0]["result"] == "loss"


def test_graded_bout_keeps_its_date_and_new_event_is_added():
    known, new = merge_bouts([_b("2026-11-07", "loss")], [_b("2026-11-11"), _b("2026-11-20", event="e2")])
    assert [b["date"] for b in known] == ["2026-11-07", "2026-11-20"] and len(new) == 1
