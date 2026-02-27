"""Conversation model for AI chat sessions."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UUID

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User
    from app.models.message import Message


class Conversation(Base):
    """AI chat conversation within a project.
    
    Each project can have multiple conversations for different
    architecture discussions.
    """
    __tablename__ = "conversations"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Conversation title (auto-generated or user-set)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # User who created the conversation
    created_by: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="conversations")
    creator: Mapped["User"] = relationship("User")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title})>"
