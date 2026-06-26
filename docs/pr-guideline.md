# Pull Request Guideline

## Commit Messages

This repository has no established commit history yet. Use concise, imperative
commit subjects with an optional type prefix.

Examples:

- `docs: expand folder structure guide`
- `feat: add ingestion service shell`
- `test: add tenant isolation regression cases`
- `fix: enforce tenant filter in dataset lookup`

Keep commits focused. Avoid mixing unrelated documentation, infrastructure,
frontend, and backend changes in one commit.

## Pull Request Requirements

Each pull request should include:

- A short summary of what changed.
- The reason for the change or linked issue when available.
- Test results, or a clear note when tests are not applicable.
- Screenshots or short recordings for frontend-visible changes.
- Migration notes for database, infrastructure, or configuration changes.
- Documentation updates for behavior, architecture, commands, or conventions.

## Review Expectations

Reviewers should prioritize correctness, tenant isolation, security, auditability,
and maintainability. For AI/RAG features, reviewers should also check grounding,
citations, refusal behavior, and tenant-scoped retrieval.

## Documentation Checklist

Update relevant docs when a change affects:

- Product scope or user workflows.
- Service boundaries or data ownership.
- Data models, migrations, or lineage.
- Local development commands.
- Deployment, secrets, or infrastructure.
- Testing strategy or fixtures.
