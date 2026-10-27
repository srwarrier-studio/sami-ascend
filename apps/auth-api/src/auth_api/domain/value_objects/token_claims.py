from dataclasses import dataclass

from auth_api.domain.value_objects.role import Role


@dataclass(frozen=True)
class TokenClaims:
    userid: str
    sap_username: str
    roles: list[Role]
