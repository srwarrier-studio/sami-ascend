from sami_agents.domain.entities.case import Decision
from sami_agents.domain.errors import CaseModelUnavailable
from sami_agents.domain.gateways.case_model import CaseModel


class MockCaseModel(CaseModel):
    def __init__(self, answers: dict[str, tuple[str, float]] | None = None, failing: bool = False):
        self.answers = answers or {}
        self.failing = failing
        self.calls: list[tuple[str, str]] = []

    def decide(self, text: str, name: str, instructions: str, choices: dict[str, str]) -> Decision:
        self.calls.append((name, text))
        if self.failing or name not in self.answers:
            raise CaseModelUnavailable(name)
        choice, confidence = self.answers[name]
        return Decision(choice, confidence)
