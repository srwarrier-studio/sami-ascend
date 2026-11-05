from workspace_api.domain.entities.master_data import BusinessPartner, Material, MaterialPage, PartnerPage, Plant
from workspace_api.domain.gateways.master_data_gateway import MasterDataGateway


class MockMasterDataGateway(MasterDataGateway):
    def __init__(self, plants: list[Plant] | None = None, materials: list[Material] | None = None, customers: list[BusinessPartner] | None = None, suppliers: list[BusinessPartner] | None = None):
        self.known_plants = plants or []
        self.known_materials = materials or []
        self.known_customers = customers or []
        self.known_suppliers = suppliers or []

    def plants(self, plants: list[str]) -> list[Plant]:
        return [p for p in self.known_plants if p.plant in plants]

    def materials(self, query: str | None, plants: list[str], top: int, skip: int) -> MaterialPage:
        found = [m for m in self.known_materials if set(m.plants) & set(plants) and (not query or m.material.startswith(query) or query in m.description)]
        return MaterialPage(found[skip : skip + top], len(found))

    def customers(self, query: str | None, companies: list[str], top: int, skip: int) -> PartnerPage:
        return self.partners(self.known_customers, query, companies, top, skip)

    def suppliers(self, query: str | None, companies: list[str], top: int, skip: int) -> PartnerPage:
        return self.partners(self.known_suppliers, query, companies, top, skip)

    def partners(self, known: list[BusinessPartner], query: str | None, companies: list[str], top: int, skip: int) -> PartnerPage:
        found = [p for p in known if set(p.company_codes) & set(companies) and (not query or p.number.startswith(query) or query in p.name)]
        return PartnerPage(found[skip : skip + top], len(found))
