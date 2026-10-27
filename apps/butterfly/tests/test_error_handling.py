from fastapi.testclient import TestClient

from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo
from butterfly.entrypoint.app import create_app
from butterfly.infrastructure.api.odata import ROOT


class BrokenRepo(SalesOrderRepo):
    def list_all(self):
        raise RuntimeError("secret detail")

    def get(self, sales_order):
        raise RuntimeError("secret detail")


class TestUnexpectedError:
    def setup_method(self):
        self.response = TestClient(create_app(BrokenRepo())).get(ROOT + "SalesOrder")

    def test_is_500_with_internal_error_code(self):
        assert self.response.status_code == 500
        assert self.response.json()["error"]["code"] == "INTERNAL_ERROR"

    def test_target_is_the_request_id_from_the_header(self):
        assert self.response.json()["error"]["target"] == self.response.headers["x-request-id"]

    def test_internal_detail_never_reaches_the_client(self):
        assert "secret" not in self.response.text
        assert "Traceback" not in self.response.text
