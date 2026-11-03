from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class WorkCenter:
    plant: str
    code: str
    name: str
    company_code: str


@dataclass(frozen=True)
class ProductionConfirmation:
    confirmation_number: str
    confirmation_counter: str
    production_order: str
    material: str
    material_description: str | None
    plant: str
    work_center: str
    work_center_name: str | None
    shift: str
    posting_date: date
    yield_quantity: Decimal
    scrap_quantity: Decimal
    target_quantity: Decimal
    quantity_unit: str
    scrap_reason: str | None
    run_hours: Decimal
    yield_value: Decimal
    scrap_value: Decimal
    target_value: Decimal
    currency: str
    company_code: str


@dataclass(frozen=True)
class WorkCenterDowntime:
    downtime_number: str
    production_order: str | None
    plant: str
    work_center: str
    work_center_name: str | None
    posting_date: date
    downtime_hours: Decimal
    downtime_cause: str
    company_code: str
