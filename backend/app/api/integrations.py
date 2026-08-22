"""
Connected Apps / Integrations API.
OAuth tokens are stored only on the backend and never returned to the frontend.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.connected_account import ConnectedAccount
from app.core.config import settings

router = APIRouter(prefix="/integrations", tags=["Integrations"])

SUPPORTED_PROVIDERS = ["gmail", "google_calendar", "google_drive", "slack", "notion", "whatsapp"]


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


@router.get("", response_model=List[IntegrationStatus])
async def list_integrations(current_user: CurrentUser, db: DbSession):
    """Return connection status for all supported providers (no tokens)."""
    result = await db.execute(
        select(ConnectedAccount).where(ConnectedAccount.user_id == current_user.id)
    )
    accounts = {a.provider: a for a in result.scalars().all()}

    statuses = []
    for provider in SUPPORTED_PROVIDERS:
        acc = accounts.get(provider)
        statuses.append(
            IntegrationStatus(
                provider=provider,
                connected=bool(acc and acc.is_active),
                account_email=acc.account_email if acc else None,
                account_name=acc.account_name if acc else None,
                is_active=bool(acc and acc.is_active),
            )
        )
    return statuses


@router.post("/{provider}/connect", response_model=ConnectResponse)
async def connect_provider(provider: str, current_user: CurrentUser, db: DbSession):
    """
    Initiate OAuth connection for a provider.
    Returns an authorization URL when credentials are configured.
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    if provider == "whatsapp":
        return ConnectResponse(
            provider=provider,
            message="WhatsApp Business API integration is planned. Requires official WhatsApp Business account and credentials.",
            authorization_url=None,
        )

    # Google family
    if provider in ("gmail", "google_calendar", "google_drive"):
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            return ConnectResponse(
                provider=provider,
                message=(
                    "Google OAuth is not configured. "
                    "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in the backend .env file."
                ),
                authorization_url=None,
            )
        # Build real Google OAuth URL (scopes depend on provider)
        scopes = {
            "gmail": "https://www.googleapis.com/auth/gmail.readonly",
            "google_calendar": "https://www.googleapis.com/auth/calendar",
            "google_drive": "https://www.googleapis.com/auth/drive.readonly",
        }
        from urllib.parse import urlencode
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": scopes.get(provider, ""),
            "access_type": "offline",
            "prompt": "consent",
            "state": f"{provider}:{current_user.id}",  # simple state; improve with signed state later
        }
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
        return ConnectResponse(
            provider=provider,
            message="Redirect the user to authorization_url to complete Google OAuth.",
            authorization_url=auth_url,
        )

    if provider == "notion":
        if not settings.NOTION_CLIENT_ID:
            return ConnectResponse(
                provider=provider,
                message="Notion OAuth is not configured. Set NOTION_CLIENT_ID and NOTION_CLIENT_SECRET.",
                authorization_url=None,
            )
        return ConnectResponse(
            provider=provider,
            message="Notion OAuth ready when credentials are set.",
            authorization_url=None,
        )

    if provider == "slack":
        if not settings.SLACK_CLIENT_ID:
            return ConnectResponse(
                provider=provider,
                message="Slack OAuth is not configured. Set SLACK_CLIENT_ID and SLACK_CLIENT_SECRET.",
                authorization_url=None,
            )
        return ConnectResponse(
            provider=provider,
            message="Slack OAuth ready when credentials are set.",
            authorization_url=None,
        )

    return ConnectResponse(provider=provider, message="Provider not implemented yet.", authorization_url=None)


@router.get("/google/callback")
async def google_callback(code: str = "", state: str = "", error: str = ""):
    """
    OAuth callback for Google.
    In production: exchange code for tokens, encrypt, store in ConnectedAccount.
    """
    if error:
        return {"status": "error", "detail": error}
    if not code:
        return {"status": "error", "detail": "Missing authorization code"}
    # Placeholder — full token exchange requires client secret and should update ConnectedAccount
    return {
        "status": "received",
        "message": (
            "Authorization code received. "
            "Token exchange and secure storage will complete once GOOGLE_CLIENT_SECRET is configured "
            "and the exchange logic is enabled."
        ),
        "state": state,
    }


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_provider(provider: str, current_user: CurrentUser, db: DbSession):
    """Disconnect a provider and remove stored tokens for the current user only."""
    result = await db.execute(
        select(ConnectedAccount)
        .where(ConnectedAccount.user_id == current_user.id)
        .where(ConnectedAccount.provider == provider)
    )
    acc = result.scalar_one_or_none()
    if acc:
        await db.delete(acc)
        await db.flush()
