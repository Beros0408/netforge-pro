"""
User service for business logic.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User, UserCreate, UserDB, UserInDB, UserUpdate
from ..utils.auth import get_password_hash, verify_password


class UserService:
    """
    Service for user operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        """
        query = select(UserDB).where(UserDB.id == user_id)
        result = await self.db.execute(query)
        user_db = result.scalar_one_or_none()
        if user_db:
            return User.from_orm(user_db)
        return None

    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """
        Get user by username.
        """
        query = select(UserDB).where(UserDB.username == username)
        result = await self.db.execute(query)
        user_db = result.scalar_one_or_none()
        if user_db:
            return UserInDB.from_orm(user_db)
        return None

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Get user by email.
        """
        query = select(UserDB).where(UserDB.email == email)
        result = await self.db.execute(query)
        user_db = result.scalar_one_or_none()
        if user_db:
            return UserInDB.from_orm(user_db)
        return None

    async def create_user(self, user: UserCreate) -> User:
        """
        Create a new user.
        """
        hashed_password = get_password_hash(user.password)
        user_db = UserDB(
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            hashed_password=hashed_password,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
        )
        self.db.add(user_db)
        await self.db.commit()
        await self.db.refresh(user_db)
        return User.from_orm(user_db)

    async def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """
        Update an existing user.
        """
        query = select(UserDB).where(UserDB.id == user_id)
        result = await self.db.execute(query)
        user_db = result.scalar_one_or_none()
        if not user_db:
            return None

        update_data = user_update.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(user_db, field, value)

        await self.db.commit()
        await self.db.refresh(user_db)
        return User.from_orm(user_db)

    async def delete_user(self, user_id: int) -> bool:
        """
        Delete a user.
        """
        query = select(UserDB).where(UserDB.id == user_id)
        result = await self.db.execute(query)
        user_db = result.scalar_one_or_none()
        if not user_db:
            return False

        await self.db.delete(user_db)
        await self.db.commit()
        return True

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user.
        """
        user = await self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return User.from_orm(user)