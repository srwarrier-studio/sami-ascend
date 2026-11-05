from butterfly.domain.entities.master_data import PLANT_COMPANIES, Plant, Product, Supplier
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.inventory_master import GROUP_OF

FINISHED = "FERT"
RAW = "ROH"


def products() -> list[Product]:
    sold = [
        Product(material_id, description, unit, GROUP_OF.get(material_id, ""), FINISHED, company.code)
        for company in COMPANIES
        for material_id, description, unit, _ in company.materials
    ]
    raw = [
        Product(material_id, description, unit, GROUP_OF.get(material_id, ""), RAW, company.code)
        for company in COMPANIES
        for material_id, description, unit, *_ in company.raw_materials
    ]
    return sold + raw


def suppliers() -> list[Supplier]:
    return [Supplier(supplier_id, name, company.code) for company in COMPANIES for supplier_id, name in company.suppliers]


def plants() -> list[Plant]:
    names = {company.code: company.name for company in COMPANIES}
    return [Plant(plant, f"{names[code]} plant", code) for plant, code in PLANT_COMPANIES.items()]
