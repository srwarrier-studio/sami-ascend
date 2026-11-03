import logging

from auth_api.domain.entities.audit_event import AuditEvent
from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork

logger = logging.getLogger(__name__)


def record(uow: AuthUnitOfWork, actor: str, action: str, outcome: str, detail: str = "") -> None:
    try:
        with uow:
            uow.audit_repo.add(AuditEvent(actor[:254], action, actor[:254], outcome, detail))
            uow.commit()
    except Exception:
        logger.exception("audit write failed")
