# ADR 001: Stack Selection

## Status

Accepted

## Decision

Use:

- Django 5.2 + Django REST framework + SimpleJWT + drf-spectacular
- PostgreSQL + Redis + Channels
- uni-app + Vue 3 + TypeScript for the WeChat Mini Program

## Why

- Django Admin reduces the cost of building the first admin and moderation workflow.
- DRF keeps API design explicit and testable.
- PostgreSQL fits relational domain data and supports full-text search.
- Redis and Channels let the project reserve a clean path for matched chat and notifications.
- uni-app fits the current goal of shipping only a WeChat Mini Program client.

## Consequences

- Local API development requires Python 3.12+.
- The frontend is now centered on the mini program client instead of a separate web app.
- Realtime features are scaffolded but intentionally not completed in the first milestone.
