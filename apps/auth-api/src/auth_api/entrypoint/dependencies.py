from typing import Annotated

from fastapi import Depends, HTTPException, Request

from auth_api.core.config import settings
from auth_api.domain.errors import InvalidToken
from auth_api.domain.value_objects.role import Role
from auth_api.domain.value_objects.token_claims import TokenClaims
from auth_api.infrastructure.interface.jwt_token_service import JwtTokenService

ACCESS_TOKEN_COOKIE = "access_token"

token_service = JwtTokenService(settings.JWT_SECRET, settings.JWT_EXPIRE_MINUTES)


def current_claims(request: Request) -> TokenClaims:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if token is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    try:
        return token_service.verify(token)
    except InvalidToken:
        raise HTTPException(status_code=401, detail="Session expired, please log in again")


def require_role(*allowed_roles: Role):
    def check(claims: Annotated[TokenClaims, Depends(current_claims)]) -> TokenClaims:
        if not set(allowed_roles) & set(claims.roles):
            raise HTTPException(
                status_code=403, detail="You are not allowed to view this page"
            )
        return claims

    return check
