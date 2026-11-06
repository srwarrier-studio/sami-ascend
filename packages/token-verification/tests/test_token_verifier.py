from datetime import datetime, timedelta, timezone

import jwt
import pytest

from token_verification import Company, InvalidToken, Role, TokenVerifier

SECRET = "s" * 32


def make_token(secret=SECRET, algorithm="HS256", minutes=5, **overrides):
    payload = {
        "sub": "user-1",
        "sap_username": "SAP_READONLY",
        "roles": ["stores"],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes),
    }
    payload.update(overrides)
    payload = {key: value for key, value in payload.items() if value is not None}
    return jwt.encode(payload, secret, algorithm=algorithm)


def test_valid_token_returns_claims():
    claims = TokenVerifier(SECRET).verify(make_token())

    assert claims.userid == "user-1"
    assert claims.sap_username == "SAP_READONLY"
    assert claims.roles == [Role.STORES]


def test_master_data_role_is_returned():
    claims = TokenVerifier(SECRET).verify(make_token(roles=["master-data"]))

    assert claims.roles == [Role.MASTER_DATA]


def test_companies_are_returned():
    claims = TokenVerifier(SECRET).verify(make_token(companies=["organica", "sabinsa"]))

    assert claims.companies == [Company.ORGANICA, Company.SABINSA]


def test_token_without_companies_has_none():
    assert TokenVerifier(SECRET).verify(make_token()).companies == []


def test_unknown_company_is_rejected():
    with pytest.raises(InvalidToken):
        TokenVerifier(SECRET).verify(make_token(companies=["acme"]))


def test_wrong_secret_is_rejected():
    with pytest.raises(InvalidToken):
        TokenVerifier("x" * 32).verify(make_token())


def test_expired_token_is_rejected():
    with pytest.raises(InvalidToken):
        TokenVerifier(SECRET).verify(make_token(minutes=-1))


def test_garbage_is_rejected():
    with pytest.raises(InvalidToken):
        TokenVerifier(SECRET).verify("not-a-token")


def test_missing_roles_is_rejected():
    with pytest.raises(InvalidToken):
        TokenVerifier(SECRET).verify(make_token(roles=None))


def test_unknown_role_is_rejected():
    with pytest.raises(InvalidToken):
        TokenVerifier(SECRET).verify(make_token(roles=["wizard"]))


def test_other_algorithm_is_rejected():
    with pytest.raises(InvalidToken):
        TokenVerifier(SECRET).verify(make_token(secret=SECRET * 2, algorithm="HS512"))


def test_alg_none_is_rejected():
    token = jwt.encode({"sub": "u", "sap_username": "S", "roles": []}, None, algorithm="none")

    with pytest.raises(InvalidToken):
        TokenVerifier(SECRET).verify(token)
