from auth_api.infrastructure.mock.mock_user_repo import MOCK_USER, MockUserRepo


from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork


class MockAuthUnitOfWork(AuthUnitOfWork):
    def __init__(self):
        self.users = {MOCK_USER}

    def __enter__(self):
        self.user_repo = MockUserRepo(self.users)
        return self

    def rollback(self):
        print("Rollback executed")

    def commit(self):
        print("Commit Executed")
