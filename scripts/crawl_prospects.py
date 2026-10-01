"""Crawl prospect candidates: Fight Matrix rankings -> screen -> Fight Matrix profile + Sherdog page.

    python scripts/crawl_prospects.py [--out data/prospects] [--max-pages 60] [--limit N]

Resumable: stage 1 writes every ranking row to fm_ranks.jsonl; stage 2 appends one
line per candidate to candidates.jsonl and skips candidates already there.
"""

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mma_predictor import prospects as PR  # noqa: E402
from mma_predictor.sources import fightmatrix, sherdog  # noqa: E402
from mma_predictor.sources.common import Fetcher  # noqa: E402


def find_sherdog(f, name: str) -> str:
    """Sherdog URL for a name: full-name search, then a surname search (Sherdog's full-name search often returns nothing)."""
    url = PR.match_name(name, sherdog.search_fighter(f, name))
    if not url and len(name.split()) > 1:
        url = PR.match_name(name, sherdog.search_fighter(f, name.split()[-1]))
    return url


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/prospects")
    ap.add_argument("--cache", default=".cache/pages")
    ap.add_argument("--max-pages", type=int, default=60)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-ranks", action="store_true")
    ap.add_argument("--skip-track", action="store_true", help="don't re-check listed prospects that left the screen")
    ap.add_argument("--confirm-only", action="store_true", help="only confirm signings on BestFightOdds")
    ap.add_argument("--noted", default="", help="noted.json: also check prospects named on outlet lists")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    f = Fetcher(Path(args.cache), delay=1.5, user_agent="Mozilla/5.0 (compatible; mma-predictor/0.1; personal research)")
    today = date.today()
    if args.confirm_only:
        confirm_signings(f, out)
        return 0

    ranks_path = out / "fm_ranks.jsonl"
    if not args.skip_ranks:
        rows = []
        for div, slug in PR.DIVISIONS.items():
            for pg in range(1, args.max_pages + 1):
                url = f"{PR.FM}/mma-ranks/{slug}/" + (f"?PageNum={pg}" if pg > 1 else "")
                try:
                    page = f.get(url, cache=False)
                except OSError as exc:
                    print(f"  {div} p{pg}: {exc}", flush=True)
                    break
                got = PR.parse_rank_page(page, div)
                if not got:
                    break
                rows += got
            print(f"{div}: {sum(r['division'] == div for r in rows)} ranked", flush=True)
        ranks_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    rows = [json.loads(l) for l in ranks_path.read_text().splitlines() if l.strip()]
    cands = [r for r in rows if PR.screen(r, today)]
    print(f"{len(rows)} ranked fighters, {len(cands)} pass the first screen", flush=True)

    cpath = out / "candidates.jsonl"
    done = set()
    if cpath.exists():
        done = {json.loads(l)["fm_url"] for l in cpath.read_text().splitlines() if l.strip()}
    todo = [c for c in cands if c["fm_url"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    with cpath.open("a") as fh:
        for i, c in enumerate(todo, 1):
            rec = dict(c)
            try:
                prof = fightmatrix.parse_profile(f.get(c["fm_url"], cache=False), c["fm_url"])
                fm = {"stats": prof.stats, "sherdog_url": prof.sherdog_url,
                      "bouts": [{"date": b.date.isoformat() if hasattr(b.date, "isoformat") else str(b.date), "opponent": b.opponent,
                                 "result": b.result, "method": b.method, "event": b.event} for b in prof.bouts]}
            except Exception as exc:  # noqa: BLE001 - keep crawling
                fm = {"error": str(exc), "bouts": [], "stats": {}}
            rec["fm"] = fm
            sd = None
            url = fm.get("sherdog_url") or ""
            try:
                if not url:
                    url = find_sherdog(f, c["name"])
                if url:
                    sd = PR.sherdog_summary(sherdog.parse_fighter(f.get(url, cache=False), url))
            except Exception as exc:  # noqa: BLE001
                rec["sherdog_error"] = str(exc)
            rec["sherdog"] = sd
            rec["check"] = PR.verify(c, fm, sd, today)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(todo)} checked", flush=True)
    # Stage 3: prospects named on outlet lists that the rankings screen missed (Sherdog + the list as the two sources).
    if args.noted:
        noted = json.loads(Path(args.noted).read_text())
        have = {PR.fold(json.loads(l)["name"]) for l in cpath.read_text().splitlines() if l.strip()}
        aliases = noted.get("aliases", {})  # list name -> Sherdog name, checked by hand (Gigi -> Giovanna)
        with cpath.open("a") as fh:
            for lst in noted["lists"]:
                for name in lst["names"]:
                    if PR.fold(name) in have or PR.fold(aliases.get(name, name)) in have:
                        continue
                    have.add(PR.fold(name))
                    try:
                        url = find_sherdog(f, aliases.get(name, name))
                        if not url:
                            print(f"  not found on Sherdog: {name}", flush=True)
                            continue
                        sd = PR.sherdog_summary(sherdog.parse_fighter(f.get(url, cache=False), url))
                    except Exception as exc:  # noqa: BLE001
                        print(f"  {name}: {exc}", flush=True)
                        continue
                    res = [b["result"] for b in sd["bouts"]]
                    last = max(sd["bouts"], key=lambda b: b["date"]) if sd["bouts"] else {}
                    row = {"division": "", "rank": None, "name": name, "fm_url": "", "age": None, "wins": res.count("win"),
                           "losses": res.count("loss"), "draws": res.count("draw"), "rating": None, "last_fight": last.get("date"),
                           "last_org": last.get("event", ""), "country": "", "via": "noted"}
                    chk = PR.verify(row, {"stats": {}, "bouts": []}, sd, today)
                    if last and (today - date.fromisoformat(last["date"])).days > 730:
                        chk["eligible"] = False
                        chk["issues"].append("inactive for two years")
                    fh.write(json.dumps(dict(row, fm={}, sherdog=sd, check=chk), ensure_ascii=False) + "\n")
                    fh.flush()
                    print(f"  {name}: {'eligible' if chk['eligible'] else '; '.join(chk['issues'])}", flush=True)
    # Stage 4: our listed prospects whose rankings row no longer passes the screen (signed? aged out?):
    # re-check their Sherdog pages so a signing shows up.
    lpath = out / "listed.json"
    if lpath.exists() and not args.skip_track:
        listed = json.loads(lpath.read_text())
        seen_urls = {(json.loads(l).get("sherdog") or {}).get("url") for l in cpath.read_text().splitlines() if l.strip()}
        todo = [e for e in listed.values() if e.get("sherdog_url") and e["sherdog_url"] not in seen_urls]
        print(f"{len(todo)} listed prospects to re-check", flush=True)
        with cpath.open("a") as fh:
            for e in todo:
                try:
                    sd = PR.sherdog_summary(sherdog.parse_fighter(f.get(e["sherdog_url"], cache=False, fresh=True), e["sherdog_url"]))
                except Exception as exc:  # noqa: BLE001
                    print(f"  {e['name']}: {exc}", flush=True)
                    continue
                row = {"division": "", "rank": None, "name": e["name"], "fm_url": "", "age": None, "wins": 0, "losses": 0, "draws": 0,
                       "rating": None, "last_fight": None, "last_org": "", "country": "", "via": "tracked"}
                fh.write(json.dumps(dict(row, fm={}, sherdog=sd, check=PR.verify(row, {"stats": {}, "bouts": []}, sd, today)), ensure_ascii=False) + "\n")
    # Stage 5: second source for each signing (BestFightOdds lists major-promotion bouts).
    confirm_signings(f, out)
    print("done", flush=True)


def confirm_signings(f, out: Path) -> None:
    from mma_predictor.sources import bestfightodds

    cands = [json.loads(l) for l in (out / "candidates.jsonl").read_text().splitlines() if l.strip()]
    noted = json.loads((out / "noted.json").read_text()) if (out / "noted.json").exists() else {}
    listed = json.loads((out / "listed.json").read_text()) if (out / "listed.json").exists() else {}
    cpath = out / "signing_checks.json"
    checks = json.loads(cpath.read_text()) if cpath.exists() else {}
    aliases = noted.get("aliases") or {}
    for s in PR.signings(noted, cands, listed, checks):
        if s["sherdog_url"] in checks:
            continue
        found = None
        spellings = [s["name"]] + [a for a, b in aliases.items() if PR.fold(b) == PR.fold(s["name"])] + [aliases.get(s["name"], s["name"])]
        for n in dict.fromkeys(spellings):
            try:
                hits = bestfightodds.search_results(f.get(bestfightodds.search_url(n), cache=False))
            except Exception as exc:  # noqa: BLE001
                print(f"  bestfightodds {n}: {exc}", flush=True)
                continue
            for _, u in [h for h in hits if PR.fold(h[0]) == PR.fold(n)][:2]:
                for b in bestfightodds.parse_fighter(f.get(u, cache=False), u):
                    d = str(b.date)[:10]
                    if abs((date.fromisoformat(d) - date.fromisoformat(s["debut"])).days) <= 2:
                        found = {"source": "BestFightOdds", "event": b.event, "date": d, "url": u}
                        break
                if found:
                    break
            if found:
                break
        if found:
            checks[s["sherdog_url"]] = found
        print(f"  signing {s['name']} ({s['promotion']} {s['debut']}): {'confirmed' if found else 'not on BestFightOdds'}", flush=True)
    cpath.write_text(json.dumps(checks, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
