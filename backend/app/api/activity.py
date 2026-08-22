"""Activity / audit log API — user-scoped."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select, desc

from app.api.deps import CurrentUser, DbSession
from app.models.activity_log import ActivityLog

router = APIRouter(prefix="/activity", tags=["Activity"])


class ActivityResponse(BaseModel):
    id: UUID
    action: str
    application: Optional[str]
    status: str
    details: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=List[ActivityResponse])
async def list_activity(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(50, ge=1, le=200),
):
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.user_id == current_user.id)
        .order_by(desc(ActivityLog.created_at))
        .limit(limit)
    )
    return result.scalars().all()
