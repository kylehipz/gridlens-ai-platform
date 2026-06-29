# Issue Handover Template

Use this structure for `.handover/issue-<number>-plan.md`.

```markdown
# Issue <number>: <title>

## Source
- GitHub issue: <url>
- Branch: <branch>
- Related docs/specs: <links or paths>

## Summary
<One concise paragraph describing the intended outcome and why it matters.>

## Acceptance Criteria
- [ ] <criterion>
- [ ] <criterion>

## Checkpoints
1. <Checkpoint name>
   - Intent: <behavior or foundation to add>
   - Scope: <subsystems/files/classes at behavior level>
   - Completion criteria: <observable done state>
   - Risks/notes: <tenant, auth, data, migration, rollout, or compatibility concerns>

## Test Plan
### Automated
- <test name/scenario>: setup, action, expected result, and layer.

### Manual / QA
- <step-by-step validation with payloads, auth context, expected response, DB/log/event checks, and cleanup.>

## Assumptions and Open Questions
- <assumption or question>

## Implementation Notes
- <constraints, sequencing notes, migration notes, or commands likely needed>
```
