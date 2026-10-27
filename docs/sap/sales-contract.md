# Sales OData V4 contract

Source of truth for butterfly (mock SAP), the workspace and synapse gateways, and the SAP
consultant guide. If this file and any other document disagree, this file wins.

## 1. Service

| Item | Value |
|------|-------|
| Service definition / binding | `ZUI_SALES_O4` (OData V4, UI-less web API) |
| Root path | `/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/` |
| Format | JSON only (`Accept: application/json`) |
| Metadata | `{root}$metadata` |

All paths below are relative to the root. Butterfly serves the same paths.

## 2. Entities

Nullable `No` means the field is always present in responses.

### SalesOrder (key: `SalesOrder`)

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `SalesOrder` | `Edm.String` (10) | No | `"0000012345"` |
| `SalesOrderType` | `Edm.String` (4) | No | `"OR"` |
| `SoldToParty` | `Edm.String` (10) | No | `"0000100001"` |
| `CustomerName` | `Edm.String` (80) | Yes | `"Acme Industries"` |
| `OrderDate` | `Edm.Date` | No | `"2026-10-27"` |
| `RequestedDeliveryDate` | `Edm.Date` | Yes | `"2026-11-05"` |
| `TransactionCurrency` | `Edm.String` (5) | No | `"INR"` |
| `TotalNetAmount` | `Edm.Decimal` (15,2) | No | `"125000.00"` |
| `OverallStatus` | `Edm.String` (1) | No | `"A"` |
| `CreatedByUser` | `Edm.String` (12) | No | `"SMANI"` |
| `CreationDateTime` | `Edm.DateTimeOffset` | No | `"2026-10-27T09:15:30Z"` |
| `LastChangeDateTime` | `Edm.DateTimeOffset` | No | `"2026-10-27T09:15:30Z"` |

Navigation: `_Item` (collection of `SalesOrderItem`).

### SalesOrderItem (key: `SalesOrder`, `SalesOrderItem`)

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `SalesOrder` | `Edm.String` (10) | No | `"0000012345"` |
| `SalesOrderItem` | `Edm.String` (6) | No | `"000010"` |
| `Material` | `Edm.String` (40) | No | `"RM-1001"` |
| `MaterialDescription` | `Edm.String` (40) | Yes | `"Steel rod 12mm"` |
| `Quantity` | `Edm.Decimal` (13,3) | No | `"50.000"` |
| `QuantityUnit` | `Edm.String` (3) | No | `"KG"` |
| `NetAmount` | `Edm.Decimal` (15,2) | No | `"62500.00"` |

Navigation: none. Items are read through `SalesOrder(...)/_Item` or `$expand=_Item`.

### Summary entities (read-only)

Used for dashboard totals. No create, change or delete.

**SalesSummaryByDay** (key: `OrderDate`)

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `OrderDate` | `Edm.Date` | No | `"2026-10-27"` |
| `TotalNetAmount` | `Edm.Decimal` (15,2) | No | `"845000.00"` |
| `OrderCount` | `Edm.Int32` | No | `14` |
| `Currency` | `Edm.String` (5) | No | `"INR"` |

**SalesSummaryByCustomer** (key: `SoldToParty`, `OrderDate`)

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `SoldToParty` | `Edm.String` (10) | No | `"0000100001"` |
| `CustomerName` | `Edm.String` (80) | Yes | `"Acme Industries"` |
| `OrderDate` | `Edm.Date` | No | `"2026-10-27"` |
| `TotalNetAmount` | `Edm.Decimal` (15,2) | No | `"125000.00"` |
| `OrderCount` | `Edm.Int32` | No | `2` |
| `Currency` | `Edm.String` (5) | No | `"INR"` |

**SalesSummaryByMaterial** (key: `Material`, `OrderDate`)

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `Material` | `Edm.String` (40) | No | `"RM-1001"` |
| `MaterialDescription` | `Edm.String` (40) | Yes | `"Steel rod 12mm"` |
| `OrderDate` | `Edm.Date` | No | `"2026-10-27"` |
| `TotalQuantity` | `Edm.Decimal` (13,3) | No | `"500.000"` |
| `QuantityUnit` | `Edm.String` (3) | No | `"KG"` |
| `TotalNetAmount` | `Edm.Decimal` (15,2) | No | `"625000.00"` |
| `Currency` | `Edm.String` (5) | No | `"INR"` |

Summaries are per day. Month-to-date and year-to-date are sums over a `$filter` on
`OrderDate`, done by synapse-api. Each summary has one row per currency per key; synapse-api
does not add amounts across currencies.

## 3. Types

| Type | Wire format | Rule |
|------|-------------|------|
| `Edm.Date` | `"2026-10-27"` | ISO 8601 date, no time zone |
| `Edm.DateTimeOffset` | `"2026-10-27T09:15:30Z"` | UTC, always with `Z`, whole seconds |
| `Edm.Decimal` | `"125000.00"` | JSON string (`IEEE754Compatible=true`), dot as separator, scale as in the tables, no thousands separator |
| `Edm.Int32` | `14` | JSON number |
| `Edm.String` | `"text"` | Document numbers keep their leading zeros |

`OverallStatus` values:

| Value | Meaning |
|-------|---------|
| `A` | Open (not yet processed) |
| `B` | In process |
| `C` | Completed |
| `X` | Cancelled |

Filter and compare status as the one-letter code. Display names are the web app's job.

## 4. Query options

Supported on `SalesOrder`, `SalesOrderItem` and the summary entities:

| Option | Support |
|--------|---------|
| `$filter` | `eq ne gt ge lt le`, `and`, `or`, `not`, `contains()`, `startswith()` |
| `$select` | Comma-separated field names |
| `$orderby` | `field [asc\|desc]`, comma-separated |
| `$top` | Default 100, maximum 1000; larger values return `400` |
| `$skip` | Non-negative integer |
| `$count` | `$count=true` adds `@odata.count` to a collection response |
| `$expand` | `_Item` on `SalesOrder` only |

Not supported: `$apply`, `$search`, `$expand` on summaries, lambda operators (`any`, `all`).
Unsupported options return `400` in the error format (section 7).
