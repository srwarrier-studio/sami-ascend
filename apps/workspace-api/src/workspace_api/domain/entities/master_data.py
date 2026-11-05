from dataclasses import dataclass, field


@dataclass(frozen=True)
class Plant:
    plant: str
    name: str
    company_code: str = ""


@dataclass(frozen=True)
class Material:
    material: str
    description: str
    unit: str
    iso_unit: str
    material_group: str
    material_type: str
    plants: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BusinessPartner:
    number: str
    name: str
    company_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MaterialPage:
    materials: list[Material]
    total: int


@dataclass(frozen=True)
class PartnerPage:
    partners: list[BusinessPartner]
    total: int
