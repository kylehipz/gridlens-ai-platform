from dataclasses import dataclass
import unittest

from gridlens_config import SettingsError, SettingsModel, field


@dataclass(frozen=True)
class ServiceSettings(SettingsModel):
    database_url: str = field(env="DATABASE_URL", secret=True)
    service_name: str = field(env="SERVICE_NAME", default="api")
    debug: bool = field(env="DEBUG", default=False)


class SettingsTests(unittest.TestCase):
    def test_required_database_url_fails_fast(self):
        with self.assertRaisesRegex(SettingsError, "DATABASE_URL"):
            ServiceSettings.from_env({})

    def test_loads_typed_settings_and_redacts_secrets(self):
        settings = ServiceSettings.from_env(
            {"DATABASE_URL": "postgresql://user:pass@localhost/db", "DEBUG": "true"}
        )
        self.assertTrue(settings.debug)
        self.assertEqual("api", settings.service_name)
        self.assertNotIn("pass", repr(settings))
        self.assertEqual("postgresql://***@localhost/db", settings.redacted_dict()["database_url"])


if __name__ == "__main__":
    unittest.main()
