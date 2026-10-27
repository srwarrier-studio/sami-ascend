import argparse
import getpass
import sys

from auth_api.application.dto.create_user_dto import CreateFirstAdminDTO
from auth_api.application.usecase.create_first_admin import CreateFirstAdmin
from auth_api.application.usecase.create_user import CreateUser
from auth_api.core.config import settings
from auth_api.domain.errors import AdminAlreadyExists, UserAlreadyExists, WeakPassword
from auth_api.infrastructure.interface.argon2_password_hasher import Argon2PasswordHasher
from auth_api.infrastructure.sqlite.sqlite_unit_of_work import SqliteAuthUnitOfWork


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
            )
        )
    except (ValueError, WeakPassword, UserAlreadyExists, AdminAlreadyExists) as error:
        sys.exit(f"Error: {error}")

    print(f"Admin created. User id: {userid}")


def main():
    parser = argparse.ArgumentParser(prog="auth-api")
    commands = parser.add_subparsers(dest="command", required=True)

    create_admin_parser = commands.add_parser(
        "create-admin", help="create the first admin user"
    )
    create_admin_parser.add_argument("--email", required=True)
    create_admin_parser.add_argument("--fullname", required=True)
    create_admin_parser.add_argument("--sap-username", required=True)
    create_admin_parser.set_defaults(handler=create_admin)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
