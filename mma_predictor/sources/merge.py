"""Merge several datasets into one fight table.

Typical use: a career dataset from Sherdog/Tapology (every pro bout, no
stats) plus a stats-rich dataset (e.g. UFC bouts with strike/takedown
counts). The same bout is matched across sources on both fighters' names
and a date within ``date_tolerance_days`` (sites sometimes disagree by a day
because of time zones). Where both have it, the row carrying per-corner stats
wins and missing fields are filled from the other.
"""

from __future__ import annotations

import csv
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ..data import normalise_name, parse_date
from .common import FIGHTER_HEADER, write_dataset


def _read(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _has_stats(row: Dict[str, str]) -> bool:
    return any((row.get(k) or "").strip() for k in ("a_sig_landed", "a_sig_attempted", "b_sig_landed"))


def _swap(row: Dict[str, str]) -> Dict[str, str]:
    out = dict(row)
    out["fighter_a"], out["fighter_b"] = row["fighter_b"], row["fighter_a"]
    for k, v in row.items():
        if k.startswith("a_"):
            out["b_" + k[2:]] = v
        elif k.startswith("b_"):
            out["a_" + k[2:]] = v
    return out


def merge_datasets(dirs: Sequence[Path], out_dir: Path, date_tolerance_days: int = 1, aliases: Optional[Dict[str, str]] = None) -> Tuple[int, int]:
    """Merge ``dirs`` (earlier = higher priority for bio fields). Returns (fighters, fights)."""
    aliases = {normalise_name(k): v for k, v in (aliases or {}).items()}

    def canon(name: str) -> str:
        return aliases.get(normalise_name(name), name.strip())

    fighters: Dict[str, Dict[str, str]] = {}
    by_pair: Dict[frozenset, List[Dict[str, str]]] = {}
    for d in dirs:
        d = Path(d)
        for row in _read(d / "fighters.csv"):
            row["name"] = canon(row["name"])
            key = normalise_name(row["name"])
            existing = fighters.get(key)
            if existing is None:
                fighters[key] = {h: row.get(h, "") for h in FIGHTER_HEADER}
            else:
                for h in FIGHTER_HEADER:
                    if not (existing.get(h) or "").strip() and (row.get(h) or "").strip():
                        existing[h] = row[h]
        for row in _read(d / "fights.csv"):
            row["fighter_a"], row["fighter_b"] = canon(row["fighter_a"]), canon(row["fighter_b"])
            if row.get("winner") and row["winner"].lower() not in ("draw", "nc"):
                row["winner"] = canon(row["winner"])
            pair = frozenset((normalise_name(row["fighter_a"]), normalise_name(row["fighter_b"])))
            when = parse_date(row["date"])
            bucket = by_pair.setdefault(pair, [])
            match = next(
                (r for r in bucket if abs(parse_date(r["date"]) - when) <= timedelta(days=date_tolerance_days)),
                None,
            )
            if match is None:
                bucket.append(row)
                continue
            if normalise_name(row["fighter_a"]) != normalise_name(match["fighter_a"]):
                row = _swap(row)
            primary, secondary = (row, match) if _has_stats(row) and not _has_stats(match) else (match, row)
            merged = dict(primary)
            for k, v in secondary.items():
                if not (merged.get(k) or "").strip() and (v or "").strip():
                    merged[k] = v
            bucket[bucket.index(match)] = merged

    for rows in by_pair.values():
        for r in rows:
            for n in (r["fighter_a"], r["fighter_b"]):
                fighters.setdefault(normalise_name(n), {h: "" for h in FIGHTER_HEADER} | {"name": n, "prior_wins": "0", "prior_losses": "0"})
    fights = sorted((r for rows in by_pair.values() for r in rows), key=lambda r: r["date"])
    write_dataset(out_dir, list(fighters.values()), fights)
    return len(fighters), len(fights)
