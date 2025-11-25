from typing import Optional
from fastapi import Depends, Request, Response
from fastapi_users import BaseUserManager, UUIDIDMixin
from app.models.users import User
from app.schemas.user import UserCreate
from app.core.config import settings
from app.users.dependencies import get_user_db

SECRET = settings.SECRET_KEY


class UserManager(UUIDIDMixin, BaseUserManager[User, str]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Called after a user registers."""
        print(f"User {user.id} has registered.")

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ):
        """Called after a user logs in."""
        print(f"User {user.id} has logged in.")

    async def oauth_callback(
        self,
        oauth_name: str,
        access_token: str,
        account_id: str,
        account_email: str,
        expires_at: Optional[int] = None,
        refresh_token: Optional[str] = None,
        request: Optional[Request] = None,
        *,
        associate_by_email: bool = False,
        is_verified_by_default: bool = False,
    ) -> User:
        """Handle OAuth callback - create or get user from OAuth data."""
        # Try to find existing user by email
        existing_user = await self.user_db.get_by_email(account_email)

        if existing_user:
            # User exists, return them
            return existing_user

        # Parse name from OAuth (Google provides full name)
        # We'll need to split it into first_name and last_name
        user_create = UserCreate(
            email=account_email,
            password="",  # OAuth users don't have passwords, but field is required
            is_verified=is_verified_by_default,
            first_name=None,
            last_name=None,
        )

        # Create new user
        user = await self.create(user_create, safe=True)
        return user


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
