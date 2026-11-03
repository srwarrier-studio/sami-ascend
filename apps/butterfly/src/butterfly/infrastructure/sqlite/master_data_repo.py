from butterfly.domain.entities.master_data import Customer, Material
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.infrastructure.memory.in_memory_master_data_repo import CURRENCIES
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.money import from_minor
from butterfly.infrastructure.sqlite.seeder import write_master_data


class SqliteMasterDataRepo(MasterDataRepo):
    def __init__(self, db: Database | None = None):
        if db is None:
            db = Database()
            write_master_data(db)
        self.db = db

    def get_customer(self, customer_id: str) -> Customer | None:
        rows = self.db.query("SELECT * FROM customer WHERE customer_id = ?", (customer_id,))
        return Customer(rows[0]["customer_id"], rows[0]["name"], rows[0]["country"], rows[0]["company_code"]) if rows else None

    def get_material(self, material_id: str) -> Material | None:
        rows = self.db.query("SELECT * FROM material WHERE material_id = ?", (material_id,))
        row = rows[0] if rows else None
        return Material(row["material_id"], row["description"], row["unit"], from_minor(row["price"]), row["company_code"]) if row else None

    def company_exists(self, company_code: str) -> bool:
        return bool(self.db.query("SELECT 1 FROM company WHERE code = ?", (company_code,)))

    def currency_exists(self, currency: str) -> bool:
        return currency in CURRENCIES
