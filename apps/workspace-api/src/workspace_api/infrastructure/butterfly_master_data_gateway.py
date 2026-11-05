import httpx

from workspace_api.domain.entities.master_data import BusinessPartner, Material, MaterialPage, PartnerPage, Plant
from workspace_api.domain.errors import SapUnavailable
from workspace_api.domain.gateways.master_data_gateway import MasterDataGateway
from workspace_api.infrastructure.butterfly_http import send
from workspace_api.infrastructure.settings import Settings

LIST_LIMIT = 1000


def literal(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def any_of(field: str, values: list[str]) -> str:
    return " or ".join(f"{field} eq {literal(value)}" for value in values)


class ButterflyMasterDataGateway(MasterDataGateway):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        timeout = settings.sap_timeout_seconds
        self.product = httpx.Client(base_url=settings.sap_product_url, timeout=timeout, transport=transport)
        self.plant = httpx.Client(base_url=settings.sap_plant_url, timeout=timeout, transport=transport)
        self.partner = httpx.Client(base_url=settings.sap_partner_url, timeout=timeout, transport=transport)

    def rows(self, client: httpx.Client, path: str, **params) -> list[dict]:
        response = send(client, "GET", path, params={"$top": LIST_LIMIT} | params)
        if response.status_code != 200:
            raise SapUnavailable(f"unexpected status {response.status_code}")
        body = response.json()
        return body["d"]["results"] if "d" in body else body["value"]

    def plants(self, plants: list[str]) -> list[Plant]:
        if not plants:
            return []
        rows = self.rows(self.plant, "Plant", **{"$filter": any_of("Plant", plants), "$orderby": "Plant", "$select": "Plant,PlantName"})
        return [Plant(row["Plant"], row["PlantName"]) for row in rows]

    def materials(self, query: str | None, plants: list[str], top: int, skip: int) -> MaterialPage:
        if not plants:
            return MaterialPage([], 0)
        held: dict[str, dict] = {}
        for row in self.rows(self.product, "ProductPlant", **{"$filter": any_of("Plant", plants), "$select": "Product,Plant,BaseUnit,BaseISOUnit"}):
            entry = held.setdefault(row["Product"], {"plants": [], "unit": row["BaseUnit"], "iso": row["BaseISOUnit"]})
            entry["plants"].append(row["Plant"])
        found = sorted(held)
        if query:
            text = literal(query)
            by_number = self.rows(self.product, "Product", **{"$filter": f"startswith(Product,{text})", "$select": "Product"})
            by_description = self.rows(self.product, "ProductDescription", **{"$filter": f"contains(ProductDescription,{text})", "$select": "Product"})
            matched = {row["Product"] for row in by_number + by_description}
            found = [number for number in found if number in matched]
        page = found[skip : skip + top]
        if not page:
            return MaterialPage([], len(found))
        details = {r["Product"]: r for r in self.rows(self.product, "Product", **{"$filter": any_of("Product", page), "$select": "Product,ProductType,ProductGroup"})}
        descriptions = {
            r["Product"]: r["ProductDescription"]
            for r in self.rows(self.product, "ProductDescription", **{"$filter": f"Language eq 'EN' and ({any_of('Product', page)})", "$select": "Product,ProductDescription"})
        }
        materials = [
            Material(number, descriptions.get(number, ""), held[number]["unit"], held[number]["iso"], details[number]["ProductGroup"], details[number]["ProductType"], sorted(held[number]["plants"]))
            for number in page
        ]
        return MaterialPage(materials, len(found))

    def customers(self, query: str | None, companies: list[str], top: int, skip: int) -> PartnerPage:
        return self.partners(("A_CustomerCompany", "A_Customer", "Customer", "CustomerName"), query, companies, top, skip)

    def suppliers(self, query: str | None, companies: list[str], top: int, skip: int) -> PartnerPage:
        return self.partners(("A_SupplierCompany", "A_Supplier", "Supplier", "SupplierName"), query, companies, top, skip)

    def partners(self, names: tuple[str, str, str, str], query: str | None, companies: list[str], top: int, skip: int) -> PartnerPage:
        company_set, entity, key, name_field = names
        if not companies:
            return PartnerPage([], 0)
        in_company: dict[str, list[str]] = {}
        for row in self.rows(self.partner, company_set, **{"$filter": any_of("CompanyCode", companies), "$select": f"{key},CompanyCode"}):
            in_company.setdefault(row[key], []).append(row["CompanyCode"])
        found = sorted(in_company)
        if query:
            text = literal(query)
            by_number = self.rows(self.partner, entity, **{"$filter": f"startswith({key},{text})", "$select": key})
            by_name = self.rows(self.partner, entity, **{"$filter": f"substringof({text},{name_field})", "$select": key})
            matched = {row[key] for row in by_number + by_name}
            found = [number for number in found if number in matched]
        page = found[skip : skip + top]
        if not page:
            return PartnerPage([], len(found))
        names_of = {r[key]: r[name_field] for r in self.rows(self.partner, entity, **{"$filter": any_of(key, page), "$select": f"{key},{name_field}"})}
        return PartnerPage([BusinessPartner(number, names_of.get(number, ""), sorted(in_company[number])) for number in page], len(found))
