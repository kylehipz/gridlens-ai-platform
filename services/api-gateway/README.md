# API Gateway Support Service

Kong is the browser-facing gateway for `/api/v1` traffic in local development.
This FastAPI service is only a small upstream support service for gateway health
and future gateway-adjacent backend behavior. It must not duplicate Kong routing
or policy ownership.

## Ownership

- Local upstream health checks used by Kong and Docker Compose.
- Future backend-for-frontend support that cannot live in Kong declarative
  configuration.
- No tenant authorization, rate limiting, or request transformation policy is
  implemented here in this scaffold.

## Key Endpoints

- `GET /health`: internal upstream health response.
- `GET /healthz`: Docker-compatible internal health response.
- Browser-facing `GET /api/v1/health` is owned by Kong and routed to
  `GET /health` on this service.

## Tables

No database tables or migrations are owned by this scaffold.

## Workers

No async worker is active for this service. The `workers/` package is present so
future gateway-support jobs have an owned location.

## Flow Diagrams

Detailed flow diagrams are deferred. The active local flow is documented in
`docs/local-development.md`: browser or curl request to Kong, Kong route to this
upstream service, upstream FastAPI health response.
