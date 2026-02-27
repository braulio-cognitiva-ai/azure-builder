"""Pricing cache model for Azure retail pricing."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, DateTime, func, Numeric, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_types import UUID


class PricingCache(Base):
    """Cached Azure pricing data.
    
    Stores pricing information from Azure Retail Prices API
    with TTL for cache invalidation.
    """
    __tablename__ = "pricing_cache"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Service name (e.g., "Virtual Machines", "App Service")
    service: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # SKU name
    sku: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Region
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Meter name (e.g., "P1 v2")
    meter: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Unit price
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    
    # Currency code
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    
    # Unit of measure (e.g., "1 Hour", "1 GB")
    unit_of_measure: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Full pricing data from API (for reference)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Cache metadata
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    
    # Composite index for fast lookups
    __table_args__ = (
        Index('idx_pricing_lookup', 'service', 'sku', 'region'),
    )
    
    def __repr__(self) -> str:
        return f"<PricingCache(service={self.service}, sku={self.sku}, region={self.region}, price={self.price})>"
