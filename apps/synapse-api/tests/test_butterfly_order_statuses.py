from datetime import date

import httpx

from synapse_api.infrastructure.butterfly_sales_source import PAGE, ButterflySalesSource
from synapse_api.infrastructure.settings import Settings

ROOT = "http://sap/root/"


def source(handler) -> ButterflySalesSource:
    return ButterflySalesSource(Settings(sap_base_url=ROOT), httpx.MockTransport(handler))


def row(status: str) -> dict:
    return {"OrderDate": "2026-10-05", "OverallStatus": status}


class TestOrderStatuses:
    def test_asks_for_the_date_range_without_cancelled_orders(self):
        seen = []

        def handler(request):
            seen.append(str(request.url))
            return httpx.Response(200, json={"value": [row("A")]})

        [status] = source(handler).order_statuses(date(2026, 10, 1), date(2026, 10, 27))
        assert (status.date, status.status) == (date(2026, 10, 5), "A")
        assert seen == [
            f"{ROOT}SalesOrder?$filter=OrderDate%20ge%202026-10-01%20and%20OrderDate%20le%202026-10-27%20and%20OverallStatus%20ne%20'X'"
            f"&$select=OrderDate,OverallStatus&$orderby=OrderDate&$top={PAGE}&$skip=0"
        ]

    def test_reads_every_page_until_a_short_one(self):
        pages = {0: [row("A")] * PAGE, PAGE: [row("B")] * 3}

        def handler(request):
            skip = int(request.url.params["$skip"])
            return httpx.Response(200, json={"value": pages[skip]})

        statuses = source(handler).order_statuses(date(2026, 10, 1), date(2026, 10, 27))
        assert len(statuses) == PAGE + 3
