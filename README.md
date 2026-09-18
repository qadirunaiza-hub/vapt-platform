# VAPT Platform

A full-stack Vulnerability Assessment and Penetration Testing (VAPT) management platform for tracking scans, findings, remediations, and generating reports.

## Architecture

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Recharts |
| Backend | FastAPI, SQLAlchemy (async), Alembic |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 16 |
| Parsers | Nmap, OWASP ZAP, Trivy |
| Reports | WeasyPrint + Jinja2 (PDF) |
| Containers | Docker, Docker Compose |

## Project Structure

```
vapt-platform/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers (auth, scans, findings, reports, retests)
│   │   ├── core/         # Config, security (JWT)
│   │   ├── db/           # SQLAlchemy session and base
│   │   ├── models/       # ORM models
│   │   ├── parsers/      # Nmap, ZAP, Trivy result parsers
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic (report generation)
│   │   ├── templates/    # Jinja2 HTML report template
│   │   ├── utils/        # Fingerprinting, validators
│   │   └── workers/      # Celery tasks (scan execution)
│   ├── migrations/       # Alembic migrations
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/   # Reusable UI components
│       ├── pages/        # Dashboard, Scans, Findings, Reports, Targets
│       ├── services/     # Axios API client
│       └── store/        # Auth context
├── docker-compose.yml
├── .env.example
└── setup.sh
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/qadirunaiza-hub/vapt-platform.git
cd vapt-platform

# Copy and configure environment
cp .env.example .env
# Edit .env with your values (SECRET_KEY, POSTGRES_PASSWORD, etc.)

# Start all services
docker compose up -d
```

Services start on:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Running Migrations Manually

```bash
docker compose exec backend alembic upgrade head
```

### Running Tests

```bash
docker compose exec backend pytest
```

## Key Features

- **Scan Management** — trigger and track Nmap, ZAP, and Trivy scans via Docker
- **Finding Tracker** — severity classification, status workflow, retest support
- **Scan Comparison** — diff findings across scan runs
- **Report Generation** — PDF reports via WeasyPrint
- **Dashboard** — charts and KPIs across targets and findings
- **JWT Auth** — token-based authentication with configurable expiry

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing secret — generate with `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | Database password |
| `JWT_EXPIRE_MINUTES` | Token lifetime (default: 480) |
| `ALLOWED_ORIGINS` | CORS origins for the frontend |

## License

Internal use — Mu-Sigma.
