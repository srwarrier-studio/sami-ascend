# butterfly/23 standard-master-data

## Goal
Butterfly answers the real SAP master data services, read only, at SAP's own URLs and in SAP's formats: `API_PRODUCT` (V4), `API_PLANT_2` (V4) and `API_BUSINESS_PARTNER` (V2, customers and suppliers), over the master data it already holds, so workspace can build dropdowns against the real contract.

## Why
shared 14 (`docs/sap/master-data-mapping.md`, samples in `docs/sap/standard/api_product/`, `api_plant_2/`, `api_business_partner-v2/`) mapped what each form needs. The forms ask users to type material, plant, unit and customer; butterfly holds the data (materials with description, unit and price; customers; suppliers; plants) but offers no service to read it. Version rule: V4 for product and plant, V2 for business partner (no V4 exists, confirmed).

## Behavior
- **Product, V4:** `/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0001/` with `Product`, `ProductDescription`, `ProductPlant`, `ProductUnitOfMeasure`; `$metadata` is the saved real one, byte for byte; every other entity set answers an empty collection. Rows have every property of the real type in the real order and JSON types (a contract test against the saved sample rows).
  - `Product` = a material of butterfly (sales materials and the raw materials used for purchasing): `Product` the material number, `ProductType` (`FERT` finished, `ROH` raw), `ProductGroup` from the material group, `BaseUnit` the SAP unit and `BaseISOUnit` the ISO unit (the unit table of butterfly 21), `Division`.
  - `ProductDescription`: one row `EN` per material with its description.
  - `ProductPlant`: a material is held in the plants of its company (plant to company table below), so `Product` + `Plant` rows exist for those plants only.
  - `ProductUnitOfMeasure`: the base unit row of each material (`AlternativeUnit` = base unit, numerator and denominator 1).
- **Plant, V4:** `/sap/opu/odata4/sap/api_plant_2/srvd_a2x/sap/plant/0001/` with `Plant`: `Plant`, `PlantName`, `ValuationArea` (= plant), `SalesOrganization`, `DefaultPurchasingOrganization`, `Language`; real `$metadata`. A plant has no company code in the real service, so a company filter is not available there.
- **Business partner, V2:** `/sap/opu/odata/sap/API_BUSINESS_PARTNER/` with `A_Customer`, `A_CustomerCompany`, `A_CustomerSalesArea`, `A_Supplier`, `A_SupplierCompany`, `A_SupplierPurchasingOrg`; real `$metadata`; other sets empty. Customer and supplier numbers, names (`CustomerName`, `CustomerFullName`, `SupplierName`, `SupplierFullName`), company rows (`CompanyCode`, payment terms, currency) and sales area / purchasing organization rows come from butterfly's customers and suppliers. `d.results`, `__metadata`, `$inlinecount=allpages` as in the sandbox.
- **Query options as the sandbox:** V4 `$top`, `$skip`, `$count=true`, `$orderby`, `$select`, `$filter` with `eq`, `startswith`, `contains`, `and`, `or`, `$expand` (`_ProductDescription`), the `any` lambda on `_ProductDescription`, `/$count`; V2 `$top`, `$skip`, `$inlinecount`, `$orderby`, `$select`, `$filter`. The real error bodies for unknown key, bad filter and unknown option, taken from the saved samples.
- **Master data changes** (butterfly already holds most): the master data repository gains the suppliers and the raw materials of each company (from the company profiles), the material group of each material, and a plant to company table (`PLANT_COMPANIES`, today `1000`, `2000`, `3000` for `INA1`, `INA2`, `INA3`) used by the requisition service and by these services. Existing validation (`get_material`, `get_customer`, `company_exists`) is unchanged.
- **Read only.** No writes; the old services stay.

## Acceptance cases
- The three `$metadata` documents are the saved real ones, byte for byte.
- A list row of each entity has exactly the property names and JSON types of the saved sample row.
- Searching `Product` by `startswith` number and `ProductDescription` by `contains` description, paging with `$count`, `$expand=_ProductDescription` and the `any` lambda give the shapes of the saved samples.
- `ProductPlant` lists a material only for the plants of its company.
- A customer filtered through `A_CustomerCompany` by company code returns only that company's customers; same for suppliers.
- Every saved error sample is reproduced (status, code, message).
- Everything in the existing butterfly suite still passes.

## Out of scope
Writes to master data, the remaining entity sets with data (valuation, MRP, sales text, addresses, bank), other languages, the real SAP system, workspace-api and workspace-web (their own phases).

## Depends on
shared 14 (merged), butterfly 22 (the plant to company table is taken from its placeholders), butterfly 21 (the unit table).
