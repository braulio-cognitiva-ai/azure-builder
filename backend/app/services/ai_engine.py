"""AI Engine for natural language → Azure CLI translation."""
import json
import re
import shlex
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from openai import AsyncAzureOpenAI

from app.config import settings


class RiskLevel(str, Enum):
    """Command risk level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Command:
    """Single Azure CLI command."""

    command: str
    description: str
    risk_level: RiskLevel
    continue_on_error: bool = False


@dataclass
class ExecutionPlan:
    """Complete execution plan with commands and metadata."""

    commands: list[Command]
    requires_approval: bool
    estimated_duration_minutes: int
    risk_level: RiskLevel
    warnings: list[str]


# System prompt for Azure CLI generation
SYSTEM_PROMPT = """You are an Azure infrastructure expert that converts natural language requests into Azure CLI commands.

RULES:
1. Output ONLY valid Azure CLI commands (bash syntax)
2. Use long-form flags (--resource-group, not -g) for clarity
3. Include --output json for commands that return data
4. For multi-step operations, output commands in execution order
5. Never use placeholders - ask for missing information instead
6. Prefer idempotent operations (check existence before create)
7. Add comments with # for complex operations
8. Use variables for values that will be reused

SAFETY:
- NEVER delete resource groups without explicit user confirmation
- NEVER delete production-tagged resources
- ALWAYS check if resource exists before destructive operations
- Use --yes flags only when safe
- Validate resource names follow Azure naming conventions

OUTPUT FORMAT (JSON):
{
  "commands": [
    {
      "command": "az group create --name rg-app-prod --location eastus",
      "description": "Create resource group for production environment",
      "risk_level": "low",
      "continue_on_error": false
    }
  ],
  "requires_approval": false,
  "estimated_duration_minutes": 2,
  "warnings": []
}

RISK LEVELS:
- low: Create resources, read operations, safe updates
- medium: Updates that might cause downtime, delete non-critical resources
- high: Delete resource groups, delete production resources, RBAC changes

If information is missing or unclear, respond with:
{
  "error": "missing_information",
  "message": "I need more information to proceed: ...",
  "questions": ["What should the resource group name be?", "Which Azure region?"]
}
"""

# Dangerous command patterns that require explicit approval
DANGER_PATTERNS = [
    r"az\s+group\s+delete",  # Resource group deletion
    r"az\s+.*\s+delete\s+.*--force",  # Force deletion
    r"az\s+ad\s+",  # Active Directory operations
    r"az\s+role\s+assignment\s+delete",  # RBAC changes
    r"--force-string",  # Bypass type validation
]

# Blocked command patterns (never allow)
BLOCKED_PATTERNS = [
    r";|\||&&|`|\$\(",  # Shell injection attempts
    r"rm\s+-rf",  # Dangerous shell commands
    r"curl.*\|.*sh",  # Pipe to shell
]


class AIEngine:
    """AI Engine for NL → Azure CLI translation."""

    def __init__(self):
        """Initialize AI engine with Azure OpenAI client."""
        self.client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )

    async def translate(
        self,
        user_message: str,
        conversation_history: Optional[list[dict[str, str]]] = None,
        tenant_context: Optional[dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """
        Translate natural language to Azure CLI commands.
        
        Args:
            user_message: User's natural language request
            conversation_history: Previous messages in conversation
            tenant_context: Optional tenant-specific context (existing resources, etc.)
            
        Returns:
            ExecutionPlan with commands and metadata
            
        Raises:
            ValueError: If AI cannot generate valid commands
        """
        # Sanitize input
        user_message = self._sanitize_input(user_message)

        # Build context prompt
        context_prompt = self._build_context_prompt(tenant_context)

        # Prepare messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + context_prompt}
        ]

        # Add conversation history (last N messages)
        if conversation_history:
            messages.extend(conversation_history[-settings.ai_max_conversation_history:])

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        # Call Azure OpenAI
        response = await self.client.chat.completions.create(
            model=settings.azure_openai_deployment_name,
            messages=messages,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            response_format={"type": "json_object"},
        )

        # Parse response
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from AI")

        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from AI: {e}")

        # Check for missing information
        if "error" in result:
            raise ValueError(result.get("message", "Unable to generate commands"))

        # Parse commands
        commands = [
            Command(
                command=cmd["command"],
                description=cmd["description"],
                risk_level=RiskLevel(cmd.get("risk_level", "low")),
                continue_on_error=cmd.get("continue_on_error", False),
            )
            for cmd in result.get("commands", [])
        ]

        # Validate commands
        validation_result = self._validate_commands(commands)
        if not validation_result["valid"]:
            raise ValueError(f"Invalid commands: {', '.join(validation_result['errors'])}")

        # Assess overall risk
        risk_level = self._assess_risk(commands)

        # Determine if approval is required
        requires_approval = (
            risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
            or result.get("requires_approval", False)
        )

        return ExecutionPlan(
            commands=commands,
            requires_approval=requires_approval,
            estimated_duration_minutes=result.get("estimated_duration_minutes", 5),
            risk_level=risk_level,
            warnings=result.get("warnings", []),
        )

    def _sanitize_input(self, text: str) -> str:
        """
        Sanitize user input to prevent prompt injection.
        
        Args:
            text: User input text
            
        Returns:
            Sanitized text
        """
        # Remove potential prompt injection attempts
        dangerous_patterns = [
            r"ignore previous instructions",
            r"system:",
            r"assistant:",
            r"<\|.*?\|>",  # Special tokens
        ]

        for pattern in dangerous_patterns:
            text = re.sub(pattern, "[FILTERED]", text, flags=re.IGNORECASE)

        # Limit length to prevent DoS
        return text[:5000]

    def _build_context_prompt(self, tenant_context: Optional[dict[str, Any]]) -> str:
        """
        Build context prompt with tenant-specific information.
        
        Args:
            tenant_context: Optional tenant context data
            
        Returns:
            Context prompt string
        """
        if not tenant_context:
            return ""

        context_parts = ["\n\nCONTEXT:"]

        if "existing_resources" in tenant_context:
            context_parts.append(
                f"Existing resources: {', '.join(tenant_context['existing_resources'])}"
            )

        if "default_location" in tenant_context:
            context_parts.append(
                f"Default Azure region: {tenant_context['default_location']}"
            )

        if "naming_convention" in tenant_context:
            context_parts.append(
                f"Naming convention: {tenant_context['naming_convention']}"
            )

        return "\n".join(context_parts)

    def _validate_commands(self, commands: list[Command]) -> dict[str, Any]:
        """
        Validate generated commands for safety and syntax.
        
        Args:
            commands: List of commands to validate
            
        Returns:
            Validation result with errors if any
        """
        errors = []

        for i, cmd in enumerate(commands):
            # Check for blocked patterns
            for pattern in BLOCKED_PATTERNS:
                if re.search(pattern, cmd.command):
                    errors.append(
                        f"Command {i+1}: Blocked pattern detected (potential security risk)"
                    )

            # Validate it's an Azure CLI command
            if not cmd.command.strip().startswith("az "):
                errors.append(f"Command {i+1}: Must start with 'az '")

            # Try to parse command with shlex (detect malformed commands)
            try:
                shlex.split(cmd.command)
            except ValueError as e:
                errors.append(f"Command {i+1}: Invalid syntax - {e}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    def _assess_risk(self, commands: list[Command]) -> RiskLevel:
        """
        Assess overall risk level for a set of commands.
        
        Args:
            commands: List of commands
            
        Returns:
            Overall risk level (highest among all commands)
        """
        risk_levels = [cmd.risk_level for cmd in commands]

        # Check for dangerous patterns
        for cmd in commands:
            for pattern in DANGER_PATTERNS:
                if re.search(pattern, cmd.command, re.IGNORECASE):
                    return RiskLevel.HIGH

        # Return highest risk level
        if RiskLevel.HIGH in risk_levels:
            return RiskLevel.HIGH
        elif RiskLevel.MEDIUM in risk_levels:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
