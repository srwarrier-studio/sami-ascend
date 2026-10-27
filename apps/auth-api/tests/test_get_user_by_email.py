from auth_api.application.dto.get_user_dto import GetUserDTO
from auth_api.application.usecase.get_user_by_email import GetUserByEmail
from auth_api.infrastructure.api.schema import UserInDB
from auth_api.infrastructure.mock.mock_unit_of_work import MockAuthUnitOfWork


def test_finds_existing_user_and_maps_to_schema():
    usecase = GetUserByEmail(uow=MockAuthUnitOfWork())

    user_dict = usecase.execute(GetUserDTO(email_id="test@email.com"))

    user = UserInDB(**user_dict)
    assert user.email == "test@email.com"
    assert user.roles == ["stores"]


def test_unknown_email_returns_none():
    usecase = GetUserByEmail(uow=MockAuthUnitOfWork())

    assert usecase.execute(GetUserDTO(email_id="nobody@email.com")) is None
