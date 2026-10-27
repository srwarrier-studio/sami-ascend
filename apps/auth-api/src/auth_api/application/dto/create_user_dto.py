from dataclasses import dataclass


@dataclass
class CreateUserDTO:
    email_id: str
    fullname: str
    password: str
    sap_username: str
    roles: list[str]
    actor: str


@dataclass
class CreateFirstAdminDTO:
    email_id: str
    fullname: str
    password: str
    sap_username: str
    actor: str
