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
from butterfly.domain.entities.finance import CashSummaryByDay, ExpenseSummaryByDay
from butterfly.domain.entities.exports import ExportSummaryByDay, ExportSummaryByDestination, ExportSummaryByMode
from butterfly.domain.entities.production import DowntimeSummaryByDay, OutputSummaryByLineShift, ProductionSummaryByDay, ScrapSummaryByDay
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

MONEY = {"total_net_amount": MONEY_SCALE, "total_net_amount_local": MONEY_SCALE}
MONEY_AND_QUANTITY = {"total_net_amount": MONEY_SCALE, "total_net_amount_local": MONEY_SCALE, "total_quantity": QUANTITY_SCALE}
OPEN = {"open_amount": MONEY_SCALE, "overdue_amount": MONEY_SCALE, "open_amount_local": MONEY_SCALE, "overdue_amount_local": MONEY_SCALE}
AGEING = {"open_amount": MONEY_SCALE, "open_amount_local": MONEY_SCALE}

BY_DAY = "order_date, currency, company_code"
BY_CUSTOMER = "order_date, sold_to_party, currency, company_code"
BY_SUPPLIER = "order_date, supplier, currency, company_code"
BY_MATERIAL = "order_date, material, currency, company_code"
BUCKET_ORDER = "CASE age_bucket WHEN 'current' THEN 0 WHEN '1-30' THEN 1 WHEN '31-60' THEN 2 WHEN '61-90' THEN 3 ELSE 4 END"


def by_day(row: sqlite3.Row):
    return (day(row["order_date"]), from_minor(row["total_net_amount"]), row["order_count"], row["currency"], row["company_code"], from_minor(row["total_net_amount_local"]), row["local_currency"])


def sales_by_day(row):
    return SalesSummaryByDay(*by_day(row))


def purchases_by_day(row):
    return PurchaseSummaryByDay(*by_day(row))


def sales_by_customer(row):
    return SalesSummaryByCustomer(
        row["sold_to_party"], row["customer_name"], day(row["order_date"]), from_minor(row["total_net_amount"]), row["order_count"], row["currency"], row["company_code"],
        from_minor(row["total_net_amount_local"]), row["local_currency"],
    )


def purchases_by_supplier(row):
    return PurchaseSummaryBySupplier(
        row["supplier"], row["supplier_name"], day(row["order_date"]), from_minor(row["total_net_amount"]), row["order_count"], row["currency"], row["company_code"],
        from_minor(row["total_net_amount_local"]), row["local_currency"],
    )


def purchases_by_material_group(row):
    return PurchaseSummaryByMaterialGroup(
        row["material_group"], row["material_group_name"], day(row["order_date"]), from_minor(row["total_net_amount"]), row["order_count"], row["currency"], row["company_code"],
        from_minor(row["total_net_amount_local"]), row["local_currency"],
    )


def by_material(kind):
    return lambda row: kind(
        row["material"], row["material_description"], day(row["order_date"]), quantity_from_minor(row["total_quantity"]), row["quantity_unit"],
        from_minor(row["total_net_amount"]), row["currency"], row["company_code"], from_minor(row["total_net_amount_local"]), row["local_currency"],
    )


def receivables(row):
    return ReceivablesSummary(
        day(row["as_of_date"]), from_minor(row["open_amount"]), from_minor(row["overdue_amount"]), row["open_count"], row["overdue_count"], row["currency"], row["company_code"],
        from_minor(row["open_amount_local"]), from_minor(row["overdue_amount_local"]),
    )


def receivables_by_customer(row):
    return ReceivablesByCustomer(
        row["sold_to_party"], row["customer_name"], day(row["as_of_date"]), from_minor(row["open_amount"]), from_minor(row["overdue_amount"]),
        row["open_count"], row["overdue_count"], row["currency"], row["company_code"], from_minor(row["open_amount_local"]), from_minor(row["overdue_amount_local"]),
    )


def ageing(row):
    return ReceivablesAgeing(day(row["as_of_date"]), row["age_bucket"], from_minor(row["open_amount"]), row["open_count"], row["currency"], row["company_code"], from_minor(row["open_amount_local"]))


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


def production_day(row):
    return ProductionSummaryByDay(
        day(row["posting_date"]), from_minor(row["planned_hours"]), from_minor(row["downtime_hours"]), from_minor(row["target_value"]), from_minor(row["good_value"]),
        from_minor(row["scrap_value"]), row["confirmation_count"], row["currency"], row["company_code"],
    )


def downtime_day(row):
    return DowntimeSummaryByDay(day(row["posting_date"]), row["downtime_cause"], from_minor(row["downtime_hours"]), row["event_count"], row["company_code"])


def scrap_day(row):
    return ScrapSummaryByDay(day(row["posting_date"]), row["scrap_reason"], from_minor(row["scrap_value"]), row["confirmation_count"], row["currency"], row["company_code"])


def output_line_shift(row):
    return OutputSummaryByLineShift(day(row["posting_date"]), row["work_center"], row["shift"], row["work_center_name"], from_minor(row["good_value"]), row["currency"], row["company_code"])


def export_day(row):
    return ExportSummaryByDay(day(row["shipment_date"]), row["shipment_count"], from_minor(row["net_amount"]), row["currency"], row["company_code"])


def export_destination(row):
    return ExportSummaryByDestination(day(row["shipment_date"]), row["country"], row["country_name"], row["shipment_count"], from_minor(row["net_amount"]), row["currency"], row["company_code"])


def export_mode(row):
    return ExportSummaryByMode(day(row["shipment_date"]), row["transport_mode"], row["shipment_count"], row["company_code"])


def cash_day(row):
    return CashSummaryByDay(day(row["posting_date"]), row["direction"], row["payment_count"], from_minor(row["amount"]), row["currency"], row["company_code"])


def expense_day(row):
    return ExpenseSummaryByDay(day(row["posting_date"]), row["expense_category"], row["payment_count"], from_minor(row["amount"]), row["currency"], row["company_code"])


AMOUNT = {"amount": MONEY_SCALE}
NET = {"net_amount": MONEY_SCALE}
STOCK = {"stock_value": MONEY_SCALE}
PRODUCTION = {"planned_hours": MONEY_SCALE, "downtime_hours": MONEY_SCALE, "target_value": MONEY_SCALE, "good_value": MONEY_SCALE, "scrap_value": MONEY_SCALE}
HOURS = {"downtime_hours": MONEY_SCALE}
SCRAP = {"scrap_value": MONEY_SCALE}
OUTPUT = {"good_value": MONEY_SCALE}
FLOWS = {"receipt_value": MONEY_SCALE, "issue_value": MONEY_SCALE}

VIEWS = {
    "CashSummaryByDay": ("cash_summary_by_day", cash_day, AMOUNT, "posting_date, direction, currency, company_code"),
    "ExpenseSummaryByDay": ("expense_summary_by_day", expense_day, AMOUNT, "posting_date, expense_category, currency, company_code"),
    "ExportSummaryByDay": ("export_summary_by_day", export_day, NET, "shipment_date, currency, company_code"),
    "ExportSummaryByDestination": ("export_summary_by_destination", export_destination, NET, "shipment_date, country, currency, company_code"),
    "ExportSummaryByMode": ("export_summary_by_mode", export_mode, {}, "shipment_date, transport_mode, company_code"),
    "ProductionSummaryByDay": ("production_summary_by_day", production_day, PRODUCTION, "posting_date, currency, company_code"),
    "DowntimeSummaryByDay": ("downtime_summary_by_day", downtime_day, HOURS, "posting_date, downtime_cause, company_code"),
    "ScrapSummaryByDay": ("scrap_summary_by_day", scrap_day, SCRAP, "posting_date, scrap_reason, currency, company_code"),
    "OutputSummaryByLineShift": ("output_summary_by_line_shift", output_line_shift, OUTPUT, "posting_date, work_center, shift, currency, company_code"),
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
