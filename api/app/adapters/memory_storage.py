from app.domain.ports import ObjectNotFoundError


class InMemoryStorage:
    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self._objects[key] = data

    def get(self, key: str) -> bytes:
        try:
            return self._objects[key]
        except KeyError:
            raise ObjectNotFoundError(key) from None

    def exists(self, key: str) -> bool:
        return key in self._objects

    def presigned_url(self, key: str, expires_in_seconds: int) -> str:
        return f"memory://{key}?expires_in={expires_in_seconds}"
