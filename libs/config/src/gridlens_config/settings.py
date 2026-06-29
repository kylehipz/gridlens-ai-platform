import os
from dataclasses import MISSING, dataclass, fields
from typing import Any


class SettingsError(ValueError):
    pass


def field(*, env: str, default: Any = MISSING, secret: bool = False) -> Any:
    from dataclasses import field as dc_field

    metadata = {"env": env, "secret": secret}
    if default is MISSING:
        return dc_field(metadata=metadata, repr=not secret)
    return dc_field(default=default, metadata=metadata, repr=not secret)


@dataclass(frozen=True)
class SettingsModel:
    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None):
        source = os.environ if environ is None else environ
        values: dict[str, Any] = {}
        missing: list[str] = []
        for item in fields(cls):
            env_name = item.metadata.get("env", item.name.upper())
            raw = source.get(env_name)
            if raw is None:
                if item.default is MISSING:
                    missing.append(env_name)
                else:
                    values[item.name] = item.default
                continue
            values[item.name] = _coerce(raw, item.type)
        if missing:
            raise SettingsError(f"Missing required configuration: {', '.join(sorted(missing))}")
        return cls(**values)

    def redacted_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for item in fields(self):
            value = getattr(self, item.name)
            if item.metadata.get("secret") or _looks_secret(item.name):
                result[item.name] = _redact(value)
            else:
                result[item.name] = value
        return result

    def __repr__(self) -> str:
        body = ", ".join(f"{key}={value!r}" for key, value in self.redacted_dict().items())
        return f"{self.__class__.__name__}({body})"


def _coerce(raw: str, annotation: Any) -> Any:
    if annotation in (int, "int"):
        return int(raw)
    if annotation in (bool, "bool"):
        return raw.lower() in {"1", "true", "yes", "on"}
    return raw


def _looks_secret(name: str) -> bool:
    lowered = name.lower()
    return any(part in lowered for part in ("password", "secret", "token", "key", "url"))


def _redact(value: Any) -> str:
    text = str(value)
    if "://" in text and "@" in text:
        scheme, rest = text.split("://", 1)
        _, host = rest.rsplit("@", 1)
        return f"{scheme}://***@{host}"
    return "***"
