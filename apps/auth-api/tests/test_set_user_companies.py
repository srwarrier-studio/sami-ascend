import sys
from types import SimpleNamespace

import pytest

from auth_api.application.dto.create_user_dto import CreateUserDTO, SetUserCompaniesDTO
from auth_api.application.usecase.create_user import CreateUser
from auth_api.application.usecase.set_user_companies import SetUserCompanies
from auth_api.domain.errors import UserNotFound
from auth_api.domain.value_objects.email_id import EmailID
from auth_api.entrypoint import cli
from auth_api.infrastructure.interface.argon2_password_hasher import Argon2PasswordHasher
from auth_api.infrastructure.sqlite.sqlite_unit_of_work import SqliteAuthUnitOfWork
from token_verification import Company

PASSWORD = "a-long-enough-password"
EMAIL = "cfo@email.com"


@pytest.fixture
def uow(tmp_path):
    uow = SqliteAuthUnitOfWork(str(tmp_path / "auth.db"))
    CreateUser(uow, Argon2PasswordHasher()).execute(
        CreateUserDTO(EMAIL, "The CFO", PASSWORD, "SAP_CFO", ["management"], "sarath", ["sabinsa"])
    )
    return uow


def companies_of(uow):
    with uow:
        return uow.user_repo.find_by_email(EmailID(EMAIL)).companies


def test_replaces_the_companies(uow):
    SetUserCompanies(uow).execute(SetUserCompaniesDTO("CFO@email.com", ["organica", "neutraceuticals"]))

    assert companies_of(uow) == [Company.NEUTRACEUTICALS, Company.ORGANICA]


def test_rejects_unknown_company_and_keeps_the_old_list(uow):
    with pytest.raises(ValueError):
        SetUserCompanies(uow).execute(SetUserCompaniesDTO(EMAIL, ["acme"]))

    assert companies_of(uow) == [Company.SABINSA]


def test_rejects_an_empty_list(uow):
    with pytest.raises(ValueError, match="at least one"):
        SetUserCompanies(uow).execute(SetUserCompaniesDTO(EMAIL, []))


def test_fails_for_an_unknown_email(uow):
    with pytest.raises(UserNotFound):
        SetUserCompanies(uow).execute(SetUserCompaniesDTO("nobody@email.com", ["sabinsa"]))


def run_cli(monkeypatch, tmp_path, *arguments):
    monkeypatch.setattr(cli, "settings", SimpleNamespace(DATABASE_PATH=str(tmp_path / "auth.db")))
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: PASSWORD)
    monkeypatch.setattr(sys, "argv", ["auth-api", *arguments])
    cli.main()


def admin_companies(tmp_path):
    uow = SqliteAuthUnitOfWork(str(tmp_path / "auth.db"))
    with uow:
        return uow.user_repo.find_by_email(EmailID("admin@email.com")).companies


def create_admin_arguments(*extra):
    return ("create-admin", "--email", "admin@email.com", "--fullname", "Admin", "--sap-username", "SAP_ADMIN", *extra)


def test_create_admin_without_a_company_flag_gets_all_three(monkeypatch, tmp_path):
    run_cli(monkeypatch, tmp_path, *create_admin_arguments())

    assert admin_companies(tmp_path) == [Company.NEUTRACEUTICALS, Company.ORGANICA, Company.SABINSA]


def test_create_admin_with_a_company_flag_gets_exactly_that(monkeypatch, tmp_path):
    run_cli(monkeypatch, tmp_path, *create_admin_arguments("--company", "organica"))

    assert admin_companies(tmp_path) == [Company.ORGANICA]


def test_set_companies_command_replaces_the_list(monkeypatch, tmp_path):
    run_cli(monkeypatch, tmp_path, *create_admin_arguments("--company", "organica"))

    run_cli(monkeypatch, tmp_path, "set-companies", "--email", "admin@email.com", "--company", "sabinsa")

    assert admin_companies(tmp_path) == [Company.SABINSA]


def test_set_companies_command_exits_for_an_unknown_email(monkeypatch, tmp_path):
    with pytest.raises(SystemExit):
        run_cli(monkeypatch, tmp_path, "set-companies", "--email", "nobody@email.com", "--company", "sabinsa")
