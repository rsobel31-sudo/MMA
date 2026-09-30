"""Weight classes in pounds, for comparing fighters' sizes.

Most bouts are within one division, so size only matters when fighters
from different divisions meet (a champion moving up, a superfight, a catch
weight). A fighter's fighting weight is the typical class of their recent
bouts; the size feature compares the two fighters' fighting weights.
"""

from __future__ import annotations

import re
from typing import Optional

# Upper limit of each division; heavyweight uses a typical fighting weight
# rather than its 265 lb limit, since most heavyweights come in well under it.
_UFC = [
    ("super heavyweight", 280.0),
    ("light heavyweight", 205.0),
    ("heavyweight", 250.0),
    ("middleweight", 185.0),
    ("welterweight", 170.0),
    ("lightweight", 155.0),
    ("featherweight", 145.0),
    ("bantamweight", 135.0),
    ("flyweight", 125.0),
    ("strawweight", 115.0),
    ("atomweight", 105.0),
]
# Promotions whose division names meant different weights.
_SPECIAL = [
    ("pride middleweight", 205.0),
    ("pride welterweight", 183.0),
    ("pride lightweight", 160.0),
    ("pride heavyweight", 250.0),
    ("dream lightweight", 154.0),
    ("dream featherweight", 139.0),
    ("dream welterweight", 168.0),
]


def division_lbs(name: Optional[str]) -> Optional[float]:
    """Pounds for a weight-class name ('Women's Flyweight' -> 125); None for catch/open weights."""
    if not name:
        return None
    s = name.strip().lower()
    m = re.search(r"(\d{3})\s*lbs?", s)
    if m:
        return float(m.group(1))
    for key, lbs in _SPECIAL:
        if key in s:
            return lbs
    for key, lbs in _UFC:
        if key in s:
            return lbs
    return None
