from sami_agents.application.plan_chat import PlanChat
from sami_agents.domain.gateways.catalog_source import CatalogSource


class AnswerChat:
    def __init__(self, catalog_source: CatalogSource, plan_chat: PlanChat):
        self.catalog_source = catalog_source
        self.plan_chat = plan_chat

    def execute(self, message: str, access_token: str) -> str:
        return self.plan_chat.execute(message, self.catalog_source.entries(access_token))
