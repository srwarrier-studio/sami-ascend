import sqlite3
import stat

from auth_api.domain.entities.audit_event import AuditEvent
from auth_api.domain.value_objects.email_id import EmailID
from token_verification import Company, Role
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


def test_committed_user_keeps_its_companies(tmp_path):
    uow = SqliteAuthUnitOfWork(str(tmp_path / "auth.db"))
    MOCK_USER.companies = [Company.ORGANICA, Company.SABINSA]

    with uow:
        uow.user_repo.add(MOCK_USER)
        uow.commit()

    with uow:
        found = uow.user_repo.find_by_email(EmailID("test@email.com"))

    assert found.companies == [Company.ORGANICA, Company.SABINSA]
    MOCK_USER.companies = []


def test_user_without_companies_is_found_with_an_empty_list(tmp_path):
    uow = SqliteAuthUnitOfWork(str(tmp_path / "auth.db"))

    with uow:
        uow.user_repo.add(MOCK_USER)
        uow.commit()

    with uow:
        assert uow.user_repo.find_by_email(EmailID("test@email.com")).companies == []


def test_database_made_before_companies_gets_the_table_and_keeps_its_users(tmp_path):
    path = str(tmp_path / "auth.db")
    SqliteAuthUnitOfWork(path)

    conn = sqlite3.connect(path)
    conn.execute("DROP TABLE user_companies")
    conn.commit()
    conn.close()

    uow = SqliteAuthUnitOfWork(path)

    with uow:
        assert uow.conn.execute("SELECT COUNT(*) FROM user_companies").fetchone()[0] == 0


def test_uncommitted_user_is_rolled_back(tmp_path):
    uow = SqliteAuthUnitOfWork(str(tmp_path / "auth.db"))

    with uow:
        uow.user_repo.add(MOCK_USER)

    with uow:
        assert uow.user_repo.find_all() == []


def test_audit_event_is_stored(tmp_path):
    uow = SqliteAuthUnitOfWork(str(tmp_path / "auth.db"))

    with uow:
        uow.audit_repo.add(AuditEvent("sarath", "user.create", "a@b.com", "success"))
        uow.commit()

    with uow:
        row = uow.conn.execute("SELECT actor, action FROM audit_log").fetchone()
    assert (row["actor"], row["action"]) == ("sarath", "user.create")


def test_database_file_is_owner_only(tmp_path):
    path = tmp_path / "auth.db"

    SqliteAuthUnitOfWork(str(path))

    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_an_old_audit_table_gains_detail_and_keeps_its_rows(tmp_path):
    import sqlite3

    path = str(tmp_path / "auth.db")
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL, outcome TEXT NOT NULL)")
    conn.execute("INSERT INTO audit_log (at, actor, action, target, outcome) VALUES ('2026-01-01', 'old', 'user_created', 'a@b.com', 'success')")
    conn.commit()
    conn.close()

    uow = SqliteAuthUnitOfWork(path)

    with uow:
        row = uow.conn.execute("SELECT actor, detail FROM audit_log").fetchone()
    assert (row["actor"], row["detail"]) == ("old", "")


def test_a_login_audit_event_keeps_its_detail(tmp_path):
    uow = SqliteAuthUnitOfWork(str(tmp_path / "auth.db"))

    with uow:
        uow.audit_repo.add(AuditEvent("a@b.com", "login.password", "a@b.com", "failed", "bad_password"))
        uow.commit()

    with uow:
        assert uow.conn.execute("SELECT detail FROM audit_log").fetchone()["detail"] == "bad_password"
