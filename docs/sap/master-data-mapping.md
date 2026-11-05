# Master data for the forms: SAP mapping

Source tags: **[sample]** real Hub sandbox response saved under `docs/sap/standard/<service>/`; **[assumption]** to confirm (see the table at the end). Method as in `docs/sap/p2p-mapping.md`. Base URL of the sandbox: `https://sandbox.api.sap.com/s4hanacloud`.

## Summary
| Need | Service | Version | Entity | Decision |
|---|---|---|---|---|
| Material (number, description, base unit, group) | `API_PRODUCT` | **V4** | `Product`, `ProductDescription` | standard |
| Materials available in a plant | `API_PRODUCT` | V4 | `ProductPlant` | standard |
| Alternative units of a material | `API_PRODUCT` | V4 | `ProductUnitOfMeasure` | standard (not needed for the forms) |
| Plant | `API_PLANT_2` | **V4** | `Plant` | standard, plus a gap: no company code |
| Customer | `API_BUSINESS_PARTNER` | V2 (no V4 found) | `A_Customer`, `A_CustomerCompany`, `A_CustomerSalesArea` | standard |
| Supplier | `API_BUSINESS_PARTNER` | V2 (no V4 found) | `A_Supplier`, `A_SupplierCompany`, `A_SupplierPurchasingOrg` | standard |
| Unit of measure list | none found (`API_PRODUCT_UOM_SRV` answers 403) | | | not needed: the unit follows the material |

## Product (materials)
**Service.** `API_PRODUCT` V4, `/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0001/` [sample]. Saved: `docs/sap/standard/api_product/`. V2 `API_PRODUCT_SRV` also answers; V4 is used (version rule). 2022 on-premise availability **to confirm with consultants**.

**Entities** [sample metadata]: `Product` (key `Product`), `ProductDescription` (`Product` + `Language`), `ProductPlant` (`Product` + `Plant`), `ProductUnitOfMeasure` (`Product` + `AlternativeUnit`), plus sales, procurement, storage, valuation and other sets not needed here.

**Fields workspace needs** [sample]:
- `Product` (the material number, 2,711 in the sandbox), `ProductType` (`SERV`, `ROH`, ...), `ProductGroup` (the material group, e.g. `P001`), `BaseUnit` (SAP unit, e.g. `H`, `EA`) and `BaseISOUnit` (`HUR`), `Division`.
- `ProductDescription.ProductDescription` by `Language` (`EN`, `ZH`, `TH`, ...): the description is not on `Product`; it is read with `$expand=_ProductDescription` or from its own entity set.
- `ProductPlant.Product`, `ProductPlant.Plant`, `BaseUnit`: which plants hold the material.

**Search and paging** [sample]:
- By number: `Product?$filter=startswith(Product,'MZ')&$select=Product,BaseUnit` works.
- By description: `ProductDescription?$filter=contains(ProductDescription,'Pump')&$count=true` works (39 hits); the same search from `Product` needs the lambda `_ProductDescription/any(d:contains(d/ProductDescription,'Pump'))` (a path through a collection without `any` is refused with `/IWCOR/CX_OD_EXPR_PARSER_ERROR`).
- `$top`, `$skip`, `$orderby`, `$select`, `$count=true` (`@odata.count`) work; `$expand=_ProductDescription` works.
- Errors: unknown key 404 `/IWBEP/CM_V4S_RUN/000`; bad filter 400 `/IWCOR/CX_OD_EXPR_PARSER_ERROR`.

**The unit follows the material.** `BaseUnit` of the product is what a requisition item takes; a form needs no unit input. A material also has alternative units in `ProductUnitOfMeasure` (with `QuantityNumerator`, `QuantityDenominator`), not needed for the first version.

## Plant
**Service.** `API_PLANT_2` V4, `/sap/opu/odata4/sap/api_plant_2/srvd_a2x/sap/plant/0001/` [sample]. Saved: `docs/sap/standard/api_plant_2/`. The first guess `api_plant` answers 403, `api_plant_2` is the real name.

**Fields** [sample]: `Plant` (key), `PlantName` (`Plant 1 US`), `ValuationArea` (equal to the plant in the sample), `SalesOrganization`, `DefaultPurchasingOrganization`, `DistributionChannel`, `Division`, `PlantCustomer`, `PlantSupplier`, `FactoryCalendar`, `AddressID`, `Language`.

**Gap: no company code.** The plant carries no company code. In SAP the company of a plant comes through the valuation area (customizing), which is not in this service. The user's companies must therefore be matched to plants outside the API: butterfly keeps a plant-to-company table (today `1000`, `2000`, `3000` for `INA1`, `INA2`, `INA3`, placeholders) **[assumption]**, replaced by the real mapping from the consultants.

Errors [sample]: unknown key 404 `/IWBEP/CM_V4S_RUN/000`; bad filter 400.

## Customer
**Service.** `API_BUSINESS_PARTNER` V2, `/sap/opu/odata/sap/API_BUSINESS_PARTNER/` [sample]. Saved: `docs/sap/standard/api_business_partner-v2/`. The V4 guesses tried (`api_businesspartner`, `api_businesspartner_2`, `api_business_partner`, `api_customer`) all answer 403, so no V4 was found; **to confirm by searching the Hub for a V4 business partner or customer API**.

**Fields** [sample]: `A_Customer`: `Customer` (key), `CustomerName`, `CustomerFullName`, `CustomerAccountGroup`, and more. By company: `A_CustomerCompany` (`Customer` + `CompanyCode`, `PaymentTerms`, `ReconciliationAccount`), by sales area: `A_CustomerSalesArea` (`SalesOrganization`, `DistributionChannel`, `Division`, `Currency`). Navigations from `A_Customer`: `to_CustomerCompany`, `to_CustomerSalesArea`.

**Search and paging** [sample]: `$filter=startswith(Customer,'1000')`, `$top`, `$inlinecount=allpages` (`d.__count`). Errors: V2 body `error.message.value`: `Property Nope not found in type A_CustomerType`; unknown key 404.

## Supplier
Same service [sample]. `A_Supplier`: `Supplier` (key), `SupplierName`, `SupplierFullName`, `SupplierAccountGroup`; `A_SupplierCompany` (`Supplier` + `CompanyCode`, `CompanyCodeName`, `Currency`, `PaymentTerms`); `A_SupplierPurchasingOrg` (`PurchasingOrganization`, `PurchasingGroup`, `PurchaseOrderCurrency`). Navigations `to_SupplierCompany`, `to_SupplierPurchasingOrg`. Needed for the purchase order step (supplier of an order).

## What this means for the forms
- **Requisition item:** material (search by number or description, limited to materials held by the chosen plant through `ProductPlant`), plant (the user's plants only), unit shown from the material's `BaseUnit`, never typed.
- **Sales order:** customer (search by name or number, limited to the user's companies through `A_CustomerCompany`), material the same way, unit from the material.
- Descriptions are language dependent; the forms use `EN` **[assumption]**.

## Assumptions (all to confirm)
| # | Assumption | Who |
|---|---|---|
| 1 | Which of `API_PRODUCT` (V4), `API_PLANT_2` (V4) and `API_BUSINESS_PARTNER` (V2) are available and activated on the 2022 on-premise system | consultants |
| 2 | A V4 business partner, customer or supplier API exists on the Hub | owner (Hub search) |
| 3 | Plant to company mapping (the API does not give it) | consultants |
| 4 | Which materials a company may use is decided by the plant (`ProductPlant`) | consultants |
| 5 | Description language `EN` | owner |
| 6 | The real material numbers, units and plants of the three companies (the sandbox data is SAP demo data) | consultants |

## Follow-up plan (for the owner to agree before any code)
| Order | Phase | Size |
|---|---|---|
| 1 | butterfly: the three services over butterfly's master data (`API_PRODUCT` V4 with product, description, plant of product; `API_PLANT_2` V4; `API_BUSINESS_PARTNER` V2 customer and supplier sets), real metadata, search and paging as in the samples, plant-to-company table | L |
| 2 | workspace-api: read routes for the user's plants, material search (by plant, number or description), customer and supplier search, limited to the user's companies | M |
| 3 | workspace-web: a searchable select for material, plant and customer; the requisition form and the sales order form use them; the unit is shown from the material and no longer typed | M |

Butterfly's internal master data (`MasterDataRepo`) keeps validating writes; the new services only read it.
