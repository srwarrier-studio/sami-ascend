import pytest

from auth_api.domain.errors import InvalidToken
from auth_api.domain.value_objects.role import Role
from auth_api.infrastructure.interface.jwt_token_service import JwtTokenService
from auth_api.infrastructure.mock.mock_user_repo import MOCK_USER


def test_issued_token_verifies_back_to_the_same_claims():
    service = JwtTokenService(secret="s" * 32, expire_minutes=5)

    claims = service.verify(service.issue(MOCK_USER))

    assert claims.userid == str(MOCK_USER.userid.value)
    assert claims.sap_username == "SAP_READONLY"
    assert claims.roles == [Role.STORES]


def test_expired_token_is_rejected():
    service = JwtTokenService(secret="s" * 32, expire_minutes=-1)

    with pytest.raises(InvalidToken):
        service.verify(service.issue(MOCK_USER))


def test_token_signed_with_another_secret_is_rejected():
    token = JwtTokenService(secret="a" * 32, expire_minutes=5).issue(MOCK_USER)

    with pytest.raises(InvalidToken):
        JwtTokenService(secret="b" * 32, expire_minutes=5).verify(token)
