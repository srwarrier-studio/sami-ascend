from auth_api.domain.value_objects.email_id import EmailID
from auth_api.domain.entities.user import User
from abc import ABC, abstractmethod
from token_verification import Company



class UserRepo(ABC):
    @abstractmethod
    def add(self, user: User) -> User: ...

    @abstractmethod
    def find_all(self) -> list[User]: ...

    @abstractmethod
    def find_by_email(self, email: EmailID) -> User | None: ...

    @abstractmethod
    def set_companies(self, user: User, companies: list[Company]) -> None: ...
