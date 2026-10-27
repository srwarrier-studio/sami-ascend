from token_verification import TokenVerifier
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE, AuthDependencies

from auth_api.core.config import settings
from auth_api.infrastructure.interface.jwt_token_service import JwtTokenService

token_service = JwtTokenService(settings.JWT_SECRET, settings.JWT_EXPIRE_MINUTES)

auth = AuthDependencies(TokenVerifier(settings.JWT_SECRET))
current_claims = auth.current_claims
require_role = auth.require_roles

__all__ = [
    "ACCESS_TOKEN_COOKIE",
    "current_claims",
    "require_role",
    "token_service",
]
