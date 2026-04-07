# Contributing Guide

## Scope

This guide defines the repository workflow and documentation rules for PairUp contributors.

## Branching

- Create feature or chore branches from `main`.
- Keep branch names descriptive, for example `feat/profile-editing` or `chore/project-setup`.
- Prefer Pull Requests for review and merge.

## Commit Conventions

Use Conventional Commits.

Recommended prefixes:

- `feat:` for new functionality
- `fix:` for bug fixes
- `docs:` for documentation-only changes
- `test:` for tests and verification coverage
- `chore:` for maintenance and tooling work
- `refactor:` for non-behavioral structural changes

Examples:

- `feat(api): add teammate application review endpoint`
- `fix(web): handle missing auth token in profile page`
- `docs(readme): clarify Python and Docker requirements`

## Commit Hygiene

- Keep commits small and reviewable.
- Commit related code, tests, and documentation together.
- Do not commit unrelated files.
- Do not rewrite shared history with `git push --force` or `git push --force-with-lease`.
- Update `.gitignore` when new generated files appear.

## Documentation Policy

- All repository documentation must be written in English.
- This applies to `README.md`, all files under `docs/`, ADRs, and developer-facing Markdown documents.
- Keep documentation operationally accurate.
- If a code change affects commands, versions, routes, architecture, or workflow, update documentation in the same change.
- Avoid machine-specific commands in repository docs unless the repository explicitly requires them.

## Review Expectations

Before opening a PR, run the checks relevant to your change.

Typical checks:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
```

For API changes:

```bash
cd apps/api
source .venv/bin/activate
python manage.py check
python manage.py migrate
pytest
```

## Source of Truth Reminder

If repository docs and the latest internal product document diverge, the internal product document is the higher-priority product source.
When that happens, update repository docs promptly so the gap does not persist.
