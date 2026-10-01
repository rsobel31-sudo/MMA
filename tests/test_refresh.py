"""Weekly refresh: fresh pages merge into the saved dataset without duplicates."""

import json

from mma_predictor.refresh import merge_rows, upsert_jsonl


def fight(d, a, b, w, m="KO/TKO", **kw):
    r = {"date": d, "event": "E", "weight_class": "", "fighter_a": a, "fighter_b": b, "winner": w, "method": m,
         "round": "1", "time": "1:00", "scheduled_rounds": "3", "title_fight": "0"}
    r.update(kw)
    return r


def test_merge_adds_new_bouts_updates_results_and_keeps_names():
    fighters = [{"name": "A.J. Smith", "url": "u1", "dob": "", "gender": "M"}, {"name": "Bo Jones", "url": "u2", "gender": "M"}]
    fights = [fight("2026-01-01", "A.J. Smith", "Bo Jones", "A.J. Smith", m="DEC")]
    new_f = [{"name": "AJ Smith", "url": "u1", "dob": "1999-01-01", "profile": "1"},
             {"name": "Cy Young", "url": "u3", "profile": "1"}]
    new_b = [fight("2026-01-02", "Bo Jones", "AJ Smith", "nc", m="NC"),          # same bout, a day off, overturned
             fight("2026-09-26", "AJ Smith", "Cy Young", "AJ Smith")]            # new bout
    out = merge_rows(fighters, fights, new_f, new_b)
    assert len(fights) == 2 and len(out["added_bouts"]) == 1 and out["added_fighters"] == 1
    assert fights[0]["winner"] == "nc" and fights[0]["fighter_a"] == "A.J. Smith"    # orientation and name kept
    assert fights[1]["fighter_a"] == "A.J. Smith" and fights[1]["winner"] == "A.J. Smith"
    assert fighters[0]["dob"] == "1999-01-01" and fighters[0]["gender"] == "M"
    assert out["changed"] and out["changed"][0]["now"] == "nc (NC)"


def test_upsert_jsonl_replaces_in_place(tmp_path):
    p = tmp_path / "x.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in [{"url": "a", "v": 1}, {"url": "b", "v": 1}]) + "\n")
    assert upsert_jsonl(p, [{"url": "a", "v": 2}, {"url": "c", "v": 1}]) == (1, 1)
    rows = [json.loads(l) for l in p.read_text().splitlines()]
    assert [(r["url"], r["v"]) for r in rows] == [("a", 2), ("b", 1), ("c", 1)]
