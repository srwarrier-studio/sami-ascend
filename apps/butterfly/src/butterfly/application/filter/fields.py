from enum import Enum


class FieldType(Enum):
    STRING = "string"
    DATE = "date"
    DATETIME = "datetime"
    DECIMAL = "decimal"


SALES_ORDER_FIELDS = {
    "SalesOrder": ("sales_order", FieldType.STRING),
    "SalesOrderType": ("sales_order_type", FieldType.STRING),
    "SoldToParty": ("sold_to_party", FieldType.STRING),
    "CustomerName": ("customer_name", FieldType.STRING),
    "OrderDate": ("order_date", FieldType.DATE),
    "RequestedDeliveryDate": ("requested_delivery_date", FieldType.DATE),
    "TransactionCurrency": ("transaction_currency", FieldType.STRING),
    "TotalNetAmount": ("total_net_amount", FieldType.DECIMAL),
    "OverallStatus": ("overall_status", FieldType.STRING),
    "CreatedByUser": ("created_by_user", FieldType.STRING),
    "CreationDateTime": ("creation_date_time", FieldType.DATETIME),
    "LastChangeDateTime": ("last_change_date_time", FieldType.DATETIME),
}

SALES_ORDER_ITEM_FIELDS = {
    "SalesOrder": ("sales_order", FieldType.STRING),
    "SalesOrderItem": ("sales_order_item", FieldType.STRING),
    "Material": ("material", FieldType.STRING),
    "MaterialDescription": ("material_description", FieldType.STRING),
    "Quantity": ("quantity", FieldType.DECIMAL),
    "QuantityUnit": ("quantity_unit", FieldType.STRING),
    "NetAmount": ("net_amount", FieldType.DECIMAL),
}

SALES_SUMMARY_BY_DAY_FIELDS = {
    "OrderDate": ("order_date", FieldType.DATE),
    "TotalNetAmount": ("total_net_amount", FieldType.DECIMAL),
    "OrderCount": ("order_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
}

SALES_SUMMARY_BY_CUSTOMER_FIELDS = {
    "SoldToParty": ("sold_to_party", FieldType.STRING),
    "CustomerName": ("customer_name", FieldType.STRING),
    "OrderDate": ("order_date", FieldType.DATE),
    "TotalNetAmount": ("total_net_amount", FieldType.DECIMAL),
    "OrderCount": ("order_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
}

SALES_SUMMARY_BY_MATERIAL_FIELDS = {
    "Material": ("material", FieldType.STRING),
    "MaterialDescription": ("material_description", FieldType.STRING),
    "OrderDate": ("order_date", FieldType.DATE),
    "TotalQuantity": ("total_quantity", FieldType.DECIMAL),
    "QuantityUnit": ("quantity_unit", FieldType.STRING),
    "TotalNetAmount": ("total_net_amount", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
}
