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

SALES_CONTRACT_FIELDS = {
    "SalesContract": ("sales_contract", FieldType.STRING),
    "PredecessorContract": ("predecessor_contract", FieldType.STRING),
    "SoldToParty": ("sold_to_party", FieldType.STRING),
    "CustomerName": ("customer_name", FieldType.STRING),
    "ValidFrom": ("valid_from", FieldType.DATE),
    "ValidTo": ("valid_to", FieldType.DATE),
    "ContractValue": ("contract_value", FieldType.DECIMAL),
    "TransactionCurrency": ("transaction_currency", FieldType.STRING),
    "ContractStatus": ("contract_status", FieldType.STRING),
}

PURCHASE_DELIVERY_FIELDS = {
    "PurchaseOrder": ("purchase_order", FieldType.STRING),
    "PurchaseOrderItem": ("purchase_order_item", FieldType.STRING),
    "Supplier": ("supplier", FieldType.STRING),
    "SupplierName": ("supplier_name", FieldType.STRING),
    "Material": ("material", FieldType.STRING),
    "MaterialDescription": ("material_description", FieldType.STRING),
    "OrderDate": ("order_date", FieldType.DATE),
    "OrderedQuantity": ("ordered_quantity", FieldType.DECIMAL),
    "DeliveredQuantity": ("delivered_quantity", FieldType.DECIMAL),
    "QuantityUnit": ("quantity_unit", FieldType.STRING),
    "NetAmount": ("net_amount", FieldType.DECIMAL),
    "TransactionCurrency": ("transaction_currency", FieldType.STRING),
    "PromisedDeliveryDate": ("promised_delivery_date", FieldType.DATE),
    "ActualDeliveryDate": ("actual_delivery_date", FieldType.DATE),
    "DeliveryStatus": ("delivery_status", FieldType.STRING),
}

PRODUCTION_ORDER_FIELDS = {
    "ProductionOrder": ("production_order", FieldType.STRING),
    "Material": ("material", FieldType.STRING),
    "MaterialDescription": ("material_description", FieldType.STRING),
    "PlannedQuantity": ("planned_quantity", FieldType.DECIMAL),
    "ConfirmedQuantity": ("confirmed_quantity", FieldType.DECIMAL),
    "QuantityUnit": ("quantity_unit", FieldType.STRING),
    "PlannedStartDate": ("planned_start_date", FieldType.DATE),
    "PlannedEndDate": ("planned_end_date", FieldType.DATE),
    "ActualEndDate": ("actual_end_date", FieldType.DATE),
    "ProductionStatus": ("production_status", FieldType.STRING),
    "DelayReason": ("delay_reason", FieldType.STRING),
}

PRODUCTION_ORDER_COMPONENT_FIELDS = {
    "ProductionOrder": ("production_order", FieldType.STRING),
    "Material": ("material", FieldType.STRING),
    "MaterialDescription": ("material_description", FieldType.STRING),
    "RequiredQuantity": ("required_quantity", FieldType.DECIMAL),
    "QuantityUnit": ("quantity_unit", FieldType.STRING),
}

PURCHASE_SUMMARY_BY_DAY_FIELDS = SALES_SUMMARY_BY_DAY_FIELDS

PURCHASE_SUMMARY_BY_SUPPLIER_FIELDS = {
    "Supplier": ("supplier", FieldType.STRING),
    "SupplierName": ("supplier_name", FieldType.STRING),
    "OrderDate": ("order_date", FieldType.DATE),
    "TotalNetAmount": ("total_net_amount", FieldType.DECIMAL),
    "OrderCount": ("order_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
}

PURCHASE_SUMMARY_BY_MATERIAL_FIELDS = SALES_SUMMARY_BY_MATERIAL_FIELDS
