import re
from typing import Any

from butterfly.application.alpha import internal
from butterfly.domain.entities.master_data import SALES_ORGANIZATIONS, Customer
from butterfly.domain.errors import ValidationDetail, ValidationFailed
from butterfly.domain.repositories.master_data_repo import MasterDataRepo

CUSTOMER_ROLES = {"FLCU00", "FLCU01"}
COUNTRY = re.compile(r"[A-Z]{2}")
NAME_PARTS = ("OrganizationBPName1", "OrganizationBPName2", "OrganizationBPName3", "OrganizationBPName4")


def rows_of(value: Any) -> list[dict]:
    if isinstance(value, dict) and "results" in value:
        value = value["results"]
    if isinstance(value, dict):
        return [value]
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def text(row: dict, name: str, default: str = "") -> str:
    value = row.get(name)
    return default if value is None else str(value).strip()


class CreateBusinessPartner:
    def __init__(self, master_data: MasterDataRepo):
        self.master_data = master_data

    def execute(self, body: dict) -> Customer:
        details: list[ValidationDetail] = []

        def problem(code: str, message: str, target: str):
            details.append(ValidationDetail(code, message, target))

        name = " ".join(part for part in (text(body, key) for key in NAME_PARTS) if part)
        if not name:
            problem("BP001", "Enter a name for the business partner", "OrganizationBPName1")
        if text(body, "BusinessPartnerCategory", "2") != "2":
            problem("BP002", "Only organizations (category 2) can be created here", "BusinessPartnerCategory")

        customer_rows = rows_of(body.get("to_Customer"))
        roles = {text(row, "BusinessPartnerRole") for row in rows_of(body.get("to_BusinessPartnerRole"))}
        if not customer_rows:
            problem("BP003", "Customer data is missing for the business partner", "to_Customer")
        elif not roles & CUSTOMER_ROLES:
            problem("BP004", "Business partner role FLCU00 or FLCU01 is missing", "to_BusinessPartnerRole")

        address_rows = rows_of(body.get("to_BusinessPartnerAddress"))
        address = address_rows[0] if address_rows else {}
        country = text(address, "Country")
        if not country:
            problem("BP005", "Enter a country in the address", "to_BusinessPartnerAddress/Country")
        elif not COUNTRY.fullmatch(country):
            problem("BP006", f"Country {country} does not exist", "to_BusinessPartnerAddress/Country")

        customer = customer_rows[0] if customer_rows else {}
        company_rows = rows_of(customer.get("to_CustomerCompany"))
        company = company_rows[0] if company_rows else {}
        company_code = text(company, "CompanyCode")
        if not company_code:
            problem("BP007", "Enter a company code for the customer", "to_Customer/to_CustomerCompany/CompanyCode")
        elif not self.master_data.company_exists(company_code):
            problem("BP008", f"Company code {company_code} does not exist", "to_Customer/to_CustomerCompany/CompanyCode")

        area_rows = rows_of(customer.get("to_CustomerSalesArea"))
        area = area_rows[0] if area_rows else {}
        currency = text(area, "Currency")
        sales_organization = text(area, "SalesOrganization")
        if currency and not self.master_data.currency_exists(currency):
            problem("BP009", f"Currency {currency} does not exist", "to_Customer/to_CustomerSalesArea/Currency")
        if sales_organization and sales_organization != SALES_ORGANIZATIONS.get(company_code):
            problem("BP010", f"Sales organization {sales_organization} does not belong to company code {company_code}", "to_Customer/to_CustomerSalesArea/SalesOrganization")

        number = text(body, "BusinessPartner")
        if number and not number.isdigit():
            problem("BP011", f"Business partner number {number} must be numeric", "BusinessPartner")
        elif number and self.master_data.get_customer(internal(number)):
            problem("BP012", f"Business partner {number} already exists", "BusinessPartner")

        if details:
            raise ValidationFailed(details)

        tax = rows_of(body.get("to_BusinessPartnerTax"))
        tax_row = tax[0] if tax else {}
        created = Customer(
            internal(number) if number else self.master_data.next_customer_number(),
            name,
            country,
            company_code,
            grouping=text(body, "BusinessPartnerGrouping"),
            account_group=text(customer, "CustomerAccountGroup", "CUST"),
            search_term=text(body, "SearchTerm1") or name.split()[0].upper()[:20],
            language=text(address, "Language") or text(body, "CorrespondenceLanguage", "EN"),
            city=text(address, "CityName"),
            postal_code=text(address, "PostalCode"),
            street=text(address, "StreetName"),
            house_number=text(address, "HouseNumber"),
            region=text(address, "Region"),
            currency=currency,
            payment_terms=text(company, "PaymentTerms") or text(area, "CustomerPaymentTerms"),
            reconciliation_account=text(company, "ReconciliationAccount"),
            incoterms=text(area, "IncotermsClassification"),
            tax_type=text(tax_row, "BPTaxType"),
            tax_number=text(tax_row, "BPTaxNumber"),
        )
        self.master_data.add_customer(created)
        return created
