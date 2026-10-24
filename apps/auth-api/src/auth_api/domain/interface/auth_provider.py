from abc import ABC, abstractmethod


class AuthProvider(ABC):
    @abstractmethod
    def authenticate(self, **kwargs): ...