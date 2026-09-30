"""Scouting reads and the pundit ledger: what the numbers can't see, fed into the picks.

A *read* is Claude's judgement on one bout after reading both fighters'
scouting reports, the fight-week news and the pundits: a log-odds nudge on
top of the model, toward one fighter, capped at +/-MAX_READ. It enters every
prediction as its own factor ("scouting read"), on the site and in the
betting sheet, and every read is graded after the fight so its value can be
measured: does model + read beat the model alone?

Read weight: reads count at full size (READ_WEIGHT = 1) for now. Once enough
bouts are graded, `fit_read_weight` estimates the weight that best predicts
results; it's applied only when the sample is large enough (MIN_READS).

The *pundit ledger* records every outlet/author pick we read, grades it, and
compares each pundit with the betting favourite on the same bouts. Pundit
weights stay equal (1.0) until an author has MIN_PUNDIT_PICKS graded picks and
beats (or trails) the favourite baseline by a statistically clear margin;
only then are they up- or down-weighted, or dropped.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

MAX_READ = 0.8
READ_WEIGHT = 1.0
MIN_READS = 150
MIN_PUNDIT_PICKS = 40
READS_DIR = Path("data/scouting/reads")
PUNDITS = Path("data/scouting/pundits.jsonl")


def slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def pair_id(a: str, b: str) -> str:
    return "read--" + "--".join(sorted((slug(a), slug(b))))


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Reads:
    """All reads, keyed by bout (unordered pair of fighter names)."""

    def __init__(self, reads: Iterable[Dict[str, object]] = ()) -> None:
        self.by_pair: Dict[str, Dict[str, object]] = {}
        for r in reads:
            self.by_pair[pair_id(str(r["a"]), str(r["b"]))] = r

    @classmethod
    def load(cls, folder: Path = READS_DIR) -> "Reads":
        rows: List[Dict[str, object]] = []
        for p in sorted(Path(folder).glob("*.json")) if Path(folder).exists() else []:
            rows += json.loads(p.read_text()).get("bouts", [])
        return cls(rows)

    def get(self, a: str, b: str) -> Optional[Dict[str, object]]:
        return self.by_pair.get(pair_id(a, b))

    def logit(self, a: str, b: str, weight: float = READ_WEIGHT) -> float:
        """Log-odds toward `a` from the read on this bout (0 without one)."""
        r = self.get(a, b)
        if not r or r.get("logit") is None:
            return 0.0
        x = max(-MAX_READ, min(MAX_READ, float(r["logit"]))) * weight
        return x if r.get("favours") == a else -x if r.get("favours") == b else 0.0


def check_read(r: Dict[str, object]) -> None:
    for k in ("a", "b", "favours", "logit", "confidence", "reasoning"):
        if k not in r:
            raise ValueError(f"read {r.get('a')} vs {r.get('b')}: missing {k}")
    if r["logit"] is not None:
        if not 0 <= float(r["logit"]) <= MAX_READ:
            raise ValueError(f"read {r['a']} vs {r['b']}: logit must be 0..{MAX_READ} toward `favours`")
        if r["favours"] not in (r["a"], r["b"]) and float(r["logit"]) > 0:
            raise ValueError(f"read {r['a']} vs {r['b']}: favours must name one of the fighters")


# ------------------------------------------------------------------ grading
def _ll(p: float, y: int) -> float:
    p = min(1 - 1e-9, max(1e-9, p))
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def grade_reads(rows: List[Dict[str, object]]) -> Dict[str, object]:
    """Graded reads carry p_model (toward a), logit (signed toward a) and y (1 if a won)."""
    g = [r for r in rows if r.get("y") in (0, 1) and r.get("p_model") is not None]
    if not g:
        return {"n": 0}
    sig = lambda z: 1 / (1 + math.exp(-z))  # noqa: E731
    lg = lambda p: math.log(p / (1 - p))  # noqa: E731
    base = sum(_ll(r["p_model"], r["y"]) for r in g) / len(g)
    withr = sum(_ll(sig(lg(r["p_model"]) + r["signed_logit"]), r["y"]) for r in g) / len(g)
    moved = [r for r in g if abs(r["signed_logit"]) > 1e-9]
    right = sum((r["signed_logit"] > 0) == bool(r["y"]) for r in moved)
    return {"n": len(g), "log_loss_model": round(base, 4), "log_loss_with_reads": round(withr, 4),
            "moved": len(moved), "moved_right": right, "weight_ready": len(g) >= MIN_READS}


def fit_read_weight(rows: List[Dict[str, object]]) -> Optional[float]:
    """Best multiplier on the reads (1-D search on log loss), only with enough graded bouts."""
    g = [r for r in rows if r.get("y") in (0, 1) and r.get("p_model") is not None]
    if len(g) < MIN_READS:
        return None
    sig = lambda z: 1 / (1 + math.exp(-z))  # noqa: E731
    lg = lambda p: math.log(p / (1 - p))  # noqa: E731
    best = min((sum(_ll(sig(lg(r["p_model"]) + w * r["signed_logit"]), r["y"]) for r in g), w) for w in [i / 20 for i in range(0, 41)])
    return best[1]


class Pundits:
    """data/scouting/pundits.jsonl: every pick we read, graded after the fight."""

    def __init__(self, path: Path = PUNDITS) -> None:
        self.path = Path(path)
        self.rows: List[Dict[str, object]] = []
        if self.path.exists():
            self.rows = [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]

    def add(self, row: Dict[str, object]) -> bool:
        key = (row["event"], pair_id(row["a"], row["b"]), row["outlet"], row.get("author", ""))
        for r in self.rows:
            if (r["event"], pair_id(r["a"], r["b"]), r["outlet"], r.get("author", "")) == key:
                r.update({k: v for k, v in row.items() if k not in ("grade",)})
                return False
        self.rows.append(dict(row, recorded=_now()))
        return True

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in self.rows))

    def scoreboard(self) -> List[Dict[str, object]]:
        """Per author: graded picks, accuracy, and a test against the market.

        Each pick carries the market's no-vig probability for the fighter picked
        (p_market). A pundit with no edge wins about sum(p_market) picks;
        z = (won - expected) / sqrt(sum p(1 - p)) says how far above or below the
        market they are, in standard errors.
        """
        by: Dict[Tuple[str, str], List[Dict[str, object]]] = {}
        for r in self.rows:
            if r.get("grade") in ("won", "lost"):
                by.setdefault((r["outlet"], r.get("author") or "(staff)"), []).append(r)
        out = []
        for (outlet, author), rs in by.items():
            n = len(rs)
            won = sum(r["grade"] == "won" for r in rs)
            priced = [r for r in rs if r.get("p_market") is not None]
            exp = sum(r["p_market"] for r in priced)
            var = sum(r["p_market"] * (1 - r["p_market"]) for r in priced)
            won_p = sum(r["grade"] == "won" for r in priced)
            z = (won_p - exp) / math.sqrt(var) if var > 0 else 0.0
            underdogs = [r for r in priced if r["p_market"] < 0.5]
            out.append({"outlet": outlet, "author": author, "picks": n, "correct": won, "accuracy": round(won / n, 3),
                        "expected": round(exp / len(priced), 3) if priced else None,
                        "underdog_picks": len(underdogs), "underdog_won": sum(r["grade"] == "won" for r in underdogs),
                        "z": round(z, 2), "weight": pundit_weight(len(priced), z)})
        return sorted(out, key=lambda s: (-s["picks"], s["outlet"]))


def pundit_weight(n: int, z: float) -> float:
    """Equal weight until the record is long and the edge is clear; then scale, or drop a clear negative."""
    if n < MIN_PUNDIT_PICKS or abs(z) < 1.96:
        return 1.0
    if z <= -1.96:
        return 0.0 if z <= -2.58 else 0.5
    return 1.5 if z < 2.58 else 2.0
