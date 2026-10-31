from sami_agents.domain.gateways.reply_writer import ReplyWriter


class MockReplyWriter(ReplyWriter):
    def __init__(self, text: str = "Here you go.", error: Exception | None = None):
        self.text = text
        self.error = error
        self.calls: list[tuple[str, list[str], str | None]] = []

    def write(self, message: str, titles: list[str], board_name: str | None) -> str:
        self.calls.append((message, titles, board_name))
        if self.error:
            raise self.error
        return self.text
