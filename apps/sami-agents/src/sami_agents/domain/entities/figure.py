from dataclasses import dataclass
from decimal import Decimal

from sami_agents.domain.entities.finding import Window
from sami_agents.domain.entities.question import Question


@dataclass
class Figure:
    question: Question
    window: Window
    currency: str
    current: Decimal
    previous: Decimal
    change: Decimal
    change_percent: Decimal | None
    significant: bool
    so_far: bool
