"""Watchdog: is every Fight Lab routine running on time, pushing, and publishing what it pushed?

Each scheduled job leaves a trace in the pushed branch (a commit, a log line, a file), so lateness is read from
origin, not from the routines' own reports. Times are US Eastern, matching the routines' schedules:

  daily sweep          06:53 daily        commit "Daily sweep..." and a data/refresh_log.jsonl line
  minor leagues        07:41 daily        commit "Minor Leagues..." (only when the files changed)
  odds sweep           12:47, 18:47 Wed-Sat  commit touching data/bestfightodds (only when lines changed)
  scouting             11:58 Tuesday      a scouting commit and the next card's players' board
  AI Picks (Friday)    11:59 Friday       picks locked for Saturday's card before it locks
  AI Picks (Sunday)    11:59 Sunday       card graded, play-by-play recaps written, data through the card
  prospects            11:57 on the 1st   data/prospects/reports/<month>.json

Also: data/health.json (failed sources), refresh steps that errored, files near the page host's 16 MB limit, profile
shards matching meta.profile_shards, and, with --published DIR (the artifact's files downloaded there), every page file
matching the pushed copy.

    python -m mma_predictor watchdog [--published DIR] [--now 2026-10-21T09:30] [--json .cache/watchdog.json]

Exit code 1 when anything is an alert.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import List, Optional
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
BRANCH = "claude/mma-fight-predictor-9sxxhl"
ET = ZoneInfo("America/New_York")
LIMIT_MB, WARN_MB = 16.0, 15.0
# Page files a publish carries; index.html is compared separately (the host wraps it).
PAGE_FILES = ("engine.js", "data.json", "prospects.json", "dwcs.json", "review.json", "rank_moves.json",
              "minor_leagues.json", "opponents.json")


class Report:
    def __init__(self):
        self.items: List[dict] = []

    def add(self, check: str, level: str, detail: str):
        self.items.append({"check": check, "level": level, "detail": detail})

    def ok(self, check, detail=""): self.add(check, "ok", detail)
    def warn(self, check, detail): self.add(check, "warn", detail)
    def alert(self, check, detail): self.add(check, "alert", detail)


def _commits(since: datetime, until: Optional[datetime] = None, path: Optional[str] = None) -> List[tuple]:
    """(commit time, subject) on origin's branch since `since` (aware datetimes), newest first."""
    ref = f"origin/{BRANCH}"
    if subprocess.run(["git", "rev-parse", "--verify", "-q", ref], cwd=ROOT, capture_output=True).returncode:
        ref = "HEAD"
    cmd = ["git", "log", ref, f"--since={since.isoformat()}", "--format=%cI%x09%s"]
    if until:
        cmd.append(f"--until={until.isoformat()}")
    if path:
        cmd += ["--", path]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        t, _, s = line.partition("\t")
        rows.append((datetime.fromisoformat(t), s))
    return rows


def _at(d: date, hh: int, mm: int = 0) -> datetime:
    return datetime.combine(d, time(hh, mm), tzinfo=ET)


def _last_weekday(now: datetime, weekday: int, due: time) -> Optional[date]:
    """The most recent date with this weekday (Mon=0) whose `due` time has passed, within the last 7 days."""
    for back in range(0, 8):
        d = (now - timedelta(days=back)).date()
        if d.weekday() == weekday and now >= datetime.combine(d, due, tzinfo=ET):
            return d
    return None


def _ago(now: datetime, t: datetime) -> str:
    h = (now - t).total_seconds() / 3600
    return f"{h:.0f}h ago" if h < 48 else f"{h / 24:.1f} days ago"


def _card_file(d: date) -> Optional[Path]:
    hits = sorted((ROOT / "data" / "card_picks").glob(f"{d.isoformat()}-*.json"))
    return hits[0] if hits else None


def _upcoming_card(on: date) -> Optional[dict]:
    p = ROOT / "data" / "upcoming.json"
    if not p.exists():
        return None
    for e in json.loads(p.read_text()).get("events", []):
        if e.get("date") == on.isoformat():
            return e
    return None


def check_daily(r: Report, now: datetime):
    today = now.date()
    day = today if now >= _at(today, 9, 15) else today - timedelta(days=1)
    hits = [c for c in _commits(_at(day, 5)) if c[1].lower().startswith("daily sweep") and c[0] < _at(day + timedelta(days=1), 5)]
    if hits:
        r.ok("Daily sweep", f"{day}: pushed {hits[-1][0].astimezone(ET):%H:%M} ET")
    else:
        r.alert("Daily sweep", f"no daily sweep commit for {day} (due 06:53 ET, checked after 09:15 ET)")
    log = ROOT / "data" / "refresh_log.jsonl"
    if log.exists():
        last = json.loads(log.read_text().strip().splitlines()[-1])
        fin = datetime.fromisoformat(last["finished"])
        failed = [k for k, v in last.items() if isinstance(v, dict) and "error" in v]
        if failed:
            r.alert("Data refresh", f"run {last.get('date')} failed: " + "; ".join(f"{k}: {last[k]['error'][:120]}" for k in failed))
        elif now - fin > timedelta(hours=30):
            r.alert("Data refresh", f"last refresh finished {_ago(now, fin)}")
        else:
            r.ok("Data refresh", f"finished {_ago(now, fin)}, data through {(last.get('export_meta') or {}).get('last_fight')}")
    hits = [c for c in _commits(now - timedelta(hours=36)) if "minor leagues" in c[1].lower()]
    if hits:
        r.ok("Minor Leagues refresh", f"pushed {_ago(now, hits[0][0])}")
    else:
        r.warn("Minor Leagues refresh", "no Minor Leagues commit in 36h (it skips the commit only when nothing changed)")


def check_health(r: Report, now: datetime):
    p = ROOT / "data" / "health.json"
    if not p.exists():
        return r.alert("Source health", "data/health.json missing")
    h = json.loads(p.read_text())
    checked = datetime.fromisoformat(h["checked"])
    if h.get("failed"):
        fails = [s for s in h.get("sources", []) if not s.get("ok")]
        r.alert("Source health", "; ".join(f"{s['source']}: {s.get('detail', '')[:100]} (last ok {s.get('last_ok')})" for s in fails)
                or ", ".join(h["failed"]))
    elif now - checked > timedelta(hours=30):
        r.alert("Source health", f"last checked {_ago(now, checked)}")
    else:
        r.ok("Source health", f"all sources ok, checked {_ago(now, checked)}")


def check_odds(r: Report, now: datetime):
    if now.weekday() not in (2, 3, 4, 5, 6) or (now.weekday() == 2 and now < _at(now.date(), 19, 30)):
        return
    hits = _commits(now - timedelta(hours=30), path="data/bestfightodds")
    if hits:
        r.ok("Odds sweep", f"lines pushed {_ago(now, hits[0][0])}")
    else:
        r.warn("Odds sweep", "no betting-line commit in 30h during fight week")


def check_scouting(r: Report, now: datetime):
    tue = _last_weekday(now, 1, time(15, 0))
    if not tue:
        return
    hits = [c for c in _commits(_at(tue, 11), _at(tue, 23, 59)) if "scout" in c[1].lower() or "tuesday" in c[1].lower()]
    if hits:
        r.ok("Tuesday scouting", f"{tue}: pushed {hits[-1][0].astimezone(ET):%H:%M} ET")
    else:
        r.alert("Tuesday scouting", f"no scouting commit on {tue} (due 11:58 ET)")
    sat = tue + timedelta(days=4)
    if _upcoming_card(sat) or _card_file(sat):
        boards = sorted((ROOT / "data" / "ai_picks" / "boards").glob(f"{sat.isoformat()}-*.json"))
        if boards:
            r.ok("Players' board", f"{boards[-1].stem}")
        else:
            r.alert("Players' board", f"no board for the {sat} card (Tuesday's run publishes it)")


def check_friday(r: Report, now: datetime):
    fri = _last_weekday(now, 4, time(15, 30))
    if not fri:
        return
    sat = fri + timedelta(days=1)
    if now.date() > sat + timedelta(days=1):
        return  # Sunday's checks take over
    ev = _upcoming_card(sat)
    f = _card_file(sat)
    if not f:
        if ev or any((ROOT / "data" / "ai_picks" / "boards").glob(f"{sat.isoformat()}-*.json")):
            r.alert("Friday AI Picks", f"no locked picks for the {sat} card ({ev['name'] if ev else 'card'}) (due Friday 11:59 ET)")
        return
    d = json.loads(f.read_text())
    if not d.get("locked_at"):
        r.alert("Friday AI Picks", f"{d.get('event')}: picks not locked")
    else:
        r.ok("Friday AI Picks", f"{d.get('event')}: locked {d['locked_at']}")
    ledger = json.loads((ROOT / "data" / "ai_picks" / "ledger.json").read_text())
    if any(w.get("event_date") == sat.isoformat() for w in ledger.get("weeks", [])):
        r.ok("Friday AI Bets", f"{sat}: bets or pass recorded")
    else:
        r.alert("Friday AI Bets", f"no AI Bets entry (bets or a recorded pass) for the {sat} card")


def check_sunday(r: Report, now: datetime):
    sun = _last_weekday(now, 6, time(16, 0))
    if not sun:
        return
    sat = sun - timedelta(days=1)
    f = _card_file(sat)
    if not f:
        return  # no UFC card that weekend
    d = json.loads(f.read_text())
    if d.get("graded"):
        r.ok("Sunday grading", f"{d.get('event')}: graded")
    else:
        r.alert("Sunday grading", f"{d.get('event')}: AI Picks not graded (due Sunday 11:59 ET)")
    ledger = json.loads((ROOT / "data" / "ai_picks" / "ledger.json").read_text())
    open_bets = [w for w in ledger.get("weeks", []) if w.get("event_date") == sat.isoformat() and not w.get("settled")]
    if open_bets and any("settled" in w for w in ledger.get("weeks", [])):
        r.alert("Sunday settling", f"AI Bets for {sat} not settled")
    recaps = sorted((ROOT / "data" / "scouting" / "recaps").glob(f"{sat.isoformat()}-*.json"))
    if not recaps:
        r.alert("Play-by-play recaps", f"no recap file for the {sat} card")
    else:
        rec = json.loads(recaps[0].read_text())
        n, bouts = len(rec.get("stories") or {}), len(d.get("bouts") or [])
        (r.ok if n >= bouts else r.warn)("Play-by-play recaps", f"{rec.get('event')}: {n}/{bouts} fights written up")
    meta = json.loads((APP / "data.json").read_text())["meta"]
    if (meta.get("last_fight") or "") < sat.isoformat():
        r.alert("Data through last card", f"data.json runs through {meta.get('last_fight')}, card was {sat}")
    snaps = sorted((ROOT / "data" / "rankings" / "snapshots").glob("*.json"))
    if not snaps or snaps[-1].stem < sat.isoformat():
        r.alert("Ranking movement", f"no rankings snapshot since the {sat} card")


def check_monthly(r: Report, now: datetime):
    first = now.date().replace(day=1)
    if now < _at(first, 17) or first < date(2026, 11, 1):
        return
    rep = ROOT / "data" / "prospects" / "reports" / f"{first:%Y-%m}.json"
    if rep.exists():
        r.ok("Monthly prospects", f"{rep.name} written")
    else:
        r.alert("Monthly prospects", f"no prospects report for {first:%B %Y} (due the 1st, 11:57 ET)")


def check_files(r: Report):
    meta = json.loads((APP / "data.json").read_text())["meta"]
    shards = sorted(APP.glob("profiles-*.json"))
    n = meta.get("profile_shards")
    if n and len(shards) != n:
        r.alert("Profile files", f"data.json expects {n} profile files, app/ has {len(shards)}")
    big = []
    for p in sorted(APP.glob("*")):
        mb = p.stat().st_size / 1e6
        if mb >= WARN_MB:
            big.append(f"{p.name} {mb:.1f} MB")
    if big:
        r.alert("File sizes", "near or over the 16 MB page limit (publishes would silently keep the old copy): " + ", ".join(big))
    else:
        r.ok("File sizes", "all page files under 15 MB")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_published(r: Report, pub: Path):
    """`pub` is a folder of the artifact's downloaded files (compared byte for byte) or a JSON file of
    {published path: bytes} from the artifact's file listing (compared by size; cheap, and a changed data file
    almost always changes size). The host wraps index.html in a small skeleton, so it may be up to 2 KB larger."""
    names = list(PAGE_FILES) + [p.name for p in sorted(APP.glob("profiles-*.json"))]
    sizes = json.loads(pub.read_text()) if pub.is_file() else None
    stale, missing = [], []
    for n in names:
        local = APP / n
        if not local.exists():
            continue
        if sizes is not None:
            if n not in sizes:
                missing.append(n)
            elif int(sizes[n]) != local.stat().st_size:
                stale.append(n)
        elif not (pub / n).exists():
            missing.append(n)
        elif _sha(local) != _sha(pub / n):
            stale.append(n)
    if sizes is not None and "index.html" in sizes:
        extra = int(sizes["index.html"]) - (APP / "index.html").stat().st_size
        if not 0 <= extra <= 2000:
            stale.append("index.html")
    detail = ""
    if sizes is None and "data.json" in stale:
        try:
            lm = json.loads((pub / "data.json").read_text())["meta"]
            detail = f"; live data.json is as of {lm.get('as_of')} (through {lm.get('last_fight')})"
        except Exception:  # noqa: BLE001 - only for the message
            pass
    recent = _commits(datetime.now(timezone.utc) - timedelta(minutes=45), path="app")
    if (stale or missing) and recent:
        r.warn("Published page", "differs from the files pushed " + _ago(datetime.now(timezone.utc), recent[0][0])
               + " (a routine may still be publishing): " + ", ".join(stale + missing))
    elif stale or missing:
        r.alert("Published page", "live page differs from the pushed files: "
                + ", ".join([f"{n} stale" for n in stale] + [f"{n} missing" for n in missing]) + detail)
    else:
        r.ok("Published page", f"all {len(names)} page files match the pushed copy")


def run(now: Optional[datetime] = None, published: Optional[Path] = None) -> Report:
    now = (now or datetime.now(timezone.utc)).astimezone(ET)
    r = Report()
    for fn in (check_daily, check_health, check_odds, check_scouting, check_friday, check_sunday, check_monthly):
        try:
            fn(r, now)
        except Exception as exc:  # noqa: BLE001 - a broken check is itself an alert
            r.alert(fn.__name__, f"check failed: {exc}")
    check_files(r)
    if published:
        check_published(r, published)
    return r


def cmd_watchdog(args) -> int:
    now = datetime.fromisoformat(args.now).replace(tzinfo=ET) if args.now else None
    r = run(now, Path(args.published) if args.published else None)
    for it in r.items:
        print(f"[{it['level'].upper():5}] {it['check']}: {it['detail']}")
    alerts = [i for i in r.items if i["level"] == "alert"]
    out = {"checked": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
           "alerts": len(alerts), "warnings": sum(i["level"] == "warn" for i in r.items), "items": r.items}
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(out, indent=1))
    print(f"{len(alerts)} alert(s), {out['warnings']} warning(s)")
    return 1 if alerts else 0


def register(sub) -> None:
    p = sub.add_parser("watchdog", help="are the routines on time, pushed and published?")
    p.add_argument("--published", help="the live artifact's files: a folder of them, or a JSON {path: bytes} from its file listing")
    p.add_argument("--now", help="pretend it is this ET time (ISO), for testing")
    p.add_argument("--json", help="also write the report here")
    p.set_defaults(func=cmd_watchdog)
