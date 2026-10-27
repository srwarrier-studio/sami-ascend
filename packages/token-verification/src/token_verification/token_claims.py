from dataclasses import dataclass

from token_verification.role import Role


@dataclass(frozen=True)
class TokenClaims:
    userid: str
    sap_username: str
    roles: list[Role]
