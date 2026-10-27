from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.sales import CustomerSales, DailySales, HighValueOrder, MaterialSales


def daily_from_json(row: dict) -> DailySales:
    return DailySales(
        date.fromisoformat(row["OrderDate"]),
        Decimal(row["TotalNetAmount"]),
        row["OrderCount"],
        row["Currency"],
    )


def customer_from_json(row: dict) -> CustomerSales:
    return CustomerSales(
        row["SoldToParty"],
        row["CustomerName"] or "",
        date.fromisoformat(row["OrderDate"]),
        Decimal(row["TotalNetAmount"]),
        row["OrderCount"],
        row["Currency"],
    )


def material_from_json(row: dict) -> MaterialSales:
    return MaterialSales(
        row["Material"],
        row["MaterialDescription"] or "",
        date.fromisoformat(row["OrderDate"]),
        Decimal(row["TotalQuantity"]),
        row["QuantityUnit"],
        Decimal(row["TotalNetAmount"]),
        row["Currency"],
    )


def order_from_json(row: dict) -> HighValueOrder:
    return HighValueOrder(
        row["SalesOrder"],
        row["CustomerName"] or "",
        date.fromisoformat(row["OrderDate"]),
        Decimal(row["TotalNetAmount"]),
        row["TransactionCurrency"],
        row["OverallStatus"],
    )
