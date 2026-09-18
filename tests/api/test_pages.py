"""Public setup must render its pages with the installed template API."""
import pytest
from fastapi.testclient import TestClient
from src.api import main


@pytest.mark.parametrize("path", [
    "/", "/about", "/timeline", "/outreach", "/discovery", "/display", "/frame",
    "/artwork/1",
])
def test_page_template_renders_without_private_state(monkeypatch, path):
    async def skip_database_initialization():
        pass

    monkeypatch.setattr(main, "init_db", skip_database_initialization)
    with TestClient(main.app) as client:
        response = client.get(path)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text
