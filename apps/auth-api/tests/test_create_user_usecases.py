import pytest

from auth_api.application.dto.create_user_dto import CreateFirstAdminDTO, CreateUserDTO
from auth_api.application.usecase.create_first_admin import CreateFirstAdmin
from auth_api.application.usecase.create_user import CreateUser
from auth_api.domain.errors import AdminAlreadyExists, UserAlreadyExists, WeakPassword
from auth_api.domain.value_objects.email_id import EmailID
from token_verification import Company, Role
from auth_api.infrastructure.interface.argon2_password_hasher import Argon2PasswordHasher
from auth_api.infrastructure.sqlite.sqlite_unit_of_work import SqliteAuthUnitOfWork

PASSWORD = "a-long-enough-password"


@pytest.fixture
def uow(tmp_path):
    return SqliteAuthUnitOfWork(str(tmp_path / "auth.db"))


def user_dto(email="Buyer@Email.com", password=PASSWORD):
    return CreateUserDTO(email, "Buyer One", password, "SAP_BUYER", ["purchase"], "sarath")


def test_creates_user_with_hashed_password_and_audit_event(uow):
    CreateUser(uow, Argon2PasswordHasher()).execute(user_dto())

    with uow:
        user = uow.user_repo.find_by_email(EmailID("buyer@email.com"))
        audit = uow.conn.execute("SELECT actor, action, target FROM audit_log").fetchone()
    assert user.roles == [Role.PURCHASE]
    assert user.hashed_password != PASSWORD
    assert Argon2PasswordHasher().verify(PASSWORD, user.hashed_password)
    assert tuple(audit) == ("sarath", "user.create", "buyer@email.com")


def test_creates_a_master_data_user(uow):
    dto = user_dto("Master@Email.com")
    dto.roles = ["master-data"]
    CreateUser(uow, Argon2PasswordHasher()).execute(dto)

    with uow:
        user = uow.user_repo.find_by_email(EmailID("master@email.com"))
    assert user.roles == [Role.MASTER_DATA]


def test_rejects_short_password(uow):
    with pytest.raises(WeakPassword):
        CreateUser(uow, Argon2PasswordHasher()).execute(user_dto(password="short"))


def test_rejects_duplicate_email(uow):
    usecase = CreateUser(uow, Argon2PasswordHasher())
    usecase.execute(user_dto())

    with pytest.raises(UserAlreadyExists):
        usecase.execute(user_dto(email="buyer@email.com"))


def test_rejects_unknown_role(uow):
    dto = user_dto()
    dto.roles = ["wizard"]

    with pytest.raises(ValueError):
        CreateUser(uow, Argon2PasswordHasher()).execute(dto)


def test_first_admin_is_created_once_only(uow):
    usecase = CreateFirstAdmin(uow, CreateUser(uow, Argon2PasswordHasher()))
    dto = CreateFirstAdminDTO("admin@email.com", "Admin", PASSWORD, "SAP_ADMIN", "sarath")

    usecase.execute(dto)

    with uow:
        assert uow.user_repo.find_by_email(EmailID("admin@email.com")).roles == [Role.ADMIN]
    dto.email_id = "second@email.com"
    with pytest.raises(AdminAlreadyExists):
        usecase.execute(dto)


def test_creates_user_with_the_given_companies(uow):
    dto = user_dto()
    dto.companies = ["organica", "organica", "sabinsa"]

    CreateUser(uow, Argon2PasswordHasher()).execute(dto)

    with uow:
        user = uow.user_repo.find_by_email(EmailID("buyer@email.com"))
    assert user.companies == [Company.ORGANICA, Company.SABINSA]


def test_rejects_unknown_company(uow):
    dto = user_dto()
    dto.companies = ["acme"]

    with pytest.raises(ValueError):
        CreateUser(uow, Argon2PasswordHasher()).execute(dto)
