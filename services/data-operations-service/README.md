# Data Operations Service

Owns dataset catalog, file registration, ingestion coordination, data quality,
and normalized operational-data workflows.

## Ownership

- Dataset metadata and readiness state.
- File object registration and source lineage.
- Ingestion source and ingestion job coordination.
- Data-quality report surfaces and normalized utility/property read models.

## Key Endpoints

- `GET /health` and `GET /healthz`: scaffold health endpoints.
- Planned dataset, file, ingestion, data-quality, property, utility account,
  meter, billing, and rate-plan routes are described in `docs/api/endpoints.md`.

## Tables

Migrations are deferred. Expected ownership includes datasets, files, ingestion
sources, ingestion jobs, quality reports, properties, meters, utility accounts,
billing statements, and rate plans.

## Workers

`gridlens_data_operations_service.workers.main` exposes deterministic readiness
for the future data operations worker. The placeholder does not poll SQS, read
AWS credentials, or call external systems.

## Flow Diagrams

Detailed ingestion and quality flow diagrams are deferred until real job
orchestration is implemented.
