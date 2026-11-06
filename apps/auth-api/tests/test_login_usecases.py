import pytest

from auth_api.application.dto.login_dto import LoginWithEntraDTO, LoginWithPasswordDTO
from auth_api.application.usecase.login_with_entra import LoginWithEntra
from auth_api.application.usecase.login_with_password import LoginWithPassword
from auth_api.domain.errors import InvalidCredentials
from auth_api.infrastructure.interface.argon2_password_hasher import Argon2PasswordHasher
from token_verification import Role, TokenVerifier

from auth_api.infrastructure.interface.jwt_token_service import JwtTokenService
from auth_api.infrastructure.mock.mock_unit_of_work import MockAuthUnitOfWork
from auth_api.infrastructure.mock.mock_user_repo import MOCK_USER

token_service = JwtTokenService(secret="s" * 32, expire_minutes=5)
verifier = TokenVerifier("s" * 32)


def password_login():
    return LoginWithPassword(MockAuthUnitOfWork(), Argon2PasswordHasher(), token_service)


def test_password_login_returns_token_for_the_user():
    token = password_login().execute(LoginWithPasswordDTO("Test@Email.com", "password"))

    assert verifier.verify(token).userid == str(MOCK_USER.userid.value)


@pytest.mark.parametrize(
    "email, password",
    [("test@email.com", "wrong"), ("nobody@email.com", "password"), ("not-an-email", "password")],
)
def test_password_login_rejects_bad_credentials(email, password):
    with pytest.raises(InvalidCredentials):
        password_login().execute(LoginWithPasswordDTO(email, password))


def test_password_login_rejects_disabled_user():
    uow = MockAuthUnitOfWork()
    MOCK_USER.disabled = True
    try:
        with pytest.raises(InvalidCredentials):
            LoginWithPassword(uow, Argon2PasswordHasher(), token_service).execute(
                LoginWithPasswordDTO("test@email.com", "password")
            )
    finally:
        MOCK_USER.disabled = False


def test_entra_login_returns_token_for_registered_user():
    token = LoginWithEntra(MockAuthUnitOfWork(), token_service).execute(
        LoginWithEntraDTO("Test@Email.com")
    )

    assert verifier.verify(token).userid == str(MOCK_USER.userid.value)


def test_entra_login_rejects_unregistered_user():
    with pytest.raises(InvalidCredentials):
        LoginWithEntra(MockAuthUnitOfWork(), token_service).execute(
            LoginWithEntraDTO("nobody@email.com")
        )


def events_of(uow):
    return [(event.actor, event.action, event.outcome, event.detail) for event in uow.events]


def test_good_password_login_is_audited():
    uow = MockAuthUnitOfWork()
    LoginWithPassword(uow, Argon2PasswordHasher(), token_service).execute(LoginWithPasswordDTO("Test@Email.com", "password"))

    assert events_of(uow) == [("test@email.com", "login.password", "success", "")]


@pytest.mark.parametrize(
    "email, password, detail",
    [("test@email.com", "wrong", "bad_password"), ("nobody@email.com", "password", "unknown_user"), ("not-an-email", "password", "bad_email")],
)
def test_failed_password_login_is_audited_with_its_reason(email, password, detail):
    uow = MockAuthUnitOfWork()
    with pytest.raises(InvalidCredentials):
        LoginWithPassword(uow, Argon2PasswordHasher(), token_service).execute(LoginWithPasswordDTO(email, password))

    assert events_of(uow) == [(email, "login.password", "failed", detail)]


def test_entra_outcomes_are_audited():
    uow = MockAuthUnitOfWork()
    LoginWithEntra(uow, token_service).execute(LoginWithEntraDTO("test@email.com"))
    with pytest.raises(InvalidCredentials):
        LoginWithEntra(uow, token_service).execute(LoginWithEntraDTO("nobody@email.com"))

    assert events_of(uow) == [
        ("test@email.com", "login.entra", "success", ""),
        ("nobody@email.com", "login.entra", "failed", "no_entra_match"),
    ]


def test_a_failed_audit_write_does_not_change_the_login():
    class BrokenAudit(MockAuthUnitOfWork):
        def __enter__(self):
            super().__enter__()
            self.audit_repo = None
            return self

    token = LoginWithPassword(BrokenAudit(), Argon2PasswordHasher(), token_service).execute(LoginWithPasswordDTO("test@email.com", "password"))

    assert verifier.verify(token).userid == str(MOCK_USER.userid.value)


def test_the_caller_cannot_tell_an_unknown_email_from_a_bad_password():
    errors = []
    for email, password in [("nobody@email.com", "password"), ("test@email.com", "wrong")]:
        with pytest.raises(InvalidCredentials) as caught:
            password_login().execute(LoginWithPasswordDTO(email, password))
        errors.append(str(caught.value))

    assert errors[0] == errors[1]


def test_the_token_of_a_master_data_user_carries_the_role():
    user = MOCK_USER.__class__(**{**MOCK_USER.__dict__, "roles": [Role.MASTER_DATA]})

    assert verifier.verify(token_service.issue(user)).roles == [Role.MASTER_DATA]
