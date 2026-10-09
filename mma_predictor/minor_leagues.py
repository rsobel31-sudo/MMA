"""The Minor Leagues tab: regional promotions in tiers by the strength of their fighters (our regional rating),
each with a short overview (home base, history, alumni who went on to the majors, prospects fighting there now).

Built from the regional crawl (data/regional/), the main dataset and the Sherdog organization pages
(data/regional/orgs.json, from scripts/crawl_promotions.py). Writes app/minor_leagues.json.

    python -m mma_predictor.minor_leagues
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

from . import prospects as PR
from . import regional as R

OUT = Path("app/minor_leagues.json")
# Not minor leagues: the UFC's own feeder shows (it runs them, and winners go straight to UFC contracts).
FEEDERS = {"Dana White's Contender Series", "Road to UFC"}
TIERS = [(1950, 1, "Elite"), (1850, 2, "Strong"), (1750, 3, "Solid"), (1650, 4, "Developmental"), (0, 5, "Local")]


def tier(rating: float):
    return next((t, label) for cut, t, label in TIERS if (rating or 0) >= cut)


def _country(loc: str) -> str:
    parts = [p.strip() for p in (loc or "").split(",") if p.strip()]
    return parts[-1] if parts else ""


def _city(loc: str) -> str:
    """"Venue, City, [State,] Country" -> "City" (or "City, State" where the country has states)."""
    parts = [p.strip() for p in (loc or "").split(",") if p.strip()]
    if len(parts) >= 4:
        return f"{parts[1]}, {parts[-2]}"
    return parts[1] if len(parts) == 3 else parts[0] if parts else ""


def brand(prom: str) -> str:
    """The major promotion's brand: "UFC on ESPN" and "UFC Fight Night" -> "UFC"."""
    for key, name in (("UFC", "UFC"), ("Professional Fighters League", "PFL"), ("PFL", "PFL"), ("Bellator", "Bellator"),
                      ("ONE", "ONE"), ("Rizin", "Rizin"), ("ACA", "ACA"), ("ACB", "ACB"), ("Strikeforce", "Strikeforce"),
                      ("World Series of Fighting", "WSOF"), ("Pride", "Pride"), ("WEC", "WEC")):
        if prom.startswith(key):
            return name
    return prom


def canonicalizer(orgs: dict = None):
    """Event -> promotion, with every name a promotion has gone by counted as one: Cage Warriors billed its
    events "CWFC 56" until 2017 and "CW 90" after, and Fight Nights Global became AMC Fight Nights. Names are
    joined through the Sherdog organization pages (data/regional/orgs.json): the names that share an organization,
    and the names on every event in its history. Each organization is shown under its busiest name since 2020."""
    if orgs is None:
        orgs = json.loads(Path("data/regional/orgs.json").read_text()) if Path("data/regional/orgs.json").exists() else {}
    bouts = {p["promotion"]: p["bouts"] for p in R.promotions(min_bouts=0)}
    by_org: Dict[str, List[str]] = {}
    for key, o in orgs.items():
        if o.get("org_url") and key not in FEEDERS:
            by_org.setdefault(o["org_url"], []).append(key)
    primary = {url: max(keys, key=lambda k: bouts.get(k, 0)) for url, keys in by_org.items()}
    primaries = set(primary.values())
    alias: Dict[str, str] = {}
    for url, keys in by_org.items():
        main = primary[url]
        names = set(keys) | {R.promotion(e[1]) for e in (orgs[keys[0]].get("events") or []) if not PR.is_major(e[1])}
        for k in names:
            if k and k not in FEEDERS and (k == main or k not in primaries):
                alias.setdefault(k, main)

    def canon(event: str) -> str:
        p = R.promotion(event)
        return p if PR.is_major(event) else alias.get(p, p)
    return canon


def overview(org: dict, prom: str, today: date, canon=None) -> dict:
    ev = org.get("events") or []
    own = [e for e in ev if (canon(e[1]) if canon else R.promotion(e[1])) == prom]
    ev = own or ev  # an organization page can carry several brands (the UFC's carries Road to UFC)
    past = [e for e in ev if e[0] <= today.isoformat()]
    future = [e for e in ev if e[0] > today.isoformat()]
    recent = [e for e in past if e[0] >= (today - timedelta(days=5 * 365)).isoformat()] or past
    countries = Counter(_country(e[2]) for e in recent if e[2])
    cities = Counter(_city(e[2]) for e in recent if e[2])
    return {"org_name": org.get("org_name"), "org_url": org.get("org_url"), "events_total": len(past),
            "first_event": past[0][0] if past else None, "last_event": past[-1] if past else None,
            "next_event": future[0] if future else None,
            "countries": [[c, n] for c, n in countries.most_common(4) if c],
            "cities": [c for c, _ in cities.most_common(4) if c],
            "active": bool(future) or bool(past and past[-1][0] >= (today - timedelta(days=365)).isoformat())}


def build(today: date = None) -> dict:
    today = today or date.today()
    canon = canonicalizer()
    recs = R.load_records()
    bs = R.all_bouts(recs)
    names: Dict[str, str] = {}
    for r in csv.DictReader(Path("data/sherdog/fighters.csv").open(encoding="utf-8")):
        if r.get("url"):
            names[r["url"]] = r["name"]
    names.update({u: r["name"] for u, r in recs.items()})
    # Each fighter's first major bout, and their major record.
    first_major: Dict[str, tuple] = {}
    major_rec: Dict[str, List[int]] = {}
    ufc_rec: Dict[str, List[int]] = {}  # the UFC is the premier promotion: its alumni are listed first
    for b in bs:
        if not PR.is_major(b.event):
            continue
        for f, s in ((b.a, b.score_a), (b.b, 1 - b.score_a)):
            first_major.setdefault(f, (b.day, R.promotion(b.event)))
            for rec in (major_rec, ufc_rec) if brand(R.promotion(b.event)) == "UFC" else (major_rec,):
                w = rec.setdefault(f, [0, 0])
                w[0] += s == 1.0
                w[1] += s == 0.0
    # Record in each promotion before reaching the majors; last regional promotion per fighter.
    here: Dict[str, Dict[str, List[int]]] = {}
    last_prom: Dict[str, tuple] = {}
    for b in bs:
        if PR.is_major(b.event):
            continue
        prom = canon(b.event)
        for f, s in ((b.a, b.score_a), (b.b, 1 - b.score_a)):
            if f in first_major and b.day >= first_major[f][0]:
                continue
            w = here.setdefault(prom, {}).setdefault(f, [0, 0])
            w[0] += s == 1.0
            w[1] += s == 0.0
        for f in (b.a, b.b):
            if b.day >= last_prom.get(f, (date.min,))[0]:
                last_prom[f] = (b.day, prom)
    pros = json.loads(Path("app/prospects.json").read_text())["prospects"] if Path("app/prospects.json").exists() else []
    orgs = json.loads(Path("data/regional/orgs.json").read_text()) if Path("data/regional/orgs.json").exists() else {}
    out = []
    for p in R.promotions(canon=canon):
        if not p["mean_rating"] or p["promotion"] in FEEDERS:
            continue
        t, label = tier(p["mean_rating"])
        prom = p["promotion"]
        alumni = []
        for f, (w, l) in here.get(prom, {}).items():
            if f not in first_major:
                continue
            mw, ml = major_rec[f]
            uw, ul = ufc_rec.get(f, (0, 0))
            first = brand(first_major[f][1])
            alumni.append({"name": names.get(f, f), "here": f"{w}-{l}",
                           "went_to": first if first == "UFC" or f not in ufc_rec else f"{first} → UFC",
                           "major": f"{mw}-{ml}", "ufc": f"{uw}-{ul}" if f in ufc_rec else None,
                           "debut": first_major[f][0].isoformat(), "_k": (f in ufc_rec, uw - ul, mw - ml, mw)})
        alumni.sort(key=lambda a: a.pop("_k"), reverse=True)
        current = [{"name": x["name"], "rank": x["p4p_rank"], "division": x["division"], "record": f"{x['wins']}-{x['losses']}"}
                   for x in pros if last_prom.get(x.get("sherdog_url") or "", (None, None))[1] == prom]
        current.sort(key=lambda x: x["rank"])
        row = dict(p, tier=t, tier_label=label, alumni_count=len(alumni), alumni=alumni[:10], prospects=current[:8])
        org = orgs.get(prom)
        if org and org.get("org_url"):
            row.update(overview(org, prom, today, canon))
        out.append(row)
    out.sort(key=lambda r: (r["tier"], -r["mean_rating"]))
    return {"built": today.isoformat(), "since": "2020-01-01",
            "tiers": [{"tier": t, "label": label, "min_rating": cut} for cut, t, label in TIERS], "promotions": out}


def main() -> int:
    d = build()
    OUT.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote {OUT} ({len(d['promotions'])} promotions, {OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
