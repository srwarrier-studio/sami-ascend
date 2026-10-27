from auth_api.application.dto.login_dto import LoginWithEntraDTO
from auth_api.domain.errors import InvalidCredentials
from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork
from auth_api.domain.interface.token_service import TokenService
from auth_api.domain.value_objects.email_id import EmailID


class LoginWithEntra:
    def __init__(self, uow: AuthUnitOfWork, token_service: TokenService):
        self.uow = uow
        self.token_service = token_service

    def execute(self, data: LoginWithEntraDTO) -> str:
        try:
            email = EmailID(data.email_id.lower())
        except ValueError:
            raise InvalidCredentials()

        with self.uow:
            user = self.uow.user_repo.find_by_email(email)

        if user is None or user.disabled:
            raise InvalidCredentials()

        return self.token_service.issue(user)
