from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Pagination:
    limit: int
    offset: int
    total_count: int
    has_next: bool
    next_offset: int | None = None

    @classmethod
    def from_page(cls, *, limit: int, offset: int, total_count: int) -> "Pagination":
        next_offset = offset + limit
        has_next = next_offset < total_count
        return cls(
            limit=limit,
            offset=offset,
            total_count=total_count,
            has_next=has_next,
            next_offset=next_offset if has_next else None,
        )


@dataclass(frozen=True)
class ListResponse(Generic[T]):
    items: list[T]
    pagination: Pagination

    def to_dict(self) -> dict[str, object]:
        return {"items": self.items, "pagination": self.pagination.__dict__}
