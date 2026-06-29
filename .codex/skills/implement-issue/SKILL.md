---
name: implement-issue
description: Implement a GitHub issue from an existing .handover/ issue plan checkpoint by checkpoint, committing each checkpoint separately. Use when Codex is asked to implement planned issue work, continue issue execution, or work from a .handover/ issue plan with tests/builds and focused commits.
---

# Implement Issue

Use this skill to execute an existing `.handover/` issue plan. The handover file is the source of truth.

## Required Starting Point

1. Locate the relevant `.handover/issue-*.md` file.
   - Prefer a file explicitly named by the user.
   - Otherwise match by current branch, issue number in branch name, or issue title.
   - If no matching handover exists, stop and ask for one or use `$plan-issue` first.

2. Read the complete handover before editing.
   - Identify checkpoints, acceptance criteria, test plan, assumptions, and open questions.
   - If the handover has unresolved questions that block implementation, ask before editing.

3. Inspect the worktree.
   - Run `git status --short --branch`.
   - Preserve unrelated user changes.
   - Do not reset, revert, or overwrite changes you did not make without explicit approval.

## Checkpoint Loop

For each checkpoint:

1. Re-read the checkpoint and relevant source files.
2. Implement only that checkpoint's behavior.
3. Add or update tests needed for that checkpoint.
4. Run targeted tests first.
5. Run broader tests or builds when the checkpoint affects shared behavior, public APIs, migrations, or frontend bundles.
6. Pipe noisy command output to a log file under `/tmp` and summarize only the result in chat.
7. Update `.handover/` progress notes only when useful for durable handoff.
8. Commit the checkpoint before moving to the next one.

## Commit Rules

- Use one focused commit per completed checkpoint.
- Use concise imperative commit subjects, with a type prefix when useful.
- Do not include unrelated formatting or cleanup.
- Before committing, review `git diff` and ensure only intended files are staged.

## Verification Rules

- Prefer stable Makefile commands when available.
- If no canonical commands exist, infer the narrowest appropriate command from project tooling.
- For build/test commands with large output, use a log file such as `/tmp/<repo>-checkpoint-<n>-test.log`.
- If a command fails, inspect the relevant log, fix if in scope, and rerun.
- Record any skipped tests with the concrete reason.

## Final Response

Summarize completed checkpoints, commits created, tests/builds run, and any remaining risks or skipped validation.
