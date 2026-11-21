"""UFCStats per-fight stats from the public GitHub scrape Greco1899/scrape_ufc_stats.

The repository re-scrapes UFCStats (the UFC's official statistics) and commits CSVs after
every card (weekly since 2026-08). It replaces the Kaggle dump, which stopped updating on
2026-08-11, and it is the same underlying data: totals summed from its per-round rows match
the Kaggle dump bout for bout (e.g. Asplund vs. Pat, 2026-08-08: 66 of 109 significant
strikes, 2 knockdowns, 284 s control). ufcstats.com itself sits behind a bot check, so we
read the repository, never the site.

    git clone --depth 1 https://github.com/Greco1899/scrape_ufc_stats <dir>

Only CSVs are read (no code from the repository is run). The rows use the Kaggle import's
schema, and bouts already in data/ufcstats are kept: this adds the ones it lacks. Results
are still checked against Sherdog by verify before any stats are used.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

REPO = "https://github.com/Greco1899/scrape_ufc_stats"


def _of(raw: str) -> Tuple[int, int]:
    m = re.match(r"\s*(\d+)\s+of\s+(\d+)", raw or "")
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def _num(raw: str) -> int:
    try:
        return int(float((raw or "").strip()))
    except ValueError:
        return 0


def _secs(raw: str) -> int:
    m = re.match(r"\s*(\d+):(\d+)", raw or "")
    return int(m.group(1)) * 60 + int(m.group(2)) if m else 0


def _height_cm(raw: str) -> str:
    m = re.match(r"(\d+)'\s*(\d+)", raw or "")
    return f"{(int(m.group(1)) * 12 + int(m.group(2))) * 2.54:.1f}" if m else ""


def _reach_cm(raw: str) -> str:
    m = re.match(r"\s*(\d+(?:\.\d+)?)\"?", raw or "")
    return f"{float(m.group(1)) * 2.54:.1f}" if m else ""


def _dob(raw: str) -> str:
    try:
        return datetime.strptime((raw or "").strip(), "%b %d, %Y").date().isoformat()
    except ValueError:
        return ""


def _method(raw: str, outcome: str) -> str:
    m = (raw or "").strip()
    if outcome == "D/D":
        return "Draw"
    if outcome == "NC/NC" or m == "Overturned":
        return "NC"
    if m in ("Could Not Continue", "Other"):
        return "TKO - " + m  # same rule as the Kaggle import
    return m


def _weight_class(raw: str) -> Tuple[str, str]:
    """'UFC Heavyweight Title Bout' -> ('Heavyweight', '1'); 'Lightweight Bout' -> ('Lightweight', '0')."""
    w = (raw or "").strip()
    title = "1" if "Title" in w else "0"
    w = re.sub(r"^(UFC|Ultimate Fighter \d+|Interim)\s+", "", w)
    w = re.sub(r"\s*(Interim\s+)?(Title\s+)?Bout$", "", w).replace("Interim ", "").strip()
    return w or "Bout", title


def convert(src: Path) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    src = Path(src)
    rd = lambda name: csv.DictReader(open(src / name, newline="", encoding="utf-8"))  # noqa: E731
    dates = {r["EVENT"].strip(): datetime.strptime(r["DATE"].strip(), "%B %d, %Y").date().isoformat()
             for r in rd("ufc_event_details.csv")}

    totals: Dict[Tuple[str, str, str], Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in rd("ufc_fight_stats.csv"):
        t = totals[(r["EVENT"].strip(), r["BOUT"].strip(), r["FIGHTER"].strip())]
        for key, col in (("sig", "SIG.STR."), ("td", "TD"), ("ground", "GROUND")):
            landed, att = _of(r[col])
            t[f"{key}_landed"] += landed
            t[f"{key}_attempted"] += att
        t["knockdowns"] += _num(r["KD"])
        t["sub_attempts"] += _num(r["SUB.ATT"])
        t["ctrl_seconds"] += _secs(r["CTRL"])
        t["rounds"] += 1

    fights: List[Dict[str, str]] = []
    for r in rd("ufc_fight_results.csv"):
        event, bout, outcome = r["EVENT"].strip(), r["BOUT"].strip(), r["OUTCOME"].strip()
        if event not in dates or " vs. " not in bout:
            continue
        a, b = (x.strip() for x in bout.split(" vs. ", 1))
        winner = {"W/L": a, "L/W": b, "D/D": "draw"}.get(outcome, "nc")
        wc, title = _weight_class(r["WEIGHTCLASS"])
        sched = re.match(r"(\d+) Rnd", r["TIME FORMAT"] or "")
        row = {"date": dates[event], "event": event, "weight_class": wc, "fighter_a": a, "fighter_b": b,
               "winner": winner, "method": _method(r["METHOD"], outcome), "round": r["ROUND"].strip(),
               "time": r["TIME"].strip(), "scheduled_rounds": sched.group(1) if sched else "1", "title_fight": title}
        for side, name in (("a", a), ("b", b)):
            t = totals.get((event, bout, name))
            for k in ("sig_landed", "sig_attempted", "td_landed", "td_attempted", "sub_attempts", "knockdowns",
                      "ctrl_seconds", "ground_landed"):
                row[f"{side}_{k}"] = str(t[k]) if t else ""
        fights.append(row)
    fights.sort(key=lambda x: x["date"])

    fighters = [{"name": r["FIGHTER"].strip(), "dob": _dob(r["DOB"]), "height_cm": _height_cm(r["HEIGHT"]),
                 "reach_cm": _reach_cm(r["REACH"]), "stance": (r["STANCE"] or "").strip(), "source": "ufcstats",
                 "url": r["URL"].strip()} for r in rd("ufc_fighter_tott.csv") if r["FIGHTER"].strip()]
    return fighters, fights


def _key(row: Dict[str, str]) -> Tuple[str, Tuple[str, str]]:
    norm = lambda s: re.sub(r"[^a-z]", "", s.lower())  # noqa: E731
    return row["date"], tuple(sorted((norm(row["fighter_a"]), norm(row["fighter_b"]))))


def merge(have_fighters: List[Dict[str, str]], have_fights: List[Dict[str, str]],
          new_fighters: Iterable[Dict[str, str]], new_fights: Iterable[Dict[str, str]]):
    """Existing rows stay as they are; bouts after the last one we have are added (with their fighters).

    Only bouts after our last date: on older cards the two scrapes spell a few names differently
    (12 of ~8,800 overlapping bouts), and adding those would count the same fight twice."""
    keys = {_key(f) for f in have_fights}
    last = max((f["date"] for f in have_fights), default="")
    added = [f for f in new_fights if f["date"] > last and _key(f) not in keys and f.get("a_sig_attempted") != ""]
    urls = {f.get("url") for f in have_fighters}
    fighters = list(have_fighters) + [f for f in new_fighters if f["url"] not in urls]
    fights = sorted(list(have_fights) + added, key=lambda x: x["date"])
    return fighters, fights, added
