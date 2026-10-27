from typing import Annotated

from fastapi import Depends, HTTPException, Request

from token_verification.errors import InvalidToken
from token_verification.role import Role
from token_verification.token_claims import TokenClaims
from token_verification.token_verifier import TokenVerifier

ACCESS_TOKEN_COOKIE = "access_token"


class AuthDependencies:
    def __init__(self, verifier: TokenVerifier):
        self.verifier = verifier

    def current_claims(self, request: Request) -> TokenClaims:
        token = request.cookies.get(ACCESS_TOKEN_COOKIE)
        if token is None:
            raise HTTPException(status_code=401, detail="Not logged in")
        try:
            return self.verifier.verify(token)
        except InvalidToken:
            raise HTTPException(
                status_code=401, detail="Session expired, please log in again"
            )

    def require_roles(self, *allowed_roles: Role):
        def check(
            claims: Annotated[TokenClaims, Depends(self.current_claims)],
        ) -> TokenClaims:
            if not set(allowed_roles) & set(claims.roles):
                raise HTTPException(
                    status_code=403, detail="You are not allowed to view this page"
                )
            return claims

        return check
