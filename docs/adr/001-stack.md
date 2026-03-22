# ADR 001: Stack Selection

## Status

Accepted

## Decision

Use:

- Django 5.2 + Django REST framework + SimpleJWT + drf-spectacular
- PostgreSQL + Redis + Channels
- Next.js 16 App Router + TypeScript + Tailwind CSS

## Why

- Django Admin reduces the cost of building the first admin and moderation workflow.
- DRF keeps API design explicit and testable.
- PostgreSQL fits relational domain data and supports full-text search.
- Redis and Channels let the project reserve a clean path for matched chat and notifications.
- Next.js fits the multi-entry web experience better than a plain SPA for home pages, forum pages, and future SEO needs.

## Consequences

- Local API development requires Python 3.12+.
- Frontend and backend remain independently deployable.
- Realtime features are scaffolded but intentionally not completed in the first milestone.
