from pydantic import BaseModel
class User(BaseModel):
    userid: str
    email: str | None = None
    fullname: str | None = None
    disabled: bool | None = None
    sap_username: str | None = None
    roles: list[str] = []


class Me(BaseModel):
    userid: str
    sap_username: str
    roles: list[str]


class UserInDB(User):
    hashed_password: str
