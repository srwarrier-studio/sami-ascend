import sqlite3
from collections.abc import Callable
from datetime import date

from butterfly.domain.entities.inventory import (
    StockMovementSummaryByDay,
    StockMovementSummaryByHour,
    StockSummaryByMaterialGroup,
    StockSummaryByStatus,
    StockSummaryByWarehouse,
    StockValueMonth,
)
from butterfly.domain.entities.sales_summary import (
    PurchaseSummaryByDay,
    PurchaseSummaryByMaterialGroup,
    PurchaseSummaryBySupplier,
    PurchaseSummaryByMaterial,
    ReceivablesAgeing,
    ReceivablesByCustomer,
    ReceivablesSummary,
    SalesSummaryByCustomer,
    SalesSummaryByDay,
    SalesSummaryByMaterial,
)
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.mappers import day
from butterfly.infrastructure.sqlite.money import MONEY_SCALE, QUANTITY_SCALE, from_minor, quantity_from_minor
from butterfly.infrastructure.sqlite.table import SqliteTable
from butterfly.infrastructure.sqlite.views import query

MONEY = {"total_net_amount": MONEY_SCALE}
MONEY_AND_QUANTITY = {"total_net_amount": MONEY_SCALE, "total_quantity": QUANTITY_SCALE}
OPEN = {"open_amount": MONEY_SCALE, "overdue_amount": MONEY_SCALE}
AGEING = {"open_amount": MONEY_SCALE}

BY_DAY = "order_date, currency, company_code"
BY_CUSTOMER = "order_date, sold_to_party, currency, company_code"
BY_SUPPLIER = "order_date, supplier, currency, company_code"
BY_MATERIAL = "order_date, material, currency, company_code"
BUCKET_ORDER = "CASE age_bucket WHEN 'current' THEN 0 WHEN '1-30' THEN 1 WHEN '31-60' THEN 2 WHEN '61-90' THEN 3 ELSE 4 END"


def by_day(row: sqlite3.Row):
    return (day(row["order_date"]), from_minor(row["total_net_amount"]), row["order_count"], row["currency"], row["company_code"])


def sales_by_day(row):
    return SalesSummaryByDay(*by_day(row))


def purchases_by_day(row):
    return PurchaseSummaryByDay(*by_day(row))


def sales_by_customer(row):
    return SalesSummaryByCustomer(
        row["sold_to_party"], row["customer_name"], day(row["order_date"]), from_minor(row["total_net_amount"]), row["order_count"], row["currency"], row["company_code"]
    )


def purchases_by_supplier(row):
    return PurchaseSummaryBySupplier(
        row["supplier"], row["supplier_name"], day(row["order_date"]), from_minor(row["total_net_amount"]), row["order_count"], row["currency"], row["company_code"]
    )


def purchases_by_material_group(row):
    return PurchaseSummaryByMaterialGroup(
        row["material_group"], row["material_group_name"], day(row["order_date"]), from_minor(row["total_net_amount"]), row["order_count"], row["currency"], row["company_code"]
    )


def by_material(kind):
    return lambda row: kind(
        row["material"], row["material_description"], day(row["order_date"]), quantity_from_minor(row["total_quantity"]), row["quantity_unit"],
        from_minor(row["total_net_amount"]), row["currency"], row["company_code"],
    )


def receivables(row):
    return ReceivablesSummary(
        day(row["as_of_date"]), from_minor(row["open_amount"]), from_minor(row["overdue_amount"]), row["open_count"], row["overdue_count"], row["currency"], row["company_code"]
    )


def receivables_by_customer(row):
    return ReceivablesByCustomer(
        row["sold_to_party"], row["customer_name"], day(row["as_of_date"]), from_minor(row["open_amount"]), from_minor(row["overdue_amount"]),
        row["open_count"], row["overdue_count"], row["currency"], row["company_code"],
    )


def ageing(row):
    return ReceivablesAgeing(day(row["as_of_date"]), row["age_bucket"], from_minor(row["open_amount"]), row["open_count"], row["currency"], row["company_code"])


def warehouse(row):
    return StockSummaryByWarehouse(row["plant"], row["storage_location"], row["storage_location_name"], from_minor(row["stock_value"]), row["material_count"], row["currency"], row["company_code"])


def material_group(row):
    return StockSummaryByMaterialGroup(row["material_group"], row["material_group_name"], from_minor(row["stock_value"]), row["material_count"], row["currency"], row["company_code"])


def stock_status(row):
    return StockSummaryByStatus(row["stock_status"], from_minor(row["stock_value"]), row["material_count"], row["currency"], row["company_code"])


def value_month(row):
    return StockValueMonth(row["posting_period"], from_minor(row["stock_value"]), row["currency"], row["company_code"])


def movements_by_day(row):
    return StockMovementSummaryByDay(day(row["posting_date"]), from_minor(row["receipt_value"]), from_minor(row["issue_value"]), row["movement_count"], row["currency"], row["company_code"])


def movements_by_hour(row):
    return StockMovementSummaryByHour(day(row["posting_date"]), row["posting_hour"], row["movement_count"], row["company_code"])


STOCK = {"stock_value": MONEY_SCALE}
FLOWS = {"receipt_value": MONEY_SCALE, "issue_value": MONEY_SCALE}

VIEWS = {
    "StockSummaryByWarehouse": ("stock_summary_by_warehouse", warehouse, STOCK, "plant, storage_location, currency, company_code"),
    "StockSummaryByMaterialGroup": ("stock_summary_by_material_group", material_group, STOCK, "material_group, currency, company_code"),
    "StockSummaryByStatus": ("stock_summary_by_status", stock_status, STOCK, "stock_status, currency, company_code"),
    "StockValueByMonth": ("stock_value_month", value_month, STOCK, "posting_period, currency, company_code"),
    "StockMovementSummaryByDay": ("stock_movement_summary_by_day", movements_by_day, FLOWS, "posting_date, currency, company_code"),
    "StockMovementSummaryByHour": ("stock_movement_summary_by_hour", movements_by_hour, {}, "posting_date, posting_hour, company_code"),
    "SalesSummaryByDay": ("sales_summary_by_day", sales_by_day, MONEY, BY_DAY),
    "SalesSummaryByCustomer": ("sales_summary_by_customer", sales_by_customer, MONEY, BY_CUSTOMER),
    "SalesSummaryByMaterial": ("sales_summary_by_material", by_material(SalesSummaryByMaterial), MONEY_AND_QUANTITY, BY_MATERIAL),
    "PurchaseSummaryByDay": ("purchase_summary_by_day", purchases_by_day, MONEY, BY_DAY),
    "PurchaseSummaryBySupplier": ("purchase_summary_by_supplier", purchases_by_supplier, MONEY, BY_SUPPLIER),
    "PurchaseSummaryByMaterialGroup": ("purchase_summary_by_material_group", purchases_by_material_group, MONEY, "order_date, material_group, currency, company_code"),
    "PurchaseSummaryByMaterial": ("purchase_summary_by_material", by_material(PurchaseSummaryByMaterial), MONEY_AND_QUANTITY, BY_MATERIAL),
}

AS_OF = {
    "ReceivablesSummary": (receivables, OPEN, "currency, company_code"),
    "ReceivablesByCustomer": (receivables_by_customer, OPEN, "sold_to_party, currency, company_code"),
    "ReceivablesAgeing": (ageing, AGEING, f"currency, company_code, {BUCKET_ORDER}"),
}


def summary_table(db: Database, name: str, as_of: date | None = None) -> SqliteTable | None:
    if name in VIEWS:
        view, mapper, scales, tie = VIEWS[name]
        return SqliteTable(db, view, lambda rows: [mapper(row) for row in rows], scales, tie)
    if name in AS_OF and as_of is not None:
        mapper, scales, tie = AS_OF[name]
        return SqliteTable(db, f"({query(name)})", lambda rows: [mapper(row) for row in rows], scales, tie, [as_of.isoformat()])
    return None
