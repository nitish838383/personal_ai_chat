"""Memory API — long-term personal memory, fully user-scoped."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, desc

from app.api.deps import CurrentUser, DbSession
from app.models.memory import Memory
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter(prefix="/memories", tags=["Memory"])


class MemoryCreate(BaseModel):
    category: str = Field(..., max_length=100)
    content: str = Field(..., min_length=1)
    importance: float = Field(0.5, ge=0.0, le=1.0)
    source: Optional[str] = None


class MemoryUpdate(BaseModel):
    category: Optional[str] = None
    content: Optional[str] = None
    importance: Optional[float] = Field(None, ge=0.0, le=1.0)


class MemoryResponse(BaseModel):
    id: UUID
    category: str
    content: str
    importance: float
    source: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=List[MemoryResponse])
async def list_memories(
    current_user: CurrentUser,
    db: DbSession,
    category: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
):
    stmt = (
        select(Memory)
        .where(Memory.user_id == current_user.id)
        .order_by(desc(Memory.importance), desc(Memory.updated_at))
        .limit(limit)
    )
    if category:
        stmt = stmt.where(Memory.category == category)
    if q:
        stmt = stmt.where(Memory.content.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(payload: MemoryCreate, current_user: CurrentUser, db: DbSession):
    mem = Memory(
        user_id=current_user.id,
        category=payload.category,
        content=payload.content,
        importance=payload.importance,
        source=payload.source or "manual",
    )
    db.add(mem)
    await db.flush()
    await db.refresh(mem)
    return mem


@router.patch("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: UUID,
    payload: MemoryUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    result = await db.execute(
        select(Memory).where(Memory.id == memory_id).where(Memory.user_id == current_user.id)
    )
    mem = result.scalar_one_or_none()
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found")
    if payload.category is not None:
        mem.category = payload.category
    if payload.content is not None:
        mem.content = payload.content
    if payload.importance is not None:
        mem.importance = payload.importance
    db.add(mem)
    await db.flush()
    await db.refresh(mem)
    return mem


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(memory_id: UUID, current_user: CurrentUser, db: DbSession):
    result = await db.execute(
        select(Memory).where(Memory.id == memory_id).where(Memory.user_id == current_user.id)
    )
    mem = result.scalar_one_or_none()
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found")
    await db.delete(mem)
    await db.flush()
