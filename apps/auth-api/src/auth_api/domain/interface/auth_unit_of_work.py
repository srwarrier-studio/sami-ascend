from auth_api.domain.repositories.user_repo import UserRepo
from abc import ABC, abstractmethod



class AuthUnitOfWork(ABC):
    user_repo: UserRepo

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.rollback()

    @abstractmethod
    def rollback(self) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...
