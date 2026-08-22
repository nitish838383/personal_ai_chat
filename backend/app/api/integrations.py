"""
Connected Apps / Integrations API.
OAuth tokens are stored only on the backend and never returned to the frontend.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from urllib.parse import urlencode
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.models.connected_account import ConnectedAccount


router = APIRouter(prefix="/integrations", tags=["Integrations"])


SUPPORTED_PROVIDERS = [
    "gmail",
    "google_calendar",
    "google_drive",
    "slack",
    "notion",
    "whatsapp",
]


class IntegrationStatus(BaseModel):
    provider: str
    connected: bool
    account_email: Optional[str] = None
    account_name: Optional[str] = None
    is_active: bool = False


class ConnectResponse(BaseModel):
    authorization_url: Optional[str] = None
    message: str
    provider: str


# ---------------------------------------------------------------------------
# LIST CONNECTED APPS
# ---------------------------------------------------------------------------

@router.get("", response_model=List[IntegrationStatus])
async def list_integrations(
    current_user: CurrentUser,
    db: DbSession,
):
    """Return connection status for the current user. Tokens are never returned."""

    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == current_user.id
        )
    )

    accounts = {
        account.provider: account
        for account in result.scalars().all()
    }

    statuses = []

    for provider in SUPPORTED_PROVIDERS:
        account = accounts.get(provider)

        statuses.append(
            IntegrationStatus(
                provider=provider,
                connected=bool(account and account.is_active),
                account_email=account.account_email if account else None,
                account_name=account.account_name if account else None,
                is_active=bool(account and account.is_active),
            )
        )

    return statuses


# ---------------------------------------------------------------------------
# CONNECT PROVIDER
# ---------------------------------------------------------------------------

@router.post("/{provider}/connect", response_model=ConnectResponse)
async def connect_provider(
    provider: str,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Start OAuth connection for the current logged-in user.
    """

    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}",
        )

    # -----------------------------------------------------------------------
    # WhatsApp
    # -----------------------------------------------------------------------

    if provider == "whatsapp":
        return ConnectResponse(
            provider=provider,
            message=(
                "WhatsApp Business API integration is planned. "
                "Requires official WhatsApp Business account and credentials."
            ),
            authorization_url=None,
        )

    # -----------------------------------------------------------------------
    # Google: Gmail / Calendar / Drive
    # -----------------------------------------------------------------------

    if provider in (
        "gmail",
        "google_calendar",
        "google_drive",
    ):

        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            return ConnectResponse(
                provider=provider,
                message=(
                    "Google OAuth is not configured. "
                    "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
                    "in the backend environment variables."
                ),
                authorization_url=None,
            )

        scopes = {
            "gmail": "https://www.googleapis.com/auth/gmail.readonly",
            "google_calendar": "https://www.googleapis.com/auth/calendar",
            "google_drive": "https://www.googleapis.com/auth/drive.readonly",
        }

        # IMPORTANT:
        # state carries the provider + logged-in user's UUID.
        # Example:
        # gmail:550e8400-e29b-41d4-a716-446655440000

        state = f"{provider}:{current_user.id}"

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": scopes[provider],
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }

        authorization_url = (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            + urlencode(params)
        )

        return ConnectResponse(
            provider=provider,
            message="Redirect the user to authorization_url to complete Google OAuth.",
            authorization_url=authorization_url,
        )

    # -----------------------------------------------------------------------
    # Notion
    # -----------------------------------------------------------------------

    if provider == "notion":

        if not settings.NOTION_CLIENT_ID:
            return ConnectResponse(
                provider=provider,
                message=(
                    "Notion OAuth is not configured. "
                    "Set NOTION_CLIENT_ID and NOTION_CLIENT_SECRET."
                ),
                authorization_url=None,
            )

        return ConnectResponse(
            provider=provider,
            message="Notion OAuth ready when credentials are set.",
            authorization_url=None,
        )

    # -----------------------------------------------------------------------
    # Slack
    # -----------------------------------------------------------------------

    if provider == "slack":

        if not settings.SLACK_CLIENT_ID:
            return ConnectResponse(
                provider=provider,
                message=(
                    "Slack OAuth is not configured. "
                    "Set SLACK_CLIENT_ID and SLACK_CLIENT_SECRET."
                ),
                authorization_url=None,
            )

        return ConnectResponse(
            provider=provider,
            message="Slack OAuth ready when credentials are set.",
            authorization_url=None,
        )

    return ConnectResponse(
        provider=provider,
        message="Provider not implemented yet.",
        authorization_url=None,
    )


# ---------------------------------------------------------------------------
# GOOGLE OAUTH CALLBACK
# ---------------------------------------------------------------------------

@router.get("/google/callback")
async def google_callback(
    db: DbSession,
    code: str = "",
    state: str = "",
    error: str = "",
):
    """
    Google OAuth callback.

    Google sends:
        ?code=XXXX&state=gmail:<user_uuid>

    The authorization code is exchanged for access/refresh tokens.
    Tokens are stored against the correct Personal AI OS user.
    """

    # Google returned an OAuth error
    if error:
        return {
            "status": "error",
            "detail": error,
        }

    # No authorization code
    if not code:
        return {
            "status": "error",
            "detail": "Missing authorization code",
        }

    # -----------------------------------------------------------------------
    # Validate state
    # -----------------------------------------------------------------------

    if not state:
        raise HTTPException(
            status_code=400,
            detail="Missing OAuth state",
        )

    try:
        provider, user_id_string = state.split(":", 1)
        user_id = UUID(user_id_string)

    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state",
        )

    if provider not in (
        "gmail",
        "google_calendar",
        "google_drive",
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid Google provider",
        )

    # -----------------------------------------------------------------------
    # Exchange authorization code for Google tokens
    # -----------------------------------------------------------------------

    token_url = "https://oauth2.googleapis.com/token"

    token_data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:

        token_response = await client.post(
            token_url,
            data=token_data,
        )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail="Google token exchange failed",
        )

    tokens = token_response.json()

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_in = tokens.get("expires_in")
    token_scope = tokens.get("scope")

    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="Google did not return an access token",
        )

    # -----------------------------------------------------------------------
    # Get Google account information
    # -----------------------------------------------------------------------

    async with httpx.AsyncClient(timeout=30.0) as client:
     profile_response = await client.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/profile",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
    )

    if profile_response.status_code != 200:
        raise HTTPException(
        status_code=profile_response.status_code,
        detail={
            "message": "Could not fetch Gmail account information",
            "google_status": profile_response.status_code,
            "google_response": profile_response.text,
        },
    )

    gmail_profile = profile_response.json()
    google_email = gmail_profile.get("emailAddress")
    google_name = None
    # -----------------------------------------------------------------------
    # Calculate token expiry
    # -----------------------------------------------------------------------

    expires_at = None

    if expires_in:
        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(seconds=int(expires_in))
        )

    # -----------------------------------------------------------------------
    # Find existing connection for THIS USER + PROVIDER
    # -----------------------------------------------------------------------

    result = await db.execute(
        select(ConnectedAccount)
        .where(
            ConnectedAccount.user_id == user_id
        )
        .where(
            ConnectedAccount.provider == provider
        )
    )

    account = result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # Update existing connection
    # -----------------------------------------------------------------------

    if account:

        account.access_token = access_token

        # Google may not return refresh_token on every authorization.
        # Never overwrite an existing refresh token with None.
        if refresh_token:
            account.refresh_token = refresh_token

        account.account_email = google_email
        account.account_name = google_name
        account.token_expires_at = expires_at
        account.scopes = token_scope
        account.is_active = True

    # -----------------------------------------------------------------------
    # Create new connection
    # -----------------------------------------------------------------------

    else:

        account = ConnectedAccount(
            user_id=user_id,
            provider=provider,
            account_email=google_email,
            account_name=google_name,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=expires_at,
            scopes=token_scope,
            is_active=True,
        )

        db.add(account)

    await db.commit()

    return {
        "status": "connected",
        "provider": provider,
        "account_email": google_email,
        "message": "Google account connected successfully.",
    }


# ---------------------------------------------------------------------------
# DISCONNECT PROVIDER
# ---------------------------------------------------------------------------

@router.delete(
    "/{provider}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def disconnect_provider(
    provider: str,
    current_user: CurrentUser,
    db: DbSession,
):
    """Disconnect a provider for the current user only."""

    result = await db.execute(
        select(ConnectedAccount)
        .where(
            ConnectedAccount.user_id == current_user.id
        )
        .where(
            ConnectedAccount.provider == provider
        )
    )

    account = result.scalar_one_or_none()

    if account:
        await db.delete(account)
        await db.flush()