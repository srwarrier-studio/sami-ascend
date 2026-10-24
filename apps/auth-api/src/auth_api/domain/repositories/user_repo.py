from auth_api.domain.value_objects.email_id import EmailID
from auth_api.domain.entities.user import User
from abc import ABC, abstractmethod



class UserRepo(ABC):
    @abstractmethod
    def add(self, user: User) -> User: ...

    @abstractmethod
    def find_all(self) -> list[User]: ...

    @abstractmethod
    def find_by_email(self, email: EmailID) -> User | None: ...