from datetime import date, timedelta
from decimal import Decimal
from urllib.parse import quote

from fastapi.testclient import TestClient

from butterfly.entrypoint.app import build_default_app
from butterfly.infrastructure.api.odata import DRIVERS_ROOT, EXPORT_ROOT, INVENTORY_ROOT, PRODUCTION_ROOT, ROOT
from butterfly.infrastructure.memory.companies import COMPANIES

TODAY = date.today()
EXPORTER = next((company, customer) for company in COMPANIES for customer in company.customers if customer.country != "IN")
DOMESTIC = next((company, customer) for company in COMPANIES for customer in company.customers if customer.country == "IN")


def start(path: str = ":memory:", day: date = TODAY) -> TestClient:
    return TestClient(build_default_app(day, "story", "august-contract", path))


def rows(client: TestClient, root: str, entity: str, query: str = "") -> list[dict]:
    found: list[dict] = []
    while True:
        path = f"{entity}?$top=1000&$skip={len(found)}{query}"
        page = client.get(root.rstrip("/") + "/" + quote(path, safe="/?=&$,()'")).json()["value"]
        found += page
        if len(page) < 1000:
            return found


def order_body(who, quantity: str = "100.000", delivery: str | None = None) -> dict:
    company, customer = who
    material, _, unit, _ = company.materials[0]
    body = {"SalesOrderType": "OR", "CompanyCode": company.code, "SoldToParty": customer.customer_id, "TransactionCurrency": customer.currency, "_Item": [{"Material": material, "Quantity": quantity, "QuantityUnit": unit}]}
    if delivery:
        body["RequestedDeliveryDate"] = delivery
    return body


def create(client: TestClient, who, **kwargs) -> dict:
    response = client.post(ROOT + "SalesOrder", json=order_body(who, **kwargs))
    assert response.status_code == 201, response.text
    return response.json()


def invoice_of(client: TestClient, number: str) -> dict | None:
    found = rows(client, DRIVERS_ROOT, "CustomerInvoice", f"&$filter=Invoice eq '9{number[1:]}'")
    return found[0] if found else None


def open_receivables(client: TestClient, currency: str, company: str) -> Decimal:
    found = rows(client, DRIVERS_ROOT, "ReceivablesSummary", f"&$filter=Currency eq '{currency}' and CompanyCode eq '{company}'")
    return Decimal(found[0]["OpenAmount"]) if found else Decimal(0)


def shipment_of(client: TestClient, number: str) -> dict | None:
    found = rows(client, EXPORT_ROOT, "ExportShipment", f"&$filter=SalesOrder eq '{number}'")
    return found[0] if found else None


def issues(client: TestClient, material: str, day: date, quantity: str) -> int:
    return len(rows(client, INVENTORY_ROOT, "StockMovement", f"&$filter=MovementType eq '601' and Material eq '{material}' and PostingDate eq {day} and Quantity eq {quantity}"))


class TestAnOrderForACustomerAbroad:
    def test_becomes_an_open_receivable_a_shipment_and_a_goods_issue(self):
        client = start()
        company, customer = EXPORTER
        material = company.materials[0][0]
        receivables, shipments, issued = open_receivables(client, customer.currency, company.code), len(rows(client, EXPORT_ROOT, "ExportShipment")), issues(client, material, TODAY, "100.000")
        order = create(client, EXPORTER)
        number, total = order["SalesOrder"], Decimal(order["TotalNetAmount"])
        invoice = invoice_of(client, number)
        assert invoice is not None and invoice["NetAmount"] == order["TotalNetAmount"] and invoice["ClearedAmount"] == "0.00" and invoice["ClearingDate"] is None
        assert open_receivables(client, customer.currency, company.code) == receivables + total
        shipment = shipment_of(client, number)
        assert shipment is not None and shipment["ShipmentStatus"] == "T" and shipment["ShipmentDate"] == str(TODAY) and shipment["DocumentAmount"] == order["TotalNetAmount"]
        assert len(rows(client, EXPORT_ROOT, "ExportShipment")) == shipments + 1
        assert issues(client, material, TODAY, "100.000") == issued + 1

    def test_shows_in_the_summaries_of_the_day(self):
        client = start()
        before = {r["CompanyCode"]: r["ShipmentCount"] for r in rows(client, EXPORT_ROOT, "ExportSummaryByDay", f"&$filter=ShipmentDate eq {TODAY}")}
        create(client, EXPORTER)
        after = {r["CompanyCode"]: r["ShipmentCount"] for r in rows(client, EXPORT_ROOT, "ExportSummaryByDay", f"&$filter=ShipmentDate eq {TODAY}")}
        assert after[EXPORTER[0].code] == before.get(EXPORTER[0].code, 0) + 1

    def test_a_second_order_gets_its_own_documents(self):
        client = start()
        first, second = create(client, EXPORTER), create(client, EXPORTER, quantity="7.000")
        assert first["SalesOrder"] != second["SalesOrder"]
        assert invoice_of(client, first["SalesOrder"])["Invoice"] != invoice_of(client, second["SalesOrder"])["Invoice"]
        assert shipment_of(client, first["SalesOrder"]) and shipment_of(client, second["SalesOrder"])


class TestAnOrderForACustomerAtHome:
    def test_has_an_invoice_and_a_goods_issue_but_no_shipment(self):
        client = start()
        company, customer = DOMESTIC
        material = company.materials[0][0]
        issued = issues(client, material, TODAY, "55.000")
        order = create(client, DOMESTIC, quantity="55.000")
        assert invoice_of(client, order["SalesOrder"]) is not None
        assert shipment_of(client, order["SalesOrder"]) is None
        assert issues(client, material, TODAY, "55.000") == issued + 1


class TestAnOrderForTheFuture:
    def test_is_invoiced_but_nothing_has_left_yet(self):
        client = start()
        company = EXPORTER[0]
        material = company.materials[0][0]
        future = str(TODAY + timedelta(days=20))
        issued = issues(client, material, TODAY + timedelta(days=20), "33.000")
        order = create(client, EXPORTER, quantity="33.000", delivery=future)
        assert invoice_of(client, order["SalesOrder"]) is not None
        assert shipment_of(client, order["SalesOrder"]) is None
        assert issues(client, material, TODAY + timedelta(days=20), "33.000") == issued


class TestChangingTheDeliveryDate:
    def test_moving_a_shipped_order_into_the_future_takes_its_shipment_back(self):
        client = start()
        order = create(client, EXPORTER)
        number = order["SalesOrder"]
        assert shipment_of(client, number) is not None
        future = str(TODAY + timedelta(days=30))
        response = client.patch(ROOT + f"SalesOrder('{number}')", json={"RequestedDeliveryDate": future}, headers={"If-Match": order["@odata.etag"]})
        assert response.status_code == 200, response.text
        assert shipment_of(client, number) is None
        assert invoice_of(client, number) is not None


class TestTheBooksStayBalanced:
    def test_stock_equals_the_movements_and_never_goes_negative(self):
        client = start()
        company = EXPORTER[0]
        material = company.materials[0][0]
        create(client, EXPORTER, quantity="250000.000")
        movements = rows(client, INVENTORY_ROOT, "StockMovement", f"&$filter=Material eq '{material}'&$orderby=MaterialDocument")
        running = Decimal(0)
        for m in movements:
            running += Decimal(m["Quantity"]) if m["DebitCreditCode"] == "S" else -Decimal(m["Quantity"])
            assert running >= 0
        stock = rows(client, INVENTORY_ROOT, "MaterialStock", f"&$filter=Material eq '{material}'")[0]
        assert Decimal(stock["StockQuantity"]) == running

    def test_the_latest_month_end_value_equals_the_stock_value_per_company(self):
        client = start()
        create(client, EXPORTER, quantity="12345.000")
        for code in {c.code for c in COMPANIES}:
            value = sum((Decimal(r["StockValue"]) for r in rows(client, INVENTORY_ROOT, "MaterialStock", f"&$filter=CompanyCode eq '{code}'")), Decimal(0))
            latest = rows(client, INVENTORY_ROOT, "StockValueByMonth", f"&$filter=CompanyCode eq '{code}'&$orderby=PostingPeriod desc")[0]
            assert Decimal(latest["StockValue"]) == value

    def test_invoice_numbers_stay_unique(self):
        client = start()
        for _ in range(3):
            create(client, EXPORTER)
        numbers = [r["Invoice"] for r in rows(client, DRIVERS_ROOT, "CustomerInvoice")]
        assert len(numbers) == len(set(numbers))

    def test_production_and_purchases_do_not_change(self):
        client = start()
        production = rows(client, PRODUCTION_ROOT, "ProductionSummaryByDay")
        purchases = rows(client, DRIVERS_ROOT, "PurchaseSummaryByDay")
        create(client, EXPORTER)
        assert rows(client, PRODUCTION_ROOT, "ProductionSummaryByDay") == production
        assert rows(client, DRIVERS_ROOT, "PurchaseSummaryByDay") == purchases


class TestRestartsAndNewDays:
    def test_the_documents_survive_a_restart(self, tmp_path):
        path = str(tmp_path / "butterfly.db")
        number = create(start(path), EXPORTER)["SalesOrder"]
        again = start(path)
        assert invoice_of(again, number) is not None and shipment_of(again, number) is not None

    def test_a_later_day_rebuilds_the_seed_and_the_order_keeps_its_documents(self, tmp_path):
        path = str(tmp_path / "butterfly.db")
        order = create(start(path), EXPORTER)
        number = order["SalesOrder"]
        tomorrow = start(path, TODAY + timedelta(days=1))
        assert invoice_of(tomorrow, number) is not None
        assert shipment_of(tomorrow, number) is not None
        kept = rows(tomorrow, ROOT, "SalesOrder", f"&$filter=SalesOrder eq '{number}'")
        assert len(kept) == 1 and kept[0]["TotalNetAmount"] == order["TotalNetAmount"]
        numbers = [r["SalesOrder"] for r in rows(tomorrow, ROOT, "SalesOrder", "&$select=SalesOrder")]
        assert len(numbers) == len(set(numbers))
