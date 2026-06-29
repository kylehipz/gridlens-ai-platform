import unittest

from gridlens_ai import BedrockChatProvider, FakeChatProvider, FakeEmbeddingProvider
from gridlens_ai.providers import RequestMetadata


class FakeBedrockClient:
    def __init__(self):
        self.calls = []

    def invoke_model(self, **kwargs):
        self.calls.append(kwargs)
        return {"output": "ok"}


class AiTests(unittest.TestCase):
    def test_fake_providers_are_deterministic(self):
        metadata = RequestMetadata("tenant_a", "req", "corr")
        provider = FakeEmbeddingProvider()
        self.assertEqual(provider.embed("hello", metadata=metadata), provider.embed("hello", metadata=metadata))
        self.assertEqual("fake:tenant_a:hello", FakeChatProvider().complete([{"role": "user", "content": "hello"}], metadata=metadata))

    def test_bedrock_seam_uses_injected_client_and_metadata(self):
        client = FakeBedrockClient()
        output = BedrockChatProvider(model_id="model", client=client).complete(
            [{"role": "user", "content": "hello"}],
            metadata=RequestMetadata("tenant_a", "req", "corr"),
        )
        self.assertEqual("ok", output)
        self.assertEqual("tenant_a", client.calls[0]["body"]["metadata"]["tenant_id"])


if __name__ == "__main__":
    unittest.main()
