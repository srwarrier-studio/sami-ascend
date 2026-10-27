import json
import logging

from structured_logging import setup_logging
from structured_logging.request_id import request_id_var


def read_line(capsys) -> dict:
    return json.loads(capsys.readouterr().out)


def test_line_has_the_agreed_fields(capsys):
    setup_logging("demo")

    logging.getLogger("app").info("hello")

    line = read_line(capsys)
    assert line["level"] == "INFO"
    assert line["service"] == "demo"
    assert line["message"] == "hello"
    assert line["request_id"] is None
    assert line["timestamp"].endswith("Z")


def test_newlines_stay_on_one_line(capsys):
    setup_logging("demo")

    logging.getLogger("app").info("a\nb")

    out = capsys.readouterr().out
    assert len(out.strip().splitlines()) == 1
    assert json.loads(out)["message"] == "a\nb"


def test_exception_is_included(capsys):
    setup_logging("demo")

    try:
        raise ValueError("boom")
    except ValueError:
        logging.getLogger("app").exception("failed")

    assert "ValueError: boom" in read_line(capsys)["exception"]


def test_request_id_is_included_when_set(capsys):
    setup_logging("demo")
    token = request_id_var.set("abc-123")

    logging.getLogger("app").info("hello")
    request_id_var.reset(token)

    assert read_line(capsys)["request_id"] == "abc-123"


def test_uvicorn_logs_use_the_same_format(capsys):
    setup_logging("demo")

    logging.getLogger("uvicorn.error").info("started")

    assert read_line(capsys)["message"] == "started"
