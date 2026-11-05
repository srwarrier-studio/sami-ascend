import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

SPECS = Path(os.environ.get("BUTTERFLY_STANDARD_SPECS", Path(__file__).resolve().parents[7] / "docs" / "sap" / "standard"))
V4_METADATA = SPECS / "api_salesorder-v4" / "metadata.xml"
V2_METADATA = SPECS / "api_sales_order_srv-v2" / "metadata.xml"
REQUISITION_METADATA = SPECS / "api_purchaserequisition_2" / "metadata.xml"
PRODUCT_METADATA = SPECS / "api_product" / "metadata.xml"
PLANT_METADATA = SPECS / "api_plant_2" / "metadata.xml"
PARTNER_METADATA = SPECS / "api_business_partner-v2" / "metadata.xml"


@dataclass(frozen=True)
class EntityType:
    properties: list[tuple[str, str]]
    navigation: list[str]

    def names(self) -> list[str]:
        return [name for name, _ in self.properties]


@dataclass(frozen=True)
class Metadata:
    path: Path
    types: dict[str, EntityType]
    sets: dict[str, str]

    def content(self) -> bytes:
        return self.path.read_bytes()


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def load(path: Path) -> Metadata:
    root = ET.parse(path).getroot()
    types = {}
    sets = {}
    for element in root.iter():
        kind = local(element.tag)
        if kind == "EntityType":
            types[element.get("Name")] = EntityType(
                [(p.get("Name"), p.get("Type")) for p in element if local(p.tag) == "Property"],
                [n.get("Name") for n in element if local(n.tag) == "NavigationProperty"],
            )
        elif kind == "EntitySet":
            sets[element.get("Name")] = element.get("EntityType").rsplit(".", 1)[-1]
    return Metadata(path, types, sets)
