from datetime import date

from butterfly.domain.entities.drivers import ProductionOrder
from butterfly.domain.entities.sales_order import SalesOrder
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.seed import build_seed
from butterfly.infrastructure.memory.story_seed import StorySeed, build_story_seed
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.money import quantity_to_minor, to_minor
from butterfly.infrastructure.sqlite.schema import REPLACED_ON_RESEED

SEEDS = ("small", "story")


def iso(value) -> str | None:
    return None if value is None else value.isoformat()


def marks(count: int) -> str:
    return ", ".join("?" * count)


def settings_of(db: Database) -> dict[str, str]:
    return {row["key"]: row["value"] for row in db.query("SELECT key, value FROM meta")}


def prepare(db: Database, seed: str, scenario: str, today: date) -> bool:
    if seed not in SEEDS:
        raise ValueError(f"unknown seed {seed}")
    wanted = {"seed": seed, "scenario": scenario, "built_on": today.isoformat()}
    if settings_of(db) == wanted:
        return False
    story = build_story_seed(today, find_scenario(scenario), COMPANIES) if seed == "story" else None
    orders = story.orders if story else build_seed(today)
    with db.transaction():
        for table in REPLACED_ON_RESEED:
            db.execute(f"DELETE FROM {table}")
        db.execute("DELETE FROM sales_order WHERE origin = 'seed'")
        db.execute("DELETE FROM meta")
        write_master_data(db)
        write_orders(db, orders)
        if story:
            write_drivers(db, story)
        db.insert_many("INSERT INTO meta (key, value) VALUES (?, ?)", list(wanted.items()))
    return True


def write_master_data(db: Database) -> None:
    db.insert_many("INSERT INTO company (code, name) VALUES (?, ?)", [(company.code, company.name) for company in COMPANIES])
    db.insert_many(
        "INSERT INTO customer (customer_id, name, country, company_code) VALUES (?, ?, ?, ?)",
        [(customer.customer_id, customer.name, customer.country, company.code) for company in COMPANIES for customer in company.customers],
    )
    db.insert_many(
        "INSERT INTO material (material_id, description, unit, price, company_code) VALUES (?, ?, ?, ?, ?)",
        [(material_id, description, unit, to_minor(price), company.code) for company in COMPANIES for material_id, description, unit, price in company.materials],
    )


def write_orders(db: Database, orders: list[SalesOrder]) -> None:
    db.insert_many(
        f"INSERT INTO sales_order (sales_order, sales_order_type, sold_to_party, customer_name, order_date, requested_delivery_date, transaction_currency, "
        f"total_net_amount, overall_status, created_by_user, creation_date_time, last_change_date_time, company_code, country, origin) VALUES ({marks(15)})",
        [
            (
                o.sales_order, o.sales_order_type, o.sold_to_party, o.customer_name, iso(o.order_date), iso(o.requested_delivery_date), o.transaction_currency,
                to_minor(o.total_net_amount), o.overall_status, o.created_by_user, iso(o.creation_date_time), iso(o.last_change_date_time), o.company_code, o.country, "seed",
            )
            for o in orders
        ],
    )
    db.insert_many(
        f"INSERT INTO sales_order_item (sales_order, sales_order_item, material, material_description, quantity, quantity_unit, net_amount) VALUES ({marks(7)})",
        [
            (i.sales_order, i.sales_order_item, i.material, i.material_description, quantity_to_minor(i.quantity), i.quantity_unit, to_minor(i.net_amount))
            for o in orders
            for i in o.items
        ],
    )


def write_drivers(db: Database, story: StorySeed) -> None:
    db.insert_many(
        f"INSERT INTO sales_contract VALUES ({marks(10)})",
        [(c.sales_contract, c.predecessor_contract, c.sold_to_party, c.customer_name, iso(c.valid_from), iso(c.valid_to), to_minor(c.contract_value), c.transaction_currency, c.contract_status, c.company_code) for c in story.contracts],
    )
    db.insert_many(
        f"INSERT INTO purchase_delivery VALUES ({marks(16)})",
        [
            (
                d.purchase_order, d.purchase_order_item, d.supplier, d.supplier_name, d.material, d.material_description, iso(d.order_date), quantity_to_minor(d.ordered_quantity),
                quantity_to_minor(d.delivered_quantity), d.quantity_unit, iso(d.promised_delivery_date), iso(d.actual_delivery_date), d.delivery_status, to_minor(d.net_amount),
                d.transaction_currency, d.company_code,
            )
            for d in story.deliveries
        ],
    )
    db.insert_many(
        f"INSERT INTO customer_invoice VALUES ({marks(11)})",
        [(i.invoice, i.sold_to_party, i.customer_name, iso(i.invoice_date), iso(i.due_date), to_minor(i.net_amount), i.transaction_currency, to_minor(i.cleared_amount), iso(i.clearing_date), i.company_code, i.country) for i in story.invoices],
    )
    db.insert_many(f"INSERT INTO production_order VALUES ({marks(12)})", [production_row(p) for p in story.production_orders])
    db.insert_many(
        f"INSERT INTO production_order_component VALUES ({marks(6)})",
        [(c.production_order, c.material, c.material_description, quantity_to_minor(c.required_quantity), c.quantity_unit, c.company_code) for c in story.components],
    )


def production_row(p: ProductionOrder) -> tuple:
    return (
        p.production_order, p.material, p.material_description, quantity_to_minor(p.planned_quantity), quantity_to_minor(p.confirmed_quantity), p.quantity_unit,
        iso(p.planned_start_date), iso(p.planned_end_date), iso(p.actual_end_date), p.production_status, p.delay_reason, p.company_code,
    )
