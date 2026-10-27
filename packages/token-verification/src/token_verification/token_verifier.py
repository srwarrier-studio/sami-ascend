import jwt

from token_verification.errors import InvalidToken
from token_verification.role import Role
from token_verification.token_claims import TokenClaims

ALGORITHM = "HS256"


class TokenVerifier:
    def __init__(self, secret: str):
        self.secret = secret

    def verify(self, token: str) -> TokenClaims:
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[ALGORITHM],
                options={"require": ["exp", "sub", "sap_username", "roles"]},
            )
            return TokenClaims(
                userid=payload["sub"],
                sap_username=payload["sap_username"],
                roles=[Role(role) for role in payload["roles"]],
            )
        except (jwt.InvalidTokenError, ValueError, TypeError):
            raise InvalidToken()
