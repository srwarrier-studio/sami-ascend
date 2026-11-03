from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class AuditEvent:
    actor: str
    action: str
    target: str
    outcome: str
    detail: str = ""
    id: int | None = None
    at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
