# The standard master data services in butterfly

Butterfly answers three real SAP master data services, read only, from the real `$metadata` and the sandbox samples saved in `docs/sap/standard/`. Study and sources: `docs/sap/master-data-mapping.md`. Each service was compared with the sandbox request by request (status, `@odata.context`, key order, JSON types, error code, message and category).

| Service | URL | Version |
|---|---|---|
| Product | `/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0001/` | V4 |
| Plant | `/sap/opu/odata4/sap/api_plant_2/srvd_a2x/sap/plant/0001/` | V4 |
| Business partner | `/sap/opu/odata/sap/API_BUSINESS_PARTNER/` | V2 (no V4 exists) |

## What is mirrored
- **Product:** `Product` (a row per sold and raw material: type `FERT` or `ROH`, group, base unit and ISO unit), `ProductDescription` (English), `ProductPlant` (a material only in the plants of its company), `ProductUnitOfMeasure` (the base unit). Search by number with `startswith`, by description on `ProductDescription` with `contains` or on `Product` through the `any` lambda; `$expand` of the three children; navigation paths.
- **Plant:** `Plant` with name, valuation area, sales and purchasing organization, channel `10`, division `00`, language `EN`. No company code (the real service has none).
- **Business partner:** `A_Customer`, `A_CustomerCompany`, `A_CustomerSalesArea`, `A_Supplier`, `A_SupplierCompany`, `A_SupplierPurchasingOrg`; customers and suppliers by company through the company rows; V2 search `substringof` and `startswith`; `$inlinecount`; `$expand` of the company, sales-area and purchasing-organization rows (shown only when the navigation is also selected, as in SAP).
- Query options as the sandbox: `$top`, `$skip`, `$count` or `$inlinecount`, `$orderby`, `$select`, `$filter`, `/$count`, key lookups; the real error bodies for unknown key, bad filter, unknown select or expand, unknown option and bad value. Every other entity set of each service answers an empty collection.

## What is butterfly's own
- The **plant to company table** (`PLANT_COMPANIES`: `1000`, `2000`, `3000` for `INA1`, `INA2`, `INA3`) and the plant names (company name plus "plant") are placeholders.
- Materials are the sold materials and the raw materials of the three companies, all with an English description; material groups from the inventory master.
- Customers and suppliers carry a name, an account group (`CUST`, `SUPL`), one company row, a sales area (customers) or a purchasing organization and purchasing group `001` (suppliers). Currency, payment terms, reconciliation account, address and country are empty.
- Etags are fixed strings, not SAP's.

## To confirm with the consultants
1. Which of `API_PRODUCT` (V4), `API_PLANT_2` (V4) and `API_BUSINESS_PARTNER` (V2) are active on the 2022 system.
2. The real plant to company mapping and plant names; which materials a company may use (the plants a material is held in).
3. The real customer and supplier numbers, names, company, sales area and purchasing organization assignments.
4. The description language (`EN`).
