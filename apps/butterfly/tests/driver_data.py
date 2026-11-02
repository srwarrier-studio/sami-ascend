from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from butterfly.domain.entities.drivers import (
    ProductionOrder,
    ProductionOrderComponent,
    PurchaseDelivery,
    SalesContract,
)
from butterfly.entrypoint.app import create_app
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo
from conftest import ORDERS

CONTRACTS = [
    SalesContract("0040000071", None, "0000100001", "Harborline Nutrition LLC", date(2024, 7, 13), date(2025, 7, 12), Decimal("8000000.00"), "INR", "E"),
    SalesContract("0040000127", "0040000071", "0000100001", "Harborline Nutrition LLC", date(2025, 7, 13), date(2026, 7, 12), Decimal("9000000.00"), "INR", "E"),
    SalesContract("0040000163", "0040000127", "0000100001", "Harborline Nutrition LLC", date(2026, 9, 14), date(2027, 9, 13), Decimal("10000000.00"), "INR", "A"),
    SalesContract("0040000140", None, "0000100002", None, date(2026, 1, 1), date(2026, 12, 31), Decimal("5000000.00"), "INR", "A"),
]

DELIVERIES = [
    PurchaseDelivery("4500001207", "00010", "0000200001", "Deccan Agro Growers Cooperative", "RAW-2002", "Black pepper, whole", date(2026, 6, 24), Decimal("5000.000"), Decimal("5000.000"), "KG", date(2026, 7, 14), date(2026, 7, 26), "D"),
    PurchaseDelivery("4500001150", "00010", "0000200001", "Deccan Agro Growers Cooperative", "RAW-2002", "Black pepper, whole", date(2026, 5, 20), Decimal("5000.000"), Decimal("5000.000"), "KG", date(2026, 6, 10), date(2026, 6, 11), "D"),
    PurchaseDelivery("4500001302", "00010", "0000200002", "Malnad Botanicals Pvt Ltd", "RAW-2003", "Frankincense resin", date(2026, 10, 1), Decimal("2000.000"), Decimal("0.000"), "KG", date(2026, 10, 20), None, "O"),
]

PRODUCTION_ORDERS = [
    ProductionOrder("0001000417", "RM-1002", "Piperine extract 95%", Decimal("4000.000"), Decimal("4000.000"), "KG", date(2026, 7, 6), date(2026, 7, 20), date(2026, 8, 3), "C", "MATERIAL_SHORTAGE"),
    ProductionOrder("0001000388", "RM-1005", "Probiotic capsule 10B CFU", Decimal("900.000"), Decimal("900.000"), "EA", date(2026, 5, 4), date(2026, 5, 18), date(2026, 5, 24), "C", "MACHINE_BREAKDOWN"),
    ProductionOrder("0001000431", "RM-1002", "Piperine extract 95%", Decimal("4000.000"), Decimal("0.000"), "KG", date(2026, 8, 4), date(2026, 8, 18), None, "R", None),
]

COMPONENTS = [
    ProductionOrderComponent("0001000417", "RAW-2002", "Black pepper, whole", Decimal("4400.000"), "KG"),
    ProductionOrderComponent("0001000388", "RAW-2005", "Gelatin capsule shells", Decimal("950.000"), "KG"),
    ProductionOrderComponent("0001000431", "RAW-2002", "Black pepper, whole", Decimal("4400.000"), "KG"),
]


def make_driver_client() -> TestClient:
    drivers = InMemoryDriverRepo(CONTRACTS, DELIVERIES, PRODUCTION_ORDERS, COMPONENTS)
    return TestClient(create_app(InMemorySalesOrderRepo(ORDERS), drivers=drivers))
