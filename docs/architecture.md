# PairUp Architecture

## Overview

PairUp uses a split architecture:

- `apps/api`: Django for admin, domain logic, moderation, and APIs
- `apps/mp`: uni-app for the WeChat Mini Program user interface
- PostgreSQL for relational data and full-text search
- Redis for channels and background coordination

## Repository Structure

- `apps/api`: Django project, domain models, admin, REST APIs, and websocket scaffolding
- `apps/mp`: WeChat Mini Program client built with uni-app and Vue 3
- `docs/`: repository documentation, development workflow, and ADRs
- `docker-compose.yml`: infrastructure services for PostgreSQL and Redis

## Domain Modules

- `accounts`: authentication, roles, user lifecycle
- `profiles`: public profile and personal details
- `teammates`: team posts, applications, matching inputs
- `dating`: dating profile, preferences, signals, matches
- `forum`: posts, comments, likes, search
- `moderation`: reports, blocks, admin handling
- `chat`: reserved for future matched-chat functionality
- `notifications`: reserved for future realtime notifications

## Runtime Boundaries

- Django Admin is the first admin console.
- Public and user-facing UI is provided by the WeChat Mini Program.
- JWT protects API access for the mini program.
- Session auth remains available for Django Admin.
- Channels and Redis are configured now so realtime features can be added without a project rewrite later.
- Docker currently provisions infrastructure only; the API runs locally and the mini program is built with the local uni-app toolchain.

## MVP Data Flow

1. A user opens the WeChat Mini Program home page.
2. The user signs in through the API.
3. The user edits a profile.
4. The user enters a module page.
5. The user creates a first action such as a teammate post.
6. Admin can inspect the data in Django Admin.
