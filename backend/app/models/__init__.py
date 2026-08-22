"""
Database models package.
Import all models here so Alembic and Base.metadata discover them.
"""

from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.memory import Memory
from app.models.task import Task
from app.models.connected_account import ConnectedAccount
from app.models.activity_log import ActivityLog
from app.models.notification import Notification
from app.models.document import Document, DocumentChunk
from app.models.integration_permission import IntegrationPermission

__all__ = [
    "User",
    "Conversation",
    "Message",
    "Memory",
    "Task",
    "ConnectedAccount",
    "ActivityLog",
    "Notification",
    "Document",
    "DocumentChunk",
    "IntegrationPermission",
]
