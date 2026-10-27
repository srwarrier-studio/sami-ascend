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

Cancelled orders (`OverallStatus` `X`) are not counted in any summary. A summary is read with
`GET {root}<Entity>` and `$filter`; reading one row by key is not supported.

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
| `$expand` | `_Item` on `SalesOrder` only; a single order accepts `$expand` and no other option |

`$filter` literals: strings in single quotes (`'O''Brien'`, a doubled quote is one quote),
dates as `2026-10-27`, timestamps as `2026-10-27T09:15:30Z`, decimals as `125000.50` with no
quotes. A literal must match the field type. `contains()` and `startswith()` work on string
fields and are case-sensitive. A field with no value (null) matches no comparison or function.
Operators and function names are lower case.

`$select` returns the chosen fields in the order of the field tables in section 2, whatever
order the request lists them. `$orderby` puts empty values first when ascending and last when
descending; rows with equal values keep their original order. `$top`, `$skip` and `$count`
accept only `0` or a positive whole number, and `true` or `false`.

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

## 6. Writes

Writes are `POST` to create and `PATCH` to change header fields. There is no delete. Send
`Content-Type: application/json`.

### Create (deep insert)

```
POST {root}SalesOrder
```

```json
{
  "SalesOrderType": "OR",
  "SoldToParty": "0000100001",
  "RequestedDeliveryDate": "2026-11-05",
  "TransactionCurrency": "INR",
  "_Item": [
    { "Material": "RM-1001", "Quantity": "50.000", "QuantityUnit": "KG" },
    { "Material": "RM-1002", "Quantity": "25.000", "QuantityUnit": "KG" }
  ]
}
```

Input rules:

| Field | Rule |
|-------|------|
| `SalesOrderType`, `SoldToParty`, `TransactionCurrency` | Required |
| `RequestedDeliveryDate` | Optional; must not be before today |
| `_Item` | Required, at least one item |
| `Material`, `Quantity`, `QuantityUnit` | Required on each item; `Quantity` greater than 0 |

SAP fills in everything else: `SalesOrder`, `SalesOrderItem` (`000010`, `000020`, ...),
`CustomerName`, `MaterialDescription`, `OrderDate` (today), `NetAmount`, `TotalNetAmount`,
`OverallStatus` (`A`), `CreatedByUser`, and both timestamps. Prices come from SAP pricing.

Sending a field SAP fills in, or a name that is not a field, is rejected with
`FIELD_NOT_ALLOWED`. Nothing is created when any problem is found, and all problems are
returned together.

Response: `201 Created` with the full order and its items, as in the `$expand=_Item` example
in section 5, plus a `Location` header with the new order URL.

### Change header fields

```
PATCH {root}SalesOrder('0000012345')
If-Match: W/"20261027091530"
```

```json
{ "RequestedDeliveryDate": "2026-11-12" }
```

Only `RequestedDeliveryDate` can be changed. A cancelled or completed order (`X`, `C`) cannot
be changed. `If-Match` is required and takes the `@odata.etag` from the last read.

Any other field in the body is `FIELD_NOT_ALLOWED`; a missing or null date is `FIELD_REQUIRED`;
a date before today is `DELIVERY_DATE_IN_PAST`; a cancelled or completed order is
`ORDER_NOT_CHANGEABLE` with `target` `SalesOrder`. These are returned as `400` in the same shape
as the create validation error. An unknown order is `404`.

Response: `200 OK` with the full updated order (no items) and a new `@odata.etag`.
`LastChangeDateTime` moves forward on every change, by at least one second, so the etag
always changes and a stale `If-Match` is always caught.

### 400 Validation error

Returned for a failed input rule. `details` has one entry per failed field, so the web form
can show every message at once. `target` is the field path.

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The sales order has errors.",
    "details": [
      {
        "code": "CUSTOMER_UNKNOWN",
        "message": "Customer 0000999999 does not exist.",
        "target": "SoldToParty"
      },
      {
        "code": "QUANTITY_NOT_POSITIVE",
        "message": "Quantity must be greater than 0.",
        "target": "_Item/1/Quantity"
      }
    ]
  }
}
```

In `_Item/1/Quantity`, `1` is the zero-based position in the request.

Detail codes: `FIELD_REQUIRED`, `FIELD_INVALID`, `FIELD_NOT_ALLOWED`, `CUSTOMER_UNKNOWN`,
`MATERIAL_UNKNOWN`, `UNIT_INVALID`, `CURRENCY_INVALID`, `QUANTITY_NOT_POSITIVE`,
`DELIVERY_DATE_IN_PAST`, `ORDER_NOT_CHANGEABLE`, `NO_ITEMS`.

| Code | Meaning | `target` |
|------|---------|----------|
| `FIELD_REQUIRED` | A required field is missing, null or empty | the field |
| `FIELD_INVALID` | The value has the wrong format (date not `YYYY-MM-DD`, quantity not a decimal string, a number where text is required) | the field |
| `FIELD_NOT_ALLOWED` | A field SAP fills in, or an unknown name | the field |
| `UNIT_INVALID` | The unit is not the material's unit | `_Item/n/QuantityUnit` |
| `NO_ITEMS` | `_Item` is missing or empty | `_Item` |

Format and field problems use the same shape, one entry each. Entries are ordered: fields that
are not allowed first, then the header fields in the order of the field table, then the items
in request order.


```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The sales order has errors.",
    "details": [
      {
        "code": "FIELD_NOT_ALLOWED",
        "message": "OverallStatus is set by SAP and cannot be sent.",
        "target": "OverallStatus"
      },
      {
        "code": "FIELD_INVALID",
        "message": "RequestedDeliveryDate must be a date like 2026-11-05.",
        "target": "RequestedDeliveryDate"
      }
    ]
  }
}
```

### 412 ETag mismatch

The order changed since it was read. The caller re-reads and retries.

```json
{
  "error": {
    "code": "ETAG_MISMATCH",
    "message": "The sales order was changed by someone else. Reload and try again.",
    "target": "SalesOrder"
  }
}
```

A `PATCH` without `If-Match` returns `428` with code `ETAG_REQUIRED`, same shape.

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

### 400 Bad request (invalid query)

A malformed `$filter`, an unknown field in `$filter`, `$select` or `$orderby`, a literal that
does not match the field type, or a bad value for `$top`, `$skip`, `$count` or `$expand` (only `_Item` can be expanded). `target` is the option.

```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "Unknown field Colour in $filter.",
    "target": "$filter"
  }
}
```

### 400 Bad request (invalid body)

The body is not valid JSON, or is JSON but not an object.

```json
{
  "error": {
    "code": "INVALID_REQUEST_BODY",
    "message": "The request body must be a JSON object.",
    "target": "body"
  }
}
```

### 404 Unknown resource, 405 Method not allowed

A path that is not in this service is `404 RESOURCE_NOT_FOUND`. A method the resource does not
support, such as `DELETE` (there is no delete) or `PUT`, is `405 METHOD_NOT_ALLOWED`. Neither
has a `target`.

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource does not exist."
  }
}
```

```json
{
  "error": {
    "code": "METHOD_NOT_ALLOWED",
    "message": "This method is not supported for this resource."
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

## 8. Identity

Every request carries one SAP login. Whether it is the end user or a technical user is not
decided here; see roadmap `shared/04`. `CreatedByUser` records whichever SAP user posted.
Who in the app actually asked is recorded in the app's `audit_log`, not in SAP.

## 9. Open questions

Kept in [consultant-questions.md](consultant-questions.md), under Sales contract.
