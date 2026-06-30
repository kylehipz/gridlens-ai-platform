# GridLens Auth

Local development identity parsing, permission helpers, and a Cognito/JWKS-ready
validator boundary. Default tests do not fetch keys or call identity providers.

Use `AUTH_MODE=cognito` for local development and deployed service paths.
Deterministic `dev:<subject>:<tenant_id>:<roles>` tokens are accepted only when
tests explicitly construct `AuthSettings.test()`.

JWT validation identifies the external subject only. Product authorization is
resolved from GridLens database rows: `app_users.external_auth_provider =
"cognito"` plus `app_users.external_subject = <cognito sub>`, followed by the
path tenant's `tenant_memberships` row.

For local Cognito testing, manually create the seeded development users in the
development user pool and set seed override variables before running
`make seed` if Cognito generated different `sub` values:

- `SEED_JORDAN_COGNITO_SUB`
- `SEED_PRIYA_COGNITO_SUB`
- `SEED_MARCUS_COGNITO_SUB`

Do not commit real Cognito identifiers, secrets, or credentials.
