import pytest

from auth_api.application.dto.login_dto import LoginWithEntraDTO, LoginWithPasswordDTO
from auth_api.application.usecase.login_with_entra import LoginWithEntra
from auth_api.application.usecase.login_with_password import LoginWithPassword
from auth_api.domain.errors import InvalidCredentials
from auth_api.infrastructure.interface.argon2_password_hasher import Argon2PasswordHasher
from token_verification import TokenVerifier

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
