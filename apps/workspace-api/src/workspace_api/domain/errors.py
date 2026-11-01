from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationDetail:
    code: str
    message: str
    target: str


class SalesOrderRejected(Exception):
    def __init__(self, details: list[ValidationDetail]):
        super().__init__(f"{len(details)} validation problems")
        self.details = details


class SapUnavailable(Exception): ...


class SapNotReached(SapUnavailable): ...


class SapBusy(SapNotReached): ...


class SapOutcomeUnknown(SapUnavailable): ...


class InvalidQuery(Exception): ...


class CompanyNotAllowed(Exception): ...


class StoreUnavailable(Exception): ...
