import sqlite3
from datetime import date, datetime

from butterfly.domain.entities.drivers import (
    CustomerInvoice,
    ProductionOrder,
    ProductionOrderComponent,
    PurchaseDelivery,
    SalesContract,
)
from butterfly.domain.entities.sales_order import SalesOrder, SalesOrderItem
from butterfly.infrastructure.sqlite.money import from_minor, quantity_from_minor


def day(value: str | None) -> date | None:
    return None if value is None else date.fromisoformat(value)


def moment(value: str) -> datetime:
    return datetime.fromisoformat(value)


def item_from_row(row: sqlite3.Row) -> SalesOrderItem:
    return SalesOrderItem(
        row["sales_order"], row["sales_order_item"], row["material"], row["material_description"], quantity_from_minor(row["quantity"]), row["quantity_unit"], from_minor(row["net_amount"])
    )


def order_from_row(row: sqlite3.Row, items: list[SalesOrderItem]) -> SalesOrder:
    return SalesOrder(
        sales_order=row["sales_order"],
        sales_order_type=row["sales_order_type"],
        sold_to_party=row["sold_to_party"],
        customer_name=row["customer_name"],
        order_date=day(row["order_date"]),
        requested_delivery_date=day(row["requested_delivery_date"]),
        transaction_currency=row["transaction_currency"],
        total_net_amount=from_minor(row["total_net_amount"]),
        overall_status=row["overall_status"],
        created_by_user=row["created_by_user"],
        creation_date_time=moment(row["creation_date_time"]),
        last_change_date_time=moment(row["last_change_date_time"]),
        items=items,
        company_code=row["company_code"],
        country=row["country"],
        sales_organization=row["sales_organization"],
        distribution_channel=row["distribution_channel"],
        division=row["division"],
        purchase_order_by_customer=row["purchase_order_by_customer"],
    )


def contract_from_row(row: sqlite3.Row) -> SalesContract:
    return SalesContract(
        row["sales_contract"], row["predecessor_contract"], row["sold_to_party"], row["customer_name"], day(row["valid_from"]), day(row["valid_to"]),
        from_minor(row["contract_value"]), row["transaction_currency"], row["contract_status"], row["company_code"],
    )


def delivery_from_row(row: sqlite3.Row) -> PurchaseDelivery:
    return PurchaseDelivery(
        row["purchase_order"], row["purchase_order_item"], row["supplier"], row["supplier_name"], row["material"], row["material_description"], day(row["order_date"]),
        quantity_from_minor(row["ordered_quantity"]), quantity_from_minor(row["delivered_quantity"]), row["quantity_unit"], day(row["promised_delivery_date"]),
        day(row["actual_delivery_date"]), row["delivery_status"], from_minor(row["net_amount"]), row["transaction_currency"], row["company_code"],
    )


def invoice_from_row(row: sqlite3.Row) -> CustomerInvoice:
    return CustomerInvoice(
        row["invoice"], row["sold_to_party"], row["customer_name"], day(row["invoice_date"]), day(row["due_date"]), from_minor(row["net_amount"]), row["transaction_currency"],
        from_minor(row["cleared_amount"]), day(row["clearing_date"]), row["company_code"], row["country"],
    )


def production_order_from_row(row: sqlite3.Row) -> ProductionOrder:
    return ProductionOrder(
        row["production_order"], row["material"], row["material_description"], quantity_from_minor(row["planned_quantity"]), quantity_from_minor(row["confirmed_quantity"]),
        row["quantity_unit"], day(row["planned_start_date"]), day(row["planned_end_date"]), day(row["actual_end_date"]), row["production_status"], row["delay_reason"], row["company_code"],
    )


def component_from_row(row: sqlite3.Row) -> ProductionOrderComponent:
    return ProductionOrderComponent(
        row["production_order"], row["material"], row["material_description"], quantity_from_minor(row["required_quantity"]), row["quantity_unit"], row["company_code"]
    )
