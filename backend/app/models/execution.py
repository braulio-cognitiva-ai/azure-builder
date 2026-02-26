"""Execution models."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation, GeneratedCommand
    from app.models.tenant import Tenant
    from app.models.user import User


class Execution(Base):
    """Command execution job."""

    __tablename__ = "executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    generated_command_id = Column(UUID(as_uuid=True), ForeignKey("generated_commands.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    started_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    error = Column(Text, nullable=True)
    output = Column(JSON, nullable=True)  # Structured results
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="executions")
    generated_command = relationship("GeneratedCommand", back_populates="executions")
    starter = relationship("User", back_populates="executions_started")
    steps = relationship("ExecutionStep", back_populates="execution", cascade="all, delete-orphan", order_by="ExecutionStep.step_number")

    def __repr__(self) -> str:
        return f"<Execution(id={self.id}, status={self.status})>"

    @property
    def is_running(self) -> bool:
        """Check if execution is currently running."""
        return self.status == "running"

    @property
    def is_complete(self) -> bool:
        """Check if execution is complete (success or failure)."""
        return self.status in ("completed", "failed", "cancelled")

    @property
    def duration_seconds(self) -> float | None:
        """Calculate execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class ExecutionStep(Base):
    """Individual command step within an execution."""

    __tablename__ = "execution_steps"
    __table_args__ = (
        UniqueConstraint("execution_id", "step_number", name="uq_execution_step"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    command = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)  # pending, running, completed, failed
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    execution = relationship("Execution", back_populates="steps")

    def __repr__(self) -> str:
        return f"<ExecutionStep(id={self.id}, step={self.step_number}, status={self.status})>"

    @property
    def duration_seconds(self) -> float | None:
        """Calculate step duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
