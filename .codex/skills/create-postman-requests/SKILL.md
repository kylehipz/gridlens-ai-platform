---
name: create-postman-requests
description: Create or update Postman Collection v2.1 requests and matching local environments relevant to the current code changes, with local collection/environment JSON as the durable source and optional Postman MCP sync. Use when Codex needs to keep Postman assets aligned with changed API routes, contracts, auth flows, examples, or variables in the current work.
---

# Create Postman Requests

Use this skill to keep Postman collections and local environments aligned with the API surface changed by the current work.

## Source of Truth

- Prefer local Postman Collection v2.1 JSON files and Postman environment JSON files in the repository.
- Use an existing collection if one can be found.
- Create a new collection only when no suitable collection exists.
- Use an existing matching environment if one can be found.
- Create a new local environment when variables are introduced and no suitable environment exists.
- Scope changes to requests that are relevant to the current diff, branch, issue, PR, or explicitly requested work.
- Use Postman MCP tools only when the user explicitly asks to sync to Postman cloud or provides workspace/collection IDs.
- Before any Postman MCP call, read the `postman://instructions` MCP resource and follow it.

## Local Collection and Environment Workflow

1. Identify the current change scope.
   - Inspect the working tree, branch diff, issue/PR handoff, changed API docs, route files, OpenAPI specs, tests, and existing Postman collections/environments.
   - Determine which API requests are added, removed, or contractually changed by this work.
   - Determine which variables are added, removed, renamed, or have changed defaults.
   - Do not inventory or rebuild unrelated API areas.
   - Ask only for base URL, auth, or environment details that cannot be inferred and are needed for the changed requests.

2. Create or update the collection.
   - Use Postman Collection v2.1 schema.
   - Organize folders by resource or workflow.
   - Avoid duplicate requests; update matching method/path requests in place.
   - Add new requests only for changed or newly introduced API behavior.
   - Update existing requests when the current changes alter methods, paths, headers, auth, query parameters, payloads, or response contracts.
   - Remove or mark obsolete requests only when the current changes remove or replace that API behavior.
   - Use variables such as `{{base_url}}`, `{{access_token}}`, `{{tenant_id}}`, and resource IDs instead of hardcoded local values.

3. Create or update the matching local environment.
   - Use a Postman environment JSON file next to the collection when the repository already uses local Postman assets.
   - Include every collection variable needed to run the changed requests.
   - Use documented local defaults when available, such as host ports from `.env.example`, Compose files, Makefile targets, or local development docs.
   - When no safe default exists, leave the value blank and add a concise `description` explaining the expected value, for example "Bearer JWT access token for authenticated API requests."
   - Mark credentials, tokens, API keys, passwords, and other sensitive values as `type: "secret"` when supported by the environment format.
   - Do not commit real secrets, real customer data, regulated data, or personal account identifiers.
   - Preserve existing environment values, variable names, descriptions, and enabled flags unless the current changes supersede them.

4. Preserve and adjust supporting behavior.
   - Preserve existing scripts, variables, folders, and examples unless the current changes supersede them.
   - Add or update post-response tests only when needed to reflect the changed request contract.
   - Save response values with `pm.collectionVariables.set` or `pm.environment.set` only when later changed requests need them.
   - Add negative-case requests only when they are directly relevant to the changed validation, auth, or tenant-isolation behavior.

5. Keep example data minimal and relevant.
   - Include representative success and failure payloads for changed requests when useful.
   - Do not include secrets, real customer data, or regulated data.

## Cloud Sync Workflow

Use this only when explicitly requested:

1. Confirm target workspace and collection ID, or create a collection if the user requests it and provides a workspace.
2. Confirm the target environment ID when syncing environment variables, or create an environment if the user requests it and provides the required workspace context.
3. Fetch the existing cloud collection and environment before updating.
4. Create or update only the requests and variables relevant to the current changes through Postman MCP tools.
5. Preserve scripts, variables, folders, examples, environment values, and descriptions unless the requested change supersedes them.

## Script Patterns

Read `references/local-collection-guidelines.md` when writing scripts, collection JSON, or environment JSON.

## Final Response

Report the local collection path, local environment path when present, requests added, changed, or removed, variables introduced or updated, placeholder descriptions added for missing defaults, and whether any cloud sync was performed.
