import json

from mma_predictor import refresh


def _setup(tmp_path, monkeypatch, remote):
    (tmp_path / "data" / "ufcstats").mkdir(parents=True)
    (tmp_path / "data" / "ufcstats" / "kaggle_version.txt").write_text("2026-08-11T09:26:18\n")
    (tmp_path / "data" / "ufcstats" / "kaggle_remote.json").write_text(json.dumps({"size": "123", "etag": "x"}))
    monkeypatch.setattr(refresh, "ROOT", tmp_path)
    monkeypatch.setattr(refresh, "_kaggle_remote", remote)
    monkeypatch.setattr(refresh.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("downloaded")))


def test_unchanged_dump_is_not_downloaded(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, lambda url: {"size": "123", "etag": "x"})
    assert refresh.refresh_kaggle() == {"dump": "2026-08-11T09:26:18", "imported": False, "unchanged": True}


def test_unreachable_kaggle_is_skipped_not_failed(tmp_path, monkeypatch):
    def boom(url):
        raise OSError("HTTP Error 429: Too Many Requests")
    _setup(tmp_path, monkeypatch, boom)
    out = refresh.refresh_kaggle()
    assert "error" not in out and "429" in out["skipped"]
