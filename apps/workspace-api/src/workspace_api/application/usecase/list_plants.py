from dataclasses import replace

from workspace_api.application.master_data_scope import company_of, plants_of
from workspace_api.domain.entities.master_data import Plant
from workspace_api.domain.gateways.master_data_gateway import MasterDataGateway


class ListPlants:
    def __init__(self, gateway: MasterDataGateway, plants_by_company: dict[str, tuple[str, ...]]):
        self.gateway = gateway
        self.plants_by_company = plants_by_company

    def execute(self, companies: list[str]) -> list[Plant]:
        found = self.gateway.plants(plants_of(companies, self.plants_by_company))
        return [replace(plant, company_code=company_of(plant.plant, self.plants_by_company)) for plant in found]
