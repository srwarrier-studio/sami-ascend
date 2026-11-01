from abc import ABC, abstractmethod

from intent_api.domain.entities.decision import Decision


class ChoiceClassifier(ABC):
    @abstractmethod
    def choose(self, text: str, instructions: str, choices: dict[str, str]) -> Decision: ...
