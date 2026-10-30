from dataclasses import dataclass, field


@dataclass
class CreateUserDTO:
    email_id: str
    fullname: str
    password: str
    sap_username: str
    roles: list[str]
    actor: str
    companies: list[str] = field(default_factory=list)


@dataclass
class CreateFirstAdminDTO:
    email_id: str
    fullname: str
    password: str
    sap_username: str
    actor: str
    companies: list[str] = field(default_factory=list)


@dataclass
class SetUserCompaniesDTO:
    email_id: str
    companies: list[str]
