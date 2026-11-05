from workspace_api.application.master_data_scope import checked
from workspace_api.domain.entities.master_data import PartnerPage
from workspace_api.domain.gateways.master_data_gateway import MasterDataGateway


class SearchCustomers:
    def __init__(self, gateway: MasterDataGateway):
        self.gateway = gateway

    def execute(self, query: str | None, companies: list[str], top: int, skip: int) -> PartnerPage:
        return self.gateway.customers(checked(query, top, skip), companies, top, skip)


class SearchSuppliers:
    def __init__(self, gateway: MasterDataGateway):
        self.gateway = gateway

    def execute(self, query: str | None, companies: list[str], top: int, skip: int) -> PartnerPage:
        return self.gateway.suppliers(checked(query, top, skip), companies, top, skip)
