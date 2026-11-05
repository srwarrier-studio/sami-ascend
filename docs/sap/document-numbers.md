# How SAP numbers its documents

Research for butterfly, so the mock hands out numbers the way S/4HANA does. Labels: **[sample]** is a
value seen in a real sandbox response in `docs/sap/standard/`, **[public]** comes from SAP public
documentation or well-known standard customizing, **[verify]** must be confirmed on the company's own system.

## The mechanism

- Every document type draws its number from a **number range object** (transaction `SNRO`), split into
  **intervals**. Each interval is **internal** (the system gives the next number) or **external** (the user types one
  inside the interval). Documents created through an API use the internal interval of their type [public].
- The document type (for example `NB`, `RE`, `KR`) points to the interval it draws from. Standard customizing ships
  fixed intervals and the cloud edition restricts changing the reserved ones [public].
- Some objects are **year dependent**: the same number can exist again in the next fiscal year, so the year is part
  of the key. Material documents, supplier invoices and accounting documents are year dependent; purchase
  requisitions, purchase orders and sales documents are not [public].
- Accounting documents are numbered **per company code and fiscal year**, so the key is company code, number and year [public].
- Numbers are taken in blocks (number range buffering), so a **gap can appear** and a number is **never reused**.
  Numbers always grow, but the mock must not promise "no gaps" [public].
- A number is a fixed-length character field of digits, kept with its leading zeros inside SAP. What an API shows depends
  on the service: every sample below is shown exactly as the sandbox returned it.

## Document by document

| Document | API field | Format seen | Key | Range and notes |
|---|---|---|---|---|
| Purchase requisition | `PurchaseRequisition` | `10000000`, `10000010` [sample] | number | Internal. Item step 10. Type `NB` [sample] |
| Purchase order | `PurchaseOrder` | `4500000011`, `4500000012` [sample] | number | Internal interval `4500000000` to `4599999999`, external `4100000000` to `4199999999` [public]. Item step 10 |
| Goods receipt (material document) | `MaterialDocument` + `MaterialDocumentYear` | `4900000121`, `5000000050`, year `2016` [sample] | year + number | Year dependent. Items `1`, `2` in the sample, `0001` in some services [sample]. Movement `101` receipt, `102` reversal, `561` initial stock [sample] |
| Supplier invoice | `SupplierInvoice` + `FiscalYear` | `5100008273`, `5100043603`, year `2016` [sample] | number + year | Year dependent. Accounting document type `RE` [sample]. Item numbers `1`, `2`.. [sample] |
| Accounting document of the invoice | `AccountingDocument` / `JournalEntry` | same number as the invoice in the sample [sample] | company code + number + year | In standard SAP the invoice document and its accounting document share the number when both ranges agree [public] |
| Other accounting documents | `AccountingDocument` | `100000032`, type `SA` [sample] | company code + number + year | One range per document type (`KR` vendor invoice, `KZ` vendor payment, `KG` vendor credit memo, `DR` customer invoice, `DZ` customer payment, `SA` G/L, `AB` general). Example numbers in SAP's help text: `DR 1600000120`, `DZ 1400000077` [public]. Exact ranges: [verify] |
| Sales order | `SalesOrder` | `1`, `2`, `43103`, `43113` in the V2 sandbox: **no leading zeros**, key `A_SalesOrder('43103')` [sample] | number | Item step 10. Type `OR` [sample] |
| Outbound delivery, billing document | `DeliveryDocument`, `BillingDocument` | classic ranges start `80xxxxxxxx` and `90xxxxxxxx` [public] | number | [verify] |

Notes that matter for the mock:
- Different documents of one flow have **different number families**: the order `45...`, the goods receipt `49...`/`50...`,
  the invoice `51...`. A document number alone does not say which type it is; the key and the service do.
- A goods receipt points back to the order with `PurchaseOrder` and `PurchaseOrderItem`; an invoice item points to the order item and
  the goods receipt (`ReferenceDocument` is a material document) [sample].

## What butterfly does today

| Document | Butterfly now | Matches the research |
|---|---|---|
| Purchase requisition | 8 digits from `10000000`, next = highest + 1 | yes [sample] |
| Material document | `4900000000 + n`, 10 digits, with `MaterialDocumentYear` | yes [sample] |
| Sales order | 10 digits with zeros (`0000020001`), next = highest + 1 | **no**: the sandbox returns numbers without leading zeros (`43103`) |
| Customer, supplier | 10 digits with zeros (`0000100001`, `0000200001`) | **no**: the sandbox returns `17100001` (customer) and `17300001` (supplier), no leading zeros |
| Purchase order, supplier invoice, accounting document, payment | not built yet | to build with the families above |

Finding: the sandbox services show numeric keys the way SAP's conversion exit prints them, without leading zeros, for
sales orders, customers and suppliers. Butterfly pads them to ten digits. Both forms mean the same number inside SAP, but
the apps would see different strings on go-live. Butterfly should return the unpadded form and accept either on input.
Whether the company's own system pads (for example when it stores `0000100001` as a text key) is a [verify] question.

## Rules for the butterfly implementation

1. One small number-range class per document family: a start, a length, an internal interval, and a `next` that never reuses a number.
2. Year dependent documents keep the year in the key, and their numbers restart per year.
3. Accounting documents key on company code, number and year, per document type.
4. Items count in steps of 10 for requisition, order and sales order; material and invoice items count 1, 2, 3.
5. No code may read meaning from a number (no prefix tests); the family is decided by the service.
6. Nothing promises gapless numbers. A test checks "always higher, never repeated".
7. Where the real format is only [verify], keep the value in one place and list it in `docs/sap/consultant-questions.md`.

## Questions for the consultants

- Number range intervals in use per document type: purchase requisition, purchase order, material documents,
  supplier invoice, and the accounting document types `RE`, `KR`, `KZ`, `DR`, `DZ`.
- Whether accounting document numbers are year dependent in the company's codes, and whether the invoice and its accounting
  document share a number.
- Whether sales order numbers are returned padded to ten digits by the service in use.
- Whether any document type uses an external interval (numbers typed by the user).

## Sources

- [SAP Knowledge Base: number range intervals for purchasing documents](https://userapps.support.sap.com/sap/support/knowledge/en/3601548)
- [SAP Community: Want to learn about number ranges](https://community.sap.com/t5/enterprise-resource-planning-blog-posts-by-members/want-to-learn-about-number-ranges/ba-p/13095430)
- [SAP Help: document number assignment](https://help.sap.com/saphelp_46C/helpdata/EN/f8/6cec6eb435d1118b3f0060b03ca329/content.htm)
- [SAP Help: Financial Accounting general topics, documents and document types](https://help.sap.com/docs/SAP_ERP/6a49d1604ffc4b908f9f78fba3824187?locale=en-US&state=PRODUCTION&version=6.18.latest) (SAP ERP 6.0, so older than S/4HANA)
- Real sandbox responses in `docs/sap/standard/`
