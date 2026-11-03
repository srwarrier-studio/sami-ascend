from auth_api.application.audit import record
from auth_api.application.dto.login_dto import LoginWithPasswordDTO
from auth_api.domain.errors import InvalidCredentials
from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork
from auth_api.domain.interface.password_hasher import PasswordHasher
from auth_api.domain.interface.token_service import TokenService
from auth_api.domain.value_objects.email_id import EmailID

ACTION = "login.password"


class LoginWithPassword:
    def __init__(
        self,
        uow: AuthUnitOfWork,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ):
        self.uow = uow
        self.password_hasher = password_hasher
        self.token_service = token_service

    def refuse(self, who: str, detail: str):
        record(self.uow, who, ACTION, "failed", detail)
        raise InvalidCredentials()

    def execute(self, data: LoginWithPasswordDTO) -> str:
        who = data.email_id.lower()
        try:
            email = EmailID(who)
        except ValueError:
            self.refuse(who, "bad_email")

        with self.uow:
            user = self.uow.user_repo.find_by_email(email)

        if user is None:
            self.refuse(who, "unknown_user")
        if user.disabled:
            self.refuse(who, "disabled")
        if not user.hashed_password or not self.password_hasher.verify(data.password, user.hashed_password):
            self.refuse(who, "bad_password")

        token = self.token_service.issue(user)
        record(self.uow, who, ACTION, "success")
        return token
