# shared/14 master-data-study

## Goal
Decide which of SAP's released master data services give workspace the lists it needs for dropdowns (materials with description and base unit, plants by company, customers, suppliers), and save their real definitions and samples, so butterfly can mirror them and the forms stop asking users to type master data. The result is a mapping document and saved real samples; no code changes.

## Why
The requisition form (workspace-web 05) and the sales order form ask users to type material, plant, unit and customer. In SAP these are picked from master data, and the base unit follows the material. Butterfly holds this data internally but has no service a screen can read.

## Behavior
- A document `docs/sap/master-data-mapping.md` with one section each for: product (material master: number, description, base unit, material group, type), plant (and its company), customer, supplier; and the unit of measure of a product.
- For each: the service (name, version, V4 first, V2 only where no V4 exists, 2022 availability), entity sets, the key and the fields workspace needs, how to list by company or plant, how to search by number or description, paging, and the real error cases the sandbox shows.
- A decision per need: `standard` (read the service as it is), or what is missing (for example plants by company code).
- Real samples saved under `docs/sap/standard/<service>/` as in shared 12 and 13 (`$metadata`, a list, one item, filtered and searched lists, errors). Only public Hub sandbox data; the key is never saved.
- A follow-up plan: butterfly phase(s) to serve the services over its master data, workspace-api read routes, workspace-web dropdowns for the requisition form and the sales order form, with sizes and order. The owner agrees the plan before any code.

## Acceptance cases
- Every need above has a section with service, version, entity, key, fields, a search example and an error example.
- The real definitions and samples of each service named are saved, and none contains a key.
- Every rule is tagged with its source (sandbox sample or SAP page) or listed as an assumption with who can confirm it.
- The follow-up plan is agreed by the owner.

## Out of scope
Any code change, writes to master data, cost centers, banks and the other master data not needed by the order and requisition forms, the real SAP system.

## Depends on
shared 12 and 13 (the method and the saved samples).
