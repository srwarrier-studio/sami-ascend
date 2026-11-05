# Customer onboarding: the flow and SAP's side

Source tags: **[sample]** real Hub sandbox response or definition saved under `docs/sap/standard/api_business_partner-v2/`; **[public]** an SAP or SAP community page (listed at the end); **[owner]** a decision of the owner; **[assumption]** to confirm (see the last table). The sandbox is read only, so every write below is **not exercised**.

## 1. The flow [owner]

| Step | Who does it | Request state afterwards | Whose work it is now |
|---|---|---|---|
| Raise the request | `sales` | `requested` | `master-data` |
| Check (duplicate, completeness) | `master-data` | `checked`, or `returned` with a reason | `accounts` (finance), or the sales person |
| Credit limit and payment terms | `accounts` | `approved`, or `returned` with a reason | `master-data`, or the sales person |
| Create the customer in SAP | `master-data` | `created` with the customer number | nobody (done) |
| Fix and resend | the sales person | `requested` | `master-data` |
| Withdraw | the sales person, while open | `withdrawn` | nobody (done) |

Rules: a state can only be left by the role responsible for it; a return always carries a reason; a sales person sees only their own requests; `master-data` and `accounts` see the requests that are or were theirs; `master-data` cannot change the credit limit or payment terms and `accounts` cannot change identity fields; `admin` has no part. `created` is only set when SAP has returned the customer number.

## 2. The request

| Field | Filled by | Goes to SAP field | Where in SAP |
|---|---|---|---|
| Name | sales | `OrganizationBPName1` (to `…4` for long names) | `A_BusinessPartner` [sample: 40 characters each] |
| Search term | sales (default: first word of the name) | `SearchTerm1` (20) | `A_BusinessPartner` |
| Category | fixed: organisation | `BusinessPartnerCategory` = `2` | `A_BusinessPartner` [sample: `2`] |
| Grouping | master-data | `BusinessPartnerGrouping` (4) | `A_BusinessPartner`; it also chooses the number range [assumption] |
| Country, city, postal code, street, house number, region | sales | `Country` (3), `CityName`, `PostalCode`, `StreetName`, `HouseNumber`, `Region` | `A_BusinessPartnerAddress` (SAP needs the country for the customer record [public]) |
| Language | sales | `Language` (2), `CorrespondenceLanguage` | address and partner |
| Contact (name, e-mail, phone) | sales | e-mail and phone entities of the address | `A_BusinessPartnerAddress` navigation `to_EmailAddress`, `to_PhoneNumber` |
| Tax number | sales | `BPTaxType` (4) and `BPTaxNumber` (20) | `A_BusinessPartnerTaxNumber`; the type codes depend on the country [assumption] |
| Company code | sales proposes, master-data confirms | `CompanyCode` | `A_CustomerCompany` |
| Sales organisation, distribution channel, division | sales proposes, master-data confirms | `SalesOrganization`, `DistributionChannel`, `Division` | `A_CustomerSalesArea` [sample: `1710`/`10`/`00`] |
| Currency | sales | `Currency` (5) | `A_CustomerSalesArea` |
| Incoterms (optional) | sales | `IncotermsClassification` (3) | `A_CustomerSalesArea` |
| **Payment terms** | **finance** | `PaymentTerms` (4) on the company, `CustomerPaymentTerms` (4) on the sales area | `A_CustomerCompany`, `A_CustomerSalesArea` [sample: `0001`, `0004`] |
| **Reconciliation account** | **finance** | `ReconciliationAccount` (10) | `A_CustomerCompany` [sample: `12100000`] |
| **Credit limit** | **finance** | not in this service | see section 3 |

The history of every step (who, what, when, reason) is part of the request and lives in workspace.

## 3. SAP's side

- **Service.** `API_BUSINESS_PARTNER`, V2, `/sap/opu/odata/sap/API_BUSINESS_PARTNER/`. No V4 exists for it (confirmed by the owner in `master-data-mapping.md`).
- **A customer is created through a business partner.** In the saved definition `A_Customer` is `creatable="false"` and `A_BusinessPartner` is creatable [sample]. A customer is created by creating the business partner with the customer roles [public]. The sandbox only reads, so this is **not exercised**.
- **One request, deep insert.** The business partner, its roles, address, customer, company code data and sales area data can go in one request with the `to_…` navigation properties, and SAP saves all or none [public]. `A_BusinessPartner` navigations [sample]: `to_BusinessPartnerRole`, `to_BusinessPartnerAddress`, `to_BusinessPartnerTax`, `to_Customer`; `A_Customer`: `to_CustomerCompany`, `to_CustomerSalesArea`.
- **Roles** [public]: `FLCU00` (customer, financial accounting view) and `FLCU01` (customer, sales view), both in `A_BusinessPartnerRole` (`BusinessPartnerRole`, 6 characters [sample]). A requirement for the customer record is the country in the address [public].
- **Create body** (shape from the definitions; values are examples, not real data):
  ```
  POST /sap/opu/odata/sap/API_BUSINESS_PARTNER/A_BusinessPartner
  { "BusinessPartnerCategory": "2", "BusinessPartnerGrouping": "<grouping>", "OrganizationBPName1": "Harborline Nutrition LLC", "SearchTerm1": "HARBORLINE",
    "to_BusinessPartnerRole": { "results": [ {"BusinessPartnerRole": "FLCU00"}, {"BusinessPartnerRole": "FLCU01"} ] },
    "to_BusinessPartnerAddress": { "results": [ {"Country": "US", "CityName": "…", "PostalCode": "…", "StreetName": "…", "Language": "EN"} ] },
    "to_Customer": { "CustomerAccountGroup": "<group>",
      "to_CustomerCompany": { "results": [ {"CompanyCode": "INA1", "ReconciliationAccount": "<account>", "PaymentTerms": "<terms>"} ] },
      "to_CustomerSalesArea": { "results": [ {"SalesOrganization": "…", "DistributionChannel": "…", "Division": "…", "Currency": "USD", "CustomerPaymentTerms": "<terms>"} ] } } }
  ```
  The response is the created business partner with its number in `BusinessPartner` (and `Customer`, equal to it in a standard system [assumption]).
- **Number.** `BusinessPartner` and `Customer` are 10-character keys [sample]. The sandbox returns `202`, `203`, `1710` and `17100001` without leading zeros [sample], which shows the format is chosen per system. A new number comes from the number range of the grouping when none is sent [assumption]. **The real format of this company is a question for the consultants; butterfly will not invent one.**
- **Account group.** Customers in the sandbox carry `CustomerAccountGroup` `CUST` [sample]; which group the company uses is a question for the consultants.
- **Credit limit.** Not in `API_BUSINESS_PARTNER`: `A_BPCreditWorthiness` holds credit standing and rating, not the limit [sample]. The limit lives in SAP's credit management, with its own service or screen; which one this company uses is a question for the consultants. Until then the request carries the limit and it is written down by hand in SAP, or held on the request only.
- **Duplicates.** The service definition has no duplicate check. Workspace runs its own at step 2 by searching existing partners by name and country (`search-by-name` sample), and shows hits to the master data person. SAP's own duplicate warning, if configured, would come back as a refusal [assumption].
- **Refusals.** Errors come back in SAP's standard error body (`error.code`, `error.message.value`) [sample: read errors]. Which codes a failed create gives (missing country, unknown role, number range exhausted, unknown payment terms) is not visible in the sandbox; butterfly will return the same body shape with SAP-style messages and the master data person sees them on the request.

## 4. Roles and boards

- **New role `master-data`:** added to `token-verification` `Role`, to auth-api's role list and to admin-web's user form; `accounts` is finance. No change to `admin`.
- **Board lanes** (workspace-api 07 registry, when it resumes): `sales`: "Returned to you" (do) and "Your requests in progress" (chase); `master-data`: "Customer requests to check" (do) and "Approved, ready to create" (do); `accounts`: "Customer requests for credit and terms" (do). Age counts from the date the request entered its current state, which workspace knows because it stores the history.
- **Where the customer shows up:** in the Customer dropdown of New sales order, which already reads `API_BUSINESS_PARTNER` through butterfly.

## 5. Follow-up plan (order and size)

1. **Role `master-data`** in `token-verification`, auth-api and admin-web. Small.
2. **butterfly 25 customer-create:** `POST A_BusinessPartner` with deep insert, roles, number range through `NumberRange` (butterfly 24), SAP-style refusals, the customer visible in the existing read services. Medium.
3. **workspace-api 08 customer-requests:** the request store and state machine, the routes for each step and role, the duplicate search, the create through butterfly, history. Large, in task groups: store and states, routes and rules, create and duplicates.
4. **workspace-web 11 customer-requests:** the request form, the sales person's list, the master data and finance queues with their actions, history on the request page. Large.
5. **Resume the work board** (workspace-api 07 route, workspace-web 09 home) with the three roles' lanes. Small to medium.
6. **Supplier and material onboarding** reuse the same request pattern. Later.

## 6. Assumptions and questions

| # | Assumption or question | Who can answer |
|---|---|---|
| 1 | The real customer number format and number ranges, and which `BusinessPartnerGrouping` creates customers | consultants |
| 2 | The customer account group, reconciliation account and payment terms codes to offer finance | consultants, finance |
| 3 | How the credit limit is stored (credit management service or screen) and how it can be written | consultants, finance |
| 4 | Tax number types for each country the company sells to | finance |
| 5 | Whether a duplicate warning is configured in SAP and what it answers | consultants |
| 6 | Whether `Customer` always equals `BusinessPartner` | consultants |
| 7 | The sales organisation, channel and division for each company | consultants |
| 8 | Which refusals a create gives (messages and codes) | consultants (a test create) |

## Sources

- [SAP Community: How to prepare a deep payload for the Business Partner master data API](https://community.sap.com/t5/enterprise-resource-planning-blog-posts-by-sap/how-to-prepare-a-deep-payload-for-business-partner-master-data-api-business/ba-p/14278616)
- [SAP Community: Creating a customer in SAP S/4HANA Public Cloud via the OData HTTP adapter](https://community.sap.com/t5/technology-blog-posts-by-members/creating-customer-in-sap-s-4-hana-public-cloud-via-odata-http-adapter/ba-p/13953228)
- [SAP Community: Step 20 with SAP Cloud SDK, create and deep insert](https://community.sap.com/t5/technology-blogs-by-sap/step-20-with-sap-cloud-sdk-create-and-deep-insert-with-the-virtual-data/bc-p/13355804/highlight/true)
- The real definitions and read samples in `docs/sap/standard/api_business_partner-v2/`
