from intent_api.domain.entities.decision import Decision
from intent_api.domain.gateways.choice_classifier import ChoiceClassifier

OTHER = "Other"
QUESTION = "Which department should handle this?"
OTHER_DESCRIPTION = "everything else"


class ReadDomain:
    def __init__(self, classifier: ChoiceClassifier, domains: dict[str, str]):
        self.classifier = classifier
        self.choices = {**domains, OTHER: OTHER_DESCRIPTION}

    def execute(self, text: str) -> Decision:
        return self.classifier.choose(text, QUESTION, self.choices)
