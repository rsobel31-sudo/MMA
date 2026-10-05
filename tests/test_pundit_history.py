import json

from mma_predictor import pundit_history as H
from mma_predictor.reads import Pundits, pundit_weight

FIGHTS = """date,event,weight_class,fighter_a,fighter_b,winner,method,round,time,scheduled_rounds,title_fight,a_odds,b_odds
2099-05-02,UFC 999 - Ace vs. Bold,,Ann Ace,Bea Bold,Bea Bold,KO/TKO,2,1:00,5,1,-200,170
2099-05-02,UFC 999 - Ace vs. Bold,,Cy Cole,Doo Ho Choi,Cy Cole,DEC,3,5:00,3,0,150,-180
2099-05-02,UFC 999 - Ace vs. Bold,,Ed Eel,Fi Fox,,NC,1,0:30,3,0,-110,-110
"""


def _bouts(tmp_path):
    p = tmp_path / "fights.csv"
    p.write_text(FIGHTS)
    a = tmp_path / "aliases.json"
    a.write_text(json.dumps({"Annie Ace": "Ann Ace"}))
    return H.Bouts(p, a)


def test_parse_method_reads_words_and_shorthand():
    assert H.parse_method("via second-round knockout") == ("KO/TKO", 2)
    assert H.parse_method("TKO2") == ("KO/TKO", 2)
    assert H.parse_method("Sub3") == ("SUB", 3)
    assert H.parse_method("by unanimous decision") == ("DEC", None)
    assert H.parse_method("") == ("", None)


def test_novig_removes_the_margin():
    assert abs(H.novig("-200", "170") - 0.643) < 0.002
    assert H.novig("", "170") is None


def test_cbs_table_grades_each_expert_against_the_market(tmp_path):
    B = _bouts(tmp_path)
    page = """<p>Picks by Brian Campbell and Brent Brookhouse.</p><table>
      <tr><th></th><th>Campbell</th><th>Brookhouse</th></tr>
      <tr><td>Ace (c) vs. Bold</td><td>Bold TKO2</td><td>Ace UD</td></tr>
      <tr><td>Cole vs. Choi</td><td>Choi SUB1</td><td>Cole UD</td></tr></table>"""
    rows, skipped = H.resolve(B, H.parse_cbs(page), "CBS Sports", "u", "2099-04-30")
    assert not skipped
    by = {(r["author"], r["a"]): r for r in rows}
    r = by[("Brian Campbell", "Ann Ace")]
    assert (r["pick"], r["grade"], r["method"], r["method_correct"]) == ("Bea Bold", "won", "KO/TKO R2", True)
    assert abs(r["p_market"] - 0.357) < 0.002  # the underdog's no-vig chance
    assert by[("Brent Brookhouse", "Cy Cole")]["grade"] == "won"
    assert by[("Brian Campbell", "Cy Cole")]["grade"] == "lost"


def test_staff_articles_follow_bouts_and_first_name_writers(tmp_path):
    B = _bouts(tmp_path)
    page = """<script type="application/ld+json">{"author":[{"name":"Mat Riddle"},{"name":"Zain Bando"}]}</script>
      <p>Our staff picks.</p><h2>Ann Ace vs. Bea Bold Predictions</h2>
      <p>Mat: Ace has the reach. (Pick: Ace)</p><p>Zain: Bold by knockout. (Pick: Bold)</p>
      <h2>Cy Cole -150</h2><p>Vs.</p><h2>Doo Ho Choi +130</h2>
      <p>Mat:</p><p>Cole by unanimous decision</p><p>Staff picking Cole: 1</p>
      <p>Zain:</p><p>Choi by second round knockout</p>"""
    cands = B.window("2099-04-30")
    rows, skipped = H.resolve(B, H.parse_staff(page, B, cands), "SI", "u", "2099-04-30", cands)
    got = {(r["author"], r["pick"], r["pick_method"]) for r in rows}
    assert got == {("Mat Riddle", "Ann Ace", ""), ("Zain Bando", "Bea Bold", ""),
                   ("Mat Riddle", "Cy Cole", "DEC"), ("Zain Bando", "Doo Ho Choi", "KO/TKO")}


def test_cageside_headshots_and_void_bouts(tmp_path):
    B = _bouts(tmp_path)
    content = """<table><thead><tr><th>Writer / Fight</th><th>Ace vs. Bold</th><th>Eel vs. Fox</th></tr></thead><tbody>
      <tr><td>Pat Danna (10-5)</td><td><img src="https://x/uploads/2099/04/bea-bold-headshot.png"></td>
      <td><img src="https://x/uploads/2099/04/Fi-Fox.png"></td></tr></tbody></table>"""
    rows, _ = H.resolve(B, H.parse_cageside(content), "Cageside Press", "u", "2099-05-02")
    assert [(r["author"], r["pick"], r["grade"]) for r in rows] == [("Pat Danna", "Bea Bold", "won"), ("Pat Danna", "Fi Fox", "void")]


def test_sherdog_preview_page(tmp_path):
    B = _bouts(tmp_path)
    page = """<a href="/authors/Tom-Feely-1675">Tom Feely</a><div>Heavyweights</div>
      <p>Cy<br>Cole (10-1) vs. Doo Ho<br>Choi (12-3)</p><p>Odds: ...</p>
      <p>Long analysis. In the end, the pick is Cole via decision.</p>"""
    rows, _ = H.resolve(B, H.parse_sherdog(page), "Sherdog", "u", "2099-04-29")
    assert [(r["author"], r["pick"], r["pick_method"], r["grade"]) for r in rows] == [("Tom Feely", "Cy Cole", "DEC", "won")]


def test_unmatched_picks_are_reported_not_guessed(tmp_path):
    B = _bouts(tmp_path)
    rows, skipped = H.resolve(B, [("A Writer", "Nobody", "Someone", "Nobody by KO")], "X", "u", "2099-04-30")
    assert rows == [] and skipped


def test_scoreboard_merges_spellings_and_ranks_by_edge_over_market(tmp_path):
    P = Pundits(tmp_path / "p.jsonl")
    def row(author, grade, p, i):
        return {"event": f"E{i}", "date": "2099-01-01", "a": f"A{i}", "b": f"B{i}", "outlet": "O", "author": author,
                "pick": f"A{i}", "p_market": p, "grade": grade}
    # A chalk picker (75% right on 80% favourites) and an underdog picker (50% right on 35% dogs).
    P.rows = [row("Frazer Kron" if i % 2 else "Frazer Krohn", "won" if i % 4 else "lost", 0.8, i) for i in range(60)]
    P.rows += [row("Dee Dog", "won" if i % 2 else "lost", 0.35, 100 + i) for i in range(60)]
    sb = P.scoreboard(today="2099-06-01")
    assert [s["author"] for s in sb] == ["Dee Dog", "Frazer Kron"] or [s["author"] for s in sb] == ["Dee Dog", "Frazer Krohn"]
    dog, chalk = sb
    assert chalk["picks"] == 60 and chalk["accuracy"] == 0.75 and chalk["z"] < 0
    assert dog["z"] > 2.0 and dog["weight"] == 1.5


def test_weights_need_a_long_record_and_a_clear_edge():
    assert pundit_weight(39, 3.0) == 1.0
    assert pundit_weight(40, 1.5) == 1.0
    assert pundit_weight(40, 2.0) == 1.5 and pundit_weight(40, 2.6) == 2.0
    assert pundit_weight(40, -2.0) == 0.5 and pundit_weight(40, -2.6) == 0.0


def test_consensus_counts_pickers_by_track_record():
    from mma_predictor.reads import pundit_consensus
    board = [{"author": "Dee Dog", "weight": 2.0}, {"author": "Che X", "weight": 0.0}]
    cs = pundit_consensus([{"author": "Dee Dog", "pick": "A"}, {"author": "Ché X", "pick": "B"}, {"author": "New Guy", "pick": "B"}], board)
    assert cs == {"pick": "A", "share": 0.667, "n": 3, "raw_share": 0.333}
    assert pundit_consensus([], board) is None


def test_cageside_encoded_filenames_and_nicknames(tmp_path, monkeypatch):
    nick = tmp_path / "nick.json"
    nick.write_text(json.dumps({"Suga": "Bea Bold"}))
    monkeypatch.setattr(H, "NICKNAMES", nick)
    B = _bouts(tmp_path)
    content = """<table><tr><th>Writer / Fight</th><th>Ace vs. Suga</th><th>Cole vs. Choi</th></tr>
      <tr><td>Pat Danna</td><td><img src="https://x/up/suga-belt.png"></td>
      <td><img src="https://x/up/689772%2Fprofile_galery%2Fprofile_picture%2FCOLE_CY_1.png"></td></tr></table>"""
    rows, skipped = H.resolve(B, H.parse_cageside(content), "Cageside Press", "u", "2099-05-02")
    assert not skipped
    assert [r["pick"] for r in rows] == ["Bea Bold", "Cy Cole"]
