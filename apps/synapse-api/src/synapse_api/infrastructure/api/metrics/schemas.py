from decimal import Decimal

from pydantic import BaseModel

from synapse_api.domain.entities.compare import Comparison, MonthFigure
from synapse_api.domain.entities.registry import Metric


class ChangeRowResponse(BaseModel):
    key: str
    name: str
    current: Decimal
    previous: Decimal
    change: Decimal
    share_of_change_percent: Decimal | None
    unit: str | None = None
    quantity_current: Decimal | None = None
    quantity_previous: Decimal | None = None
    price_current: Decimal | None = None
    price_previous: Decimal | None = None
    volume_effect: Decimal | None = None
    price_effect: Decimal | None = None


class ComparisonResponse(BaseModel):
    currency: str
    current: Decimal
    previous: Decimal
    change: Decimal
    change_percent: Decimal | None
    rows: list[ChangeRowResponse] | None


class CompareResponse(BaseModel):
    comparisons: list[ComparisonResponse]

    @classmethod
    def from_domain(cls, comparisons: list[Comparison]) -> "CompareResponse":
        return cls.model_validate({"comparisons": comparisons}, from_attributes=True)


class TrendMonthResponse(BaseModel):
    year: int
    month: int
    net_amount: Decimal


class MonthFigureResponse(BaseModel):
    currency: str
    net_amount: Decimal
    order_count: int | None
    previous_change_percent: Decimal | None
    complete: bool
    trend: list[TrendMonthResponse]


class MonthResponse(BaseModel):
    figures: list[MonthFigureResponse]

    @classmethod
    def from_domain(cls, figures: list[MonthFigure]) -> "MonthResponse":
        return cls.model_validate({"figures": figures}, from_attributes=True)


class DimensionResponse(BaseModel):
    name: str
    splits_volume_and_price: bool


class MetricResponse(BaseModel):
    name: str
    label: str
    dimensions: list[DimensionResponse]


class MetricsResponse(BaseModel):
    metrics: list[MetricResponse]

    @classmethod
    def from_domain(cls, metrics: list[Metric]) -> "MetricsResponse":
        return cls(
            metrics=[
                MetricResponse(
                    name=m.name,
                    label=m.label,
                    dimensions=[DimensionResponse(name=d.name, splits_volume_and_price=d.quantity is not None) for d in m.dimensions.values() if d.name != "day"],
                )
                for m in metrics
            ]
        )
