from auth_api.domain.entities.user import User
from auth_api.domain.value_objects.email_id import EmailID
from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork
from auth_api.application.dto.get_user_dto import GetUserDTO
from auth_api.domain.repositories.user_repo import UserRepo



class GetUserByEmail:
    def __init__(self, uow: AuthUnitOfWork):
        self.uow = uow

    def execute(self, data: GetUserDTO):
        with self.uow:
            user: User | None = self.uow.user_repo.find_by_email(EmailID(data.email_id))
            if user:
                return user.to_dict()

