from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol


@dataclass(frozen=True)
class RequestMetadata:
    tenant_id: str
    request_id: str
    correlation_id: str


class EmbeddingProvider(Protocol):
    def embed(self, text: str, *, metadata: RequestMetadata) -> list[float]:
        ...


class ChatProvider(Protocol):
    def complete(self, messages: list[dict[str, str]], *, metadata: RequestMetadata) -> str:
        ...


class FakeEmbeddingProvider:
    def embed(self, text: str, *, metadata: RequestMetadata) -> list[float]:
        digest = sha256(f"{metadata.tenant_id}:{text}".encode()).digest()
        return [round(byte / 255, 6) for byte in digest[:8]]


class FakeChatProvider:
    def complete(self, messages: list[dict[str, str]], *, metadata: RequestMetadata) -> str:
        last = messages[-1]["content"] if messages else ""
        return f"fake:{metadata.tenant_id}:{last[:32]}"


class BedrockChatProvider:
    def __init__(self, *, model_id: str, client):
        self.model_id = model_id
        self.client = client

    def complete(self, messages: list[dict[str, str]], *, metadata: RequestMetadata) -> str:
        response = self.client.invoke_model(
            modelId=self.model_id,
            body={"messages": messages, "metadata": metadata.__dict__},
        )
        return response["output"]
