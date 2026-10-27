from auth_api.application.dto.login_dto import LoginWithPasswordDTO
from auth_api.domain.errors import InvalidCredentials
from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork
from auth_api.domain.interface.password_hasher import PasswordHasher
from auth_api.domain.interface.token_service import TokenService
from auth_api.domain.value_objects.email_id import EmailID


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

    def execute(self, data: LoginWithPasswordDTO) -> str:
        try:
            email = EmailID(data.email_id.lower())
        except ValueError:
            raise InvalidCredentials()

        with self.uow:
            user = self.uow.user_repo.find_by_email(email)

        if user is None or user.disabled:
            raise InvalidCredentials()
        if not self.password_hasher.verify(data.password, user.hashed_password):
            raise InvalidCredentials()

        return self.token_service.issue(user)
