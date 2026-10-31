from abc import ABC, abstractmethod
from datetime import date

from sami_agents.domain.entities.finding import MemberChange, Window


class DataSource(ABC):
    @abstractmethod
    def records(self, token: str, record_type: str, key_field: str, key: str, start: date | None, end: date | None) -> list[dict]: ...

    @abstractmethod
    def member_change(self, token: str, metric: str, dimension: str, key: str, window: Window) -> MemberChange | None: ...
