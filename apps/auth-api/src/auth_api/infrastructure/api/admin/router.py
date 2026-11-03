import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from token_verification import Company, Role
from token_verification.fastapi_deps import AuthDependencies
from token_verification.token_claims import TokenClaims

from auth_api.application.dto.create_user_dto import CreateUserDTO
from auth_api.application.usecase.admin_users import CreateManagedUser, ListUsers, ReadAuditLog, UpdateUser, UserChanges
from auth_api.domain.entities.user import User
from auth_api.domain.errors import LastAdmin, SelfLockout, UserAlreadyExists, UserNotFound, WeakPassword
from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork
from auth_api.domain.interface.password_hasher import PasswordHasher
from auth_api.domain.repositories.audit_repo import AuditFilter
from auth_api.infrastructure.api.admin.schemas import AuditOut, AuditPage, CreateUserBody, UpdateUserBody, UserOut

MAX_PAGE = 200


def refuse(status: int, code: str, message: str = "") -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message or code})


def create_admin_router(uow: AuthUnitOfWork, hasher: PasswordHasher, auth: AuthDependencies) -> APIRouter:
    router = APIRouter(prefix="/admin")
    admin_claims = auth.require_roles(Role.ADMIN)

    def current_admin(claims: Annotated[TokenClaims, Depends(admin_claims)]) -> User:
        with uow:
            user = uow.user_repo.find_by_id(claims.userid)
        if user is None or user.disabled or Role.ADMIN not in user.roles:
            raise HTTPException(status_code=401, detail="Session expired, please log in again")
        return user

    Admin = Annotated[User, Depends(current_admin)]

    @router.get("/users")
    def list_users(admin: Admin, q: str = "") -> list[UserOut]:
        return [UserOut.from_domain(user) for user in ListUsers(uow).execute(q)]

    @router.post("/users", status_code=201)
    def create_user(admin: Admin, body: CreateUserBody) -> UserOut:
        dto = CreateUserDTO(
            email_id=body.email, fullname=body.fullname, password=body.password, sap_username=body.sap_username,
            roles=[role.value for role in body.roles], actor=admin.email.value,
            companies=[company.value for company in body.companies], entra_username=body.entra_username,
        )
        try:
            userid = CreateManagedUser(uow, hasher).execute(dto)
        except UserAlreadyExists as error:
            raise refuse(409, "USER_ALREADY_EXISTS", str(error))
        except WeakPassword as error:
            raise refuse(422, "WEAK_PASSWORD", str(error))
        except ValueError as error:
            raise refuse(422, "INVALID_USER", str(error))
        except sqlite3.IntegrityError:
            raise refuse(409, "ENTRA_USERNAME_TAKEN", "That Entra username belongs to another user")
        with uow:
            return UserOut.from_domain(uow.user_repo.find_by_id(userid))

    @router.patch("/users/{userid}")
    def update_user(admin: Admin, userid: str, body: UpdateUserBody) -> UserOut:
        changes = UserChanges(body.fullname, body.sap_username, body.entra_username, body.roles, body.companies, body.disabled)
        try:
            user = UpdateUser(uow).execute(userid, changes, str(admin.userid.value), admin.email.value)
        except UserNotFound:
            raise refuse(404, "USER_NOT_FOUND")
        except LastAdmin:
            raise refuse(409, "LAST_ADMIN", "At least one active admin is needed")
        except SelfLockout as error:
            raise refuse(409, "SELF_LOCKOUT", str(error))
        except sqlite3.IntegrityError:
            raise refuse(409, "ENTRA_USERNAME_TAKEN", "That Entra username belongs to another user")
        return UserOut.from_domain(user)

    @router.get("/roles")
    def roles(admin: Admin) -> list[str]:
        return [role.value for role in Role]

    @router.get("/companies")
    def companies(admin: Admin) -> list[str]:
        return [company.value for company in Company]

    @router.get("/audit-log")
    def audit_log(
        admin: Admin,
        limit: Annotated[int, Query(ge=1, le=MAX_PAGE)] = 50,
        before: int | None = None,
        actor: str | None = None,
        action: str | None = None,
        outcome: str | None = None,
        start: Annotated[str | None, Query(alias="from")] = None,
        end: Annotated[str | None, Query(alias="to")] = None,
    ) -> AuditPage:
        events = ReadAuditLog(uow).execute(AuditFilter(actor and actor.lower(), action, outcome, start, end), limit + 1, before)
        page = events[:limit]
        return AuditPage(items=[AuditOut.from_domain(event) for event in page], next=page[-1].id if len(events) > limit else None)

    return router
