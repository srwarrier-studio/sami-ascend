from auth_api.application.dto.create_user_dto import CreateFirstAdminDTO, CreateUserDTO
from auth_api.application.usecase.create_user import CreateUser
from auth_api.domain.errors import AdminAlreadyExists
from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork
from token_verification import Role


class CreateFirstAdmin:
    def __init__(self, uow: AuthUnitOfWork, create_user: CreateUser):
        self.uow = uow
        self.create_user = create_user

    def execute(self, data: CreateFirstAdminDTO) -> str:
        with self.uow:
            admin_exists = any(Role.ADMIN in user.roles for user in self.uow.user_repo.find_all())
        if admin_exists:
            raise AdminAlreadyExists("An admin already exists, use the admin app to add users")

        return self.create_user.execute(
            CreateUserDTO(
                email_id=data.email_id,
                fullname=data.fullname,
                password=data.password,
                sap_username=data.sap_username,
                roles=[Role.ADMIN.value],
                actor=data.actor,
            )
        )
