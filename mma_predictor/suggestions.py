"""Prospects the owner suggests from the page, each credited to the commentator who rates them.

    python -m mma_predictor prospect-suggestions --docs .cache/suggestions   # an ArtifactData out_dir export
    python -m mma_predictor prospect-suggestions --name "Abdi Iniestra" --by Hellowhosthat --where "Sherdog forums"

For each pending suggestion:
1. Find the fighter on Sherdog (full name, then surname, unique loose match) and on Fight Matrix's
   rankings (data/prospects/fm_ranks.jsonl). Found in both: the normal two-source check, with their
   Fight Matrix rating in the score. Sherdog only: checked as a list pick (Sherdog + the commentator's
   call as the two sources), rated neutrally on the Fight Matrix component.
2. Log the call under the commentator's name (data/prospects/noted.json), with the owner's background
   notes, so it counts toward that commentator's track record like any other call.
3. Rebuild app/prospects.json and report each suggestion's outcome: added (rank and score), already
   listed, not eligible (why), or not found. The routine writes the outcome back to the page.
"""

from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from . import prospects as PR
from .sources.wikipedia import match_key

ROOT = Path(__file__).resolve().parent.parent
PDIR = ROOT / "data" / "prospects"
UPDATES = PDIR / "suggestion_updates.json"
UA = "Mozilla/5.0 (compatible; mma-predictor/0.1; personal research)"
WHERE = {  # page choice -> (kind, outlet)
    "Sherdog forums": ("forum", "Sherdog Forums"), "X / Twitter": ("creator", "X"), "Tapology": ("creator", "Tapology"),
    "Reddit": ("forum", "Reddit"), "Podcast / YouTube": ("creator", "Podcast/YouTube"), "Article": ("outlet", ""), "Other": ("creator", ""),
}


def find_sherdog(f, name: str) -> str:
    from .sources import sherdog

    url = PR.match_name(name, sherdog.search_fighter(f, name))
    if not url and len(name.split()) > 1:
        url = PR.match_name(name, sherdog.search_fighter(f, name.split()[-1]))
    return url


def fm_row(name: str) -> Optional[dict]:
    path = PDIR / "fm_ranks.jsonl"
    if not path.exists():
        return None
    k = match_key(name)
    hits = [r for r in (json.loads(l) for l in path.read_text().splitlines() if l.strip()) if match_key(r["name"]) == k]
    return hits[0] if len(hits) == 1 else None


def spellings(name: str) -> list:
    """'Daniyar (Daniiar) Toychubek Uulu' -> ['Daniyar Toychubek Uulu', 'Daniiar Toychubek Uulu']."""
    import re

    m = re.search(r"\(([^)]+)\)", name)
    base = re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", " ", name)).strip()
    if not m:
        return [base]
    before = name[:m.start()].strip().split()
    alt = re.sub(r"\s+", " ", " ".join(before[:-1] + [m.group(1)]) + " " + name[m.end():]).strip()
    return list(dict.fromkeys([base, alt]))


def check(f, name: str, today: date) -> Optional[dict]:
    """A candidate record like the crawl's: Fight Matrix + Sherdog when ranked there, else Sherdog alone.
    Alternate spellings in brackets are each tried."""
    for n in spellings(name):
        rec = _check(f, n, today)
        if rec:
            return rec
    return None


def _check(f, name: str, today: date) -> Optional[dict]:
    from .sources import fightmatrix, sherdog

    row = fm_row(name)
    fm = {"stats": {}, "bouts": []}
    url = ""
    if row:
        try:
            prof = fightmatrix.parse_profile(f.get(row["fm_url"], cache=False), row["fm_url"])
            fm = {"stats": prof.stats, "sherdog_url": prof.sherdog_url, "bouts": [
                {"date": str(b.date), "opponent": b.opponent, "result": b.result, "method": b.method, "event": b.event} for b in prof.bouts]}
            url = prof.sherdog_url or ""
        except Exception:  # noqa: BLE001 - fall back to Sherdog alone
            row = None
    url = url or find_sherdog(f, name)
    if not url:
        return None
    sd = PR.sherdog_summary(sherdog.parse_fighter(f.get(url, cache=False, fresh=True), url))
    if row is None:
        res = [b["result"] for b in sd["bouts"]]
        last = max(sd["bouts"], key=lambda b: b["date"]) if sd["bouts"] else {}
        row = {"division": "", "rank": None, "name": name, "fm_url": "", "age": None, "wins": res.count("win"), "losses": res.count("loss"),
               "draws": res.count("draw"), "rating": None, "last_fight": last.get("date"), "last_org": last.get("event", ""), "country": "", "via": "suggested"}
    chk = PR.verify(row, fm, sd, today)
    last = max((b["date"] for b in sd["bouts"]), default=None)
    if last and (today - date.fromisoformat(last)).days > 730:
        chk["eligible"] = False
        chk["issues"].append("inactive for two years")
    return dict(row, fm=fm, sherdog=sd, check=chk)


def call_list(s: dict, today: date) -> dict:
    kind, outlet = WHERE.get(s.get("where", ""), ("creator", ""))
    who = (s.get("commentator") or "").strip() or "Owner"
    return {"kind": kind, "outlet": outlet or s.get("where", "") or "Owner's report", "author": who, "person": who,
            "title": f"Suggested on Fight Lab: {who}" + (f" on {s['where']}" if s.get("where") else ""),
            "url": s.get("link", ""), "date": (s.get("said_on") or today.isoformat())[:10], "names": [spellings(s["name"])[0]],
            "background": (s.get("background") or "").strip()[:2000], "via": "owner"}


def load_docs(path: Path) -> Dict[str, dict]:
    if path.is_dir():
        return {p.stem: json.loads(p.read_text()) for p in sorted(path.rglob("*.json"))}
    data = json.loads(path.read_text())
    return {d.get("id") or d.get("_id"): d for d in data} if isinstance(data, list) else data


def cmd_suggestions(args) -> int:
    from .sources.common import Fetcher
    from .tapology_import import add_list

    today = date.today()
    docs = load_docs(Path(args.docs)) if args.docs else {
        "cli": {"name": args.name, "commentator": args.by, "where": args.where, "said_on": args.date, "link": args.link,
                "background": args.background, "status": "pending"}}
    pending = {k: d for k, d in docs.items() if d and d.get("name") and d.get("status", "pending") == "pending"}
    if not pending:
        print("No pending suggestions.")
        return 0
    f = Fetcher(ROOT / ".cache" / "pages", delay=1.5, user_agent=UA)
    noted = json.loads((PDIR / "noted.json").read_text())
    cpath = PDIR / "candidates.jsonl"
    found: Dict[str, Optional[dict]] = {}
    for k, s in pending.items():
        name = s["name"].strip()
        try:
            rec = check(f, name, today)
        except Exception as exc:  # noqa: BLE001
            print(f"  {name}: lookup failed ({exc})")
            rec = None
        found[k] = rec
        add_list(noted, call_list(s, today))
        if rec and not args.dry_run:
            with cpath.open("a") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if args.dry_run:
        print(json.dumps({k: (v or {}).get("check") for k, v in found.items()}, indent=1))
        return 0
    (PDIR / "noted.json").write_text(json.dumps(noted, ensure_ascii=False, indent=1))
    subprocess.run([sys.executable, "-m", "mma_predictor", "prospects"], cwd=ROOT, check=True, capture_output=True)
    built = json.loads((ROOT / "app" / "prospects.json").read_text())
    by_url = {p.get("sherdog_url"): p for p in built["prospects"]}
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    updates = {}
    for k, s in pending.items():
        rec = found[k]
        if rec is None:
            u = {"status": "not found", "detail": "No unique match on Sherdog. Check the spelling, or add a Sherdog link."}
        else:
            p = by_url.get((rec.get("sherdog") or {}).get("url"))
            if p:
                u = {"status": "listed", "p4p_rank": p["p4p_rank"], "div_rank": p["div_rank"], "division": p["division"], "score": p["score"],
                     "record": f"{p['wins']}-{p['losses']}" + (f"-{p['draws']}" if p.get("draws") else ""), "age": p.get("age"),
                     "detail": f"#{p['p4p_rank']} overall, #{p['div_rank']} {p['division']}, score {p['score']}"}
            else:
                u = {"status": "not eligible", "detail": "; ".join(rec["check"].get("issues") or ["did not pass the screen"])}
            u["sherdog_url"] = (rec.get("sherdog") or {}).get("url", "")
        u["processed"] = now
        updates[k] = u
        print(f"  {s['name']}: {u['status']} - {u['detail']}")
    UPDATES.write_text(json.dumps(updates, indent=1, ensure_ascii=False))
    print(f"Outcomes in {UPDATES.relative_to(ROOT)}: write each into prospect_suggestions/<id> (update, pin if_version).")
    return 0


def register(sub) -> None:
    p = sub.add_parser("prospect-suggestions", help="check and score prospects the owner suggested on the page")
    p.add_argument("--docs", default="", help="ArtifactData export (out_dir) of prospect_suggestions, or a JSON file")
    p.add_argument("--name", default="")
    p.add_argument("--by", default="", help="the commentator who rates them")
    p.add_argument("--where", default="Other", choices=list(WHERE))
    p.add_argument("--date", default="")
    p.add_argument("--link", default="")
    p.add_argument("--background", default="")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_suggestions)
