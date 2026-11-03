# Production OData V4 contract

Source of truth for butterfly (mock SAP), the synapse gateways and the SAP consultant for what the
shop floor did: confirmed output, scrap and downtime per work center and shift. Production orders
themselves are in `drivers-contract.md` (`ProductionOrder`, `ProductionOrderComponent`). If this file
and any other document disagree, this file wins. Everything here is read-only.

Types, `$filter` literals, `$select`, `$orderby`, `$top`, `$skip`, `$count` and the error format are
exactly as in `sales-contract.md` (sections 3, 4 and 7). `$expand` is not supported. A summary takes
the same query options as any other entity and needs the whole key in `$orderby` when paged.

## 1. Service

| Item | Value |
|------|-------|
| Service definition / binding | `ZUI_PRODUCTION_O4` (OData V4, UI-less web API) |
| Root path | `/sap/opu/odata4/sap/zui_production_o4/srvd_a2x/sap/zproduction/0001/` |
| Format | JSON only (`Accept: application/json`) |

All paths below are relative to the root. Reads are `GET {root}<Entity>` with query options; reading
one row by key is not supported.

## 2. Entities

Nullable `No` means the field is always present in responses. A "line" in the apps is a work center
(`WorkCenter`). Values are the quantity valued at the standard price of the material, so output of
materials counted in different units can be added.

### ProductionConfirmation (key: `ConfirmationNumber`, `ConfirmationCounter`)

One row per confirmation of a production order: what one work center produced in one shift. Cancelled
confirmations and their reversals are left out.

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `ConfirmationNumber` | `Edm.String` (10) | No | `"0000812345"` |
| `ConfirmationCounter` | `Edm.String` (8) | No | `"00000001"` |
| `ProductionOrder` | `Edm.String` (10) | No | `"0001000417"` |
| `Material` | `Edm.String` (40) | No | `"RM-1002"` |
| `MaterialDescription` | `Edm.String` (40) | Yes | `"Piperine extract 95%"` |
| `Plant` | `Edm.String` (4) | No | `"1000"` |
| `WorkCenter` | `Edm.String` (8) | No | `"LINE1"` |
| `WorkCenterName` | `Edm.String` (40) | Yes | `"Line 1"` |
| `Shift` | `Edm.String` (1) | No | `"M"` |
| `PostingDate` | `Edm.Date` | No | `"2026-10-08"` |
| `YieldQuantity` | `Edm.Decimal` (13,3) | No | `"290.000"` |
| `ScrapQuantity` | `Edm.Decimal` (13,3) | No | `"8.700"` |
| `TargetQuantity` | `Edm.Decimal` (13,3) | No | `"291.667"` |
| `QuantityUnit` | `Edm.String` (3) | No | `"KG"` |
| `ScrapReason` | `Edm.String` (20) | Yes | `"MACHINE_SETTING"` |
| `RunHours` | `Edm.Decimal` (5,2) | No | `"8.00"` |
| `YieldValue` | `Edm.Decimal` (15,2) | No | `"217500.00"` |
| `ScrapValue` | `Edm.Decimal` (15,2) | No | `"6525.00"` |
| `TargetValue` | `Edm.Decimal` (15,2) | No | `"218750.25"` |
| `Currency` | `Edm.String` (5) | No | `"INR"` |
| `CompanyCode` | `Edm.String` (4) | No | `"INA1"` |

`YieldQuantity` is the good output confirmed, `ScrapQuantity` what was scrapped, `TargetQuantity` the
planned output of the shift (the order's planned quantity spread over its shifts), `RunHours` the
scheduled hours of the shift. `ScrapReason` is empty when nothing was scrapped.

### WorkCenterDowntime (key: `DowntimeNumber`)

One row per stoppage of a work center.

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `DowntimeNumber` | `Edm.String` (10) | No | `"0000045012"` |
| `ProductionOrder` | `Edm.String` (10) | Yes | `"0001000417"` |
| `Plant` | `Edm.String` (4) | No | `"1000"` |
| `WorkCenter` | `Edm.String` (8) | No | `"LINE1"` |
| `WorkCenterName` | `Edm.String` (40) | Yes | `"Line 1"` |
| `PostingDate` | `Edm.Date` | No | `"2026-10-20"` |
| `DowntimeHours` | `Edm.Decimal` (7,2) | No | `"112.00"` |
| `DowntimeCause` | `Edm.String` (20) | No | `"BREAKDOWN"` |
| `CompanyCode` | `Edm.String` (4) | No | `"INA1"` |

### Summaries (read-only)

Aggregated by SAP so a consumer never pages through confirmations to total them. A summary has one
row per key; values are in `Currency` (rupees).

| Entity | Key | Fields besides the key | Built from |
|--------|-----|------------------------|------------|
| `ProductionSummaryByDay` | `PostingDate`, `Currency`, `CompanyCode` | `PlannedHours`, `DowntimeHours`, `TargetValue`, `GoodValue`, `ScrapValue`, `ConfirmationCount` | `ProductionConfirmation` and `WorkCenterDowntime` |
| `DowntimeSummaryByDay` | `PostingDate`, `DowntimeCause`, `CompanyCode` | `DowntimeHours`, `EventCount` | `WorkCenterDowntime` |
| `ScrapSummaryByDay` | `PostingDate`, `ScrapReason`, `Currency`, `CompanyCode` | `ScrapValue`, `ConfirmationCount` | `ProductionConfirmation` |
| `OutputSummaryByLineShift` | `PostingDate`, `WorkCenter`, `Shift`, `Currency`, `CompanyCode` | `WorkCenterName`, `GoodValue` | `ProductionConfirmation` |

Types: `PlannedHours` is the sum of `RunHours`, `DowntimeHours` the sum of the downtime hours of the
same day and company (both `Edm.Decimal` (9,2)); `TargetValue`, `GoodValue` (sum of `YieldValue`) and
`ScrapValue` are `Edm.Decimal` (15,2); `ConfirmationCount` and `EventCount` are `Edm.Int32`.
`ScrapSummaryByDay` has no row for confirmations without scrap. A consumer works out effectiveness
from `ProductionSummaryByDay`: availability is `1 - DowntimeHours / PlannedHours`, performance is
`(GoodValue + ScrapValue) / TargetValue`, quality is `GoodValue / (GoodValue + ScrapValue)`.

## 3. Codes

| Field | Value | Meaning |
|-------|-------|---------|
| `Shift` | `M` | Morning |
| | `A` | Afternoon |
| | `N` | Night |
| `ScrapReason` | `MATERIAL_DEFECT` | The material was defective |
| | `MACHINE_SETTING` | The machine was set up wrongly |
| | `OPERATOR_ERROR` | An operator error |
| | `OTHER` | Anything else |
| `DowntimeCause` | `BREAKDOWN` | A machine stopped |
| | `CHANGEOVER` | Changing the line to another product |
| | `NO_MATERIAL` | A component was not available |
| | `MAINTENANCE` | Planned maintenance |
| | `OTHER` | Anything else |

Filter and compare codes as written.

## 4. How the entities connect

| From | To | Join |
|------|----|------|
| `ProductionConfirmation.ProductionOrder` | `ProductionOrder.ProductionOrder` | order and its confirmations (`drivers-contract.md`) |
| the sum of `YieldQuantity` of an order | `ProductionOrder.ConfirmedQuantity` | equal for a completed order |
| `WorkCenterDowntime.ProductionOrder` | `ProductionOrder.DelayReason` | a delay reason (`MACHINE_BREAKDOWN`, `MATERIAL_SHORTAGE`) has a downtime of that cause |
| `ProductionConfirmation.Material` | `StockMovement` (131) | a finished product receipt for the confirmed output (`inventory-contract.md`) |

## 5. Reads

All examples use the root path from section 1. `{root}` stands for it. The responses are real and are
checked by a test against the data of 2026-10-31.

### Confirmations of a production order

```
GET {root}ProductionConfirmation?$filter=ProductionOrder eq '0001000417'&$orderby=PostingDate,ConfirmationNumber&$top=2
```

```json
{
  "@odata.context": "$metadata#ProductionConfirmation",
  "value": [
    {
      "ConfirmationNumber": "8000002347",
      "ConfirmationCounter": "00000001",
      "ProductionOrder": "0001000417",
      "Material": "RM-1002",
      "MaterialDescription": "Piperine extract 95%",
      "Plant": "1000",
      "WorkCenter": "LINE2",
      "WorkCenterName": "Line 2",
      "Shift": "A",
      "PostingDate": "2026-07-06",
      "YieldQuantity": "160.000",
      "ScrapQuantity": "0.000",
      "TargetQuantity": "160.000",
      "QuantityUnit": "KG",
      "ScrapReason": null,
      "RunHours": "8.00",
      "YieldValue": "240000.00",
      "ScrapValue": "0.00",
      "TargetValue": "240000.00",
      "Currency": "INR",
      "CompanyCode": "INA1"
    },
    {
      "ConfirmationNumber": "8000002365",
      "ConfirmationCounter": "00000001",
      "ProductionOrder": "0001000417",
      "Material": "RM-1002",
      "MaterialDescription": "Piperine extract 95%",
      "Plant": "1000",
      "WorkCenter": "LINE2",
      "WorkCenterName": "Line 2",
      "Shift": "N",
      "PostingDate": "2026-07-07",
      "YieldQuantity": "172.800",
      "ScrapQuantity": "5.184",
      "TargetQuantity": "160.000",
      "QuantityUnit": "KG",
      "ScrapReason": "OPERATOR_ERROR",
      "RunHours": "8.00",
      "YieldValue": "259200.00",
      "ScrapValue": "7776.00",
      "TargetValue": "240000.00",
      "Currency": "INR",
      "CompanyCode": "INA1"
    }
  ]
}
```

### Stoppages of one cause

```
GET {root}WorkCenterDowntime?$filter=DowntimeCause eq 'BREAKDOWN'&$orderby=PostingDate,DowntimeNumber
```

```json
{
  "@odata.context": "$metadata#WorkCenterDowntime",
  "value": [
    {
      "DowntimeNumber": "0000045262",
      "ProductionOrder": "0001000408",
      "Plant": "1000",
      "WorkCenter": "LINE2",
      "WorkCenterName": "Line 2",
      "PostingDate": "2026-05-20",
      "DowntimeHours": "48.00",
      "DowntimeCause": "BREAKDOWN",
      "CompanyCode": "INA1"
    }
  ]
}
```

### Production per day

```
GET {root}ProductionSummaryByDay?$filter=CompanyCode eq 'INA1' and PostingDate ge 2026-10-14&$orderby=PostingDate,Currency,CompanyCode&$top=2
```

```json
{
  "@odata.context": "$metadata#ProductionSummaryByDay",
  "value": [
    {
      "PostingDate": "2026-10-14",
      "PlannedHours": "48.00",
      "DowntimeHours": "0.00",
      "TargetValue": "777189.08",
      "GoodValue": "814055.90",
      "ScrapValue": "16411.91",
      "ConfirmationCount": 6,
      "Currency": "INR",
      "CompanyCode": "INA1"
    },
    {
      "PostingDate": "2026-10-15",
      "PlannedHours": "48.00",
      "DowntimeHours": "0.00",
      "TargetValue": "777189.08",
      "GoodValue": "743603.82",
      "ScrapValue": "15167.32",
      "ConfirmationCount": 6,
      "Currency": "INR",
      "CompanyCode": "INA1"
    }
  ]
}
```

### Downtime by cause

```
GET {root}DowntimeSummaryByDay?$filter=PostingDate eq 2026-10-10 and CompanyCode eq 'INA1'&$orderby=PostingDate,DowntimeCause,CompanyCode
```

```json
{
  "@odata.context": "$metadata#DowntimeSummaryByDay",
  "value": [
    {
      "PostingDate": "2026-10-10",
      "DowntimeCause": "MAINTENANCE",
      "DowntimeHours": "18.00",
      "EventCount": 3,
      "CompanyCode": "INA1"
    }
  ]
}
```

### Scrap by reason

```
GET {root}ScrapSummaryByDay?$filter=PostingDate eq 2026-10-14 and CompanyCode eq 'INA1'&$orderby=PostingDate,ScrapReason,Currency,CompanyCode
```

```json
{
  "@odata.context": "$metadata#ScrapSummaryByDay",
  "value": [
    {
      "PostingDate": "2026-10-14",
      "ScrapReason": "MACHINE_SETTING",
      "ScrapValue": "7364.39",
      "ConfirmationCount": 2,
      "Currency": "INR",
      "CompanyCode": "INA1"
    },
    {
      "PostingDate": "2026-10-14",
      "ScrapReason": "MATERIAL_DEFECT",
      "ScrapValue": "1434.80",
      "ConfirmationCount": 1,
      "Currency": "INR",
      "CompanyCode": "INA1"
    },
    {
      "PostingDate": "2026-10-14",
      "ScrapReason": "OPERATOR_ERROR",
      "ScrapValue": "5997.90",
      "ConfirmationCount": 2,
      "Currency": "INR",
      "CompanyCode": "INA1"
    },
    {
      "PostingDate": "2026-10-14",
      "ScrapReason": "OTHER",
      "ScrapValue": "1614.82",
      "ConfirmationCount": 1,
      "Currency": "INR",
      "CompanyCode": "INA1"
    }
  ]
}
```

### Output by line and shift

```
GET {root}OutputSummaryByLineShift?$filter=PostingDate eq 2026-10-14 and CompanyCode eq 'INA1'&$orderby=PostingDate,WorkCenter,Shift,Currency,CompanyCode
```

```json
{
  "@odata.context": "$metadata#OutputSummaryByLineShift",
  "value": [
    {
      "PostingDate": "2026-10-14",
      "WorkCenter": "LINE1",
      "Shift": "A",
      "WorkCenterName": "Line 1",
      "GoodValue": "246468.69",
      "Currency": "INR",
      "CompanyCode": "INA1"
    },
    {
      "PostingDate": "2026-10-14",
      "WorkCenter": "LINE2",
      "Shift": "N",
      "WorkCenterName": "Line 2",
      "GoodValue": "502420.31",
      "Currency": "INR",
      "CompanyCode": "INA1"
    },
    {
      "PostingDate": "2026-10-14",
      "WorkCenter": "LINE3",
      "Shift": "M",
      "WorkCenterName": "Line 3",
      "GoodValue": "65166.90",
      "Currency": "INR",
      "CompanyCode": "INA1"
    }
  ]
}
```

## 6. Notes for the SAP consultant

These are the usual SAP sources; confirm them and expose each entity as a read-only CDS view entity
with a projection, in the same service binding.

| Entity | Usual source |
|--------|--------------|
| `ProductionConfirmation` | order confirmations (`AFRU`) with the order (`AUFK`, `AFKO`), the work center (`CRHD`, `CRTX`) and the variance reason for scrap |
| `WorkCenterDowntime` | work center downtime from maintenance notifications and breakdown confirmations (`QMEL`, `AFRU` with a downtime reason), or the shop floor system if downtime is kept there |
| `ProductionSummaryBy*`, `DowntimeSummaryByDay`, `ScrapSummaryByDay`, `OutputSummaryByLineShift` | aggregate CDS views over the two views above, so SAP does the totalling |

The data is read with the shared management login, so the app limits who can ask for it (role
`management` or `admin`). Large tables must be selective on the filter fields used above:
`PostingDate`, `WorkCenter`, `ProductionOrder`, `DowntimeCause`.
