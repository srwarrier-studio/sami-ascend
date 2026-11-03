from datetime import date
from decimal import Decimal

from synapse_api.application.catalog import GetWidgetData, ListCatalog
from synapse_api.application.receivables_widgets import receivables_catalog
from synapse_api.domain.entities.receivables import AgeBucket, CustomerReceivable, ReceivablesTotal
from synapse_api.infrastructure.mock_receivables_source import MockReceivablesSource

TODAY = date(2026, 11, 3)


def data(source: MockReceivablesSource, entry_id: str, currency: str = "INR", top: int = 5) -> dict:
    return GetWidgetData(receivables_catalog(source)).execute(entry_id, TODAY, currency, top)


def customer(code: str, name: str, overdue: str, open_: str = "1000", currency: str = "INR") -> CustomerReceivable:
    return CustomerReceivable(code, name, currency, Decimal(open_), Decimal(overdue))


class TestList:
    def test_lists_three_finance_widgets_under_their_old_ids(self):
        entries = ListCatalog(receivables_catalog(MockReceivablesSource())).execute()
        assert [e.id for e in entries] == ["fin-receivables", "fin-ageing", "fin-overdue"]
        assert {e.category for e in entries} == {"Finance"}


class TestOutstanding:
    def test_shows_the_open_amount_and_what_is_overdue_of_it(self):
        source = MockReceivablesSource(totals=[ReceivablesTotal("INR", Decimal("1840000"), Decimal("450000"), 12, 3), ReceivablesTotal("USD", Decimal("5"), Decimal("1"), 1, 1)])
        props = data(source, "fin-receivables")
        assert props["value"] == 1840000.0
        assert props["caption"] == "₹4,50,000 overdue"
        assert props["measure"] == "receivables"

    def test_nothing_open_is_zero(self):
        assert data(MockReceivablesSource(), "fin-receivables")["value"] == 0.0


class TestAgeing:
    def test_has_the_five_buckets_in_order_with_missing_ones_as_zero(self):
        source = MockReceivablesSource(buckets=[AgeBucket("31-60", "INR", Decimal("540"), 2), AgeBucket("current", "INR", Decimal("920"), 5), AgeBucket("current", "USD", Decimal("9"), 1)])
        assert data(source, "fin-ageing")["data"] == [
            {"label": "Not due", "value": 920.0},
            {"label": "1-30 days", "value": 0.0},
            {"label": "31-60 days", "value": 540.0},
            {"label": "61-90 days", "value": 0.0},
            {"label": "90+ days", "value": 0.0},
        ]


class TestMostOverdue:
    def test_ranks_customers_with_something_overdue(self):
        source = MockReceivablesSource(customers=[customer("1", "Kestrel", "310"), customer("2", "Alder", "240"), customer("3", "Never late", "0"), customer("4", "Other money", "999", currency="USD")])
        assert data(source, "fin-overdue")["items"] == [{"label": "Kestrel", "value": 310.0}, {"label": "Alder", "value": 240.0}]

    def test_top_limits_the_rows(self):
        source = MockReceivablesSource(customers=[customer(str(n), f"C{n}", str(n)) for n in range(1, 9)])
        assert len(data(source, "fin-overdue", top=2)["items"]) == 2
