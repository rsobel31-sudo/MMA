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
