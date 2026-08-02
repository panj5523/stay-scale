from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.modules.auth.dependencies import require_admin
from app.modules.auth.models import AdminUser
from app.modules.auth.schemas import AdminLoginResponse, AdminUserResponse
from app.modules.auth.service import AdminAuthService


async def fake_session() -> AsyncIterator[object]:
    yield object()


def test_admin_login_returns_access_token(monkeypatch) -> None:
    async def fake_login(_service, _username, _password):
        return AdminLoginResponse(
            access_token="signed-token",
            expires_in=3600,
            user=AdminUserResponse(
                public_id="admin-001",
                username="admin",
                display_name="项目管理员",
                role="review_admin",
            ),
        )

    monkeypatch.setattr(AdminAuthService, "login", fake_login)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "secure-password"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["access_token"] == "signed-token"


def test_management_queue_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/management/reviews")

    assert response.status_code == 401


def test_current_admin_returns_authenticated_user() -> None:
    user = AdminUser(
        public_id="admin-001",
        username="admin",
        password_hash="not-used",
        display_name="项目管理员",
        role="review_admin",
        status="active",
    )

    async def fake_admin() -> AdminUser:
        return user

    app.dependency_overrides[require_admin] = fake_admin
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/auth/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["username"] == "admin"
