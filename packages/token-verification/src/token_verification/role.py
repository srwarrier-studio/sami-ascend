from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    MANAGEMENT = "management"
    PURCHASE = "purchase"
    STORES = "stores"
    PRODUCTION = "production"
    QUALITY = "quality"
    SALES = "sales"
    ACCOUNTS = "accounts"
