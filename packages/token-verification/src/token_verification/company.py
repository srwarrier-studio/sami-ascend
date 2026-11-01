from enum import StrEnum

CODES = {"sabinsa": "INA1", "neutraceuticals": "INA2", "organica": "INA3"}


class Company(StrEnum):
    SABINSA = "sabinsa"
    NEUTRACEUTICALS = "neutraceuticals"
    ORGANICA = "organica"

    @property
    def code(self) -> str:
        return CODES[self.value]

    @classmethod
    def from_code(cls, code: str) -> "Company":
        for company in cls:
            if company.code == code:
                return company
        raise ValueError(f"Unknown company code {code}")
