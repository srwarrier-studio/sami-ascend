from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.sales import CustomerSales, DailySales, HighValueOrder, MaterialSales, OrderStatus


def daily_from_json(row: dict) -> DailySales:
    return DailySales(
        date.fromisoformat(row["OrderDate"]),
        Decimal(row["TotalNetAmountLocal"]),
        row["OrderCount"],
        row["LocalCurrency"],
    )


def customer_from_json(row: dict) -> CustomerSales:
    return CustomerSales(
        row["SoldToParty"],
        row["CustomerName"] or "",
        date.fromisoformat(row["OrderDate"]),
        Decimal(row["TotalNetAmountLocal"]),
        row["OrderCount"],
        row["LocalCurrency"],
    )


def material_from_json(row: dict) -> MaterialSales:
    return MaterialSales(
        row["Material"],
        row["MaterialDescription"] or "",
        date.fromisoformat(row["OrderDate"]),
        Decimal(row["TotalQuantity"]),
        row["QuantityUnit"],
        Decimal(row["TotalNetAmountLocal"]),
        row["LocalCurrency"],
    )


def order_from_json(row: dict) -> HighValueOrder:
    return HighValueOrder(
        row["SalesOrder"],
        row["CustomerName"] or "",
        date.fromisoformat(row["OrderDate"]),
        Decimal(row["TotalNetAmountLocal"]),
        row["LocalCurrency"],
        row["OverallStatus"],
    )


def status_from_json(row: dict) -> OrderStatus:
    return OrderStatus(date.fromisoformat(row["OrderDate"]), row["OverallStatus"])
