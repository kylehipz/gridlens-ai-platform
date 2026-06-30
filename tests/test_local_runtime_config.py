import re
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]

API_SERVICES = [
    "identity-tenant-service",
    "data-operations-service",
    "assistant-service",
    "program-evaluation-service",
    "insights-reporting-service",
    "governance-service",
    "alerts-anomalies-service",
]

WORKER_SERVICES = [
    "data-operations-worker",
    "assistant-worker",
    "program-evaluation-worker",
    "insights-reporting-worker",
]

OBSERVABILITY_SERVICES = [
    "otel-collector",
    "prometheus",
    "loki",
    "tempo",
    "grafana",
]


class LocalRuntimeConfigTests(TestCase):
    def test_env_example_uses_managed_aws_placeholders_not_emulators(self) -> None:
        env_example = (ROOT / ".env.example").read_text()

        self.assertIn("AWS_PROFILE=gridlens-dev", env_example)
        self.assertIn("AWS_REGION=ap-southeast-1", env_example)
        self.assertIn("AWS_SDK_LOAD_CONFIG=1", env_example)
        self.assertNotIn("OBJECT_STORAGE_ENDPOINT=http://localhost:9000", env_example)
        self.assertNotIn("QUEUE_ENDPOINT=http://localhost:4566", env_example)
        self.assertNotIn("LOCALSTACK", env_example.upper())
        self.assertNotIn("MINIO", env_example.upper())
        self.assertNotIn("ELASTICMQ", env_example.upper())

    def test_compose_mounts_host_aws_config_read_only(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text()

        self.assertIn("${HOME}/.aws:/home/app/.aws:ro", compose)
        self.assertIn("AWS_SDK_LOAD_CONFIG: \"1\"", compose)
        self.assertNotIn("AWS_ACCESS_KEY_ID", compose)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", compose)
        self.assertNotIn("AWS_SESSION_TOKEN", compose)

    def test_compose_published_ports_are_loopback_only(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text()
        dev_compose = (ROOT / "docker-compose.dev.yml").read_text()

        expected_bindings = [
            "127.0.0.1:${POSTGRES_PORT:-5432}:5432",
            "127.0.0.1:${API_HOST_PORT:-8000}:8000",
            "127.0.0.1:${OTEL_HTTP_PORT:-4318}:4318",
            "127.0.0.1:${PROMETHEUS_PORT:-9090}:9090",
            "127.0.0.1:${LOKI_PORT:-3100}:3100",
            "127.0.0.1:${TEMPO_PORT:-3200}:3200",
            "127.0.0.1:${GRAFANA_PORT:-3000}:3000",
        ]

        merged_compose = f"{compose}\n{dev_compose}"
        for binding in expected_bindings:
            with self.subTest(binding=binding):
                self.assertIn(binding, merged_compose)
        self.assertNotIn("API_DEBUG_PORT", merged_compose)
        self.assertNotIn("WORKER_DEBUG_PORT", merged_compose)

    def test_api_host_port_is_separate_from_container_listener(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text()
        env_example = (ROOT / ".env.example").read_text()

        self.assertIn("API_PORT: 8000", compose)
        self.assertIn("127.0.0.1:${API_HOST_PORT:-8000}:8000", compose)
        self.assertIn("API_HOST_PORT=8000", env_example)
        self.assertNotIn("${API_PORT:-8000}:8000", compose)
        self.assertNotIn("API_PORT=8000", env_example)

    def test_kong_declarative_config_routes_api_health(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text()
        kong_config = (ROOT / "infra" / "local" / "kong" / "kong.yml").read_text()

        self.assertIn("KONG_DATABASE: \"off\"", compose)
        self.assertIn("KONG_DECLARATIVE_CONFIG: /kong/declarative/kong.yml", compose)
        self.assertIn("./infra/local/kong/kong.yml:/kong/declarative/kong.yml:ro", compose)
        self.assertIn("_format_version: \"3.0\"", kong_config)
        self.assertIn("name: gridlens-health-upstream", kong_config)
        self.assertIn("url: http://identity-tenant-service:8000/health", kong_config)
        self.assertIn("/api/v1/health", kong_config)
        self.assertIn("name: gridlens-observability-upstream", kong_config)
        self.assertIn("url: http://identity-tenant-service:8000", kong_config)
        self.assertIn("/__observability", kong_config)
        self.assertIn("/metrics", kong_config)

    def test_compose_starts_scaffold_services_and_workers(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text()
        dev_compose = (ROOT / "docker-compose.dev.yml").read_text()
        merged_compose = f"{compose}\n{dev_compose}"

        self.assertNotIn("\n  api:\n", merged_compose)
        self.assertNotIn("\n  api-gateway:\n", merged_compose)
        self.assertNotIn("\n  worker:\n", merged_compose)
        self.assertNotIn("services/api-gateway/Dockerfile", merged_compose)
        self.assertNotIn("workers/local-runtime-worker/Dockerfile", merged_compose)

        for service in API_SERVICES:
            with self.subTest(service=service):
                self.assertIn(f"\n  {service}:\n", compose)
                self.assertIn(f"\n  {service}:\n", dev_compose)
                self.assertIn(f"dockerfile: services/{service}/Dockerfile", compose)
                self.assertIn(f"./services/{service}/src:/app/src:ro", dev_compose)

        for worker in WORKER_SERVICES:
            with self.subTest(worker=worker):
                self.assertIn(f"\n  {worker}:\n", compose)
                self.assertIn(f"\n  {worker}:\n", dev_compose)

    def test_compose_starts_local_observability_stack(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text()
        env_example = (ROOT / ".env.example").read_text()
        prometheus = (ROOT / "infra" / "local" / "observability" / "prometheus.yml").read_text()
        otel = (ROOT / "infra" / "local" / "observability" / "otel-collector.yaml").read_text()
        datasources = (
            ROOT
            / "infra"
            / "local"
            / "observability"
            / "grafana"
            / "provisioning"
            / "datasources"
            / "datasources.yml"
        ).read_text()
        dashboard = (
            ROOT
            / "infra"
            / "local"
            / "observability"
            / "grafana"
            / "dashboards"
            / "service-health.json"
        ).read_text()

        for service in OBSERVABILITY_SERVICES:
            with self.subTest(service=service):
                self.assertIn(f"\n  {service}:\n", compose)

        self.assertIn("OBSERVABILITY_MODE: ${OBSERVABILITY_MODE:-local}", compose)
        self.assertIn("LOG_EXPORTER: ${LOG_EXPORTER:-loki}", compose)
        self.assertIn("METRICS_EXPORTER: ${METRICS_EXPORTER:-prometheus}", compose)
        self.assertIn("TRACES_EXPORTER: ${TRACES_EXPORTER:-tempo}", compose)
        self.assertIn("OTEL_EXPORTER_OTLP_ENDPOINT", compose)
        self.assertIn("OBSERVABILITY_MODE=local", env_example)
        self.assertIn("OBSERVABILITY_SMOKE_ROUTES_ENABLED=true", env_example)
        self.assertIn("OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318", env_example)
        self.assertIn("otel-collector:8889", prometheus)
        self.assertIn("loki:3100/loki/api/v1/push", otel)
        self.assertIn("tempo:4317", otel)
        self.assertIn("url: http://prometheus:9090", datasources)
        self.assertIn("url: http://loki:3100", datasources)
        self.assertIn("url: http://tempo:3200", datasources)
        self.assertIn("GridLens Local Service Health", dashboard)

    def test_dev_overlay_runs_modules_without_devtools(self) -> None:
        dev_compose = (ROOT / "docker-compose.dev.yml").read_text()
        identity_dockerfile = (
            ROOT / "services" / "identity-tenant-service" / "Dockerfile"
        ).read_text()
        data_operations_dockerfile = (
            ROOT / "services" / "data-operations-service" / "Dockerfile"
        ).read_text()
        pyproject = (ROOT / "pyproject.toml").read_text()

        self.assertNotIn("debugpy", pyproject)
        self.assertIn("pip install --no-cache-dir \".[dev]\"", identity_dockerfile)
        self.assertIn("pip install --no-cache-dir \".[dev]\"", data_operations_dockerfile)
        self.assertNotIn("devtools", identity_dockerfile)
        self.assertNotIn("devtools", data_operations_dockerfile)
        self.assertNotIn("/app/devtools/reload_debug.py", dev_compose)
        self.assertIn("gridlens_identity_tenant_service.main", dev_compose)
        self.assertIn("gridlens_identity_tenant_service.main:app", dev_compose)
        self.assertIn("gridlens_data_operations_service.workers.main", dev_compose)
        self.assertNotIn("gridlens_api_gateway", dev_compose)
        self.assertNotIn("gridlens_local_runtime_worker.main", dev_compose)

    def test_makefile_exposes_gateway_run_commands(self) -> None:
        makefile = (ROOT / "Makefile").read_text()

        self.assertIn("dev-gateway:", makefile)
        self.assertIn("up --build identity-tenant-service kong", makefile)
        self.assertIn("run-identity-tenant:", makefile)
        self.assertIn("uvicorn gridlens_identity_tenant_service.main:app", makefile)
        self.assertNotIn("run-api:", makefile)
        self.assertNotIn("gridlens_api_gateway", makefile)

    def test_docker_builds_use_root_pyproject_without_local_artifacts(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text()
        dockerignore = (ROOT / ".dockerignore").read_text()
        identity_dockerfile = (
            ROOT / "services" / "identity-tenant-service" / "Dockerfile"
        ).read_text()
        data_operations_dockerfile = (
            ROOT / "services" / "data-operations-service" / "Dockerfile"
        ).read_text()

        self.assertIn("context: .", compose)
        self.assertIn("dockerfile: services/identity-tenant-service/Dockerfile", compose)
        self.assertIn("dockerfile: services/data-operations-service/Dockerfile", compose)
        self.assertNotIn("dockerfile: services/api-gateway/Dockerfile", compose)
        self.assertNotIn("dockerfile: workers/local-runtime-worker/Dockerfile", compose)
        self.assertIn("COPY pyproject.toml ./", identity_dockerfile)
        self.assertIn("COPY pyproject.toml ./", data_operations_dockerfile)
        self.assertIn(".venv", dockerignore)
        self.assertIn(".git", dockerignore)

    def test_runtime_files_do_not_include_static_aws_credentials(self) -> None:
        secret_pattern = re.compile(
            r"AWS_(ACCESS_KEY_ID|SECRET_ACCESS_KEY|SESSION_TOKEN)\s*=|AKIA[0-9A-Z]{16}"
        )
        checked_paths = [
            ROOT / ".env.example",
            ROOT / "docker-compose.yml",
            ROOT / "docker-compose.dev.yml",
            ROOT / "Makefile",
            ROOT / "docs" / "local-development.md",
            ROOT / "README.md",
        ]

        for path in checked_paths:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(secret_pattern.search(path.read_text()))

    def test_default_tests_do_not_define_aws_network_opt_in(self) -> None:
        makefile = (ROOT / "Makefile").read_text()
        import_pattern = re.compile(r"^\s*(import|from)\s+(boto3|botocore)\b", re.MULTILINE)
        tests = "\n".join(path.read_text() for path in (ROOT / "tests").glob("test_*.py"))

        self.assertNotIn("LIVE_AWS", makefile)
        self.assertNotIn("AWS_NETWORK", makefile)
        self.assertIsNone(import_pattern.search(tests))

    def test_ci_runs_typecheck_lint_and_mocked_aws_database_checks(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text()

        self.assertIn("image: pgvector/pgvector:pg16", workflow)
        self.assertIn("run: make typecheck", workflow)
        self.assertIn("run: make lint", workflow)
        self.assertIn("run: make bootstrap-live-db", workflow)
        self.assertIn("run: make test-live-db", workflow)
        self.assertIn("POSTGRES_CONTAINER_ID=$container_id", workflow)
        self.assertIn('AWS_EC2_METADATA_DISABLED: "true"', workflow)
        self.assertIn("AWS_ACCESS_KEY_ID: mock", workflow)
        self.assertIn("AWS_SECRET_ACCESS_KEY: mock", workflow)
        self.assertIn("BEDROCK_TEXT_MODEL_ID: mock-text-model", workflow)

    def test_makefile_exposes_live_database_targets_for_ci(self) -> None:
        makefile = (ROOT / "Makefile").read_text()

        self.assertIn("bootstrap-live-db:", makefile)
        self.assertIn("test-live-db:", makefile)
        self.assertIn("POSTGRES_CONTAINER_ID ?=", makefile)
        self.assertIn("docker exec -e PGPASSWORD", makefile)
        self.assertIn("CREATE EXTENSION IF NOT EXISTS vector", makefile)
        self.assertIn("app.live_smoke_check", makefile)
