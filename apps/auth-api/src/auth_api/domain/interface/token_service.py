from abc import ABC, abstractmethod

from auth_api.domain.entities.user import User


class TokenService(ABC):
    @abstractmethod
    def issue(self, user: User) -> str: ...
