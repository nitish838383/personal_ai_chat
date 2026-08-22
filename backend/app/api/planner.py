"""AI Daily Planner — generates a plan from tasks + calendar context."""

from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.task import Task
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/planner", tags=["Planner"])


class PlannerResponse(BaseModel):
    date: str
    summary: str
    priority_tasks: List[dict[str, Any]]
    recommendations: List[str]


@router.get("/today", response_model=PlannerResponse)
async def get_today_plan(current_user: CurrentUser, db: DbSession):
    """
    Generate a daily plan for the authenticated user.
    Uses tasks (and later calendar / memory when connected).
    """
    result = await db.execute(
        select(Task)
        .where(Task.user_id == current_user.id)
        .where(Task.status.in_(["pending", "in_progress"]))
        .order_by(Task.priority.desc())
        .limit(20)
    )
    tasks = result.scalars().all()

    priority_tasks = [
        {
            "id": str(t.id),
            "title": t.title,
            "priority": t.priority,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "status": t.status,
        }
        for t in tasks
    ]

    # Simple recommendations without requiring AI key
    recommendations = []
    high = [t for t in tasks if t.priority == "high"]
    if high:
        recommendations.append(f"Focus first on high-priority tasks: {', '.join(t.title for t in high[:3])}")
    if not tasks:
        recommendations.append("No pending tasks. Ask the AI to help plan your day or create tasks.")
    else:
        recommendations.append("Review and complete pending tasks. Use AI Chat for deeper planning.")

    # Optional AI enhancement
    ai = get_ai_service()
    summary = f"You have {len(tasks)} open task(s) today."
    if ai.api_key and tasks:
        try:
            task_list = "\n".join(f"- [{t.priority}] {t.title}" for t in tasks[:10])
            resp = await ai.chat([
                {"role": "system", "content": "You are a concise daily planner assistant."},
                {"role": "user", "content": f"Summarize this task list into a short daily plan (2-3 sentences):\n{task_list}"},
            ])
            summary = resp.get("choices", [{}])[0].get("message", {}).get("content", summary)
        except Exception:
            pass

    return PlannerResponse(
        date=datetime.now(timezone.utc).date().isoformat(),
        summary=summary,
        priority_tasks=priority_tasks,
        recommendations=recommendations,
    )
