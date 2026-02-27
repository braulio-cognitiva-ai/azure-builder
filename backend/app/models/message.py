"""Message model for conversation messages."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import String, Text, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UUID

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class MessageRole(str, enum.Enum):
    """Message role in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base):
    """Individual message in a conversation.
    
    Stores user prompts and AI responses in the chat flow.
    """
    __tablename__ = "messages"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message role
    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(MessageRole, native_enum=False, length=20),
        nullable=False
    )
    
    # Message content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata (token count, model used, etc.) - renamed to avoid SQLAlchemy reserved word conflict
    message_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, content={self.content[:50]}...)>"
