from abc import ABC, abstractmethod

from workspace_api.domain.entities.master_data import MaterialPage, PartnerPage, Plant


class MasterDataGateway(ABC):
    @abstractmethod
    def plants(self, plants: list[str]) -> list[Plant]: ...

    @abstractmethod
    def materials(self, query: str | None, plants: list[str], top: int, skip: int) -> MaterialPage: ...

    @abstractmethod
    def customers(self, query: str | None, companies: list[str], top: int, skip: int) -> PartnerPage: ...

    @abstractmethod
    def suppliers(self, query: str | None, companies: list[str], top: int, skip: int) -> PartnerPage: ...
