# The standard Sales Order service in butterfly

Butterfly (the mock SAP) answers SAP's own Sales Order API, built from the real specifications and
sample responses saved in `docs/sap/standard/`. It is read only for now. The old custom service
(`.../zui_sales_o4/...`) is unchanged.

## URLs

| Version | Base | Entity sets |
|---|---|---|
| V4 | `/sap/opu/odata4/sap/api_salesorder/srvd_a2x/sap/salesorder/0001/` | `SalesOrder`, `SalesOrderItem`, and the other 9 sets of the real service (answer empty) |
| V2 | `/sap/opu/odata/sap/API_SALES_ORDER_SRV/` | `A_SalesOrder`, `A_SalesOrderItem`, and the other sets (answer empty) |

Also served: `$metadata` (the real file, byte for byte), `/<set>/$count` (plain text),
`<set>('<key>')`, `SalesOrder('<key>')/_Item` (V4) and `A_SalesOrder('<key>')/to_Item` (V2),
`SalesOrderItem(SalesOrder='..',SalesOrderItem='..')`. Keys work with or without leading zeros.

## What each version does

| | V4 | V2 |
|---|---|---|
| List wrapper | `value`, `@odata.context`, `@odata.metadataEtag` | `d.results` with `__metadata` and deferred links |
| Count | `$count=true` gives `@odata.count` | `$inlinecount=allpages` gives `d.__count` (string) |
| Dates, amounts | ISO dates, amounts as JSON numbers | `/Date(ms)/`, amounts as strings |
| `$filter` | the V4 subset our parser knows | the same, plus `datetime'...'` literals and `10M` decimals |
| `$select`, `$orderby`, `$top`, `$skip` | yes | yes |
| `$expand` | `_Item`, also `_Item($select=a,b)` | `to_Item` |
| `$apply` | `groupby((fields),aggregate(Amount with sum as Alias))`, also after `filter(...)/` | refused (400) |
| Company | `BillingCompanyCode` | no company field |

Etags: V2 rows carry the real kind, `W/"datetimeoffset'2016-09-02T06%3A15%3A47.1257050Z'"`, built from the last change time; the create and change phase must compare `If-Match` against that same string. V4 etags are opaque (`W/"..."`) as in SAP.

Refusals copy the sandbox: an amount filter without `TransactionCurrency` (V4), `$orderby` on an
aggregate alias, `countdistinct` (501), unknown properties, each in the service's own error body.

## What is stored, and how it maps

The stored order gained `sales_organization`, `distribution_channel`, `division` and
`purchase_order_by_customer`. The sales organization follows the company code through one table
(`SALES_ORGANIZATIONS` in `domain/entities/master_data.py`) unless it is given. Item units are SAP's
internal unit; the ISO unit comes from `ISO_UNITS`. Customer name, country and the rupee amounts are
not in SAP's order and are not in these responses.

## Assumptions not copied from a real sample

Behavior with no sample to copy, to be checked against a real system: the 404 body for an unknown key
(both versions), the V2 message for a malformed `$filter`, the V2 and V4 handling of options outside
the list above (answered as an invalid option), and the V2 `$expand` of anything but `to_Item`.

## What is not here yet

Create and change in the standard body (butterfly 22), the standard customer and business partner
service, schedule lines, partners and texts with data, and the other standard services (billing
document, purchase order, material document, and the rest of the study).
