from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from synapse_api.domain.entities.kpis import SalesTotal


class SalesTotalResponse(BaseModel):
    start: date
    end: date
    net_amount: Decimal
    order_count: int
    currency: str


class SalesTotalsResponse(BaseModel):
    totals: list[SalesTotalResponse]

    @classmethod
    def from_domain(cls, totals: list[SalesTotal]) -> "SalesTotalsResponse":
        return cls.model_validate({"totals": totals}, from_attributes=True)
