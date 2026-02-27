"""Database models."""
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus
from app.models.proposal import ArchitectureProposal, ProposalStatus
from app.models.proposal_option import ProposalOption
from app.models.deployment import DeploymentRequest, DeploymentStatus
from app.models.deployment_resource import DeploymentResource, ResourceStatus
from app.models.execution_log import ExecutionLog, LogLevel
from app.models.audit import AuditLog, AuditAction
from app.models.azure_connection import AzureConnection, AuthMethod, ConnectionStatus
from app.models.template import Template
from app.models.pricing_cache import PricingCache
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole

__all__ = [
    # Tenant & Users
    "Tenant",
    "User",
    "UserRole",
    
    # Projects
    "Project",
    "ProjectStatus",
    
    # Proposals
    "ArchitectureProposal",
    "ProposalStatus",
    "ProposalOption",
    
    # Deployments
    "DeploymentRequest",
    "DeploymentStatus",
    "DeploymentResource",
    "ResourceStatus",
    "ExecutionLog",
    "LogLevel",
    
    # Audit
    "AuditLog",
    "AuditAction",
    
    # Azure
    "AzureConnection",
    "AuthMethod",
    "ConnectionStatus",
    
    # Templates & Pricing
    "Template",
    "PricingCache",
    
    # Conversations
    "Conversation",
    "Message",
    "MessageRole",
]
