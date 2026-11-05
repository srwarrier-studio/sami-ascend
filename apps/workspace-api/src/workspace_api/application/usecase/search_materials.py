from workspace_api.application.master_data_scope import checked, plants_of
from workspace_api.domain.entities.master_data import MaterialPage
from workspace_api.domain.errors import CompanyNotAllowed
from workspace_api.domain.gateways.master_data_gateway import MasterDataGateway


class SearchMaterials:
    def __init__(self, gateway: MasterDataGateway, plants_by_company: dict[str, tuple[str, ...]]):
        self.gateway = gateway
        self.plants_by_company = plants_by_company

    def execute(self, query: str | None, plant: str | None, companies: list[str], top: int, skip: int) -> MaterialPage:
        text = checked(query, top, skip)
        mine = plants_of(companies, self.plants_by_company)
        if plant is not None and plant not in mine:
            raise CompanyNotAllowed(plant)
        return self.gateway.materials(text, [plant] if plant else mine, top, skip)
