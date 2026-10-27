from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.sales import CustomerSales, DailySales, MaterialSales


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
