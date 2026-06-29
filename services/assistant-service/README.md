# Assistant Service

Owns assistant conversations, retrieval, document indexing, prompt
orchestration, citations, refusal behavior, and assistant evaluation workflows.

## Ownership

- Tenant-scoped assistant sessions and messages.
- Assistant document parsing, chunking, indexing, and retrieval.
- Prompt assembly and provider interaction behind injectable adapters.
- Citation, grounding, refusal, and assistant evaluation behavior.

## Key Endpoints

- `GET /health` and `GET /healthz`: scaffold health endpoints.
- Planned assistant chat and source-document routes are described in
  `docs/api/endpoints.md`.

## Tables

Migrations are deferred. Expected ownership includes assistant sessions,
messages, source documents, chunks, retrieval traces, citations, and evaluation
records.

## Workers

`gridlens_assistant_service.workers.main` exposes deterministic readiness for
future document indexing or retrieval-maintenance workers. The placeholder does
not call Bedrock, S3, SQS, or vector stores.

## Flow Diagrams

Detailed assistant, indexing, and retrieval flow diagrams are deferred until the
first RAG implementation workstream.
