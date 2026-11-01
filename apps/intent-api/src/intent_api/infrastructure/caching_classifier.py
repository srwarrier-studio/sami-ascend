from intent_api.domain.entities.decision import Decision
from intent_api.domain.gateways.choice_classifier import ChoiceClassifier


class CachingClassifier(ChoiceClassifier):
    def __init__(self, classifier: ChoiceClassifier):
        self.classifier = classifier
        self.answers: dict[tuple, Decision] = {}

    def choose(self, text: str, instructions: str, choices: dict[str, str]) -> Decision:
        key = (text, instructions, tuple(choices.items()))
        if key not in self.answers:
            self.answers[key] = self.classifier.choose(text, instructions, choices)
        return self.answers[key]
