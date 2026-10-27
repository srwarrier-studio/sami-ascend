from auth_api.domain.value_objects.email_id import EmailID
from token_verification import Role
from auth_api.domain.value_objects.user_id import UserID
from auth_api.domain.entities.user import User
from auth_api.domain.repositories.user_repo import UserRepo
from auth_api.infrastructure.interface.argon2_password_hasher import Argon2PasswordHasher


MOCK_USER = User(
    userid=UserID.new(),
    email=EmailID("test@email.com"),
    fullname="Test User",
    hashed_password=Argon2PasswordHasher().hash("password"),
    disabled=False,
    sap_username="SAP_READONLY",
    roles=[Role.STORES],
)

class MockUserRepo(UserRepo):
    def __init__(self, store: set[User]):
        self.store = store

    def add(self, user):
        self.store.add(user)
        return user

    def find_all(self):
        return list(self.store)

    def find_by_email(self, email):
        for user in self.store:
            if user.email == email:
                return user
