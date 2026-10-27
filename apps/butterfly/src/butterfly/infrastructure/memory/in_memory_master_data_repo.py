from butterfly.domain.entities.master_data import Customer, Material
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.infrastructure.memory.seed import CUSTOMERS, MATERIALS

CURRENCIES = {"INR"}


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

    def currency_exists(self, currency: str) -> bool:
        return currency in CURRENCIES
