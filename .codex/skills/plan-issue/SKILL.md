---
name: plan-issue
description: Plan a GitHub issue into implementation checkpoints and a QA-grade test suite, then write a handover file under .handover/. Use when Codex needs to fetch an issue from the current branch, an explicit issue number or URL, or GitHub context; break the issue down; clarify missing acceptance criteria; and produce an implementation/test handoff before coding.
---

# Plan Issue

Use this skill to convert a GitHub issue into a durable `.handover/` plan that another agent can implement without reinterpreting the issue.

## Workflow

1. Resolve the issue source.
   - Prefer an explicit issue number or URL from the user.
   - Otherwise infer from the current branch name, linked PR metadata, or local GitHub context.
   - If multiple issues are plausible, ask the user to choose.

2. Fetch and inspect the issue.
   - Read the issue title, body, labels, comments, linked PRs, and any referenced docs or designs.
   - Use GitHub tools or `gh issue view` when available.
   - Do not rely only on a branch name when issue content can be fetched.

3. Extract acceptance criteria.
   - Treat explicit acceptance criteria, checklist items, reproduction steps, expected behavior, and linked spec requirements as acceptance criteria.
   - If acceptance criteria are absent or materially ambiguous, ask the user before producing the final handover.
   - If the user declines to add criteria, record the inferred criteria as assumptions.

4. Break the issue into checkpoints.
   - Make each checkpoint independently understandable and small enough to implement and commit.
   - Include intent, touched subsystem, expected behavior, dependencies, risks, and completion criteria.
   - Sequence checkpoints so tests or scaffolding come before behavior where practical.

5. Build a QA-grade test suite plan.
   - Include automated test cases and manual validation steps.
   - For API work, include endpoint, method, auth context, payload, expected response, expected database state, emitted events or logs, and negative cases.
   - For database work, include migration checks, constraints, indexes, rollback concerns, and tenant isolation.
   - For frontend work, include user path, state setup, accessibility checks, responsive checks, and screenshots or recordings when appropriate.
   - Cover happy paths, validation failures, authorization failures, cross-tenant denial, idempotency, retry behavior, and regression scenarios when relevant.

6. Write the handover file.
   - Create `.handover/` in the repository root if needed.
   - Use `.handover/issue-<number>-plan.md` when an issue number exists.
   - Use `.handover/issue-plan-<short-slug>.md` when no issue number exists.
   - Follow `references/handover-template.md`.

## Output Rules

- Produce the file as the primary artifact, not only a chat summary.
- Keep the final user response brief and include the handover path.
- Do not implement code while using this skill unless the user separately asks for implementation after the plan is written.
