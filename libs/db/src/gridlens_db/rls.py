from dataclasses import dataclass
from typing import Any

from sqlalchemy import text


@dataclass(frozen=True)
class RlsSessionContext:
    tenant_id: str
    actor_id: str
    request_id: str

    def settings(self) -> dict[str, str]:
        return {
            "app.tenant_id": self.tenant_id,
            "app.actor_id": self.actor_id,
            "app.request_id": self.request_id,
        }

    def apply(self, connection: Any) -> None:
        for key, value in self.settings().items():
            connection.execute(
                text("select set_config(:key, :value, true)"),
                {"key": key, "value": value},
            )
