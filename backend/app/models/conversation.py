"""Conversation and message models."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.execution import Execution
    from app.models.project import Project
    from app.models.tenant import Tenant
    from app.models.user import User


class Conversation(Base):
    """AI conversation session within a project."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="conversations")
    creator = relationship("User", back_populates="conversations_created")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    generated_commands = relationship("GeneratedCommand", back_populates="conversation", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title})>"


class Message(Base):
    """Message in a conversation (user or assistant)."""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=False, default=dict)  # token_count, model, etc.
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"


class GeneratedCommand(Base):
    """AI-generated Azure CLI commands before execution."""

    __tablename__ = "generated_commands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    commands = Column(JSON, nullable=False)  # Array of command objects
    risk_level = Column(String(20), nullable=False)  # low, medium, high
    estimated_cost_monthly = Column(Numeric(10, 2), nullable=True)
    requires_approval = Column(Boolean, nullable=False, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="generated_commands")
    message = relationship("Message")
    approver = relationship("User", foreign_keys=[approved_by])
    executions = relationship("Execution", back_populates="generated_command")

    def __repr__(self) -> str:
        return f"<GeneratedCommand(id={self.id}, risk_level={self.risk_level})>"

    @property
    def is_approved(self) -> bool:
        """Check if commands are approved for execution."""
        return self.approved_by is not None and self.approved_at is not None
