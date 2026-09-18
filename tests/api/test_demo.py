"""The public demo must stay separate and must not contact live integrations."""

import importlib.util
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from src.api import main


def test_demo_refuses_existing_unmarked_data(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "atelier_demo", Path(__file__).parents[2] / "scripts/run_demo.py"
    )
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    sentinel = tmp_path / "private-records.txt"
    sentinel.write_text("preserve this existing collection")
    with pytest.raises(SystemExit, match="non-demo"):
        demo.prepare_directory(tmp_path)
    assert sentinel.read_text() == "preserve this existing collection"
    assert not (tmp_path / ".atelier-demo").exists()


def test_demo_blocks_external_actions_before_routes_run(monkeypatch):
    monkeypatch.setattr(main.settings, "demo_mode", True)

    async def skip_init():
        pass

    monkeypatch.setattr(main, "init_db", skip_init)
    with TestClient(main.app) as client:
        for method, path in [
            ("POST", "/api/gmail/send"),
            ("GET", "/api/gmail/auth-url"),
            ("POST", "/api/alerts/searches/1/run"),
            ("POST", "/api/alerts/searches/run-all"),
            ("POST", "/api/scrape/background"),
            ("POST", "/api/images/download"),
        ]:
            response = client.request(method, path)
            assert response.status_code == 403
            assert "synthetic demo" in response.json()["detail"]
        status = client.get("/api/gmail/status").json()
        assert status["authenticated"] is False
        assert status["configured"] is False


def test_demo_labels_and_biography_do_not_claim_real_artist(monkeypatch):
    monkeypatch.setattr(main.settings, "demo_mode", True)
    for key, value in {
        "demo_mode": True,
        "collection_name": "Atelier Studio",
        "collection_dates": "Sample collection",
    }.items():
        monkeypatch.setitem(main.templates.env.globals, key, value)

    async def skip_init():
        pass

    monkeypatch.setattr(main, "init_db", skip_init)
    with TestClient(main.app) as client:
        for path in ["/", "/timeline", "/about", "/frame"]:
            response = client.get(path)
            assert response.status_code == 200
            assert "Dan Brown" not in response.text
            assert "DEMO COLLECTION" in response.text
        assert "const lifeEvents = []" in client.get("/timeline").text
