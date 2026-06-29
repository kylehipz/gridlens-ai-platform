---
name: fix-pr-findings
description: Fix actionable findings from an existing PR review handover, usually under .handover/, by treating each finding as an implementation checkpoint and creating one focused commit per finding. Use when Codex is asked to address PR review findings, fix a pr-review handoff, resolve handover findings, or continue PR review remediation with checkpoint commits.
---

# Fix PR Findings

Use this skill to execute a PR review handover. The handover file is the source of truth for what must be fixed.

## Required Starting Point

1. Locate the relevant PR review handover.
   - Prefer a file explicitly named by the user.
   - Otherwise inspect `.handover/` for `pr-review-*.md` files and choose the one matching the current PR, branch, or user request.
   - If multiple files plausibly match, read their titles and dates, then choose the newest relevant handover.
   - If no PR review handover exists, stop and ask for the handover or use `$pr-review` first.

2. Read the complete handover before editing.
   - Identify all actionable findings, severities, file references, recommended fixes, open questions, and validation notes.
   - Treat each actionable finding as one checkpoint.
   - Do not create checkpoints for informational notes, already-fixed items, or "no issue found" role summaries.

3. Inspect the worktree.
   - Run `git status --short --branch`.
   - Preserve unrelated user changes.
   - Do not reset, revert, overwrite, or stage changes you did not make without explicit approval.

## Checkpoint Loop

For each finding, in priority order:

1. Re-read the finding and inspect the referenced files plus nearby code needed to understand the behavior.
2. Determine the smallest correct fix for that finding.
3. Implement only that finding's fix.
4. Add or update tests that prove the finding is fixed when the codebase has a relevant test surface.
5. Run targeted tests first.
6. Run broader tests or builds when the fix touches shared behavior, public APIs, migrations, deployment config, security controls, or tenant isolation.
7. Pipe noisy command output to a log file under `/tmp` and summarize only the result in chat.
8. Update the `.handover/` file only when useful for durable handoff, such as marking a finding fixed with commit hash, test command, or remaining caveat.
9. Review the diff for that checkpoint.
10. Commit the checkpoint before starting the next finding.

If one finding reveals a second independent issue, finish the current finding first, then decide whether the new issue belongs in the same checkpoint only if it is required to fix the finding. Otherwise note it separately and continue with the handover findings.

## Commit Rules

- Use one focused commit per completed finding.
- Use concise imperative commit subjects, with a type prefix when useful.
- Mention the finding identifier or severity in the commit body when the handover provides one.
- Stage only files changed for the current finding.
- Do not include unrelated formatting, cleanup, generated churn, or user changes.
- Before committing, review `git diff --staged` and ensure the staged diff matches the finding.

## Verification Rules

- Prefer stable Makefile commands when available.
- If no canonical command exists, infer the narrowest appropriate command from project tooling.
- For build/test commands with large output, use a log file such as `/tmp/<repo>-pr-finding-<n>-test.log`.
- If a command fails because of the current fix, inspect the log, fix the problem, and rerun.
- If a command fails for an unrelated pre-existing reason, document the failure with the concrete command and key error.
- Record any skipped tests with the concrete reason.

## Final Response

Summarize the findings fixed, commits created, tests/builds run, and any findings not completed. Include the handover path when one was used.
