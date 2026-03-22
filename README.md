# PairUp

PairUp is a campus relationship and collaboration platform for university students.

The current scaffold focuses on three product areas:

- dating and social matching
- teammate matching
- discussion forum for graduate school, civil service exams, and related topics

## Repository Layout

- `apps/api`: Django 5.2 + Django REST framework + PostgreSQL + Redis + Channels
- `apps/web`: Next.js 16 App Router + TypeScript + Tailwind CSS
- `docs/`: developer-facing documentation, architecture notes, ADRs, and contribution rules

## Source of Truth

If `README.md`, `docs/`, and the latest internal product document differ, the internal product document wins.

The repository-level baseline currently follows [docs/product-baseline.md](docs/product-baseline.md).

## Toolchain Requirements

### Minimum Required Versions

- Node.js `>=22`
- pnpm `>=10.26.1`
- Python `>=3.12`
- Docker Engine with Docker Compose v2

### Verified Local Versions

The scaffold was last verified in this repository on `2026-03-22` with:

- Node.js `25.2.1`
- pnpm `10.26.1`
- Docker Engine `28.5.1`
- Docker Compose `2.40.0`

### Infrastructure Versions from This Repository

- PostgreSQL `16` via `postgres:16-alpine`
- Redis `7` via `redis:7-alpine`

## Development Setup

### 1. Install Workspace Dependencies

```bash
pnpm install
```

### 2. Start Infrastructure with Docker

The current `docker-compose.yml` only manages infrastructure services.
The API and web applications still run as local processes.

```bash
docker compose up -d db redis
docker compose ps
```

### 3. Run the Web App

```bash
pnpm --filter web dev
```

The web app will be available at `http://localhost:3000`.

### 4. Run the API Locally

Before creating the virtual environment, make sure `python3 --version` reports `3.12` or newer.

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The API and admin endpoints will be available at:

- API root: `http://localhost:8000/api/v1/`
- Django Admin: `http://localhost:8000/admin/`
- OpenAPI schema: `http://localhost:8000/api/schema/`
- Swagger UI: `http://localhost:8000/api/docs/`

## Verification Commands

### Web

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm --filter web build
```

### API

```bash
cd apps/api
source .venv/bin/activate
python manage.py check
python manage.py migrate
pytest
```

## Current MVP Flow Covered by the Scaffold

1. Register and log in with email and password.
2. Edit the personal profile.
3. Enter one of the three main modules.
4. Create a teammate post as the first real end-to-end action.
5. Review data in Django Admin.

## Commit and Documentation Conventions

### Commit Rules

- Use Conventional Commits such as `feat:`, `fix:`, `docs:`, `test:`, and `chore:`.
- Keep commits small and reviewable.
- Do not use `git push --force` or `git push --force-with-lease` on shared branches.
- Do not commit unrelated files.

### Documentation Language Policy

- Keep all repository documentation in English.
- This rule applies to `README.md`, files under `docs/`, ADRs, and developer-facing Markdown files.
- If code changes affect setup, scripts, architecture, or workflow, update the relevant documentation in the same change.

## Documentation Index

- [Architecture](docs/architecture.md)
- [Product Baseline](docs/product-baseline.md)
- [Development Guide](docs/development.md)
- [Contributing Guide](docs/contributing.md)
- [ADR 001: Stack Selection](docs/adr/001-stack.md)
