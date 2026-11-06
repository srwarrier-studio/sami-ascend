import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from token_verification import Role, TokenVerifier
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE, AuthDependencies

from auth_api.application.dto.login_dto import LoginWithEntraDTO, LoginWithPasswordDTO
from auth_api.application.usecase.login_with_entra import LoginWithEntra
from auth_api.application.usecase.login_with_password import LoginWithPassword
from auth_api.domain.entities.user import User
from auth_api.domain.errors import InvalidCredentials
from auth_api.domain.value_objects.email_id import EmailID
from auth_api.domain.value_objects.user_id import UserID
from auth_api.infrastructure.api.admin.router import create_admin_router
from auth_api.infrastructure.interface.argon2_password_hasher import Argon2PasswordHasher
from auth_api.infrastructure.interface.jwt_token_service import JwtTokenService
from auth_api.infrastructure.sqlite.sqlite_unit_of_work import SqliteAuthUnitOfWork

SECRET = "s" * 32
BASE = "/admin"
hasher = Argon2PasswordHasher()
tokens = JwtTokenService(SECRET, 5)


@pytest.fixture
def uow(tmp_path):
    return SqliteAuthUnitOfWork(str(tmp_path / "auth.db"))


def seed(uow, email, roles, disabled=False):
    user = User(UserID.new(), EmailID(email), email.split("@")[0], hasher.hash("long-enough-pass"), disabled, "SAPUSER", roles)
    with uow:
        uow.user_repo.add(user)
        uow.commit()
    return user


def client_for(uow, user=None) -> TestClient:
    app = FastAPI()
    app.include_router(create_admin_router(lambda: SqliteAuthUnitOfWork(uow.database_path), hasher, AuthDependencies(TokenVerifier(SECRET))))
    client = TestClient(app)
    if user:
        client.cookies.set(ACCESS_TOKEN_COOKIE, tokens.issue(user))
    return client


@pytest.fixture
def admin(uow):
    return seed(uow, "boss@sami.com", [Role.ADMIN])


@pytest.fixture
def api(uow, admin):
    return client_for(uow, admin)


NEW = {"email": "Bob@Sami.com", "fullname": "Bob", "sap_username": "BOB", "roles": ["production"], "companies": ["sabinsa"], "password": "a-long-enough-pass"}


class TestAccess:
    @pytest.mark.parametrize("path", ["/users", "/roles", "/companies", "/audit-log"])
    def test_signed_out_is_401(self, uow, path):
        assert client_for(uow).get(BASE + path).status_code == 401

    @pytest.mark.parametrize("path", ["/users", "/roles", "/companies", "/audit-log"])
    def test_non_admins_are_403(self, uow, admin, path):
        manager = seed(uow, "m@sami.com", [Role.MANAGEMENT])
        assert client_for(uow, manager).get(BASE + path).status_code == 403

    def test_a_disabled_admin_token_stops_working(self, uow, admin):
        second = seed(uow, "two@sami.com", [Role.ADMIN])
        client = client_for(uow, second)
        client_for(uow, admin).patch(f"{BASE}/users/{second.userid.value}", json={"disabled": True})
        assert client.get(BASE + "/users").status_code == 401


class TestUsers:
    def test_create_then_list(self, api):
        created = api.post(BASE + "/users", json=NEW)
        assert created.status_code == 201
        assert created.json()["email"] == "bob@sami.com" and created.json()["roles"] == ["production"] and created.json()["has_password"]
        assert {u["email"] for u in api.get(BASE + "/users").json()} == {"boss@sami.com", "bob@sami.com"}

    def test_search_matches_name_and_email(self, api):
        api.post(BASE + "/users", json=NEW)
        assert [u["email"] for u in api.get(BASE + "/users?q=bob").json()] == ["bob@sami.com"]

    def test_a_duplicate_email_is_409(self, api):
        api.post(BASE + "/users", json=NEW)
        response = api.post(BASE + "/users", json=NEW)
        assert response.status_code == 409 and response.json()["detail"]["code"] == "USER_ALREADY_EXISTS"

    def test_a_weak_password_is_422(self, api):
        response = api.post(BASE + "/users", json={**NEW, "password": "short"})
        assert response.status_code == 422 and response.json()["detail"]["code"] == "WEAK_PASSWORD"

    def test_an_unknown_role_is_422(self, api):
        assert api.post(BASE + "/users", json={**NEW, "roles": ["wizard"]}).status_code == 422

    def test_lists_of_allowed_values(self, api):
        assert "production" in api.get(BASE + "/roles").json() and "organica" in api.get(BASE + "/companies").json()

    def test_the_master_data_role_is_listed_and_can_be_given(self, api):
        assert "master-data" in api.get(BASE + "/roles").json()
        created = api.post(BASE + "/users", json={**NEW, "roles": ["master-data"]})
        assert created.status_code == 201 and created.json()["roles"] == ["master-data"]

    def test_update_roles_and_companies(self, api):
        userid = api.post(BASE + "/users", json=NEW).json()["userid"]
        changed = api.patch(f"{BASE}/users/{userid}", json={"roles": ["accounts", "quality"], "companies": ["organica"]}).json()
        assert changed["roles"] == ["accounts", "quality"] and changed["companies"] == ["organica"]

    def test_an_unknown_user_is_404(self, api):
        assert api.patch(BASE + "/users/nope", json={"disabled": True}).status_code == 404


class TestDisable:
    def test_disabling_stops_sign_in_and_enabling_restores_it(self, uow, api):
        userid = api.post(BASE + "/users", json=NEW).json()["userid"]
        login = LoginWithPassword(uow, hasher, tokens)
        api.patch(f"{BASE}/users/{userid}", json={"disabled": True})
        with pytest.raises(InvalidCredentials):
            login.execute(LoginWithPasswordDTO("bob@sami.com", "a-long-enough-pass"))
        api.patch(f"{BASE}/users/{userid}", json={"disabled": False})
        assert login.execute(LoginWithPasswordDTO("bob@sami.com", "a-long-enough-pass"))

    def test_an_admin_cannot_disable_themselves(self, uow, admin, api):
        seed(uow, "two@sami.com", [Role.ADMIN])
        response = api.patch(f"{BASE}/users/{admin.userid.value}", json={"disabled": True})
        assert response.status_code == 409 and response.json()["detail"]["code"] == "SELF_LOCKOUT"

    def test_an_admin_cannot_drop_their_own_admin_role(self, uow, admin, api):
        seed(uow, "two@sami.com", [Role.ADMIN])
        assert api.patch(f"{BASE}/users/{admin.userid.value}", json={"roles": ["management"]}).status_code == 409

    def test_the_last_active_admin_cannot_be_disabled_or_demoted(self, uow, admin, api):
        other = seed(uow, "two@sami.com", [Role.ADMIN], disabled=False)
        client_for(uow, other).patch(f"{BASE}/users/{admin.userid.value}", json={"disabled": True})
        response = client_for(uow, other).patch(f"{BASE}/users/{other.userid.value}", json={"roles": ["management"]})
        assert response.status_code in (401, 409)

    def test_demoting_the_only_other_admin_is_refused(self, uow, admin, api):
        other = seed(uow, "two@sami.com", [Role.ADMIN])
        api.patch(f"{BASE}/users/{other.userid.value}", json={"disabled": True})
        third = seed(uow, "three@sami.com", [Role.MANAGEMENT])
        response = api.patch(f"{BASE}/users/{admin.userid.value}", json={"roles": ["management"]})
        assert response.status_code == 409
        assert third


class TestEntra:
    def test_a_user_without_a_password_is_entra_only(self, uow, api):
        created = api.post(BASE + "/users", json={**NEW, "password": ""}).json()
        assert created["has_password"] is False
        with pytest.raises(InvalidCredentials):
            LoginWithPassword(uow, hasher, tokens).execute(LoginWithPasswordDTO("bob@sami.com", ""))

    def test_the_entra_name_is_tried_before_the_email(self, uow, api):
        api.post(BASE + "/users", json={**NEW, "password": "", "entra_username": "Bob.Smith@corp.onmicrosoft.com"})
        token = LoginWithEntra(uow, tokens).execute(LoginWithEntraDTO("bob.smith@corp.onmicrosoft.com"))
        assert TokenVerifier(SECRET).verify(token).roles == [Role.PRODUCTION]

    def test_an_entra_name_belongs_to_one_user(self, api):
        api.post(BASE + "/users", json={**NEW, "entra_username": "x@corp.com"})
        response = api.post(BASE + "/users", json={**NEW, "email": "c@sami.com", "entra_username": "x@corp.com"})
        assert response.status_code == 409 and response.json()["detail"]["code"] == "ENTRA_USERNAME_TAKEN"

    def test_an_entra_identity_with_no_row_is_refused(self, uow, api):
        with pytest.raises(InvalidCredentials):
            LoginWithEntra(uow, tokens).execute(LoginWithEntraDTO("stranger@corp.com"))

    def test_the_token_carries_exactly_the_rows_roles(self, uow, api):
        userid = api.post(BASE + "/users", json={**NEW, "password": ""}).json()["userid"]
        api.patch(f"{BASE}/users/{userid}", json={"roles": ["accounts"], "companies": ["organica"]})
        claims = TokenVerifier(SECRET).verify(LoginWithEntra(uow, tokens).execute(LoginWithEntraDTO("bob@sami.com")))
        assert claims.roles == [Role.ACCOUNTS] and [c.value for c in claims.companies] == ["organica"]


class TestAuditLog:
    def test_admin_changes_are_logged_without_passwords(self, api):
        userid = api.post(BASE + "/users", json=NEW).json()["userid"]
        api.patch(f"{BASE}/users/{userid}", json={"roles": ["quality"], "disabled": True})
        rows = api.get(BASE + "/audit-log").json()["items"]
        assert [(r["action"], r["detail"]) for r in rows] == [("user.update", "roles"), ("user.disable", ""), ("user.create", "")]
        assert all(r["actor"] == "boss@sami.com" and "long-enough" not in str(r) for r in rows)

    def test_paging_returns_every_row_once_newest_first(self, uow, api):
        for i in range(5):
            api.post(BASE + "/users", json={**NEW, "email": f"u{i}@sami.com"})
        seen, before = [], None
        while True:
            page = api.get(BASE + "/audit-log", params={"limit": 2, **({"before": before} if before else {})}).json()
            seen += [r["id"] for r in page["items"]]
            before = page["next"]
            if before is None:
                break
        assert seen == sorted(set(seen), reverse=True) and len(seen) == 5

    def test_filters_combine(self, uow, api):
        api.post(BASE + "/users", json=NEW)
        with pytest.raises(InvalidCredentials):
            LoginWithPassword(uow, hasher, tokens).execute(LoginWithPasswordDTO("bob@sami.com", "wrong"))
        failed = api.get(BASE + "/audit-log?outcome=failed").json()["items"]
        assert [r["detail"] for r in failed] == ["bad_password"]
        assert api.get(BASE + "/audit-log?outcome=failed&action=user.create").json()["items"] == []
        assert [r["actor"] for r in api.get(BASE + "/audit-log?actor=BOB@sami.com").json()["items"]] == ["bob@sami.com"]

    def test_an_action_ending_in_a_star_matches_a_prefix(self, uow, api):
        api.post(BASE + "/users", json=NEW)
        with pytest.raises(InvalidCredentials):
            LoginWithPassword(uow, hasher, tokens).execute(LoginWithPasswordDTO("bob@sami.com", "wrong"))
        assert [r["action"] for r in api.get(BASE + "/audit-log?action=user.*").json()["items"]] == ["user.create"]
        assert [r["action"] for r in api.get(BASE + "/audit-log?action=login.*").json()["items"]] == ["login.password"]


class TestConcurrentRequests:
    def test_overlapping_requests_do_not_share_a_connection(self, uow, api):
        from concurrent.futures import ThreadPoolExecutor

        def call(path):
            return api.get(BASE + path).status_code

        with ThreadPoolExecutor(max_workers=8) as pool:
            codes = list(pool.map(call, ["/roles", "/companies", "/users", "/audit-log"] * 40))

        assert set(codes) == {200}
