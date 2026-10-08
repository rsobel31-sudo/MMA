"""Our own rating of the regional scene: Glicko over every fight in the regional crawl (data/regional/).

The crawl holds the Sherdog record of every prospect candidate, of the 2019/2021 backtest cohorts, and of
everyone they fought. Each bout is seen once (from either side), dated, and replayed in order, so a fighter's
rating is earned from who they beat and lost to, weighted by how good those opponents were at the time,
and a result counts the day it happens (no waiting on anyone else's update).

`backtest()` replays the ratings as they stood on the Fight Matrix snapshot dates and asks the same question
the Fight Matrix test asked: of the prospects on that date, who went on to win in a major promotion?
"""

from __future__ import annotations

import gzip
import json
import math
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

DIR = Path("data/regional")
Q = math.log(10) / 400
RD0, RD_MIN = 350.0, 40.0
C2 = (RD0 ** 2 - 50.0 ** 2) / 60  # RD drifts from 50 back to 350 over five idle years (per 30 days)


def load_records(d: Path = DIR) -> Dict[str, dict]:
    recs: Dict[str, dict] = {}
    for p in sorted(d.glob("pages-*.jsonl.gz")):
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    recs[r["url"]] = r
    if (d / "open.jsonl").exists():
        for line in (d / "open.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                recs[r["url"]] = r
    return recs


@dataclass(order=True)
class Bout:
    day: date
    a: str = field(compare=False)
    b: str = field(compare=False)
    score_a: float = field(compare=False)  # 1 win, 0 loss, 0.5 draw (from a's side)
    method: str = field(compare=False)
    event: str = field(compare=False)


def bouts(recs: Dict[str, dict]) -> List[Bout]:
    """Every bout once, from whichever side we hold; no contests and unlinked opponents left out."""
    seen, out = set(), []
    for url, r in recs.items():
        for x in r["bouts"]:
            u, res = x.get("u"), x.get("r")
            if not u or res not in ("win", "loss", "draw"):
                continue
            try:
                d = date.fromisoformat(x["d"])
            except ValueError:
                continue
            key = (d, min(url, u), max(url, u))
            if key in seen:
                continue
            seen.add(key)
            out.append(Bout(d, url, u, {"win": 1.0, "loss": 0.0, "draw": 0.5}[res], x.get("m", ""), x.get("e", "")))
    out.sort()
    return out


def main_bouts(d: Path = Path("data/sherdog")) -> List[Bout]:
    """The main dataset's bouts (about 22,000 fighters' full Sherdog records), keyed by Sherdog link where the
    name is unique, so the regional graph is anchored to the major-promotion end."""
    import csv

    url_of: Dict[str, str] = {}
    dup = set()
    for r in csv.DictReader((d / "fighters.csv").open(encoding="utf-8")):
        if r.get("url"):
            if r["name"] in url_of and url_of[r["name"]] != r["url"]:
                dup.add(r["name"])
            url_of[r["name"]] = r["url"]
    out = []
    for r in csv.DictReader((d / "fights.csv").open(encoding="utf-8")):
        a, b = url_of.get(r["fighter_a"]), url_of.get(r["fighter_b"])
        if not a or not b or r["fighter_a"] in dup or r["fighter_b"] in dup:
            continue
        w = r.get("winner") or ""
        if w == r["fighter_a"]:
            sc = 1.0
        elif w == r["fighter_b"]:
            sc = 0.0
        elif r.get("method", "").upper() in ("DRAW",):
            sc = 0.5
        else:
            continue  # no contest, or no result
        try:
            out.append(Bout(date.fromisoformat(r["date"][:10]), a, b, sc, r.get("method", ""), r.get("event", "")))
        except ValueError:
            continue
    return out


def all_bouts(recs: Dict[str, dict], with_main: bool = True) -> List[Bout]:
    """Regional crawl plus the main dataset, each bout once."""
    bs = bouts(recs)
    if with_main:
        seen = {(b.day, min(b.a, b.b), max(b.a, b.b)) for b in bs}
        for b in main_bouts():
            k = (b.day, min(b.a, b.b), max(b.a, b.b))
            if k not in seen:
                seen.add(k)
                bs.append(b)
        bs.sort()
    return bs


@dataclass
class Player:
    r: float = 1500.0
    rd: float = RD0
    last: Optional[date] = None
    n: int = 0


def _g(rd: float) -> float:
    return 1 / math.sqrt(1 + 3 * Q * Q * rd * rd / math.pi ** 2)


def _expected(r: float, rj: float, rdj: float) -> float:
    return 1 / (1 + 10 ** (-_g(rdj) * (r - rj) / 400))


def _age(p: Player, d: date, cap: float = RD0) -> float:
    if p.last is None:
        return p.rd
    months = max(0.0, (d - p.last).days / 30.0)
    return min(cap, math.sqrt(p.rd ** 2 + C2 * months))


def replay(bs: Iterable[Bout], until: Optional[date] = None, finish_weight: float = 1.0, rd0: float = RD0) -> Dict[str, Player]:
    """Glicko-1, one bout per rating period, both sides updated from their pre-fight values.
    finish_weight < 1 scores a decision win as that share of a full win (0.9 -> a decision is 0.9/0.1).
    rd0 < 350 is a firmer prior: a short record moves the rating less (shrinks 3-0 and 5-0 records toward 1500)."""
    ps: Dict[str, Player] = {}
    for b in bs:
        if until and b.day >= until:
            break
        if b.a == b.b:
            continue
        pa, pb = ps.setdefault(b.a, Player(rd=rd0)), ps.setdefault(b.b, Player(rd=rd0))
        rda, rdb = _age(pa, b.day, rd0), _age(pb, b.day, rd0)
        s = b.score_a
        if s in (0.0, 1.0) and finish_weight < 1 and b.method.upper().startswith("DEC"):
            s = finish_weight if s == 1.0 else 1 - finish_weight
        new = []
        for me, rd_me, op, rd_op, sc in ((pa, rda, pb, rdb, s), (pb, rdb, pa, rda, 1 - s)):
            e = _expected(me.r, op.r, rd_op)
            g = _g(rd_op)
            d2 = 1 / (Q * Q * g * g * e * (1 - e))
            denom = 1 / rd_me ** 2 + 1 / d2
            new.append((me.r + Q / denom * g * (sc - e), max(RD_MIN, math.sqrt(1 / denom))))
        for me, (r, rd) in zip((pa, pb), new):
            me.r, me.rd, me.last, me.n = r, rd, b.day, me.n + 1
    return ps


# ------------------------------------------------------------------ backtest
def backtest(out: Optional[Path] = None, finish_weights=(1.0, 0.9), with_main: bool = True, k_rd: float = 0.0, rd0: float = RD0, log=print) -> dict:
    """Our rating vs Fight Matrix's on the 2019/2021 cohorts, scored the way the Fight Matrix test was."""
    from . import prospects_backtest as PB

    recs = load_records()
    bs = all_bouts(recs, with_main)
    profiles = {}
    for src in (Path("data/fightmatrix/profiles.jsonl"), Path("data/prospects/backtest/profiles.jsonl")):
        if src.exists():
            for line in src.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    profiles[r["url"]] = r
    report = {"records": len(recs), "bouts": len(bs)}
    for snap in sorted(Path("data/prospects/backtest").glob("snapshot_*.jsonl")):
        when = date.fromisoformat(snap.stem.split("_")[1])
        rows = [json.loads(l) for l in snap.read_text(encoding="utf-8").splitlines() if l.strip()]
        pool = PB.snapshot_pool(rows, profiles, when)
        cur = {k: v / 0.9 for k, v in PB.CURRENT.items()}
        res = {"prospects": len(pool), "made_it": sum(p["made_it"] for p in pool),
               "fm": {"auc_rating": round(PB.auc(pool, lambda p: p["rating"]), 3),
                      "auc_score": round(PB.auc(pool, lambda p: PB.score(p, cur)), 3),
                      "top50_score": round(PB.top_rate(pool, lambda p: PB.score(p, cur), 50), 3)}}
        for fw in finish_weights:
            ours = replay(bs, until=when, finish_weight=fw, rd0=rd0)
            covered = []
            for p in pool:
                su = (profiles.get(p["url"]) or {}).get("sherdog_url")
                pl = ours.get(su) if su else None
                p["ours"] = pl.r - k_rd * pl.rd if pl else None
                p["ours_low"] = pl.r - pl.rd if pl else None
                if pl:
                    covered.append(p)
            # The same score with our rating's within-division percentile in place of Fight Matrix's.
            swapped = [dict(p, c=dict(p["c"])) for p in covered]
            by_div: Dict[str, List[dict]] = {}
            for p in swapped:
                by_div.setdefault(p["division"], []).append(p)
            for ps_ in by_div.values():
                xs = sorted(p["ours"] for p in ps_)
                for p in ps_:
                    p["c"]["rating"] = 0.5 if len(xs) < 2 else sum(x < p["ours"] for x in xs) / (len(xs) - 1)
            blend = [dict(p, c=dict(p["c"], rating=(p["c"]["rating"] + q["c"]["rating"]) / 2)) for p, q in zip(covered, swapped)]
            res[f"ours_fw{fw}"] = {
                "covered": len(covered),
                "auc_rating": round(PB.auc(covered, lambda p: p["ours"]), 3),
                "auc_rating_low": round(PB.auc(covered, lambda p: p["ours_low"]), 3),
                "fm_auc_rating_same_fighters": round(PB.auc(covered, lambda p: p["rating"]), 3),
                "auc_score": round(PB.auc(swapped, lambda p: PB.score(p, cur)), 3),
                "auc_score_blend": round(PB.auc(blend, lambda p: PB.score(p, cur)), 3),
                "fm_auc_score_same_fighters": round(PB.auc(covered, lambda p: PB.score(p, cur)), 3),
                "top50_score": round(PB.top_rate(swapped, lambda p: PB.score(p, cur), 50), 3),
                "top50_blend": round(PB.top_rate(blend, lambda p: PB.score(p, cur), 50), 3),
                "fm_top50_same_fighters": round(PB.top_rate(covered, lambda p: PB.score(p, cur), 50), 3),
            }
        report[when.isoformat()] = res
        log(f"{when}: {json.dumps(res)}")
    if out:
        out.write_text(json.dumps(report, indent=1))
    return report


# ------------------------------------------------------- strength of schedule after signing
def pre_fight_ratings(bs: List[Bout]) -> List[Tuple[Bout, float, float, int, int]]:
    """Each bout with both fighters' ratings going in (a's, b's) and how many rated bouts each had."""
    ps: Dict[str, Player] = {}
    out = []
    for b in bs:
        if b.a == b.b:
            continue
        pa, pb = ps.setdefault(b.a, Player()), ps.setdefault(b.b, Player())
        out.append((b, pa.r, pb.r, pa.n, pb.n))
        replay_one(ps, b)
    return out


def replay_one(ps: Dict[str, Player], b: Bout) -> None:
    pa, pb = ps.setdefault(b.a, Player()), ps.setdefault(b.b, Player())
    rda, rdb = _age(pa, b.day), _age(pb, b.day)
    new = []
    for me, rd_me, op, rd_op, sc in ((pa, rda, pb, rdb, b.score_a), (pb, rdb, pa, rda, 1 - b.score_a)):
        e = _expected(me.r, op.r, rd_op)
        g = _g(rd_op)
        denom = 1 / rd_me ** 2 + Q * Q * g * g * e * (1 - e)
        new.append((me.r + Q / denom * g * (sc - e), max(RD_MIN, math.sqrt(1 / denom))))
    for me, (r, rd) in zip((pa, pb), new):
        me.r, me.rd, me.last, me.n = r, rd, b.day, me.n + 1


def schedules(first: int = 3, later: int = 6, since: date = date(2008, 1, 1), min_later: int = 1) -> dict:
    """For everyone who reached a major promotion: the opponents in their first `first` major bouts (rating going
    in), and how they did in the `later` major bouts after that. Does a soft start predict struggles?
    min_later > 1 keeps only fighters who stayed around, which favours the ones who kept winning (survivorship);
    "next_bout" (the first bout after the start, whoever had one) is free of that."""
    from . import prospects as PR

    names = {}
    for r in load_records().values():
        names[r["url"]] = r["name"]
    import csv

    for r in csv.DictReader(Path("data/sherdog/fighters.csv").open(encoding="utf-8")):
        if r.get("url"):
            names.setdefault(r["url"], r["name"])
    rows = pre_fight_ratings(all_bouts(load_records()))
    major: Dict[str, List[Tuple[date, float, float, str]]] = {}  # fighter -> (day, opp rating, result, event)
    for b, ra, rb, na, nb in rows:
        if not PR.is_major(b.event) or not na or not nb:  # an opponent with no rated bouts is a default 1500, not a known level
            continue
        ea = 1 / (1 + 10 ** (-(ra - rb) / 400))
        major.setdefault(b.a, []).append((b.day, rb, b.score_a, b.event, ea, ra))
        major.setdefault(b.b, []).append((b.day, ra, 1 - b.score_a, b.event, 1 - ea, rb))
    starts = []
    for f, xs in major.items():
        xs.sort()
        if xs[0][0] < since or len(xs) < first:
            continue
        early = xs[:first]
        starts.append({"url": f, "name": names.get(f, f), "debut": xs[0][0].isoformat(), "early_opp": sum(x[1] for x in early) / first,
                       "early_wins": sum(x[2] for x in early), "later": [x[2] for x in xs[first:first + later]],
                       "later_expected": [x[4] for x in xs[first:first + later]], "later_opp": [x[1] for x in xs[first:first + later]],
                       "rating_after_early": xs[first][5] if len(xs) > first else None,
                       "early": [(x[0].isoformat(), round(x[1]), x[2], x[3]) for x in early]})
    opps = sorted(s["early_opp"] for s in starts)
    q = lambda p: opps[int(p * (len(opps) - 1))]
    lo, hi = q(1 / 3), q(2 / 3)
    out = {"fighters": len(starts), "soft_below": round(lo), "tough_above": round(hi), "groups": {}}
    for label, keep in (("soft", lambda s: s["early_opp"] <= lo), ("middle", lambda s: lo < s["early_opp"] < hi), ("tough", lambda s: s["early_opp"] >= hi)):
        for rec in ("3-0", "2-1"):
            w = int(rec[0])
            g = [s for s in starts if keep(s) and s["early_wins"] == w and len(s["later"]) >= min_later]
            later = [x for s in g for x in s["later"]]
            exp = [x for s in g for x in s["later_expected"]]
            lopp = [x for s in g for x in s["later_opp"]]
            out["groups"][f"{label} {rec}"] = {"fighters": len(g), "later_bouts": len(later),
                                               "later_win_rate": round(sum(later) / len(later), 3) if later else None,
                                               "expected": round(sum(exp) / len(exp), 3) if exp else None,
                                               "vs_expected": round((sum(later) - sum(exp)) / len(later), 3) if later else None,
                                               "later_opp": round(sum(lopp) / len(lopp)) if lopp else None,
                                               "next_bout_win_rate": round(sum(s["later"][0] for s in g) / len(g), 3) if g else None,
                                               "next_bout_expected": round(sum(s["later_expected"][0] for s in g) / len(g), 3) if g else None,
                                               "z": round((sum(later) - sum(exp)) / math.sqrt(sum(e * (1 - e) for e in exp)), 2) if exp else None}
    out["starts"] = starts
    return out


# ------------------------------------------------------- today's prospects: ours vs Fight Matrix
def compare_current(prospects_path: Path = Path("app/prospects.json"), top: int = 15, k_rd: float = 1.0, rd0: float = RD0) -> dict:
    """Each listed prospect's within-division percentile on our rating and on Fight Matrix's (the score's rating
    component), and the biggest disagreements both ways."""
    recs = load_records()
    ps = replay(all_bouts(recs), rd0=rd0)
    P = json.loads(prospects_path.read_text())["prospects"]
    rows = []
    for p in P:
        pl = ps.get(p.get("sherdog_url") or "")
        if pl:
            rows.append({"name": p["name"], "division": p["division"], "rank": p["p4p_rank"], "record": f"{p['wins']}-{p['losses']}",
                         "fm_pct": p["components"]["rating"], "ours": round(pl.r - k_rd * pl.rd), "r": round(pl.r), "rd": round(pl.rd), "bouts_rated": pl.n})
    by: Dict[str, List[dict]] = {}
    for r in rows:
        by.setdefault(r["division"], []).append(r)
    for g in by.values():
        xs = sorted(r["ours"] for r in g)
        for r in g:
            r["ours_pct"] = 0.5 if len(xs) < 2 else round(sum(x < r["ours"] for x in xs) / (len(xs) - 1), 3)
            r["gap"] = round(r["ours_pct"] - r["fm_pct"], 3)
    n = len(rows)
    import statistics as st

    corr = None
    if n > 2:
        a, b = [r["ours_pct"] for r in rows], [r["fm_pct"] for r in rows]
        ma, mb = st.mean(a), st.mean(b)
        corr = round(sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)), 3)
    rows.sort(key=lambda r: r["gap"])
    return {"listed": len(P), "rated": n, "correlation": corr, "ours_higher": rows[::-1][:top], "fm_higher": rows[:top]}
