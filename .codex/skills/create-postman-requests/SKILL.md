---
name: create-postman-requests
description: Create or update Postman Collection v2.1 requests and matching environments directly in Postman cloud through MCP, defaulting to the Postman workspace named "My Workspace". Use when Codex needs to keep Postman assets aligned with changed API routes, contracts, auth flows, examples, or variables in the current work; update local collection/environment JSON only when explicitly requested.
---

# Create Postman Requests

Use this skill to keep Postman cloud collections and environments aligned with the API surface changed by the current work.

## Default Target

- Treat Postman cloud as the primary target, not repository JSON files.
- Default to the Postman workspace named `My Workspace`.
- Resolve `My Workspace` by exact workspace name before making changes; a known candidate is workspace ID `6f6fe0f2-a2f8-4733-890d-13b68bb223af`.
- Verify the resolved workspace with `getWorkspace` before writes.
- Ask for a workspace ID only when the workspace cannot be resolved, is inaccessible, or multiple exact matches remain ambiguous.
- Use an existing cloud collection if one can be found in the target workspace.
- Create a new cloud collection only when no suitable collection exists.
- Use an existing matching cloud environment if one can be found in the target workspace.
- Create a new cloud environment only when variables are introduced and no suitable environment exists.
- Scope changes to requests that are relevant to the current diff, branch, issue, PR, or explicitly requested work.
- Before any Postman MCP call, read the `postman://instructions` MCP resource and follow it.

## Cloud Sync Workflow

1. Identify the current change scope.
   - Inspect the working tree, branch diff, issue/PR handoff, changed API docs, route files, OpenAPI specs, tests, and existing Postman collections/environments.
   - Determine which API requests are added, removed, or contractually changed by this work.
   - Determine which variables are added, removed, renamed, or have changed defaults.
   - Do not inventory or rebuild unrelated API areas.
   - Ask only for base URL, auth, or environment details that cannot be inferred and are needed for the changed requests.

2. Resolve the Postman targets.
   - Search for the `My Workspace` workspace first with organization ownership, then broaden only if needed.
   - Confirm the exact workspace by name and `getWorkspace`.
   - Search the resolved workspace for existing matching collections and environments.
   - Fetch the selected cloud collection and environment before updating them.
   - Preserve collection IDs, request IDs, folder IDs, environment IDs, scripts, variables, examples, environment values, descriptions, and enabled flags unless the current changes supersede them.

3. Create or update the cloud collection.
   - Use Postman Collection v2.1 schema.
   - Organize folders by resource or workflow.
   - Avoid duplicate requests; update matching method/path requests in place.
   - Add new requests only for changed or newly introduced API behavior.
   - Update existing requests when the current changes alter methods, paths, headers, auth, query parameters, payloads, or response contracts.
   - Remove or mark obsolete requests only when the current changes remove or replace that API behavior.
   - Use variables such as `{{base_url}}`, `{{access_token}}`, `{{tenant_id}}`, and resource IDs instead of hardcoded local values.
   - Prefer request-level create/update MCP tools for targeted changes; use full collection replacement only when required, and preserve existing IDs in the request body.

4. Create or update the matching cloud environment.
   - Include every collection variable needed to run the changed requests.
   - Use documented local defaults when available, such as host ports from `.env.example`, Compose files, Makefile targets, or local development docs.
   - When no safe default exists, leave the value blank and add a concise `description` explaining the expected value, for example "Bearer JWT access token for authenticated API requests."
   - Mark credentials, tokens, API keys, passwords, and other sensitive values as `type: "secret"` when supported by the environment format.
   - Do not sync real secrets, real customer data, regulated data, or personal account identifiers.
   - Preserve existing environment values, variable names, descriptions, and enabled flags unless the current changes supersede them.

5. Preserve and adjust supporting behavior.
   - Preserve existing scripts, variables, folders, and examples unless the current changes supersede them.
   - Add or update post-response tests only when needed to reflect the changed request contract.
   - Save response values with `pm.collectionVariables.set` or `pm.environment.set` only when later changed requests need them.
   - Add negative-case requests only when they are directly relevant to the changed validation, auth, or tenant-isolation behavior.

6. Keep example data minimal and relevant.
   - Include representative success and failure payloads for changed requests when useful.
   - Do not include secrets, real customer data, or regulated data.

## Local Collection and Environment Workflow

Use local repository Postman JSON only when the user explicitly requests local files, import/export artifacts, or updates to existing repository Postman assets.

1. Use existing repository collection/environment files if present.
2. Create new local JSON only when explicitly requested and no suitable local files exist.
3. Follow the same request, variable, script, example-data, and secrecy rules as cloud sync.
4. Do not delete, rewrite, or reformat unrelated local Postman artifacts.

## Script Patterns

Read `references/local-collection-guidelines.md` only when writing scripts, collection JSON, or environment JSON.

## Final Response

Report the target workspace name and ID, collection/environment created or updated with IDs when available, requests added/changed/removed, variables introduced or updated, placeholder descriptions added for missing defaults, and whether any local repository Postman files were changed.
