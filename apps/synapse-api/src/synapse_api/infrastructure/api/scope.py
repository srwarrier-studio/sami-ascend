from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from token_verification import Company, Role
from token_verification.fastapi_deps import AuthDependencies
from token_verification.token_claims import TokenClaims

from synapse_api.domain.errors import CompanyNotAllowed, InvalidQuery

ALL = "all"


def company_scope(auth: AuthDependencies) -> Callable[..., tuple[str, ...]]:
    management = Depends(auth.require_roles(Role.MANAGEMENT, Role.ADMIN))

    def scope(claims: Annotated[TokenClaims, management], company: str = ALL) -> tuple[str, ...]:
        own = sorted(c.code for c in claims.companies)
        if company == ALL:
            if not own:
                raise CompanyNotAllowed(ALL)
            return tuple(own)
        try:
            code = Company(company).code
        except ValueError:
            raise InvalidQuery(f"company must be {ALL} or one of {', '.join(c.value for c in Company)}") from None
        if code not in own:
            raise CompanyNotAllowed(company)
        return (code,)

    return scope
