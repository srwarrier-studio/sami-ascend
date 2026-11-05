# workspace-api/06 master-data

## Goal
workspace-api offers role-checked read routes for the lists the forms need (the user's plants, materials by plant, customers, suppliers), behind a gateway that calls butterfly's real product, plant and business partner services, so workspace-web can replace typed master data with dropdowns.

## Why
shared 14 (`docs/sap/master-data-mapping.md`) and butterfly 23 (`docs/sap/standard-master-data-in-butterfly.md`) give the real services. The requisition and sales order forms ask users to type material, plant, unit and customer. Version rule: V4 product and plant, V2 business partner (no V4 exists).

## Behavior
- **Gateway** `MasterDataGateway` (domain): `plants(plants)`, `materials(query, plants, top, skip)`, `customers(query, companies, top, skip)`, `suppliers(query, companies, top, skip)`. Entities `Plant` (`plant`, `name`), `Material` (`material`, `description`, `unit`, `iso_unit`, `material_group`, `material_type`, `plants`), `BusinessPartner` (`number`, `name`, `company_codes`), pages with `total`.
- **Implementations:** `ButterflyMasterDataGateway` (httpx; `SAP_PRODUCT_URL`, `SAP_PLANT_URL`, `SAP_PARTNER_URL`, defaults butterfly on port 8003) and a mock for tests.
  - Plants: the real `Plant` service, limited to the user's plants.
  - Materials: the plants' `ProductPlant` rows give the materials held there and their unit; a query matches the number (`startswith`) or the description (`contains` on `ProductDescription`); descriptions, group and type of the page come from `ProductDescription` and `Product`. Sorted by number.
  - Customers and suppliers: the company rows (`A_CustomerCompany`, `A_SupplierCompany`) of the user's companies give the numbers; names from `A_Customer`, `A_Supplier`; a query matches the number (`startswith`) or the name (`substringof`).
  - The join is done in workspace-api over at most `LIST_LIMIT` (1000) rows of each call; a ceiling to lift when real volumes need server side paging.
- **Routes** under `/v1/workspace/master-data`:
  - `GET /plants` (roles `purchase`, `sales`, `management`): the plants of the user's companies, `{plants: [{plant, name, company_code}]}`.
  - `GET /materials?q=&plant=&top=20&skip=0` (roles `purchase`, `sales`): materials held in the plant given, or in all the user's plants; a `plant` the user does not have is `403 COMPANY_NOT_ALLOWED`; `{materials, total}`.
  - `GET /customers?q=&top=20&skip=0` (role `sales`) and `GET /suppliers?q=&top=20&skip=0` (role `purchase`): the user's companies only, `{customers|suppliers: [{number, name, company_codes}], total}`.
  - `top` is 1 to 50, `skip` 0 or more, `q` at most 40 characters (anything else `422 INVALID_QUERY`); quotes in `q` are escaped, never sent raw.
- Same error mapping as workspace-api 05: `401`, `403`, `422 INVALID_QUERY`, `503 SAP_UNAVAILABLE` (no fallback data).
- Plants of a company are the `plants_by_company` setting of workspace-api 05 (placeholders until the consultants give the real ones).

## Acceptance cases
- A purchase user sees only the plants of their companies; a sales user sees customers of their companies only; a stores user gets `403`.
- Materials are limited to a plant of the user; searching by the start of a number and by a word of the description both find the material; the unit and the plants come with it.
- A `plant` of another company is `403`; a quote in `q` does not break the call.
- Each route answers `503` when butterfly is down, and `422` for a bad `top`, `skip` or long `q`.
- The gateway tests run against butterfly's real app in process (as in workspace-api 05), not hand-made responses.

## Out of scope
The screens (workspace-web 06), writes to master data, caching, other master data (cost centers, banks), real server side paging beyond the 1000 row ceiling.

## Depends on
butterfly 23 (the three services), workspace-api 05 (settings, roles, error handlers).
