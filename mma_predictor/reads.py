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
                # Archive picks (scout history) are graded on import: a re-parse may correct pick and grade alike.
                r.update({k: v for k, v in row.items() if k != "grade" or "published" in row})
                return False
        self.rows.append(dict(row, recorded=_now()))
        return True

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in self.rows))

    def people(self) -> Dict[str, str]:
        """Each written author name -> one canonical name per person: accents, case and small spelling slips
        ('Frazer Kron' / 'Frazer Krohn', 'Beaupré' / 'Beaupre') are the same person; the most used spelling wins."""
        from collections import Counter
        from difflib import SequenceMatcher

        counts = Counter(str(r.get("author") or "") for r in self.rows if r.get("author"))
        fold = lambda n: re.sub(r"[^a-z ]", "", unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode().lower()).split()  # noqa: E731
        canon: Dict[str, str] = {}
        heads: List[str] = []
        for name, _ in counts.most_common():
            f = fold(name)
            for h in heads:
                g = fold(h)
                if f and g and f[0] == g[0] and SequenceMatcher(None, " ".join(f[1:]), " ".join(g[1:])).ratio() >= 0.85:
                    canon[name] = h
                    break
            else:
                heads.append(name)
                canon[name] = name
        return canon

    def scoreboard(self, today: Optional[str] = None) -> List[Dict[str, object]]:
        """Per picker (a person, across outlets): graded picks, accuracy, and a test against the market.

        Each pick carries the market's no-vig probability for the fighter picked (p_market). A picker with
        no edge wins about sum(p_market) picks; z = (won - expected) / sqrt(sum p(1 - p)) says how far above
        or below the market they are, in standard errors. Ranking is by z, so a long record of beating the
        favourite counts and a famous name or a run of chalk picks does not.
        """
        canon = self.people()
        today = today or datetime.now(timezone.utc).date().isoformat()
        year_ago = f"{int(today[:4]) - 1}{today[4:10]}"
        by: Dict[str, List[Dict[str, object]]] = {}
        for r in self.rows:
            if r.get("grade") in ("won", "lost") and r.get("author"):
                by.setdefault(canon.get(str(r["author"]), str(r["author"])), []).append(r)

        def test(rs: List[Dict[str, object]]) -> Tuple[float, float, int]:
            priced = [r for r in rs if r.get("p_market") is not None]
            exp = sum(float(r["p_market"]) for r in priced)
            var = sum(float(r["p_market"]) * (1 - float(r["p_market"])) for r in priced)
            won = sum(r["grade"] == "won" for r in priced)
            return ((won - exp) / math.sqrt(var) if var > 0 else 0.0), (exp / len(priced) if priced else 0.0), len(priced)

        out = []
        for author, rs in by.items():
            n = len(rs)
            won = sum(r["grade"] == "won" for r in rs)
            z, expected, n_priced = test(rs)
            priced = [r for r in rs if r.get("p_market") is not None]
            dogs = [r for r in priced if float(r["p_market"]) < 0.5]
            meth = [r for r in rs if r.get("method_correct") is not None]
            recent = [r for r in rs if str(r.get("date", "")) >= year_ago]
            rz, _, rn = test(recent)
            outlets = [o for o, _ in __import__("collections").Counter(str(r["outlet"]) for r in rs).most_common()]
            out.append({"author": author, "outlet": outlets[0], "outlets": outlets, "picks": n, "correct": won,
                        "accuracy": round(won / n, 3), "expected": round(expected, 3) if n_priced else None,
                        "edge": round(won / n - expected, 3) if n_priced else None,
                        "underdog_picks": len(dogs), "underdog_won": sum(r["grade"] == "won" for r in dogs),
                        "methods": len(meth), "method_hits": sum(bool(r["method_correct"]) for r in meth),
                        "first": min(str(r["date"]) for r in rs), "last": max(str(r["date"]) for r in rs),
                        "recent": {"picks": rn, "z": round(rz, 2)},
                        "z": round(z, 2), "weight": pundit_weight(n_priced, z)})
        return sorted(out, key=lambda s: (-(s["picks"] >= MIN_PUNDIT_PICKS), -s["z"], -s["picks"]))


def pundit_weight(n: int, z: float) -> float:
    """Equal weight until the record is long and the edge is clear; then scale, or drop a clear negative."""
    if n < MIN_PUNDIT_PICKS or abs(z) < 1.96:
        return 1.0
    if z <= -1.96:
        return 0.0 if z <= -2.58 else 0.5
    return 1.5 if z < 2.58 else 2.0


def pundit_consensus(picks: Iterable[Dict[str, object]], board: Iterable[Dict[str, object]]) -> Optional[Dict[str, object]]:
    """Fight-week pundit picks on one bout, each counted by its picker's Fight Track Record weight
    (1.0 until the record is long and clear). Returns the leading fighter, their weighted share and the
    picks behind it, or None when nobody has picked the bout."""
    def fold(n: object) -> str:
        return re.sub(r"[^a-z ]", "", unicodedata.normalize("NFKD", str(n or "")).encode("ascii", "ignore").decode().lower()).strip()

    weights = {fold(b["author"]): float(b["weight"]) for b in board}
    tally: Dict[str, float] = {}
    rows = list(picks)
    for r in rows:
        tally[str(r["pick"])] = tally.get(str(r["pick"]), 0.0) + weights.get(fold(r.get("author")), 1.0)
    total = sum(tally.values())
    if not total:
        return None
    pick, w = max(tally.items(), key=lambda kv: kv[1])
    return {"pick": pick, "share": round(w / total, 3), "n": len(rows), "raw_share": round(sum(str(r["pick"]) == pick for r in rows) / len(rows), 3)}
