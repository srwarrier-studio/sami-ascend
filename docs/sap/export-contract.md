# Export OData V4 contract

Source of truth for butterfly (mock SAP), the synapse gateways and the SAP consultant for export
shipments: what left for customers abroad, where, how, and whether it has arrived. If this file and
any other document disagree, this file wins. Everything here is read-only.

Types, `$filter` literals, `$select`, `$orderby`, `$top`, `$skip`, `$count` and the error format are
exactly as in `sales-contract.md` (sections 3, 4 and 7). `$expand` is not supported. A summary takes
the same query options as any other entity and needs the whole key in `$orderby` when paged.

## 1. Service

| Item | Value |
|------|-------|
| Service definition / binding | `ZUI_EXPORT_O4` (OData V4, UI-less web API) |
| Root path | `/sap/opu/odata4/sap/zui_export_o4/srvd_a2x/sap/zexport/0001/` |
| Format | JSON only (`Accept: application/json`) |

All paths below are relative to the root. Reads are `GET {root}<Entity>` with query options; reading
one row by key is not supported.

## 2. Entities

Nullable `No` means the field is always present in responses. An export is a sales order whose
ship-to country is not the country of the selling company (India, `IN`). One shipment is one outbound
delivery of one sales order.

### ExportShipment (key: `Shipment`)

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `Shipment` | `Edm.String` (10) | No | `"6000001234"` |
| `SalesOrder` | `Edm.String` (10) | No | `"0000012031"` |
| `SoldToParty` | `Edm.String` (10) | No | `"0000100001"` |
| `CustomerName` | `Edm.String` (80) | Yes | `"Harborline Nutrition LLC"` |
| `Country` | `Edm.String` (2) | No | `"US"` |
| `CountryName` | `Edm.String` (40) | Yes | `"United States"` |
| `TransportMode` | `Edm.String` (1) | No | `"S"` |
| `ShipmentDate` | `Edm.Date` | No | `"2026-10-08"` |
| `ExpectedArrivalDate` | `Edm.Date` | No | `"2026-11-02"` |
| `ActualArrivalDate` | `Edm.Date` | Yes | `"2026-11-03"` |
| `ShipmentStatus` | `Edm.String` (1) | No | `"D"` |
| `NetAmount` | `Edm.Decimal` (15,2) | No | `"2480000.00"` |
| `Currency` | `Edm.String` (5) | No | `"INR"` |
| `DocumentAmount` | `Edm.Decimal` (15,2) | No | `"31000.00"` |
| `DocumentCurrency` | `Edm.String` (5) | No | `"USD"` |
| `CompanyCode` | `Edm.String` (4) | No | `"INA1"` |

`ShipmentDate` is the goods issue date of the delivery. `NetAmount` is the net value in the company
code currency (`Currency`, rupees) so exports in different currencies can be added; `DocumentAmount`
is the same value in the currency of the order (`DocumentCurrency`). `ActualArrivalDate` is empty
while the shipment is in transit. Cancelled orders have no shipment.

### Summaries (read-only)

Aggregated by SAP so a consumer never pages through shipments to total them. Amounts are in the
company code currency (`Currency`).

| Entity | Key | Fields besides the key | Built from |
|--------|-----|------------------------|------------|
| `ExportSummaryByDay` | `ShipmentDate`, `Currency`, `CompanyCode` | `ShipmentCount`, `NetAmount` | `ExportShipment` |
| `ExportSummaryByDestination` | `ShipmentDate`, `Country`, `Currency`, `CompanyCode` | `CountryName`, `ShipmentCount`, `NetAmount` | `ExportShipment` |
| `ExportSummaryByMode` | `ShipmentDate`, `TransportMode`, `CompanyCode` | `ShipmentCount` | `ExportShipment` |

`NetAmount` is `Edm.Decimal` (15,2); `ShipmentCount` is `Edm.Int32`.

## 3. Codes

| Field | Value | Meaning |
|-------|-------|---------|
| `TransportMode` | `S` | Sea |
| | `A` | Air |
| | `R` | Road |
| `ShipmentStatus` | `T` | In transit (no arrival yet) |
| | `D` | Delivered |

Filter and compare codes as written. A shipment is late when `ActualArrivalDate` is after
`ExpectedArrivalDate`, or `ActualArrivalDate` is empty and `ExpectedArrivalDate` is before today; the
consumer does the arithmetic.

## 4. How the entities connect

| From | To | Join |
|------|----|------|
| `ExportShipment.SalesOrder` | `SalesOrder.SalesOrder` | the order shipped (`sales-contract.md`) |
| `ExportShipment.NetAmount` | `SalesOrder.TotalNetAmount` | the order total in rupees; for an order in rupees they are equal |
| `ExportShipment.SoldToParty` | `SalesOrder.SoldToParty` | same customer |
| `ExportShipment` | `StockMovement` (601) | the goods issue of the delivery (`inventory-contract.md`) |

## 5. Reads

All examples use the root path from section 1. `{root}` stands for it. The responses are real and are
checked by a test against the data of 2026-10-31.

## 6. Notes for the SAP consultant

These are the usual SAP sources; confirm them and expose each entity as a read-only CDS view entity
with a projection, in the same service binding.

| Entity | Usual source |
|--------|--------------|
| `ExportShipment` | outbound delivery (`LIKP`, `LIPS`) with the sales order (`VBAK`, `VBAP`), the ship-to country (`KNA1-LAND1`, `T005T`), the shipping condition or transport group for the mode, goods issue date (`WADAT_IST`), and the proof of delivery date (`PODAT`) for the arrival |
| `ExportSummaryBy*` | aggregate CDS views over the `ExportShipment` view, so SAP does the totalling |

The data is read with the shared management login, so the app limits who can ask for it (role
`management` or `admin`). Large tables must be selective on the filter fields used above:
`ShipmentDate`, `Country`, `ShipmentStatus`, `CompanyCode`.
