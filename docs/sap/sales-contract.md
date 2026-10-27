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

## 5. Reads

All examples use the root path from section 1. `{root}` stands for it.

### List with count

```
GET {root}SalesOrder?$filter=OrderDate eq 2026-10-27&$select=SalesOrder,CustomerName,TotalNetAmount&$orderby=CreationDateTime desc&$top=2&$count=true
```

```json
{
  "@odata.context": "$metadata#SalesOrder(SalesOrder,CustomerName,TotalNetAmount)",
  "@odata.count": 14,
  "value": [
    {
      "SalesOrder": "0000012345",
      "CustomerName": "Acme Industries",
      "TotalNetAmount": "125000.00"
    },
    {
      "SalesOrder": "0000012344",
      "CustomerName": "Bharat Steels",
      "TotalNetAmount": "98000.50"
    }
  ]
}
```

Without `$select`, every field in section 2 is returned. `@odata.count` is the number of rows
matching `$filter`, before `$top` and `$skip`. It appears only when `$count=true`.

### Single order by key

```
GET {root}SalesOrder('0000012345')
```

```json
{
  "@odata.context": "$metadata#SalesOrder/$entity",
  "@odata.etag": "W/\"20261027091530\"",
  "SalesOrder": "0000012345",
  "SalesOrderType": "OR",
  "SoldToParty": "0000100001",
  "CustomerName": "Acme Industries",
  "OrderDate": "2026-10-27",
  "RequestedDeliveryDate": "2026-11-05",
  "TransactionCurrency": "INR",
  "TotalNetAmount": "125000.00",
  "OverallStatus": "A",
  "CreatedByUser": "SMANI",
  "CreationDateTime": "2026-10-27T09:15:30Z",
  "LastChangeDateTime": "2026-10-27T09:15:30Z"
}
```

A single-entity response carries `@odata.etag`. Collection rows do not.

### Order with items

```
GET {root}SalesOrder('0000012345')?$expand=_Item
```

```json
{
  "@odata.context": "$metadata#SalesOrder(_Item())/$entity",
  "@odata.etag": "W/\"20261027091530\"",
  "SalesOrder": "0000012345",
  "SalesOrderType": "OR",
  "SoldToParty": "0000100001",
  "CustomerName": "Acme Industries",
  "OrderDate": "2026-10-27",
  "RequestedDeliveryDate": "2026-11-05",
  "TransactionCurrency": "INR",
  "TotalNetAmount": "125000.00",
  "OverallStatus": "A",
  "CreatedByUser": "SMANI",
  "CreationDateTime": "2026-10-27T09:15:30Z",
  "LastChangeDateTime": "2026-10-27T09:15:30Z",
  "_Item": [
    {
      "SalesOrder": "0000012345",
      "SalesOrderItem": "000010",
      "Material": "RM-1001",
      "MaterialDescription": "Steel rod 12mm",
      "Quantity": "50.000",
      "QuantityUnit": "KG",
      "NetAmount": "62500.00"
    },
    {
      "SalesOrder": "0000012345",
      "SalesOrderItem": "000020",
      "Material": "RM-1002",
      "MaterialDescription": "Steel plate 5mm",
      "Quantity": "25.000",
      "QuantityUnit": "KG",
      "NetAmount": "62500.00"
    }
  ]
}
```

### Items of one order

```
GET {root}SalesOrder('0000012345')/_Item?$orderby=SalesOrderItem
```

Returns `{"@odata.context": ..., "value": [ ...items as above... ]}`.

### Summary

```
GET {root}SalesSummaryByDay?$filter=OrderDate ge 2026-10-26 and OrderDate le 2026-10-27&$orderby=OrderDate
```

```json
{
  "@odata.context": "$metadata#SalesSummaryByDay",
  "value": [
    {
      "OrderDate": "2026-10-26",
      "TotalNetAmount": "712000.00",
      "OrderCount": 11,
      "Currency": "INR"
    },
    {
      "OrderDate": "2026-10-27",
      "TotalNetAmount": "845000.00",
      "OrderCount": 14,
      "Currency": "INR"
    }
  ]
}
```

### Paging

A collection response never carries `@odata.nextLink`. Callers page with `$top` and `$skip`
and stop when a page returns fewer rows than `$top`.

## 7. Error format

Every non-2xx response has this body and `Content-Type: application/json`:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "target": "string",
    "details": [
      { "code": "string", "message": "string", "target": "string" }
    ]
  }
}
```

| Field | Rule |
|-------|------|
| `code` | Stable machine code, upper snake case. Apps branch on this, never on `message` |
| `message` | Plain English for a person, safe to show |
| `target` | Field or resource the error is about; omitted when there is none |
| `details` | One entry per problem; omitted when there is only the top-level error |

### 400 Bad request (unsupported option)

```json
{
  "error": {
    "code": "UNSUPPORTED_QUERY_OPTION",
    "message": "Query option $apply is not supported.",
    "target": "$apply"
  }
}
```

### 403 Not authorized

```json
{
  "error": {
    "code": "NOT_AUTHORIZED",
    "message": "You are not authorized to read sales orders."
  }
}
```

### 404 Not found

```json
{
  "error": {
    "code": "SALES_ORDER_NOT_FOUND",
    "message": "Sales order 0000099999 does not exist.",
    "target": "SalesOrder"
  }
}
```

### 500 Server error

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred. Quote the request id when reporting it.",
    "target": "request-id-0f3c9a"
  }
}
```

For `500`, `target` holds the request id. The `400` validation and `412` ETag mismatch
examples are in section 6, next to the writes they belong to.
