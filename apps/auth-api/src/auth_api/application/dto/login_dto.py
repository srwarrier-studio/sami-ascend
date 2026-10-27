from dataclasses import dataclass


@dataclass
class LoginWithPasswordDTO:
    email_id: str
    password: str


@dataclass
class LoginWithEntraDTO:
    email_id: str
