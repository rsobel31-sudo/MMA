"""Cross-source verification: nothing is used on one source's word alone.

Sources and what each can confirm:

    Sherdog        every pro bout (result, method, round, date), DOB, height
    UFCStats       UFC bouts (via the Kaggle dataset): result + per-fight stats,
                   DOB, height, reach
    StatsFight     recent UFC bouts: result, its own strike/takedown counts,
                   height, reach
    Fight Matrix   results (sourced from Sherdog, so not independent for them)
                   and its own ratings

Rules applied when building the dataset (``attach_stats``):

- A UFCStats bout is used only if Sherdog has the same bout (same two
  fighters within a day) with the same winner. Method or round differences
  are reported; the winner must agree.
- Its stats are attached when StatsFight agrees with them, or when
  StatsFight doesn't cover the bout (older fights) and they pass internal
  checks (landed <= attempted, control time <= fight time). Stats StatsFight
  contradicts (the two disagree on who out-landed whom by a wide margin, or
  on takedowns by 3+ and by more than half) are dropped for that bout.
- A physical attribute (DOB, height, reach) counts as verified when two
  sources agree (DOB exactly, height/reach within 3 cm).
"""

from __future__ import annotations

import dataclasses
import json
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .data import Fight, FighterBio, Method
from .sources.wikipedia import match_key


# ------------------------------------------------------------------ matching
def _tokens(name: str) -> set:
    return set(match_key(name).split())


def name_score(x: str, y: str) -> int:
    """2 = same name (any order/accents), 1 = plausibly the same (shares a surname-length token), 0 = different."""
    if match_key(x) == match_key(y):
        return 2
    tx, ty = _tokens(x), _tokens(y)
    shared = {t for t in tx & ty if len(t) >= 3}
    return 1 if shared and (len(tx) >= 2 and len(ty) >= 2) else 0


@dataclasses.dataclass(frozen=True)
class BoutMatch:
    other: Fight
    base: Optional[Fight]
    swapped: bool = False  # other.fighter_a is base.fighter_b


def match_bouts(base: Iterable[Fight], other: Iterable[Fight], tolerance_days: int = 1) -> List[BoutMatch]:
    """Match each ``other`` bout to a ``base`` bout: same date (+-tolerance), both fighters matching.

    At least one name must match exactly (score 2) and the other plausibly.
    """
    by_date: Dict[date, List[Fight]] = defaultdict(list)
    for f in base:
        by_date[f.date].append(f)
    out: List[BoutMatch] = []
    for o in other:
        best: Tuple[int, Optional[Fight], bool] = (0, None, False)
        for d in range(-tolerance_days, tolerance_days + 1):
            for f in by_date.get(o.date + timedelta(days=d), []):
                for swapped, (x, y) in ((False, (f.fighter_a, f.fighter_b)), (True, (f.fighter_b, f.fighter_a))):
                    s1, s2 = name_score(o.fighter_a, x), name_score(o.fighter_b, y)
                    if min(s1, s2) >= 1 and max(s1, s2) == 2:
                        score = s1 + s2 - abs(d)
                        if score > best[0]:
                            best = (score, f, swapped)
        out.append(BoutMatch(o, best[1], best[2]))
    return out


def name_map(matches: Iterable[BoutMatch]) -> Dict[str, str]:
    """other-source name -> base-source name, by majority over matched bouts."""
    votes: Dict[str, Counter] = defaultdict(Counter)
    for m in matches:
        if m.base is None:
            continue
        a, b = (m.base.fighter_b, m.base.fighter_a) if m.swapped else (m.base.fighter_a, m.base.fighter_b)
        votes[m.other.fighter_a][a] += 1
        votes[m.other.fighter_b][b] += 1
    return {k: v.most_common(1)[0][0] for k, v in votes.items()}


# ------------------------------------------------------------------ results
def result_check(m: BoutMatch) -> str:
    """'agree', 'method', 'round' (details differ) or 'winner' (results conflict)."""
    o, f = m.other, m.base
    assert f is not None

    def side(fight: Fight, flip: bool) -> Optional[str]:
        if fight.winner is None:
            return None
        won_a = fight.winner == fight.fighter_a
        return ("a" if won_a else "b") if not flip else ("b" if won_a else "a")

    if side(o, False) != side(f, m.swapped):
        return "winner"
    if o.method.bucket != f.method.bucket and not ({o.method, f.method} <= {Method.DEC, Method.SPLIT_DEC}):
        return "method"
    if o.end_round != f.end_round:
        return "round"
    return "agree"


# ------------------------------------------------------------------ stats vs StatsFight
@dataclasses.dataclass
class StatsCheck:
    verdict: str  # "agree", "disputed"
    reasons: List[str]


def stats_check(f: Fight, sf: Dict, swapped: bool) -> Optional[StatsCheck]:
    """Compare UFCStats corner stats with a StatsFight record of the same bout."""
    if f.stats_a is None or f.stats_b is None or "strikes" not in sf:
        return None
    sa, sb = (sf["strikes"]["b"], sf["strikes"]["a"]) if swapped else (sf["strikes"]["a"], sf["strikes"]["b"])
    reasons = []
    # Strike share: StatsFight counts all strikes its own way, so compare who out-landed whom.
    u_total = f.stats_a.sig_landed + f.stats_b.sig_landed
    s_total = sa[0] + sb[0]
    if u_total >= 20 and s_total >= 20:
        u_share, s_share = f.stats_a.sig_landed / u_total, sa[0] / s_total
        if (u_share - 0.5) * (s_share - 0.5) < 0 and abs(u_share - s_share) > 0.2:
            reasons.append(f"strike share {u_share:.0%} (UFCStats) vs {s_share:.0%} (StatsFight)")
    if "takedowns" in sf:
        ta, tb = (sf["takedowns"]["b"], sf["takedowns"]["a"]) if swapped else (sf["takedowns"]["a"], sf["takedowns"]["b"])
        for who, u, s in (("A", f.stats_a.td_landed, ta[0]), ("B", f.stats_b.td_landed, tb[0])):
            # Counting conventions differ (chained takedowns), so only a large relative gap is a contradiction.
            if abs(u - s) >= 3 and abs(u - s) > 0.5 * max(u, s):
                reasons.append(f"takedowns {who} {u} (UFCStats) vs {s} (StatsFight)")
    return StatsCheck("disputed" if reasons else "agree", reasons)


def internally_consistent(f: Fight) -> bool:
    for s in (f.stats_a, f.stats_b):
        if s is None:
            return False
        if s.sig_landed > s.sig_attempted or s.td_landed > s.td_attempted:
            return False
        if s.ctrl_seconds > f.duration_seconds + 5:
            return False
    return True


def statsfight_fights(records: Iterable[Dict]) -> List[Tuple[Fight, Dict]]:
    """StatsFight records as Fight objects (for matching), paired with the record."""
    out = []
    for r in records:
        if "date" not in r or "a" not in r or "a_result" not in r:
            continue
        winner = r["a"] if r["a_result"] == "Win" else r["b"] if r["a_result"] == "Loss" else None
        m = str(r.get("method", "")).upper()
        method = (Method.KO if "KO" in m else Method.SUB if m.startswith("SUB") else Method.SPLIT_DEC if m in ("SD", "MD")
                  else Method.DEC if m in ("UD", "DEC") else Method.DRAW if r["a_result"] == "Draw" else Method.NC)
        f = Fight(date.fromisoformat(r["date"]), r["a"], r["b"], winner, method, int(r.get("round") or 1), 0)
        out.append((f, r))
    return out


# ------------------------------------------------------------------ physical attributes
def bio_checks(pairs: Iterable[Tuple[FighterBio, FighterBio]]) -> Dict[str, Counter]:
    """Compare the same fighter's DOB and height across two sources."""
    out = {"dob": Counter(), "height": Counter()}
    for x, y in pairs:
        if x.dob and y.dob:
            out["dob"]["agree" if x.dob == y.dob else "differ"] += 1
        if x.height_cm and y.height_cm:
            out["height"]["agree" if abs(x.height_cm - y.height_cm) <= 3 else "differ"] += 1
    return out


def load_jsonl(path: Path) -> List[Dict]:
    if not Path(path).exists():
        return []
    return [json.loads(line) for line in Path(path).open(encoding="utf-8") if line.strip()]


# ------------------------------------------------------------------ building the verified dataset
STAT_FIELDS = ("sig_landed", "sig_attempted", "td_landed", "td_attempted", "sub_attempts", "knockdowns", "ctrl_seconds", "ground_landed")


def _read_csv(path: Path) -> List[Dict[str, str]]:
    import csv

    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_verified(base_dir: Path, stats_dir: Path, statsfight_path: Path, out_dir: Path,
                   strict_stats: bool = False, fightmatrix_path: Optional[Path] = None,
                   odds_path: Optional[Path] = None) -> Dict:
    """Sherdog careers + UFCStats stats on the bouts a second source confirms. Returns the report.

    ``strict_stats``: attach stats only where StatsFight confirms them (not
    merely internally consistent), for comparing the two policies.
    """
    from .data import load_dataset
    from .sources.common import write_dataset

    base_bios, base_fights = load_dataset(Path(base_dir))
    stat_bios, stat_fights = load_dataset(Path(stats_dir))
    base_rows = _read_csv(Path(base_dir) / "fights.csv")
    stat_rows = _read_csv(Path(stats_dir) / "fights.csv")
    row_key = lambda r: (r["date"], r["fighter_a"], r["fighter_b"])  # noqa: E731
    base_by_key = {row_key(r): r for r in base_rows}
    stat_by_key = {row_key(r): r for r in stat_rows}

    # StatsFight: matched to UFCStats bouts to check both result and stats.
    sf = statsfight_fights(load_jsonl(Path(statsfight_path)))
    sf_matches = {id(m.base): (m, rec) for m, (_, rec) in zip(match_bouts(stat_fights, [f for f, _ in sf]), sf) if m.base}

    checks: Dict[str, Dict[str, str]] = defaultdict(dict)  # per fighter: attribute -> how it was verified
    report: Dict = {"results": Counter(), "stats": Counter(), "conflicts": [], "disputed_stats": [], "statsfight_results": Counter()}
    matches = match_bouts(base_fights, stat_fights)
    for m in matches:
        o = m.other
        if m.base is None:
            report["results"]["no second source"] += 1
            continue
        verdict = result_check(m)
        report["results"][verdict] += 1
        sfm = sf_matches.get(id(o))
        if sfm:  # a third opinion on the result
            report["statsfight_results"][result_check(BoutMatch(sfm[0].other, o, sfm[0].swapped))] += 1
        if verdict == "winner":
            report["conflicts"].append({"date": o.date.isoformat(), "bout": f"{o.fighter_a} vs {o.fighter_b}",
                                        "ufcstats": o.winner, "sherdog": m.base.winner,
                                        "statsfight": sfm[1].get("a_result") and (sfm[1]["a"] if sfm[1]["a_result"] == "Win" else sfm[1]["b"] if sfm[1]["a_result"] == "Loss" else "none") if sfm else None})
            continue
        # Stats: confirmed by StatsFight, or (if it lacks the bout) internally consistent.
        chk = stats_check(o, sfm[1], sfm[0].swapped) if sfm else None
        if chk is not None:
            status = "verified" if chk.verdict == "agree" else "disputed"
            if status == "disputed":
                report["disputed_stats"].append({"date": o.date.isoformat(), "bout": f"{o.fighter_a} vs {o.fighter_b}", "why": chk.reasons})
        else:
            status = "official only" if internally_consistent(o) else "inconsistent"
        report["stats"][status] += 1
        if status == "disputed" or status == "inconsistent" or (strict_stats and status != "verified"):
            continue
        for n in (m.base.fighter_a, m.base.fighter_b):
            key = "stats_verified" if status == "verified" else "stats_official"
            checks[n][key] = str(int(checks[n].get(key, "0")) + 1)
        brow = base_by_key.get((m.base.date.isoformat(), m.base.fighter_a, m.base.fighter_b))
        srow = stat_by_key.get((o.date.isoformat(), o.fighter_a, o.fighter_b))
        if brow is None or srow is None:
            continue
        # UFCStats corner a is the base row's corner b when swapped.
        for field in STAT_FIELDS:
            ua, ub = srow.get("a_" + field, ""), srow.get("b_" + field, "")
            brow["a_" + field], brow["b_" + field] = (ub, ua) if m.swapped else (ua, ub)

    # Physical attributes: a second source must agree.
    names = name_map(matches)
    base_fighters = _read_csv(Path(base_dir) / "fighters.csv")
    by_name = {r["name"]: r for r in base_fighters}
    stat_by_name = {b.name: b for b in stat_bios.values()}
    sf_reach: Dict[str, List[float]] = defaultdict(list)
    for f, rec in sf:
        for side, n in (("a", f.fighter_a), ("b", f.fighter_b)):
            v = (rec.get("reach_cm") or {}).get(side)
            if v:
                sf_reach[match_key(n)].append(float(v))
    # Fight Matrix birth dates, keyed by the Sherdog page they link to, break DOB ties.
    fm_dob: Dict[str, str] = {}
    for prof in load_jsonl(Path(fightmatrix_path)) if fightmatrix_path else []:
        d = (prof.get("stats") or {}).get("Birth Date", "").strip()
        if prof.get("sherdog_url") and re.match(r"\d{4}-\d{2}-\d{2}$", d):
            fm_dob[prof["sherdog_url"].rstrip("/").lower()] = d
    report["dob_conflicts"] = []
    report["dob"], report["height"], report["reach"] = Counter(), Counter(), Counter()
    for sname, bname in names.items():
        row, sb = by_name.get(bname), stat_by_name.get(sname)
        if row is None or sb is None:
            continue
        bb = base_bios.get(bname)
        if bb and bb.dob and sb.dob:
            if bb.dob == sb.dob:
                report["dob"]["agree"] += 1
                checks[bname]["dob"] = "Sherdog + UFCStats agree"
            else:
                third = fm_dob.get((row.get("url") or "").rstrip("/").lower())
                if third == sb.dob.isoformat():
                    row["dob"] = third
                    report["dob"]["differ, Fight Matrix sides with UFCStats"] += 1
                    checks[bname]["dob"] = "UFCStats + Fight Matrix agree (Sherdog differs)"
                elif third == bb.dob.isoformat():
                    report["dob"]["differ, Fight Matrix sides with Sherdog"] += 1
                    checks[bname]["dob"] = "Sherdog + Fight Matrix agree (UFCStats differs)"
                else:
                    report["dob"]["differ, unresolved (Sherdog kept)"] += 1
                    checks[bname]["dob"] = f"disputed: Sherdog {bb.dob}, UFCStats {sb.dob}"
                    report["dob_conflicts"].append({"name": bname, "sherdog": bb.dob.isoformat(), "ufcstats": sb.dob.isoformat(), "fightmatrix": third})
        if bb and bb.height_cm and sb.height_cm:
            ok = abs(bb.height_cm - sb.height_cm) <= 3
            report["height"]["agree" if ok else "differ"] += 1
            checks[bname]["height"] = "Sherdog + UFCStats agree" if ok else f"disputed: Sherdog {bb.height_cm:.0f} cm, UFCStats {sb.height_cm:.0f} cm"
        if sb.reach_cm:
            others = sf_reach.get(match_key(sname)) or sf_reach.get(match_key(bname))
            if others:
                ok = abs(sorted(others)[len(others) // 2] - sb.reach_cm) <= 3
                report["reach"]["agree" if ok else "differ"] += 1
                if ok:
                    row["reach_cm"] = f"{sb.reach_cm:.1f}"
                    checks[bname]["reach"] = "UFCStats + StatsFight agree"
                else:
                    checks[bname]["reach"] = f"disputed: UFCStats {sb.reach_cm:.0f} cm, StatsFight {sorted(others)[len(others) // 2]:.0f} cm (not used)"
            else:
                report["reach"]["no second source"] += 1
                checks[bname]["reach"] = f"UFCStats only ({sb.reach_cm:.0f} cm), not used until a second source confirms it"
    # Betting lines (BestFightOdds): attached only to bouts it confirms, with sane lines.
    if odds_path and Path(odds_path).exists():
        from .odds import link, load_lines

        lines, odds_report = link(base_fights, load_lines(Path(odds_path)))
        report["odds"] = odds_report
        by_id = {id(f): f for f in base_fights}
        market = {}
        for fid, ml in lines.items():
            f = by_id[fid]
            brow = base_by_key.get((f.date.isoformat(), f.fighter_a, f.fighter_b))
            if brow is not None:
                brow["a_odds"], brow["b_odds"] = str(ml.a_close), str(ml.b_close)
            market[f"{f.date.isoformat()}|{f.fighter_a}|{f.fighter_b}"] = {
                "a_open": ml.a_open, "b_open": ml.b_open, "a_close": ml.a_close, "b_close": ml.b_close,
                "movement_a": [round(x, 4) for x in ml.movement_a], "pages": ml.pages}
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        Path(out_dir, "odds.json").write_text(json.dumps(market, separators=(",", ":")))
    write_dataset(Path(out_dir), base_fighters, base_rows)
    report["results"], report["stats"] = dict(report["results"]), dict(report["stats"])
    for k in ("statsfight_results", "dob", "height", "reach"):
        report[k] = dict(report[k])
    Path(out_dir, "verification.json").write_text(json.dumps(report, indent=1))
    Path(out_dir, "fighter_checks.json").write_text(json.dumps(checks, indent=0, sort_keys=True))
    return report
