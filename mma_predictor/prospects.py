"""Prospects: the best young fighters not yet in a major promotion.

Eligibility (all must hold, checked on two sources):
- under 28 years old,
- fewer than 14 professional fights,
- never fought in a major promotion (UFC, PFL/Bellator, ONE, ACA, RIZIN); the
  Contender Series doesn't count as the UFC,
- active: fought in the last two years.

Candidates come from Fight Matrix's divisional rankings, which rank fighters in
every promotion, regional ones included (age, record, rating, last promotion on
each row). Each candidate's Fight Matrix profile (birth date, full record, every
bout's event) is then checked against their Sherdog page: birth date and record
must agree, and neither may show a major-promotion bout.

Prospect score (0-100), within the eligible pool:
  50%  Fight Matrix rating, as a percentile (it already weighs opposition)
  15%  winning: win share, with an unbeaten bonus
  10%  finishing: share of wins inside the distance
  10%  youth: younger is better, below 28
   5%  activity: fought in the last 12 months
  10%  buzz: independent outlet lists and coverage naming them (capped)
"""

from __future__ import annotations

import html as htmllib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

FM = "https://www.fightmatrix.com"
DIVISIONS = {
    "Flyweight": "flyweight", "Bantamweight": "bantamweight", "Featherweight": "featherweight", "Lightweight": "lightweight",
    "Welterweight": "welterweight", "Middleweight": "middleweight", "Light Heavyweight": "light-heavyweight-185-205-lbs",
    "Heavyweight": "heavyweight-265-lbs", "Women's Atomweight": "womens-atomweight", "Women's Strawweight": "womens-strawweight",
    "Women's Flyweight": "womens-flyweight", "Women's Bantamweight": "womens-bantamweight", "Women's Featherweight": "womens-featheweight",
}
MAJOR = re.compile(r"^\s*(UFC|PFL|Professional Fighters League|Bellator|ONE\b|ONE Championship|OneFC|ONE FC|ONE Friday|ONE Fight Night|ACA|Absolute Championship"
                   r"|Absolute Championship Akhmat|Rizin|RIZIN)", re.I)
NOT_MAJOR = re.compile(r"Contender Series|Road to UFC|Road to ONE|Fight Pass Invitational", re.I)
MAX_AGE, MAX_FIGHTS = 28, 14


def is_major(org_or_event: str) -> bool:
    s = org_or_event or ""
    return bool(MAJOR.search(s)) and not NOT_MAJOR.search(s)


def _text(s: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def parse_rank_page(page: str, division: str) -> List[Dict[str, object]]:
    rows = []
    for r in re.findall(r'<tr class="rankRowX".*?</table>', page, re.S):
        rk = re.search(r'class="tdRank(?:Alt)?">(\d+)<', r)
        a = re.search(r'<a name="([^"]+)"[^>]*href="(/fighter-profile/[^"]+)"', r)
        age = re.search(r'</strong>&nbsp;&nbsp;<span style="font-size: 8pt;">\((\d+)\)', r)
        rec = re.search(r'font-size: 9pt;">(\d+)-(\d+)-(\d+)', r)
        pts = re.search(r'class="tdBar"[^>]*>(\d+)<', r)
        last = re.search(r"Last Fight: ([\d/]+) \[([^\]]+)\]", r)
        flag = re.search(r'/images/flag/([A-Za-z]+)\.png', r)
        if not (rk and a and rec):
            continue
        ld = None
        if last:
            m, d, y = last.group(1).split("/")
            ld = f"{y}-{int(m):02d}-{int(d):02d}"
        rows.append({
            "division": division, "rank": int(rk.group(1)), "name": htmllib.unescape(a.group(1)), "fm_url": FM + a.group(2),
            "age": int(age.group(1)) if age else None, "wins": int(rec.group(1)), "losses": int(rec.group(2)), "draws": int(rec.group(3)),
            "rating": int(pts.group(1)) if pts else None, "last_fight": ld, "last_org": last.group(2) if last else "",
            "country": flag.group(1) if flag else "",
        })
    return rows


def screen(row: Dict[str, object], today: date) -> bool:
    """First pass on the rankings row alone."""
    n = row["wins"] + row["losses"] + row["draws"]
    if row["age"] is None or row["age"] >= MAX_AGE or n >= MAX_FIGHTS or n == 0:
        return False
    if is_major(str(row["last_org"])):
        return False
    if not row["last_fight"] or (today - date.fromisoformat(row["last_fight"])).days > 730:
        return False
    return True


def age_on(dob: Optional[str], today: date) -> Optional[float]:
    if not dob:
        return None
    d = date.fromisoformat(dob)
    return (today - d).days / 365.25


def verify(row: Dict[str, object], fm: Dict[str, object], sherdog: Optional[Dict[str, object]], today: date) -> Dict[str, object]:
    """Two-source eligibility: Fight Matrix profile and Sherdog page must agree."""
    issues = []
    fm_dob = (fm.get("stats") or {}).get("Birth Date") or ""
    fm_events = [b.get("event", "") for b in fm.get("bouts", [])]
    if any(is_major(e) for e in fm_events):
        issues.append("major-promotion bout on Fight Matrix")
    if sherdog is None:
        issues.append("no Sherdog page")
        return {"eligible": False, "verified": False, "issues": issues}
    sd_dob = sherdog.get("dob") or ""
    sd_bouts = sherdog.get("bouts", [])
    sd_n = len([b for b in sd_bouts if b.get("result") in ("win", "loss", "draw", "nc")])
    sd_w = len([b for b in sd_bouts if b.get("result") == "win"])
    if any(is_major(b.get("event", "")) for b in sd_bouts):
        issues.append("major-promotion bout on Sherdog")
    dob = sd_dob or fm_dob
    if fm_dob and sd_dob and abs((date.fromisoformat(fm_dob) - date.fromisoformat(sd_dob)).days) > 1:
        issues.append(f"birth dates disagree ({fm_dob} vs {sd_dob})")
    age = age_on(dob, today)
    if age is None:
        issues.append("no birth date")
    elif age >= MAX_AGE:
        issues.append(f"age {age:.1f}")
    if sd_n >= MAX_FIGHTS:
        issues.append(f"{sd_n} fights on Sherdog")
    fm_n = row["wins"] + row["losses"] + row["draws"]
    if abs(sd_n - fm_n) > 1 or abs(sd_w - row["wins"]) > 1:
        issues.append(f"records disagree (Fight Matrix {row['wins']}-{row['losses']}-{row['draws']}, Sherdog {sd_w} wins in {sd_n})")
    return {"eligible": not issues, "verified": not any("disagree" in i or "no " in i for i in issues), "issues": issues,
            "dob": dob, "age": round(age, 1) if age is not None else None, "fights": sd_n}


def score_pool(prospects: List[Dict[str, object]], today: date) -> None:
    """Prospect score in place (see module docstring)."""
    by_div: Dict[str, List[Dict[str, object]]] = {}
    for p in prospects:
        by_div.setdefault(p["division"], []).append(p)
    for ps in by_div.values():
        ratings = sorted(p["rating"] for p in ps if p.get("rating"))
        for p in ps:
            r = p.get("rating")
            # No Fight Matrix rating (found only via an outlet list): neutral on this component.
            pct = 0.5 if not r or len(ratings) < 2 else sum(x < r for x in ratings) / (len(ratings) - 1)
            n = p["wins"] + p["losses"] + p["draws"]
            win = (p["wins"] + 1) / (n + 2) + (0.08 if p["losses"] == 0 and p["wins"] >= 5 else 0)
            fin = p.get("finish_rate") or 0.0
            youth = max(0.0, min(1.0, (MAX_AGE - (p.get("age") or MAX_AGE)) / 7))
            days = (today - date.fromisoformat(p["last_fight"])).days if p.get("last_fight") else 999
            active = 1.0 if days <= 365 else 0.4
            buzz = min(1.0, len(p.get("noted_by", [])) / 2)
            p["components"] = {"rating": round(pct, 3), "winning": round(min(1, win), 3), "finishing": round(fin, 3),
                               "youth": round(youth, 3), "activity": active, "buzz": buzz}
            p["score"] = round(100 * (0.50 * pct + 0.15 * min(1, win) + 0.10 * fin + 0.10 * youth + 0.05 * active + 0.10 * buzz), 1)


def sherdog_summary(page) -> Dict[str, object]:
    return {"dob": page.dob.isoformat() if page.dob else "", "url": page.url, "team": page.team, "nationality": page.nationality,
            "height_cm": page.height_cm, "reach_cm": page.reach_cm, "stance": page.stance, "nickname": page.nickname,
            "bouts": [{"date": b.date.isoformat(), "opponent": b.opponent, "result": b.result, "method": b.method.value if hasattr(b.method, "value") else str(b.method),
                       "round": b.round, "time": b.time, "event": b.event} for b in page.bouts]}


# ------------------------------------------------------------------- build
def fold(s: str) -> str:
    import unicodedata

    s = unicodedata.normalize("NFKD", s or "")
    return re.sub(r"[^a-z0-9]+", " ", "".join(c for c in s if not unicodedata.combining(c)).lower()).strip()


def noted_index(noted: Dict[str, object]) -> Dict[str, List[Dict[str, str]]]:
    idx: Dict[str, List[Dict[str, str]]] = {}
    for lst in noted.get("lists", []):
        src = {k: lst.get(k, "") for k in ("outlet", "author", "title", "url", "date")}
        for n in lst.get("names", []):
            idx.setdefault(fold(n), []).append(src)
    return idx


def build(candidates: Iterable[Dict[str, object]], noted: Dict[str, object], today: date) -> List[Dict[str, object]]:
    """Eligible, two-source-verified prospects, scored and ranked."""
    idx = noted_index(noted)
    hints = {fold(k): v for k, v in (noted.get("division_hints") or {}).items()}
    out, seen = [], set()
    for c in candidates:
        chk = c.get("check") or {}
        sd = c.get("sherdog") or {}
        if not chk.get("eligible") or not sd:
            continue
        key = fold(c["name"])
        if key in seen:
            continue
        seen.add(key)
        bouts = sorted(sd.get("bouts", []), key=lambda b: b["date"], reverse=True)
        wins = [b for b in bouts if b["result"] == "win"]
        fin = [b for b in wins if b["method"] in ("KO/TKO", "SUB")]
        last = bouts[0] if bouts else {}
        rec = {"W": sum(b["result"] == "win" for b in bouts), "L": sum(b["result"] == "loss" for b in bouts),
               "D": sum(b["result"] == "draw" for b in bouts), "NC": sum(b["result"] == "nc" for b in bouts)}
        out.append({
            "name": c["name"], "division": c["division"] or hints.get(key) or "Unknown", "fm_rank": c.get("rank"), "rating": c.get("rating"),
            "age": chk.get("age"), "dob": chk.get("dob"), "wins": rec["W"], "losses": rec["L"], "draws": rec["D"], "nc": rec["NC"],
            "finish_rate": round(len(fin) / len(wins), 3) if wins else 0.0, "ko": sum(b["method"] == "KO/TKO" for b in wins),
            "sub": sum(b["method"] == "SUB" for b in wins), "last_fight": last.get("date") or c.get("last_fight"),
            "promotion": c.get("last_org") or "", "last_event": last.get("event", ""), "country": c.get("country") or sd.get("nationality", ""),
            "nationality": sd.get("nationality", ""), "team": sd.get("team", "") or (c.get("fm", {}).get("stats", {}) or {}).get("Association", ""),
            "height_cm": sd.get("height_cm"), "reach_cm": sd.get("reach_cm"), "stance": sd.get("stance"), "nickname": sd.get("nickname", ""),
            "recent": [{k: b[k] for k in ("date", "opponent", "result", "method", "round", "event")} for b in bouts[:6]],
            "sherdog_url": sd.get("url", ""), "fm_url": c.get("fm_url", ""), "noted_by": idx.get(key, []),
            "sources": [s for s in ("Fight Matrix" if c.get("fm_url") else "", "Sherdog", "outlet list" if c.get("via") == "noted" else "") if s],
        })
    score_pool(out, today)
    out.sort(key=lambda p: -p["score"])
    for i, p in enumerate(out, 1):
        p["p4p_rank"] = i
    by_div: Dict[str, int] = {}
    for p in out:
        by_div[p["division"]] = by_div.get(p["division"], 0) + 1
        p["div_rank"] = by_div[p["division"]]
    return out


def cmd_build(args) -> int:
    today = date.today()
    cands = [json.loads(l) for l in Path(args.candidates).read_text().splitlines() if l.strip()]
    noted = json.loads(Path(args.noted).read_text()) if Path(args.noted).exists() else {}
    ranks = Path(args.candidates).with_name("fm_ranks.jsonl")
    screened = sum(1 for l in ranks.read_text().splitlines() if l.strip()) if ranks.exists() else None
    pros = build(cands, noted, today)
    out = {"built": datetime.utcnow().replace(microsecond=0).isoformat() + "Z", "screened": screened, "checked": len(cands),
           "rules": {"max_age": MAX_AGE, "max_fights": MAX_FIGHTS, "major": "UFC, PFL/Bellator, ONE, ACA, RIZIN"},
           "lists": [{k: l.get(k, "") for k in ("outlet", "author", "title", "url", "date")} for l in noted.get("lists", [])],
           "prospects": pros}
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    rejected = [c for c in cands if not (c.get("check") or {}).get("eligible")]
    reasons: Dict[str, int] = {}
    for c in rejected:
        for i in (c.get("check") or {}).get("issues", ["?"]):
            k = re.sub(r"\(.*|\d+(\.\d+)?", "", i).strip()
            reasons[k] = reasons.get(k, 0) + 1
    print(f"{len(pros)} prospects from {len(cands)} checked ({screened} ranked fighters screened) -> {args.out}")
    print("Left out:", ", ".join(f"{k} {v}" for k, v in sorted(reasons.items(), key=lambda kv: -kv[1])))
    for p in pros[:15]:
        print(f"  {p['p4p_rank']:>3}. {p['name']:<26} {p['division']:<20} {p['age']:>4} {p['wins']}-{p['losses']}  {p['promotion'][:22]:<22} {p['score']}  {'★' * len(p['noted_by'])}")
    return 0


def register(sub) -> None:
    p = sub.add_parser("prospects", help="build the Prospects list (see mma_predictor/prospects.py)")
    p.add_argument("--candidates", default="data/prospects/candidates.jsonl")
    p.add_argument("--noted", default="data/prospects/noted.json")
    p.add_argument("--out", default="app/prospects.json")
    p.set_defaults(func=cmd_build)
