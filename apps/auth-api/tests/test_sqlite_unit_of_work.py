import stat

from auth_api.domain.entities.audit_event import AuditEvent
from auth_api.domain.value_objects.email_id import EmailID
from auth_api.domain.value_objects.role import Role
from auth_api.infrastructure.mock.mock_user_repo import MOCK_USER
from auth_api.infrastructure.sqlite.sqlite_unit_of_work import SqliteAuthUnitOfWork


def test_committed_user_is_found_with_roles_intact(tmp_path):
    uow = SqliteAuthUnitOfWork(str(tmp_path / "auth.db"))
    MOCK_USER.roles = [Role.STORES, Role.QUALITY]

    with uow:
        uow.user_repo.add(MOCK_USER)
        uow.commit()

    with uow:
        found = uow.user_repo.find_by_email(EmailID("test@email.com"))

    assert found == MOCK_USER
    assert found.roles == [Role.QUALITY, Role.STORES]
    assert found.sap_username == "SAP_READONLY"
    MOCK_USER.roles = [Role.STORES]


def test_uncommitted_user_is_rolled_back(tmp_path):
    uow = SqliteAuthUnitOfWork(str(tmp_path / "auth.db"))

    with uow:
        uow.user_repo.add(MOCK_USER)

    with uow:
        assert uow.user_repo.find_all() == []


def test_audit_event_is_stored(tmp_path):
    uow = SqliteAuthUnitOfWork(str(tmp_path / "auth.db"))

    with uow:
        uow.audit_repo.add(AuditEvent("sarath", "user_created", "a@b.com", "success"))
        uow.commit()

    with uow:
        row = uow.conn.execute("SELECT actor, action FROM audit_log").fetchone()
    assert (row["actor"], row["action"]) == ("sarath", "user_created")


def test_database_file_is_owner_only(tmp_path):
    path = tmp_path / "auth.db"

    SqliteAuthUnitOfWork(str(path))

    assert stat.S_IMODE(path.stat().st_mode) == 0o600
