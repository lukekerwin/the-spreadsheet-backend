"""Google OAuth configuration for fastapi-users."""

from httpx_oauth.clients.google import GoogleOAuth2

from app.core.config import settings

# Google OAuth client (credentials loaded via pydantic settings)
google_oauth_client = GoogleOAuth2(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
)
