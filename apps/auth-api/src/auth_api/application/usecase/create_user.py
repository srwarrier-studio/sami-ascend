from auth_api.application.dto.create_user_dto import CreateUserDTO
from auth_api.domain.entities.audit_event import AuditEvent
from auth_api.domain.entities.user import User
from auth_api.domain.errors import UserAlreadyExists, WeakPassword
from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork
from auth_api.domain.interface.password_hasher import PasswordHasher
from auth_api.domain.value_objects.email_id import EmailID
from token_verification import Company, Role
from auth_api.domain.value_objects.user_id import UserID

MIN_PASSWORD_LENGTH = 12


class CreateUser:
    def __init__(self, uow: AuthUnitOfWork, password_hasher: PasswordHasher):
        self.uow = uow
        self.password_hasher = password_hasher

    def execute(self, data: CreateUserDTO) -> str:
        email = EmailID(data.email_id.lower())
        roles = [Role(role) for role in data.roles]
        companies = list(dict.fromkeys(Company(company) for company in data.companies))
        if data.password and len(data.password) < MIN_PASSWORD_LENGTH:
            raise WeakPassword(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
            )

        with self.uow:
            if self.uow.user_repo.find_by_email(email):
                raise UserAlreadyExists("A user with this email already exists")

            user = User(
                userid=UserID.new(),
                email=email,
                fullname=data.fullname,
                hashed_password=self.password_hasher.hash(data.password) if data.password else "",
                disabled=False,
                sap_username=data.sap_username,
                roles=roles,
                companies=companies,
                entra_username=(data.entra_username or "").strip().lower() or None,
            )
            self.uow.user_repo.add(user)
            self.uow.audit_repo.add(
                AuditEvent(
                    actor=data.actor,
                    action="user.create",
                    target=email.value,
                    outcome="success",
                    detail="entra only" if not data.password else "",
                )
            )
            self.uow.commit()

        return str(user.userid.value)
