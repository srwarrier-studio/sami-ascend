import pytest
from token_verification import InvalidToken, TokenVerifier

from token_verification import Role
from auth_api.infrastructure.interface.jwt_token_service import JwtTokenService
from auth_api.infrastructure.mock.mock_user_repo import MOCK_USER


def test_issued_token_verifies_back_to_the_same_claims():
    service = JwtTokenService(secret="s" * 32, expire_minutes=5)

    claims = TokenVerifier("s" * 32).verify(service.issue(MOCK_USER))

    assert claims.userid == str(MOCK_USER.userid.value)
    assert claims.sap_username == "SAP_READONLY"
    assert claims.roles == [Role.STORES]


def test_expired_token_is_rejected():
    service = JwtTokenService(secret="s" * 32, expire_minutes=-1)

    with pytest.raises(InvalidToken):
        TokenVerifier("s" * 32).verify(service.issue(MOCK_USER))


def test_token_signed_with_another_secret_is_rejected():
    token = JwtTokenService(secret="a" * 32, expire_minutes=5).issue(MOCK_USER)

    with pytest.raises(InvalidToken):
        TokenVerifier("b" * 32).verify(token)
