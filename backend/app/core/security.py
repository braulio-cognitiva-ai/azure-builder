"""Security utilities (JWT, password hashing)."""
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password for storage.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User UUID
        tenant_id: Tenant UUID
        email: User email
        role: User role
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)

    to_encode = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": "azure-builder-api",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False}  # We don't use audience claim
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")


def extract_token_from_header(authorization: Optional[str]) -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    
    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")
        
    Returns:
        Token string or None if invalid format
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]


class TokenPayload:
    """Parsed JWT token payload."""

    def __init__(self, payload: dict[str, Any]):
        """Initialize from decoded JWT payload."""
        self.user_id = UUID(payload["sub"])
        self.tenant_id = UUID(payload["tenant_id"])
        self.email = payload["email"]
        self.role = payload["role"]
        self.exp = datetime.fromtimestamp(payload["exp"])
        self.iat = datetime.fromtimestamp(payload["iat"])

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.exp

    @property
    def is_owner(self) -> bool:
        """Check if user is tenant owner."""
        return self.role == "owner"

    @property
    def is_admin(self) -> bool:
        """Check if user is admin or owner."""
        return self.role in ("owner", "admin")

    @property
    def can_execute(self) -> bool:
        """Check if user can execute commands."""
        return self.role in ("owner", "admin", "operator")
