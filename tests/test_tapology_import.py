"""Tapology pages the owner saved: ranking lists -> dated calls, linked to the same person elsewhere."""

from argparse import Namespace

from mma_predictor import tapology_import as T

SAVED = """<!DOCTYPE html><!-- saved from url=(0099)https://www.tapology.com/profiles/hellowhosthat/my-rankings/4430-flyweight-prospects-outside-the-ufc-and-bellator -->
<html><head><title>My Flyweight Prospects Outside the UFC and Bellator | Tapology</title></head><body>
<nav><a href="/fightcenter/fighters/1-nav-link">Search</a></nav>
<div class="rankingItem"><span>1</span><a href="/fightcenter/fighters/12345-abdi-iniestra">Abdi Iniestra</a> 5-0</div>
<div class="rankingItem"><span>2</span><a href="https://www.tapology.com/fightcenter/fighters/222-gabriel-urbino">Gabriel "Gabo" Urbino</a></div>
<div class="sidebar"><a href="/fightcenter/fighters/12345-abdi-iniestra">Abdi Iniestra</a></div>
<p>Updated: Sep 14, 2026</p></body></html>"""


def args(**kw):
    base = dict(url="", title="", author="", date="", kind="creator", outlet="Tapology", person="", keep=True)
    base.update(kw)
    return Namespace(**base)


def test_saved_ranking_page_becomes_calls_linked_to_existing_person(tmp_path):
    f = tmp_path / "page.html"
    f.write_text(SAVED)
    noted = {"lists": [{"kind": "forum", "outlet": "Sherdog Forums", "author": "Hellowhosthat", "url": "s", "date": "2023-01-25", "names": ["X Y"]}]}
    msg = T.import_file(f, noted, args())
    lst = noted["lists"][-1]
    assert lst["names"] == ["Abdi Iniestra", "Gabriel Urbino"] and lst["author"] == "hellowhosthat"
    assert lst["date"] == "2026-09-14" and lst["outlet"] == "Tapology" and "Flyweight" in msg
    assert lst["person"] == "Hellowhosthat" and noted["lists"][0]["person"] == "Hellowhosthat"   # one track record
    assert noted["division_hints"]["Abdi Iniestra"] == "Flyweight"
    assert "already there" in T.import_file(f, noted, args())


def test_pasted_list_with_header(tmp_path):
    f = tmp_path / "list.txt"
    f.write_text("author: HuskySamoan\ntitle: Bantamweight prospects\ndate: 2026-09\n\n1. Asaf Chopurov (11-0) - best in the world\n2) Renat Khavalov\n- Ab\n")
    noted = {"lists": []}
    T.import_file(f, noted, args(outlet="Sherdog Forums"))
    lst = noted["lists"][0]
    assert lst["names"] == ["Asaf Chopurov", "Renat Khavalov"] and lst["author"] == "HuskySamoan" and lst["date"] == "2026-09"
