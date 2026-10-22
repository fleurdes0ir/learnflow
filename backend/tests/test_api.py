import pytest
from fastapi.testclient import TestClient

from app.db import session as db
from app.main import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


def test_healthz_ok(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_careers_returns_three_enum_roles(client: TestClient) -> None:
    r = client.get("/api/v1/meta/careers")
    assert r.status_code == 200
    body = r.json()
    assert body["careers"] == ["Backend Developer", "Data Scientist", "DevOps Engineer"]
    assert body["count"] == 3


def test_cors_allows_local_frontend(client: TestClient) -> None:
    r = client.options(
        "/api/v1/meta/careers",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_blocks_unknown_origin(client: TestClient) -> None:
    r = client.get("/healthz", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_readyz_503_when_db_down(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_down() -> bool:
        return False

    monkeypatch.setattr(db, "check_db", fake_down)
    r = client.get("/readyz")
    assert r.status_code == 503
    assert r.json() == {"status": "not_ready", "database": "down"}


def test_readyz_200_when_db_up(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_up() -> bool:
        return True

    monkeypatch.setattr(db, "check_db", fake_up)
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "database": "up"}
