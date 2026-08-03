import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.security import create_user_access_token, hash_password, verify_password
from app.modules.listings.models import CanonicalListing

from .models import UserAccount, UserFavorite
from .schemas import FavoriteResponse, UserLoginResponse, UserResponse


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register(self, email: str, password: str, display_name: str) -> UserLoginResponse:
        normalized = email.strip().lower()
        if await self.session.scalar(select(UserAccount.id).where(UserAccount.email == normalized)):
            raise ValueError("Email is already registered")
        user = UserAccount(
            public_id=str(uuid.uuid4()),
            email=normalized,
            password_hash=hash_password(password),
            display_name=display_name.strip(),
            status="active",
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return self._login_response(user)

    async def login(self, email: str, password: str) -> UserLoginResponse | None:
        user = await self.session.scalar(
            select(UserAccount).where(
                UserAccount.email == email.strip().lower(), UserAccount.status == "active"
            )
        )
        if user is None or not verify_password(password, user.password_hash):
            return None
        user.last_login_at = datetime.now(UTC).replace(tzinfo=None)
        await self.session.commit()
        return self._login_response(user)

    async def list_favorites(self, user: UserAccount) -> list[FavoriteResponse]:
        rows = (
            await self.session.execute(
                select(UserFavorite, CanonicalListing)
                .join(CanonicalListing, CanonicalListing.id == UserFavorite.canonical_listing_id)
                .where(UserFavorite.user_id == user.id)
                .order_by(UserFavorite.created_at.desc())
            )
        ).all()
        return [
            FavoriteResponse(
                listing_public_id=listing.public_id,
                name=listing.name,
                city=listing.city,
                district=listing.district,
                created_at=favorite.created_at,
            )
            for favorite, listing in rows
        ]

    async def add_favorite(self, user: UserAccount, listing_public_id: str) -> FavoriteResponse:
        listing = await self.session.scalar(
            select(CanonicalListing).where(
                CanonicalListing.public_id == listing_public_id, CanonicalListing.status == "active"
            )
        )
        if listing is None:
            raise FileNotFoundError("Listing not found")
        favorite = await self.session.scalar(
            select(UserFavorite).where(
                UserFavorite.user_id == user.id, UserFavorite.canonical_listing_id == listing.id
            )
        )
        if favorite is None:
            favorite = UserFavorite(user_id=user.id, canonical_listing_id=listing.id)
            self.session.add(favorite)
            await self.session.commit()
            await self.session.refresh(favorite)
        return FavoriteResponse(
            listing_public_id=listing.public_id,
            name=listing.name,
            city=listing.city,
            district=listing.district,
            created_at=favorite.created_at,
        )

    async def remove_favorite(self, user: UserAccount, listing_public_id: str) -> None:
        favorite = await self.session.scalar(
            select(UserFavorite)
            .join(CanonicalListing, CanonicalListing.id == UserFavorite.canonical_listing_id)
            .where(UserFavorite.user_id == user.id, CanonicalListing.public_id == listing_public_id)
        )
        if favorite is not None:
            await self.session.delete(favorite)
            await self.session.commit()

    @staticmethod
    def response(user: UserAccount) -> UserResponse:
        return UserResponse(
            public_id=user.public_id, email=user.email, display_name=user.display_name
        )

    @classmethod
    def _login_response(cls, user: UserAccount) -> UserLoginResponse:
        token, expires_in = create_user_access_token(subject=user.public_id)
        return UserLoginResponse(access_token=token, expires_in=expires_in, user=cls.response(user))
