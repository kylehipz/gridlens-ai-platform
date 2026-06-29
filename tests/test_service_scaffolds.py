import importlib
import sys
from pathlib import Path
from unittest import TestCase

from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[1]

SERVICES = {
    "identity-tenant-service": "gridlens_identity_tenant_service",
    "data-operations-service": "gridlens_data_operations_service",
    "assistant-service": "gridlens_assistant_service",
    "program-evaluation-service": "gridlens_program_evaluation_service",
    "insights-reporting-service": "gridlens_insights_reporting_service",
    "governance-service": "gridlens_governance_service",
    "alerts-anomalies-service": "gridlens_alerts_anomalies_service",
}

LAYERS = ("api", "application", "domain", "infrastructure", "workers")


class ServiceScaffoldTests(TestCase):
    def test_each_service_has_expected_package_layers(self) -> None:
        for service_name, package_name in SERVICES.items():
            with self.subTest(service=service_name):
                service_root = ROOT / "services" / service_name
                package_root = service_root / "src" / package_name

                self.assertTrue((service_root / "pyproject.toml").is_file())
                self.assertTrue((service_root / "Dockerfile").is_file())
                self.assertTrue((service_root / "README.md").is_file())
                self.assertTrue((service_root / "tests").is_dir())
                self.assertTrue((package_root / "__init__.py").is_file())
                self.assertTrue((package_root / "main.py").is_file())
                for layer in LAYERS:
                    self.assertTrue((package_root / layer / "__init__.py").is_file())

    def test_each_service_exposes_fastapi_app(self) -> None:
        for service_name, package_name in SERVICES.items():
            with self.subTest(service=service_name):
                src = str(ROOT / "services" / service_name / "src")
                if src not in sys.path:
                    sys.path.insert(0, src)

                module = importlib.import_module(f"{package_name}.main")

                self.assertIsInstance(module.app, FastAPI)
