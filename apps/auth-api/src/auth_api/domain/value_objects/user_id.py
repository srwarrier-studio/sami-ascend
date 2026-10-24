from uuid import UUID, uuid4
from dataclasses import dataclass



@dataclass(frozen=True)
class UserID:
    value: UUID

    @classmethod
    def new(cls):
        return cls(uuid4())

    