# Drivers OData V4 contract

Source of truth for butterfly (mock SAP), the synapse gateways and the SAP consultant for the
data behind "why" questions: customer contracts, supplier deliveries and production. See
`docs/ai-analysis.md` for why these are needed. If this file and any other document disagree,
this file wins. Everything here is read-only.

Types, `$filter` literals, `$select`, `$orderby`, `$top`, `$skip`, `$count` and the error format
are exactly as in `sales-contract.md` (sections 3, 4 and 7). `$expand` is not supported.

## 1. Service

| Item | Value |
|------|-------|
| Service definition / binding | `ZUI_DRIVERS_O4` (OData V4, UI-less web API) |
| Root path | `/sap/opu/odata4/sap/zui_drivers_o4/srvd_a2x/sap/zdrivers/0001/` |
| Format | JSON only (`Accept: application/json`) |

All paths below are relative to the root. Reads are `GET {root}<Entity>` with query options;
reading one row by key is not supported.

## 2. Entities

Nullable `No` means the field is always present in responses.

### SalesContract (key: `SalesContract`)

One row per contract. A renewal is a new row whose `PredecessorContract` is the contract it
replaces.

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `SalesContract` | `Edm.String` (10) | No | `"0040000127"` |
| `PredecessorContract` | `Edm.String` (10) | Yes | `"0040000071"` |
| `SoldToParty` | `Edm.String` (10) | No | `"0000100001"` |
| `CustomerName` | `Edm.String` (80) | Yes | `"Acme Industries"` |
| `ValidFrom` | `Edm.Date` | No | `"2025-07-13"` |
| `ValidTo` | `Edm.Date` | No | `"2026-07-12"` |
| `ContractValue` | `Edm.Decimal` (15,2) | No | `"9000000.00"` |
| `TransactionCurrency` | `Edm.String` (5) | No | `"INR"` |
| `ContractStatus` | `Edm.String` (1) | No | `"E"` |

### PurchaseDelivery (key: `PurchaseOrder`, `PurchaseOrderItem`)

One row per purchase order item with its delivery dates. `NetAmount` is the ordered quantity times the net price of the item. `ActualDeliveryDate` is the date of
the first goods receipt that completed the item; it is empty while the item is open.

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `PurchaseOrder` | `Edm.String` (10) | No | `"4500001207"` |
| `PurchaseOrderItem` | `Edm.String` (5) | No | `"00010"` |
| `Supplier` | `Edm.String` (10) | No | `"0000200001"` |
| `SupplierName` | `Edm.String` (80) | Yes | `"Doosan Metals Pvt Ltd"` |
| `Material` | `Edm.String` (40) | No | `"RAW-2002"` |
| `MaterialDescription` | `Edm.String` (40) | Yes | `"Steel coil"` |
| `OrderDate` | `Edm.Date` | No | `"2026-06-24"` |
| `OrderedQuantity` | `Edm.Decimal` (13,3) | No | `"5000.000"` |
| `DeliveredQuantity` | `Edm.Decimal` (13,3) | No | `"5000.000"` |
| `QuantityUnit` | `Edm.String` (3) | No | `"KG"` |
| `NetAmount` | `Edm.Decimal` (15,2) | No | `"260000.00"` |
| `TransactionCurrency` | `Edm.String` (5) | No | `"INR"` |
| `PromisedDeliveryDate` | `Edm.Date` | No | `"2026-07-14"` |
| `ActualDeliveryDate` | `Edm.Date` | Yes | `"2026-07-26"` |
| `DeliveryStatus` | `Edm.String` (1) | No | `"D"` |

### ProductionOrder (key: `ProductionOrder`)

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `ProductionOrder` | `Edm.String` (10) | No | `"0001000417"` |
| `Material` | `Edm.String` (40) | No | `"RM-1002"` |
| `MaterialDescription` | `Edm.String` (40) | Yes | `"Steel plate 5mm"` |
| `PlannedQuantity` | `Edm.Decimal` (13,3) | No | `"4000.000"` |
| `ConfirmedQuantity` | `Edm.Decimal` (13,3) | No | `"4000.000"` |
| `QuantityUnit` | `Edm.String` (3) | No | `"KG"` |
| `PlannedStartDate` | `Edm.Date` | No | `"2026-07-06"` |
| `PlannedEndDate` | `Edm.Date` | No | `"2026-07-20"` |
| `ActualEndDate` | `Edm.Date` | Yes | `"2026-08-03"` |
| `ProductionStatus` | `Edm.String` (1) | No | `"C"` |
| `DelayReason` | `Edm.String` (20) | Yes | `"MATERIAL_SHORTAGE"` |

`ActualEndDate` is empty while the order is running. `DelayReason` is the reason the planner
confirmed when the order finished late; it is empty for an order that finished on time.

### ProductionOrderComponent (key: `ProductionOrder`, `Material`)

The materials an order consumes.

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `ProductionOrder` | `Edm.String` (10) | No | `"0001000417"` |
| `Material` | `Edm.String` (40) | No | `"RAW-2002"` |
| `MaterialDescription` | `Edm.String` (40) | Yes | `"Steel coil"` |
| `RequiredQuantity` | `Edm.Decimal` (13,3) | No | `"4400.000"` |
| `QuantityUnit` | `Edm.String` (3) | No | `"KG"` |

## 3. Codes

| Field | Value | Meaning |
|-------|-------|---------|
| `ContractStatus` | `A` | Active (valid today) |
| | `E` | Expired (`ValidTo` has passed) |
| | `C` | Cancelled before its end |
| `DeliveryStatus` | `O` | Open (not fully received) |
| | `D` | Delivered |
| | `X` | Cancelled (left out of the purchase summaries) |
| `ProductionStatus` | `R` | Released, running |
| | `C` | Completed |
| `DelayReason` | `MATERIAL_SHORTAGE` | A component was not available |
| | `MACHINE_BREAKDOWN` | A machine stopped |
| | `MANPOWER` | Not enough staff or shifts |
| | `OTHER` | Anything else |

Filter and compare codes as written. A late delivery is a row where `ActualDeliveryDate` is
after `PromisedDeliveryDate`, or `ActualDeliveryDate` is empty and `PromisedDeliveryDate` is
before today; the consumer does the arithmetic, SAP does not return a delay field.

## 4. How the entities connect

| From | To | Join |
|------|----|------|
| `SalesContract.SoldToParty` | `SalesOrder.SoldToParty` | same customer (`sales-contract.md`) |
| `ProductionOrder.Material` | `SalesOrderItem.Material` | the product that is sold |
| `ProductionOrderComponent.ProductionOrder` | `ProductionOrder.ProductionOrder` | order and its components |
| `ProductionOrderComponent.Material` | `PurchaseDelivery.Material` | component and the purchase of it |

## 5. Reads

All examples use the root path from section 1. `{root}` stands for it.

### Contracts of one customer

```
GET {root}SalesContract?$filter=SoldToParty eq '0000100001' and ValidTo ge 2026-01-01&$orderby=ValidFrom
```

```json
{
  "@odata.context": "$metadata#SalesContract",
  "value": [
    {
      "SalesContract": "0040000127",
      "PredecessorContract": "0040000071",
      "SoldToParty": "0000100001",
      "CustomerName": "Acme Industries",
      "ValidFrom": "2025-07-13",
      "ValidTo": "2026-07-12",
      "ContractValue": "9000000.00",
      "TransactionCurrency": "INR",
      "ContractStatus": "E"
    },
    {
      "SalesContract": "0040000163",
      "PredecessorContract": "0040000127",
      "SoldToParty": "0000100001",
      "CustomerName": "Acme Industries",
      "ValidFrom": "2026-09-14",
      "ValidTo": "2027-09-13",
      "ContractValue": "10000000.00",
      "TransactionCurrency": "INR",
      "ContractStatus": "A"
    }
  ]
}
```

### Deliveries of a material in a period

```
GET {root}PurchaseDelivery?$filter=Material eq 'RAW-2002' and PromisedDeliveryDate ge 2026-07-01 and PromisedDeliveryDate le 2026-07-31&$orderby=PromisedDeliveryDate
```

```json
{
  "@odata.context": "$metadata#PurchaseDelivery",
  "value": [
    {
      "PurchaseOrder": "4500001207",
      "PurchaseOrderItem": "00010",
      "Supplier": "0000200001",
      "SupplierName": "Doosan Metals Pvt Ltd",
      "Material": "RAW-2002",
      "MaterialDescription": "Steel coil",
      "OrderDate": "2026-06-24",
      "OrderedQuantity": "5000.000",
      "DeliveredQuantity": "5000.000",
      "QuantityUnit": "KG",
      "NetAmount": "260000.00",
      "TransactionCurrency": "INR",
      "PromisedDeliveryDate": "2026-07-14",
      "ActualDeliveryDate": "2026-07-26",
      "DeliveryStatus": "D"
    }
  ]
}
```

### Production orders of one product

```
GET {root}ProductionOrder?$filter=Material eq 'RM-1002' and PlannedEndDate ge 2026-07-01&$orderby=PlannedEndDate&$top=2
```

```json
{
  "@odata.context": "$metadata#ProductionOrder",
  "value": [
    {
      "ProductionOrder": "0001000417",
      "Material": "RM-1002",
      "MaterialDescription": "Steel plate 5mm",
      "PlannedQuantity": "4000.000",
      "ConfirmedQuantity": "4000.000",
      "QuantityUnit": "KG",
      "PlannedStartDate": "2026-07-06",
      "PlannedEndDate": "2026-07-20",
      "ActualEndDate": "2026-08-03",
      "ProductionStatus": "C",
      "DelayReason": "MATERIAL_SHORTAGE"
    },
    {
      "ProductionOrder": "0001000423",
      "Material": "RM-1002",
      "MaterialDescription": "Steel plate 5mm",
      "PlannedQuantity": "4000.000",
      "ConfirmedQuantity": "4000.000",
      "QuantityUnit": "KG",
      "PlannedStartDate": "2026-08-06",
      "PlannedEndDate": "2026-08-20",
      "ActualEndDate": "2026-08-20",
      "ProductionStatus": "C",
      "DelayReason": null
    }
  ]
}
```

### Components of a production order

```
GET {root}ProductionOrderComponent?$filter=ProductionOrder eq '0001000417'
```

```json
{
  "@odata.context": "$metadata#ProductionOrderComponent",
  "value": [
    {
      "ProductionOrder": "0001000417",
      "Material": "RAW-2002",
      "MaterialDescription": "Steel coil",
      "RequiredQuantity": "4400.000",
      "QuantityUnit": "KG"
    }
  ]
}
```

## 6. Notes for the SAP consultant

These are the usual SAP sources; confirm them and expose each entity as a read-only CDS view
entity with a projection, in the same service binding.

| Entity | Usual source |
|--------|--------------|
| `SalesContract` | SD outline agreements: contract header and item (`VBAK`, `VBAP`) with contract data (`VEDA`, validity dates) |
| `PurchaseDelivery` | purchase order item and schedule line (`EKPO`, `EKET`) with goods receipt history (`EKBE`) |
| `ProductionOrder` | production order header and item (`AFKO`, `AFPO`) with confirmations for the actual end and the variance reason |
| `ProductionOrderComponent` | order reservations (`RESB`) |

The data is read with the shared management login, so the app limits who can ask for it (role
`management` or `admin`). Large tables must be selective on the filter fields used above:
`SoldToParty`, `ValidFrom`/`ValidTo`, `Material`, `PromisedDeliveryDate`, `PlannedEndDate`.
