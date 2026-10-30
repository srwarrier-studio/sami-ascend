from auth_api.application.dto.create_user_dto import SetUserCompaniesDTO
from auth_api.domain.errors import UserNotFound
from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork
from auth_api.domain.value_objects.email_id import EmailID
from token_verification import Company


class SetUserCompanies:
    def __init__(self, uow: AuthUnitOfWork):
        self.uow = uow

    def execute(self, data: SetUserCompaniesDTO) -> None:
        companies = list(dict.fromkeys(Company(company) for company in data.companies))
        if not companies:
            raise ValueError("A user needs at least one company")

        with self.uow:
            user = self.uow.user_repo.find_by_email(EmailID(data.email_id.lower()))
            if user is None:
                raise UserNotFound("No user with this email")
            self.uow.user_repo.set_companies(user, companies)
            self.uow.commit()
