# Repository Guidelines

## Purpose

This file is a minimal contributor entry point for agents and humans working in
this repository. Keep detailed guidance in `docs/` so it can evolve by topic.

## Key References

- `docs/requirements.md`: product scope, personas, and target capabilities.
- `docs/folder-structure.md`: intended repository layout and ownership rules.
- `docs/testing-guideline.md`: testing strategy and naming conventions.
- `docs/pr-guideline.md`: commit and pull request expectations.

## Repository Status

The repository currently contains documentation and project metadata. Source
directories such as `services/`, `libs/`, `frontend/`, `infra/`, `scripts/`, and
`tests/` should be added as implementation work begins.

## Working Rules

- Do not commit secrets, credentials, real customer data, or regulated data.
- Keep tenant isolation enforced server-side, not through frontend filtering.
- Update documentation when behavior, architecture, commands, or conventions
  change.
- Prefer stable commands in `Makefile` once build tooling is introduced.
