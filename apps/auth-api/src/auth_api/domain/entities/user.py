from typing import Self
from auth_api.domain.value_objects.email_id import EmailID
from auth_api.domain.value_objects.user_id import UserID
from dataclasses import dataclass


@dataclass
class User:
    userid: UserID
    email: EmailID
    fullname:str
    hashed_password: str
    disabled: bool

    def to_dict(self):
        return {
            "userid": self.userid.value,
            "email": self.email.value,
            "fullname": self.fullname,
            "hashed_password": self.hashed_password
        }


    def __eq__(self, other: object):
        if not isinstance(other, User):
            return False
        return self.user_id == other.user_id

    def __hash__(self):
        return hash(self.user_id.value)