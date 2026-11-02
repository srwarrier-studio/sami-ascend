import re
import tomllib
from pathlib import Path

from intent_api.domain.entities.registry_info import RecordInfo, RegistryInfo

FIELD_ROW = re.compile(r"^\| `(\w+)` \| `Edm\.\w+`", re.MULTILINE)
ENTITY_HEADING = re.compile(r"^### (\w+) \(key", re.MULTILINE)


def load_registry_info(path: Path) -> RegistryInfo:
    data = tomllib.loads(path.read_text())
    metrics = {name: set(body.get("by", {})) for name, body in data.get("metric", {}).items()}
    records = {name: RecordInfo(body["entity"], tuple(body["key_fields"])) for name, body in data.get("record", {}).items()}
    return RegistryInfo(metrics, records)


def load_contract_fields(folder: Path) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    for path in sorted(folder.glob("*-contract.md")):
        text = path.read_text()
        headings = list(ENTITY_HEADING.finditer(text))
        for heading, following in zip(headings, [*headings[1:], None]):
            end = following.start() if following else len(text)
            fields[heading.group(1)] = FIELD_ROW.findall(text[heading.end():end])
    return fields
