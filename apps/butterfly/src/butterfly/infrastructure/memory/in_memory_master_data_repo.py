from butterfly.domain.entities.master_data import Customer, Material
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.infrastructure.memory.seed import CUSTOMERS, MATERIALS

CURRENCIES = {"INR"}
COMPANIES = {"INA1", "INA2", "INA3"}


class InMemoryMasterDataRepo(MasterDataRepo):
    def __init__(self):
        self.customers = {cid: Customer(cid, name) for cid, name in CUSTOMERS}
        self.materials = {
            mid: Material(mid, description, unit, price)
            for mid, description, unit, price in MATERIALS
        }

    def get_customer(self, customer_id: str) -> Customer | None:
        return self.customers.get(customer_id)

    def get_material(self, material_id: str) -> Material | None:
        return self.materials.get(material_id)

    def company_exists(self, company_code: str) -> bool:
        return company_code in COMPANIES

    def currency_exists(self, currency: str) -> bool:
        return currency in CURRENCIES
