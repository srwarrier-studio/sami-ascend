from datetime import datetime, timedelta, timezone

import jwt

from auth_api.domain.entities.user import User
from auth_api.domain.errors import InvalidToken
from auth_api.domain.interface.token_service import TokenService
from auth_api.domain.value_objects.role import Role
from auth_api.domain.value_objects.token_claims import TokenClaims

ALGORITHM = "HS256"


class JwtTokenService(TokenService):
    def __init__(self, secret: str, expire_minutes: int):
        self.secret = secret
        self.expire_minutes = expire_minutes

    def issue(self, user: User) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        payload = {
            "sub": str(user.userid.value),
            "sap_username": user.sap_username,
            "roles": [role.value for role in user.roles],
            "exp": expires_at,
        }
        return jwt.encode(payload, self.secret, algorithm=ALGORITHM)

    def verify(self, token: str) -> TokenClaims:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[ALGORITHM])
        except jwt.InvalidTokenError:
            raise InvalidToken()
        return TokenClaims(
            userid=payload["sub"],
            sap_username=payload["sap_username"],
            roles=[Role(role) for role in payload["roles"]],
        )
