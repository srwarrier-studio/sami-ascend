from datetime import date
from decimal import Decimal
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from butterfly.entrypoint.app import build_default_app, create_app
from butterfly.infrastructure.api.odata import DRIVERS_ROOT, ROOT
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo as MemoryDrivers
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo as MemoryOrders
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.story_seed import build_story_seed
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.driver_repo import SqliteDriverRepo
from butterfly.infrastructure.sqlite.sales_order_repo import SqliteSalesOrderRepo
from butterfly.infrastructure.sqlite.seeder import prepare

TODAY = date(2026, 10, 31)
STORY = build_story_seed(TODAY, find_scenario("august-contract"), COMPANIES)
RATE = {"USD": Decimal(80), "INR": Decimal(1)}
ARGS = (STORY.contracts, STORY.deliveries, STORY.production_orders, STORY.components, STORY.invoices)
MEMORY = TestClient(create_app(MemoryOrders(STORY.orders), drivers=MemoryDrivers(*ARGS)))
SQLITE = TestClient(create_app(SqliteSalesOrderRepo.from_orders(STORY.orders), drivers=SqliteDriverRepo.from_lists(*ARGS)))


def get(client: TestClient, root: str, path: str):
    response = client.get(root.rstrip("/") + "/" + quote(path, safe="/?=&$,()'"))
    return response.status_code, response.json()


def every(client: TestClient, root: str, entity: str, query: str = "") -> list[dict]:
    found: list[dict] = []
    while True:
        page = get(client, root, f"{entity}?$top=1000&$skip={len(found)}{query}")[1]["value"]
        found += page
        if len(page) < 1000:
            return found


class TestOrdersAndPurchaseItems:
    def test_an_order_carries_its_value_in_rupees(self):
        for row in every(SQLITE, ROOT, "SalesOrder", "&$filter=OrderDate ge 2026-10-20&$select=TransactionCurrency,TotalNetAmount,TotalNetAmountLocal,LocalCurrency"):
            assert Decimal(row["TotalNetAmountLocal"]) == Decimal(row["TotalNetAmount"]) * RATE[row["TransactionCurrency"]] and row["LocalCurrency"] == "INR"

    def test_a_rupee_order_is_its_own_local_amount(self):
        rows = every(SQLITE, ROOT, "SalesOrder", "&$filter=TransactionCurrency eq 'INR'&$top=50")
        assert rows and all(r["TotalNetAmountLocal"] == r["TotalNetAmount"] for r in rows)

    def test_a_purchase_item_carries_its_value_in_rupees(self):
        rows = every(SQLITE, DRIVERS_ROOT, "PurchaseDelivery", "&$filter=OrderDate ge 2026-09-01")
        assert {r["TransactionCurrency"] for r in rows} == {"INR", "USD"}
        for r in rows:
            assert Decimal(r["NetAmountLocal"]) == Decimal(r["NetAmount"]) * RATE[r["TransactionCurrency"]] and r["LocalCurrency"] == "INR"


class TestSummariesAddUp:
    def test_sales_by_day_local_equals_the_orders_local_over_all_currencies(self):
        summary = sum((Decimal(r["TotalNetAmountLocal"]) for r in every(SQLITE, ROOT, "SalesSummaryByDay")), Decimal(0))
        orders = sum((o.total_net_amount_local for o in STORY.orders if o.overall_status != "X"), Decimal(0))
        assert summary == orders

    def test_the_customer_and_material_summaries_add_up_to_the_day_summary(self):
        day = sum((Decimal(r["TotalNetAmountLocal"]) for r in every(SQLITE, ROOT, "SalesSummaryByDay")), Decimal(0))
        customer = sum((Decimal(r["TotalNetAmountLocal"]) for r in every(SQLITE, ROOT, "SalesSummaryByCustomer")), Decimal(0))
        material = sum((Decimal(r["TotalNetAmountLocal"]) for r in every(SQLITE, ROOT, "SalesSummaryByMaterial")), Decimal(0))
        assert day == customer == material

    def test_a_dollar_row_is_80_times_its_document_amount_and_a_rupee_row_equals_it(self):
        for r in every(SQLITE, ROOT, "SalesSummaryByDay", "&$filter=OrderDate ge 2026-10-01"):
            assert Decimal(r["TotalNetAmountLocal"]) == Decimal(r["TotalNetAmount"]) * RATE[r["Currency"]]

    def test_purchase_summaries_add_up(self):
        by_day = sum((Decimal(r["TotalNetAmountLocal"]) for r in every(SQLITE, DRIVERS_ROOT, "PurchaseSummaryByDay")), Decimal(0))
        for entity in ("PurchaseSummaryBySupplier", "PurchaseSummaryByMaterial", "PurchaseSummaryByMaterialGroup"):
            assert sum((Decimal(r["TotalNetAmountLocal"]) for r in every(SQLITE, DRIVERS_ROOT, entity)), Decimal(0)) == by_day, entity
        assert by_day == sum((d.net_amount_local for d in STORY.deliveries if d.delivery_status != "X"), Decimal(0))

    @pytest.mark.parametrize("as_of", ["2026-10-31", "2026-08-15", "2026-03-01"])
    def test_receivables_local_equals_the_open_invoices_in_rupees(self, as_of):
        from butterfly.application.receivables import is_overdue, open_amount, open_invoices
        from butterfly.domain.entities.master_data import to_local

        invoices = open_invoices(STORY.invoices, date.fromisoformat(as_of))
        day = date.fromisoformat(as_of)
        rows = every(SQLITE, DRIVERS_ROOT, "ReceivablesSummary", f"&AsOfDate={as_of}")
        assert sum((Decimal(r["OpenAmountLocal"]) for r in rows), Decimal(0)) == sum((to_local(open_amount(i, day), i.transaction_currency) for i in invoices), Decimal(0))
        assert sum((Decimal(r["OverdueAmountLocal"]) for r in rows), Decimal(0)) == sum((to_local(open_amount(i, day), i.transaction_currency) for i in invoices if is_overdue(i, day)), Decimal(0))
        ageing = every(SQLITE, DRIVERS_ROOT, "ReceivablesAgeing", f"&AsOfDate={as_of}")
        customers = every(SQLITE, DRIVERS_ROOT, "ReceivablesByCustomer", f"&AsOfDate={as_of}")
        total = sum((Decimal(r["OpenAmountLocal"]) for r in rows), Decimal(0))
        assert sum((Decimal(r["OpenAmountLocal"]) for r in ageing), Decimal(0)) == total == sum((Decimal(r["OpenAmountLocal"]) for r in customers), Decimal(0))


QUERIES = [
    (ROOT, "SalesOrder?$filter=TotalNetAmountLocal gt 1000000.5&$orderby=TotalNetAmountLocal desc&$top=8&$count=true"),
    (ROOT, "SalesOrder?$filter=LocalCurrency eq 'INR' and TransactionCurrency eq 'USD'&$orderby=TotalNetAmountLocal,SalesOrder&$top=5&$count=true"),
    (ROOT, "SalesSummaryByDay?$filter=TotalNetAmountLocal gt 2000000.5&$orderby=TotalNetAmountLocal desc&$top=6&$count=true"),
    (ROOT, "SalesSummaryByCustomer?$filter=OrderDate ge 2026-10-01&$orderby=TotalNetAmountLocal desc&$top=6"),
    (ROOT, "SalesSummaryByMaterial?$filter=TotalNetAmountLocal gt 100000.5&$orderby=TotalNetAmountLocal&$top=5&$count=true"),
    (DRIVERS_ROOT, "PurchaseDelivery?$filter=NetAmountLocal gt 500000.5&$orderby=NetAmountLocal desc&$top=5&$count=true"),
    (DRIVERS_ROOT, "PurchaseSummaryByDay?$filter=TotalNetAmountLocal gt 1000000.5&$orderby=TotalNetAmountLocal desc&$top=5&$count=true"),
    (DRIVERS_ROOT, "PurchaseSummaryByMaterialGroup?$filter=LocalCurrency eq 'INR'&$orderby=TotalNetAmountLocal desc&$top=5"),
    (DRIVERS_ROOT, "ReceivablesSummary?AsOfDate=2026-10-31&$filter=OpenAmountLocal gt 1000000.5&$orderby=OpenAmountLocal desc"),
    (DRIVERS_ROOT, "ReceivablesByCustomer?AsOfDate=2026-10-31&$orderby=OverdueAmountLocal desc,SoldToParty&$top=6&$count=true"),
    (DRIVERS_ROOT, "ReceivablesAgeing?AsOfDate=2026-10-31&$filter=OpenAmountLocal gt 100000.5&$orderby=OpenAmountLocal desc"),
]


@pytest.mark.parametrize(("root", "path"), QUERIES)
def test_the_database_answers_like_the_lists_on_the_new_fields(root, path):
    status, body = get(SQLITE, root, path)
    assert status == 200 and (status, body) == get(MEMORY, root, path)


class TestAnApiOrderAndTheMigration:
    PAYLOAD = {"SalesOrderType": "OR", "CompanyCode": "INA1", "SoldToParty": "0000100001", "TransactionCurrency": "USD", "_Item": [{"Material": "RM-1001", "Quantity": "10.000", "QuantityUnit": "KG"}]}

    def test_a_created_order_has_the_pair_and_a_change_keeps_it(self):
        client = TestClient(build_default_app(date.today(), "small", "august-contract", ":memory:"))
        payload = {**self.PAYLOAD, "TransactionCurrency": "INR"}
        created = client.post(ROOT + "SalesOrder", json=payload).json()
        assert created["TotalNetAmountLocal"] == created["TotalNetAmount"] and created["LocalCurrency"] == "INR"
        changed = client.patch(ROOT + f"SalesOrder('{created['SalesOrder']}')", json={"RequestedDeliveryDate": "2030-01-01"}, headers={"If-Match": created["@odata.etag"]}).json()
        assert changed["TotalNetAmountLocal"] == created["TotalNetAmountLocal"]

    def test_an_older_database_gets_the_columns_the_views_and_the_local_amounts_of_its_api_orders(self, tmp_path):
        path = str(tmp_path / "butterfly.db")
        db = Database(path)
        prepare(db, "small", "august-contract", date.today())
        db.execute("INSERT INTO sales_order VALUES ('0000099999', 'OR', '0000100001', NULL, '2026-11-03', NULL, 'USD', 625000, 'A', 'ME', '2026-11-03T09:00:00+00:00', '2026-11-03T09:00:00+00:00', 'INA1', 'US', 'api', 625000, 'INR')")
        db.execute("INSERT INTO sales_order_item VALUES ('0000099999', '000010', 'RM-1001', NULL, 10000, 'KG', 625000, 625000)")
        for view in [row["name"] for row in db.query("SELECT name FROM sqlite_master WHERE type = 'view'")]:
            db.execute(f"DROP VIEW {view}")
        for table, column in (("sales_order", "total_net_amount_local"), ("sales_order", "local_currency"), ("sales_order_item", "net_amount_local")):
            db.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
        db.execute("UPDATE meta SET value = '4' WHERE key = 'layout'")
        db.close()
        client = TestClient(build_default_app(date.today(), "small", "august-contract", path))
        row = get(client, ROOT, "SalesOrder?$filter=SalesOrder eq '0000099999'")[1]["value"][0]
        assert row["TotalNetAmountLocal"] == "500000.00" and row["LocalCurrency"] == "INR" and row["TotalNetAmount"] == "6250.00"
        day = get(client, ROOT, "SalesSummaryByDay?$filter=OrderDate eq 2026-11-03")[1]["value"]
        assert any(r["TotalNetAmountLocal"] == "500000.00" for r in day)
