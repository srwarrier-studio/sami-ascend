from abc import ABC, abstractmethod
from datetime import datetime

from workspace_api.domain.entities.order_request import OrderRequest


class OrderRequestStore(ABC):
    @abstractmethod
    def add(self, request: OrderRequest) -> None: ...

    @abstractmethod
    def claim_due(self, now: datetime) -> OrderRequest | None: ...

    @abstractmethod
    def update(self, request_id: str, **changes) -> None: ...

    @abstractmethod
    def recover_sending(self) -> int: ...

    @abstractmethod
    def get(self, request_id: str, user: str) -> OrderRequest | None: ...

    @abstractmethod
    def list_open(self, user: str, limit: int) -> list[OrderRequest]: ...
