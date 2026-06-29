---
name: pr-review
description: Review a pull request or branch through Senior Backend Engineer, Security Engineer, Database Engineer, and DevOps Engineer lenses, then write a review handover under .handover/. Use when Codex is asked for PR review, branch review, pre-merge review, or role-based engineering review with durable findings.
---

# PR Review

Use this skill to produce a durable, role-based review handover.

## Workflow

1. Determine the review target.
   - Prefer an explicit PR number or URL.
   - Otherwise infer the current branch and compare it to the base branch.
   - Fetch PR metadata, changed files, review comments, linked issues, and CI status when available.

2. Inspect the diff and relevant context.
   - Read changed code and nearby unchanged code needed to validate behavior.
   - Inspect tests, migrations, infrastructure, API contracts, and docs touched by the change.
   - Do not limit review to the diff if surrounding code affects correctness.

3. Review through four roles.
   - Senior Backend Engineer: correctness, API behavior, domain boundaries, error handling, maintainability, observability, and test coverage.
   - Security Engineer: authn/authz, tenant isolation, secrets, input validation, data exposure, dependency risk, auditability, and abuse cases.
   - Database Engineer: schema design, migrations, constraints, indexes, query plans, transactions, lock risk, rollback, and data integrity.
   - DevOps Engineer: CI/builds, deployment safety, config, environment variables, runtime dependencies, logging/metrics, rollback, and operational risk.

4. Prioritize findings.
   - Lead with bugs, regressions, security issues, data risks, and missing tests.
   - Include file and line references wherever possible.
   - For each finding, state severity, impact, evidence, and recommended fix.
   - Clearly say when no issues are found for a role.

5. Write the handover.
   - Create `.handover/` in the repository root if needed.
   - Use `.handover/pr-review-<pr-number-or-branch>-<yyyy-mm-dd>.md`.
   - Follow `references/review-template.md`.

## Final Response

Keep the chat response short. Include the handover path and the count of findings by severity.
