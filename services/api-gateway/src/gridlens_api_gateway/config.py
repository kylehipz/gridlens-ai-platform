from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_env: str
    host: str
    port: int
    log_level: str


def load_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "local"),
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        log_level=os.getenv("LOG_LEVEL", "info"),
    )
