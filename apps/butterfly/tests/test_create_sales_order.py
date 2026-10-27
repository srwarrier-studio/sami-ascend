import copy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from butterfly.application.usecase.create_sales_order import CreateSalesOrder
from butterfly.domain.errors import ValidationFailed
from butterfly.infrastructure.memory.in_memory_master_data_repo import InMemoryMasterDataRepo
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo
from conftest import ORDERS, TODAY

NOW = datetime(2026, 10, 27, 9, 15, 30, 750000, tzinfo=timezone.utc)

VALID_BODY = {
    "SalesOrderType": "OR",
    "SoldToParty": "0000100001",
    "RequestedDeliveryDate": "2026-11-05",
    "TransactionCurrency": "INR",
    "_Item": [
        {"Material": "RM-1001", "Quantity": "50.000", "QuantityUnit": "KG"},
        {"Material": "RM-1002", "Quantity": "25.000", "QuantityUnit": "KG"},
    ],
}


def body(**changes):
    result = copy.deepcopy(VALID_BODY)
    result.update(changes)
    return result


def body_without(*names):
    result = copy.deepcopy(VALID_BODY)
    for name in names:
        del result[name]
    return result


def item_body(**changes):
    item = {"Material": "RM-1001", "Quantity": "50.000", "QuantityUnit": "KG"}
    item.update(changes)
    return body(_Item=[item])


def make(orders=None, now=NOW):
    repo = InMemorySalesOrderRepo(list(ORDERS) if orders is None else orders)
    return repo, CreateSalesOrder(repo, InMemoryMasterDataRepo(), lambda: now)


def problems(request_body, now=NOW):
    repo, use_case = make(now=now)
    before = len(repo.list_all())
    with pytest.raises(ValidationFailed) as error:
        use_case.execute(request_body)
    assert len(repo.list_all()) == before
    return [(d.code, d.target) for d in error.value.details]


class TestCreateSalesOrder:
    def setup_method(self):
        self.repo, self.use_case = make()
        self.order = self.use_case.execute(VALID_BODY)

    def test_gets_the_next_number_after_the_seed(self):
        assert self.order.sales_order == "0000012031"

    def test_is_stored_and_can_be_read_back(self):
        assert self.repo.get("0000012031") == self.order
        assert len(self.repo.list_all()) == len(ORDERS) + 1

    def test_header_comes_from_the_request_and_master_data(self):
        assert self.order.sales_order_type == "OR"
        assert self.order.sold_to_party == "0000100001"
        assert self.order.customer_name == "Acme Industries"
        assert self.order.transaction_currency == "INR"
        assert self.order.requested_delivery_date == date(2026, 11, 5)

    def test_sap_fills_in_status_user_and_order_date(self):
        assert self.order.overall_status == "A"
        assert self.order.created_by_user == "BUTTERFLY"
        assert self.order.order_date == date(2026, 10, 27)

    def test_timestamps_are_now_in_whole_seconds(self):
        assert self.order.creation_date_time == NOW.replace(microsecond=0)
        assert self.order.last_change_date_time == self.order.creation_date_time

    def test_items_are_numbered_10_20_and_belong_to_the_order(self):
        assert [i.sales_order_item for i in self.order.items] == ["000010", "000020"]
        assert {i.sales_order for i in self.order.items} == {"0000012031"}

    def test_item_text_and_amounts_come_from_master_data(self):
        first = self.order.items[0]

        assert first.material_description == "Steel rod 12mm"
        assert first.net_amount == Decimal("62500.00")
        assert self.order.items[1].net_amount == Decimal("62500.00")

    def test_total_is_the_sum_of_the_items(self):
        assert self.order.total_net_amount == Decimal("125000.00")

    def test_second_order_gets_the_next_number(self):
        second = self.use_case.execute(VALID_BODY)

        assert second.sales_order == "0000012032"
        assert self.repo.list_all()[-1] == second

    def test_first_number_in_an_empty_store(self):
        _, use_case = make(orders=[])

        assert use_case.execute(VALID_BODY).sales_order == "0000000001"


class TestAmounts:
    def create(self, **item):
        return make()[1].execute(item_body(**item))

    def test_whole_quantity_is_stored_with_three_decimals(self):
        assert str(self.create(Quantity="50").items[0].quantity) == "50.000"

    def test_fractional_quantity(self):
        assert self.create(Quantity="0.5").items[0].net_amount == Decimal("625.00")

    def test_amount_rounds_half_up_to_two_decimals(self):
        item = self.create(Material="RM-1006", Quantity="0.002", QuantityUnit="EA").items[0]

        assert item.net_amount == Decimal("0.01")

    def test_each_material_uses_its_own_price(self):
        item = self.create(Material="RM-1005", Quantity="2", QuantityUnit="EA").items[0]

        assert item.net_amount == Decimal("190.00")

    def test_many_items_are_numbered_in_steps_of_ten(self):
        items = [{"Material": "RM-1001", "Quantity": "1", "QuantityUnit": "KG"}] * 12
        order = make()[1].execute(body(_Item=items))

        assert order.items[-1].sales_order_item == "000120"
        assert order.total_net_amount == Decimal("15000.00")


class TestDeliveryDate:
    def create(self, value):
        return make()[1].execute(body(RequestedDeliveryDate=value))

    def test_today_is_accepted(self):
        assert self.create("2026-10-27").requested_delivery_date == date(2026, 10, 27)

    def test_future_is_accepted(self):
        assert self.create("2030-01-01").requested_delivery_date == date(2030, 1, 1)

    def test_omitted_is_stored_as_empty(self):
        assert make()[1].execute(body_without("RequestedDeliveryDate")).requested_delivery_date is None

    def test_null_is_stored_as_empty(self):
        assert self.create(None).requested_delivery_date is None

    def test_yesterday_is_rejected(self):
        assert problems(body(RequestedDeliveryDate="2026-10-26")) == [
            ("DELIVERY_DATE_IN_PAST", "RequestedDeliveryDate")
        ]

    def test_today_is_judged_in_utc_at_the_time_of_the_call(self):
        late = datetime(2026, 10, 27, 23, 59, 59, tzinfo=timezone.utc)
        assert problems(body(RequestedDeliveryDate="2026-10-26"), now=late)
        next_day = late + timedelta(seconds=1)
        assert problems(body(RequestedDeliveryDate="2026-10-27"), now=next_day)

    @pytest.mark.parametrize(
        "value", ["05-11-2026", "2026/11/05", "2026-13-01", "2026-02-30", "tomorrow", "", 20261105, True, ["2026-11-05"]]
    )
    def test_wrong_format_is_field_invalid(self, value):
        assert problems(body(RequestedDeliveryDate=value)) == [
            ("FIELD_INVALID", "RequestedDeliveryDate")
        ]


class TestRequiredFields:
    @pytest.mark.parametrize("name", ["SalesOrderType", "SoldToParty", "TransactionCurrency"])
    def test_missing(self, name):
        assert problems(body_without(name)) == [("FIELD_REQUIRED", name)]

    @pytest.mark.parametrize("name", ["SalesOrderType", "SoldToParty", "TransactionCurrency"])
    @pytest.mark.parametrize("value", [None, "", "   "])
    def test_null_or_blank(self, name, value):
        assert problems(body(**{name: value})) == [("FIELD_REQUIRED", name)]

    @pytest.mark.parametrize("name", ["Material", "Quantity", "QuantityUnit"])
    def test_item_field_missing(self, name):
        item = {"Material": "RM-1001", "Quantity": "5", "QuantityUnit": "KG"}
        del item[name]

        assert problems(body(_Item=[item])) == [("FIELD_REQUIRED", f"_Item/0/{name}")]


class TestFieldFormats:
    @pytest.mark.parametrize(
        "name,value",
        [
            ("SalesOrderType", "ORDER1"),
            ("SalesOrderType", 5),
            ("SoldToParty", "00001000011"),
            ("SoldToParty", 100001),
            ("TransactionCurrency", "INRINR"),
            ("TransactionCurrency", ["INR"]),
        ],
    )
    def test_too_long_or_not_text(self, name, value):
        assert problems(body(**{name: value})) == [("FIELD_INVALID", name)]

    def test_any_short_order_type_is_accepted(self):
        assert make()[1].execute(body(SalesOrderType="ZZ")).sales_order_type == "ZZ"


class TestReferenceData:
    def test_unknown_customer(self):
        assert problems(body(SoldToParty="0000999999")) == [("CUSTOMER_UNKNOWN", "SoldToParty")]

    def test_customer_number_must_match_exactly(self):
        assert problems(body(SoldToParty="100001")) == [("CUSTOMER_UNKNOWN", "SoldToParty")]

    def test_unknown_currency(self):
        assert problems(body(TransactionCurrency="USD")) == [("CURRENCY_INVALID", "TransactionCurrency")]

    def test_currency_is_case_sensitive(self):
        assert problems(body(TransactionCurrency="inr")) == [("CURRENCY_INVALID", "TransactionCurrency")]

    def test_unknown_material(self):
        assert problems(item_body(Material="RM-9999")) == [("MATERIAL_UNKNOWN", "_Item/0/Material")]

    def test_unit_that_is_not_the_materials_unit(self):
        assert problems(item_body(QuantityUnit="EA")) == [("UNIT_INVALID", "_Item/0/QuantityUnit")]

    def test_unit_is_not_checked_when_the_material_is_unknown(self):
        assert problems(item_body(Material="RM-9999", QuantityUnit="XX")) == [
            ("MATERIAL_UNKNOWN", "_Item/0/Material")
        ]


class TestQuantity:
    @pytest.mark.parametrize("value", ["0", "0.000", "-1", "-0.5"])
    def test_zero_or_negative(self, value):
        assert problems(item_body(Quantity=value)) == [("QUANTITY_NOT_POSITIVE", "_Item/0/Quantity")]

    @pytest.mark.parametrize(
        "value", ["abc", "1,5", "1.2345", "1e2", "+5", " 5", "5 ", ".5", "5.", 50, 50.5, True, "12345678901"]
    )
    def test_not_a_decimal_string_with_up_to_three_decimals(self, value):
        assert problems(item_body(Quantity=value)) == [("FIELD_INVALID", "_Item/0/Quantity")]

    def test_smallest_quantity_is_accepted(self):
        assert make()[1].execute(item_body(Quantity="0.001")).items[0].quantity == Decimal("0.001")


class TestItems:
    @pytest.mark.parametrize("value", [None, []])
    def test_missing_or_empty(self, value):
        assert problems(body(_Item=value)) == [("NO_ITEMS", "_Item")]

    def test_omitted(self):
        assert problems(body_without("_Item")) == [("NO_ITEMS", "_Item")]

    @pytest.mark.parametrize("value", ["RM-1001", {"Material": "RM-1001"}, 5])
    def test_not_a_list(self, value):
        assert problems(body(_Item=value)) == [("FIELD_INVALID", "_Item")]

    @pytest.mark.parametrize("entry", ["RM-1001", 5, None, ["a"]])
    def test_item_that_is_not_an_object(self, entry):
        assert problems(body(_Item=[entry])) == [("FIELD_INVALID", "_Item/0")]

    def test_error_in_the_second_item_has_index_one(self):
        good = {"Material": "RM-1001", "Quantity": "5", "QuantityUnit": "KG"}
        bad = {"Material": "RM-1001", "Quantity": "0", "QuantityUnit": "KG"}

        assert problems(body(_Item=[good, bad])) == [("QUANTITY_NOT_POSITIVE", "_Item/1/Quantity")]

    def test_one_bad_item_stops_the_whole_order(self):
        good = {"Material": "RM-1001", "Quantity": "5", "QuantityUnit": "KG"}
        bad = {"Material": "RM-9999", "Quantity": "5", "QuantityUnit": "KG"}

        assert problems(body(_Item=[good, bad, good]))


class TestFieldsTheCallerMayNotSend:
    @pytest.mark.parametrize(
        "name",
        ["SalesOrder", "CustomerName", "OrderDate", "TotalNetAmount", "OverallStatus",
         "CreatedByUser", "CreationDateTime", "LastChangeDateTime", "Colour"],
    )
    def test_header_field(self, name):
        assert problems(body(**{name: "x"})) == [("FIELD_NOT_ALLOWED", name)]

    @pytest.mark.parametrize("name", ["SalesOrderItem", "NetAmount", "MaterialDescription", "SalesOrder", "Colour"])
    def test_item_field(self, name):
        assert problems(item_body(**{name: "x"})) == [("FIELD_NOT_ALLOWED", f"_Item/0/{name}")]

    def test_field_names_are_case_sensitive(self):
        result = problems(body(soldtoparty="0000100001"))

        assert ("FIELD_NOT_ALLOWED", "soldtoparty") in result


class TestSeveralProblemsAtOnce:
    def test_all_are_returned_in_one_failure(self):
        everything_wrong = {
            "OverallStatus": "C",
            "SoldToParty": "0000999999",
            "RequestedDeliveryDate": "2020-01-01",
            "TransactionCurrency": "USD",
            "_Item": [
                {"Material": "RM-9999", "Quantity": "1", "QuantityUnit": "KG"},
                {"Material": "RM-1001", "Quantity": "0", "QuantityUnit": "EA"},
            ],
        }

        assert problems(everything_wrong) == [
            ("FIELD_NOT_ALLOWED", "OverallStatus"),
            ("FIELD_REQUIRED", "SalesOrderType"),
            ("CUSTOMER_UNKNOWN", "SoldToParty"),
            ("DELIVERY_DATE_IN_PAST", "RequestedDeliveryDate"),
            ("CURRENCY_INVALID", "TransactionCurrency"),
            ("MATERIAL_UNKNOWN", "_Item/0/Material"),
            ("QUANTITY_NOT_POSITIVE", "_Item/1/Quantity"),
            ("UNIT_INVALID", "_Item/1/QuantityUnit"),
        ]

    def test_every_problem_has_a_readable_message(self):
        _, use_case = make()
        with pytest.raises(ValidationFailed) as error:
            use_case.execute({})

        assert all(detail.message for detail in error.value.details)

    def test_empty_body_reports_every_required_field_and_no_items(self):
        assert problems({}) == [
            ("FIELD_REQUIRED", "SalesOrderType"),
            ("FIELD_REQUIRED", "SoldToParty"),
            ("FIELD_REQUIRED", "TransactionCurrency"),
            ("NO_ITEMS", "_Item"),
        ]

    def test_nothing_is_stored_after_a_failure(self):
        repo, use_case = make()
        with pytest.raises(ValidationFailed):
            use_case.execute(body(SoldToParty="0000999999"))

        assert repo.next_number() == "0000012031"
