# Azure Builder

AI-powered Azure infrastructure provisioning platform. Describe what you want in natural language, review the generated Azure CLI commands, and deploy to your Azure subscription.

## Features

- 🤖 **AI-Powered Translation**: Natural language → Azure CLI commands using GPT-4
- 🔒 **Secure Execution**: Sandboxed Docker containers with your Azure credentials
- 👥 **Multi-Tenant SaaS**: Row-level security, per-tenant isolation
- 💰 **Cost Estimation**: Know what you'll spend before you deploy
- 📝 **Full Audit Trail**: Complete history of all commands and executions
- 📚 **Template Library**: Pre-built patterns for common infrastructure
- ✅ **Approval Workflows**: Review and approve before execution
- 🔄 **Rollback Support**: Undo deployments when needed

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for comprehensive technical details.

**Tech Stack:**
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python), PostgreSQL, Redis
- **AI**: Azure OpenAI (GPT-4)
- **Execution**: Docker containers with Azure CLI
- **Infrastructure**: Azure Container Apps, Azure Key Vault, Azure Service Bus

## Quick Start (Local Development)

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Azure subscription (for testing deployments)

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd azure-builder
cp .env.example .env
# Edit .env with your Azure credentials
```

### 2. Start Services

```bash
# Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create test tenant and user (optional)
docker-compose exec backend python -c "
from app.database import AsyncSessionLocal
from app.models import Tenant, User
import asyncio

async def setup():
    async with AsyncSessionLocal() as db:
        tenant = Tenant(name='Test Tenant', slug='test')
        db.add(tenant)
        await db.flush()
        
        user = User(
            tenant_id=tenant.id,
            email='admin@test.com',
            name='Admin User',
            role='owner'
        )
        db.add(user)
        await db.commit()
        print('Created test tenant and admin user')

asyncio.run(setup())
"
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run backend (with auto-reload)
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Deployment

### Azure Container Apps (Recommended)

```bash
# Deploy infrastructure
cd infra
az deployment group create \
  --resource-group rg-azurebuilder-prod \
  --template-file main.bicep \
  --parameters @parameters.prod.json
```

### Manual Deployment

1. **Database**: Azure Database for PostgreSQL Flexible Server
2. **Cache**: Azure Cache for Redis
3. **Backend**: Azure Container Apps (FastAPI)
4. **Frontend**: Azure Static Web Apps or Container Apps
5. **Secrets**: Azure Key Vault
6. **Queue**: Azure Service Bus

See `infra/` directory for Bicep templates.

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

**Required:**
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `JWT_SECRET_KEY`: Secret for JWT signing

### Azure Setup

1. **Create Service Principal** (for platform authentication):
   ```bash
   az ad sp create-for-rbac --name azure-builder --role Contributor
   ```

2. **Create Key Vault**:
   ```bash
   az keyvault create --name kv-azurebuilder --resource-group rg-azurebuilder
   ```

3. **Configure Azure OpenAI**:
   - Deploy GPT-4 model in Azure OpenAI
   - Copy endpoint and API key to `.env`

## Security

- ✅ Row-Level Security (RLS) for multi-tenant data isolation
- ✅ Azure credentials stored in Key Vault, never in database
- ✅ Sandboxed execution in ephemeral Docker containers
- ✅ Input sanitization to prevent prompt injection
- ✅ Command validation and risk assessment
- ✅ Full audit logging
- ✅ HTTPS/TLS for all communication

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## Project Structure

```
azure-builder/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── api/      # API routes
│   │   ├── services/ # Business logic
│   │   └── core/     # Security, RBAC, tenant context
│   ├── alembic/      # Database migrations
│   └── tests/
├── frontend/         # Next.js frontend
│   └── src/
│       ├── app/      # Next.js 14 App Router
│       ├── components/
│       ├── lib/      # API client, utilities
│       └── hooks/
├── infra/            # Infrastructure as Code (Bicep)
├── docs/             # Documentation
└── docker-compose.yml
```

## Roadmap

- [x] Phase 1: Core platform (AI translation, execution, templates)
- [ ] Phase 2: Terraform support, GitHub Actions integration
- [ ] Phase 3: Multi-cloud (AWS, GCP)
- [ ] Phase 4: Marketplace, advanced RBAC, compliance automation

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## License

Copyright © 2024 Azure Builder. All rights reserved.

## Support

- Documentation: https://docs.azurebuilder.com
- Issues: GitHub Issues
- Email: support@azurebuilder.com
