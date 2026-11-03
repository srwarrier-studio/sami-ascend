import time
from datetime import date
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from butterfly.entrypoint.app import create_app
from butterfly.infrastructure.api.odata import DRIVERS_ROOT, ROOT
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo as MemoryDrivers
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo as MemoryOrders
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.story_seed import build_story_seed
from butterfly.infrastructure.sqlite.driver_repo import SqliteDriverRepo
from butterfly.infrastructure.sqlite.sales_order_repo import SqliteSalesOrderRepo

TODAY = date(2026, 10, 31)
STORY = build_story_seed(TODAY, find_scenario("august-contract"), COMPANIES)


def memory_client() -> TestClient:
    drivers = MemoryDrivers(STORY.contracts, STORY.deliveries, STORY.production_orders, STORY.components, STORY.invoices)
    return TestClient(create_app(MemoryOrders(STORY.orders), drivers=drivers))


def sqlite_client() -> TestClient:
    drivers = SqliteDriverRepo.from_lists(STORY.contracts, STORY.deliveries, STORY.production_orders, STORY.components, STORY.invoices)
    return TestClient(create_app(SqliteSalesOrderRepo.from_orders(STORY.orders), drivers=drivers))


MEMORY, SQLITE = memory_client(), sqlite_client()

ORDERS = [
    "SalesOrder?$top=5",
    "SalesOrder?$filter=CompanyCode eq 'INA2' and OverallStatus ne 'X'&$orderby=OrderDate desc,SalesOrder&$top=20",
    "SalesOrder?$filter=OrderDate ge 2026-08-01 and OrderDate le 2026-08-31&$count=true&$top=3",
    "SalesOrder?$filter=TotalNetAmount gt 100000.50&$orderby=TotalNetAmount desc&$top=10",
    "SalesOrder?$filter=TotalNetAmount gt 100000.555&$orderby=TotalNetAmount&$top=5",
    "SalesOrder?$filter=TotalNetAmount eq 0.001",
    "SalesOrder?$filter=contains(CustomerName,'Nutrition')&$top=4&$skip=2&$count=true",
    "SalesOrder?$filter=startswith(CustomerName,'Harbor') or Country eq 'US'&$orderby=CustomerName desc,OrderDate&$top=8",
    "SalesOrder?$filter=not (RequestedDeliveryDate eq 2026-08-10)&$count=true&$top=2",
    "SalesOrder?$filter=RequestedDeliveryDate ne 2026-08-10&$count=true&$top=2",
    "SalesOrder?$filter=CreationDateTime ge 2026-10-01T00:00:00Z&$orderby=CreationDateTime desc&$top=3",
    "SalesOrder?$expand=_Item&$top=2",
    "SalesOrder?$select=SalesOrder,TotalNetAmount&$orderby=SalesOrder desc&$top=3",
    "SalesOrder?$filter=OverallStatus eq 'Z'&$count=true",
    "SalesOrder?$skip=100000&$count=true",
]
DRIVERS = [
    "SalesContract?$filter=ContractStatus eq 'E'&$orderby=ValidFrom&$top=10",
    "SalesContract?$filter=ContractValue gt 1000000 and TransactionCurrency eq 'USD'&$count=true",
    "PurchaseDelivery?$filter=DeliveryStatus eq 'O'&$orderby=PromisedDeliveryDate,PurchaseOrder&$top=10&$count=true",
    "PurchaseDelivery?$filter=ActualDeliveryDate gt PromisedDeliveryDate&$top=3",
    "PurchaseDelivery?$filter=OrderedQuantity ge 5000.5 and Material eq 'RAW-2002'&$top=5",
    "CustomerInvoice?$filter=NetAmount gt ClearedAmount&$top=3",
    "CustomerInvoice?$filter=ClearedAmount gt 0 and DueDate lt 2026-09-01&$orderby=InvoiceDate desc&$top=6&$count=true",
    "ProductionOrder?$filter=ProductionStatus eq 'C' and PlannedQuantity gt 100&$orderby=PlannedStartDate&$top=5",
    "ProductionOrderComponent?$filter=ProductionOrder eq '0001000417'",
    "ProductionOrderComponent?$orderby=RequiredQuantity desc&$top=4",
]


def get(client: TestClient, root: str, path: str):
    response = client.get(root.rstrip("/") + "/" + quote(path, safe="/?=&$,()'"))
    return response.status_code, response.json()


@pytest.mark.parametrize("path", ORDERS)
def test_orders_answer_the_same_from_sql(path):
    assert get(SQLITE, ROOT, path) == get(MEMORY, ROOT, path)


@pytest.mark.parametrize("path", DRIVERS)
def test_driver_entities_answer_the_same_from_sql(path):
    assert get(SQLITE, DRIVERS_ROOT, path) == get(MEMORY, DRIVERS_ROOT, path)


@pytest.mark.parametrize("path", ["SalesOrder?$filter=Bogus eq 'x'", "SalesOrder?$filter=OrderDate eq 'x'", "SalesOrder?$orderby=Nope", "SalesOrder?$top=abc", "SalesOrder?$filter=(", "SalesOrder?$count=maybe"])
def test_a_bad_query_is_refused_the_same_way(path):
    assert get(SQLITE, ROOT, path) == get(MEMORY, ROOT, path)
    assert get(SQLITE, ROOT, path)[0] == 400


class TestInjection:
    @pytest.mark.parametrize("value", ["x' OR '1'='1", "x'; DROP TABLE sales_order; --", "x' --", "%", "_", "a''b"])
    def test_a_value_is_data_never_sql(self, value):
        text = value.replace("'", "''")
        status, body = get(SQLITE, ROOT, f"SalesOrder?$filter=CustomerName eq '{text}'&$count=true")
        assert status == 200 and body["@odata.count"] == 0
        assert get(SQLITE, ROOT, "SalesOrder?$top=1&$count=true")[1]["@odata.count"] == len(STORY.orders)

    def test_contains_treats_percent_as_a_character_not_a_pattern(self):
        assert get(SQLITE, ROOT, "SalesOrder?$filter=contains(CustomerName,'%')&$count=true")[1]["@odata.count"] == 0


def test_a_1000_row_read_is_not_slower_than_the_lists():
    path = "SalesOrder?$top=1000&$orderby=OrderDate desc,SalesOrder"
    started = time.perf_counter()
    get(MEMORY, ROOT, path)
    memory = time.perf_counter() - started
    started = time.perf_counter()
    get(SQLITE, ROOT, path)
    sqlite = time.perf_counter() - started
    assert sqlite < max(memory * 3, 1.0)
