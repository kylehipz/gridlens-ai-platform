# GridLens Frontend

The frontend is a Vite React TypeScript app for the GridLens browser workspace.
It currently provides the application shell, development sign-in, workspace
picker, required route scaffolds, API request primitives, screen-state
components, and Vitest/React Testing Library setup.

## Commands

Run commands from the repository root:

```sh
make run-frontend
make test-frontend
```

Run commands directly from this directory:

```sh
npm run dev
npm run build
npm test -- --run
```

## Development Auth

The sign-in route uses a local development session stored in `localStorage`.
This exists only to exercise protected routing and tenant-aware navigation.
Server-side APIs must still enforce authentication, authorization, and tenant
isolation.

## Structure

- `src/app/`: app provider wiring.
- `src/routes/`: route definitions and protected-route behavior.
- `src/pages/`: route-level scaffold pages.
- `src/components/`: shared shell and UI state primitives.
- `src/api/`: API client and error normalization.
- `src/hooks/`: shared React hooks.
- `src/styles/`: global design tokens and layout styles.
- `src/test/`: frontend test setup and render utilities.
