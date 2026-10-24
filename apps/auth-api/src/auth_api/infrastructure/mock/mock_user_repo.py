from auth_api.domain.value_objects.email_id import EmailID
from auth_api.domain.value_objects.user_id import UserID
from auth_api.domain.entities.user import User
from auth_api.domain.repositories.user_repo import UserRepo


MOCK_USER = User(userid=UserID.new(),email=EmailID("test@email.com"), fullname="Test User", hashed_password="password", disabled=False)

class MockUserRepo(UserRepo):
    def __init__(self):
        self.store: set[User] = set()  
        self.add(MOCK_USER)

    def add(self, user):
        self.store.add(user)
        return user

    def find_all(self):
        return list(self.store)

    def find_by_email(self, email):
        for user in self.store:
            if user.email_id == email:
                return user