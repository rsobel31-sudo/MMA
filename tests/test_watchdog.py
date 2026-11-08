import json

from mma_predictor import watchdog


def _app(tmp_path, monkeypatch, shards=2):
    app = tmp_path / "app"
    app.mkdir()
    (app / "data.json").write_text(json.dumps({"meta": {"profile_shards": shards}}))
    (app / "engine.js").write_text("x")
    (app / "index.html").write_text("<p>page</p>")
    for i in range(2):
        (app / f"profiles-{i}.json").write_text("{}")
    monkeypatch.setattr(watchdog, "APP", app)
    monkeypatch.setattr(watchdog, "_commits", lambda *a, **k: [])
    return app


def _levels(r):
    return {i["check"]: i["level"] for i in r.items}


def test_published_sizes_match_and_differ(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    sizes = {p.name: p.stat().st_size for p in app.iterdir()}
    sizes["index.html"] += 500  # the host's skeleton
    f = tmp_path / "sizes.json"
    f.write_text(json.dumps(sizes))
    r = watchdog.Report()
    watchdog.check_published(r, f)
    assert _levels(r)["Published page"] == "ok"
    sizes["data.json"] += 7
    del sizes["profiles-1.json"]
    f.write_text(json.dumps(sizes))
    r = watchdog.Report()
    watchdog.check_published(r, f)
    item = r.items[0]
    assert item["level"] == "alert" and "data.json stale" in item["detail"] and "profiles-1.json missing" in item["detail"]


def test_published_folder_compares_bytes(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    live = tmp_path / "live"
    live.mkdir()
    for p in app.iterdir():
        (live / p.name).write_bytes(p.read_bytes())
    r = watchdog.Report()
    watchdog.check_published(r, live)
    assert _levels(r)["Published page"] == "ok"
    (live / "engine.js").write_text("y")
    r = watchdog.Report()
    watchdog.check_published(r, live)
    assert "engine.js stale" in r.items[0]["detail"]


def test_shard_count_and_size_limit(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, shards=3)
    r = watchdog.Report()
    watchdog.check_files(r)
    assert _levels(r)["Profile files"] == "alert"
    with open(app / "profiles-0.json", "wb") as fh:
        fh.truncate(15_500_000)
    r = watchdog.Report()
    watchdog.check_files(r)
    assert _levels(r)["File sizes"] == "alert"


def test_ufc_stats_lag(tmp_path, monkeypatch):
    from datetime import datetime
    root = tmp_path
    (root / "data" / "ufcstats").mkdir(parents=True)
    (root / "data" / "card_picks").mkdir(parents=True)
    (root / "data" / "ufcstats" / "fights.csv").write_text("date,event\n2026-08-08,A\n")
    for d in ("2026-08-01", "2026-10-31", "2026-11-07"):
        (root / "data" / "card_picks" / f"{d}-card.json").write_text("{}")
    monkeypatch.setattr(watchdog, "ROOT", root)
    r = watchdog.Report()
    watchdog.check_ufc_stats(r, datetime(2026, 11, 8, 9, tzinfo=watchdog.ET))
    assert r.items[0]["level"] == "warn" and "at least 2 UFC card" in r.items[0]["detail"]
