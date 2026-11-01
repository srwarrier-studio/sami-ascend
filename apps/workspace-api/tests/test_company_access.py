import pytest

from workspace_api.infrastructure.mock_sales_order_gateway import MockSalesOrderGateway

from test_routes_access import VALID_BODY, make_client

URL = "/v1/workspace/sales-orders"


class TestOrdersAreForTheUsersCompanies:
    def test_an_order_for_a_company_of_the_user_is_created_with_it(self):
        response = make_client(MockSalesOrderGateway(), ["sales"], ["sabinsa"]).post(URL, json=VALID_BODY)
        assert response.status_code == 201
        assert (response.json()["company_code"], response.json()["country"]) == ("INA1", "IN")

    def test_a_user_with_several_companies_can_use_each_of_them(self):
        gateway = MockSalesOrderGateway()
        client = make_client(gateway, ["sales"], ["sabinsa", "organica"])
        assert client.post(URL, json=VALID_BODY).status_code == 201
        assert client.post(URL, json={**VALID_BODY, "company_code": "INA3"}).status_code == 201
        assert [o.company_code for o in gateway.orders] == ["INA1", "INA3"]

    @pytest.mark.parametrize("companies", [["organica"], ["neutraceuticals", "organica"], []])
    def test_a_company_the_user_does_not_have_is_403_and_nothing_is_sent(self, companies):
        gateway = MockSalesOrderGateway()
        response = make_client(gateway, ["sales"], companies).post(URL, json=VALID_BODY)
        assert response.status_code == 403
        assert response.json()["code"] == "COMPANY_NOT_ALLOWED"
        assert gateway.orders == []

    def test_an_unknown_company_code_is_403_too(self):
        response = make_client(MockSalesOrderGateway(), ["sales"], ["sabinsa"]).post(URL, json={**VALID_BODY, "company_code": "ZZZZ"})
        assert response.status_code == 403

    def test_the_company_code_is_required(self):
        body = {key: value for key, value in VALID_BODY.items() if key != "company_code"}
        assert make_client(MockSalesOrderGateway(), ["sales"], ["sabinsa"]).post(URL, json=body).status_code == 422

    def test_a_code_longer_than_four_characters_is_422(self):
        assert make_client(MockSalesOrderGateway(), ["sales"], ["sabinsa"]).post(URL, json={**VALID_BODY, "company_code": "INA10"}).status_code == 422


class TestTheListShowsOnlyTheUsersCompanies:
    def gateway_with_two_companies(self):
        gateway = MockSalesOrderGateway()
        writer = make_client(gateway, ["sales"], ["sabinsa", "organica"])
        writer.post(URL, json=VALID_BODY)
        writer.post(URL, json={**VALID_BODY, "company_code": "INA3"})
        return gateway

    def test_a_user_sees_only_the_orders_of_their_own_companies(self):
        gateway = self.gateway_with_two_companies()
        orders = make_client(gateway, ["sales"], ["sabinsa"]).get(URL).json()["orders"]
        assert [o["company_code"] for o in orders] == ["INA1"]

    def test_a_user_with_both_companies_sees_both(self):
        gateway = self.gateway_with_two_companies()
        body = make_client(gateway, ["sales"], ["sabinsa", "organica"]).get(URL).json()
        assert body["total"] == 2

    def test_a_user_with_no_company_sees_nothing(self):
        gateway = self.gateway_with_two_companies()
        assert make_client(gateway, ["sales"], []).get(URL).json() == {"orders": [], "total": 0}
