"""Application configuration management."""
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "Azure Builder API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = Field(default="production", pattern="^(development|staging|production)$")
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./azurebuilder.db"
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_echo: bool = False
    
    # Redis (optional for dev)
    redis_url: Optional[str] = Field(default=None)
    redis_max_connections: int = 50
    
    # Azure
    azure_tenant_id: Optional[str] = None
    azure_subscription_id: Optional[str] = None
    azure_key_vault_url: Optional[str] = None
    azure_service_bus_connection_string: Optional[str] = None
    azure_service_bus_queue_name: str = "execution-jobs"
    
    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_deployment_name: str = "gpt-4-turbo"
    azure_openai_api_version: str = "2024-02-01"
    
    # Authentication (Azure AD B2C)
    azure_ad_b2c_tenant: Optional[str] = None
    azure_ad_b2c_client_id: Optional[str] = None
    azure_ad_b2c_policy_name: str = "B2C_1_signupsignin"
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24  # 24 hours
    
    # Security
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True
    allowed_hosts: list[str] = ["*"]
    
    # Rate Limiting (requests per minute)
    rate_limit_free: int = 10
    rate_limit_pro: int = 100
    rate_limit_enterprise: int = 1000
    
    # Execution
    execution_timeout_seconds: int = 300  # 5 minutes
    max_concurrent_executions_free: int = 5
    max_concurrent_executions_pro: int = 20
    max_concurrent_executions_enterprise: int = 100
    docker_execution_image: str = "mcr.microsoft.com/azure-cli:latest"
    docker_network_name: str = "azurebuilder-execution"
    
    # AI Engine
    ai_max_tokens: int = 4096
    ai_temperature: float = 0.1
    ai_max_conversation_history: int = 10
    
    # Azure Pricing API
    azure_pricing_api_url: str = "https://prices.azure.com/api/retail/prices"
    pricing_cache_ttl: int = 3600  # 1 hour in seconds
    
    # MCP (Model Context Protocol) - for future use
    mcp_endpoint: Optional[str] = None
    mcp_api_key: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure correct driver for SQLAlchemy."""
        if isinstance(v, str):
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://")
            elif v.startswith("sqlite://") and "+aiosqlite" not in v:
                return v.replace("sqlite://", "sqlite+aiosqlite://")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export singleton
settings = get_settings()
