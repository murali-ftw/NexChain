# Claude.md - NexChain Project Documentation

## Project Overview
NexChain is a Supply Chain Intelligence Co-Pilot application providing real-time visibility and decision support for supply chain operations.

## Project Structure

```
.
├── frontend/              # Angular 17+ web application
├── backend-api/          # Python FastAPI backend
├── ai_service/           # AI/ML service for supply chain intelligence
├── ai/                   # AI models and utilities
├── mcp_server/           # MCP (Model Context Protocol) server
├── mock_apis/            # Mock API services for testing
├── db/                   # Database schemas and migrations
├── infra/                # Infrastructure configuration (Docker, K8s, etc.)
├── docs/                 # Project documentation and specifications
├── PRODUCT.md            # Product requirements and vision
├── README.md             # Setup and getting started guide
└── pyproject.toml        # Python project configuration
```

## Key Technologies

**Frontend:**
- Angular 17+
- TypeScript
- Aetheria Glass design system

**Backend:**
- Python 3.10+
- FastAPI
- SQLAlchemy/PostgreSQL

**AI/ML:**
- Supply chain intelligence models
- LLM integrations

**DevOps:**
- Docker
- Kubernetes (configured in infra/)
- GitHub Actions

## Development Setup
See [README.md](./README.md) for complete setup instructions.

### Prerequisites
- Node.js 18+ (frontend)
- Python 3.10+ (backend/AI)
- Docker & Docker Compose
- PostgreSQL

### Quick Start
```bash
# Frontend
cd frontend && npm install && npm start

# Backend
cd backend-api && pip install -r requirements.txt && python -m app.main

# AI Service
cd ai_service && pip install -r requirements.txt
```

## Architecture Notes

### Frontend (Angular)
- Component-based architecture
- Design system: Aetheria Glass
- Responsive UI for supply chain dashboards

### Backend API
- FastAPI framework
- RESTful endpoints
- Authentication & authorization
- Database ORM with SQLAlchemy

### AI Service
- Separate microservice for ML models
- Supply chain analytics
- Predictive insights

## Important Files & Entry Points

- **Frontend:** `frontend/src/main.ts`
- **Backend:** `backend-api/app/main.py`
- **AI Service:** `ai_service/main.py`
- **Database:** `db/migrations/` for schema changes
- **Product Spec:** `PRODUCT.md`
- **API Contracts:** `docs/api_contracts.md`

## Testing & Quality

- **Python:** pytest, mypy type checking, ruff linting
- **Frontend:** Angular test suite
- **Pre-commit:** cspell for spell checking

## Documentation
- `docs/problem_statement.md` - Problem context
- `docs/02_technical_requirements.md` - Technical specs
- `docs/05_app_flow.md` - User flows
- `docs/api_contracts.md` - API specifications
- `docs/08_release_candidate_audit.md` - Deployment checklist

## Deployment
See `infra/` directory for deployment configurations.

## Contributing
- Use feature branches off `main`
- All tests must pass before PR merge
- Follow existing code style and conventions
