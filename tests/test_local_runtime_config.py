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
