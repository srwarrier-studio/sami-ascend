from dataclasses import dataclass

from token_verification import Company, Role

from auth_api.domain.entities.audit_event import AuditEvent
from auth_api.domain.entities.user import User
from auth_api.domain.errors import LastAdmin, SelfLockout, UserNotFound
from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork
from auth_api.domain.interface.password_hasher import PasswordHasher
from auth_api.domain.repositories.audit_repo import AuditFilter
from auth_api.application.dto.create_user_dto import CreateUserDTO
from auth_api.application.usecase.create_user import CreateUser


@dataclass
class UserChanges:
    fullname: str | None = None
    sap_username: str | None = None
    entra_username: str | None = None
    roles: list[Role] | None = None
    companies: list[Company] | None = None
    disabled: bool | None = None


class ListUsers:
    def __init__(self, uow: AuthUnitOfWork):
        self.uow = uow

    def execute(self, query: str = "") -> list[User]:
        text = query.strip().lower()
        with self.uow:
            users = self.uow.user_repo.find_all()
        matching = [user for user in users if text in f"{user.fullname} {user.email.value}".lower()]
        return sorted(matching, key=lambda user: user.fullname.lower())


class CreateManagedUser:
    def __init__(self, uow: AuthUnitOfWork, password_hasher: PasswordHasher):
        self.create = CreateUser(uow, password_hasher)

    def execute(self, data: CreateUserDTO) -> str:
        return self.create.execute(data)


class UpdateUser:
    def __init__(self, uow: AuthUnitOfWork):
        self.uow = uow

    def execute(self, userid: str, changes: UserChanges, actor_id: str, actor: str) -> User:
        with self.uow:
            user = self.uow.user_repo.find_by_id(userid)
            if user is None:
                raise UserNotFound(userid)
            was_admin = not user.disabled and Role.ADMIN in user.roles
            changed = self.apply(user, changes, own=userid == actor_id)
            self.guard_last_admin(user, was_admin)
            self.uow.user_repo.update(user)
            for action, detail in changed:
                self.uow.audit_repo.add(AuditEvent(actor, action, user.email.value, "success", detail))
            self.uow.commit()
        return user

    def apply(self, user: User, changes: UserChanges, own: bool) -> list[tuple[str, str]]:
        events: list[tuple[str, str]] = []
        fields = []
        if changes.disabled is not None and changes.disabled != user.disabled:
            if own and changes.disabled:
                raise SelfLockout("You cannot disable yourself")
            user.disabled = changes.disabled
            events.append(("user.disable" if changes.disabled else "user.enable", ""))
        if changes.roles is not None and sorted(changes.roles) != sorted(user.roles):
            if own and Role.ADMIN in user.roles and Role.ADMIN not in changes.roles:
                raise SelfLockout("You cannot remove your own admin role")
            user.roles = sorted(set(changes.roles))
            fields.append("roles")
        if changes.companies is not None and sorted(changes.companies) != sorted(user.companies):
            user.companies = sorted(set(changes.companies))
            fields.append("companies")
        for name in ("fullname", "sap_username"):
            value = getattr(changes, name)
            if value is not None and value != getattr(user, name):
                setattr(user, name, value)
                fields.append(name)
        if changes.entra_username is not None:
            value = changes.entra_username.strip().lower() or None
            if value != user.entra_username:
                user.entra_username = value
                fields.append("entra_username")
        if fields:
            events.append(("user.update", ", ".join(fields)))
        return events

    def guard_last_admin(self, edited: User, was_admin: bool) -> None:
        if not was_admin or (not edited.disabled and Role.ADMIN in edited.roles):
            return
        if not any(u.userid != edited.userid and not u.disabled and Role.ADMIN in u.roles for u in self.uow.user_repo.find_all()):
            raise LastAdmin()


class ReadAuditLog:
    def __init__(self, uow: AuthUnitOfWork):
        self.uow = uow

    def execute(self, filters: AuditFilter, limit: int, before: int | None):
        with self.uow:
            return self.uow.audit_repo.list(filters, limit, before)
