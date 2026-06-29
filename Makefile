.PHONY: setup test test-backend test-frontend lint format migrate seed run

setup:
	@printf '%s\n' 'GridLens setup'
	@printf '%s\n' 'Current state: documentation and repository scaffolding only.'
	@test -f README.md
	@test -f .env.example || printf '%s\n' 'Note: .env.example is added by the repository hygiene checkpoint.'
	@printf '%s\n' 'No package installation is required yet.'
	@printf '%s\n' 'Next: inspect .env.example, then run make test.'

test: test-backend test-frontend
	@printf '%s\n' 'Repository test placeholders completed.'

test-backend:
	@if test -d services; then \
		printf '%s\n' 'Backend services directory exists, but no backend test runner is configured yet.'; \
	else \
		printf '%s\n' 'No services/ directory yet; backend tests are pending implementation work.'; \
	fi

test-frontend:
	@if test -d frontend; then \
		printf '%s\n' 'Frontend directory exists, but no frontend test runner is configured yet.'; \
	else \
		printf '%s\n' 'No frontend/ directory yet; frontend tests are pending implementation work.'; \
	fi

lint:
	@printf '%s\n' 'Checking repository hygiene...'
	@if git grep -n -I -E '^(<<<<<<<|=======|>>>>>>>)' -- .; then \
		printf '%s\n' 'Unresolved merge conflict marker found.'; \
		exit 1; \
	fi
	@if test -n "$$GITHUB_BASE_REF"; then \
		base_ref="origin/$$GITHUB_BASE_REF"; \
		if ! git rev-parse --verify --quiet "$$base_ref" >/dev/null; then \
			git fetch --no-tags --prune --depth=1 origin \
				"+refs/heads/$$GITHUB_BASE_REF:refs/remotes/origin/$$GITHUB_BASE_REF"; \
		fi; \
		git diff --check "$$base_ref...HEAD"; \
	else \
		git diff --check --cached; \
		git diff --check; \
	fi
	@printf '%s\n' 'Repository hygiene checks passed.'

format:
	@printf '%s\n' 'No formatter is configured yet. Future Python and frontend formatters should run here.'

migrate:
	@printf '%s\n' 'No database migrations exist yet. Future migration commands should run here.'

seed:
	@printf '%s\n' 'No seed data task exists yet. Future tasks must use synthetic development data only.'

run:
	@printf '%s\n' 'No local application stack exists yet. Future Docker Compose or dev-server commands should run here.'
