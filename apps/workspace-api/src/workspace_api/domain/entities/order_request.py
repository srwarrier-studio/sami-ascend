from dataclasses import dataclass
from datetime import datetime

QUEUED, SENDING, POSTED, REJECTED, UNKNOWN, FAILED = "queued", "sending", "posted", "rejected", "unknown", "failed"
OPEN = (QUEUED, SENDING, UNKNOWN, FAILED)


@dataclass(frozen=True)
class OrderRequest:
    id: str
    user: str
    sap_username: str
    request_id: str | None
    body: dict
    status: str
    attempts: int
    next_attempt_at: datetime
    created_at: datetime
    updated_at: datetime
    sales_order: str | None = None
    details: list[dict] | None = None
    message: str | None = None
