# Inventory OData V4 contract

Source of truth for butterfly (mock SAP), the synapse gateways and the SAP consultant for stock:
what is on hand, what moved, and what it is worth. If this file and any other document disagree,
this file wins. Everything here is read-only.

Types, `$filter` literals, `$select`, `$orderby`, `$top`, `$skip`, `$count` and the error format
are exactly as in `sales-contract.md` (sections 3, 4 and 7). `$expand` is not supported. A summary
takes the same query options as any other entity and needs the whole key in `$orderby` when paged.

## 1. Service

| Item | Value |
|------|-------|
| Service definition / binding | `ZUI_INVENTORY_O4` (OData V4, UI-less web API) |
| Root path | `/sap/opu/odata4/sap/zui_inventory_o4/srvd_a2x/sap/zinventory/0001/` |
| Format | JSON only (`Accept: application/json`) |

All paths below are relative to the root. Reads are `GET {root}<Entity>` with query options;
reading one row by key is not supported.

## 2. Entities

Nullable `No` means the field is always present in responses. A "warehouse" in the apps is a
storage location (`StorageLocation`) of a plant.

### MaterialStock (key: `Material`, `Plant`, `StorageLocation`)

One row per material in a storage location with stock on hand now, including rows with zero stock.
Unrestricted-use stock only (blocked and quality stock are not counted).

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `Material` | `Edm.String` (40) | No | `"RAW-2002"` |
| `MaterialDescription` | `Edm.String` (40) | Yes | `"Black pepper, whole"` |
| `MaterialGroup` | `Edm.String` (9) | No | `"RAW-BOTANIC"` |
| `MaterialGroupName` | `Edm.String` (60) | Yes | `"Botanical raw materials"` |
| `Plant` | `Edm.String` (4) | No | `"1000"` |
| `StorageLocation` | `Edm.String` (4) | No | `"0001"` |
| `StorageLocationName` | `Edm.String` (16) | Yes | `"Raw material store"` |
| `StockQuantity` | `Edm.Decimal` (13,3) | No | `"18250.000"` |
| `QuantityUnit` | `Edm.String` (3) | No | `"KG"` |
| `StockValue` | `Edm.Decimal` (15,2) | No | `"1186250.00"` |
| `Currency` | `Edm.String` (5) | No | `"INR"` |
| `ReorderLevel` | `Edm.Decimal` (13,3) | No | `"6000.000"` |
| `StockStatus` | `Edm.String` (1) | No | `"O"` |
| `LastMovementDate` | `Edm.Date` | Yes | `"2026-10-28"` |
| `CompanyCode` | `Edm.String` (4) | No | `"INA1"` |

`StockValue` is the stock valued at the material's valuation price in the plant's currency.
`ReorderLevel` is the reorder point of the material in the plant (`0` when none is set).
`LastMovementDate` is the posting date of the latest goods movement of the material in the
location; it is empty when there has been none.

### StockMovement (key: `MaterialDocument`, `MaterialDocumentItem`, `MaterialDocumentYear`)

One row per goods movement item (goods receipt, goods issue, transfer). Cancelled documents and
their reversals are left out.

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `MaterialDocument` | `Edm.String` (10) | No | `"4900001234"` |
| `MaterialDocumentItem` | `Edm.String` (4) | No | `"0001"` |
| `MaterialDocumentYear` | `Edm.String` (4) | No | `"2026"` |
| `PostingDate` | `Edm.Date` | No | `"2026-10-28"` |
| `EntryDateTime` | `Edm.DateTimeOffset` | No | `"2026-10-28T10:42:15Z"` |
| `Material` | `Edm.String` (40) | No | `"RAW-2002"` |
| `MaterialDescription` | `Edm.String` (40) | Yes | `"Black pepper, whole"` |
| `Plant` | `Edm.String` (4) | No | `"1000"` |
| `StorageLocation` | `Edm.String` (4) | No | `"0001"` |
| `MovementType` | `Edm.String` (3) | No | `"101"` |
| `DebitCreditCode` | `Edm.String` (1) | No | `"S"` |
| `Quantity` | `Edm.Decimal` (13,3) | No | `"5000.000"` |
| `QuantityUnit` | `Edm.String` (3) | No | `"KG"` |
| `Amount` | `Edm.Decimal` (15,2) | No | `"260000.00"` |
| `Currency` | `Edm.String` (5) | No | `"INR"` |
| `CompanyCode` | `Edm.String` (4) | No | `"INA1"` |

`EntryDateTime` is when the document was entered (the document header's entry date and time, in
UTC). `Amount` is the movement valued in the plant's currency and is never negative.

### Summaries (read-only)

Aggregated by SAP so a consumer never pages through stock rows or movements to total them. All
amounts are in `Currency`; a summary has one row per currency and company.

| Entity | Key | Fields besides the key | Built from |
|--------|-----|------------------------|------------|
| `StockSummaryByWarehouse` | `Plant`, `StorageLocation`, `Currency`, `CompanyCode` | `StorageLocationName`, `StockValue`, `MaterialCount` | `MaterialStock` |
| `StockSummaryByMaterialGroup` | `MaterialGroup`, `Currency`, `CompanyCode` | `MaterialGroupName`, `StockValue`, `MaterialCount` | `MaterialStock` |
| `StockSummaryByStatus` | `StockStatus`, `Currency`, `CompanyCode` | `StockValue`, `MaterialCount` | `MaterialStock` |
| `StockValueByMonth` | `PostingPeriod`, `Currency`, `CompanyCode` | `StockValue` | valuation history |
| `StockMovementSummaryByDay` | `PostingDate`, `Currency`, `CompanyCode` | `ReceiptValue`, `IssueValue`, `MovementCount` | `StockMovement` |
| `StockMovementSummaryByHour` | `PostingDate`, `PostingHour`, `CompanyCode` | `MovementCount` | `StockMovement` |

Types: `StockValue`, `ReceiptValue`, `IssueValue` are `Edm.Decimal` (15,2); `MaterialCount` and
`MovementCount` are `Edm.Int32`; `PostingHour` is `Edm.Int32` (0 to 23, from `EntryDateTime` in
UTC); `PostingPeriod` is `Edm.String` (7) as `"2026-10"`. `MaterialCount` counts material and
location rows. `StockValueByMonth` is the stock value at the end of the month, and for the current
month the value now; months before the first valuation have no row.

## 3. Codes

| Field | Value | Meaning |
|-------|-------|---------|
| `StockStatus` | `O` | At or above the reorder level (or no reorder level is set and there is stock) |
| | `L` | Low: stock is above zero and below `ReorderLevel` |
| | `Z` | Zero: no stock |
| `DebitCreditCode` | `S` | Debit: stock goes up (a receipt) |
| | `H` | Credit: stock goes down (an issue) |
| `MovementType` | `101` | Goods receipt for a purchase order |
| | `131` | Goods receipt from production |
| | `261` | Goods issue to a production order |
| | `601` | Goods issue for a delivery to a customer |
| | `561` | Initial entry of stock balances |
| | `702` | Inventory difference, issue (stock count) |

Filter and compare codes as written. `StockStatus` is derived by SAP because a `$filter` cannot
compare one field with another. Other movement types may appear in real data and are returned as
they are; the apps read only these.

## 4. How the entities connect

| From | To | Join |
|------|----|------|
| `MaterialStock.Material` | `PurchaseDelivery.Material`, `SalesOrder` items `Material`, `ProductionOrder.Material` | same material (`drivers-contract.md`, `sales-contract.md`) |
| `StockMovement` 101 | `PurchaseDelivery` | a receipt posts on the `ActualDeliveryDate` for the delivered quantity |
| `StockMovement` 131 | `ProductionOrder` | a receipt posts on the `ActualEndDate` for the confirmed quantity |
| `StockMovement` 261 | `ProductionOrderComponent` | an issue for the components of the order |
| `StockMovement` 601 | `SalesOrder` items | an issue for the quantity ordered |
| `MaterialStock.MaterialGroup` | the material master (`MARA-MATKL`) | one group per material |

## 5. Reads

All examples use the root path from section 1. `{root}` stands for it. The responses are real and are
checked by a test against the data of 2026-10-31.

### Items below the reorder level

```
GET {root}MaterialStock?$filter=StockStatus ne 'O'&$orderby=Material,Plant,StorageLocation&$top=2
```

```json
{
  "@odata.context": "$metadata#MaterialStock",
  "value": [
    {
      "Material": "NRAW-2005",
      "MaterialDescription": "Vitamin C and zinc premix",
      "MaterialGroup": "ACTIVE",
      "MaterialGroupName": "Active ingredients and premixes",
      "Plant": "2000",
      "StorageLocation": "0001",
      "StorageLocationName": "Raw material store",
      "StockQuantity": "0.000",
      "QuantityUnit": "KG",
      "StockValue": "0.00",
      "Currency": "INR",
      "ReorderLevel": "2840.905",
      "StockStatus": "Z",
      "LastMovementDate": "2026-10-31",
      "CompanyCode": "INA2"
    },
    {
      "Material": "NU-1004",
      "MaterialDescription": "Turmeric complex softgel 500mg",
      "MaterialGroup": "DOSAGE",
      "MaterialGroupName": "Finished dosage forms",
      "Plant": "2000",
      "StorageLocation": "0002",
      "StorageLocationName": "Finished goods store",
      "StockQuantity": "11685.885",
      "QuantityUnit": "EA",
      "StockValue": "98161.43",
      "Currency": "INR",
      "ReorderLevel": "58429.427",
      "StockStatus": "L",
      "LastMovementDate": "2026-10-30",
      "CompanyCode": "INA2"
    }
  ]
}
```

### Movements of a material in a period

```
GET {root}StockMovement?$filter=Material eq 'RAW-2002' and PostingDate ge 2026-10-01 and PostingDate le 2026-10-31&$orderby=PostingDate,MaterialDocument,MaterialDocumentItem,MaterialDocumentYear&$top=2
```

```json
{
  "@odata.context": "$metadata#StockMovement",
  "value": [
    {
      "MaterialDocument": "4900009696",
      "MaterialDocumentItem": "0001",
      "MaterialDocumentYear": "2026",
      "PostingDate": "2026-10-06",
      "EntryDateTime": "2026-10-06T10:48:00Z",
      "Material": "RAW-2002",
      "MaterialDescription": "Black pepper, whole",
      "Plant": "1000",
      "StorageLocation": "0001",
      "MovementType": "261",
      "DebitCreditCode": "H",
      "Quantity": "4400.000",
      "QuantityUnit": "KG",
      "Amount": "228800.00",
      "Currency": "INR",
      "CompanyCode": "INA1"
    },
    {
      "MaterialDocument": "4900009954",
      "MaterialDocumentItem": "0001",
      "MaterialDocumentYear": "2026",
      "PostingDate": "2026-10-16",
      "EntryDateTime": "2026-10-16T16:42:00Z",
      "Material": "RAW-2002",
      "MaterialDescription": "Black pepper, whole",
      "Plant": "1000",
      "StorageLocation": "0001",
      "MovementType": "101",
      "DebitCreditCode": "S",
      "Quantity": "5000.000",
      "QuantityUnit": "KG",
      "Amount": "260000.00",
      "Currency": "INR",
      "CompanyCode": "INA1"
    }
  ]
}
```

### Further reads (examples are added with the summaries)

- Stock of one group: `{root}StockSummaryByMaterialGroup?$filter=CompanyCode eq 'INA1'&$orderby=MaterialGroup,Currency,CompanyCode`
- Receipts and issues per day: `{root}StockMovementSummaryByDay?$filter=PostingDate ge 2026-10-01&$orderby=PostingDate,Currency,CompanyCode`
- Stock value at each month end: `{root}StockValueByMonth?$orderby=PostingPeriod,Currency,CompanyCode`

## 6. Notes for the SAP consultant

These are the usual SAP sources; confirm them and expose each entity as a read-only CDS view
entity with a projection, in the same service binding.

| Entity | Usual source |
|--------|--------------|
| `MaterialStock` | stock by storage location (`MARD`, or `I_MaterialStock_2`), valuation (`MBEW`) for the value, reorder point from plant data (`MARC-MINBE`), group and text from the material master (`MARA-MATKL`, `T023T`), storage location text (`T001L`) |
| `StockMovement` | material documents (`MKPF`, `MSEG`, or `I_MaterialDocumentItem_2`) with the document header for the entry date and time |
| `StockSummaryBy*` | aggregate CDS views over `MaterialStock`, so SAP does the totalling |
| `StockValueByMonth` | valuation history by period (`MBEWH`) |
| `StockMovementSummaryBy*` | aggregate CDS views over `StockMovement` (sum of `Amount` by `DebitCreditCode`, count of items) |

The data is read with the shared management login, so the app limits who can ask for it (role
`management` or `admin`). Large tables must be selective on the filter fields used above:
`Material`, `Plant`, `StorageLocation`, `PostingDate`, `StockStatus`.
