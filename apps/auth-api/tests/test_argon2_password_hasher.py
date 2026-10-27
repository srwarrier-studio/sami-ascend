from auth_api.infrastructure.interface.argon2_password_hasher import Argon2PasswordHasher


def test_verify_accepts_right_password_and_rejects_wrong_one():
    hasher = Argon2PasswordHasher()

    hashed = hasher.hash("secret")

    assert hashed != "secret"
    assert hasher.verify("secret", hashed)
    assert not hasher.verify("wrong", hashed)
