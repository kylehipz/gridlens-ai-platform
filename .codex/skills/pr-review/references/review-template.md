# PR Review Handover Template

Use this structure for `.handover/pr-review-<target>-<date>.md`.

```markdown
# PR Review: <target>

## Source
- Target: <PR URL, PR number, or branch comparison>
- Base: <base branch/sha>
- Head: <head branch/sha>
- CI status: <summary>

## Findings
### Critical
- <file:line> <role>: <issue, impact, and fix>

### High
- <file:line> <role>: <issue, impact, and fix>

### Medium
- <file:line> <role>: <issue, impact, and fix>

### Low
- <file:line> <role>: <issue, impact, and fix>

## Role Notes
### Senior Backend Engineer
<Findings or "No additional issues found.">

### Security Engineer
<Findings or "No additional issues found.">

### Database Engineer
<Findings or "No additional issues found.">

### DevOps Engineer
<Findings or "No additional issues found.">

## Test and CI Review
- <tests reviewed, missing coverage, failed checks, skipped checks>

## Open Questions
- <question or none>
```
