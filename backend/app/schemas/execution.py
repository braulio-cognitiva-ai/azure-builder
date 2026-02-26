"""Execution schemas."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ExecutionStepBase(BaseModel):
    """Base execution step fields."""

    step_number: int
    command: str
    status: str = Field(pattern=r"^(pending|running|completed|failed)$")


class ExecutionStep(ExecutionStepBase):
    """Full execution step schema."""

    id: UUID
    execution_id: UUID
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True


class ExecutionBase(BaseModel):
    """Base execution fields."""

    status: str = Field(
        default="pending",
        pattern=r"^(pending|running|completed|failed|cancelled)$"
    )


class ExecutionCreate(BaseModel):
    """Schema for creating an execution."""

    generated_command_id: UUID


class ExecutionUpdate(BaseModel):
    """Schema for updating an execution."""

    status: Optional[str] = Field(
        None,
        pattern=r"^(pending|running|completed|failed|cancelled)$"
    )


class Execution(ExecutionBase):
    """Full execution schema."""

    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    generated_command_id: UUID
    started_by: UUID
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    output: Optional[dict[str, Any]] = None
    created_at: datetime
    duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True


class ExecutionWithSteps(Execution):
    """Execution with all steps."""

    steps: list[ExecutionStep] = Field(default_factory=list)


class ExecutionCancelRequest(BaseModel):
    """Request to cancel an execution."""

    reason: Optional[str] = None


class ExecutionRollbackRequest(BaseModel):
    """Request to rollback an execution."""

    confirm: bool = Field(..., description="Must be true to confirm rollback")
