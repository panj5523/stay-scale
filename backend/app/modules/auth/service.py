from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import AdminUser
from app.modules.auth.schemas import AdminLoginResponse, AdminUserResponse
from app.modules.auth.security import create_access_token, verify_password


class AdminAuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def login(self, username: str, password: str) -> AdminLoginResponse | None:
        user = await self.session.scalar(
            select(AdminUser).where(
                AdminUser.username == username.strip().lower(),
                AdminUser.status == "active",
            )
        )
        if user is None or not verify_password(password, user.password_hash):
            return None
        user.last_login_at = datetime.now(UTC).replace(tzinfo=None)
        token, expires_in = create_access_token(subject=user.public_id, role=user.role)
        await self.session.commit()
        return AdminLoginResponse(
            access_token=token,
            expires_in=expires_in,
            user=self._response(user),
        )

    @staticmethod
    def _response(user: AdminUser) -> AdminUserResponse:
        return AdminUserResponse(
            public_id=user.public_id,
            username=user.username,
            display_name=user.display_name,
            role=user.role,
        )
