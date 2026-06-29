# Issue 37: T06: Frontend Scaffold

## Source
- GitHub issue: https://github.com/kylehipz/gridlens-ai-platform/issues/37
- Branch: feat/37-t06-frontend-scaffold
- Related docs/specs: docs/requirements.md, docs/folder-structure.md, docs/testing-guideline.md, docs/local-development.md, docs/gridlens_ui.svg

## Summary
Create the GridLens browser app foundation as a real tenant-aware workspace, not a marketing page. The scaffold must establish the Vite React TypeScript app, route shell, protected-route behavior, reusable UI primitives, API/error/loading patterns, and frontend test utilities so later feature work can build on stable conventions.

## Acceptance Criteria
- [ ] Vite React TypeScript app exists under `frontend/`.
- [ ] Routes exist for sign in, workspace picker, dashboard, assistant, datasets, evaluations, anomalies, reports, audit, usage, and settings.
- [ ] Design tokens, layout primitives, navigation, API client, error/loading primitives, and test setup exist.
- [ ] UI styling is aligned to `docs/gridlens_ui.svg`.
- [ ] `make run-frontend` starts the app and shows the sign-in or workspace route.
- [ ] `make test-frontend` runs Vitest/React Testing Library setup.
- [ ] A protected route redirects unauthenticated dev users to sign-in.
- [ ] The app shell remains usable at mobile and desktop widths without text overlapping navigation or buttons.

## Checkpoints
1. Frontend toolchain scaffold
   - Intent: Add the Vite React TypeScript project and stable package/test/build scripts.
   - Scope: `frontend/package.json`, Vite config, TypeScript configs, index HTML, source entry points, root Makefile frontend targets.
   - Completion criteria: `npm install` can produce a lockfile, `npm run build` and `npm test -- --run` are wired through Makefile targets.
   - Risks/notes: Keep frontend dependencies public-safe and development-only where appropriate; avoid changing backend test commands beyond replacing the frontend placeholder.

2. Route, auth, and app shell foundation
   - Intent: Establish route-level layouts and protected-route behavior for the required product areas.
   - Scope: `frontend/src/app`, `frontend/src/routes`, `frontend/src/pages`, navigation/layout components, auth/workspace state helpers.
   - Completion criteria: Required routes render through a tenant-aware shell, unauthenticated protected routes redirect to sign-in, and the first authenticated viewport is a real workspace.
   - Risks/notes: This is a dev scaffold only; do not pretend frontend route guards enforce tenant isolation server-side.

3. Shared UI, API, and state primitives
   - Intent: Provide reusable design tokens, loading/error/empty states, API client normalization, and query/form patterns.
   - Scope: `frontend/src/styles`, `frontend/src/components`, `frontend/src/api`, reusable hooks and utilities.
   - Completion criteria: Feature pages consume shared primitives and no permanent hardcoded API data is embedded as if it were authoritative backend state.
   - Risks/notes: Static page summaries are acceptable scaffold copy; future API-backed feature pages must replace page-local samples with service data.

4. Frontend test utilities and coverage
   - Intent: Add Vitest and React Testing Library setup that protects routing, auth redirect, API normalization, and responsive navigation behavior.
   - Scope: `frontend/src/test`, `*.test.tsx`, package scripts, Makefile `test-frontend`.
   - Completion criteria: Tests cover unauthenticated redirects, route rendering, API error normalization, and mobile navigation interaction.
   - Risks/notes: Tests should not require network access or real tenant data.

5. Responsive polish and documentation
   - Intent: Ensure the scaffold is usable at mobile and desktop widths and contributor commands are documented.
   - Scope: CSS tokens/layout, `frontend/README.md`, root `README.md`, relevant docs command references.
   - Completion criteria: Build/tests pass, manual responsive inspection shows no overlapping navigation/buttons, and docs list the new `make run-frontend`/`make test-frontend` behavior.
   - Risks/notes: Do not broaden the scope into real feature workflows before their API tasks exist.

## Test Plan
### Automated
- `make test-frontend`: install-independent Vitest/React Testing Library command from the frontend package; expects all frontend unit and component tests to pass.
- `npm run build` from `frontend/`: validates TypeScript compilation and Vite production build.
- Protected route test: render a protected path without dev auth, expect redirect/sign-in content.
- Route smoke test: render required app routes with authenticated dev state, expect route-specific landmarks/headings.
- API client test: mock failed fetch response, expect normalized `ApiError` with status and message.
- Mobile navigation test: render narrow viewport, open navigation menu, activate a route, expect navigation remains operable and closes predictably.
- `make test`: confirms adding frontend tooling does not break the default offline repository suite.

### Manual / QA
- Run `make run-frontend`, open the printed local Vite URL, and verify the unauthenticated initial view is sign-in.
- Use the development sign-in path, verify workspace picker/dashboard shell renders with tenant name, route navigation, and status primitives.
- Visit `/dashboard`, `/assistant`, `/datasets`, `/evaluations`, `/anomalies`, `/reports`, `/audit`, `/usage`, and `/settings`; each should render inside the app shell.
- At a mobile-width viewport, open and close navigation and verify text does not overlap nav controls or action buttons.
- At a desktop-width viewport, verify the persistent shell remains scannable and aligned with `docs/gridlens_ui.svg` visual direction.

## Assumptions and Open Questions
- The referenced source task file `tasks/01-foundation-and-architecture.md` is not present in this checkout; the GitHub issue body is treated as the authoritative task content.
- Dev authentication is a frontend-only scaffold used to exercise route behavior. Backend tenant isolation remains mandatory for real APIs.
- Static scaffold page summaries may communicate intended feature areas, but later API feature tasks must replace them with service-backed data.

## Implementation Notes
- Use Vite, React, TypeScript, React Router, Vitest, and React Testing Library.
- Keep route definitions centralized so later feature modules can attach loaders, queries, and forms without replacing the shell.
- Prefer CSS custom property design tokens over one-off colors and spacing.
- Expose stable root commands: `make run-frontend` and `make test-frontend`.
