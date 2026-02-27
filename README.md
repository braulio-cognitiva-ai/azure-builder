# Azure Builder

**AI Solution Architect as a Service**

Transform natural language into production-ready Azure infrastructure. Get 2-3 architecture options with real-time costs, review generated Bicep templates, approve, and deploy—all from a conversational interface.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)

---

## 🎯 What is Azure Builder?

**Azure Builder is NOT a CLI wrapper.** It's an intelligent solution architect that:

1. **Listens** to your needs in natural language
2. **Proposes** 2-3 architecture options with different trade-offs
3. **Estimates** real-time costs from Azure Retail Prices API
4. **Generates** Bicep/ARM templates automatically
5. **Provisions** resources with approval workflows
6. **Monitors** deployment progress with live logs

### Example Conversation

```
You: I need a web API with authentication and SQL database. Budget is $200/month.

Azure Builder: I've designed 3 architecture options for you:

Option 1: Basic Web API ($55/month)
  • App Service (B1)
  • SQL Database (Basic)
  • Storage Account
  • Key Vault
  • Application Insights
  ✅ Lowest cost, simple architecture
  ❌ No auto-scaling, 5 DTU may be slow

Option 2: Scalable Web API ($245/month)
  • App Service (P1V2)
  • SQL Database (S1)
  • Redis Cache
  • Key Vault
  • Application Insights
  ✅ Auto-scaling, better performance
  ❌ Higher cost

Option 3: Enterprise Web API ($850/month)
  • App Service (P3V2)
  • SQL Database (P1)
  • Redis Cache (Premium)
  • Application Gateway
  • Key Vault
  • Application Insights
  ✅ High availability, multi-region ready
  ❌ Highest cost

Which option would you like to deploy?

You: Option 2 looks good. Let's deploy it.

Azure Builder: Great choice! Generating deployment plan...
  [Shows Bicep template, resource list, and total cost]
  Ready to deploy. Click "Approve & Deploy" to proceed.
```

---

## ✨ Key Features

### 🤖 AI-Powered Architecture Design
- **Natural Language Input:** Describe what you need in plain English
- **Multi-Option Proposals:** Get 2-3 distinct architectures with different SKU tiers
- **Context-Aware:** Integrates with your existing Azure infrastructure
- **Template Library:** 8 pre-built patterns (web apps, microservices, data pipelines, AI/ML)

### 💰 Real-Time Cost Estimation
- **Azure Retail Prices API:** Always up-to-date pricing
- **Regional Comparisons:** See cost differences across regions
- **SKU Comparisons:** Compare P1V2 vs P2V2 vs P3V2
- **Monthly Breakdowns:** Know exactly what you'll pay

### 🔒 Enterprise-Ready Security
- **Azure AD B2C Integration:** SSO with social logins
- **Role-Based Access Control:** Admin, Operator, Viewer roles
- **Tenant Data Isolation:** Row-level security (RLS) in PostgreSQL
- **Azure Key Vault:** Secure credential storage
- **OAuth2 for Azure:** No permanent credentials, token-based access

### ✅ Approval Workflows
- **Review Before Deploy:** See all resources, costs, and warnings
- **Bicep/ARM Templates:** Download generated infrastructure code
- **Multi-User Approval:** Operator creates, Admin approves
- **Audit Trail:** Complete history of who did what, when

### 🚀 Full Deployment Lifecycle
- **Automatic Bicep Generation:** From architecture to code
- **Real-Time Progress:** Live logs during provisioning
- **Resource Tracking:** Monitor each resource individually
- **Rollback Support:** Undo deployments when needed
- **Drift Detection:** Alert when manual changes occur

### 🏢 Multi-Tenant SaaS
- **Complete Tenant Isolation:** Data, credentials, rate limits
- **Plan Tiers:** Free, Pro, Enterprise with different quotas
- **Usage Analytics:** Track proposals, deployments, costs per tenant
- **White-Label Ready:** Customize branding per tenant

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Architecture Overview](#-architecture-overview)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [MVP Deployment](#-mvp-deployment)
- [Development](#-development)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (for local development)
- **Node.js 20+** (for frontend)
- **Python 3.11+** (for backend)
- **PostgreSQL 15+** (or SQLite for quick start)
- **Azure Subscription** (for testing deployments)
- **Azure OpenAI** (or OpenAI API key)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/azure-builder.git
cd azure-builder
```

### 2. Quick Start with Docker Compose

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env

# Start all services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# Run database migrations
docker-compose exec backend alembic upgrade head

# Seed templates
docker-compose exec backend python scripts/seed_templates.py
```

### 3. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Swagger UI)

### 4. Create Your First Project

1. Sign up at http://localhost:3000/signup
2. Create a new project
3. Connect your Azure subscription (Settings → Azure)
4. Start a conversation: "I need a web app with SQL database"
5. Review proposals
6. Select an option
7. Approve and deploy!

---

## 🏗️ Architecture Overview

Azure Builder follows a modern SaaS architecture with clear separation of concerns:

```
┌─────────────┐         ┌─────────────┐         ┌──────────────┐
│   Browser   │────────▶│  Next.js    │────────▶│   FastAPI    │
│   (React)   │  HTTPS  │  Frontend   │   REST  │   Backend    │
└─────────────┘         └─────────────┘         └───────┬──────┘
                                                         │
                        ┌────────────────────────────────┼─────────────┐
                        │                                │             │
                        ▼                                ▼             ▼
                ┌───────────────┐              ┌──────────────┐  ┌──────────┐
                │  PostgreSQL   │              │ Azure OpenAI │  │  Redis   │
                │   (Data)      │              │  (GPT-4)     │  │  (Cache) │
                └───────────────┘              └──────────────┘  └──────────┘
                        │
                        ▼
                ┌────────────────────────────────────────────────────┐
                │  Azure Resources (Deployed by Platform)           │
                │  • App Services  • SQL Databases  • Storage       │
                │  • Virtual Networks  • Key Vaults  • and more...  │
                └────────────────────────────────────────────────────┘
```

### Core Components

1. **Frontend (Next.js 14)**
   - Server-side rendering (SSR)
   - Real-time updates via SWR
   - Responsive design (Tailwind CSS)
   - Conversational interface

2. **Backend API (FastAPI)**
   - Async Python (asyncio + asyncpg)
   - Pydantic validation
   - SQLAlchemy ORM
   - JWT authentication

3. **AI Engine**
   - Azure OpenAI (GPT-4 Turbo)
   - Structured JSON output
   - Context-aware prompting
   - Multi-option generation

4. **Pricing Engine**
   - Azure Retail Prices API integration
   - Redis caching (1-hour TTL)
   - Fallback estimates
   - Regional comparison

5. **Deployment Engine**
   - Bicep template generation
   - Azure SDK integration
   - Real-time progress tracking
   - Rollback support

6. **Database (PostgreSQL)**
   - 14 tables with full schema
   - Row-level security (RLS)
   - JSONB for flexible data
   - Audit logging

For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🛠️ Tech Stack

### Backend

| Technology        | Purpose                  | Version |
|-------------------|--------------------------|---------|
| Python            | Primary language         | 3.11+   |
| FastAPI           | Web framework            | 0.109+  |
| SQLAlchemy        | ORM                      | 2.0+    |
| asyncpg           | PostgreSQL driver        | 0.29+   |
| Pydantic          | Data validation          | 2.5+    |
| Alembic           | Database migrations      | 1.13+   |
| httpx             | Async HTTP client        | 0.26+   |
| python-jose       | JWT tokens               | 3.3+    |
| passlib           | Password hashing         | 1.7+    |

### Frontend

| Technology        | Purpose                  | Version |
|-------------------|--------------------------|---------|
| TypeScript        | Type-safe JavaScript     | 5.0+    |
| Next.js           | React framework          | 14.0+   |
| React             | UI library               | 18.2+   |
| Tailwind CSS      | Styling                  | 3.4+    |
| SWR               | Data fetching            | 2.2+    |
| React Hook Form   | Form handling            | 7.49+   |
| Zod               | Schema validation        | 3.22+   |
| Recharts          | Data visualization       | 2.10+   |
| Lucide React      | Icon library             | Latest  |

### Infrastructure

| Technology              | Purpose                    |
|-------------------------|----------------------------|
| PostgreSQL 15+          | Primary database           |
| Redis                   | Session & pricing cache    |
| Azure OpenAI            | AI architecture generation |
| Azure Key Vault         | Secrets management         |
| Azure Container Apps    | Application hosting (MVP)  |
| Azure Front Door        | CDN + WAF                  |
| Docker                  | Containerization           |
| Docker Compose          | Local development          |

### DevOps

| Technology        | Purpose                  |
|-------------------|--------------------------|
| GitHub Actions    | CI/CD pipeline           |
| pytest            | Backend testing          |
| Jest              | Frontend testing         |
| Playwright        | E2E testing              |
| Black             | Python formatting        |
| ESLint            | TypeScript linting       |
| Prettier          | Code formatting          |

---

## 💻 Installation

### Local Development (Docker Compose)

**Easiest way to get started:**

```bash
# 1. Clone repo
git clone https://github.com/your-org/azure-builder.git
cd azure-builder

# 2. Copy .env template
cp .env.example .env

# 3. Edit .env
nano .env

# 4. Start all services
docker-compose up -d

# 5. Run migrations
docker-compose exec backend alembic upgrade head

# 6. Seed templates
docker-compose exec backend python scripts/seed_templates.py

# 7. Open browser
open http://localhost:3000
```

### Manual Setup (No Docker)

**Backend:**

```bash
cd backend/

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
nano .env

# Run migrations
alembic upgrade head

# Seed templates
python scripts/seed_templates.py

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend/

# Install dependencies
npm install

# Set up environment
cp .env.local.example .env.local
nano .env.local

# Start dev server
npm run dev
```

**Database:**

```bash
# PostgreSQL (recommended for production)
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=azurebuilder \
  -e POSTGRES_DB=azurebuilder \
  -p 5432:5432 \
  postgres:15

# OR SQLite (quick start)
# Just set DATABASE_URL=sqlite+aiosqlite:///./azurebuilder.db in .env
```

**Redis (optional for local dev):**

```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine
```

---

## ⚙️ Configuration

### Environment Variables

**Backend (.env):**

```bash
# Application
APP_NAME=Azure Builder API
ENVIRONMENT=development  # development | staging | production
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/azurebuilder

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-turbo
AZURE_OPENAI_API_VERSION=2024-02-01

# OR OpenAI (fallback)
OPENAI_API_KEY=sk-...

# Azure Key Vault (for production)
AZURE_KEY_VAULT_URL=https://your-vault.vault.azure.net

# Authentication
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Azure AD B2C (optional, for SSO)
AZURE_AD_B2C_TENANT=yourtenant.onmicrosoft.com
AZURE_AD_B2C_CLIENT_ID=your-client-id
AZURE_AD_B2C_POLICY_NAME=B2C_1_signupsignin

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Pricing
AZURE_PRICING_API_URL=https://prices.azure.com/api/retail/prices
PRICING_CACHE_TTL=3600

# AI Settings
AI_MAX_TOKENS=4096
AI_TEMPERATURE=0.1

# Rate Limiting
RATE_LIMIT_FREE=10
RATE_LIMIT_PRO=100
RATE_LIMIT_ENTERPRISE=1000
```

**Frontend (.env.local):**

```bash
# API
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_WS_URL=ws://localhost:8000/ws

# App
NEXT_PUBLIC_APP_NAME=Azure Builder
NEXT_PUBLIC_APP_VERSION=1.0.0

# Azure AD B2C (optional)
NEXT_PUBLIC_AZURE_AD_B2C_TENANT=yourtenant.onmicrosoft.com
NEXT_PUBLIC_AZURE_AD_B2C_CLIENT_ID=your-client-id
NEXT_PUBLIC_AZURE_AD_B2C_POLICY_NAME=B2C_1_signupsignin
```

---

## 📚 API Documentation

### Interactive Docs

Once the backend is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

### Key Endpoints

**Authentication:**
```http
POST   /api/v1/auth/login       # Login
POST   /api/v1/auth/logout      # Logout
GET    /api/v1/auth/me          # Get current user
```

**Projects:**
```http
GET    /api/v1/projects         # List projects
POST   /api/v1/projects         # Create project
GET    /api/v1/projects/{id}    # Get project
PUT    /api/v1/projects/{id}    # Update project
DELETE /api/v1/projects/{id}    # Delete project
```

**Proposals:**
```http
POST   /api/v1/projects/{id}/proposals      # Create proposal
GET    /api/v1/proposals/{id}                # Get proposal
GET    /api/v1/proposals/{id}/options        # Get options
POST   /api/v1/proposals/{id}/select         # Select option
POST   /api/v1/proposals/{id}/refine         # Refine proposal
```

**Deployments:**
```http
POST   /api/v1/proposals/{id}/deploy         # Create deployment
GET    /api/v1/deployments/{id}              # Get deployment
GET    /api/v1/deployments/{id}/review       # Review deployment
POST   /api/v1/deployments/{id}/approve      # Approve deployment
POST   /api/v1/deployments/{id}/execute      # Execute deployment
POST   /api/v1/deployments/{id}/rollback     # Rollback deployment
GET    /api/v1/deployments/{id}/logs         # Get logs
```

**Templates:**
```http
GET    /api/v1/templates                     # List templates
GET    /api/v1/templates/{id}                # Get template
GET    /api/v1/templates/categories          # List categories
```

**Pricing:**
```http
POST   /api/v1/pricing/estimate              # Estimate cost
POST   /api/v1/pricing/compare-regions       # Compare regions
POST   /api/v1/pricing/compare-skus          # Compare SKUs
```

**Azure Connections:**
```http
POST   /api/v1/azure/connect                 # Connect subscription
GET    /api/v1/azure/status                  # Get connections
GET    /api/v1/azure/{id}/quotas             # Get quotas
GET    /api/v1/azure/{id}/resources          # Get existing resources
DELETE /api/v1/azure/{id}                    # Remove connection
```

### Example: Create Proposal

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/proposals \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "I need a web API with authentication and SQL database. Budget is $200/month."
  }'
```

**Response:**
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "status": "ready",
  "options": [
    {
      "option_number": 1,
      "name": "Basic Web API",
      "monthly_cost": 55.00,
      "architecture_diagram": "...",
      "resources_json": {...},
      "pros_cons_json": {...}
    },
    {
      "option_number": 2,
      "name": "Scalable Web API",
      "monthly_cost": 245.00,
      ...
    },
    {
      "option_number": 3,
      "name": "Enterprise Web API",
      "monthly_cost": 850.00,
      ...
    }
  ]
}
```

---

## 🌐 MVP Deployment (Azure Container Apps)

Deploy the entire platform to Azure in ~10 minutes.

### Prerequisites

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login

# Set subscription
az account set --subscription <subscription-id>

# Install Bicep
az bicep install
```

### Deploy Infrastructure

```bash
cd infrastructure/

# Create resource group
az group create \
  --name rg-azurebuilder-prod \
  --location eastus

# Deploy Bicep template
az deployment group create \
  --resource-group rg-azurebuilder-prod \
  --template-file main.bicep \
  --parameters environment=production \
  --parameters adminEmail=admin@example.com
```

This creates:
- Container Apps Environment
- PostgreSQL Flexible Server
- Azure Cache for Redis
- Azure Key Vault
- Azure Front Door
- Application Insights
- Log Analytics Workspace

### Deploy Application

```bash
# Build and push backend
cd backend/
az acr login --name <acr-name>
docker build -t <acr-name>.azurecr.io/azurebuilder-api:latest .
docker push <acr-name>.azurecr.io/azurebuilder-api:latest

# Build and push frontend
cd ../frontend/
docker build -t <acr-name>.azurecr.io/azurebuilder-web:latest .
docker push <acr-name>.azurecr.io/azurebuilder-web:latest

# Deploy to Container Apps
az containerapp update \
  --name azurebuilder-api \
  --resource-group rg-azurebuilder-prod \
  --image <acr-name>.azurecr.io/azurebuilder-api:latest

az containerapp update \
  --name azurebuilder-web \
  --resource-group rg-azurebuilder-prod \
  --image <acr-name>.azurecr.io/azurebuilder-web:latest
```

### Run Migrations

```bash
az containerapp exec \
  --name azurebuilder-api \
  --resource-group rg-azurebuilder-prod \
  --command "alembic upgrade head"

az containerapp exec \
  --name azurebuilder-api \
  --resource-group rg-azurebuilder-prod \
  --command "python scripts/seed_templates.py"
```

### Access Application

```bash
# Get frontend URL
az containerapp show \
  --name azurebuilder-web \
  --resource-group rg-azurebuilder-prod \
  --query properties.configuration.ingress.fqdn \
  -o tsv

# Open browser
open https://<fqdn>
```

### Estimated Cost

**Monthly cost for MVP deployment:**
- Container Apps (Frontend + Backend): ~$30
- PostgreSQL Flexible Server (B1ms): ~$12
- Azure Cache for Redis (Basic C0): ~$16
- Azure Key Vault (Standard): ~$3
- Azure Front Door (Standard): ~$35
- Application Insights: ~$3
- **Total: ~$100/month**

---

## 🧪 Testing

### Backend Tests

```bash
cd backend/

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_ai_engine.py

# Run specific test
pytest tests/test_ai_engine.py::test_generate_proposal
```

### Frontend Tests

```bash
cd frontend/

# Install test dependencies
npm install --save-dev jest @testing-library/react

# Run unit tests
npm test

# Run E2E tests
npm run test:e2e

# Run with coverage
npm run test:coverage
```

### Integration Tests

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/

# Clean up
docker-compose -f docker-compose.test.yml down
```

---

## 🔧 Development

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Code Formatting

**Backend:**
```bash
cd backend/

# Format code
black .

# Sort imports
isort .

# Lint
flake8 .

# Type checking
mypy .
```

**Frontend:**
```bash
cd frontend/

# Format code
npm run format

# Lint
npm run lint

# Type checking
npm run type-check
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Write tests**
5. **Run tests and linting:**
   ```bash
   # Backend
   cd backend && pytest && black . && flake8 .
   
   # Frontend
   cd frontend && npm test && npm run lint
   ```
6. **Commit your changes:**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
7. **Push to your fork:**
   ```bash
   git push origin feature/amazing-feature
   ```
8. **Open a Pull Request**

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### Code Style

**Python:**
- Follow PEP 8
- Use Black for formatting
- Use type hints
- Document all public functions

**TypeScript:**
- Follow Airbnb style guide
- Use ESLint + Prettier
- Use TypeScript strict mode
- Document complex functions

### Pull Request Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted and linted
- [ ] No breaking changes (or documented)
- [ ] Commit messages follow convention
- [ ] PR description is clear

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Microsoft Azure** for the comprehensive cloud platform
- **OpenAI** for GPT models
- **FastAPI** for the amazing Python web framework
- **Next.js** for the powerful React framework
- **PostgreSQL** for the robust database
- **All contributors** who help make this project better

---

## 📞 Support

- **Documentation:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Issues:** [GitHub Issues](https://github.com/your-org/azure-builder/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/azure-builder/discussions)
- **Email:** support@azurebuilder.dev

---

## 🗺️ Roadmap

### Q1 2025
- [x] MVP backend implementation
- [x] Database schema design
- [x] AI engine with multi-option generation
- [x] Real-time pricing integration
- [ ] Complete frontend (React/Next.js)
- [ ] Azure SDK deployment integration
- [ ] Production deployment

### Q2 2025
- [ ] Azure MCP integration for infrastructure awareness
- [ ] Multi-region cost comparison
- [ ] Export to Terraform/Pulumi
- [ ] Scheduled deployments
- [ ] Drift detection

### Q3 2025
- [ ] What-if analysis
- [ ] Region recommendations
- [ ] Template marketplace
- [ ] Team collaboration features
- [ ] Advanced RBAC

### Q4 2025
- [ ] Multi-cloud support (AWS, GCP)
- [ ] Cost optimization recommendations
- [ ] Compliance scanning (HIPAA, SOC2, etc.)
- [ ] Auto-scaling policies
- [ ] Custom templates

---

## 📊 Project Status

**Current Phase:** MVP Complete (Backend)  
**Next Milestone:** Frontend Development  
**Expected Beta:** Q2 2025  
**Expected GA:** Q3 2025

---

## 🌟 Star History

If you find Azure Builder useful, please consider giving it a star ⭐ on GitHub!

---

Made with ❤️ by the Azure Builder Team

