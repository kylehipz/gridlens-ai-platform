from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol


@dataclass(frozen=True)
class ObjectMetadata:
    key: str
    checksum_sha256: str
    size_bytes: int


class ObjectStorage(Protocol):
    def put(self, key: str, content: bytes) -> ObjectMetadata:
        ...

    def get(self, key: str) -> bytes:
        ...

    def delete(self, key: str) -> None:
        ...

    def presign_get(self, key: str, *, expires_seconds: int) -> str:
        ...


class FakeObjectStorage:
    def __init__(self):
        self._objects: dict[str, bytes] = {}

    def put(self, key: str, content: bytes) -> ObjectMetadata:
        self._objects[key] = content
        return ObjectMetadata(key=key, checksum_sha256=sha256(content).hexdigest(), size_bytes=len(content))

    def get(self, key: str) -> bytes:
        return self._objects[key]

    def delete(self, key: str) -> None:
        self._objects.pop(key, None)

    def presign_get(self, key: str, *, expires_seconds: int) -> str:
        if key not in self._objects:
            raise KeyError(key)
        return f"fake://object/{key}?expires={expires_seconds}"


class S3ObjectStorage:
    def __init__(self, *, bucket: str, client):
        self.bucket = bucket
        self.client = client

    def __repr__(self) -> str:
        return f"S3ObjectStorage(bucket={self.bucket!r}, client=***)"

    def put(self, key: str, content: bytes) -> ObjectMetadata:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        return ObjectMetadata(key=key, checksum_sha256=sha256(content).hexdigest(), size_bytes=len(content))

    def get(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def presign_get(self, key: str, *, expires_seconds: int) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )
