from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class MaterialGroup:
    code: str
    name: str


@dataclass(frozen=True)
class StorageLocation:
    plant: str
    code: str
    name: str
    company_code: str


@dataclass(frozen=True)
class MaterialStock:
    material: str
    material_description: str | None
    material_group: str
    material_group_name: str | None
    plant: str
    storage_location: str
    storage_location_name: str | None
    stock_quantity: Decimal
    quantity_unit: str
    stock_value: Decimal
    currency: str
    reorder_level: Decimal
    last_movement_date: date | None
    company_code: str

    @property
    def stock_status(self) -> str:
        if self.stock_quantity == 0:
            return "Z"
        return "L" if self.stock_quantity < self.reorder_level else "O"


@dataclass(frozen=True)
class StockMovement:
    material_document: str
    material_document_item: str
    material_document_year: str
    posting_date: date
    entry_date_time: datetime
    material: str
    material_description: str | None
    plant: str
    storage_location: str
    movement_type: str
    debit_credit_code: str
    quantity: Decimal
    quantity_unit: str
    amount: Decimal
    currency: str
    company_code: str


@dataclass(frozen=True)
class StockValueMonth:
    posting_period: str
    stock_value: Decimal
    currency: str
    company_code: str


@dataclass(frozen=True)
class MaterialGroupAssignment:
    material: str
    material_group: str
