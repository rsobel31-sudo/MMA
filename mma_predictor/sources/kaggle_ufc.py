"""The "UFC Datasets 1994-2025" Kaggle dataset (neelagiriaditya/ufc-datasets-1994-2025).

A scrape of UFCStats, the UFC's official statistics: every UFC bout with
per-corner knockdowns, significant strikes landed/attempted, takedowns,
submission attempts, control time and ground strikes. It fills the per-fight
stats that Sherdog records lack.

Download (public, no login needed):
    https://www.kaggle.com/api/v1/datasets/download/neelagiriaditya/ufc-datasets-1994-2025
then ``python -m mma_predictor import kaggle --dir <unzipped folder> --out data/ufcstats``.

Only bouts are converted here. Results are checked against Sherdog (and
StatsFight where it has the bout) by ``verify.py`` before the two are merged.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple

DOWNLOAD_URL = "https://www.kaggle.com/api/v1/datasets/download/neelagiriaditya/ufc-datasets-1994-2025"


def _height_cm(raw: str) -> str:
    m = re.match(r"(\d+)'\s*(\d+)", raw or "")
    return f"{(int(m.group(1)) * 12 + int(m.group(2))) * 2.54:.1f}" if m else ""


def _method(row: Dict[str, str]) -> str:
    status, m = row["result_status"], row["method"].strip()
    if status == "draw":
        return "Draw"
    if status == "no_contest" or m == "Overturned":
        return "NC"
    if m in ("Could Not Continue", "Other"):
        return "TKO - " + m  # injury and other stoppages count as TKO
    return m


def _rounds(time_format: str) -> int:
    m = re.match(r"(\d+) Rnd", time_format or "")
    return int(m.group(1)) if m else 1


def _int(raw: str) -> str:
    raw = (raw or "").strip()
    return str(int(float(raw))) if raw not in ("", "--") else ""


def convert(src: Path) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    src = Path(src)
    fighters: Dict[str, Dict[str, str]] = {}
    with open(src / "fighter.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            reach = r.get("reach_inches", "").strip()
            fighters[r["fighter_id"]] = {
                "name": r["fighter_name"].strip(), "dob": r.get("dob", "").strip(), "height_cm": _height_cm(r.get("height", "")),
                "reach_cm": f"{float(reach) * 2.54:.1f}" if reach else "", "stance": r.get("stance", "").strip(),
                "source": "ufcstats", "url": f"http://ufcstats.com/fighter-details/{r['fighter_id']}",
            }
    fights: List[Dict[str, str]] = []
    with open(src / "master.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            a, b = r["r_fighter_name"].strip(), r["b_fighter_name"].strip()
            winner = "draw" if r["result_status"] == "draw" else "nc" if r["result_status"] == "no_contest" else (
                a if r["winner_id"] == r["r_fighter_id"] else b if r["winner_id"] == r["b_fighter_id"] else "nc")
            row = {
                "date": r["event_date"], "event": r["event_name"].strip(), "weight_class": r["weight_class"].strip(),
                "fighter_a": a, "fighter_b": b, "winner": winner, "method": _method(r),
                "round": r["finish_round"], "time": r["finish_time"], "scheduled_rounds": str(_rounds(r["time_format"])),
                "title_fight": r["title_fight"],
            }
            for side, p in (("a", "r"), ("b", "b")):
                row.update({
                    f"{side}_sig_landed": _int(r[f"{p}_total_sig_landed"]), f"{side}_sig_attempted": _int(r[f"{p}_total_sig_atmp"]),
                    f"{side}_td_landed": _int(r[f"{p}_total_td_success"]), f"{side}_td_attempted": _int(r[f"{p}_total_td_atmp"]),
                    f"{side}_sub_attempts": _int(r[f"{p}_total_sub_att"]), f"{side}_knockdowns": _int(r[f"{p}_total_kd"]),
                    f"{side}_ctrl_seconds": _int(r[f"{p}_total_ctrl_seconds"]),
                    f"{side}_ground_landed": _int(r[f"{p}_total_sig_str_landed_ground"]),
                })
            fights.append(row)
    fights.sort(key=lambda x: x["date"])
    return list(fighters.values()), fights
