"""Security Validation Service - Azure Security Best Practices Checker.

This service validates architecture proposals against Azure Security Benchmark
and Well-Architected Framework security pillar.
"""
from typing import List, Optional
from enum import Enum
from dataclasses import dataclass
from app.schemas.proposal import ResourceDefinition


class SecuritySeverity(str, Enum):
    """Security issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityIssue:
    """Security issue or recommendation."""
    severity: SecuritySeverity
    category: str  # e.g., "Network Security", "Identity", "Data Protection"
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None
    issue: str = ""
    recommendation: str = ""
    doc_link: Optional[str] = None


@dataclass
class SecurityReport:
    """Security validation report."""
    issues: List[SecurityIssue]
    score: int  # 0-100, where 100 is perfect
    passed_checks: int
    total_checks: int
    
    @property
    def has_critical(self) -> bool:
        """Check if any critical issues exist."""
        return any(issue.severity == SecuritySeverity.CRITICAL for issue in self.issues)
    
    @property
    def has_high(self) -> bool:
        """Check if any high severity issues exist."""
        return any(issue.severity == SecuritySeverity.HIGH for issue in self.issues)


class SecurityValidator:
    """Validates architecture proposals for security best practices."""
    
    # Resource types that typically contain secrets/credentials
    CREDENTIAL_RESOURCES = {
        "Microsoft.Sql/servers",
        "Microsoft.DBforPostgreSQL/servers",
        "Microsoft.DBforMySQL/servers",
        "Microsoft.Storage/storageAccounts",
        "Microsoft.ContainerRegistry/registries",
        "Microsoft.Cache/Redis",
    }
    
    # Resource types that should not be publicly accessible
    PRIVATE_RESOURCES = {
        "Microsoft.Sql/servers",
        "Microsoft.DBforPostgreSQL/servers",
        "Microsoft.DBforMySQL/servers",
        "Microsoft.Storage/storageAccounts",
    }
    
    def validate_proposal(self, resources: List[ResourceDefinition]) -> SecurityReport:
        """Validate a complete architecture proposal.
        
        Args:
            resources: List of Azure resources in the proposal
            
        Returns:
            SecurityReport with issues and score
        """
        issues: List[SecurityIssue] = []
        
        # Run all validation checks
        issues.extend(self._check_key_vault_usage(resources))
        issues.extend(self._check_public_access(resources))
        issues.extend(self._check_network_security(resources))
        issues.extend(self._check_managed_identity(resources))
        issues.extend(self._check_https_enforcement(resources))
        issues.extend(self._check_encryption(resources))
        issues.extend(self._check_logging(resources))
        
        # Calculate score (each check category worth ~14 points)
        total_checks = 7  # Number of check methods
        failed_checks = len(set(issue.category for issue in issues if issue.severity in [SecuritySeverity.CRITICAL, SecuritySeverity.HIGH]))
        passed_checks = total_checks - failed_checks
        score = int((passed_checks / total_checks) * 100)
        
        return SecurityReport(
            issues=issues,
            score=score,
            passed_checks=passed_checks,
            total_checks=total_checks
        )
    
    def _check_key_vault_usage(self, resources: List[ResourceDefinition]) -> List[SecurityIssue]:
        """Check if secrets are stored in Key Vault."""
        issues = []
        
        # Check if any credential resources exist
        has_credential_resources = any(
            r.type in self.CREDENTIAL_RESOURCES for r in resources
        )
        
        # Check if Key Vault is present
        has_keyvault = any(
            r.type == "Microsoft.KeyVault/vaults" for r in resources
        )
        
        if has_credential_resources and not has_keyvault:
            issues.append(SecurityIssue(
                severity=SecuritySeverity.HIGH,
                category="Data Protection",
                issue="Architecture includes resources with credentials but no Key Vault",
                recommendation="Add Azure Key Vault to securely store connection strings, API keys, and passwords",
                doc_link="https://learn.microsoft.com/azure/key-vault/general/overview"
            ))
        
        return issues
    
    def _check_public_access(self, resources: List[ResourceDefinition]) -> List[SecurityIssue]:
        """Check for resources exposed to public internet."""
        issues = []
        
        for resource in resources:
            if resource.type in self.PRIVATE_RESOURCES:
                # Check properties for public access indicators
                props = resource.properties or {}
                
                # SQL/Database servers
                if resource.type in ["Microsoft.Sql/servers", "Microsoft.DBforPostgreSQL/servers", "Microsoft.DBforMySQL/servers"]:
                    if props.get("publicNetworkAccess", "Enabled") == "Enabled":
                        issues.append(SecurityIssue(
                            severity=SecuritySeverity.HIGH,
                            category="Network Security",
                            resource_type=resource.type,
                            resource_name=resource.name,
                            issue=f"Database server '{resource.name}' allows public network access",
                            recommendation="Disable public access and use Private Endpoints or VNet integration",
                            doc_link="https://learn.microsoft.com/azure/postgresql/flexible-server/concepts-networking"
                        ))
                
                # Storage accounts
                if resource.type == "Microsoft.Storage/storageAccounts":
                    if props.get("allowBlobPublicAccess", True):
                        issues.append(SecurityIssue(
                            severity=SecuritySeverity.MEDIUM,
                            category="Network Security",
                            resource_type=resource.type,
                            resource_name=resource.name,
                            issue=f"Storage account '{resource.name}' allows public blob access",
                            recommendation="Set allowBlobPublicAccess to false unless public access is explicitly required",
                            doc_link="https://learn.microsoft.com/azure/storage/blobs/anonymous-read-access-prevent"
                        ))
        
        return issues
    
    def _check_network_security(self, resources: List[ResourceDefinition]) -> List[SecurityIssue]:
        """Check for Network Security Groups and firewall rules."""
        issues = []
        
        # Check if VMs or App Services exist
        compute_resources = [r for r in resources if r.type in [
            "Microsoft.Compute/virtualMachines",
            "Microsoft.Web/sites",
            "Microsoft.ContainerInstance/containerGroups"
        ]]
        
        # Check if NSG exists
        has_nsg = any(r.type == "Microsoft.Network/networkSecurityGroups" for r in resources)
        
        # Check if VNet exists
        has_vnet = any(r.type == "Microsoft.Network/virtualNetworks" for r in resources)
        
        if compute_resources and not has_vnet:
            issues.append(SecurityIssue(
                severity=SecuritySeverity.MEDIUM,
                category="Network Security",
                issue="Compute resources without Virtual Network isolation",
                recommendation="Deploy resources in a Virtual Network for network isolation and security",
                doc_link="https://learn.microsoft.com/azure/virtual-network/virtual-networks-overview"
            ))
        
        if compute_resources and not has_nsg:
            issues.append(SecurityIssue(
                severity=SecuritySeverity.MEDIUM,
                category="Network Security",
                issue="Compute resources without Network Security Groups",
                recommendation="Add Network Security Groups to control inbound/outbound traffic",
                doc_link="https://learn.microsoft.com/azure/virtual-network/network-security-groups-overview"
            ))
        
        return issues
    
    def _check_managed_identity(self, resources: List[ResourceDefinition]) -> List[SecurityIssue]:
        """Check if resources use Managed Identity instead of credentials."""
        issues = []
        
        # Resource types that should use Managed Identity
        identity_capable = [
            "Microsoft.Web/sites",
            "Microsoft.Compute/virtualMachines",
            "Microsoft.ContainerInstance/containerGroups",
            "Microsoft.Logic/workflows",
            "Microsoft.DataFactory/factories"
        ]
        
        for resource in resources:
            if resource.type in identity_capable:
                props = resource.properties or {}
                identity = props.get("identity", {})
                
                if not identity or identity.get("type") == "None":
                    issues.append(SecurityIssue(
                        severity=SecuritySeverity.MEDIUM,
                        category="Identity & Access",
                        resource_type=resource.type,
                        resource_name=resource.name,
                        issue=f"Resource '{resource.name}' does not use Managed Identity",
                        recommendation="Enable System-Assigned or User-Assigned Managed Identity to avoid storing credentials",
                        doc_link="https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview"
                    ))
        
        return issues
    
    def _check_https_enforcement(self, resources: List[ResourceDefinition]) -> List[SecurityIssue]:
        """Check if HTTPS is enforced for web services."""
        issues = []
        
        for resource in resources:
            # App Services
            if resource.type == "Microsoft.Web/sites":
                props = resource.properties or {}
                if not props.get("httpsOnly", False):
                    issues.append(SecurityIssue(
                        severity=SecuritySeverity.HIGH,
                        category="Data Protection",
                        resource_type=resource.type,
                        resource_name=resource.name,
                        issue=f"App Service '{resource.name}' does not enforce HTTPS",
                        recommendation="Set httpsOnly to true to encrypt all traffic",
                        doc_link="https://learn.microsoft.com/azure/app-service/configure-ssl-bindings"
                    ))
            
            # Storage Accounts
            if resource.type == "Microsoft.Storage/storageAccounts":
                props = resource.properties or {}
                if not props.get("supportsHttpsTrafficOnly", True):
                    issues.append(SecurityIssue(
                        severity=SecuritySeverity.HIGH,
                        category="Data Protection",
                        resource_type=resource.type,
                        resource_name=resource.name,
                        issue=f"Storage account '{resource.name}' allows HTTP traffic",
                        recommendation="Set supportsHttpsTrafficOnly to true",
                        doc_link="https://learn.microsoft.com/azure/storage/common/storage-require-secure-transfer"
                    ))
        
        return issues
    
    def _check_encryption(self, resources: List[ResourceDefinition]) -> List[SecurityIssue]:
        """Check for encryption at rest."""
        issues = []
        
        for resource in resources:
            # SQL Databases
            if resource.type == "Microsoft.Sql/servers/databases":
                props = resource.properties or {}
                if not props.get("transparentDataEncryption"):
                    issues.append(SecurityIssue(
                        severity=SecuritySeverity.MEDIUM,
                        category="Data Protection",
                        resource_type=resource.type,
                        resource_name=resource.name,
                        issue=f"SQL Database '{resource.name}' may not have Transparent Data Encryption enabled",
                        recommendation="Ensure TDE is enabled (usually enabled by default)",
                        doc_link="https://learn.microsoft.com/azure/azure-sql/database/transparent-data-encryption-tde-overview"
                    ))
        
        return issues
    
    def _check_logging(self, resources: List[ResourceDefinition]) -> List[SecurityIssue]:
        """Check if diagnostic logging and monitoring are configured."""
        issues = []
        
        # Check if Application Insights exists
        has_app_insights = any(
            r.type == "Microsoft.Insights/components" for r in resources
        )
        
        # Check if Log Analytics workspace exists
        has_log_analytics = any(
            r.type == "Microsoft.OperationalInsights/workspaces" for r in resources
        )
        
        if not has_app_insights and not has_log_analytics:
            issues.append(SecurityIssue(
                severity=SecuritySeverity.LOW,
                category="Monitoring",
                issue="No monitoring or logging solution detected",
                recommendation="Add Application Insights or Log Analytics for security monitoring and diagnostics",
                doc_link="https://learn.microsoft.com/azure/azure-monitor/overview"
            ))
        
        return issues


# Convenience function for quick validation
def validate_security(resources: List[ResourceDefinition]) -> SecurityReport:
    """Validate security of a resource list.
    
    Args:
        resources: List of Azure resources to validate
        
    Returns:
        SecurityReport with findings
    """
    validator = SecurityValidator()
    return validator.validate_proposal(resources)
