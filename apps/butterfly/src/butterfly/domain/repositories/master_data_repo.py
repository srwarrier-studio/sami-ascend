from abc import ABC, abstractmethod

from butterfly.domain.entities.master_data import Customer, Material


class MasterDataRepo(ABC):
    @abstractmethod
    def get_customer(self, customer_id: str) -> Customer | None: ...

    @abstractmethod
    def get_material(self, material_id: str) -> Material | None: ...

    @abstractmethod
    def currency_exists(self, currency: str) -> bool: ...
