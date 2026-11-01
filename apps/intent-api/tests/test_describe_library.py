from intent_api.application.describe_library import DescribeLibrary
from intent_api.domain.entities.scenario import Library, Scenario

LIBRARY = Library(
    {"Sales": "sales, customers", "Purchase": "spend"},
    {
        "sales_value": Scenario("sales_value", "Sales", "the sales figure", ("a",), ("period",)),
        "sales_trend": Scenario("sales_trend", "Sales", "the trend", ("a", "b"), ("period",), ("sales_value",)),
    },
)


class TestDescribeLibrary:
    def test_summary_counts_domains_and_scenarios(self):
        assert DescribeLibrary(LIBRARY).summary() == "ok: 2 domains, 2 scenarios"

    def test_show_lists_scenarios_under_their_domain(self):
        assert DescribeLibrary(LIBRARY).show().splitlines() == [
            "Sales: sales, customers",
            "  sales_value: the sales figure (needs period; 1 examples)",
            "  sales_trend: the trend (needs period; covers sales_value; 2 examples)",
            "Purchase: spend",
        ]
