"""Helper to write activity / audit log entries (always user-scoped)."""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog


async def log_activity(
    db: AsyncSession,
    user_id: UUID,
    action: str,
    application: Optional[str] = None,
    status: str = "success",
    details: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> ActivityLog:
    entry = ActivityLog(
        user_id=user_id,
        action=action,
        application=application,
        status=status,
        details=details,
        metadata_=metadata,
    )
    db.add(entry)
    await db.flush()
    return entry
