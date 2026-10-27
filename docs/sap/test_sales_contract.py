import json
import re
from pathlib import Path

CONTRACT = Path(__file__).with_name("sales-contract.md").read_text()

FIELD_ROW = re.compile(r"^\| `(\w+)` \| `(Edm\.\w+)`", re.MULTILINE)
JSON_BLOCK = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
STRUCTURE_KEYS = {"value", "_Item"}

PATTERNS = {
    "Edm.Date": re.compile(r"\d{4}-\d{2}-\d{2}"),
    "Edm.DateTimeOffset": re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"),
    "Edm.Decimal": re.compile(r"-?\d+\.\d+"),
    "Edm.String": re.compile(r".*"),
}


def field_types():
    types = {}
    for name, edm in FIELD_ROW.findall(CONTRACT):
        assert types.setdefault(name, edm) == edm, f"{name} has two types"
    return types


def example_blocks():
    blocks = [json.loads(text) for text in JSON_BLOCK.findall(CONTRACT)]
    return [b for b in blocks if b.get("error", {}).get("code") != "string"]


def check_value(name, edm, value):
    if edm == "Edm.Int32":
        assert isinstance(value, int) and not isinstance(value, bool), name
    else:
        assert isinstance(value, str), name
        assert PATTERNS[edm].fullmatch(value), f"{name}={value!r} is not {edm}"


def check_node(node, types):
    if isinstance(node, list):
        for item in node:
            check_node(item, types)
        return
    for key, value in node.items():
        if key.startswith("@"):
            continue
        if key in STRUCTURE_KEYS:
            check_node(value, types)
            continue
        assert key in types, f"{key} is not in any field table"
        check_value(key, types[key], value)


def test_every_field_has_a_type():
    assert len(field_types()) >= 21


def test_examples_exist():
    assert len(example_blocks()) >= 10


def test_example_fields_match_the_tables():
    types = field_types()
    for block in example_blocks():
        if "error" not in block:
            check_node(block, types)


def test_errors_follow_the_error_format():
    errors = [b["error"] for b in example_blocks() if "error" in b]
    assert len(errors) >= 6
    for error in errors:
        assert re.fullmatch(r"[A-Z_]+", error["code"])
        assert error["message"]
        for detail in error.get("details", []):
            assert re.fullmatch(r"[A-Z_]+", detail["code"])
            assert detail["message"] and detail["target"]


def test_detail_codes_are_listed_in_the_contract():
    listed = set(re.findall(r"`([A-Z_]{5,})`", CONTRACT))
    for block in example_blocks():
        for detail in block.get("error", {}).get("details", []):
            assert detail["code"] in listed
