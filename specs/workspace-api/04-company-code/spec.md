# workspace-api/04 company-code

## Goal
A sales order is entered for one of the user's companies: the route takes `company_code`, refuses a company the user does not belong to, and sends `CompanyCode` to butterfly (butterfly 12 refuses an order without one).

## Behavior
- **token-verification** (the one shared package, named here because this spec says so): `Company` gains `code` (`sabinsa` is `INA1`, `neutraceuticals` is `INA2`, `organica` is `INA3`) and `Company.from_code(code)`, so every app maps between the token's companies and SAP company codes in one place.
- `POST /sales-orders` takes `company_code` (required, text of at most 4 characters). A code that is not one of the user's companies is `403` with `COMPANY_NOT_ALLOWED`; nothing is sent to SAP and nothing is queued. A user with no companies cannot create orders.
- The company code is part of the stored request, so a queued order is posted later with the same `CompanyCode` (no change to the queue rules).
- `GET /sales-orders` lists only orders of the user's companies (`CompanyCode eq ... or ...` in the filter to butterfly) and returns `company_code` and `country` on every order. A user with no companies gets an empty page.
- Butterfly's validation answers for the new field (`FIELD_REQUIRED`, `COMPANY_UNKNOWN`, a customer or material of another company is `CUSTOMER_UNKNOWN` or `MATERIAL_UNKNOWN`) already come through as `422 VALIDATION_FAILED` details; no new mapping.

## Acceptance cases
- `Company` codes: each company has its code, `from_code` finds it, an unknown code is refused.
- Create with a company of the user: butterfly receives `CompanyCode` and the response has `company_code` and `country`.
- Create with a company the user does not have: `403 COMPANY_NOT_ALLOWED`, no gateway call, no queue row.
- Create with no `company_code`: `422` from the request validation.
- A queued order keeps its company code and is posted with it by the worker after SAP recovers.
- List: the filter sent to butterfly names only the user's company codes; a user with two companies sees both, a user with none sees nothing.
- The butterfly integration tests run against butterfly 12 and pass (the failing `test_order_queue_butterfly` case passes again).

## Out of scope
The order form and company choice in workspace-web, a group view, order changes, currency rules (butterfly already validates the currency), real SAP company codes (butterfly consultant question 15).

## Depends on
butterfly 12 (data and contract), auth-api 04 (companies in the token).
