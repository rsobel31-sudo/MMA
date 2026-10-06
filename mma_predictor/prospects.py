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
from typing import Dict, Iterable, List, Optional, Tuple

from .data import join_initials

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
PER_DIVISION = 100  # the list keeps each division's top 100 by score
UNRATED_PCT = 0.5  # rating percentile for prospects Fight Matrix doesn't rank


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


def major_status(bouts: List[Dict[str, object]], before: Optional[str] = None) -> Tuple[str, List[str]]:
    """Where a fighter stands with the major promotions (optionally as of a date):
    'never' fought in one; 'left' one (their most recent fight is outside the majors, and never the UFC);
    'in' one (their most recent fight was in a major); 'ufc' (fought in the UFC: never a prospect again).
    Also returns the majors they've fought in, e.g. ['ACA']."""
    bs = sorted((b for b in bouts if before is None or (b.get("date") and str(b["date"]) < before)), key=lambda b: str(b.get("date") or ""))
    majors = [b for b in bs if is_major(str(b.get("event", "")))]
    names = list(dict.fromkeys(promotion_of(str(b["event"])) for b in majors))
    if not majors:
        return "never", []
    if "UFC" in names:
        return "ufc", names
    return ("in" if is_major(str(bs[-1].get("event", ""))) else "left"), names


def verify(row: Dict[str, object], fm: Dict[str, object], sherdog: Optional[Dict[str, object]], today: date) -> Dict[str, object]:
    """Two-source eligibility: Fight Matrix profile and Sherdog page must agree."""
    issues = []
    fm_dob = (fm.get("stats") or {}).get("Birth Date") or ""
    # Majors: a fighter who has formally left PFL, ONE, ACA or RIZIN (most recent fight outside them) is
    # eligible again; anyone currently in a major, or who has fought in the UFC, is not.
    st, _ = major_status(fm.get("bouts", []))
    if st == "ufc":
        issues.append("UFC bout on Fight Matrix")
    elif st == "in":
        issues.append("most recent fight in a major promotion (Fight Matrix)")
    if sherdog is None:
        issues.append("no Sherdog page")
        return {"eligible": False, "verified": False, "issues": issues}
    sd_dob = sherdog.get("dob") or ""
    sd_bouts = sherdog.get("bouts", [])
    sd_n = len([b for b in sd_bouts if b.get("result") in ("win", "loss", "draw", "nc")])
    sd_w = len([b for b in sd_bouts if b.get("result") == "win"])
    st, former = major_status(sd_bouts)
    if st == "ufc":
        issues.append("UFC bout on Sherdog")
    elif st == "in":
        issues.append("most recent fight in a major promotion (Sherdog)")
    last = max((str(b["date"]) for b in sd_bouts if b.get("date")), default="")
    if last and (today - date.fromisoformat(last[:10])).days > 730:
        issues.append("inactive for two years")
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
    sd_l = len([b for b in sd_bouts if b.get("result") == "loss"])
    if sd_w <= sd_l:
        issues.append(f"no winning record ({sd_w}-{sd_l})")
    fm_n = row["wins"] + row["losses"] + row["draws"]
    if abs(sd_n - fm_n) > 1 or abs(sd_w - row["wins"]) > 1:
        issues.append(f"records disagree (Fight Matrix {row['wins']}-{row['losses']}-{row['draws']}, Sherdog {sd_w} wins in {sd_n})")
    return {"eligible": not issues, "verified": not any("disagree" in i or "no " in i for i in issues), "issues": issues,
            "dob": dob, "age": round(age, 1) if age is not None else None, "fights": sd_n, "former": former if st == "left" else []}


def score_pool(prospects: List[Dict[str, object]], today: date) -> None:
    """Prospect score in place (see module docstring)."""
    by_div: Dict[str, List[Dict[str, object]]] = {}
    for p in prospects:
        by_div.setdefault(p["division"], []).append(p)
    for ps in by_div.values():
        ratings = sorted(p["rating"] for p in ps if p.get("rating"))
        for p in ps:
            r = p.get("rating")
            # No Fight Matrix rating: neutral (the division's middle), whoever found them. Fight Matrix doesn't
            # rank many regional fighters at all, so a missing rating says little either way (owner's call,
            # Oct 2026); winning, finishing, youth and activity then decide where they land.
            if not r or len(ratings) < 2:
                pct = UNRATED_PCT
            else:
                pct = sum(x < r for x in ratings) / (len(ratings) - 1)
            n = p["wins"] + p["losses"] + p["draws"]
            win = (p["wins"] + 1) / (n + 2) + (0.08 if p["losses"] == 0 and p["wins"] >= 5 else 0)
            fin = p.get("finish_rate") or 0.0
            youth = max(0.0, min(1.0, (MAX_AGE - (p.get("age") or MAX_AGE)) / 7))
            days = (today - date.fromisoformat(p["last_fight"])).days if p.get("last_fight") else 999
            active = 1.0 if days <= 365 else 0.4
            # Buzz: sources naming them, each weighted by its graded track record (source_track).
            buzz = min(1.0, sum(n.get("weight", 1.0) for n in p.get("noted_by", [])) / 2)
            p["components"] = {"rating": round(pct, 3), "winning": round(min(1, win), 3), "finishing": round(fin, 3),
                               "youth": round(youth, 3), "activity": active, "buzz": buzz}
            # Mix checked against Fight Matrix snapshots from Jan 2019 and Jan 2021 (prospects_backtest): rating
            # carries most of the signal; finishing and youth add little; activity a bit more than first thought.
            # Fitted weights flip between the two snapshots, so only this small shift (finishing 10 -> 5,
            # activity 5 -> 10, better on both) was adopted.
            p["score"] = round(100 * (0.50 * pct + 0.15 * min(1, win) + 0.05 * fin + 0.10 * youth + 0.10 * active + 0.10 * buzz), 1)


def sherdog_summary(page) -> Dict[str, object]:
    return {"dob": page.dob.isoformat() if page.dob else "", "url": page.url, "team": page.team, "weight_class": page.weight_class, "nationality": page.nationality,
            "height_cm": page.height_cm, "reach_cm": page.reach_cm, "stance": page.stance, "nickname": page.nickname,
            "bouts": [{"date": b.date.isoformat(), "opponent": b.opponent, "result": b.result, "method": b.method.value if hasattr(b.method, "value") else str(b.method),
                       "round": b.round, "time": b.time, "event": b.event} for b in page.bouts]}


# ------------------------------------------------------------------- build
def fold(s: str) -> str:
    import unicodedata

    s = unicodedata.normalize("NFKD", s or "")
    return " ".join(join_initials(re.sub(r"[^a-z0-9]+", " ", "".join(c for c in s if not unicodedata.combining(c)).lower()).split()))


SUFFIX = {"jr", "sr", "ii", "iii", "iv", "uulu", "kyzy"}


def _close(a: str, b: str) -> bool:
    """Same name token: equal, one a prefix of the other (Max/Maximus), or one edit apart in a long token."""
    if a == b or (min(len(a), len(b)) >= 3 and (a.startswith(b) or b.startswith(a))):
        return True
    if min(len(a), len(b)) < 6 or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    short, long_ = sorted((a, b), key=len)
    return any(long_[:i] + long_[i + 1:] == short for i in range(len(long_)))


def match_name(name: str, hits: List[tuple]) -> str:
    """URL of the one search hit that is this person (surname exact, given names close), else ''.

    Lists write names loosely (Max Lally = Maximus Lally, Sean Clancy = Sean Clancy Jr.), so an
    exact match is tried first and a loose one is accepted only when it is unique.
    """
    want = fold(name)
    exact = {u for n, u in hits if fold(n) == want}
    if len(exact) == 1:
        return exact.pop()
    toks = want.split()
    if len(toks) < 2:
        return ""
    found = set()
    for n, u in hits:
        got = [t for t in fold(n).split() if t not in SUFFIX]
        if len(got) < 2 or toks[-1] not in got and not any(_close(toks[-1], g) and len(g) >= 6 for g in got):
            continue
        if all(any(_close(t, g) for g in got) for t in toks):
            found.add(u)
    return found.pop() if len(found) == 1 else ""


def source_of(lst: Dict[str, object]) -> str:
    """One caller: an outlet's author, a creator, or a forum username. A list with a `person` belongs to
    that person wherever they posted it (Sherdog, Tapology, X), so their calls share one track record."""
    if lst.get("person"):
        return f"person|{lst['person']}"
    return f"{lst.get('kind', 'outlet')}|{lst.get('outlet', '')}|{lst.get('author', '')}"


def _division(sherdog_wc: str) -> str:
    wc = (sherdog_wc or "").strip().title()
    return wc if wc in DIVISIONS and not wc.startswith("Women") else ""


MIN_CALLS = 20  # graded calls before a source's weight can move


PROMOTIONS = (("UFC", r"^\s*UFC"), ("PFL", r"^\s*(PFL|Professional Fighters League)"), ("Bellator", r"^\s*Bellator"),
              ("ONE", r"^\s*(ONE\b|One Championship|OneFC|ONE FC)"), ("ACA", r"^\s*(ACA|Absolute Championship)"), ("RIZIN", r"^\s*Rizin"))


def promotion_of(event: str) -> str:
    for name, rx in PROMOTIONS:
        if re.search(rx, event or "", re.I):
            return name
    return "major"


def first_major(bouts: List[Dict[str, object]]) -> Optional[Dict[str, object]]:
    maj = sorted((b for b in bouts if is_major(str(b.get("event", "")))), key=lambda b: str(b["date"]))
    return maj[0] if maj else None


def grade_call(bouts: List[Dict[str, object]], since: str) -> Optional[bool]:
    """Did a prospect call pan out?

    - In a major promotion (or ever in the UFC) when called: not a prospect call, not graded (None).
      A fighter who had formally left PFL/ONE/ACA/RIZIN by then is a prospect like any other.
    - Signed with a major promotion (a major-promotion bout) after the call: hit.
    - Otherwise: hit if they won at least two thirds of their decided fights since the call
      (at least two of them); None while fewer than two fights have happened.
    """
    if major_status(bouts, before=since)[0] in ("in", "ufc"):
        return None
    if any(is_major(str(b.get("event", ""))) and str(b.get("date", "")) >= since for b in bouts):
        return True
    after = [b for b in bouts if str(b.get("date", "")) >= since and b.get("result") in ("win", "loss")]
    if len(after) < 2:
        return None
    wins = sum(b["result"] == "win" for b in after)
    return wins / len(after) >= 2 / 3


def signings(noted: Dict[str, object], candidates: List[Dict[str, object]], listed: Dict[str, Dict[str, object]],
             checks: Optional[Dict[str, Dict[str, object]]] = None) -> List[Dict[str, object]]:
    """Prospects who signed with a major promotion after being called (by a caller) or listed (by us).

    The signing is dated by the first major-promotion bout on Sherdog; `confirm` holds the
    second source for it (BestFightOdds, filled in by the crawl) when we have one.
    """
    key = person_keys(noted, candidates)
    rec: Dict[str, tuple] = {}
    for c in candidates:
        sd = c.get("sherdog") or {}
        if sd.get("bouts"):
            shown = (noted.get("aliases") or {}).get(c["name"], c["name"])
            rec.setdefault(key(c["name"]), (listed.get(key(c["name"]), {}).get("name") or shown, sd))
    calls: Dict[str, List[dict]] = {}
    for lst in noted.get("lists", []):
        since = str(lst.get("date", ""))[:10] or "1900-01-01"
        if len(since) == 7:
            since += "-01"
        for n in lst.get("names", []):
            calls.setdefault(key(n), []).append({"source": source_of(lst), "outlet": lst.get("outlet", ""), "author": lst.get("author", ""),
                                                 "kind": lst.get("kind", "outlet"), "date": since, "url": lst.get("url", ""), "title": lst.get("title", "")})
    out = []
    for k in set(calls) | set(listed):
        if k not in rec:
            continue
        name, sd = rec[k]
        ours = listed.get(k)
        valid = sorted((c for c in calls.get(k, []) if major_status(sd["bouts"], before=c["date"])[0] not in ("in", "ufc")), key=lambda c: c["date"])
        starts = [c["date"] for c in valid] + ([str(ours["first_listed"])] if ours and major_status(sd["bouts"], before=str(ours["first_listed"]))[0] not in ("in", "ufc") else [])
        if not starts:
            continue  # in a major promotion whenever they were named
        fm = first_major([b for b in sd["bouts"] if str(b.get("date", "")) >= min(starts)])
        if fm is None:
            continue
        before = [c for c in valid if c["date"] <= str(fm["date"])]
        ours_before = ours if ours and str(ours.get("first_listed", "9999")) <= str(fm["date"]) and str(ours["first_listed"]) in starts else None
        if not before and not ours_before:
            continue
        out.append({"name": name, "sherdog_url": sd.get("url", ""), "promotion": promotion_of(str(fm["event"])),
                    "debut": str(fm["date"]), "event": fm["event"], "result": fm.get("result"), "method": fm.get("method"),
                    "called_by": before, "first_call": before[0] if before else None,
                    "lead_days": (date.fromisoformat(str(fm["date"])) - date.fromisoformat(before[0]["date"])).days if before else None,
                    "on_our_list": bool(ours_before), "our_rank": (ours_before or {}).get("best_rank"),
                    "confirmed_by": (checks or {}).get(sd.get("url", ""))})
    return sorted(out, key=lambda s: s["debut"], reverse=True)


def person_keys(noted: Dict[str, object], candidates: Iterable[Dict[str, object]]):
    """name -> one key per person: the Sherdog URL when any record of that name has one, so
    'Tommy Morrisson' on one list and 'Tommy Morrison' on another are the same prospect."""
    url = {}
    for c in candidates:
        u = (c.get("sherdog") or {}).get("url")
        if u:
            url.setdefault(fold(c["name"]), u)
    for a, b in (noted.get("aliases") or {}).items():  # either spelling may be the one a record carries
        if fold(b) in url:
            url.setdefault(fold(a), url[fold(b)])
        elif fold(a) in url:
            url.setdefault(fold(b), url[fold(a)])
    return lambda name: url.get(fold(name), fold(name))


def source_track(noted: Dict[str, object], candidates: Iterable[Dict[str, object]], today: date) -> List[Dict[str, object]]:
    """Each caller's record: graded calls, hits, and a z-score against the pooled hit rate of every graded call.
    Weights stay 1.0 until a caller has MIN_CALLS graded calls and |z| > 1.96, as for the betting pundits."""
    import math

    candidates = list(candidates)
    key = person_keys(noted, candidates)
    bouts_by = {key(c["name"]): (c.get("sherdog") or {}).get("bouts", []) for c in candidates if c.get("sherdog")}
    calls = []
    for lst in noted.get("lists", []):
        since = str(lst.get("date", ""))[:10] or "1900-01-01"
        if len(since) == 7:
            since += "-01"
        for n in lst.get("names", []):
            g = grade_call(bouts_by.get(key(n), []), since)
            calls.append((source_of(lst), lst, n, g))
    graded = [c for c in calls if c[3] is not None]
    p0 = sum(c[3] for c in graded) / len(graded) if graded else 0.5
    out = []
    for src in sorted({c[0] for c in calls}):
        mine = [c for c in calls if c[0] == src]
        g = [c for c in mine if c[3] is not None]
        hits = sum(c[3] for c in g)
        n = len(g)
        z = (hits - n * p0) / math.sqrt(n * p0 * (1 - p0)) if n and 0 < p0 < 1 else 0.0
        w = 1.0
        if n >= MIN_CALLS and abs(z) >= 1.96:
            w = (2.0 if z >= 2.58 else 1.5) if z > 0 else (0.0 if z <= -2.58 else 0.5)
        lst = mine[0][1]
        outlets = ", ".join(dict.fromkeys(str(c[1].get("outlet", "")) for c in mine if c[1].get("outlet")))
        out.append({"source": src, "kind": lst.get("kind", "outlet"), "outlet": outlets, "author": lst.get("person") or lst.get("author", ""),
                    "calls": len(mine), "graded": n, "hits": hits, "hit_rate": round(hits / n, 3) if n else None,
                    "baseline": round(p0, 3), "z": round(z, 2), "weight": w})
    return sorted(out, key=lambda t: (-t["graded"], -t["calls"]))


def noted_index(noted: Dict[str, object], key=fold) -> Dict[str, List[Dict[str, str]]]:
    idx: Dict[str, List[Dict[str, str]]] = {}
    for lst in noted.get("lists", []):
        src = {k: lst.get(k, "") for k in ("outlet", "author", "title", "url", "date", "kind", "background")}
        src["source"] = source_of(lst)
        for n in lst.get("names", []):
            if src not in idx.setdefault(key(n), []):
                idx[key(n)].append(src)
    return idx


def fill_fm_ratings(candidates: List[Dict[str, object]], path: Path = Path("data/prospects/fm_ranks.jsonl")) -> None:
    """Candidates found by name (lists, suggestions, sweeps) get their Fight Matrix rank and rating when
    exactly one ranked fighter has their name and division-free record agrees within a fight."""
    from .sources.wikipedia import match_key

    if not path.exists():
        return
    by: Dict[str, List[dict]] = {}
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            by.setdefault(match_key(r["name"]), []).append(r)
    for c in candidates:
        if c.get("rating") or not c.get("sherdog"):
            continue
        hits = by.get(match_key(c["name"]), [])
        if len(hits) != 1:
            continue
        h = hits[0]
        sd_w = sum(b.get("result") == "win" for b in c["sherdog"].get("bouts", []))
        if abs(int(h.get("wins") or 0) - sd_w) > 1:
            continue
        c.update(rating=h.get("rating"), rank=h.get("rank"), division=c.get("division") or h.get("division"), fm_rank_url=h.get("fm_url"))


OWNER_PICKS = Path("data/prospects/owner_picks.json")


def load_owner_picks(path: Path = OWNER_PICKS) -> List[Dict[str, str]]:
    return (json.loads(path.read_text()).get("picks") or []) if path.exists() else []


def apply_owner_picks(candidates: List[Dict[str, object]], picks: List[Dict[str, str]]) -> None:
    """Fighters the owner put on the list themselves are listed whatever the rules say: the rules they break
    are kept (and shown on the page) as `overrides`. The Sherdog record still has to be found and verified."""
    urls = {p.get("sherdog_url") for p in picks if p.get("sherdog_url")}
    names = {fold(p["name"]) for p in picks if p.get("name")}
    for c in candidates:
        sd = c.get("sherdog") or {}
        if not sd or not (sd.get("url") in urls or fold(c["name"]) in names):
            continue
        chk = c.setdefault("check", {})
        chk["overrides"] = list(chk.get("issues") or [])
        chk["eligible"], chk["owner_pick"] = True, True


def add_owner_pick(name: str, sherdog_url: str, note: str = "", added: Optional[str] = None, path: Path = OWNER_PICKS) -> bool:
    d = json.loads(path.read_text()) if path.exists() else {
        "_note": "Prospects the owner put on the list themselves (a suggestion on the page, or asked in chat): listed whatever the "
                 "rules say, marked Owner's pick, with the rules they break shown. Remove an entry to put them back under the rules.",
        "picks": []}
    if any(p.get("sherdog_url") == sherdog_url or fold(p.get("name", "")) == fold(name) for p in d["picks"]):
        return False
    d["picks"].append({"name": name, "sherdog_url": sherdog_url, "added": added or date.today().isoformat(), "note": note})
    path.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    return True


def build(candidates: Iterable[Dict[str, object]], noted: Dict[str, object], today: date) -> List[Dict[str, object]]:
    """Eligible, two-source-verified prospects, scored and ranked."""
    # Fight Matrix records first: when two records are the same person, keep the one with a rating.
    candidates = sorted(candidates, key=lambda c: not c.get("fm_url"))
    fill_fm_ratings(candidates)
    person = person_keys(noted, candidates)
    idx = noted_index(noted, person)
    track = source_track(noted, candidates, today)
    weights = {t["source"]: t["weight"] for t in track}
    hints = {fold(k): v for k, v in (noted.get("division_hints") or {}).items()}
    out, seen = [], set()
    for c in candidates:
        chk = c.get("check") or {}
        sd = c.get("sherdog") or {}
        if not chk.get("eligible") or not sd:
            continue
        key = person(c["name"])
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
            "name": (noted.get("aliases") or {}).get(c["name"], c["name"]), "division": c["division"] or hints.get(fold(c["name"])) or _division(sd.get("weight_class", "")) or "Unknown", "fm_rank": c.get("rank"), "rating": c.get("rating"),
            "age": chk.get("age"), "dob": chk.get("dob"), "wins": rec["W"], "losses": rec["L"], "draws": rec["D"], "nc": rec["NC"],
            "finish_rate": round(len(fin) / len(wins), 3) if wins else 0.0, "ko": sum(b["method"] == "KO/TKO" for b in wins),
            "sub": sum(b["method"] == "SUB" for b in wins), "last_fight": last.get("date") or c.get("last_fight"),
            "promotion": c.get("last_org") or "", "last_event": last.get("event", ""), "country": c.get("country") or sd.get("nationality", ""),
            "nationality": sd.get("nationality", ""), "team": sd.get("team", "") or (c.get("fm", {}).get("stats", {}) or {}).get("Association", ""),
            "height_cm": sd.get("height_cm"), "reach_cm": sd.get("reach_cm"), "stance": sd.get("stance"), "nickname": sd.get("nickname", ""),
            "recent": [{k: b[k] for k in ("date", "opponent", "result", "method", "round", "event")} for b in bouts[:6]],
            "sherdog_url": sd.get("url", ""), "fm_url": c.get("fm_url") or c.get("fm_rank_url", ""),
            "noted_by": [dict(n, weight=weights.get(n["source"], 1.0)) for n in idx.get(key, [])],
            "sources": [s for s in ("Fight Matrix" if c.get("fm_url") else "", "Sherdog", "outlet list" if c.get("via") == "noted" else "") if s],
            "former": major_status(sd.get("bouts", []))[1],
            "via": c.get("via") or ("rankings" if c.get("fm_url") else ""),
            **({"owner_pick": True, "overrides": chk.get("overrides") or []} if chk.get("owner_pick") else {}),
        })
    score_pool(out, today)
    build.track = track  # exposed for the output file
    out.sort(key=lambda p: -p["score"])
    # Top PER_DIVISION in each division (the owner's picks always stay), then the overall ranking.
    by_div: Dict[str, int] = {}
    kept = []
    for p in out:
        by_div[p["division"]] = by_div.get(p["division"], 0) + 1
        p["div_rank"] = by_div[p["division"]]
        if p["div_rank"] <= PER_DIVISION or p.get("owner_pick"):
            kept.append(p)
    for i, p in enumerate(kept, 1):
        p["p4p_rank"] = i
    return kept


def cmd_build(args) -> int:
    today = date.today()
    cands = [json.loads(l) for l in Path(args.candidates).read_text().splitlines() if l.strip()]
    noted = json.loads(Path(args.noted).read_text()) if Path(args.noted).exists() else {}
    ranks = Path(args.candidates).with_name("fm_ranks.jsonl")
    screened = sum(1 for l in ranks.read_text().splitlines() if l.strip()) if ranks.exists() else None
    # Re-check every candidate from its stored Fight Matrix and Sherdog records, so rule changes apply
    # without a recrawl.
    for c in cands:
        if c.get("sherdog") is not None:
            c["check"] = verify(c, c.get("fm") or {"stats": {}, "bouts": []}, c["sherdog"], today)
    apply_owner_picks(cands, load_owner_picks())
    pros = build(cands, noted, today)
    # Our own list's history: who we listed, from when, at best what rank (credits us when they sign).
    lpath = Path(args.candidates).with_name("listed.json")
    listed = json.loads(lpath.read_text()) if lpath.exists() else {}
    person = person_keys(noted, cands)
    for p in pros:
        k = person(p["name"])
        e = listed.setdefault(k, {"name": p["name"], "sherdog_url": p.get("sherdog_url", ""), "first_listed": today.isoformat(), "best_rank": p["p4p_rank"]})
        e["last_listed"] = today.isoformat()
        e["best_rank"] = min(e.get("best_rank") or p["p4p_rank"], p["p4p_rank"])
    lpath.write_text(json.dumps(listed, ensure_ascii=False, indent=0, sort_keys=True))
    cpath = Path(args.candidates).with_name("signing_checks.json")
    signed = signings(noted, cands, listed, json.loads(cpath.read_text()) if cpath.exists() else {})
    out = {"built": datetime.utcnow().replace(microsecond=0).isoformat() + "Z", "screened": screened, "checked": len(cands),
           "rules": {"max_age": MAX_AGE, "max_fights": MAX_FIGHTS, "per_division": PER_DIVISION, "major": "UFC, PFL/Bellator, ONE, ACA, RIZIN"},
           "lists": [{k: l.get(k, "") for k in ("outlet", "author", "title", "url", "date")} for l in noted.get("lists", [])],
           "callers": getattr(build, "track", []), "signed": signed, "prospects": pros}
    from .prospect_report import attach  # each prospect's move since the last monthly snapshot, and the latest report

    attach(out, today)
    if Path(args.out).exists():  # prospect-week's section survives a rebuild
        prev = json.loads(Path(args.out).read_text())
        if "week" in prev:
            out["week"] = prev["week"]
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    rejected = [c for c in cands if not (c.get("check") or {}).get("eligible")]
    reasons: Dict[str, int] = {}
    for c in rejected:
        for i in (c.get("check") or {}).get("issues", ["?"]):
            k = re.sub(r"\(.*|\d+(\.\d+)?", "", i).strip()
            reasons[k] = reasons.get(k, 0) + 1
    print(f"{len(pros)} prospects from {len(cands)} checked ({screened} ranked fighters screened) -> {args.out}")
    print("Left out:", ", ".join(f"{k} {v}" for k, v in sorted(reasons.items(), key=lambda kv: -kv[1])))
    print(f"{len(signed)} signed after being called or listed: " + ", ".join(f"{x['name']} ({x['promotion']} {x['debut'][:7]})" for x in signed[:12]))
    for p in pros[:15]:
        print(f"  {p['p4p_rank']:>3}. {p['name']:<26} {p['division']:<20} {p['age']:>4} {p['wins']}-{p['losses']}  {p['promotion'][:22]:<22} {p['score']}  {'★' * len(p['noted_by'])}")
    return 0


def register(sub) -> None:
    p = sub.add_parser("prospects", help="build the Prospects list (see mma_predictor/prospects.py)")
    p.add_argument("--candidates", default="data/prospects/candidates.jsonl")
    p.add_argument("--noted", default="data/prospects/noted.json")
    p.add_argument("--out", default="app/prospects.json")
    p.set_defaults(func=cmd_build)
