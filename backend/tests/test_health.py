from fastapi.testclient import TestClient

from app.api.v1 import health
from app.main import app


def test_liveness() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_when_dependencies_are_available(monkeypatch) -> None:
    async def available_database() -> health.ComponentCheck:
        return health.ComponentCheck(status="up", message="MySQL 连接正常")

    async def available_redis() -> health.ComponentCheck:
        return health.ComponentCheck(status="up", message="Redis 连接正常")

    monkeypatch.setattr(health, "check_database", available_database)
    monkeypatch.setattr(health, "check_redis", available_redis)

    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_when_database_is_unavailable(monkeypatch) -> None:
    async def unavailable_database() -> health.ComponentCheck:
        return health.ComponentCheck(status="down", message="MySQL 连接失败")

    async def available_redis() -> health.ComponentCheck:
        return health.ComponentCheck(status="up", message="Redis 连接正常")

    monkeypatch.setattr(health, "check_database", unavailable_database)
    monkeypatch.setattr(health, "check_redis", available_redis)

    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"]["database"]["status"] == "down"
