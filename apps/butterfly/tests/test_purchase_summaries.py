from dataclasses import replace
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from butterfly.application.usecase.summarize_purchases_by_day import SummarizePurchasesByDay
from butterfly.application.usecase.summarize_purchases_by_material import SummarizePurchasesByMaterial
from butterfly.application.usecase.summarize_purchases_by_supplier import SummarizePurchasesBySupplier
from butterfly.entrypoint.app import build_default_app
from butterfly.infrastructure.api.odata import DRIVERS_ROOT
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.story_seed import build_story_seed

TODAY = date(2026, 10, 31)
SEED = build_story_seed(TODAY)
GROUP = build_story_seed(TODAY, companies=COMPANIES)
REPO = InMemoryDriverRepo(deliveries=SEED.deliveries)
TOTAL = sum(d.net_amount for d in SEED.deliveries)


class TestSummariesAddUpToTheDeliveries:
    def test_every_summary_has_the_same_grand_total(self):
        for use_case in (SummarizePurchasesByDay, SummarizePurchasesBySupplier, SummarizePurchasesByMaterial):
            assert sum(r.total_net_amount for r in use_case(REPO).execute()) == TOTAL

    def test_by_supplier_groups_a_days_items_of_one_supplier(self):
        row = next(r for r in SummarizePurchasesBySupplier(REPO).execute() if r.order_date == date(2026, 6, 24) and r.supplier == "0000200001")
        assert (row.total_net_amount, row.order_count, row.supplier_name) == (Decimal("444000.00"), 2, "Deccan Agro Growers Cooperative")

    def test_by_material_sums_the_ordered_quantity_and_amount(self):
        row = next(r for r in SummarizePurchasesByMaterial(REPO).execute() if r.order_date == date(2026, 6, 24) and r.material == "RAW-2002")
        assert (row.total_quantity, row.quantity_unit, row.total_net_amount) == (Decimal("5000.000"), "KG", Decimal("260000.00"))

    def test_rows_come_in_date_order(self):
        days = [r.order_date for r in SummarizePurchasesByDay(REPO).execute()]
        assert days == sorted(days)

    def test_the_day_summary_counts_every_item_of_that_day(self):
        assert sum(r.order_count for r in SummarizePurchasesByDay(REPO).execute()) == len(SEED.deliveries)


class TestCancelledItemsAreLeftOut:
    CANCELLED = [replace(d, delivery_status="X") if d.purchase_order == "4500001207" else d for d in SEED.deliveries]
    REPO = InMemoryDriverRepo(deliveries=CANCELLED)

    def test_no_summary_counts_a_cancelled_item(self):
        gone = next(d for d in SEED.deliveries if d.purchase_order == "4500001207")
        for use_case in (SummarizePurchasesByDay, SummarizePurchasesBySupplier, SummarizePurchasesByMaterial):
            assert sum(r.total_net_amount for r in use_case(self.REPO).execute()) == TOTAL - gone.net_amount

    def test_a_material_with_only_cancelled_items_on_a_day_has_no_row(self):
        rows = SummarizePurchasesByMaterial(self.REPO).execute()
        assert not [r for r in rows if r.material == "RAW-2002" and r.order_date == date(2026, 6, 24)]


class TestThroughTheService:
    CLIENT = TestClient(build_default_app(TODAY, "story"))

    def get(self, path: str):
        return self.CLIENT.get(DRIVERS_ROOT + path)

    def test_filter_by_supplier_and_date_range(self):
        rows = self.get("PurchaseSummaryBySupplier?$filter=Supplier eq '0000200003' and OrderDate ge 2026-06-01 and OrderDate le 2026-06-30").json()["value"]
        assert [(r["OrderDate"], r["TotalNetAmount"]) for r in rows] == [("2026-06-24", "214000.00")]

    def test_paging_by_the_whole_key_reads_everything_once(self):
        rows, page = [], 100
        while chunk := self.get(f"PurchaseSummaryByMaterial?$orderby=OrderDate,Material,Currency&$top={page}&$skip={len(rows)}").json()["value"]:
            rows += chunk
        assert len(rows) == len({(r["OrderDate"], r["Material"]) for r in rows}) == len(GROUP.deliveries)
        assert sum(Decimal(r["TotalNetAmount"]) for r in rows) == sum(d.net_amount for d in GROUP.deliveries)

    def test_count_and_select_work_like_the_other_entities(self):
        body = self.get("PurchaseSummaryByDay?$count=true&$top=1&$select=OrderDate,TotalNetAmount").json()
        assert body["@odata.count"] > 1
        assert list(body["value"][0]) == ["OrderDate", "TotalNetAmount"]
