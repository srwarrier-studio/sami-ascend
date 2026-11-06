from abc import ABC, abstractmethod

from butterfly.domain.entities.master_data import Customer, Material, Plant, Product, Supplier


class MasterDataRepo(ABC):
    @abstractmethod
    def get_customer(self, customer_id: str) -> Customer | None: ...

    @abstractmethod
    def next_customer_number(self) -> str: ...

    @abstractmethod
    def add_customer(self, customer: Customer) -> None: ...

    @abstractmethod
    def get_material(self, material_id: str) -> Material | None: ...

    @abstractmethod
    def company_exists(self, company_code: str) -> bool: ...

    @abstractmethod
    def currency_exists(self, currency: str) -> bool: ...

    @abstractmethod
    def list_customers(self) -> list[Customer]: ...

    @abstractmethod
    def list_products(self) -> list[Product]: ...

    @abstractmethod
    def list_suppliers(self) -> list[Supplier]: ...

    @abstractmethod
    def list_plants(self) -> list[Plant]: ...
