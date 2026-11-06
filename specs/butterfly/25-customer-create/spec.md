# butterfly/25 customer-create

## Goal
Butterfly accepts the real SAP create for a customer: `POST A_BusinessPartner` with a deep insert (roles, address, customer, company and sales area rows) on `API_BUSINESS_PARTNER`, takes the number from `NumberRange`, refuses in SAP's error body, and the new customer shows in the existing read services and in the Customer dropdown.

## Why
shared 15 (`docs/sap/customer-onboarding.md`) fixed the SAP side: a customer is created through a business partner with roles `FLCU00` and `FLCU01`, in one request, all or nothing. workspace-api 08 creates customers through this call when `master-data` finishes a request. The sandbox is read only, so the create is mirrored from the saved definitions and public notes, not exercised; the consultant questions stay open (`docs/sap/consultant-questions.md`).

## Behavior
- **Route.** `POST /sap/opu/odata/sap/API_BUSINESS_PARTNER/A_BusinessPartner`, V2 dialect (`d`, `__metadata`), answers `201` with the created business partner row, `BusinessPartner` filled.
- **Deep insert.** The body may carry `to_BusinessPartnerRole`, `to_BusinessPartnerAddress` (with `Country`, `CityName`, `PostalCode`, `StreetName`, `HouseNumber`, `Region`, `Language`), `to_BusinessPartnerTax` and `to_Customer` with `to_CustomerCompany` and `to_CustomerSalesArea`. Saved in one step or not at all.
- **Number.** Not sent: next free number from a new `CUSTOMER` range in `NumberRange` (placeholder range, the real one is consultant question 1). Sent: kept if free, refused if taken. `Customer` equals `BusinessPartner` (assumption 6), shown without leading zeros as in butterfly 24.
- **Refusals** in the V2 error body (`error.code`, `error.message.value`), with SAP-style messages: no name; category not `2`; no `FLCU00`/`FLCU01` role when `to_Customer` is sent; no address country; unknown country, company code, currency; unknown sales organization for the company; number taken; number range full (`NumberRangeFull`).
- **Store.** `Customer` gains the fields the create carries (grouping, account group, search term, address, language, payment terms, reconciliation account, currency, incoterms, tax number) with defaults, so existing seed customers and orders do not change. Both repos (memory, SQLite) get `add_customer`; an older database is rebuilt as in earlier phases.
- **Reads.** `A_BusinessPartner` (new entity set from the saved definition), `A_Customer`, `A_CustomerCompany`, `A_CustomerSalesArea`, `A_BusinessPartnerAddress` and the role set show the new customer; the Customer dropdown (`list_customers`) and the sales order create find it.
- **Not built:** change, block, delete; credit limit (not in this service); suppliers and materials; real number format and codes.

## Acceptance cases
- Deep insert with both roles, address and company and sales area rows returns `201`; the customer is then read from every set above.
- Without a number the next one of the range is used; two creates give two numbers; a sent number that exists is refused.
- Each refusal listed gives its status, code and message, and stores nothing (all or nothing).
- A customer created here can be used by the standard and the custom sales order create.
- The existing butterfly suite passes unchanged.

## Out of scope
workspace-api 08 and workspace-web 11 (request flow), credit limit, supplier and material create, the real number format and codes.

## Depends on
shared 15, butterfly 23 (master data services), butterfly 24 (`NumberRange`, ALPHA).
