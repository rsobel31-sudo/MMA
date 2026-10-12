"""Weekly data refresh: new results in, stale records re-checked, everything re-verified and re-exported.

    python -m mma_predictor refresh            # the whole Sunday refresh
    python -m mma_predictor refresh --dry-run  # fetch and merge, report, write nothing

The page cache isn't kept between sessions, so the refresh never rebuilds from it. It
updates the saved datasets in place:

1. Sherdog: every fighter on UFC events since the last bout we have, plus a rotating
   batch of exported fighters whose pages are the longest unchecked (non-UFC bouts,
   corrected results). Their bouts are merged into data/sherdog by (date, both names).
2. UFCStats (Kaggle scrape): re-downloaded; imported only when the dump is newer.
3. StatsFight (the second opinion on stats): new UFC bouts from its sitemap.
4. Fight Matrix and BestFightOdds pages of the recent fighters, replaced in place
   (closing lines and post-fight ratings).
5. Division/gender (Wikipedia roster), the upcoming cards, verify and export.

Each run appends a line to data/refresh_log.jsonl.
"""

from __future__ import annotations

import csv
import dataclasses
import json
import subprocess
import sys
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .data import normalise_name

ROOT = Path(__file__).resolve().parent.parent
SHERDOG = ROOT / "data" / "sherdog"
REFRESHED = SHERDOG / "refreshed.json"
LOG = ROOT / "data" / "refresh_log.jsonl"
UA = "Mozilla/5.0 (compatible; mma-predictor/0.1; personal research)"
EXPORT_ARGS = ["--data", "data/verified", "--events", "UFC", "--min-fights", "2", "--active-years", "3",
               "--source", "Sherdog + UFCStats (cross-verified) + Fight Matrix + BestFightOdds + Wikipedia"]
BIO = ("dob", "height_cm", "reach_cm", "stance", "weight_class", "nationality", "team", "url", "profile")
RESULT = ("event", "winner", "method", "round", "time", "scheduled_rounds", "title_fight")


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _key(row: Dict[str, str], day_shift: int = 0) -> tuple:
    d = (date.fromisoformat(row["date"]) + timedelta(days=day_shift)).isoformat()
    return d, frozenset((normalise_name(row["fighter_a"]), normalise_name(row["fighter_b"])))


def merge_rows(fighters: List[Dict[str, str]], fights: List[Dict[str, str]],
               new_fighters: List[Dict[str, str]], new_fights: List[Dict[str, str]]) -> Dict[str, object]:
    """Merge freshly parsed rows into a dataset (in place). Returns what changed.

    Fighters match by Sherdog URL, else name; a renamed page keeps the dataset's name so
    existing bouts stay linked. Bouts match by date (±1 day) and both names: a known bout
    takes the fresh result (overturned decisions, NCs), an unknown one is added.
    """
    by_url = {r["url"]: r for r in fighters if r.get("url")}
    by_name = {r["name"]: r for r in fighters}
    rename: Dict[str, str] = {}
    added_fighters = 0
    for nf in new_fighters:
        old = (by_url.get(nf["url"]) if nf.get("url") else None) or by_name.get(nf["name"])
        if old is None:
            fighters.append(nf)
            by_name[nf["name"]] = nf
            if nf.get("url"):
                by_url[nf["url"]] = nf
            added_fighters += 1
            continue
        if old["name"] != nf["name"]:
            rename[nf["name"]] = old["name"]
        if nf.get("profile") == "1":  # the fighter's own page: its bio is current
            for k in BIO:
                if nf.get(k):
                    old[k] = nf[k]
    index = {_key(r): r for r in fights}
    added, changed = [], []
    for nb in new_fights:
        nb = dict(nb)
        for k in ("fighter_a", "fighter_b", "winner"):
            nb[k] = rename.get(nb[k], nb[k])
        old = index.get(_key(nb)) or index.get(_key(nb, -1)) or index.get(_key(nb, 1))
        if old is None:
            fights.append(nb)
            index[_key(nb)] = nb
            added.append(nb)
            continue
        if normalise_name(old["fighter_a"]) != normalise_name(nb["fighter_a"]):  # same bout, other corner first
            nb["fighter_a"], nb["fighter_b"] = nb["fighter_b"], nb["fighter_a"]
        diff = [k for k in RESULT if nb.get(k) and nb[k] != old.get(k) and k != "event"]
        if any(k in diff for k in ("winner", "method")):
            changed.append({"date": old["date"], "bout": f"{old['fighter_a']} vs {old['fighter_b']}",
                            "was": f"{old.get('winner')} ({old.get('method')})", "now": f"{nb['winner']} ({nb['method']})"})
        for k in RESULT:
            if nb.get(k):
                old[k] = nb[k]
    fights.sort(key=lambda r: r["date"])
    return {"added_fighters": added_fighters, "added_bouts": added, "changed": changed}


def upsert_jsonl(path: Path, records: Iterable[dict], key: str = "url") -> Tuple[int, int]:
    """Replace records with the same key in a JSON-lines file (keeping order); append new ones."""
    recs = {r[key]: r for r in records}
    replaced = 0
    lines: List[str] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            k = json.loads(line).get(key)
            if k in recs:
                lines.append(json.dumps(recs.pop(k), default=str))
                replaced += 1
            else:
                lines.append(line)
    lines += [json.dumps(r, default=str) for r in recs.values()]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return replaced, len(recs)


def stale_batch(n: int, today: date, exclude: Iterable[str] = ()) -> List[str]:
    """Sherdog URLs of exported fighters whose pages were checked longest ago (never = oldest)."""
    if n <= 0:
        return []
    seen = json.loads(REFRESHED.read_text()) if REFRESHED.exists() else {}
    url_of = {r["name"]: r["url"] for r in _read_csv(SHERDOG / "fighters.csv") if r.get("url")}
    exported = json.loads((ROOT / "app" / "data.json").read_text())["fighters"]
    # Recently active first among equals: their records are the ones that change.
    exported.sort(key=lambda f: f.get("layoff_days") or 9999)
    skip = set(exclude)
    urls = [url_of[f["name"]] for f in exported if f["name"] in url_of and url_of[f["name"]] not in skip]
    urls.sort(key=lambda u: seen.get(u, "0000"))
    return urls[:n]


def _fetcher(delay: float):
    from .sources.common import Fetcher

    return Fetcher(ROOT / ".cache" / "pages", delay=delay, user_agent=UA)


def fetch_sherdog(urls: List[str], delay: float, log=print) -> list:
    from .sources import sherdog

    f = _fetcher(delay)
    pages = []
    for i, u in enumerate(urls, 1):
        for attempt in (1, 2):
            try:
                pages.append(sherdog.parse_fighter(f.get(u, cache=False, fresh=True), u))
                break
            except Exception as exc:  # noqa: BLE001 - one bad page shouldn't stop the week
                if attempt == 2:
                    log(f"  skip {u}: {exc}")
        if i % 50 == 0:
            log(f"  {i}/{len(urls)} Sherdog pages")
    return pages


def refresh_fightmatrix(names: List[str], delay: float, log=print) -> Dict[str, int]:
    """Re-fetch the Fight Matrix profiles of these fighters (known profiles only; the monthly
    prospects crawl and the rankings crawl add new ones)."""
    from .sources import fightmatrix
    from .sources.wikipedia import match_key

    path = ROOT / "data" / "fightmatrix" / "profiles.jsonl"
    if not path.exists():
        return {"refreshed": 0, "unknown": len(names)}
    by_key: Dict[str, List[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            by_key.setdefault(match_key(r.get("name", "")), []).append(r["url"])
    f = _fetcher(delay)
    recs, unknown = [], 0
    for n in names:
        urls = by_key.get(match_key(n), [])
        if len(urls) != 1:
            unknown += 1
            continue
        try:
            recs.append(dataclasses.asdict(fightmatrix.parse_profile(f.get(urls[0], cache=False, fresh=True), urls[0])))
        except Exception as exc:  # noqa: BLE001
            log(f"  fightmatrix {n}: {exc}")
    replaced, new = upsert_jsonl(path, recs)
    return {"refreshed": replaced + new, "unknown": unknown}


def refresh_bestfightodds(names: List[str], delay: float, log=print) -> Dict[str, int]:
    """Re-fetch these fighters' BestFightOdds pages: closing lines of the bouts just fought."""
    from .sources import bestfightodds
    from .sources.wikipedia import match_key

    path = ROOT / "data" / "bestfightodds" / "fighters.jsonl"
    by_key: Dict[str, List[str]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                by_key.setdefault(match_key(r.get("name", "")), []).append(r["url"])
    f = _fetcher(delay)
    recs, unknown = [], 0
    for n in names:
        urls = by_key.get(match_key(n), [])
        if len(urls) != 1:
            try:
                hits = bestfightodds.search_results(f.get(bestfightodds.search_url(n), cache=False, fresh=True))
                urls = [u for name, u in hits if match_key(name) == match_key(n)]
            except Exception as exc:  # noqa: BLE001
                log(f"  bestfightodds search {n}: {exc}")
                urls = []
        if len(urls) != 1:
            unknown += 1
            continue
        try:
            bouts = bestfightodds.parse_fighter(f.get(urls[0], cache=False, fresh=True), urls[0])
        except Exception as exc:  # noqa: BLE001
            log(f"  bestfightodds {n}: {exc}")
            continue
        recs.append({"url": urls[0], "name": bouts[0].fighter if bouts else n, "bouts": [dataclasses.asdict(b) for b in bouts]})
    replaced, new = upsert_jsonl(path, recs)
    return {"refreshed": replaced + new, "unknown": unknown}


def refresh_rankings(delay: float, path: Optional[Path] = None) -> Dict[str, object]:
    """The official UFC rankings (Wikipedia's mirror of the media panel, plus its Meta rankings) into
    data/ranked_fighters.json, which the export reads for each fighter's official rank. The UFC re-ranks
    each week after a card, so this runs with every refresh."""
    from .sources import wikipedia

    path = path or ROOT / "data" / "ranked_fighters.json"
    rows = wikipedia.parse_rankings(_fetcher(delay).get(wikipedia.RANKINGS_URL, cache=False, fresh=True))
    if len(rows) < 150:  # a broken or half-loaded page; keep the last good copy
        raise RuntimeError(f"only {len(rows)} ranked fighters parsed")
    old = json.loads(path.read_text()) if path.exists() else {}
    key = lambda r: (r["system"], r["division"], r["rank"], r["name"])  # noqa: E731
    changed = len({key(r) for r in rows} ^ {key(r) for r in old.get("rankings", [])})
    old.update({"rankings": rows, "fetched": date.today().isoformat(), "source": wikipedia.RANKINGS_URL})
    path.write_text(json.dumps(old, ensure_ascii=False, indent=1) + "\n")
    return {"ranked": len(rows), "changed": changed}


def refresh_review(log=print) -> Dict[str, object]:
    """After each UFC card: rebuild the review dataset and re-run the model review (review.py), which refits the
    decision-chance correction and switches method only when another one beats it out of sample; then sweep the
    card's play-by-play and recaps (fight_recaps.py). Skipped when no UFC bout has been added since the last review."""
    from . import review, review_data

    last = json.loads(review.OUT.read_text()).get("through", "") if review.OUT.exists() else ""
    newest = max((r["date"] for r in _read_csv(ROOT / "data" / "verified" / "fights.csv") if r["event"].startswith("UFC")), default="")
    if newest <= last:
        return {"skipped": f"no UFC bout after {last}"}
    out = review.run(review_data.build(log=lambda m: None))
    review.publish(out)
    res = {"through": out["through"], "decision": out["decision"]["chosen"], "switched": out["switched"]}
    # The post-fight play-by-play sweep for the newest recapped card (Sherdog's round-by-round with round scores,
    # MMA Mania's live blog, outlet recaps): the packet the Sunday card review reads, plus the committed index.
    try:
        from . import fight_recaps
        from .sources.common import Fetcher

        ev = (json.loads((ROOT / "app" / "data.json").read_text()).get("recaps") or {}).get("events", [None])[0]
        if ev:
            pk = fight_recaps.collect(ev, Fetcher(ROOT / ".cache" / "pages", delay=1.5, user_agent=UA), log=lambda m: None)
            res["play_by_play"] = {"event": ev["event"], "two_outlets": sum(len({s["outlet"] for s in b["sources"]}) >= 2 for b in pk["bouts"].values()),
                                   "bouts": len(pk["bouts"])}
    except Exception as exc:  # noqa: BLE001 - the review itself already ran
        res["play_by_play"] = {"error": str(exc)[:200]}
    return res


def refresh_kaggle(log=print) -> Dict[str, object]:
    """Re-download the UFCStats scrape; import it only if the dump is newer than ours."""
    from .sources import kaggle_ufc

    out = ROOT / ".cache" / "kaggle"
    out.mkdir(parents=True, exist_ok=True)
    zpath = out / "ufc.zip"
    subprocess.run(["curl", "-sSL", "-o", str(zpath), kaggle_ufc.DOWNLOAD_URL], check=True, timeout=600)
    with zipfile.ZipFile(zpath) as z:
        info = max(z.infolist(), key=lambda i: i.date_time)
        stamp = datetime(*info.date_time).isoformat()
        z.extractall(out)
    marker = ROOT / "data" / "ufcstats" / "kaggle_version.txt"
    have = marker.read_text().strip() if marker.exists() else ""
    if stamp <= have:
        return {"dump": stamp, "imported": False}
    _run(["import", "kaggle", "--dir", str(out), "--out", "data/ufcstats"], log)
    marker.write_text(stamp + "\n")
    return {"dump": stamp, "imported": True}


def _run(args: List[str], log=print, script: bool = False) -> str:
    cmd = [sys.executable] + ([str(ROOT / "scripts" / args[0])] + args[1:] if script else ["-m", "mma_predictor"] + args)
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    tail = (res.stdout or "").strip().splitlines()[-1:] or [""]
    log(f"  {' '.join(args[:2])}: {tail[0][:160]}")
    if res.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed:\n{res.stderr[-2000:]}")
    return res.stdout


def last_bout_date() -> date:
    rows = _read_csv(SHERDOG / "fights.csv")
    return max(date.fromisoformat(r["date"]) for r in rows)


def cmd_refresh(args) -> int:
    from .sources import common, sherdog

    today = date.today()
    since = date.fromisoformat(args.since) if args.since else last_bout_date() - timedelta(days=args.overlap)
    print(f"Refresh {today}: UFC events after {since}, {args.rotate} stale records", flush=True)
    report: Dict[str, object] = {"date": today.isoformat(), "since": since.isoformat()}

    # 1. Sherdog
    f = _fetcher(args.delay)
    recent = sherdog.recent_event_fighters(f, events=12, since=since, fresh=True, log=lambda m: None)
    stale = stale_batch(args.rotate, today, exclude=recent)
    print(f"  {len(recent)} fighters on recent UFC events, {len(stale)} stale records", flush=True)
    pages = fetch_sherdog(recent + stale, args.delay)
    new_f, new_b = common.pages_to_rows(pages, "sherdog")
    fighters, fights = _read_csv(SHERDOG / "fighters.csv"), _read_csv(SHERDOG / "fights.csv")
    before = len(fights)
    merged = merge_rows(fighters, fights, new_f, new_b)
    report["sherdog"] = {"pages": len(pages), "recent_fighters": len(recent), "stale_checked": len(stale),
                         "bouts_before": before, "bouts_added": len(merged["added_bouts"]),
                         "fighters_added": merged["added_fighters"], "results_changed": merged["changed"],
                         "last_bout": max(r["date"] for r in fights)}
    print(f"  +{len(merged['added_bouts'])} bouts, {len(merged['changed'])} results changed, "
          f"last bout {report['sherdog']['last_bout']}", flush=True)
    if args.dry_run:
        print(json.dumps(report, indent=1, default=str))
        return 0
    common.write_dataset(SHERDOG, fighters, fights)
    seen = json.loads(REFRESHED.read_text()) if REFRESHED.exists() else {}
    seen.update({p.url: today.isoformat() for p in pages})
    REFRESHED.write_text(json.dumps(seen, indent=0, sort_keys=True))

    names = [p.name for p in pages if p.url in set(recent)]
    steps = [
        ("ufcstats", lambda: refresh_kaggle()),
        ("statsfight", lambda: {"tail": _run(["crawl_verify_sources.py", "statsfight", "--delay", str(args.delay)], script=True).strip()[-200:]}),
        ("fightmatrix", lambda: refresh_fightmatrix(names, args.delay)),
        ("bestfightodds", lambda: refresh_bestfightodds(names, args.delay)),
        ("enrich", lambda: {"tail": _run(["enrich", "--data", "data/sherdog"]).strip()[-200:]}),
        ("upcoming", lambda: {"tail": _run(["upcoming", "--refresh"]).strip()[-200:]}),
        ("rankings", lambda: refresh_rankings(args.delay)),
        ("verify", lambda: {"tail": _run(["verify"]).strip()[-300:]}),
        ("export", lambda: {"tail": _run(["export"] + EXPORT_ARGS).strip()[-300:]}),
        ("review", lambda: refresh_review()),
    ]
    for name, step in steps:
        if name in (args.skip or []):
            continue
        try:
            report[name] = step()
        except Exception as exc:  # noqa: BLE001 - later steps still run on what we have; the log says what failed
            report[name] = {"error": str(exc)[:500]}
            print(f"  {name} FAILED: {str(exc)[:300]}", flush=True)
    meta = json.loads((ROOT / "app" / "data.json").read_text())["meta"]
    report["export_meta"] = {k: meta.get(k) for k in ("as_of", "last_fight", "bouts", "fighters_exported")}
    report["backtest"] = {k: (meta.get("backtest") or {}).get(k) for k in ("n", "accuracy", "log_loss")}
    report["finished"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(report, default=str) + "\n")
    failed = [k for k, v in report.items() if isinstance(v, dict) and "error" in v]
    print(f"Done: data through {meta.get('last_fight')}, {meta.get('bouts')} bouts, {meta.get('fighters_exported')} fighters"
          + (f"; FAILED: {', '.join(failed)}" if failed else ""), flush=True)
    return 1 if failed else 0


def upcoming_names(days: int, today: Optional[date] = None) -> List[str]:
    """Fighters booked on the UFC cards in app/data.json within the next ``days`` days."""
    today = today or date.today()
    events = json.loads((ROOT / "app" / "data.json").read_text())["upcoming"]["events"]
    names = []
    for e in events:
        if today.isoformat() <= e["date"] <= (today + timedelta(days=days)).isoformat():
            names += [str(b[k]) for b in e.get("bouts", []) if not b.get("decided") for k in ("a", "b")]
    return list(dict.fromkeys(names))


def cmd_odds_sweep(args) -> int:
    """Betting lines only: booked UFC fighters' BestFightOdds pages, the Contender Series weeks, then a re-export."""
    from . import dwcs

    names = upcoming_names(args.days)
    print(f"Odds sweep: {len(names)} fighters on UFC cards in the next {args.days} days", flush=True)
    report = {"bestfightodds": refresh_bestfightodds(names, args.delay)}
    print(f"  UFC: {report['bestfightodds']}", flush=True)
    bfo = dwcs.bfo_lines(dwcs._fetcher(".cache/pages"))
    report["dwcs_changed"] = dwcs.refresh_odds(None, bfo) if bfo else None
    dwcs.export()
    if not args.no_export:
        print(_run(["export"] + EXPORT_ARGS).strip()[-300:], flush=True)
    events = json.loads((ROOT / "app" / "data.json").read_text())["upcoming"]["events"]
    for e in events:
        if e["date"] <= (date.today() + timedelta(days=args.days)).isoformat():
            bs = e.get("bouts", [])
            print(f"  {e['date']} {e['name']}: {sum(1 for b in bs if b.get('market'))}/{len(bs)} bouts priced")
    return 0


def register(sub) -> None:
    p = sub.add_parser("odds-sweep", help="betting lines only: BestFightOdds for upcoming UFC cards and the Contender Series")
    p.add_argument("--days", type=int, default=21, help="UFC cards this many days ahead")
    p.add_argument("--delay", type=float, default=2.0)
    p.add_argument("--no-export", action="store_true", help="skip the app/data.json re-export")
    p.set_defaults(func=cmd_odds_sweep)

    p = sub.add_parser("refresh", help="weekly data refresh: new results, stale records, re-verify, re-export")
    p.add_argument("--since", help="UFC events after this date (default: our last bout minus --overlap days)")
    p.add_argument("--overlap", type=int, default=3)
    p.add_argument("--rotate", type=int, default=150, help="stale exported fighters to re-check")
    p.add_argument("--delay", type=float, default=2.0)
    p.add_argument("--skip", nargs="*", choices=["ufcstats", "statsfight", "fightmatrix", "bestfightodds", "enrich", "upcoming", "verify", "export"])
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_refresh)
