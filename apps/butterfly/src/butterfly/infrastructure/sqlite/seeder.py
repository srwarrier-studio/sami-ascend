from dataclasses import replace
from datetime import date

from butterfly.domain.entities.drivers import CustomerInvoice, ProductionOrder
from butterfly.domain.entities.exports import ExportShipment
from butterfly.domain.entities.finance import CashPayment
from butterfly.domain.entities.master_data import LOCAL_CURRENCY, to_local
from butterfly.domain.entities.sales_order import SalesOrder
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.export_seed import build_exports
from butterfly.infrastructure.memory.invoices import CUSTOMERS, build_invoices
from butterfly.infrastructure.memory.finance_seed import build_cash
from butterfly.infrastructure.memory.inventory_master import GROUP_OF, GROUPS, LOCATIONS
from butterfly.infrastructure.memory.inventory_seed import InventorySeed, build_inventory, items_of
from butterfly.infrastructure.memory.production_master import WORK_CENTERS
from butterfly.infrastructure.memory.production_seed import ProductionSeed, build_production
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.seed import build_seed
from butterfly.infrastructure.memory.story_seed import StorySeed, build_story_seed
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.mappers import item_from_row, order_from_row
from butterfly.infrastructure.sqlite.money import quantity_to_minor, to_minor
from butterfly.infrastructure.sqlite.schema import REPLACED_ON_RESEED

SEEDS = ("small", "story")
LAYOUT = "6"
DERIVED_TABLES = ["cash_payment", "export_shipment", "stock_value_month", "stock_movement", "material_stock", "customer_invoice"]


def iso(value) -> str | None:
    return None if value is None else value.isoformat()


def marks(count: int) -> str:
    return ", ".join("?" * count)


def settings_of(db: Database) -> dict[str, str]:
    return {row["key"]: row["value"] for row in db.query("SELECT key, value FROM meta")}


def prepare(db: Database, seed: str, scenario: str, today: date, story: StorySeed | None = None) -> bool:
    if seed not in SEEDS:
        raise ValueError(f"unknown seed {seed}")
    wanted = {"seed": seed, "scenario": scenario, "built_on": today.isoformat(), "layout": LAYOUT}
    if settings_of(db) == wanted:
        return False
    if seed == "story" and story is None:
        story = build_story_seed(today, find_scenario(scenario), COMPANIES)
    if seed == "small":
        story = None
    orders = story.orders if story else build_seed(today)
    with db.transaction():
        for table in REPLACED_ON_RESEED:
            db.execute(f"DELETE FROM {table}")
        db.execute("DELETE FROM sales_order WHERE origin = 'seed'")
        db.execute("DELETE FROM meta")
        write_master_data(db)
        write_orders(db, clear_of_api_numbers(db, orders))
        if story:
            write_drivers(db, story, with_invoices=False)
            write_production(db, build_production(story, COMPANIES, today))
            derive_documents(db, story, today)
        db.insert_many("INSERT INTO meta (key, value) VALUES (?, ?)", list(wanted.items()))
    return True


def write_master_data(db: Database) -> None:
    db.insert_many("INSERT INTO material_group (code, name) VALUES (?, ?)", [(group.code, group.name) for group in GROUPS])
    db.insert_many("INSERT INTO material_group_of (material, material_group) VALUES (?, ?)", list(GROUP_OF.items()))
    db.insert_many("INSERT INTO work_center (plant, code, name, company_code) VALUES (?, ?, ?, ?)", [(w.plant, w.code, w.name, w.company_code) for w in WORK_CENTERS])
    db.insert_many("INSERT INTO storage_location (plant, code, name, company_code) VALUES (?, ?, ?, ?)", [(l.plant, l.code, l.name, l.company_code) for l in LOCATIONS])
    db.insert_many("INSERT INTO company (code, name) VALUES (?, ?)", [(company.code, company.name) for company in COMPANIES])
    db.insert_many(
        "INSERT INTO customer (customer_id, name, country, company_code) VALUES (?, ?, ?, ?)",
        [(customer.customer_id, customer.name, customer.country, company.code) for company in COMPANIES for customer in company.customers],
    )
    db.insert_many(
        "INSERT INTO material (material_id, description, unit, price, company_code) VALUES (?, ?, ?, ?, ?)",
        [(material_id, description, unit, to_minor(price), company.code) for company in COMPANIES for material_id, description, unit, price in company.materials],
    )


def write_inventory(db: Database, inventory: InventorySeed) -> None:
    db.insert_many(
        f"INSERT INTO material_stock VALUES ({marks(12)})",
        [
            (s.material, s.material_description, s.material_group, s.plant, s.storage_location, quantity_to_minor(s.stock_quantity), s.quantity_unit, to_minor(s.stock_value),
             s.currency, quantity_to_minor(s.reorder_level), iso(s.last_movement_date), s.company_code)
            for s in inventory.stocks
        ],
    )
    db.insert_many(
        f"INSERT INTO stock_movement VALUES ({marks(16)})",
        [
            (m.material_document, m.material_document_item, m.material_document_year, iso(m.posting_date), m.entry_date_time.isoformat(), m.material, m.material_description,
             m.plant, m.storage_location, m.movement_type, m.debit_credit_code, quantity_to_minor(m.quantity), m.quantity_unit, to_minor(m.amount), m.currency, m.company_code)
            for m in inventory.movements
        ],
    )
    db.insert_many(
        f"INSERT INTO stock_value_month VALUES ({marks(4)})",
        [(v.posting_period, v.currency, v.company_code, to_minor(v.stock_value)) for v in inventory.monthly],
    )


def write_production(db: Database, production: ProductionSeed) -> None:
    db.insert_many(
        f"INSERT INTO production_confirmation VALUES ({marks(20)})",
        [
            (c.confirmation_number, c.confirmation_counter, c.production_order, c.material, c.material_description, c.plant, c.work_center, c.shift, iso(c.posting_date),
             quantity_to_minor(c.yield_quantity), quantity_to_minor(c.scrap_quantity), quantity_to_minor(c.target_quantity), c.quantity_unit, c.scrap_reason, to_minor(c.run_hours),
             to_minor(c.yield_value), to_minor(c.scrap_value), to_minor(c.target_value), c.currency, c.company_code)
            for c in production.confirmations
        ],
    )
    db.insert_many(
        f"INSERT INTO work_center_downtime VALUES ({marks(8)})",
        [(d.downtime_number, d.production_order, d.plant, d.work_center, iso(d.posting_date), to_minor(d.downtime_hours), d.downtime_cause, d.company_code) for d in production.downtimes],
    )


def write_cash(db: Database, payments: list[CashPayment]) -> None:
    db.insert_many(
        f"INSERT INTO cash_payment VALUES ({marks(13)})",
        [
            (p.payment_document, iso(p.posting_date), p.direction, p.payment_type, p.partner, p.partner_name, p.expense_category, p.reference, to_minor(p.amount), p.currency,
             to_minor(p.document_amount), p.document_currency, p.company_code)
            for p in payments
        ],
    )


def write_exports(db: Database, shipments: list[ExportShipment]) -> None:
    db.insert_many(
        f"INSERT INTO export_shipment VALUES ({marks(16)})",
        [
            (s.shipment, s.sales_order, s.sold_to_party, s.customer_name, s.country, s.country_name, s.transport_mode, iso(s.shipment_date), iso(s.expected_arrival_date),
             iso(s.actual_arrival_date), s.shipment_status, to_minor(s.net_amount), s.currency, to_minor(s.document_amount), s.document_currency, s.company_code)
            for s in shipments
        ],
    )


def write_orders(db: Database, orders: list[SalesOrder], origin: str = "seed") -> None:
    db.insert_many(
        f"INSERT INTO sales_order (sales_order, sales_order_type, sold_to_party, customer_name, order_date, requested_delivery_date, transaction_currency, "
        f"total_net_amount, overall_status, created_by_user, creation_date_time, last_change_date_time, company_code, country, origin, total_net_amount_local, local_currency) VALUES ({marks(17)})",
        [
            (
                o.sales_order, o.sales_order_type, o.sold_to_party, o.customer_name, iso(o.order_date), iso(o.requested_delivery_date), o.transaction_currency,
                to_minor(o.total_net_amount), o.overall_status, o.created_by_user, iso(o.creation_date_time), iso(o.last_change_date_time), o.company_code, o.country, origin, to_minor(o.total_net_amount_local), o.local_currency,
            )
            for o in orders
        ],
    )
    db.insert_many(
        f"INSERT INTO sales_order_item (sales_order, sales_order_item, material, material_description, quantity, quantity_unit, net_amount, net_amount_local) VALUES ({marks(8)})",
        [
            (i.sales_order, i.sales_order_item, i.material, i.material_description, quantity_to_minor(i.quantity), i.quantity_unit, to_minor(i.net_amount), to_minor(to_local(i.net_amount, o.transaction_currency)))
            for o in orders
            for i in o.items
        ],
    )


def write_invoices(db: Database, invoices: list[CustomerInvoice]) -> None:
    db.insert_many(
        f"INSERT INTO customer_invoice VALUES ({marks(13)})",
        [
            (i.invoice, i.sold_to_party, i.customer_name, iso(i.invoice_date), iso(i.due_date), to_minor(i.net_amount), i.transaction_currency, to_minor(i.cleared_amount), iso(i.clearing_date),
             i.company_code, i.country, to_minor(i.net_amount_local), to_minor(i.cleared_amount_local))
            for i in invoices
        ],
    )


def stored_orders(db: Database) -> list[SalesOrder]:
    items: dict[str, list] = {}
    for row in db.query("SELECT * FROM sales_order_item ORDER BY rowid"):
        items.setdefault(row["sales_order"], []).append(item_from_row(row))
    return [order_from_row(row, items.get(row["sales_order"], [])) for row in db.query("SELECT * FROM sales_order ORDER BY rowid")]


def clear_of_api_numbers(db: Database, orders: list[SalesOrder]) -> list[SalesOrder]:
    taken = {int(row["sales_order"]) for row in db.query("SELECT sales_order FROM sales_order WHERE origin = 'api'")}
    if not taken or taken.isdisjoint(int(order.sales_order) for order in orders):
        return orders
    spare = max(taken | {int(order.sales_order) for order in orders})
    moved = []
    for order in orders:
        if int(order.sales_order) in taken:
            spare += 1
            number = f"{spare:010d}"
            order = replace(order, sales_order=number, items=[replace(item, sales_order=number) for item in order.items])
        moved.append(order)
    return moved


def derive_documents(db: Database, story: StorySeed, today: date) -> None:
    known = items_of(COMPANIES)
    orders = [o for o in stored_orders(db) if o.sold_to_party in CUSTOMERS and all(i.material in known for i in o.items)]
    documents = replace(story, orders=orders, invoices=build_invoices(orders, today))
    for table in DERIVED_TABLES:
        db.execute(f"DELETE FROM {table}")
    write_invoices(db, documents.invoices)
    write_inventory(db, build_inventory(documents, COMPANIES, today))
    write_exports(db, build_exports(documents, today))
    write_cash(db, build_cash(documents.invoices, documents.deliveries, today))


def write_drivers(db: Database, story: StorySeed, with_invoices: bool = True) -> None:
    db.insert_many(
        f"INSERT INTO sales_contract VALUES ({marks(10)})",
        [(c.sales_contract, c.predecessor_contract, c.sold_to_party, c.customer_name, iso(c.valid_from), iso(c.valid_to), to_minor(c.contract_value), c.transaction_currency, c.contract_status, c.company_code) for c in story.contracts],
    )
    db.insert_many(
        f"INSERT INTO purchase_delivery VALUES ({marks(18)})",
        [
            (
                d.purchase_order, d.purchase_order_item, d.supplier, d.supplier_name, d.material, d.material_description, iso(d.order_date), quantity_to_minor(d.ordered_quantity),
                quantity_to_minor(d.delivered_quantity), d.quantity_unit, iso(d.promised_delivery_date), iso(d.actual_delivery_date), d.delivery_status, to_minor(d.net_amount),
                d.transaction_currency, d.company_code, to_minor(d.net_amount_local), d.local_currency,
            )
            for d in story.deliveries
        ],
    )
    if with_invoices:
        write_invoices(db, story.invoices)
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
