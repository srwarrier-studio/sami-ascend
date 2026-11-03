from datetime import datetime

from pydantic import BaseModel, Field
from token_verification import Company, Role

from auth_api.domain.entities.audit_event import AuditEvent
from auth_api.domain.entities.user import User


class UserOut(BaseModel):
    userid: str
    email: str
    fullname: str
    sap_username: str
    entra_username: str | None
    roles: list[str]
    companies: list[str]
    disabled: bool
    has_password: bool
    created_at: str

    @classmethod
    def from_domain(cls, user: User) -> "UserOut":
        return cls(
            userid=str(user.userid.value),
            email=user.email.value,
            fullname=user.fullname,
            sap_username=user.sap_username,
            entra_username=user.entra_username,
            roles=[role.value for role in user.roles],
            companies=[company.value for company in user.companies],
            disabled=user.disabled,
            has_password=bool(user.hashed_password),
            created_at=user.created_at,
        )


class CreateUserBody(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    fullname: str = Field(min_length=1, max_length=100)
    sap_username: str = Field(min_length=1, max_length=30)
    entra_username: str | None = Field(default=None, max_length=254)
    roles: list[Role] = Field(default_factory=list)
    companies: list[Company] = Field(default_factory=list)
    password: str = Field(default="", max_length=200)


class UpdateUserBody(BaseModel):
    fullname: str | None = Field(default=None, min_length=1, max_length=100)
    sap_username: str | None = Field(default=None, min_length=1, max_length=30)
    entra_username: str | None = Field(default=None, max_length=254)
    roles: list[Role] | None = None
    companies: list[Company] | None = None
    disabled: bool | None = None


class AuditOut(BaseModel):
    id: int
    at: datetime
    actor: str
    action: str
    target: str
    outcome: str
    detail: str

    @classmethod
    def from_domain(cls, event: AuditEvent) -> "AuditOut":
        return cls(id=event.id or 0, at=event.at, actor=event.actor, action=event.action, target=event.target, outcome=event.outcome, detail=event.detail)


class AuditPage(BaseModel):
    items: list[AuditOut]
    next: int | None
