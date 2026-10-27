import json
import re
from pathlib import Path

import pytest

CONTRACT = (Path(__file__).resolve().parents[3] / "docs/sap/sales-contract.md").read_text()
JSON_BLOCK = re.compile(r"```json\n(.*?)\n```", re.DOTALL)


def json_blocks() -> list[dict]:
    return [json.loads(text) for text in JSON_BLOCK.findall(CONTRACT)]


def error_example(code: str, detail_code: str | None = None) -> dict:
    for block in json_blocks():
        error = block.get("error", {})
        if error.get("code") != code:
            continue
        if detail_code is None or detail_code in [d["code"] for d in error.get("details", [])]:
            return block
    pytest.fail(f"no example with code {code} {detail_code or ''}")


def order_example(context: str) -> dict:
    for block in json_blocks():
        if block.get("@odata.context") == context:
            return block
    pytest.fail(f"no example with context {context}")


def same_shape(actual, expected, path="body"):
    if expected is None or actual is None:
        return
    if isinstance(expected, dict):
        assert isinstance(actual, dict), path
        assert list(actual) == list(expected), f"{path}: {list(actual)} != {list(expected)}"
        for key in expected:
            same_shape(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(expected, list):
        assert isinstance(actual, list), path
        if actual and expected:
            same_shape(actual[0], expected[0], f"{path}[0]")
    else:
        assert type(actual) is type(expected), f"{path}: {actual!r} vs {expected!r}"
