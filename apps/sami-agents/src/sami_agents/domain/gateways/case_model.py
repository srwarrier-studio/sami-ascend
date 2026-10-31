from abc import ABC, abstractmethod

from sami_agents.domain.entities.case import Decision


class CaseModel(ABC):
    @abstractmethod
    def decide(self, text: str, name: str, instructions: str, choices: dict[str, str]) -> Decision: ...
