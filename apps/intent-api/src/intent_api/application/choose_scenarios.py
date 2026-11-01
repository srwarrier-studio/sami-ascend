import re

from intent_api.domain.entities.scenario import Library
from intent_api.domain.entities.selection import Selected
from intent_api.domain.gateways.choice_classifier import ChoiceClassifier

NOTHING = "nothing"
QUESTION = "What does the manager want to know?"
CLAUSE_BREAKS = re.compile(r"\s+and\s+|,\s*|;\s*|\s+then\s+")


def split_clauses(text: str) -> list[str]:
    return [clause for clause in CLAUSE_BREAKS.split(text) if clause.strip()]


class ChooseScenarios:
    def __init__(self, classifier: ChoiceClassifier, library: Library, max_scenarios: int = 4, min_probability: float = 0.0):
        self.classifier = classifier
        self.library = library
        self.max_scenarios = max_scenarios
        self.min_probability = min_probability

    def execute(self, text: str, domain: str) -> list[Selected]:
        choices = {scenario.id: scenario.description for scenario in self.library.scenarios.values() if scenario.domain == domain}
        choices[NOTHING] = "nothing about figures is asked"
        best: dict[str, Selected] = {}
        for clause in split_clauses(text):
            decision = self.classifier.choose(clause, QUESTION, choices)
            if decision.choice == NOTHING or decision.probability < self.min_probability:
                continue
            if decision.choice not in best or decision.probability > best[decision.choice].probability:
                best[decision.choice] = Selected(decision.choice, decision.probability, clause)
        for selected in list(best.values()):
            for covered in self.library.scenarios[selected.scenario].covers:
                best.pop(covered, None)
        return sorted(best.values(), key=lambda selected: -selected.probability)[: self.max_scenarios]
