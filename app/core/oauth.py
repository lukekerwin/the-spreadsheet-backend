"""Google OAuth configuration for fastapi-users."""

import os
from httpx_oauth.clients.google import GoogleOAuth2
from dotenv import load_dotenv

# Load environment variables from .env.dev file
load_dotenv(".env.dev")

# Google OAuth client
google_oauth_client = GoogleOAuth2(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
)
