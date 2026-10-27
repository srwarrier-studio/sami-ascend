from auth_api.domain.value_objects.email_id import EmailID
from token_verification import Role
from auth_api.domain.value_objects.user_id import UserID
from dataclasses import dataclass


@dataclass
class User:
    userid: UserID
    email: EmailID
    fullname: str
    hashed_password: str
    disabled: bool
    sap_username: str
    roles: list[Role]

    def to_dict(self):
        return {
            "userid": str(self.userid.value),
            "email": self.email.value,
            "fullname": self.fullname,
            "hashed_password": self.hashed_password,
            "disabled": self.disabled,
            "sap_username": self.sap_username,
            "roles": [role.value for role in self.roles],
        }

    def __eq__(self, other: object):
        if not isinstance(other, User):
            return False
        return self.userid == other.userid

    def __hash__(self):
        return hash(self.userid.value)
