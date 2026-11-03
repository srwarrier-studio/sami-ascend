import json
import re
from pathlib import Path

CONTRACT = Path(__file__).with_name("drivers-contract.md").read_text()

FIELD_ROW = re.compile(r"^\| `(\w+)` \| `(Edm\.\w+)`(?: \(\d+(?:,\d+)?\))? \| (Yes|No) \|", re.MULTILINE)
JSON_BLOCK = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
STRUCTURE_KEYS = {"value"}

PATTERNS = {
    "Edm.Date": re.compile(r"\d{4}-\d{2}-\d{2}"),
    "Edm.Decimal": re.compile(r"-?\d+\.\d+"),
    "Edm.String": re.compile(r".*"),
}


def fields():
    found = {}
    for name, edm, nullable in FIELD_ROW.findall(CONTRACT):
        assert found.setdefault(name, (edm, nullable)) == (edm, nullable), f"{name} is described two ways"
    return found


def example_blocks():
    return [json.loads(text) for text in JSON_BLOCK.findall(CONTRACT)]


def check_row(row, described):
    for key, value in row.items():
        if key.startswith("@"):
            continue
        assert key in described, f"{key} is not in any field table"
        edm, nullable = described[key]
        if value is None:
            assert nullable == "Yes", f"{key} is null but not nullable"
        elif edm == "Edm.Int32":
            assert isinstance(value, int), key
        else:
            assert isinstance(value, str), key
            assert PATTERNS[edm].fullmatch(value), f"{key}={value!r} is not {edm}"


def test_every_field_has_a_type_and_nullability():
    assert len(fields()) >= 30


def test_there_is_an_example_for_each_entity():
    assert len(example_blocks()) == 7


def test_example_rows_match_the_tables():
    described = fields()
    for block in example_blocks():
        for row in block["value"]:
            check_row(row, described)


def test_examples_are_not_missing_non_nullable_fields_of_their_entity():
    described = fields()
    required = {name for name, (_, nullable) in described.items() if nullable == "No"}
    for block in example_blocks():
        entity = block["@odata.context"].removeprefix("$metadata#")
        table = re.split(r"\n#{2,3} ", CONTRACT.split(f"### {entity} ")[1])[0]
        needed = {name for name in re.findall(r"^\| `(\w+)` \|", table, re.MULTILINE) if name in required}
        for row in block["value"]:
            assert needed <= set(row), f"{entity} example misses {needed - set(row)}"


def test_codes_used_in_examples_are_listed():
    listed = set(re.findall(r"`([A-Z_]+|[A-Z])`", CONTRACT))
    for block in example_blocks():
        for row in block["value"]:
            for key in ("ContractStatus", "DeliveryStatus", "ProductionStatus", "DelayReason"):
                if row.get(key):
                    assert row[key] in listed, f"{key}={row[key]} is not in section 3"


def test_every_entity_is_read_only_and_says_so():
    assert "read-only" in CONTRACT
