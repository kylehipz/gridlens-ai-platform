# Local Postman Collection Guidelines

Use Postman Collection v2.1:

```json
{
  "info": {
    "name": "Service API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [],
  "variable": [
    { "key": "base_url", "value": "http://localhost:8000" }
  ]
}
```

Use this request shape:

```json
{
  "name": "Create Resource",
  "event": [
    {
      "listen": "test",
      "script": {
        "type": "text/javascript",
        "exec": [
          "pm.test('returns 201', function () {",
          "  pm.response.to.have.status(201);",
          "});",
          "const json = pm.response.json();",
          "pm.collectionVariables.set('resource_id', json.id);"
        ]
      }
    }
  ],
  "request": {
    "method": "POST",
    "header": [
      { "key": "Content-Type", "value": "application/json" },
      { "key": "Authorization", "value": "Bearer {{access_token}}" },
      { "key": "X-Tenant-Id", "value": "{{tenant_id}}" }
    ],
    "body": {
      "mode": "raw",
      "raw": "{\n  \"name\": \"Example\"\n}",
      "options": { "raw": { "language": "json" } }
    },
    "url": {
      "raw": "{{base_url}}/resources",
      "host": ["{{base_url}}"],
      "path": ["resources"]
    }
  }
}
```

Prefer collection variables for values shared across workflows. Prefer environment variables for deployment-specific values and secrets. Never commit real secrets.

Use this local environment shape:

```json
{
  "name": "Service Local",
  "values": [
    {
      "key": "base_url",
      "value": "http://127.0.0.1:8000",
      "type": "default",
      "enabled": true
    },
    {
      "key": "access_token",
      "value": "",
      "type": "secret",
      "enabled": true,
      "description": "Bearer JWT access token for authenticated API requests."
    }
  ]
}
```

For every variable used by changed requests, add a matching environment value when the repository maintains Postman environments. Use documented local defaults from `.env.example`, Compose files, Makefile targets, or local development docs. If no safe default exists, leave `value` empty and add a concise `description` explaining what belongs there. Use `type: "secret"` for credentials, tokens, API keys, passwords, or other sensitive values.
