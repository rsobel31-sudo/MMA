"""Outside ratings as point-in-time evidence (Fight Matrix).

Fight Matrix profiles list both fighters' ratings before and after every
bout in three systems (Elo K-170, a modified Elo, Glicko-1). A fighter's
rating on a date is their post-fight rating from their last bout before that
date, so a backtest never sees the future. Opponents' ratings come from the
profiles that list them, so an uncrawled fighter is covered wherever they met
a crawled one.

These ratings are Fight Matrix's own opinion, not facts to verify; they enter
the model as one feature next to ours, and the backtest decides their weight.
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .sources.wikipedia import match_key
from .verify import load_jsonl

SYSTEM = "glicko"


class ExternalRatings:
    def __init__(self, profiles: Iterable[Dict], names: Iterable[str], url_to_name: Optional[Dict[str, str]] = None,
                 system: str = SYSTEM) -> None:
        by_key: Dict[str, List[str]] = defaultdict(list)
        for n in names:
            by_key[match_key(n)].append(n)
        url_to_name = {k.rstrip("/").lower(): v for k, v in (url_to_name or {}).items()}

        def resolve(fm_name: str, sherdog_url: str = "") -> Optional[str]:
            if sherdog_url and sherdog_url.rstrip("/").lower() in url_to_name:
                return url_to_name[sherdog_url.rstrip("/").lower()]
            cands = by_key.get(match_key(fm_name), [])
            return cands[0] if len(cands) == 1 else None  # ambiguous names are skipped

        points: Dict[str, Dict[date, float]] = defaultdict(dict)
        for prof in profiles:
            me = resolve(prof["name"], prof.get("sherdog_url", ""))
            for b in prof.get("bouts", []):
                d = date.fromisoformat(b["date"]) if isinstance(b["date"], str) else b["date"]
                mine, theirs = (b.get("ratings") or {}).get(system), (b.get("opp_ratings") or {}).get(system)
                if me and mine:
                    points[me][d] = float(mine[1])
                opp = resolve(b["opponent"])
                if opp and theirs:
                    points[opp].setdefault(d, float(theirs[1]))
        self._dates: Dict[str, List[date]] = {}
        self._values: Dict[str, List[float]] = {}
        for n, pts in points.items():
            ds = sorted(pts)
            self._dates[n], self._values[n] = ds, [pts[d] for d in ds]

    def before(self, name: str, when: date) -> Optional[float]:
        """Rating after the fighter's last bout strictly before ``when`` (None if unknown)."""
        ds = self._dates.get(name)
        if not ds:
            return None
        i = bisect.bisect_left(ds, when)
        return self._values[name][i - 1] if i else None

    def __len__(self) -> int:
        return len(self._dates)

    @classmethod
    def load(cls, path: Path, names: Iterable[str], url_to_name: Optional[Dict[str, str]] = None) -> "ExternalRatings":
        return cls(load_jsonl(Path(path)), names, url_to_name)


DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "fightmatrix" / "profiles.jsonl"


def for_dataset(data_dir: Path, bios: Dict, path: Path = DEFAULT_PATH) -> Optional[ExternalRatings]:
    """Fight Matrix ratings linked to a dataset's fighters (by Sherdog URL, else unique name); None if not crawled."""
    import csv

    if not Path(path).exists():
        return None
    urls: Dict[str, str] = {}
    fighters_csv = Path(data_dir) / "fighters.csv"
    if fighters_csv.exists():
        with open(fighters_csv, newline="", encoding="utf-8") as fh:
            urls = {r["url"]: r["name"] for r in csv.DictReader(fh) if r.get("url")}
    return ExternalRatings.load(Path(path), bios.keys(), urls)
