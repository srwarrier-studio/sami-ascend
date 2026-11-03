from auth_api.domain.entities.audit_event import AuditEvent
from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork
from auth_api.domain.repositories.audit_repo import AuditRepo
from auth_api.infrastructure.mock.mock_user_repo import MOCK_USER, MockUserRepo


class MockAuditRepo(AuditRepo):
    def __init__(self, events: list[AuditEvent]):
        self.events = events

    def add(self, event: AuditEvent) -> None:
        self.events.append(event)

    def list(self, filters, limit, before):
        return list(reversed(self.events))[:limit]


class MockAuthUnitOfWork(AuthUnitOfWork):
    def __init__(self):
        self.users = {MOCK_USER}
        self.events: list[AuditEvent] = []

    def __enter__(self):
        self.user_repo = MockUserRepo(self.users)
        self.audit_repo = MockAuditRepo(self.events)
        return self

    def rollback(self):
        print("Rollback executed")

    def commit(self):
        print("Commit Executed")
