import json
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from structured_logging import RequestIdMiddleware, get_request_id, setup_logging

app = FastAPI()
app.add_middleware(RequestIdMiddleware)


@app.get("/ping")
def ping():
    logging.getLogger("app").info("inside")
    return {"request_id": get_request_id()}


def log_lines(capsys) -> list[dict]:
    return [json.loads(line) for line in capsys.readouterr().out.splitlines()]


def test_request_without_header_gets_generated_id(capsys):
    setup_logging("demo")

    response = TestClient(app).get("/ping")

    request_id = response.headers["x-request-id"]
    assert response.json()["request_id"] == request_id
    assert len(request_id) == 36
    assert all(line["request_id"] == request_id for line in log_lines(capsys))


def test_valid_incoming_id_is_kept():
    response = TestClient(app).get("/ping", headers={"X-Request-ID": "abc-123_X"})

    assert response.headers["x-request-id"] == "abc-123_X"


def test_unsafe_incoming_ids_are_replaced():
    client = TestClient(app)

    for bad in ["x" * 65, "has space", "a;b", "a\tb"]:
        response = client.get("/ping", headers={"X-Request-ID": bad})
        assert response.headers["x-request-id"] != bad
        assert len(response.headers["x-request-id"]) == 36


def test_access_line_has_method_path_status_and_no_secrets(capsys):
    setup_logging("demo")

    TestClient(app).get(
        "/ping?token=secret", headers={"Cookie": "access_token=jwt", "Authorization": "Bearer x"}
    )

    out = capsys.readouterr().out
    access = [json.loads(line) for line in out.splitlines() if '"GET' in line][0]
    assert access["message"].startswith("GET /ping 200 ")
    assert "secret" not in out and "jwt" not in out and "Bearer" not in out


def test_unhandled_error_is_logged_as_500(capsys):
    setup_logging("demo")
    failing = FastAPI()
    failing.add_middleware(RequestIdMiddleware)

    @failing.get("/boom")
    def boom():
        raise RuntimeError("x")

    try:
        TestClient(failing).get("/boom")
    except RuntimeError:
        pass

    assert any(
        line["message"].startswith("GET /boom 500 ") for line in log_lines(capsys)
    )


def test_request_id_is_null_after_the_request():
    TestClient(app).get("/ping")

    assert get_request_id() is None
