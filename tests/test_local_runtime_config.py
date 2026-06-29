from pathlib import Path
import re
from unittest import TestCase


ROOT = Path(__file__).resolve().parents[1]


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
            "127.0.0.1:${API_DEBUG_PORT:-5678}:5678",
            "127.0.0.1:${WORKER_DEBUG_PORT:-5679}:5679",
        ]

        merged_compose = f"{compose}\n{dev_compose}"
        for binding in expected_bindings:
            with self.subTest(binding=binding):
                self.assertIn(binding, merged_compose)

    def test_api_host_port_is_separate_from_container_listener(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text()
        env_example = (ROOT / ".env.example").read_text()

        self.assertIn("API_PORT: 8000", compose)
        self.assertIn("127.0.0.1:${API_HOST_PORT:-8000}:8000", compose)
        self.assertIn("API_HOST_PORT=8000", env_example)
        self.assertNotIn("${API_PORT:-8000}:8000", compose)
        self.assertNotIn("API_PORT=8000", env_example)

    def test_dev_overlay_uses_debug_reload_commands(self) -> None:
        dev_compose = (ROOT / "docker-compose.dev.yml").read_text()
        api_dockerfile = (ROOT / "services" / "api-gateway" / "Dockerfile").read_text()
        worker_dockerfile = (
            ROOT / "workers" / "local-runtime-worker" / "Dockerfile"
        ).read_text()

        self.assertIn("debugpy>=1.8,<2", api_dockerfile)
        self.assertIn("debugpy>=1.8,<2", worker_dockerfile)
        self.assertIn("/app/devtools/reload_debug.py", dev_compose)
        self.assertIn("gridlens_api_gateway.main", dev_compose)
        self.assertIn("API_DEBUG_PORT", dev_compose)
        self.assertIn("gridlens_local_runtime_worker.main", dev_compose)
        self.assertIn("WORKER_DEBUG_PORT", dev_compose)

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
