# Program Evaluation Service

Owns program configuration, participation tracking, evaluation runs, baseline
modeling, savings estimation, evaluation-linked anomalies, and run metadata.

## Ownership

- Program and participant lifecycle.
- Evaluation run creation, status, approval, cancellation, and comparison.
- Evaluation inputs, period results, participant results, and evidence links.
- Modeling boundaries for baseline and savings calculations.

## Key Endpoints

- `GET /health` and `GET /healthz`: scaffold health endpoints.
- Planned program, participant, and evaluation routes are described in
  `docs/api/endpoints.md`.

## Tables

Migrations are deferred. Expected ownership includes programs, participants,
evaluation runs, evaluation inputs, period results, participant results,
approval records, and model-run metadata.

## Workers

`gridlens_program_evaluation_service.workers.main` exposes deterministic
readiness for future evaluation execution workers. The placeholder does not poll
queues, query databases, or call AI providers.

## Flow Diagrams

Detailed evaluation execution and approval flow diagrams are deferred until
calculation jobs and persistence are implemented.
