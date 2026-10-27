from dataclasses import replace
from datetime import date

import pytest

from butterfly.application.dto.list_query_dto import ListQuery
from butterfly.application.usecase.list_sales_orders import ListSalesOrders
from butterfly.domain.errors import InvalidQuery
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo
from conftest import ORDERS, TODAY


def run(filter_text, orders=ORDERS):
    query = ListQuery(filter=filter_text)
    return ListSalesOrders(InMemorySalesOrderRepo(orders)).execute(query).rows


def numbers(filter_text, orders=ORDERS):
    return [order.sales_order for order in run(filter_text, orders)]


def expected(condition):
    return [order.sales_order for order in ORDERS if condition(order)]


class TestNoFilter:
    def test_returns_every_order(self):
        assert len(run(None)) == len(ORDERS)


class TestComparisonOperators:
    def test_eq_on_text(self):
        assert numbers("OverallStatus eq 'A'") == expected(lambda o: o.overall_status == "A")

    def test_ne_on_text(self):
        assert numbers("OverallStatus ne 'A'") == expected(lambda o: o.overall_status != "A")

    def test_eq_on_date(self):
        assert numbers("OrderDate eq 2026-10-27") == expected(lambda o: o.order_date == TODAY)

    def test_gt_and_lt_on_date(self):
        day = date(2026, 10, 22)
        assert numbers("OrderDate gt 2026-10-22") == expected(lambda o: o.order_date > day)
        assert numbers("OrderDate lt 2026-10-22") == expected(lambda o: o.order_date < day)

    def test_ge_and_le_include_the_boundary_date(self):
        day = date(2026, 10, 22)
        assert numbers("OrderDate ge 2026-10-22") == expected(lambda o: o.order_date >= day)
        assert numbers("OrderDate le 2026-10-22") == expected(lambda o: o.order_date <= day)

    def test_decimal_with_a_fraction(self):
        limit = ORDERS[0].total_net_amount
        assert numbers(f"TotalNetAmount ge {limit}") == expected(lambda o: o.total_net_amount >= limit)

    def test_decimal_written_as_a_whole_number(self):
        assert numbers("TotalNetAmount gt 100000") == expected(lambda o: o.total_net_amount > 100000)

    def test_timestamp_in_utc(self):
        first = ORDERS[10].creation_date_time
        stamp = first.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert numbers(f"CreationDateTime ge {stamp}") == expected(
            lambda o: o.creation_date_time >= first
        )


class TestStringFunctions:
    def test_contains(self):
        assert numbers("contains(CustomerName,'Steel')") == expected(
            lambda o: "Steel" in o.customer_name
        )

    def test_startswith(self):
        assert numbers("startswith(CustomerName,'Acme')") == expected(
            lambda o: o.customer_name.startswith("Acme")
        )

    def test_matching_is_case_sensitive(self):
        assert numbers("contains(CustomerName,'steel')") == []

    def test_empty_text_matches_every_filled_value(self):
        assert len(numbers("contains(CustomerName,'')")) == len(ORDERS)

    def test_space_after_comma_is_allowed(self):
        assert numbers("contains(CustomerName, 'Steel')") == numbers("contains(CustomerName,'Steel')")

    def test_can_be_negated(self):
        assert numbers("not contains(CustomerName,'Steel')") == expected(
            lambda o: "Steel" not in o.customer_name
        )


class TestLogic:
    def test_and_needs_both(self):
        assert numbers("OverallStatus eq 'A' and SoldToParty eq '0000100001'") == expected(
            lambda o: o.overall_status == "A" and o.sold_to_party == "0000100001"
        )

    def test_or_needs_either(self):
        assert numbers("OverallStatus eq 'A' or OverallStatus eq 'B'") == expected(
            lambda o: o.overall_status in ("A", "B")
        )

    def test_not_flips_the_result(self):
        assert numbers("not OverallStatus eq 'A'") == numbers("OverallStatus ne 'A'")

    def test_date_range_with_ge_and_le(self):
        low, high = date(2026, 10, 20), date(2026, 10, 24)
        assert numbers("OrderDate ge 2026-10-20 and OrderDate le 2026-10-24") == expected(
            lambda o: low <= o.order_date <= high
        )

    def test_filter_matching_nothing_returns_an_empty_list(self):
        assert numbers("OverallStatus eq 'Z'") == []


class TestPrecedence:
    def test_and_binds_tighter_than_or(self):
        text = "OverallStatus eq 'X' or OverallStatus eq 'A' and SoldToParty eq '0000100001'"
        assert numbers(text) == expected(
            lambda o: o.overall_status == "X"
            or (o.overall_status == "A" and o.sold_to_party == "0000100001")
        )

    def test_parentheses_override_precedence(self):
        text = "(OverallStatus eq 'X' or OverallStatus eq 'A') and SoldToParty eq '0000100001'"
        assert numbers(text) == expected(
            lambda o: o.overall_status in ("X", "A") and o.sold_to_party == "0000100001"
        )

    def test_not_binds_tighter_than_and(self):
        text = "not OverallStatus eq 'A' and SoldToParty eq '0000100001'"
        assert numbers(text) == expected(
            lambda o: o.overall_status != "A" and o.sold_to_party == "0000100001"
        )

    def test_not_over_a_group(self):
        text = "not (OverallStatus eq 'A' or OverallStatus eq 'B')"
        assert numbers(text) == expected(lambda o: o.overall_status not in ("A", "B"))

    def test_nested_parentheses(self):
        assert numbers("((OverallStatus eq 'A'))") == numbers("OverallStatus eq 'A'")

    def test_extra_spaces_are_fine(self):
        assert numbers("  OverallStatus   eq   'A'  ") == numbers("OverallStatus eq 'A'")


class TestNullValues:
    def with_nulls(self):
        return [
            replace(ORDERS[0], customer_name=None, requested_delivery_date=None),
            replace(ORDERS[1], customer_name="Acme", requested_delivery_date=date(2026, 11, 1)),
        ]

    def test_null_text_matches_no_comparison(self):
        orders = self.with_nulls()
        assert numbers("CustomerName ne 'Zed'", orders) == [orders[1].sales_order]

    def test_null_text_matches_no_function(self):
        orders = self.with_nulls()
        assert numbers("contains(CustomerName,'A')", orders) == [orders[1].sales_order]

    def test_null_date_matches_no_comparison(self):
        orders = self.with_nulls()
        assert numbers("RequestedDeliveryDate lt 2027-01-01", orders) == [orders[1].sales_order]


class TestLiterals:
    def test_doubled_quote_is_one_quote(self):
        orders = [replace(ORDERS[0], customer_name="D'Souza & Co"), ORDERS[1]]
        assert numbers("CustomerName eq 'D''Souza & Co'", orders) == [orders[0].sales_order]

    def test_negative_number_is_allowed(self):
        assert numbers("TotalNetAmount gt -1") == [order.sales_order for order in ORDERS]

    def test_text_with_keywords_inside_quotes_is_just_text(self):
        orders = [replace(ORDERS[0], customer_name="Black and White"), ORDERS[1]]
        assert numbers("CustomerName eq 'Black and White'", orders) == [orders[0].sales_order]

    def test_text_with_parentheses_inside_quotes_is_just_text(self):
        orders = [replace(ORDERS[0], customer_name="A (B)"), ORDERS[1]]
        assert numbers("CustomerName eq 'A (B)'", orders) == [orders[0].sales_order]


BAD_FILTERS = {
    "empty": "",
    "only spaces": "   ",
    "missing value": "OverallStatus eq",
    "missing operator": "OverallStatus 'A'",
    "unknown field": "Colour eq 'red'",
    "unknown operator": "OverallStatus like 'A'",
    "upper case operator": "OverallStatus EQ 'A'",
    "upper case and": "OverallStatus eq 'A' AND SoldToParty eq '1'",
    "unclosed parenthesis": "(OverallStatus eq 'A'",
    "extra closing parenthesis": "OverallStatus eq 'A')",
    "unterminated string": "OverallStatus eq 'A",
    "double quoted string": 'OverallStatus eq "A"',
    "dangling and": "OverallStatus eq 'A' and",
    "two conditions without and": "OverallStatus eq 'A' SoldToParty eq '1'",
    "text field compared to number": "OverallStatus eq 5",
    "number field compared to text": "TotalNetAmount gt '100'",
    "date field compared to text": "OrderDate eq '2026-10-27'",
    "impossible date": "OrderDate eq 2026-13-45",
    "date field compared to timestamp": "OrderDate eq 2026-10-27T09:15:30Z",
    "contains on a date": "contains(OrderDate,'2026')",
    "contains without quotes": "contains(CustomerName,Steel)",
    "contains missing bracket": "contains(CustomerName,'a'",
    "function used as a value": "OverallStatus eq contains(CustomerName,'a')",
    "unexpected character": "OverallStatus eq 'A' ; drop",
}


class TestMalformedFilter:
    @pytest.mark.parametrize("text", BAD_FILTERS.values(), ids=BAD_FILTERS.keys())
    def test_is_rejected_with_invalid_query(self, text):
        with pytest.raises(InvalidQuery) as error:
            run(text)

        assert error.value.target == "$filter"
        assert error.value.message

    def test_is_rejected_even_when_there_are_no_orders(self):
        with pytest.raises(InvalidQuery):
            run("Colour eq 'red'", [])
