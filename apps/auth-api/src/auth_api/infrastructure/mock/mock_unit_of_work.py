from auth_api.infrastructure.mock.mock_user_repo import MockUserRepo


from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork


class MockAuthUnitOfWork(AuthUnitOfWork):
    def __enter__(self):
        self.user_repo = MockUserRepo()

    def rollback(self):
        print("Rollback executed")

    def commit(self):
        print("Commit Executed")