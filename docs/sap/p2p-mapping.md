# Procure to pay: SAP mapping

Source tags: **[sample]** real Hub sandbox response saved under `docs/sap/standard/`; **[doc]** SAP public page; **[assumption]** to confirm (see the assumptions section, not yet written). Study in progress: sections 1 to 6, document flow, assumptions and plan drafted; waiting for the owner's review.

## 1. Purchase requisition (ME51N)

**API.** `API_PURCHASEREQUISITION_2`, OData **V4**, service path `/sap/opu/odata4/sap/api_purchaserequisition_2/srvd_a2x/sap/purchaserequisition/0001/` [sample]. It replaces the deprecated V2 `API_PURCHASEREQ_PROCESS_SRV` [doc, cloud blog 2402]. 2022 on-premise availability: a community post says it did not appear under Add Service on one 2022 system; **to confirm with consultants** (fallback V2 `API_PURCHASEREQ_PROCESS_SRV`). Saved: `docs/sap/standard/api_purchaserequisition_2/`.

**Entity sets** [sample metadata]: `PurchaseReqn` (header, key `PurchaseRequisition`), `PurchaseReqnItem` (key `PurchaseRequisition` + `PurchaseRequisitionItem`), `PurchaseReqnAcctAssgmt` (key adds `PurchaseReqnAcctAssgmtNumber`), `PurchaseReqnDelivAddress`, `PurchaseReqnItemText`. Navigation: header `_PurchaseRequisitionItem`; item `_PurReqn`, `_PurchaseReqnAcctAssgmt`, `_PurchaseReqnDelivAddress`, `_PurchaseReqnItemText`.

**Header fields** [sample]: `PurchaseRequisition`, `PurchaseRequisitionType` (`NB` standard), `PurReqnDescription`, `PurReqnHeaderNote`, `SourceDetermination`, `PurReqnDoOnlyValidation`, `SAP__Messages`.

**Item fields that matter** [sample]: `Material`, `PurchaseRequisitionItemText`, `MaterialGroup`, `RequestedQuantity`, `BaseUnit`, `BaseUnitISOCode`, `PurchaseRequisitionPrice`, `PurReqnPriceQuantity`, `PurReqnItemCurrency`, `ItemNetAmount`, `Plant`, `CompanyCode`, `PurchasingOrganization`, `PurchasingGroup`, `DeliveryDate`, `Supplier`, `FixedSupplier`, `PurchasingInfoRecord`, `PurchaseContract`, `AccountAssignmentCategory`, `RequisitionerName`, `CreatedByUser`, `PurReqCreationDate`, `PurReqnReleaseStatus`, `ProcessingStatus`, `ReleaseIsNotCompleted`, `IsClosed`, `IsDeleted`, `OrderedQuantity`, `PurchasingDocument` and `PurchasingDocumentItem` (the order that consumed it), `GoodsReceiptIsExpected`, `InvoiceIsExpected`.

**Create body.** Header with deep insert of items under `_PurchaseRequisitionItem`; the cloud tutorial creates type `NB` with plant, account assignment category, quantity, price, currency, material, material group, purchasing group, delivery date [doc]. Which fields are mandatory is **not shown by the metadata** (everything is non-nullable in the EDM) and the sandbox refuses writes (405 `OPERATION_NOT_SUPPORTED`), so required fields and the create response are **[assumption], to confirm on a real system**. Quantity change needs both `RequestedQuantity` and `BaseUnitISOCode` [doc, SAP KBA 3742701].

**Number.** Internal range, 8 digits starting `10000000`, items step 10 [sample]. Range object and external ranges: **[assumption]**.

**Statuses** [sample]:
- `ProcessingStatus`: `N` not edited (no order yet), `B` order created (item with `PurchasingDocument` 4500000024, `OrderedQuantity` 10). Other values (`A` RFQ created, `K` contract created) **[assumption]** from SAP's EBAN-BSAKZ.
- `PurReqnReleaseStatus`: `02` and `03` appear. `03` is on the item already ordered; `02` on an unordered, deleted item. Meaning of the codes (`01` not released ... `05` fully released) **[assumption]** until the release strategy is seen.
- Deleted flag `IsDeleted`; closed flag `IsClosed`.

**Query behavior** [sample]: `$top`, `$filter`, `$select`, `$expand` (navigation names above, `_PurReqn...` wrong name gives 400 "expand path contains an invalid property"), `$count` (12211 rows in the sandbox). `$apply aggregate($count)` is not supported (`SADL_GW/001`). Bad filter gives 400 `/IWCOR/CX_OD_EXPR_PARSER_ERROR`; unknown key gives 404.

**Actions** [sample metadata]: `Validate`, `EnablePurReqForPurchasing`, `DiscardPurReqFromPurchasing`, `EnablePurReqItemForPurchasing`, `DiscardPurReqItemFromPurg`. These are bound actions on header and item; the last four move a requisition in or out of purchasing (shopping-cart flow).

**Roles.** `purchase` creates for the plant; approver role to be named. **[assumption]**

## 2. Release (approval): requisition part

**What the API exposes.** Only the result of release: `PurReqnReleaseStatus`, `ReleaseIsNotCompleted`, `ExternalApprovalStatus` on the item [sample]. There is **no release action** in this service (the five actions above are not release). Release is therefore done in SAP (ME54N) or by another service; which one is **to confirm with consultants** (candidates: the Fiori app "Manage Purchase Requisitions" release, or a workflow/approval service). Butterfly must carry its own release action and mirror the item fields.

**How SAP decides who approves** [doc, background]: release strategy by classification (characteristics such as document type, value, plant), release group, release codes, per header or per item; the strategy is applied when the requisition is saved. Real values come from the consultants; butterfly keeps one release-rule table with SAP standard behavior (owner decision).

**Refusal when not released.** Expected: a purchase order cannot reference an unreleased item. Real message **[assumption]**, to be seen in the order step.


**Order release (ME29N)** [sample, `api_purchaseorder_2`]: exposed on the order header only as `ReleaseIsNotCompleted`, `PurgReleaseSequenceStatus`, `ReleaseCode`, `PurchasingReleaseStrategy`, `PurchasingProcessingStatus`; the service has **no actions at all** (metadata lists none), so release is not an API call here. Same consequence as for the requisition: butterfly carries its own release action. Real status values **[assumption]**.

## 3. Purchase order (ME21N)

**API.** `API_PURCHASEORDER_2`, OData **V4**, `/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/` [sample]. V2 fallback `API_PURCHASEORDER_PROCESS_SRV` (`A_PurchaseOrder`) also answers on the sandbox. 2022 on-premise availability **to confirm with consultants**. Saved: `docs/sap/standard/api_purchaseorder_2/`.

**Entity sets** [sample metadata]: `PurchaseOrder` (key `PurchaseOrder`), `PurchaseOrderItem` (+`PurchaseOrderItem`), `PurchaseOrderScheduleLine` (+`ScheduleLine`), `PurchaseOrderAccountAssignment`, `PurchaseOrderPartner`, `PurchaseOrderNote`, `PurchaseOrderItemNote`, `PurchaseOrderSupplierAddress`, `PurOrderItemDeliveryAddress`, `PurOrderItemPricingElement`, `PurchaseOrderInvoicingPlan(+Item)`, `POSubcontractingComponent`. Header navigations: `_PurchaseOrderItem`, `_PurchaseOrderNote`, `_PurchaseOrderPartner`, `_SupplierAddress`. Writes and the create body: sandbox is read only, so create body, required fields and responses are **[assumption]**.

**Header fields** [sample]: `PurchaseOrderType` (`NB`), `CompanyCode`, `PurchasingOrganization`, `PurchasingGroup`, `Supplier`, `PaymentTerms` (`0004`), `CashDiscount1Days/Percent`, `NetPaymentDays`, `DocumentCurrency`, `ExchangeRate`, `PurchaseOrderDate`, `CreationDate`, `CreatedByUser`, `PurchasingProcessingStatus`, `PurchaseOrderDeletionCode`, `PurchasingCompletenessStatus`, `PricingProcedure`, `PurchaseContract`, `IncotermsClassification`.

**Item fields that matter** [sample]: `Material`, `Plant`, `StorageLocation`, `OrderQuantity`, `PurchaseOrderQuantityUnit`, `NetPriceAmount`, `NetPriceQuantity`, `NetAmount`, `PurchasingInfoRecord`, `PurchaseContract(+Item)`, **`PurchaseRequisition` and `PurchaseRequisitionItem`** (the link back), `GoodsReceiptIsExpected`, `InvoiceIsExpected`, `InvoiceIsGoodsReceiptBased`, `GoodsReceiptIsNonValuated`, `IsFinallyInvoiced`, `PurchasingDocumentDeletionCode`, `UnlimitedOverdeliveryIsAllowed`, `OverdelivTolrtdLmtRatioInPct`, `UnderdelivTolrtdLmtRatioInPct`, `GoodsReceiptDurationInDays`, `PlannedDeliveryDurationInDays`.

**Schedule lines** [sample]: key `ScheduleLine`; `ScheduleLineDeliveryDate`, `ScheduleLineOrderQuantity`, `OpenPurchaseOrderQuantity` (what is still to receive), and again `PurchaseRequisition`/`PurchaseRequisitionItem`.

**Number.** Range starts `4500000001`, 10 digits; items step 10 [sample].

**Price and supplier determination.** Item carries `PurchasingInfoRecord` (e.g. `5300000354` on order 4500000011) and `PurchaseContract`; SAP picks supplier and price from info record or contract when source determination runs (`SourceDetermination` on the requisition header). Exact rules **[assumption]**, to read from SAP help.

**Errors** [sample]: 404 unknown order; 400 `/IWCOR/CX_OD_EXPR_PARSER_ERROR` bad filter; 400 `/IWCOR/CX_OD_SELECT_ERROR` unknown select property. Business refusals (unreleased requisition, blocked supplier) **[assumption]**.

**Roles.** `purchase`; approver for release. **[assumption]**

## 4. Goods receipt (MIGO, 101; reversal 102)

**API.** `API_MATERIAL_DOCUMENT_SRV`, OData **V2**, `/sap/opu/odata/sap/API_MATERIAL_DOCUMENT_SRV/` [sample]. Hub title "Material Documents - Read, Create" (V2). The owner searched the Hub for V4 material APIs on 2026-11-04 and found none, so **V2 is the only version** (confirmed); create is supported by the real service. Saved: `docs/sap/standard/api_material_document_srv-v2/`.

**Entity sets** [sample metadata]: `A_MaterialDocumentHeader` (key `MaterialDocumentYear` + `MaterialDocument`), `A_MaterialDocumentItem` (+`MaterialDocumentItem`), `A_SerialNumberMaterialDocument`. Function imports **`Cancel`** and **`CancelItem`** (this is how a document is reversed). Navigations `to_MaterialDocumentItem`, `to_MaterialDocumentHeader`.

**Header** [sample]: `MaterialDocument`, `MaterialDocumentYear`, `InventoryTransactionType` (`WE` goods receipt, `WA` goods issue), `DocumentDate`, `PostingDate`, `CreatedByUser`.

**Item, real goods receipt to a purchase order** [sample `items-movement-101-purchase-order.json`]: `GoodsMovementType 101`, `GoodsMovementRefDocType B`, `PurchaseOrder 4500000001`, `PurchaseOrderItem 10`, `Supplier`, `Material`, `Plant`, `QuantityInEntryUnit 100`, `IsCompletelyDelivered true` (delivery-completed flag), `InventoryStockType 01` (unrestricted), `DebitCreditCode S` (debit). Movement 101 for production orders also exists (ref type `F`); filter by `PurchaseOrder` to get the purchasing ones.

**Reversal** [sample `items-movement-102-production.json`]: `GoodsMovementType 102`, `DebitCreditCode H`, `ReversedMaterialDocument(+Year, Item)` points to the original; original gets `GoodsMovementIsCancelled`. A 102 against a purchase order not seen in the sandbox; same fields **[assumption]**.

**Accounting entry.** Item carries `GLAccount`, `ProfitCenter`, `FiscalYear`, `FiscalYearPeriod`, `CompanyCodeCurrency`, `GdsMvtExtAmtInCoCodeCrcy`; receipt of valuated stock posts stock account against GR/IR clearing **[assumption]**, account determination to confirm with finance.

**What changes on the order after receipt:** order item `OpenPurchaseOrderQuantity` on the schedule line falls by the received quantity; `IsCompletelyDelivered` closes it **[assumption on exact fields; to verify by comparing order 4500000001 before/after in the saved samples]**.

**Over/under delivery tolerance:** per order item `OverdelivTolrtdLmtRatioInPct`, `UnderdelivTolrtdLmtRatioInPct`, `UnlimitedOverdeliveryIsAllowed` [sample metadata]; SAP refuses a receipt beyond the limit; real message **[assumption]**.

**Roles.** `stores`. **[assumption]**

## 5. Invoice verification (MIRO)

**API.** `API_SUPPLIERINVOICE_PROCESS_SRV`, OData **V2**, `/sap/opu/odata/sap/API_SUPPLIERINVOICE_PROCESS_SRV/` [sample]. The owner searched the Hub for a V4 supplier invoice API on 2026-11-04 and found none, so **V2 is the only version** (confirmed). Saved: `docs/sap/standard/api_supplierinvoice_process_srv-v2/`.

**Entity sets** [sample metadata]: `A_SupplierInvoice` (key `SupplierInvoice` + `FiscalYear`), `A_SuplrInvcItemPurOrdRef` (+`SupplierInvoiceItem`; invoice lines against orders), `A_SupplierInvoiceItemGLAcct`, `A_SupplierInvoiceItemMaterial`, `A_SupplierInvoiceTax`, `A_SupplierInvoiceBlock`, `A_SuplrInvcHeaderWhldgTax`, and others. Function imports **`Post`**, **`Release`** (`DiscountDaysHaveToBeShifted`), **`Cancel`** (`PostingDate`, `ReversalReason`) [sample metadata].

**Header** [sample]: `CompanyCode`, `DocumentDate`, `PostingDate`, `SupplierInvoiceIDByInvcgParty` (supplier's own number), `InvoicingParty` (supplier), `DocumentCurrency`, `InvoiceGrossAmount`, `PaymentTerms`, `DueCalculationBaseDate`, `CashDiscount1/2Percent/Days`, `NetPaymentDays`, `PaymentBlockingReason`, `AccountingDocumentType` (`RE`), `JournalEntry` (+year, company code: the accounting document), `SupplierInvoiceStatus` (`5` posted), `SupplierInvoicePaymentStatus` (`Cleared` on invoice 5100000001), `SupplierInvoiceApprovalStatus`, `IsReversed`, `ReverseDocument`, `SupplierInvoiceIsCreditMemo`.

**Item against an order, the three-way link** [sample `one-with-po-items.json`]: `PurchaseOrder 4500000012`, `PurchaseOrderItem 30`, **`ReferenceDocument 5000000054`, `ReferenceDocumentFiscalYear`, `ReferenceDocumentItem`** (the goods receipt material document), `QuantityInPurchaseOrderUnit 20`, `SupplierInvoiceItemAmount 440.00`, `TaxCode`, `IsFinallyInvoiced`.

**Number.** Range starts `5100000001`, 10 digits; accounting document has the same number in the sample [sample].

**Blocked invoices** [sample]: `PaymentBlockingReason A` on invoices 5100043603 and 5100044193; `A_SupplierInvoiceBlock` lists them with `NetDueDate`, `PurchasingGroup`, `PostingDate`. `A` is the block indicator in SAP's standard (blocked for payment, set when the match fails); the reason codes per tolerance key (price, quantity, date, ...) **[assumption]**.

**Tolerance keys.** SAP delivers `AN`, `AP`, `BD`, `BR`, `BW`, `DQ`, `DW`, `KW`, `LA`, `LD`, `PP`, `PS`, `ST`, `VP` **[doc/assumption, from SAP customizing; to confirm with consultants and finance]** with default limits. Not exposed by the API; butterfly keeps them in one table.

**Match.** Invoice quantity and price are compared to order and goods receipt per item; outside tolerance, the invoice posts but is blocked (`PaymentBlockingReason`) and is freed with `Release` **[assumption on exact rules]**. Real refusal messages **[assumption]** (sandbox read only).

**Roles.** `accounts`. **[assumption]**

## 6. Payment (F-53 one invoice, F110 run)

**API.** No payment API was found. What is readable: the accounting document lines via `API_OPLACCTGDOCITEMCUBE_SRV` (`/sap/opu/odata/sap/API_OPLACCTGDOCITEMCUBE_SRV/A_OperationalAcctgDocItemCube`), saved in `docs/sap/standard/api_oplacctgdocitemcube_srv-v2/` [sample]. It carries `AccountingDocument`, `FinancialAccountType`, `IsCleared`, `ClearingAccountingDocument`, `ClearingDate`, `ClearingDocFiscalYear`, `NetDueDate`, `Supplier`, `PurchasingDocument`, `AmountInCompanyCodeCurrency`. A write API for an outgoing payment is **not found**: payment posting (F-53) is **[assumption]**, to be asked of the consultants (candidate: a Journal Entry / payment posting service).

**Effect.** The payment document clears the invoice's supplier line: `IsCleared` true, `ClearingAccountingDocument` set; the invoice shows `SupplierInvoicePaymentStatus` `Cleared` [sample]. Debit supplier, credit bank **[assumption]**.

**Payment run (F110)** and **early-payment discount**: later phases (owner decision).

**Roles.** `accounts`. **[assumption]**

## Document flow

| From | To | Fields | Source |
|---|---|---|---|
| Requisition item | Order item | order item `PurchaseRequisition` + `PurchaseRequisitionItem`; requisition item `PurchasingDocument` + `PurchasingDocumentItem` | sample |
| Requisition item (when ordered) | itself | `ProcessingStatus` `N` to `B`, `OrderedQuantity` filled | sample |
| Order item | Goods receipt item | `PurchaseOrder` + `PurchaseOrderItem` on the material document item, `GoodsMovementRefDocType B` | sample |
| Goods receipt item | Invoice item | `ReferenceDocument` + `ReferenceDocumentFiscalYear` + `ReferenceDocumentItem`, with `PurchaseOrder` + `PurchaseOrderItem` | sample |
| Invoice | Accounting document | `JournalEntry` + `JournalEntryFiscalYear` + `JournalEntryCompanyCode` | sample |
| Accounting document | Payment | `ClearingAccountingDocument`, `ClearingDate` | sample |

What changes on the earlier document when a later one posts: requisition item status and ordered quantity at the order; order open quantity at goods receipt; `IsFinallyInvoiced` at the invoice; invoice `PaymentStatus` at the payment. Exact fields for the order and receipt rows are **[assumption]** until compared before and after.

## Assumptions (all to confirm)

| # | Assumption | Who |
|---|---|---|
| 1 | Release is on; approval rules in one butterfly table with SAP standard behavior (owner decision 2026-11-04) | consultants |
| 2 | Payment: one invoice at a time first, run later, no early-payment discount (owner decision) | finance |
| 3 | SAP standard document types (`NB`), movement types (101, 102) and tolerance keys wherever not known (owner decision) | consultants |
| 4 | Which services are available on the 2022 on-premise system (V4 requisition and order) | consultants |
| 5 | The service that releases a requisition and an order | consultants |
| 6 | Required create fields and create responses of every service (sandbox is read only) | consultants |
| 7 | Business refusal messages (unreleased item, over-delivery, tolerance block) | consultants |
| 8 | Release status codes and processing status codes beyond the ones sampled | consultants |
| 9 | Payment posting service and accounting entries | finance |
| 10 | Roles: `purchase`, `stores`, `accounts`, approver role | owner |

## Follow-up plan (for the owner to agree before any code)

| Order | Phase | Size |
|---|---|---|
| 1 | butterfly: purchase requisition service (V4, read + create + release rules table) | M |
| 2 | butterfly: purchase order (V4, create from requisition items, release) | L |
| 3 | butterfly: material document (V2, goods receipt 101, reversal via `Cancel`) | M |
| 4 | butterfly: supplier invoice (V2, three-way match, tolerance table, `Post`/`Release`/`Cancel`) | L |
| 5 | butterfly: outgoing payment and clearing (own service until the real one is known) | M |
| 6 | butterfly: document flow checks across the five | S |
| 7 | workspace-api gateway per step, then workspace-web screens per step (requisition, order, receipt, invoice, payment) | M each |
