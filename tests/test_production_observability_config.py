from pathlib import Path
from unittest import TestCase

from gridlens_observability import settings_from_env

ROOT = Path(__file__).resolve().parents[1]


def parse_env_example(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        values[key] = value
    return values


class ProductionObservabilityConfigTests(TestCase):
    def test_production_env_selects_aws_exporters(self) -> None:
        env = parse_env_example(ROOT / "infra" / "production" / "observability.env.example")
        settings = settings_from_env(env)

        self.assertTrue(settings.is_production)
        self.assertEqual("cloudwatch-logs", settings.log_exporter)
        self.assertEqual("cloudwatch", settings.metrics_exporter)
        self.assertEqual("xray", settings.traces_exporter)
        self.assertEqual("gridlens", settings.service_name)

    def test_production_observability_config_has_no_static_aws_credentials(self) -> None:
        text = (ROOT / "infra" / "production" / "observability.env.example").read_text()

        self.assertIn("CLOUDWATCH_LOG_GROUP=/gridlens/production/services", text)
        self.assertIn("CLOUDWATCH_METRIC_NAMESPACE=GridLens/Production", text)
        self.assertIn("XRAY_TRACE_NAME=gridlens-production", text)
        self.assertNotIn("AWS_ACCESS_KEY_ID", text)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", text)
        self.assertNotIn("AWS_SESSION_TOKEN", text)
        self.assertNotIn("AKIA", text)
