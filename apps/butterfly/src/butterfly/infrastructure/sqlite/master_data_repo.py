from dataclasses import fields

from butterfly.domain.entities.number_range import CUSTOMER
from butterfly.domain.entities.master_data import Customer, Material, Plant, Product, Supplier
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.infrastructure.memory.in_memory_master_data_repo import CURRENCIES
from butterfly.infrastructure.memory.master_lists import plants, products, suppliers
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.money import from_minor
from butterfly.infrastructure.sqlite.seeder import write_master_data


CUSTOMER_COLUMNS = [field.name for field in fields(Customer)]


def customer_from(row) -> Customer:
    return Customer(**{name: row[name] for name in CUSTOMER_COLUMNS})


class SqliteMasterDataRepo(MasterDataRepo):
    def __init__(self, db: Database | None = None):
        if db is None:
            db = Database()
            write_master_data(db)
        self.db = db

    def get_customer(self, customer_id: str) -> Customer | None:
        rows = self.db.query("SELECT * FROM customer WHERE customer_id = ?", (customer_id,))
        return customer_from(rows[0]) if rows else None

    def next_customer_number(self) -> str:
        return CUSTOMER.next(row["customer_id"] for row in self.db.query("SELECT customer_id FROM customer")).zfill(10)

    def add_customer(self, customer: Customer) -> None:
        names = ", ".join(CUSTOMER_COLUMNS)
        marks = ", ".join("?" for _ in CUSTOMER_COLUMNS)
        self.db.execute(f"INSERT INTO customer ({names}) VALUES ({marks})", tuple(getattr(customer, name) for name in CUSTOMER_COLUMNS))

    def get_material(self, material_id: str) -> Material | None:
        rows = self.db.query("SELECT * FROM material WHERE material_id = ?", (material_id,))
        row = rows[0] if rows else None
        return Material(row["material_id"], row["description"], row["unit"], from_minor(row["price"]), row["company_code"]) if row else None

    def company_exists(self, company_code: str) -> bool:
        return bool(self.db.query("SELECT 1 FROM company WHERE code = ?", (company_code,)))

    def currency_exists(self, currency: str) -> bool:
        return currency in CURRENCIES

    def list_customers(self) -> list[Customer]:
        rows = self.db.query("SELECT * FROM customer ORDER BY rowid")
        return [customer_from(row) for row in rows]

    def list_products(self) -> list[Product]:
        return products()

    def list_suppliers(self) -> list[Supplier]:
        return suppliers()

    def list_plants(self) -> list[Plant]:
        return plants()
