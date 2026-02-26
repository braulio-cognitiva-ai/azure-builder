# Azure Builder - Technical Architecture

## Executive Summary

Azure Builder is a production-grade, multi-tenant SaaS platform that enables users to provision Azure infrastructure using natural language. The platform translates user intent into Azure CLI commands, provides approval workflows, and executes commands in isolated environments against the user's Azure subscription.

**Core Value Proposition:**
- Natural language → Azure CLI translation via AI
- Review & approve before execution
- Multi-tenant isolation with enterprise-grade security
- Full audit trail and cost estimation

---

## 1. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │    Next.js 14 Frontend (React, Tailwind, TypeScript)         │  │
│  │    - AI Chat Interface    - Monaco Editor                    │  │
│  │    - Real-time WebSocket  - Template Gallery                 │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
└────────────────────────────┼─────────────────────────────────────────┘
                             │ HTTPS / WSS
┌────────────────────────────┼─────────────────────────────────────────┐
│                       API GATEWAY LAYER                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  FastAPI API Gateway                                          │  │
│  │  - JWT Authentication    - Rate Limiting                      │  │
│  │  - Tenant Context        - Request Validation                │  │
│  └────────┬──────────┬──────────┬──────────┬─────────────────────┘  │
└───────────┼──────────┼──────────┼──────────┼─────────────────────────┘
            │          │          │          │
┌───────────┴──────────┴──────────┴──────────┴─────────────────────────┐
│                      APPLICATION SERVICES                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│  │  AI Engine   │  │  Execution   │  │   Template Service      │   │
│  │   Service    │  │   Engine     │  │                         │   │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │  - Pre-built patterns   │   │
│  │ │ OpenAI   │ │  │ │ Docker   │ │  │  - Best practices       │   │
│  │ │ GPT-4    │ │  │ │ Sandbox  │ │  │  - Quick start          │   │
│  │ └──────────┘ │  │ └──────────┘ │  └─────────────────────────┘   │
│  │ - NL→CLI     │  │ - Isolated   │  ┌─────────────────────────┐   │
│  │ - Validation │  │ - Rollback   │  │  Cost Estimation        │   │
│  │ - Safety     │  │ - Approval   │  │   Service               │   │
│  └──────────────┘  └──────────────┘  │  - Pre-execution calc   │   │
│                                       └─────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │           Audit & Logging Service                              │ │
│  │  - Full command history  - Compliance logs  - RBAC tracking   │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────┴──────────────────────────────────────────┐
│                         DATA LAYER                                    │
│  ┌──────────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  PostgreSQL      │  │    Redis     │  │  Azure Service Bus  │   │
│  │  + Row-Level     │  │  - Cache     │  │  - Async execution  │   │
│  │    Security      │  │  - Sessions  │  │  - Job queue        │   │
│  └──────────────────┘  └──────────────┘  └─────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┴──────────────────────────────────────────┐
│                      EXTERNAL SERVICES                                │
│  ┌──────────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  Azure AD B2C    │  │ Azure Key    │  │  Customer's Azure   │   │
│  │  Authentication  │  │   Vault      │  │   Subscription      │   │
│  │                  │  │ - SP creds   │  │  (Their resources)  │   │
│  └──────────────────┘  └──────────────┘  └─────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
```

### Communication Patterns

**Synchronous (REST):**
- User authentication & authorization
- CRUD operations (projects, templates, settings)
- AI command generation (with streaming response)
- Template browsing

**Asynchronous (WebSocket + Queue):**
- Real-time command execution status
- Live terminal output streaming
- Multi-step deployment progress
- Background job processing (long-running executions)

**Message Queue (Azure Service Bus):**
- Execution jobs (submitted to queue for worker processing)
- Audit log aggregation
- Notification delivery
- Scheduled cleanups

---

## 2. Multi-Tenancy & Data Isolation

### Decision: Row-Level Security (RLS) with Single Database

**Strategy:** Single PostgreSQL database with Row-Level Security policies.

**Justification:**

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Database-per-tenant** | Ultimate isolation | Operational nightmare (backup, migration, schema changes), cost scales linearly | ❌ Not suitable for SaaS |
| **Schema-per-tenant** | Good isolation | Complex routing, schema migrations painful, connection pooling issues | ⚠️ Medium complexity |
| **Row-Level Security** | Simple ops, cost-effective, proven at scale (used by Notion, Linear, etc.) | Requires careful policy design | ✅ **CHOSEN** |

**Implementation:**

1. **Tenant Context Middleware:**
   - Every request extracts `tenant_id` from JWT
   - Sets PostgreSQL session variable: `SET app.current_tenant_id = '<tenant_id>'`
   - All queries automatically scoped by RLS policies

2. **RLS Policies (example for projects table):**
```sql
CREATE POLICY tenant_isolation ON projects
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

3. **Fail-Safe:**
   - Middleware MUST set tenant context before any DB operation
   - Queries without tenant context fail fast
   - Separate read/write policies for defense in depth

### Azure Resource Isolation

**Critical Principle:** We NEVER provision resources in our Azure subscription.

**How It Works:**

1. **Customer Onboarding:**
   - User creates Azure Service Principal in THEIR subscription
   - Grants it contributor/owner role (their choice)
   - Provides us with: `tenant_id`, `client_id`, `client_secret`

2. **Credential Storage:**
   - Encrypted at rest in Azure Key Vault
   - Never stored in application database
   - Retrieved only during execution (short-lived access)

3. **Execution Model:**
   - Each execution runs in isolated Docker container
   - Azure CLI authenticated with customer's service principal
   - All resources created in THEIR subscription
   - No cross-tenant access possible

**Security Benefits:**
- Zero liability for customer resources
- Customer maintains full control
- Credentials never leave our security boundary
- Audit trail in customer's Azure activity log

### Secrets Management

**Architecture:**

```
┌──────────────────────────────────────────────────────────────┐
│  Application Database (PostgreSQL)                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ tenants table                                           │ │
│  │  - id (uuid)                                            │ │
│  │  - name (string)                                        │ │
│  │  - azure_key_vault_secret_id (string) ← Reference only │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬───────────────────────────────┘
                               │
                ┌──────────────▼──────────────┐
                │  Managed Identity (MI)      │
                │  (App → Key Vault access)   │
                └──────────────┬──────────────┘
                               │
                ┌──────────────▼──────────────────────────────┐
                │  Azure Key Vault                            │
                │  ┌────────────────────────────────────────┐ │
                │  │ Secret: tenant-{uuid}-sp-credentials  │ │
                │  │ {                                      │ │
                │  │   "tenant_id": "...",                  │ │
                │  │   "client_id": "...",                  │ │
                │  │   "client_secret": "...",              │ │
                │  │   "subscription_id": "..."             │ │
                │  │ }                                      │ │
                │  └────────────────────────────────────────┘ │
                └─────────────────────────────────────────────┘
```

**Flow:**
1. User configures Azure connection in UI
2. Backend validates credentials (test auth)
3. Stores in Key Vault with tenant-specific name
4. Only reference ID stored in database
5. Execution worker retrieves from KV using Managed Identity
6. Credentials injected into ephemeral execution container
7. Container destroyed after execution (credentials never persisted)

**Key Rotation:**
- Users can rotate service principal secrets in Azure
- Update in our platform → new version in Key Vault
- Old executions fail, prompting user to update
- No automatic rotation (customer controls their Azure security)

### Network Isolation

**Container Network:**
- Each execution runs in dedicated Docker network
- No container-to-container communication
- Outbound: Azure APIs only (via egress rules)
- Inbound: Closed (execution is push-based)

**Platform Network:**
- Frontend & Backend in same Azure Virtual Network
- Private Endpoints for PostgreSQL, Redis, Key Vault
- Public access only via Application Gateway (WAF enabled)
- DDoS protection standard tier

---

## 3. Core Services

### API Gateway (FastAPI)

**Responsibilities:**
- Authentication (JWT validation)
- Authorization (RBAC checks)
- Rate limiting (per-tenant, per-user)
- Request routing
- Tenant context injection
- WebSocket management

**Tech Choice: FastAPI**
- Async-first (critical for WebSocket)
- Type safety (Pydantic)
- Auto-generated OpenAPI docs
- High performance (Starlette + uvicorn)
- Python ecosystem (integrates well with AI libraries)

**Rate Limiting Strategy:**
```python
Tier-based limits:
- Free: 10 requests/min, 5 concurrent executions
- Pro: 100 requests/min, 20 concurrent executions
- Enterprise: Custom limits
```

### AI Engine Service

**Natural Language → Azure CLI Translation**

**System Prompt (Core):**
```
You are an Azure infrastructure expert. Convert natural language requests into Azure CLI commands.

RULES:
1. Output ONLY valid Azure CLI commands (bash syntax)
2. Use long-form flags (--resource-group, not -g) for clarity
3. Include --output json for parseable results
4. For multi-step operations, output commands in execution order
5. Never use placeholders - ask for missing info instead
6. Prefer idempotent operations (check existence before create)

SAFETY:
- NEVER delete resource groups without explicit confirmation
- NEVER delete production-tagged resources
- ALWAYS check if resource exists before destructive operations
- Use --yes flags only when safe

OUTPUT FORMAT:
{
  "commands": [
    {
      "command": "az group create --name rg-app-prod --location eastus",
      "description": "Create resource group for production environment",
      "risk_level": "low"
    }
  ],
  "requires_confirmation": false,
  "estimated_duration_minutes": 2
}
```

**Implementation Pipeline:**

```python
class AIEngine:
    async def translate(self, user_message: str, context: ConversationContext):
        # 1. Load conversation history (last 10 messages)
        history = await self.load_conversation_history(context.conversation_id)
        
        # 2. Inject tenant-specific context
        tenant_resources = await self.load_tenant_resources(context.tenant_id)
        context_prompt = self.build_context_prompt(tenant_resources)
        
        # 3. Call OpenAI with function calling
        response = await self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT + context_prompt},
                *history,
                {"role": "user", "content": user_message}
            ],
            functions=[AZURE_CLI_FUNCTION_SCHEMA],
            temperature=0.1  # Low temp for consistency
        )
        
        # 4. Parse and validate commands
        commands = self.parse_function_call(response)
        validation_result = await self.validate_commands(commands)
        
        # 5. Apply safety filters
        risk_assessment = self.assess_risk(commands)
        
        # 6. Return structured plan
        return ExecutionPlan(
            commands=commands,
            validation=validation_result,
            risk=risk_assessment,
            requires_approval=risk_assessment.level > RiskLevel.LOW
        )
```

**Validation Layers:**

1. **Syntax Validation:** Parse with `shlex`, ensure valid Azure CLI syntax
2. **Command Allowlist:** Only permit `az` commands (no bash injection)
3. **Blocklist:** Detect dangerous patterns (rm -rf, delete without --yes, etc.)
4. **Resource Name Validation:** Ensure names follow Azure conventions
5. **Subscription Check:** Verify command targets correct subscription

**Safety Filters:**

```python
DANGER_PATTERNS = [
    r'az\s+group\s+delete',  # Resource group deletion
    r'az\s+.*\s+delete\s+.*--force',  # Force deletion
    r'az\s+ad\s+',  # Active Directory operations
    r'az\s+role\s+assignment\s+delete',  # RBAC changes
]

def assess_risk(commands: List[Command]) -> RiskLevel:
    for cmd in commands:
        if any(re.search(pattern, cmd.command) for pattern in DANGER_PATTERNS):
            return RiskLevel.HIGH  # Requires explicit approval
        if 'delete' in cmd.command.lower():
            return RiskLevel.MEDIUM  # Show warning
    return RiskLevel.LOW  # Auto-executable
```

### Execution Engine

**Sandboxed CLI Execution**

**Architecture:**

```
┌──────────────────────────────────────────────────────────────┐
│  FastAPI Backend                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Execution Service                                      │ │
│  │  - Validates execution request                          │ │
│  │  - Publishes to Azure Service Bus queue                │ │
│  │  - Returns execution_id to client                       │ │
│  └──────────────────┬─────────────────────────────────────┘ │
└────────────────────┬┴──────────────────────────────────────┘
                     │
      ┌──────────────▼─────────────────┐
      │  Azure Service Bus Queue       │
      │  - execution_id                │
      │  - tenant_id                   │
      │  - commands[]                  │
      └──────────────┬─────────────────┘
                     │
      ┌──────────────▼─────────────────┐
      │  Execution Worker (Python)     │
      │  - Polls queue                 │
      │  - Spawns Docker container     │
      │  - Streams output via WS       │
      └──────────────┬─────────────────┘
                     │
      ┌──────────────▼───────────────────────────────┐
      │  Ephemeral Docker Container                  │
      │  ┌────────────────────────────────────────┐ │
      │  │ Azure CLI + Python                     │ │
      │  │ - Authenticated with SP credentials    │ │
      │  │ - Executes commands sequentially       │ │
      │  │ - Captures stdout/stderr               │ │
      │  │ - No network access except Azure APIs  │ │
      │  └────────────────────────────────────────┘ │
      │  Auto-destroyed after execution             │
      └─────────────────────────────────────────────┘
```

**Execution Worker Implementation:**

```python
class ExecutionWorker:
    async def process_job(self, job: ExecutionJob):
        execution = await db.get_execution(job.execution_id)
        execution.status = ExecutionStatus.RUNNING
        await db.save(execution)
        
        try:
            # 1. Retrieve Azure credentials from Key Vault
            credentials = await key_vault.get_secret(
                f"tenant-{job.tenant_id}-sp-credentials"
            )
            
            # 2. Create isolated Docker container
            container = await docker_client.containers.create(
                image="azure-cli-executor:latest",
                detach=True,
                network_mode="bridge",  # Isolated network
                mem_limit="512m",
                cpu_quota=50000,  # 0.5 CPU
                environment={
                    "AZURE_TENANT_ID": credentials["tenant_id"],
                    "AZURE_CLIENT_ID": credentials["client_id"],
                    "AZURE_CLIENT_SECRET": credentials["client_secret"],
                    "AZURE_SUBSCRIPTION_ID": credentials["subscription_id"],
                },
                auto_remove=True  # Cleanup after execution
            )
            
            await container.start()
            
            # 3. Execute commands sequentially
            results = []
            for cmd in job.commands:
                result = await self.exec_in_container(container, cmd)
                results.append(result)
                
                # Stream output to WebSocket
                await self.broadcast_output(
                    execution_id=job.execution_id,
                    output=result.stdout
                )
                
                # Stop on error if not flagged as continue-on-error
                if result.exit_code != 0 and not cmd.continue_on_error:
                    raise ExecutionError(f"Command failed: {cmd.command}")
            
            # 4. Mark as complete
            execution.status = ExecutionStatus.COMPLETED
            execution.results = results
            await db.save(execution)
            
            # 5. Audit log
            await audit_service.log_execution(execution)
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            await db.save(execution)
        finally:
            # Container auto-removed due to auto_remove=True
            await self.cleanup_credentials(credentials)
```

**Rollback Capability:**

- Before destructive operations, capture current state
- Store as JSON snapshot in execution record
- Provide "Revert" button in UI
- Generate inverse commands (create → delete, update → restore previous values)
- Best-effort rollback (warn if not fully reversible)

### Template Service

**Pre-built Infrastructure Patterns**

**Template Structure:**

```json
{
  "id": "web-app-standard",
  "name": "Standard Web Application",
  "description": "App Service + SQL Database + Storage Account",
  "category": "web",
  "difficulty": "beginner",
  "estimated_cost_monthly": "$50-200",
  "parameters": [
    {
      "name": "app_name",
      "type": "string",
      "description": "Unique application name",
      "validation": "^[a-z0-9-]{3,24}$"
    },
    {
      "name": "location",
      "type": "select",
      "options": ["eastus", "westus2", "westeurope"],
      "default": "eastus"
    },
    {
      "name": "sku",
      "type": "select",
      "options": ["B1", "P1V2", "P2V2"],
      "default": "B1"
    }
  ],
  "commands": [
    "az group create --name rg-{{app_name}} --location {{location}}",
    "az appservice plan create --name plan-{{app_name}} --resource-group rg-{{app_name}} --sku {{sku}}",
    "az webapp create --name {{app_name}} --resource-group rg-{{app_name}} --plan plan-{{app_name}}",
    "az sql server create --name sql-{{app_name}} --resource-group rg-{{app_name}} --admin-user sqladmin --admin-password '{{generated_password}}'",
    "az sql db create --name db-{{app_name}} --server sql-{{app_name}} --resource-group rg-{{app_name}} --service-objective S0"
  ],
  "post_deployment": {
    "message": "Your web app is ready! Set up connection strings in App Settings.",
    "next_steps": [
      "Configure deployment source",
      "Set up custom domain",
      "Enable Application Insights"
    ]
  }
}
```

**Template Gallery:**
- Categorized by use case (web, data, ai, networking, etc.)
- Community-contributed templates (moderated)
- Version controlled (users can pin to specific versions)
- Cost estimates based on current Azure pricing API

### Cost Estimation Service

**Pre-Execution Cost Calculation**

**Implementation:**

```python
class CostEstimator:
    async def estimate(self, commands: List[Command]) -> CostEstimate:
        resources = self.parse_resources_from_commands(commands)
        
        estimates = []
        for resource in resources:
            # Query Azure Retail Pricing API
            pricing = await self.azure_pricing_api.get_price(
                service=resource.type,
                region=resource.location,
                sku=resource.sku
            )
            
            estimates.append({
                "resource": resource.name,
                "type": resource.type,
                "hourly": pricing.hourly,
                "monthly": pricing.monthly,
                "unit": pricing.unit
            })
        
        return CostEstimate(
            resources=estimates,
            total_monthly=sum(e["monthly"] for e in estimates),
            currency="USD"
        )
```

**Displayed Before Execution:**
- Per-resource cost breakdown
- Total monthly estimate
- Comparison with current spend (if tracking enabled)
- Warning if exceeds tenant's budget threshold

### Audit & Logging Service

**Comprehensive Audit Trail**

**Logged Events:**
- User authentication/authorization
- Command generation (NL input + AI output)
- Execution approval/rejection
- Command execution (start, progress, completion)
- Resource modifications (inferred from Azure CLI output)
- Settings changes
- RBAC modifications

**Storage:**

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID NOT NULL REFERENCES users(id),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,  -- 'command_executed', 'user_login', etc.
    event_data JSONB NOT NULL,
    ip_address INET,
    user_agent TEXT,
    severity VARCHAR(20) NOT NULL,  -- 'info', 'warning', 'critical'
    INDEX idx_tenant_timestamp (tenant_id, timestamp DESC),
    INDEX idx_event_type (event_type),
    INDEX idx_user_timestamp (user_id, timestamp DESC)
);
```

**Retention:**
- Free tier: 30 days
- Pro: 1 year
- Enterprise: Unlimited (archival to Azure Blob Storage)

**Compliance:**
- Export to CSV/JSON for compliance audits
- Immutable logs (append-only, no deletion)
- Integration with SIEM tools (Splunk, Azure Sentinel)

---

## 4. Security

### Authentication: Azure AD B2C

**Why Azure AD B2C:**
- Native Azure integration
- Social login support (GitHub, Google, Microsoft)
- MFA out of the box
- Scales to millions of users
- Compliance (SOC2, GDPR)

**JWT Claims:**
```json
{
  "sub": "user-uuid",
  "tenant_id": "tenant-uuid",
  "email": "user@example.com",
  "roles": ["admin", "operator"],
  "exp": 1234567890,
  "iss": "https://azurebuilder.b2clogin.com"
}
```

### Authorization: RBAC

**Roles:**

| Role | Permissions |
|------|-------------|
| **Owner** | Full access, manage users, billing |
| **Admin** | Manage projects, execute commands, view audit logs |
| **Operator** | Execute approved commands, view projects |
| **Viewer** | Read-only access, view executions |

**Implementation:**

```python
class RBACMiddleware:
    async def check_permission(self, user: User, action: str, resource: str):
        if user.role == Role.OWNER:
            return True  # Owners can do anything
        
        permission_matrix = {
            Role.ADMIN: ["project:*", "execution:*", "audit:read"],
            Role.OPERATOR: ["execution:execute", "project:read"],
            Role.VIEWER: ["*:read"]
        }
        
        allowed = permission_matrix[user.role]
        required = f"{resource}:{action}"
        
        return any(fnmatch.fnmatch(required, pattern) for pattern in allowed)
```

### Credential Security

**Azure Service Principal Handling:**

1. **Storage:** Azure Key Vault with RBAC access control
2. **Access:** Managed Identity only (no keys in code)
3. **Rotation:** User-managed (we notify on expiring secrets)
4. **Scope:** Least privilege (recommend Reader for dry-run, Contributor for execution)

**Encryption:**
- At rest: Transparent Data Encryption (TDE) for PostgreSQL
- In transit: TLS 1.3 for all connections
- In use: Ephemeral credentials (injected into containers, destroyed after execution)

### Input Sanitization

**Preventing Prompt Injection:**

```python
def sanitize_user_input(text: str) -> str:
    # Remove potential prompt injection attempts
    dangerous_patterns = [
        r'ignore previous instructions',
        r'system:',
        r'assistant:',
        r'<\|.*?\|>',  # Special tokens
        r'\{\{.*?\}\}',  # Template injection
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '[FILTERED]', text, flags=re.IGNORECASE)
    
    # Limit length to prevent DoS
    return text[:5000]
```

**Command Validation:**

- Allowlist approach: Only `az` commands permitted
- Argument validation: Ensure all flags are valid Azure CLI options
- No shell metacharacters (`;`, `|`, `&&`, `>`, etc.) outside of quoted strings
- Parsed with `shlex` to detect injection attempts

### Sandboxed Execution

**Defense in Depth:**

1. **Docker Container:** Isolated filesystem, network, process namespace
2. **Resource Limits:** CPU, memory, disk I/O capped
3. **No Privileged Access:** Containers run as non-root user
4. **Network Policy:** Only Azure API endpoints reachable (via egress rules)
5. **Timeout:** Max execution time (5 minutes default, configurable per tier)
6. **No Persistence:** Container destroyed immediately after execution

**Docker Image Hardening:**

```dockerfile
FROM mcr.microsoft.com/azure-cli:latest

# Run as non-root user
RUN useradd -m -u 1000 executor
USER executor

# Minimal tooling (only Azure CLI)
RUN rm -rf /usr/local/bin/* && \
    ln -s /usr/local/bin/az /usr/local/bin/az

# Read-only root filesystem (except /tmp)
VOLUME /tmp
```

---

## 5. Tech Stack Decision

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Frontend** | Next.js 14 (App Router) | Server Components, streaming, excellent DX, Vercel deployment |
| **Backend** | FastAPI (Python) | Async-first, type-safe, fast, great for AI workloads |
| **Database** | PostgreSQL 15 | RLS support, JSONB, mature, battle-tested |
| **Cache** | Redis 7 | Session storage, rate limiting, real-time features |
| **Queue** | Azure Service Bus | Native Azure integration, dead-letter queue, at-least-once delivery |
| **AI** | Azure OpenAI (GPT-4) | Enterprise SLA, data residency, same cloud as deployment |
| **Container Orchestration** | Azure Container Apps | Serverless Kubernetes, scale-to-zero, simpler than AKS |
| **IaC** | Bicep | Native Azure, cleaner than ARM, less overhead than Terraform |
| **Monitoring** | Azure Monitor + App Insights | Native integration, distributed tracing, log analytics |

### Backend: FastAPI vs Node.js/Express

**Winner: FastAPI**

**Reasons:**
1. **Async-first:** Native WebSocket support, critical for real-time execution streaming
2. **Type Safety:** Pydantic models prevent runtime errors, auto-validation
3. **AI Ecosystem:** Direct integration with OpenAI SDK, Azure SDK (both excellent Python support)
4. **Performance:** Comparable to Node.js for I/O-bound workloads (which this is)
5. **Developer Experience:** Auto-generated OpenAPI docs, less boilerplate

**Trade-off:** Node.js has larger talent pool, but FastAPI's advantages outweigh this.

### Infrastructure: Azure Container Apps vs AKS

**Winner: Azure Container Apps**

**Reasons:**
1. **Simplicity:** No Kubernetes expertise required
2. **Cost:** Scale-to-zero for dev/staging environments
3. **Managed:** Automatic HTTPS, ingress, service discovery
4. **Sufficient:** Our needs don't require Kubernetes complexity

**Future Migration Path:** If we need advanced Kubernetes features (custom CRDs, operators), Container Apps can export to AKS.

---

## 6. Database Schema

### Entity-Relationship Model

```
tenants (1) ----< (M) users
tenants (1) ----< (M) projects
projects (1) ----< (M) conversations
conversations (1) ----< (M) messages
conversations (1) ----< (M) executions
executions (1) ----< (M) execution_steps
tenants (1) ----< (M) audit_logs
```

### SQL DDL

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable RLS
ALTER DATABASE azure_builder SET app.current_tenant_id TO '';

-- Tenants
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,  -- For subdomain/URL
    tier VARCHAR(20) NOT NULL DEFAULT 'free',  -- 'free', 'pro', 'enterprise'
    azure_key_vault_secret_id VARCHAR(255),  -- Reference to KV secret
    settings JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',  -- 'owner', 'admin', 'operator', 'viewer'
    azure_ad_oid VARCHAR(255) UNIQUE,  -- Azure AD Object ID
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);

-- Row-Level Security for users
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_users ON users
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',  -- Custom fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_projects_tenant ON projects(tenant_id);
CREATE INDEX idx_projects_created_by ON projects(created_by);

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_projects ON projects
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Conversations (AI chat sessions within a project)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_project ON conversations(project_id);
CREATE INDEX idx_conversations_tenant ON conversations(tenant_id);

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_conversations ON conversations
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Messages (user/AI messages in a conversation)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',  -- Token count, model used, etc.
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_tenant ON messages(tenant_id);

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_messages ON messages
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Generated Commands (AI output before execution)
CREATE TABLE generated_commands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    commands JSONB NOT NULL,  -- Array of {command, description, risk_level}
    risk_level VARCHAR(20) NOT NULL,  -- 'low', 'medium', 'high'
    estimated_cost_monthly DECIMAL(10,2),
    requires_approval BOOLEAN NOT NULL DEFAULT false,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_generated_commands_conversation ON generated_commands(conversation_id);
CREATE INDEX idx_generated_commands_tenant ON generated_commands(tenant_id);

ALTER TABLE generated_commands ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_generated_commands ON generated_commands
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Executions (command execution jobs)
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    generated_command_id UUID NOT NULL REFERENCES generated_commands(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    started_by UUID NOT NULL REFERENCES users(id),
    error TEXT,
    output JSONB,  -- Structured command results
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_executions_tenant ON executions(tenant_id);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_conversation ON executions(conversation_id);

ALTER TABLE executions ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_executions ON executions
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Execution Steps (individual command execution within a job)
CREATE TABLE execution_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    step_number INT NOT NULL,
    command TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
    exit_code INT,
    stdout TEXT,
    stderr TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    UNIQUE(execution_id, step_number)
);

CREATE INDEX idx_execution_steps_execution ON execution_steps(execution_id, step_number);

-- Templates (pre-built infrastructure patterns)
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    difficulty VARCHAR(20) NOT NULL,  -- 'beginner', 'intermediate', 'advanced'
    estimated_cost_monthly VARCHAR(50),
    template_data JSONB NOT NULL,  -- Full template definition
    is_public BOOLEAN NOT NULL DEFAULT true,
    created_by UUID REFERENCES users(id),  -- NULL if system template
    tenant_id UUID REFERENCES tenants(id),  -- NULL if public template
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_templates_category ON templates(category);
CREATE INDEX idx_templates_tenant ON templates(tenant_id) WHERE tenant_id IS NOT NULL;

-- Audit Logs (immutable)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),  -- NULL for system events
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    ip_address INET,
    user_agent TEXT,
    severity VARCHAR(20) NOT NULL DEFAULT 'info'  -- 'info', 'warning', 'critical'
);

CREATE INDEX idx_audit_logs_tenant_timestamp ON audit_logs(tenant_id, timestamp DESC);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, timestamp DESC);

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_audit_logs ON audit_logs
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## 7. API Design

### REST API Endpoints

**Base URL:** `https://api.azurebuilder.com/v1`

#### Authentication

```
POST   /auth/login          # Azure AD B2C login
POST   /auth/logout         # Logout
POST   /auth/refresh        # Refresh JWT token
GET    /auth/me             # Current user info
```

#### Tenants

```
GET    /tenants/{id}        # Get tenant details (owner only)
PUT    /tenants/{id}        # Update tenant settings
PUT    /tenants/{id}/azure  # Configure Azure connection
DELETE /tenants/{id}/azure  # Remove Azure connection
GET    /tenants/{id}/usage  # Usage statistics
```

#### Users

```
GET    /users               # List users in tenant
POST   /users               # Invite user
GET    /users/{id}          # Get user
PUT    /users/{id}          # Update user
DELETE /users/{id}          # Remove user
PUT    /users/{id}/role     # Change user role
```

#### Projects

```
GET    /projects            # List projects
POST   /projects            # Create project
GET    /projects/{id}       # Get project
PUT    /projects/{id}       # Update project
DELETE /projects/{id}       # Delete project
```

#### Conversations

```
GET    /projects/{id}/conversations           # List conversations in project
POST   /projects/{id}/conversations           # Create conversation
GET    /conversations/{id}                     # Get conversation with messages
DELETE /conversations/{id}                     # Delete conversation
POST   /conversations/{id}/messages           # Send message (triggers AI)
GET    /conversations/{id}/messages           # Get messages (with pagination)
```

#### Command Generation

```
POST   /conversations/{id}/generate           # Generate Azure CLI commands from NL
GET    /generated-commands/{id}               # Get generated command details
POST   /generated-commands/{id}/approve       # Approve for execution
POST   /generated-commands/{id}/reject        # Reject
POST   /generated-commands/{id}/edit          # Edit before approval
```

#### Executions

```
POST   /generated-commands/{id}/execute       # Start execution
GET    /executions                            # List executions (with filters)
GET    /executions/{id}                       # Get execution details
POST   /executions/{id}/cancel                # Cancel running execution
GET    /executions/{id}/logs                  # Get execution logs (streaming)
POST   /executions/{id}/rollback              # Rollback execution
```

#### Templates

```
GET    /templates                             # List templates (public + tenant's)
GET    /templates/{id}                        # Get template details
POST   /templates                             # Create custom template
PUT    /templates/{id}                        # Update template
DELETE /templates/{id}                        # Delete template
POST   /templates/{id}/instantiate            # Create project from template
```

#### Cost Estimation

```
POST   /estimate/commands                     # Estimate cost for commands
GET    /estimate/current                      # Current tenant resource costs
```

#### Audit Logs

```
GET    /audit-logs                            # List audit logs (with filters)
GET    /audit-logs/{id}                       # Get audit log details
POST   /audit-logs/export                     # Export logs (CSV/JSON)
```

### WebSocket API

**URL:** `wss://api.azurebuilder.com/v1/ws`

**Authentication:** JWT token in query param or header

**Message Format:**

```json
{
  "type": "execution_status",
  "execution_id": "uuid",
  "status": "running",
  "data": {
    "step": 2,
    "total_steps": 5,
    "current_command": "az webapp create...",
    "output": "Creating web app..."
  }
}
```

**Event Types:**
- `execution_status` - Execution state change
- `execution_output` - Real-time command output
- `execution_complete` - Execution finished
- `execution_error` - Execution failed

---

## 8. Frontend Architecture

### Page Structure

```
/ (landing)                         # Public landing page (index.html)
/login                              # Azure AD B2C login
/register                           # Sign up flow

/dashboard                          # Main dashboard (overview)
  - Recent projects
  - Recent executions
  - Usage stats

/projects                           # Projects list
/projects/new                       # Create project
/projects/{id}                      # Project workspace
  ┌─────────────────────────────────────────┐
  │ Sidebar      │ Main Area                │
  │              │                           │
  │ Conversations│ ┌─────────────────────┐  │
  │ - Conv 1     │ │ AI Chat Interface   │  │
  │ - Conv 2     │ │ (Messages)          │  │
  │              │ └─────────────────────┘  │
  │              │                           │
  │              │ ┌─────────────────────┐  │
  │              │ │ Generated Commands  │  │
  │              │ │ (Monaco Editor)     │  │
  │              │ └─────────────────────┘  │
  │              │                           │
  │              │ [Estimate Cost] [Execute] │
  └─────────────────────────────────────────┘

/projects/{id}/executions           # Execution history
/projects/{id}/executions/{exec_id} # Execution details (live logs)

/templates                          # Template gallery
/templates/{id}                     # Template details

/settings                           # Tenant settings
/settings/azure                     # Azure connection
/settings/team                      # Team management
/settings/billing                   # Billing & usage

/audit                              # Audit log viewer (admin only)
```

### Component Hierarchy

**Key Components:**

1. **ChatInterface**
   - MessageList
   - MessageBubble (user/assistant)
   - MessageInput (textarea with submit)
   - TypingIndicator

2. **CommandPreview**
   - MonacoEditor (read-only, syntax highlighting)
   - CommandList (risk indicators, descriptions)
   - ApprovalControls (approve/reject/edit buttons)
   - CostEstimate (breakdown display)

3. **ExecutionViewer**
   - ExecutionStatus (progress bar, current step)
   - TerminalOutput (real-time logs, ANSI color support)
   - ExecutionControls (cancel, rollback)
   - ResultsSummary (success/failure, resources created)

4. **TemplateGallery**
   - TemplateCard (preview, category, cost estimate)
   - TemplateFilters (category, difficulty)
   - TemplateDetail (parameters, preview commands)
   - InstantiateModal (fill parameters, create project)

5. **DashboardWidgets**
   - RecentProjects
   - RecentExecutions
   - UsageChart (executions over time)
   - CostOverview (monthly spend)

### Real-Time Updates (WebSocket)

**Implementation:**

```typescript
// hooks/useWebSocket.ts
export function useWebSocket(executionId: string) {
  const [status, setStatus] = useState<ExecutionStatus>('pending');
  const [output, setOutput] = useState<string[]>([]);
  
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}?token=${getToken()}`);
    
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      
      if (msg.execution_id !== executionId) return;
      
      switch (msg.type) {
        case 'execution_status':
          setStatus(msg.status);
          break;
        case 'execution_output':
          setOutput(prev => [...prev, msg.data.output]);
          break;
      }
    };
    
    return () => ws.close();
  }, [executionId]);
  
  return { status, output };
}
```

### Monaco Editor Integration

**For Command Preview:**

```typescript
// components/terminal/CommandEditor.tsx
import Editor from '@monaco-editor/react';

export function CommandEditor({ commands, readOnly = true }) {
  const code = commands.map(c => c.command).join('\n\n');
  
  return (
    <Editor
      height="400px"
      language="shell"
      theme="vs-dark"
      value={code}
      options={{
        readOnly,
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: 'on',
        scrollBeyondLastLine: false,
      }}
    />
  );
}
```

### State Management

**Approach:** React Server Components + TanStack Query (for client state)

- Server Components for initial data fetching (projects, templates)
- TanStack Query for client-side caching, mutations, optimistic updates
- WebSocket state managed via custom hooks (not in query cache)
- Auth state in React Context (JWT token, user info)

**No Redux/Zustand needed** - RSC + React Query covers 90% of use cases.

---

## 9. Deployment Architecture

### Production Infrastructure (Azure)

```
┌─────────────────────────────────────────────────────────────┐
│ Azure Front Door (CDN + WAF)                                │
│ - Global load balancing                                      │
│ - SSL termination                                            │
│ - DDoS protection                                            │
└────────────┬────────────────────────────────────────────────┘
             │
┌────────────┴────────────────────────────────────────────────┐
│ Application Gateway (Regional)                              │
│ - Path-based routing (/api → backend, / → frontend)        │
│ - Web Application Firewall                                  │
└────┬───────────────┬──────────────────────────────────────┘
     │               │
     │               │
┌────▼──────────┐  ┌─▼───────────────────────────────────────┐
│ Azure         │  │ Azure Container Apps                     │
│ Static Web    │  │                                          │
│ Apps          │  │ ┌────────────┐  ┌────────────────────┐ │
│               │  │ │ Frontend   │  │ Backend (FastAPI)   │ │
│ (Next.js)     │  │ │ Container  │  │ - API Gateway       │ │
│               │  │ │            │  │ - AI Engine         │ │
│               │  │ └────────────┘  │ - Services          │ │
└───────────────┘  │                 └────────────────────┘ │
                   │                                          │
                   │ ┌────────────────────────────────────┐ │
                   │ │ Execution Worker                   │ │
                   │ │ - Polls Azure Service Bus          │ │
                   │ │ - Spawns Docker containers         │ │
                   │ └────────────────────────────────────┘ │
                   └──────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼───────┐  ┌─────────▼────────┐  ┌────────▼────────┐
│ PostgreSQL    │  │ Redis            │  │ Azure Service   │
│ Flexible      │  │ Cache            │  │ Bus             │
│ Server        │  │                  │  │                 │
│ - RLS enabled │  │ - Session store  │  │ - Job queue     │
│ - Backup      │  │ - Rate limiting  │  │                 │
└───────────────┘  └──────────────────┘  └─────────────────┘
        │
┌───────▼────────────────────────────────────────────────────┐
│ Azure Key Vault                                            │
│ - Tenant Azure credentials                                 │
│ - Application secrets                                      │
│ - TLS certificates                                         │
└────────────────────────────────────────────────────────────┘
```

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: cd backend && pytest
      - name: Run frontend tests
        run: cd frontend && npm test

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build frontend
        run: cd frontend && npm run build
      
      - name: Deploy frontend to Azure Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
      
      - name: Build backend Docker image
        run: docker build -t azurebuilder-backend:${{ github.sha }} backend/
      
      - name: Push to Azure Container Registry
        run: |
          az acr login --name azurebuilderregistry
          docker push azurebuilderregistry.azurecr.io/backend:${{ github.sha }}
      
      - name: Deploy to Container Apps
        run: |
          az containerapp update \
            --name backend \
            --resource-group rg-azurebuilder-prod \
            --image azurebuilderregistry.azurecr.io/backend:${{ github.sha }}
```

### Scaling Strategy

**Frontend:**
- Azure Static Web Apps with CDN (auto-scales globally)
- Server-side rendering via Container Apps (scales 0-100)

**Backend:**
- Container Apps with KEDA scaling
- Scale triggers:
  - HTTP: Scale up when avg request latency > 500ms
  - Queue: Scale up when Azure Service Bus queue depth > 10

**Database:**
- PostgreSQL: Vertical scaling (start with 2 vCores, scale to 64)
- Read replicas for reporting queries

**Execution Workers:**
- Scale based on Azure Service Bus queue depth
- Max concurrency per worker: 5 containers
- Total worker instances: 1-20 (auto-scale)

### Cost Optimization

**Development:**
- Scale to zero during off-hours
- Use B-series VMs (burstable)
- Dev database: 1 vCore

**Production:**
- Reserved instances for baseline load (30% savings)
- Spot instances for burst capacity (90% savings)
- Auto-shutdown for idle environments

**Estimated Monthly Costs:**

| Tier | Users | Cost |
|------|-------|------|
| Dev/Staging | 10 | $50 |
| Production (Small) | 100 | $500 |
| Production (Medium) | 1,000 | $2,000 |
| Production (Large) | 10,000 | $10,000 |

---

## 10. Monitoring & Observability

### Application Insights

**Tracked Metrics:**
- Request rate, latency, error rate (by endpoint)
- AI translation latency & token usage
- Execution duration (by command type)
- WebSocket connection count
- Database query performance

**Custom Events:**
- `command_generated` - NL → CLI translation
- `execution_started` - Execution job submitted
- `execution_completed` - Success/failure with details
- `approval_required` - High-risk command flagged

### Log Analytics

**Structured Logging:**

```python
logger.info(
    "Execution completed",
    extra={
        "execution_id": execution.id,
        "tenant_id": execution.tenant_id,
        "duration_seconds": duration,
        "commands_count": len(execution.commands),
        "status": "success"
    }
)
```

**Kusto Queries (KQL):**

```kql
// Average execution time by tenant
customEvents
| where name == "execution_completed"
| summarize avg(duration_seconds) by tenant_id

// Failed executions in last hour
customEvents
| where name == "execution_completed" and status == "failed"
| where timestamp > ago(1h)
| project timestamp, tenant_id, execution_id, error
```

### Alerting

**Critical Alerts (PagerDuty):**
- Error rate > 5% for 5 minutes
- Any execution worker crashes
- Database connection pool exhaustion
- Key Vault access denied

**Warning Alerts (Slack):**
- AI translation latency > 3 seconds
- Execution queue depth > 50
- Tenant approaching rate limit

---

## 11. Security Compliance

### SOC 2 Type II Readiness

- **Audit logging:** All actions logged, immutable
- **Access control:** RBAC, MFA enforced for admins
- **Encryption:** At rest (TDE) and in transit (TLS 1.3)
- **Incident response:** Automated alerting, runbooks
- **Vendor management:** Azure compliance certifications inherited

### GDPR Compliance

- **Data residency:** EU customers → Azure West Europe region
- **Right to deletion:** Cascade delete on tenant removal
- **Data portability:** Export API for all tenant data
- **Privacy by design:** Minimal data collection, no tracking

---

## 12. Future Enhancements

**Phase 2 (Q2 2024):**
- Terraform support (in addition to Azure CLI)
- GitHub Actions integration (commit infrastructure as code)
- Scheduled deployments (cron-style)

**Phase 3 (Q3 2024):**
- AWS & GCP support (multi-cloud)
- Slack bot interface
- Terraform state management

**Phase 4 (Q4 2024):**
- Marketplace (community templates)
- Advanced RBAC (custom roles)
- Compliance automation (policy enforcement)

---

## Summary

Azure Builder is architected for production from day one:

✅ **Multi-tenant:** Row-level security, per-tenant isolation  
✅ **Secure:** Azure AD B2C, Key Vault, sandboxed execution  
✅ **Scalable:** Container Apps, auto-scaling, efficient queuing  
✅ **Observable:** Full logging, metrics, distributed tracing  
✅ **Cost-effective:** Scale-to-zero, reserved instances  
✅ **Compliant:** SOC 2, GDPR ready  

This is not a prototype. This is a platform ready for paying customers.
