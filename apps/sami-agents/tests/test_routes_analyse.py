import pytest
from fastapi.testclient import TestClient
from test_answer_question import answerer, source
from test_routes_chat import SECRET, token_with
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from sami_agents.entrypoint.app import create_app
from sami_agents.infrastructure.settings import Settings

URL = "/v1/agents/analyse"


def client(roles=None, data=None):
    analyst = answerer(data or source())
    app = create_app(Settings(jwt_secret=SECRET, _env_file=None), analyst=analyst)
    test = TestClient(app)
    if roles is not None:
        test.cookies.set(ACCESS_TOKEN_COOKIE, token_with(roles))
    return test


class TestAccess:
    def test_no_cookie_is_401_and_other_roles_are_403(self):
        assert client().post(URL, json={"question": "why did sales fall in August"}).status_code == 401
        assert client(["sales"]).post(URL, json={"question": "why did sales fall in August"}).status_code == 403

    @pytest.mark.parametrize("roles", [["management"], ["admin"]])
    def test_management_and_admin_pass(self, roles):
        assert client(roles).post(URL, json={"question": "show me sales"}).status_code == 200


class TestTheAnswer:
    def test_a_readable_question_returns_the_json_answer(self):
        # the route uses today's real date, so ask about a month long gone
        body = client(["management"]).post(URL, json={"question": "Why did sales fall in August 2025?"}).json()
        assert body["readable"] is True and body["question"]["month"] == "2025-08"
        assert [b["type"] for b in body["blocks"]][0] == "text"

    def test_a_figure_question_returns_its_intent(self):
        body = client(["management"]).post(URL, json={"question": "What were the sales for August 2025?"}).json()
        assert body["question"]["intent"] == "figure" and [b["type"] for b in body["blocks"]] == ["text", "trend"]

    def test_an_unreadable_question_is_200_with_the_help_text(self):
        body = client(["management"]).post(URL, json={"question": "tell me a joke"}).json()
        assert (body["readable"], body["analysis"]) == (False, None)

    def test_the_question_is_trimmed_and_must_have_text(self):
        assert client(["management"]).post(URL, json={"question": "   "}).status_code == 422
        assert client(["management"]).post(URL, json={"question": ""}).status_code == 422
        assert client(["management"]).post(URL, json={"question": "x" * 501}).status_code == 422
        assert client(["management"]).post(URL, json={}).status_code == 422

    def test_data_that_cannot_be_read_is_503_and_nothing_partial(self):
        data = source()
        data.fail()
        response = client(["management"], data).post(URL, json={"question": "Why did sales fall in August 2025?"})
        assert (response.status_code, response.json()) == (503, {"code": "DATA_UNAVAILABLE"})

    def test_the_request_id_is_on_the_response_and_the_users_token_goes_to_the_data(self):
        data = source()
        response = client(["management"], data).post(URL, json={"question": "Why did sales fall in August 2025?"})
        assert response.headers["x-request-id"] and len(set(data.tokens)) == 1 and data.tokens[0] != "tok"


class TestFollowUpContext:
    def post(self, question, context):
        return client(["management"]).post(URL, json={"question": question, "context": context})

    def test_the_context_fills_the_metric_and_month_a_follow_up_leaves_out(self):
        body = self.post("give me the reason for the decline", {"metric": "sales", "month": "2025-08"}).json()
        assert body["readable"] is True and body["question"]["metric"] == "sales" and body["question"]["month"] == "2025-08"

    def test_without_it_the_same_question_is_unreadable(self):
        assert client(["management"]).post(URL, json={"question": "give me the reason for the decline"}).json()["problem"] == "unreadable"

    @pytest.mark.parametrize("context", [{"metric": "sales"}, {"metric": "sales", "month": "August"}, {"metric": "sales", "month": "2025-13"}, {"metric": "Sales; DROP", "month": "2025-08"}, "x"])
    def test_a_bad_context_is_422(self, context):
        assert self.post("why?", context).status_code == 422
