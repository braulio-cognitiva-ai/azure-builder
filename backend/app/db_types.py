"""Database type utilities for cross-database compatibility."""
import uuid
from sqlalchemy import String, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY as PG_ARRAY, INET as PG_INET
from app.config import settings

# Detect database type
is_sqlite = str(settings.database_url).startswith("sqlite")


class UUID(TypeDecorator):
    """Platform-independent UUID type.
    
    Uses PostgreSQL UUID on PostgreSQL, and String(36) on SQLite.
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, str):
                return uuid.UUID(value)
            return value


def ARRAY(item_type, **kwargs):
    """Platform-independent ARRAY type.
    
    Uses PostgreSQL ARRAY on PostgreSQL, and JSON on SQLite.
    """
    from sqlalchemy import JSON
    if is_sqlite:
        # SQLite: store as JSON array
        return JSON
    else:
        # PostgreSQL: use native ARRAY
        return PG_ARRAY(item_type, **kwargs)


def INET(**kwargs):
    """Platform-independent INET type.
    
    Uses PostgreSQL INET on PostgreSQL, and String on SQLite.
    """
    if is_sqlite:
        # SQLite: store as string
        return String(45)  # Max length for IPv6
    else:
        # PostgreSQL: use native INET
        return PG_INET
