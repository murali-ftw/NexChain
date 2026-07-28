# Workbench - Development Environment Standards

## IDE & Editor Setup

### Recommended Tools
- **IDE:** VS Code with Claude Code extension
- **Python:** Python extension, Pylance
- **Frontend:** Angular Language Service
- **Git:** Built-in git support

### VS Code Extensions
- `ms-python.python`
- `ms-python.vscode-pylance`
- `Angular.ng-template`
- `esbenp.prettier-vscode`
- `ms-vscode.makefile-tools`
- `codestream.codestream` (optional, for code review)

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost:5432/nexchain
OPENAI_API_KEY=your_key_here
ENVIRONMENT=development
DEBUG=true
```

### Frontend (.env)
```
API_URL=http://localhost:8000
ENVIRONMENT=development
```

## Running Services Locally

### Start All Services (Docker Compose)
```bash
docker-compose up
```

### Individual Services

**Frontend (Angular)**
```bash
cd frontend
npm install
npm start
# Access at http://localhost:4200
```

**Backend API**
```bash
cd backend-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**AI Service**
```bash
cd ai_service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Database**
```bash
# Using Docker
docker run -d \
  -e POSTGRES_USER=nexchain \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=nexchain \
  -p 5432:5432 \
  postgres:15
```

## Code Quality & Linting

### Python
```bash
# Type checking
mypy backend-api/ ai_service/

# Linting
ruff check backend-api/ ai_service/

# Format
ruff format backend-api/ ai_service/

# Tests
pytest backend-api/ -v
```

### Frontend
```bash
# Lint
ng lint

# Format
npx prettier --write .

# Tests
ng test

# Build
ng build
```

### Spell Check
```bash
cspell lint "**/*.{ts,py,md}"
```

## Git Workflow

### Branches
- `main` - Production-ready code
- `dev` - Development branch
- `feature/*` - Feature branches
- `fix/*` - Bug fix branches

### Pre-commit Checks
- Spell checking (cspell)
- Linting (ruff, eslint)
- Type checking (mypy, TypeScript)

### Commit Convention
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

## Debugging

### Python Debugging
```bash
# With VS Code debugger
# Or use pdb
python -m pdb backend-api/app/main.py
```

### Frontend Debugging
```bash
# Chrome DevTools
# Angular DevTools extension for Chrome
```

### Database Debugging
```bash
psql -U nexchain -d nexchain -h localhost
```

## Common Tasks

### Add a Python Package
```bash
pip install package_name
pip freeze > requirements.txt
```

### Add a Frontend Package
```bash
cd frontend
npm install package_name
```

### Database Migration
```bash
cd db
# Create migration
# Run: python manage.py migrate
```

### Run Tests
```bash
# Python
pytest backend-api/ -v --cov

# Frontend
ng test
```

## Performance Tips

- Use `npm ci` instead of `npm install` for faster installs
- Cache `node_modules` and virtual environments
- Use `--watch` mode during development
- Profile frontend with Angular DevTools

## Environment-Specific Notes

### Development
- Hot reload enabled for both frontend and backend
- Verbose logging
- Mock data available in `mock_apis/`

### Testing
- Use test database (separate from dev DB)
- Mock external APIs
- Fixtures in `tests/fixtures/`

### Production
- See `infra/` for production configurations
- Environment variables must be set via CI/CD

## Useful Commands

```bash
# Root level
npm install          # Install all frontend deps
make setup          # Setup dev environment (if Makefile exists)
git status          # Check git state
git log --oneline   # See recent commits

# Watch logs from all services
docker-compose logs -f

# Clean up
docker-compose down -v
rm -rf venv node_modules __pycache__
```

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process on port
lsof -i :8000  # Backend
lsof -i :4200  # Frontend
kill -9 <PID>
```

### Database Connection Issues
- Verify PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Ensure database migrations are run

### Node Modules Issues
```bash
rm -rf node_modules package-lock.json
npm install
```

### Python Venv Issues
```bash
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
