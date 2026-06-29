---
name: create-postman-requests
description: Create or update Postman Collection v2.1 requests for API workflows, with local collection JSON as the durable source and optional Postman MCP sync. Use when Codex needs to create a Postman collection, add or update requests, add tests, save variables, chain requests, or prepare API QA workflows.
---

# Create Postman Requests

Use this skill to maintain API request workflows in Postman format.

## Source of Truth

- Prefer local Postman Collection v2.1 JSON files in the repository.
- Use an existing collection if one can be found.
- Create a new collection only when no suitable collection exists.
- Use Postman MCP tools only when the user explicitly asks to sync to Postman cloud or provides workspace/collection IDs.
- Before any Postman MCP call, read the `postman://instructions` MCP resource and follow it.

## Local Collection Workflow

1. Locate API documentation and routes.
   - Inspect OpenAPI specs, route files, API docs, tests, and existing Postman collections.
   - Ask only for base URL, auth, or environment details that cannot be inferred.

2. Create or update the collection.
   - Use Postman Collection v2.1 schema.
   - Organize folders by resource or workflow.
   - Avoid duplicate requests; update matching method/path requests in place.
   - Use variables such as `{{base_url}}`, `{{access_token}}`, `{{tenant_id}}`, and resource IDs instead of hardcoded local values.

3. Add useful scripts.
   - Add post-response tests for status code, content type, required fields, and business invariants.
   - Save response values with `pm.collectionVariables.set` or `pm.environment.set` when later requests need them.
   - Chain requests by using saved IDs/tokens from earlier requests.
   - Include negative-case requests for validation, auth, and tenant isolation when relevant.

4. Add examples when useful.
   - Include representative success and failure payloads.
   - Do not include secrets, real customer data, or regulated data.

## Cloud Sync Workflow

Use this only when explicitly requested:

1. Confirm target workspace and collection ID, or create a collection if the user requests it and provides a workspace.
2. Fetch the existing cloud collection before updating.
3. Create or update requests through Postman MCP tools.
4. Preserve scripts, variables, folders, and examples unless the requested change supersedes them.

## Script Patterns

Read `references/local-collection-guidelines.md` when writing scripts or collection JSON.

## Final Response

Report the local collection path, requests added or changed, variables introduced, and whether any cloud sync was performed.
