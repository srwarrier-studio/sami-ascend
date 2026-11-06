from butterfly.domain.entities.number_range import CUSTOMER
from butterfly.domain.entities.master_data import Customer, Material, Plant, Product, Supplier
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.master_lists import plants, products, suppliers

CURRENCIES = {"INR", "USD"}
COMPANY_CODES = {company.code for company in COMPANIES}


class InMemoryMasterDataRepo(MasterDataRepo):
    def __init__(self):
        self.customers = {
            customer.customer_id: Customer(customer.customer_id, customer.name, customer.country, company.code)
            for company in COMPANIES
            for customer in company.customers
        }
        self.materials = {
            material_id: Material(material_id, description, unit, price, company.code)
            for company in COMPANIES
            for material_id, description, unit, price in company.materials
        }

    def get_customer(self, customer_id: str) -> Customer | None:
        return self.customers.get(customer_id)

    def next_customer_number(self) -> str:
        return CUSTOMER.next(self.customers).zfill(10)

    def add_customer(self, customer: Customer) -> None:
        self.customers[customer.customer_id] = customer

    def get_material(self, material_id: str) -> Material | None:
        return self.materials.get(material_id)

    def company_exists(self, company_code: str) -> bool:
        return company_code in COMPANY_CODES

    def currency_exists(self, currency: str) -> bool:
        return currency in CURRENCIES

    def list_customers(self) -> list[Customer]:
        return list(self.customers.values())

    def list_products(self) -> list[Product]:
        return products()

    def list_suppliers(self) -> list[Supplier]:
        return suppliers()

    def list_plants(self) -> list[Plant]:
        return plants()
