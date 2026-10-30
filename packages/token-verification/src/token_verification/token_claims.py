from dataclasses import dataclass, field

from token_verification.company import Company
from token_verification.role import Role


@dataclass(frozen=True)
class TokenClaims:
    userid: str
    sap_username: str
    roles: list[Role]
    companies: list[Company] = field(default_factory=list)
