from auth_api.application.audit import record
from auth_api.application.dto.login_dto import LoginWithEntraDTO
from auth_api.domain.errors import InvalidCredentials
from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork
from auth_api.domain.interface.token_service import TokenService
from auth_api.domain.value_objects.email_id import EmailID

ACTION = "login.entra"


class LoginWithEntra:
    def __init__(self, uow: AuthUnitOfWork, token_service: TokenService):
        self.uow = uow
        self.token_service = token_service

    def refuse(self, who: str, detail: str):
        record(self.uow, who, ACTION, "failed", detail)
        raise InvalidCredentials()

    def execute(self, data: LoginWithEntraDTO) -> str:
        who = data.email_id.lower()
        try:
            email = EmailID(who)
        except ValueError:
            self.refuse(who, "bad_email")

        with self.uow:
            user = self.uow.user_repo.find_by_email(email)

        if user is None:
            self.refuse(who, "no_entra_match")
        if user.disabled:
            self.refuse(who, "disabled")

        token = self.token_service.issue(user)
        record(self.uow, who, ACTION, "success")
        return token
