import argparse
import asyncio
import getpass
from uuid import uuid4

from sqlalchemy import select

from app.core.config import settings
from app.db.session import async_session_factory, engine
from app.modules.auth.models import AdminUser
from app.modules.auth.security import hash_password


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or reset a Stay Scale administrator")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--display-name", default="项目管理员")
    parser.add_argument("--role", choices=("review_admin", "super_admin"), default="review_admin")
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    password = settings.admin_initial_password or getpass.getpass("Administrator password: ")
    if len(password) < 8:
        raise ValueError("Administrator password must contain at least 8 characters")
    username = args.username.strip().lower()
    async with async_session_factory() as session:
        user = await session.scalar(select(AdminUser).where(AdminUser.username == username))
        if user is None:
            user = AdminUser(
                public_id=str(uuid4()),
                username=username,
                display_name=args.display_name.strip(),
                role=args.role,
                status="active",
                password_hash=hash_password(password),
            )
            session.add(user)
            action = "created"
        else:
            user.password_hash = hash_password(password)
            user.display_name = args.display_name.strip()
            user.role = args.role
            user.status = "active"
            action = "updated"
        await session.commit()
        print(f"Administrator {username!r} {action} with role {args.role}.")


async def main() -> None:
    try:
        await run()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
