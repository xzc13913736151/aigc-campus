# Development Guide

## Purpose

This document defines the supported local development flow for PairUp.
It is intentionally repository-specific and should stay aligned with the actual scripts, dependency constraints, and infrastructure defined in the codebase.

## Supported Toolchain

### Minimum Versions

- Node.js `>=22`
- pnpm `>=10.26.1`
- Python `>=3.12`
- Docker Engine with Docker Compose v2

### Verified Versions

The scaffold was verified on `2026-03-22` with:

- Node.js `25.2.1`
- pnpm `10.26.1`
- Docker Engine `28.5.1`
- Docker Compose `2.40.0`

If you use newer versions, keep them reasonably close to this range unless there is a clear migration decision recorded in `docs/adr/`.

## Infrastructure

The repository currently uses Docker only for infrastructure services:

- PostgreSQL `16` from `postgres:16-alpine`
- Redis `7` from `redis:7-alpine`

Start infrastructure:

```bash
docker compose up -d db redis
docker compose ps
```

Stop infrastructure:

```bash
docker compose down
```

The API is not containerized in this scaffold yet.
Run it locally, and build the mini program with the local uni-app toolchain.

## Mini Program Development

Install dependencies from the repository root:

```bash
pnpm install
```

Copy the environment template before starting the apps:

```bash
cp .env.example .env
```

The API auto-loads the repository root `.env` file during local development.

Start the WeChat Mini Program build:

```bash
pnpm --dir apps/mp dev:mp-weixin
```

Key commands:

```bash
pnpm --dir apps/mp dev:mp-weixin
pnpm --dir apps/mp build:mp-weixin
```

After the build starts, import the generated directory into WeChat Developer Tools:

- `apps/mp/dist/dev/mp-weixin`

## API Development

Before creating the virtual environment, confirm that `python3 --version` is at least `3.12`.
Do not document or rely on machine-specific interpreter paths in repository docs.

Create the local environment:

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Run the API:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Email verification codes:

- The default local mail backend is `django.core.mail.backends.console.EmailBackend`.
- When you request a verification code locally, the email content is printed in the API terminal.
- To send real emails, set `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, and `DEFAULT_FROM_EMAIL`.
- Registration now requires a verification code from `/api/v1/auth/email-code/request/`.

Key API verification commands:

```bash
python manage.py check
python manage.py migrate
pytest
```

Default API URLs:

- API root: `http://localhost:8000/api/v1/`
- Django Admin: `http://localhost:8000/admin/`
- OpenAPI schema: `http://localhost:8000/api/schema/`
- Swagger UI: `http://localhost:8000/api/docs/`

## Recommended Local Workflow

Use three terminals:

1. Infrastructure

```bash
docker compose up -d db redis
```

2. API

```bash
cd apps/api
source .venv/bin/activate
python manage.py runserver
```

3. Mini Program

```bash
pnpm --dir apps/mp dev:mp-weixin
```

## Repository Notes

- Root `pnpm` scripts now target the mini program workflow.
- API dependency management is defined in `apps/api/pyproject.toml`.
- If the repo later adds app containers, update this document instead of leaving mixed local-only and container-only instructions in `README.md`.
