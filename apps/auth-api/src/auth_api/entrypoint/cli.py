import argparse
import getpass
import sys

from auth_api.application.dto.create_user_dto import CreateFirstAdminDTO, SetUserCompaniesDTO
from auth_api.application.usecase.create_first_admin import CreateFirstAdmin
from auth_api.application.usecase.create_user import CreateUser
from auth_api.application.usecase.set_user_companies import SetUserCompanies
from auth_api.core.config import settings
from auth_api.domain.errors import AdminAlreadyExists, UserAlreadyExists, UserNotFound, WeakPassword
from auth_api.infrastructure.interface.argon2_password_hasher import Argon2PasswordHasher
from auth_api.infrastructure.sqlite.sqlite_unit_of_work import SqliteAuthUnitOfWork
from token_verification import Company

COMPANY_IDS = [company.value for company in Company]


def create_admin(args: argparse.Namespace):
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Confirm password: "):
        sys.exit("Passwords do not match")

    uow = SqliteAuthUnitOfWork(settings.DATABASE_PATH)
    usecase = CreateFirstAdmin(uow, CreateUser(uow, Argon2PasswordHasher()))
    try:
        userid = usecase.execute(
            CreateFirstAdminDTO(
                email_id=args.email,
                fullname=args.fullname,
                password=password,
                sap_username=args.sap_username,
                actor=getpass.getuser(),
                companies=args.company or COMPANY_IDS,
            )
        )
    except (ValueError, WeakPassword, UserAlreadyExists, AdminAlreadyExists) as error:
        sys.exit(f"Error: {error}")

    print(f"Admin created. User id: {userid}")


def set_companies(args: argparse.Namespace):
    uow = SqliteAuthUnitOfWork(settings.DATABASE_PATH)
    try:
        SetUserCompanies(uow).execute(SetUserCompaniesDTO(email_id=args.email, companies=args.company))
    except (ValueError, UserNotFound) as error:
        sys.exit(f"Error: {error}")

    print(f"Companies set to: {', '.join(args.company)}")


def main():
    parser = argparse.ArgumentParser(prog="auth-api")
    commands = parser.add_subparsers(dest="command", required=True)

    create_admin_parser = commands.add_parser(
        "create-admin", help="create the first admin user"
    )
    create_admin_parser.add_argument("--email", required=True)
    create_admin_parser.add_argument("--fullname", required=True)
    create_admin_parser.add_argument("--sap-username", required=True)
    create_admin_parser.add_argument("--company", action="append", choices=COMPANY_IDS)
    create_admin_parser.set_defaults(handler=create_admin)

    set_companies_parser = commands.add_parser(
        "set-companies", help="replace the companies a user may see"
    )
    set_companies_parser.add_argument("--email", required=True)
    set_companies_parser.add_argument("--company", action="append", choices=COMPANY_IDS, required=True)
    set_companies_parser.set_defaults(handler=set_companies)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
