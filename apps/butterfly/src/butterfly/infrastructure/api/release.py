import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from butterfly.application.usecase.change_purchase_requisition_item import RequisitionNotFound
from butterfly.application.usecase.release_purchase_requisition import ReleasePurchaseRequisition
from butterfly.domain.errors import ValidationDetail, ValidationFailed
from butterfly.infrastructure.api.standard.requisition import domain_failure

ROOT = "/butterfly/purchase-requisitions"


def build_release_router(release: ReleasePurchaseRequisition) -> APIRouter:
    router = APIRouter(prefix=ROOT)

    @router.post("/{number}/release")
    async def release_requisition(number: str, request: Request):
        try:
            payload = json.loads(await request.body())
            if not isinstance(payload, dict) or not isinstance(payload.get("ReleaseCode"), str) or set(payload) - {"ReleaseCode", "PurchaseRequisitionItem"}:
                raise ValidationFailed([ValidationDetail("INVALID_REQUEST_BODY", "Send ReleaseCode and optionally PurchaseRequisitionItem.", "body")])
            requisition = release.execute(number, payload["ReleaseCode"], payload.get("PurchaseRequisitionItem"))
        except ValueError:
            status, body = domain_failure(ValidationFailed([ValidationDetail("INVALID_REQUEST_BODY", "The request body must be JSON.", "body")]))
            return JSONResponse(body, status_code=status)
        except (ValidationFailed, RequisitionNotFound) as error:
            status, body = domain_failure(error)
            return JSONResponse(body, status_code=status)
        return {
            "PurchaseRequisition": requisition.purchase_requisition,
            "items": [
                {
                    "PurchaseRequisitionItem": i.purchase_requisition_item,
                    "PurReqnReleaseStatus": i.release_status,
                    "ReleaseCodesGiven": list(i.release_codes),
                    "ReleaseIsNotCompleted": i.release_is_not_completed,
                }
                for i in requisition.items
            ],
        }

    return router
