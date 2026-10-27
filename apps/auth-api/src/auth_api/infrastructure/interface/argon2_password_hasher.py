from pwdlib import PasswordHash

from auth_api.domain.interface.password_hasher import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    def __init__(self):
        self.password_hash = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self.password_hash.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        return self.password_hash.verify(password, hashed_password)
