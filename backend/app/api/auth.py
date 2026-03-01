"""Authentication API routes."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.schemas.user import User as UserSchema

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Register request schema."""

    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response schema."""

    access_token: str
    token_type: str = "bearer"
    user: UserSchema


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user with a personal tenant."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create tenant
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Personal",
        slug=f"personal-{uuid.uuid4().hex[:8]}",
        plan_tier="free",
        settings={},
    )
    db.add(tenant)
    await db.flush()

    # Create user
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=data.email,
        name=data.name,
        role=UserRole.ADMIN,
        password_hash=get_password_hash(data.password),
        last_login=datetime.utcnow(),
    )
    db.add(user)
    await db.flush()

    access_token = create_access_token(
        user_id=user.id,
        tenant_id=tenant.id,
        email=user.email,
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
    )

    return LoginResponse(
        access_token=access_token,
        user=UserSchema.model_validate(user),
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password."""
    # Query user by email
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Verify password
    if not user.password_hash or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Create access token
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        role=user.role,
    )

    return LoginResponse(
        access_token=access_token,
        user=UserSchema.model_validate(user),
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user.
    
    In production, this would invalidate the token (add to blocklist).
    """
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current user information."""
    return UserSchema.model_validate(current_user)


@router.post("/refresh")
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token.
    
    In production, this would validate the refresh token and issue a new access token.
    """
    # Placeholder implementation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not implemented yet",
    )
