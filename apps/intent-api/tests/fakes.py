from intent_api.domain.entities.decision import Decision
from intent_api.domain.errors import ClassifierUnavailable
from intent_api.domain.gateways.choice_classifier import ChoiceClassifier


class FakeClassifier(ChoiceClassifier):
    def __init__(self, decision: Decision | None = None, by_text: dict[str, Decision] | None = None):
        self.decision = decision
        self.by_text = by_text or {}
        self.calls = []

    def choose(self, text: str, instructions: str, choices: dict[str, str]) -> Decision:
        self.calls.append((text, instructions, choices))
        if text in self.by_text:
            return self.by_text[text]
        if self.decision is None:
            raise ClassifierUnavailable("down")
        return self.decision
