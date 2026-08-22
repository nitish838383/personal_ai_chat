"""
Chat & Conversation API.
All queries are strictly scoped to the authenticated user.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.conversation import Conversation, Message
from app.schemas.chat import (
    ChatRequest,
    ConversationCreate,
    ConversationDetail,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
)
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(current_user: CurrentUser, db: DbSession):
    """List conversations for the current user only."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .where(Conversation.is_archived == False)  # noqa: E712
        .order_by(desc(Conversation.updated_at))
    )
    return result.scalars().all()


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    conv = Conversation(
        user_id=current_user.id,
        title=payload.title or "New conversation",
    )
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return conv


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    payload: ConversationUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if payload.title is not None:
        conv.title = payload.title
    if payload.is_archived is not None:
        conv.is_archived = payload.is_archived

    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return conv


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
    await db.flush()


@router.post("", response_model=MessageResponse)
async def chat(
    payload: ChatRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Send a message and get an AI response.
    Creates a new conversation if conversation_id is not provided.
    All data is scoped to the current user.
    """
    # Resolve or create conversation
    if payload.conversation_id:
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == payload.conversation_id)
            .where(Conversation.user_id == current_user.id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = Conversation(user_id=current_user.id, title=payload.message[:80])
        db.add(conv)
        await db.flush()
        await db.refresh(conv)
        conv.messages = []

    # Store user message
    user_msg = Message(
        conversation_id=conv.id,
        user_id=current_user.id,
        role="user",
        content=payload.message,
    )
    db.add(user_msg)
    await db.flush()

    # Build message history for AI
    history = [
        {"role": m.role, "content": m.content}
        for m in sorted(conv.messages, key=lambda x: x.created_at)
        if m.role in ("user", "assistant", "system")
    ]
    history.append({"role": "user", "content": payload.message})

    # System prompt for Personal AI OS
    system_prompt = {
        "role": "system",
        "content": (
            "You are the Personal AI OS assistant. You help the user manage their digital life. "
            "Be concise, helpful, and proactive. When you use tools or external data, "
            "briefly mention the source. Never invent private data."
        ),
    }
    messages_for_ai = [system_prompt] + history

    ai = get_ai_service()
    try:
        response = await ai.chat(messages_for_ai)
        assistant_content = (
            response.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "I could not generate a response.")
        )
    except Exception as e:
        print(f"AI ERROR: {type(e).__name__}: {e}")
        raise HTTPException(
        status_code=500,
        detail=f"AI provider error: {str(e)[:300]}",
    )
    # Store assistant message
    assistant_msg = Message(
        conversation_id=conv.id,
        user_id=current_user.id,
        role="assistant",
        content=assistant_content,
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)

    return assistant_msg
