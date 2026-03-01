# Azure Builder - Example Usage

## Scenario: Teams Chatbot with $300/month Budget

### 1. Create Project with Budget

**Request:**
```http
POST /api/v1/projects
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Customer Support Bot",
  "description": "Teams chatbot for 24/7 customer support",
  "budget_limit": 300.00
}
```

**Response:**
```json
{
  "id": "uuid-123",
  "name": "Customer Support Bot",
  "description": "Teams chatbot for 24/7 customer support",
  "budget_limit": 300.00,
  "status": "active",
  "created_at": "2026-03-01T16:00:00Z"
}
```

---

### 2. Request Architecture Proposal

**Request:**
```http
POST /api/v1/projects/uuid-123/proposals
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_request": "I need a Teams chatbot that can handle customer support queries, with SQL database for storing conversation history and user preferences"
}
```

**Response (Simplified):**
```json
{
  "id": "proposal-456",
  "project_id": "uuid-123",
  "status": "ready",
  "user_request": "I need a Teams chatbot...",
  "options": [
    {
      "option_number": 1,
      "name": "Serverless Chatbot",
      "description": "Azure Functions-based bot with Cosmos DB serverless storage. Scales to zero when not in use. Ideal for small to medium traffic.",
      "monthly_cost": 45.00,
      "architecture_diagram": "graph TB\n    Teams[Microsoft Teams]\n    BotService[Azure Bot Service<br/>F0 Free]\n    Functions[Azure Functions<br/>Consumption]\n    CosmosDB[(Cosmos DB<br/>Serverless)]\n    AppInsights[Application Insights]\n    KeyVault[Key Vault]\n    \n    Teams -->|Messages| BotService\n    BotService -->|Process| Functions\n    Functions -->|Store| CosmosDB\n    Functions -->|Secrets| KeyVault\n    Functions -->|Logs| AppInsights",
      "pros_cons_json": {
        "pros": [
          "Lowest cost at $45/month",
          "Auto-scales to zero (no idle costs)",
          "No infrastructure management",
          "Fast deployment"
        ],
        "cons": [
          "Cold start latency (~2-3 seconds)",
          "Limited to 10GB storage in Cosmos serverless",
          "May struggle with high concurrent users"
        ],
        "security_report": {
          "score": 85,
          "passed_checks": 6,
          "total_checks": 7,
          "has_critical": false,
          "has_high": false,
          "issues": [
            {
              "severity": "medium",
              "category": "Network Security",
              "issue": "Compute resources without Virtual Network isolation",
              "recommendation": "Deploy resources in a Virtual Network for network isolation and security",
              "doc_link": "https://learn.microsoft.com/azure/virtual-network/virtual-networks-overview"
            }
          ]
        },
        "budget_exceeded": false
      },
      "resources_json": {
        "resources": [
          {
            "type": "Azure Bot Service",
            "name": "bot-support-prod",
            "sku": "F0",
            "region": "eastus",
            "properties": {
              "messaging_endpoint": "https://func-support-prod.azurewebsites.net/api/messages"
            }
          },
          {
            "type": "Azure Functions",
            "name": "func-support-prod",
            "sku": "Consumption",
            "region": "eastus",
            "properties": {
              "runtime": "node",
              "version": "18"
            }
          },
          {
            "type": "Cosmos DB Account",
            "name": "cosmos-support-prod",
            "sku": "Serverless",
            "region": "eastus",
            "properties": {
              "api": "SQL",
              "consistency": "Session"
            }
          },
          {
            "type": "Key Vault",
            "name": "kv-support-prod",
            "sku": "Standard",
            "region": "eastus",
            "properties": {}
          },
          {
            "type": "Application Insights",
            "name": "appi-support-prod",
            "sku": "Standard",
            "region": "eastus",
            "properties": {}
          }
        ]
      }
    },
    {
      "option_number": 2,
      "name": "Container-Based Chatbot",
      "description": "Azure Container Apps with SQL Database. Always-on service with persistent connections. Better performance and no cold starts.",
      "monthly_cost": 180.00,
      "architecture_diagram": "graph TB\n    Teams[Microsoft Teams]\n    BotService[Azure Bot Service<br/>S1]\n    ContainerApp[Container App<br/>1 vCPU, 2GB]\n    SQL[(SQL Database<br/>Basic)]\n    AppInsights[Application Insights]\n    KeyVault[Key Vault]\n    \n    Teams -->|Messages| BotService\n    BotService -->|Process| ContainerApp\n    ContainerApp -->|Query| SQL\n    ContainerApp -->|Secrets| KeyVault\n    ContainerApp -->|Logs| AppInsights",
      "pros_cons_json": {
        "pros": [
          "No cold starts (always ready)",
          "Better performance under load",
          "Persistent database connections",
          "Auto-scaling support"
        ],
        "cons": [
          "Higher cost at $180/month",
          "Requires container management",
          "Basic SQL tier may be slow for complex queries"
        ],
        "security_report": {
          "score": 71,
          "passed_checks": 5,
          "total_checks": 7,
          "has_critical": false,
          "has_high": true,
          "issues": [
            {
              "severity": "high",
              "category": "Network Security",
              "resource_type": "Microsoft.Sql/servers",
              "resource_name": "sql-support-prod",
              "issue": "Database server 'sql-support-prod' allows public network access",
              "recommendation": "Disable public access and use Private Endpoints or VNet integration",
              "doc_link": "https://learn.microsoft.com/azure/postgresql/flexible-server/concepts-networking"
            },
            {
              "severity": "medium",
              "category": "Network Security",
              "issue": "Compute resources without Network Security Groups",
              "recommendation": "Add Network Security Groups to control inbound/outbound traffic",
              "doc_link": "https://learn.microsoft.com/azure/virtual-network/network-security-groups-overview"
            }
          ]
        },
        "budget_exceeded": false
      }
    },
    {
      "option_number": 3,
      "name": "Enterprise Chatbot with AI",
      "description": "Full enterprise setup with Azure OpenAI integration for intelligent responses, premium SQL, Redis caching, and Private Endpoints.",
      "monthly_cost": 520.00,
      "architecture_diagram": "graph TB\n    Teams[Microsoft Teams]\n    BotService[Azure Bot Service<br/>S1]\n    ContainerApp[Container App<br/>2 vCPU, 4GB]\n    SQL[(SQL Database<br/>S1)]\n    Redis[Redis Cache<br/>Basic C1]\n    OpenAI[Azure OpenAI<br/>GPT-4]\n    AppInsights[Application Insights]\n    KeyVault[Key Vault]\n    VNet[Virtual Network]\n    \n    Teams -->|Messages| BotService\n    BotService -->|Process| ContainerApp\n    ContainerApp -->|Query| SQL\n    ContainerApp -->|Cache| Redis\n    ContainerApp -->|AI| OpenAI\n    ContainerApp -->|Secrets| KeyVault\n    ContainerApp -->|Logs| AppInsights\n    \n    subgraph VNet\n        ContainerApp\n        SQL\n        Redis\n    end",
      "pros_cons_json": {
        "pros": [
          "AI-powered intelligent responses",
          "Excellent performance (S1 SQL, Redis caching)",
          "High availability and redundancy",
          "Full network isolation with VNet",
          "Can handle 10,000+ daily users"
        ],
        "cons": [
          "Exceeds budget at $520/month",
          "Complex architecture requires expertise",
          "OpenAI costs can spike with heavy usage",
          "Overkill for small deployments"
        ],
        "security_report": {
          "score": 100,
          "passed_checks": 7,
          "total_checks": 7,
          "has_critical": false,
          "has_high": false,
          "issues": []
        },
        "budget_exceeded": true
      }
    }
  ]
}
```

---

### 3. Frontend Display

#### Option 1: Serverless (Within Budget) ✅
```
┌─────────────────────────────────────────────────────────┐
│ 🟢 Option 1: Serverless Chatbot                        │
│ Monthly Cost: $45.00 ✓ Within budget                   │
│ Security Score: 85/100 ⚠️ 1 medium issue                │
├─────────────────────────────────────────────────────────┤
│ [Mermaid Diagram Renders Here]                          │
├─────────────────────────────────────────────────────────┤
│ 👍 Pros:                                                 │
│ • Lowest cost at $45/month                              │
│ • Auto-scales to zero (no idle costs)                   │
│ • No infrastructure management                          │
│                                                          │
│ 👎 Cons:                                                 │
│ • Cold start latency (~2-3 seconds)                     │
│ • Limited to 10GB storage                               │
│                                                          │
│ ⚠️ Security:                                             │
│ • MEDIUM: Resources not in Virtual Network              │
│   → Deploy in VNet for better isolation                 │
│                                                          │
│ [Select This Option] [View Details] [Download Bicep]   │
└─────────────────────────────────────────────────────────┘
```

#### Option 2: Container-Based (Within Budget) ✅
```
┌─────────────────────────────────────────────────────────┐
│ 🟡 Option 2: Container-Based Chatbot                   │
│ Monthly Cost: $180.00 ✓ Within budget                  │
│ Security Score: 71/100 🔴 1 high issue                  │
├─────────────────────────────────────────────────────────┤
│ [Mermaid Diagram Renders Here]                          │
├─────────────────────────────────────────────────────────┤
│ 👍 Pros:                                                 │
│ • No cold starts                                        │
│ • Better performance                                    │
│ • Auto-scaling support                                  │
│                                                          │
│ 👎 Cons:                                                 │
│ • Higher cost                                           │
│ • Requires container management                         │
│                                                          │
│ 🔴 Security Issues (HIGH):                              │
│ • SQL Server allows public network access              │
│   → Use Private Endpoints or disable public access     │
│                                                          │
│ [Select This Option] [View Details] [Download Bicep]   │
└─────────────────────────────────────────────────────────┘
```

#### Option 3: Enterprise (Over Budget) ❌
```
┌─────────────────────────────────────────────────────────┐
│ 🔴 Option 3: Enterprise Chatbot with AI                │
│ Monthly Cost: $520.00 ⚠️ $220 over budget               │
│ Security Score: 100/100 ✅ Perfect                      │
├─────────────────────────────────────────────────────────┤
│ [Mermaid Diagram Renders Here]                          │
├─────────────────────────────────────────────────────────┤
│ 👍 Pros:                                                 │
│ • AI-powered intelligent responses                      │
│ • Excellent performance                                 │
│ • Full network isolation                                │
│                                                          │
│ 👎 Cons:                                                 │
│ • Exceeds budget at $520/month                          │
│ • Complex architecture                                  │
│ • OpenAI costs can spike                                │
│                                                          │
│ ✅ Security: No issues found                            │
│                                                          │
│ [Select Anyway] [View Details] [Download Bicep]        │
└─────────────────────────────────────────────────────────┘
```

---

### 4. User Selects Option 2

**Request:**
```http
POST /api/v1/proposals/proposal-456/select
Authorization: Bearer <token>
Content-Type: application/json

{
  "selected_option_number": 2
}
```

---

### 5. Review Deployment (Before Approval)

**Request:**
```http
GET /api/v1/deployments/{deployment-id}/review
```

**Response:**
```json
{
  "deployment_id": "deploy-789",
  "status": "pending_approval",
  "monthly_cost": 180.00,
  "resources_to_create": 7,
  "security_warnings": [
    "SQL Server allows public network access (HIGH)"
  ],
  "resource_list": [
    "Azure Bot Service (bot-support-prod) - S1",
    "Container App (ca-support-prod) - 1 vCPU, 2GB",
    "SQL Server (sql-support-prod) - Basic",
    "SQL Database (db-support-prod) - Basic",
    "Application Insights (appi-support-prod)",
    "Key Vault (kv-support-prod)",
    "Log Analytics Workspace (log-support-prod)"
  ],
  "bicep_template": "... [full Bicep code] ..."
}
```

---

### 6. Approve and Deploy

**Request:**
```http
POST /api/v1/deployments/deploy-789/approve
Authorization: Bearer <token>
Content-Type: application/json

{
  "acknowledge_warnings": true,
  "parameters": {
    "sql_admin_password": "<from-keyvault>"
  }
}
```

**Response:**
```json
{
  "deployment_id": "deploy-789",
  "status": "deploying",
  "message": "Deployment started. Track progress at /deployments/deploy-789/logs"
}
```

---

## Key Features Demonstrated

### ✅ Budget Awareness
- Project has $300/month budget
- Options 1 & 2 are within budget
- Option 3 is flagged as exceeding budget by $220

### ✅ Visual Diagrams
- Mermaid.js syntax generates professional diagrams
- Shows all components and relationships
- Includes SKU information

### ✅ Security Validation
- Automated security scan for each option
- Severity-based warnings (CRITICAL, HIGH, MEDIUM, LOW)
- Actionable recommendations with documentation links
- Security score (0-100)

### ✅ Approval Workflow
- Review before deployment
- See all resources, costs, and warnings
- Must acknowledge security warnings
- Download Bicep template

---

## Implementation Notes

### Frontend Rendering (Mermaid)

Install Mermaid:
```bash
npm install mermaid
```

Render in React:
```tsx
import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

function ArchitectureDiagram({ diagram }: { diagram: string }) {
  const ref = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (ref.current) {
      mermaid.initialize({ 
        startOnLoad: true,
        theme: 'default',
        securityLevel: 'loose'
      });
      mermaid.render('mermaid-diagram', diagram).then(({ svg }) => {
        if (ref.current) {
          ref.current.innerHTML = svg;
        }
      });
    }
  }, [diagram]);
  
  return <div ref={ref} className="architecture-diagram" />;
}
```

### Budget Badge Component

```tsx
function BudgetBadge({ cost, limit }: { cost: number; limit?: number }) {
  if (!limit) return null;
  
  const exceeded = cost > limit;
  const diff = cost - limit;
  
  if (exceeded) {
    return (
      <Badge color="red">
        💰 ${diff.toFixed(2)} over budget
      </Badge>
    );
  }
  
  return (
    <Badge color="green">
      ✓ Within budget (${(limit - cost).toFixed(2)} remaining)
    </Badge>
  );
}
```

### Security Score Display

```tsx
function SecurityScore({ report }: { report: SecurityReport }) {
  const color = report.score >= 90 ? 'green' 
              : report.score >= 70 ? 'yellow' 
              : 'red';
  
  return (
    <div className="security-score">
      <Progress value={report.score} color={color} />
      <span>{report.score}/100</span>
      
      {report.has_critical && (
        <Alert severity="error">Critical security issues found</Alert>
      )}
      
      {report.has_high && !report.has_critical && (
        <Alert severity="warning">High-priority recommendations</Alert>
      )}
    </div>
  );
}
```

---

**This example demonstrates the complete flow of the enhanced Azure Builder with budget constraints, visual diagrams, and security validation.**
