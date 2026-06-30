from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from gridlens_observability import configure_observability, settings_from_env

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
    def test_production_env_selects_stdout_logs_and_adot_otlp_exporters(self) -> None:
        env = parse_env_example(ROOT / "infra" / "production" / "observability.env.example")
        settings = settings_from_env(env)

        self.assertTrue(settings.is_production)
        self.assertEqual("stdout", settings.log_exporter)
        self.assertEqual("otlp", settings.metrics_exporter)
        self.assertEqual("otlp", settings.traces_exporter)
        self.assertEqual("http://localhost:4318", settings.otlp_endpoint)
        self.assertEqual("gridlens", settings.service_name)

    def test_production_observability_configures_adot_without_otel_logs(self) -> None:
        env = parse_env_example(ROOT / "infra" / "production" / "observability.env.example")

        with (
            patch("gridlens_observability.setup.configure_json_logging") as json_logging,
            patch("gridlens_observability.setup.configure_otel_logging") as otel_logging,
            patch("gridlens_observability.setup.configure_otel_metrics") as otel_metrics,
            patch("gridlens_observability.setup.configure_otel_tracing") as otel_tracing,
        ):
            settings = configure_observability(service_name="identity-tenant-service", environ=env)

        self.assertTrue(settings.is_production)
        json_logging.assert_called_once()
        otel_logging.assert_not_called()
        otel_metrics.assert_called_once_with(
            endpoint="http://localhost:4318",
            service_name="identity-tenant-service",
        )
        otel_tracing.assert_called_once_with(
            endpoint="http://localhost:4318",
            service_name="identity-tenant-service",
        )

    def test_production_observability_config_has_no_static_aws_credentials(self) -> None:
        text = (ROOT / "infra" / "production" / "observability.env.example").read_text()

        self.assertIn("LOG_EXPORTER=stdout", text)
        self.assertIn("METRICS_EXPORTER=otlp", text)
        self.assertIn("TRACES_EXPORTER=otlp", text)
        self.assertIn("OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318", text)
        self.assertIn("CLOUDWATCH_LOG_GROUP=/gridlens/production/services", text)
        self.assertIn("CLOUDWATCH_METRIC_NAMESPACE=GridLens/Production", text)
        self.assertIn("XRAY_TRACE_NAME=gridlens-production", text)
        self.assertNotIn("LOG_EXPORTER=cloudwatch-logs", text)
        self.assertNotIn("AWS_ACCESS_KEY_ID", text)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", text)
        self.assertNotIn("AWS_SESSION_TOKEN", text)
        self.assertNotIn("AKIA", text)
