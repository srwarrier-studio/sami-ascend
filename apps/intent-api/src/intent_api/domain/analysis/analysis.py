from dataclasses import dataclass, field
from decimal import Decimal

from intent_api.domain.analysis.finding import Step, Window
from intent_api.domain.analysis.measure import MoverRow
from intent_api.domain.analysis.question import Question


@dataclass(frozen=True)
class Cause:
    source: str
    kind: str
    key: str


@dataclass
class Finding:
    dimension: str
    key: str
    name: str
    current: Decimal
    previous: Decimal
    change: Decimal
    change_percent: Decimal | None
    share_percent: Decimal | None
    kind: str
    unit: str | None = None
    volume_effect: Decimal | None = None
    price_effect: Decimal | None = None
    paths: list[tuple[Step, ...]] = field(default_factory=list)
    causes: list[Cause] = field(default_factory=list)
    explained: bool = False


@dataclass
class Analysis:
    question: Question
    window: Window
    currency: str
    current: Decimal
    previous: Decimal
    change: Decimal
    change_percent: Decimal | None
    significant: bool
    findings: list[Finding] = field(default_factory=list)
    offsets: list[Finding] = field(default_factory=list)
    tables: dict[str, list[MoverRow]] = field(default_factory=dict)
    explained_percent: Decimal = Decimal(0)
    unexplained_percent: Decimal = Decimal(100)
    limits: list[str] = field(default_factory=list)
    other_currencies: list[tuple[str, Decimal | None]] = field(default_factory=list)
