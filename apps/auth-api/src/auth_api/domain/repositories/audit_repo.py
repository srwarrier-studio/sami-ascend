from abc import ABC, abstractmethod

from auth_api.domain.entities.audit_event import AuditEvent


class AuditRepo(ABC):
    @abstractmethod
    def add(self, event: AuditEvent) -> None: ...
