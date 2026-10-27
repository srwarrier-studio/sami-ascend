from abc import ABC, abstractmethod

from auth_api.domain.entities.user import User
from auth_api.domain.value_objects.token_claims import TokenClaims


class TokenService(ABC):
    @abstractmethod
    def issue(self, user: User) -> str: ...

    @abstractmethod
    def verify(self, token: str) -> TokenClaims: ...
