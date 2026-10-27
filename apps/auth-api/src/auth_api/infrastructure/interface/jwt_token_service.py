from datetime import datetime, timedelta, timezone

import jwt
from token_verification.token_verifier import ALGORITHM

from auth_api.domain.entities.user import User
from auth_api.domain.interface.token_service import TokenService


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
