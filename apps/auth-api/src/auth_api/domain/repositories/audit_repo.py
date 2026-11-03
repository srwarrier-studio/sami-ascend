from abc import ABC, abstractmethod
from dataclasses import dataclass

from auth_api.domain.entities.audit_event import AuditEvent


@dataclass
class AuditFilter:
    actor: str | None = None
    action: str | None = None
    outcome: str | None = None
    start: str | None = None
    end: str | None = None


class AuditRepo(ABC):
    @abstractmethod
    def add(self, event: AuditEvent) -> None: ...

    @abstractmethod
    def list(self, filters: AuditFilter, limit: int, before: int | None) -> list[AuditEvent]: ...
