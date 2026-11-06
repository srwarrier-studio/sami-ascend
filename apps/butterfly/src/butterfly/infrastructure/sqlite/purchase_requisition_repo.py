from datetime import date

from butterfly.domain.entities.number_range import PURCHASE_REQUISITION
from butterfly.domain.entities.purchase_requisition import PurchaseRequisition, PurchaseRequisitionItem
from butterfly.domain.repositories.purchase_requisition_repo import PurchaseRequisitionRepo
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.mappers import moment
from butterfly.infrastructure.sqlite.money import from_minor, quantity_from_minor, quantity_to_minor, to_minor
from butterfly.infrastructure.sqlite.seeder import iso, marks

CODE_SEPARATOR = ","


def item_from_row(row) -> PurchaseRequisitionItem:
    return PurchaseRequisitionItem(
        purchase_requisition=row["purchase_requisition"],
        purchase_requisition_item=row["purchase_requisition_item"],
        material=row["material"],
        item_text=row["item_text"],
        material_group=row["material_group"],
        requested_quantity=quantity_from_minor(row["requested_quantity"]),
        base_unit=row["base_unit"],
        price=from_minor(row["price"]),
        currency=row["currency"],
        plant=row["plant"],
        company_code=row["company_code"],
        purchasing_organization=row["purchasing_organization"],
        purchasing_group=row["purchasing_group"],
        delivery_date=date.fromisoformat(row["delivery_date"]),
        release_status=row["release_status"],
        processing_status=row["processing_status"],
        release_codes=tuple(code for code in row["release_codes"].split(CODE_SEPARATOR) if code),
        ordered_quantity=quantity_from_minor(row["ordered_quantity"]),
        purchasing_document=row["purchasing_document"],
        purchasing_document_item=row["purchasing_document_item"],
        supplier=row["supplier"],
        is_deleted=bool(row["is_deleted"]),
    )


def item_values(i: PurchaseRequisitionItem) -> tuple:
    return (
        i.purchase_requisition, i.purchase_requisition_item, i.material, i.item_text, i.material_group, quantity_to_minor(i.requested_quantity), i.base_unit,
        to_minor(i.price), i.currency, i.plant, i.company_code, i.purchasing_organization, i.purchasing_group, iso(i.delivery_date), i.release_status,
        i.processing_status, CODE_SEPARATOR.join(i.release_codes), quantity_to_minor(i.ordered_quantity), i.purchasing_document, i.purchasing_document_item,
        i.supplier, int(i.is_deleted),
    )


class SqlitePurchaseRequisitionRepo(PurchaseRequisitionRepo):
    def __init__(self, db: Database):
        self.db = db

    def list_all(self) -> list[PurchaseRequisition]:
        items: dict[str, list[PurchaseRequisitionItem]] = {}
        for row in self.db.query("SELECT * FROM purchase_requisition_item ORDER BY rowid"):
            items.setdefault(row["purchase_requisition"], []).append(item_from_row(row))
        return [self.build(row, items.get(row["purchase_requisition"], [])) for row in self.db.query("SELECT * FROM purchase_requisition ORDER BY rowid")]

    def get(self, purchase_requisition: str) -> PurchaseRequisition | None:
        rows = self.db.query("SELECT * FROM purchase_requisition WHERE purchase_requisition = ?", (purchase_requisition,))
        if not rows:
            return None
        items = self.db.query("SELECT * FROM purchase_requisition_item WHERE purchase_requisition = ? ORDER BY rowid", (purchase_requisition,))
        return self.build(rows[0], [item_from_row(row) for row in items])

    def build(self, row, items: list[PurchaseRequisitionItem]) -> PurchaseRequisition:
        return PurchaseRequisition(
            row["purchase_requisition"], row["requisition_type"], row["description"], row["created_by_user"],
            moment(row["creation_date_time"]), moment(row["last_change_date_time"]), items,
        )

    def next_number(self) -> str:
        taken = [row["purchase_requisition"] for row in self.db.query("SELECT purchase_requisition FROM purchase_requisition")]
        return PURCHASE_REQUISITION.next(taken)

    def add(self, requisition: PurchaseRequisition) -> None:
        with self.db.transaction():
            self.db.execute(
                f"INSERT INTO purchase_requisition VALUES ({marks(6)})",
                (requisition.purchase_requisition, requisition.requisition_type, requisition.description, requisition.created_by_user,
                 iso(requisition.creation_date_time), iso(requisition.last_change_date_time)),
            )
            self.write_items(requisition)

    def update(self, requisition: PurchaseRequisition) -> None:
        with self.db.transaction():
            self.db.execute(
                "UPDATE purchase_requisition SET requisition_type = ?, description = ?, last_change_date_time = ? WHERE purchase_requisition = ?",
                (requisition.requisition_type, requisition.description, iso(requisition.last_change_date_time), requisition.purchase_requisition),
            )
            self.db.execute("DELETE FROM purchase_requisition_item WHERE purchase_requisition = ?", (requisition.purchase_requisition,))
            self.write_items(requisition)

    def write_items(self, requisition: PurchaseRequisition) -> None:
        self.db.insert_many(f"INSERT INTO purchase_requisition_item VALUES ({marks(22)})", [item_values(item) for item in requisition.items])
