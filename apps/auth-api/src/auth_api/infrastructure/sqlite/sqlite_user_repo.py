import sqlite3
from uuid import UUID

from auth_api.domain.entities.user import User
from auth_api.domain.repositories.user_repo import UserRepo
from auth_api.domain.value_objects.email_id import EmailID
from auth_api.domain.value_objects.role import Role
from auth_api.domain.value_objects.user_id import UserID


class SqliteUserRepo(UserRepo):
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, user: User) -> User:
        self.conn.execute(
            "INSERT INTO users (userid, email, fullname, hashed_password, disabled, sap_username)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                str(user.userid.value),
                user.email.value,
                user.fullname,
                user.hashed_password,
                int(user.disabled),
                user.sap_username,
            ),
        )
        self.conn.executemany(
            "INSERT INTO user_roles (userid, role) VALUES (?, ?)",
            [(str(user.userid.value), role.value) for role in user.roles],
        )
        return user

    def find_all(self) -> list[User]:
        rows = self.conn.execute("SELECT * FROM users").fetchall()
        return [self._to_user(row) for row in rows]

    def find_by_email(self, email: EmailID) -> User | None:
        row = self.conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.value,)
        ).fetchone()
        return self._to_user(row) if row else None

    def _to_user(self, row: sqlite3.Row) -> User:
        role_rows = self.conn.execute(
            "SELECT role FROM user_roles WHERE userid = ? ORDER BY role", (row["userid"],)
        ).fetchall()
        return User(
            userid=UserID(UUID(row["userid"])),
            email=EmailID(row["email"]),
            fullname=row["fullname"],
            hashed_password=row["hashed_password"],
            disabled=bool(row["disabled"]),
            sap_username=row["sap_username"],
            roles=[Role(role_row["role"]) for role_row in role_rows],
        )
