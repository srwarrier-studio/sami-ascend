from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.gateways.chat_model import ChatModel


class MockChatModel(ChatModel):
    def __init__(self, picks: list[str] | None = None, error: Exception | None = None):
        self.picks = picks or []
        self.error = error
        self.messages: list[str] = []

    def pick_widgets(self, message: str, catalog: list[CatalogEntry]) -> list[str]:
        self.messages.append(message)
        if self.error:
            raise self.error
        return list(self.picks)
