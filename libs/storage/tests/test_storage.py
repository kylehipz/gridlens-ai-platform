import unittest

from gridlens_storage import FakeObjectStorage, S3ObjectStorage


class FakeS3Client:
    def __init__(self):
        self.calls = []

    def put_object(self, **kwargs):
        self.calls.append(("put", kwargs))


class StorageTests(unittest.TestCase):
    def test_fake_adapter_put_get_delete_and_presign(self):
        storage = FakeObjectStorage()
        key = "tenants/tenant_a/files/file_1/source.csv"
        metadata = storage.put(key, b"content")
        self.assertEqual(7, metadata.size_bytes)
        self.assertEqual(b"content", storage.get(key))
        self.assertEqual("fake://object/tenants/tenant_a/files/file_1/source.csv?expires=60", storage.presign_get(key, expires_seconds=60))
        storage.delete(key)
        with self.assertRaises(KeyError):
            storage.get(key)

    def test_s3_seam_uses_injected_client_and_hides_client_repr(self):
        client = FakeS3Client()
        storage = S3ObjectStorage(bucket="gridlens-dev", client=client)
        storage.put("tenants/tenant_a/files/file_1/source.csv", b"x")
        self.assertEqual("put", client.calls[0][0])
        self.assertNotIn("FakeS3Client", repr(storage))


if __name__ == "__main__":
    unittest.main()
