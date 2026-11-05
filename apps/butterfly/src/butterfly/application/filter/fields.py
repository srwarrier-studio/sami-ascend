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
    "CompanyCode": ("company_code", FieldType.STRING),
    "Country": ("country", FieldType.STRING),
    "TotalNetAmountLocal": ("total_net_amount_local", FieldType.DECIMAL),
    "LocalCurrency": ("local_currency", FieldType.STRING),
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
    "CompanyCode": ("company_code", FieldType.STRING),
    "TotalNetAmountLocal": ("total_net_amount_local", FieldType.DECIMAL),
    "LocalCurrency": ("local_currency", FieldType.STRING),
}

SALES_SUMMARY_BY_CUSTOMER_FIELDS = {
    "SoldToParty": ("sold_to_party", FieldType.STRING),
    "CustomerName": ("customer_name", FieldType.STRING),
    "OrderDate": ("order_date", FieldType.DATE),
    "TotalNetAmount": ("total_net_amount", FieldType.DECIMAL),
    "OrderCount": ("order_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
    "TotalNetAmountLocal": ("total_net_amount_local", FieldType.DECIMAL),
    "LocalCurrency": ("local_currency", FieldType.STRING),
}

SALES_SUMMARY_BY_MATERIAL_FIELDS = {
    "Material": ("material", FieldType.STRING),
    "MaterialDescription": ("material_description", FieldType.STRING),
    "OrderDate": ("order_date", FieldType.DATE),
    "TotalQuantity": ("total_quantity", FieldType.DECIMAL),
    "QuantityUnit": ("quantity_unit", FieldType.STRING),
    "TotalNetAmount": ("total_net_amount", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
    "TotalNetAmountLocal": ("total_net_amount_local", FieldType.DECIMAL),
    "LocalCurrency": ("local_currency", FieldType.STRING),
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
    "CompanyCode": ("company_code", FieldType.STRING),
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
    "CompanyCode": ("company_code", FieldType.STRING),
    "NetAmountLocal": ("net_amount_local", FieldType.DECIMAL),
    "LocalCurrency": ("local_currency", FieldType.STRING),
}

CUSTOMER_INVOICE_FIELDS = {
    "Invoice": ("invoice", FieldType.STRING),
    "SoldToParty": ("sold_to_party", FieldType.STRING),
    "CustomerName": ("customer_name", FieldType.STRING),
    "InvoiceDate": ("invoice_date", FieldType.DATE),
    "DueDate": ("due_date", FieldType.DATE),
    "NetAmount": ("net_amount", FieldType.DECIMAL),
    "TransactionCurrency": ("transaction_currency", FieldType.STRING),
    "ClearedAmount": ("cleared_amount", FieldType.DECIMAL),
    "ClearingDate": ("clearing_date", FieldType.DATE),
    "CompanyCode": ("company_code", FieldType.STRING),
    "Country": ("country", FieldType.STRING),
}

RECEIVABLES_SUMMARY_FIELDS = {
    "AsOfDate": ("as_of_date", FieldType.DATE),
    "OpenAmount": ("open_amount", FieldType.DECIMAL),
    "OverdueAmount": ("overdue_amount", FieldType.DECIMAL),
    "OpenCount": ("open_count", FieldType.DECIMAL),
    "OverdueCount": ("overdue_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
    "OpenAmountLocal": ("open_amount_local", FieldType.DECIMAL),
    "OverdueAmountLocal": ("overdue_amount_local", FieldType.DECIMAL),
    "LocalCurrency": ("local_currency", FieldType.STRING),
}

RECEIVABLES_BY_CUSTOMER_FIELDS = {
    "SoldToParty": ("sold_to_party", FieldType.STRING),
    "CustomerName": ("customer_name", FieldType.STRING),
    **RECEIVABLES_SUMMARY_FIELDS,
}

RECEIVABLES_AGEING_FIELDS = {
    "AsOfDate": ("as_of_date", FieldType.DATE),
    "AgeBucket": ("age_bucket", FieldType.STRING),
    "OpenAmount": ("open_amount", FieldType.DECIMAL),
    "OpenCount": ("open_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
    "OpenAmountLocal": ("open_amount_local", FieldType.DECIMAL),
    "LocalCurrency": ("local_currency", FieldType.STRING),
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
    "CompanyCode": ("company_code", FieldType.STRING),
}

PRODUCTION_ORDER_COMPONENT_FIELDS = {
    "ProductionOrder": ("production_order", FieldType.STRING),
    "Material": ("material", FieldType.STRING),
    "MaterialDescription": ("material_description", FieldType.STRING),
    "RequiredQuantity": ("required_quantity", FieldType.DECIMAL),
    "QuantityUnit": ("quantity_unit", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}

MATERIAL_STOCK_FIELDS = {
    "Material": ("material", FieldType.STRING),
    "MaterialDescription": ("material_description", FieldType.STRING),
    "MaterialGroup": ("material_group", FieldType.STRING),
    "MaterialGroupName": ("material_group_name", FieldType.STRING),
    "Plant": ("plant", FieldType.STRING),
    "StorageLocation": ("storage_location", FieldType.STRING),
    "StorageLocationName": ("storage_location_name", FieldType.STRING),
    "StockQuantity": ("stock_quantity", FieldType.DECIMAL),
    "QuantityUnit": ("quantity_unit", FieldType.STRING),
    "StockValue": ("stock_value", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "ReorderLevel": ("reorder_level", FieldType.DECIMAL),
    "StockStatus": ("stock_status", FieldType.STRING),
    "LastMovementDate": ("last_movement_date", FieldType.DATE),
    "CompanyCode": ("company_code", FieldType.STRING),
}
STOCK_MOVEMENT_FIELDS = {
    "MaterialDocument": ("material_document", FieldType.STRING),
    "MaterialDocumentItem": ("material_document_item", FieldType.STRING),
    "MaterialDocumentYear": ("material_document_year", FieldType.STRING),
    "PostingDate": ("posting_date", FieldType.DATE),
    "EntryDateTime": ("entry_date_time", FieldType.DATETIME),
    "Material": ("material", FieldType.STRING),
    "MaterialDescription": ("material_description", FieldType.STRING),
    "Plant": ("plant", FieldType.STRING),
    "StorageLocation": ("storage_location", FieldType.STRING),
    "MovementType": ("movement_type", FieldType.STRING),
    "DebitCreditCode": ("debit_credit_code", FieldType.STRING),
    "Quantity": ("quantity", FieldType.DECIMAL),
    "QuantityUnit": ("quantity_unit", FieldType.STRING),
    "Amount": ("amount", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
STOCK_SUMMARY_BY_WAREHOUSE_FIELDS = {
    "Plant": ("plant", FieldType.STRING),
    "StorageLocation": ("storage_location", FieldType.STRING),
    "StorageLocationName": ("storage_location_name", FieldType.STRING),
    "StockValue": ("stock_value", FieldType.DECIMAL),
    "MaterialCount": ("material_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
STOCK_SUMMARY_BY_MATERIAL_GROUP_FIELDS = {
    "MaterialGroup": ("material_group", FieldType.STRING),
    "MaterialGroupName": ("material_group_name", FieldType.STRING),
    "StockValue": ("stock_value", FieldType.DECIMAL),
    "MaterialCount": ("material_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
STOCK_SUMMARY_BY_STATUS_FIELDS = {
    "StockStatus": ("stock_status", FieldType.STRING),
    "StockValue": ("stock_value", FieldType.DECIMAL),
    "MaterialCount": ("material_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
STOCK_VALUE_BY_MONTH_FIELDS = {
    "PostingPeriod": ("posting_period", FieldType.STRING),
    "StockValue": ("stock_value", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
STOCK_MOVEMENT_SUMMARY_BY_DAY_FIELDS = {
    "PostingDate": ("posting_date", FieldType.DATE),
    "ReceiptValue": ("receipt_value", FieldType.DECIMAL),
    "IssueValue": ("issue_value", FieldType.DECIMAL),
    "MovementCount": ("movement_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
STOCK_MOVEMENT_SUMMARY_BY_HOUR_FIELDS = {
    "PostingDate": ("posting_date", FieldType.DATE),
    "PostingHour": ("posting_hour", FieldType.DECIMAL),
    "MovementCount": ("movement_count", FieldType.DECIMAL),
    "CompanyCode": ("company_code", FieldType.STRING),
}
PRODUCTION_CONFIRMATION_FIELDS = {
    "ConfirmationNumber": ("confirmation_number", FieldType.STRING),
    "ConfirmationCounter": ("confirmation_counter", FieldType.STRING),
    "ProductionOrder": ("production_order", FieldType.STRING),
    "Material": ("material", FieldType.STRING),
    "MaterialDescription": ("material_description", FieldType.STRING),
    "Plant": ("plant", FieldType.STRING),
    "WorkCenter": ("work_center", FieldType.STRING),
    "WorkCenterName": ("work_center_name", FieldType.STRING),
    "Shift": ("shift", FieldType.STRING),
    "PostingDate": ("posting_date", FieldType.DATE),
    "YieldQuantity": ("yield_quantity", FieldType.DECIMAL),
    "ScrapQuantity": ("scrap_quantity", FieldType.DECIMAL),
    "TargetQuantity": ("target_quantity", FieldType.DECIMAL),
    "QuantityUnit": ("quantity_unit", FieldType.STRING),
    "ScrapReason": ("scrap_reason", FieldType.STRING),
    "RunHours": ("run_hours", FieldType.DECIMAL),
    "YieldValue": ("yield_value", FieldType.DECIMAL),
    "ScrapValue": ("scrap_value", FieldType.DECIMAL),
    "TargetValue": ("target_value", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
WORK_CENTER_DOWNTIME_FIELDS = {
    "DowntimeNumber": ("downtime_number", FieldType.STRING),
    "ProductionOrder": ("production_order", FieldType.STRING),
    "Plant": ("plant", FieldType.STRING),
    "WorkCenter": ("work_center", FieldType.STRING),
    "WorkCenterName": ("work_center_name", FieldType.STRING),
    "PostingDate": ("posting_date", FieldType.DATE),
    "DowntimeHours": ("downtime_hours", FieldType.DECIMAL),
    "DowntimeCause": ("downtime_cause", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
PRODUCTION_SUMMARY_BY_DAY_FIELDS = {
    "PostingDate": ("posting_date", FieldType.DATE),
    "PlannedHours": ("planned_hours", FieldType.DECIMAL),
    "DowntimeHours": ("downtime_hours", FieldType.DECIMAL),
    "TargetValue": ("target_value", FieldType.DECIMAL),
    "GoodValue": ("good_value", FieldType.DECIMAL),
    "ScrapValue": ("scrap_value", FieldType.DECIMAL),
    "ConfirmationCount": ("confirmation_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
DOWNTIME_SUMMARY_BY_DAY_FIELDS = {
    "PostingDate": ("posting_date", FieldType.DATE),
    "DowntimeCause": ("downtime_cause", FieldType.STRING),
    "DowntimeHours": ("downtime_hours", FieldType.DECIMAL),
    "EventCount": ("event_count", FieldType.DECIMAL),
    "CompanyCode": ("company_code", FieldType.STRING),
}
SCRAP_SUMMARY_BY_DAY_FIELDS = {
    "PostingDate": ("posting_date", FieldType.DATE),
    "ScrapReason": ("scrap_reason", FieldType.STRING),
    "ScrapValue": ("scrap_value", FieldType.DECIMAL),
    "ConfirmationCount": ("confirmation_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
OUTPUT_SUMMARY_BY_LINE_SHIFT_FIELDS = {
    "PostingDate": ("posting_date", FieldType.DATE),
    "WorkCenter": ("work_center", FieldType.STRING),
    "Shift": ("shift", FieldType.STRING),
    "WorkCenterName": ("work_center_name", FieldType.STRING),
    "GoodValue": ("good_value", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
EXPORT_SHIPMENT_FIELDS = {
    "Shipment": ("shipment", FieldType.STRING),
    "SalesOrder": ("sales_order", FieldType.STRING),
    "SoldToParty": ("sold_to_party", FieldType.STRING),
    "CustomerName": ("customer_name", FieldType.STRING),
    "Country": ("country", FieldType.STRING),
    "CountryName": ("country_name", FieldType.STRING),
    "TransportMode": ("transport_mode", FieldType.STRING),
    "ShipmentDate": ("shipment_date", FieldType.DATE),
    "ExpectedArrivalDate": ("expected_arrival_date", FieldType.DATE),
    "ActualArrivalDate": ("actual_arrival_date", FieldType.DATE),
    "ShipmentStatus": ("shipment_status", FieldType.STRING),
    "NetAmount": ("net_amount", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "DocumentAmount": ("document_amount", FieldType.DECIMAL),
    "DocumentCurrency": ("document_currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
EXPORT_SUMMARY_BY_DAY_FIELDS = {
    "ShipmentDate": ("shipment_date", FieldType.DATE),
    "ShipmentCount": ("shipment_count", FieldType.DECIMAL),
    "NetAmount": ("net_amount", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
EXPORT_SUMMARY_BY_DESTINATION_FIELDS = {
    "ShipmentDate": ("shipment_date", FieldType.DATE),
    "Country": ("country", FieldType.STRING),
    "CountryName": ("country_name", FieldType.STRING),
    "ShipmentCount": ("shipment_count", FieldType.DECIMAL),
    "NetAmount": ("net_amount", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
EXPORT_SUMMARY_BY_MODE_FIELDS = {
    "ShipmentDate": ("shipment_date", FieldType.DATE),
    "TransportMode": ("transport_mode", FieldType.STRING),
    "ShipmentCount": ("shipment_count", FieldType.DECIMAL),
    "CompanyCode": ("company_code", FieldType.STRING),
}
CASH_PAYMENT_FIELDS = {
    "PaymentDocument": ("payment_document", FieldType.STRING),
    "PostingDate": ("posting_date", FieldType.DATE),
    "Direction": ("direction", FieldType.STRING),
    "PaymentType": ("payment_type", FieldType.STRING),
    "Partner": ("partner", FieldType.STRING),
    "PartnerName": ("partner_name", FieldType.STRING),
    "ExpenseCategory": ("expense_category", FieldType.STRING),
    "Reference": ("reference", FieldType.STRING),
    "Amount": ("amount", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "DocumentAmount": ("document_amount", FieldType.DECIMAL),
    "DocumentCurrency": ("document_currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
CASH_SUMMARY_BY_DAY_FIELDS = {
    "PostingDate": ("posting_date", FieldType.DATE),
    "Direction": ("direction", FieldType.STRING),
    "PaymentCount": ("payment_count", FieldType.DECIMAL),
    "Amount": ("amount", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
EXPENSE_SUMMARY_BY_DAY_FIELDS = {
    "PostingDate": ("posting_date", FieldType.DATE),
    "ExpenseCategory": ("expense_category", FieldType.STRING),
    "PaymentCount": ("payment_count", FieldType.DECIMAL),
    "Amount": ("amount", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
}
PURCHASE_SUMMARY_BY_DAY_FIELDS = SALES_SUMMARY_BY_DAY_FIELDS

PURCHASE_SUMMARY_BY_SUPPLIER_FIELDS = {
    "Supplier": ("supplier", FieldType.STRING),
    "SupplierName": ("supplier_name", FieldType.STRING),
    "OrderDate": ("order_date", FieldType.DATE),
    "TotalNetAmount": ("total_net_amount", FieldType.DECIMAL),
    "OrderCount": ("order_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
    "TotalNetAmountLocal": ("total_net_amount_local", FieldType.DECIMAL),
    "LocalCurrency": ("local_currency", FieldType.STRING),
}

PURCHASE_SUMMARY_BY_MATERIAL_GROUP_FIELDS = {
    "MaterialGroup": ("material_group", FieldType.STRING),
    "MaterialGroupName": ("material_group_name", FieldType.STRING),
    "OrderDate": ("order_date", FieldType.DATE),
    "TotalNetAmount": ("total_net_amount", FieldType.DECIMAL),
    "OrderCount": ("order_count", FieldType.DECIMAL),
    "Currency": ("currency", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
    "TotalNetAmountLocal": ("total_net_amount_local", FieldType.DECIMAL),
    "LocalCurrency": ("local_currency", FieldType.STRING),
}
PURCHASE_SUMMARY_BY_MATERIAL_FIELDS = SALES_SUMMARY_BY_MATERIAL_FIELDS


STANDARD_V4_ORDER_FIELDS = {
    "SalesOrder": ("sales_order", FieldType.STRING),
    "SalesOrderType": ("sales_order_type", FieldType.STRING),
    "SoldToParty": ("sold_to_party", FieldType.STRING),
    "SalesOrganization": ("sales_organization", FieldType.STRING),
    "DistributionChannel": ("distribution_channel", FieldType.STRING),
    "OrganizationDivision": ("division", FieldType.STRING),
    "CreatedByUser": ("created_by_user", FieldType.STRING),
    "LastChangeDateTime": ("last_change_date_time", FieldType.DATETIME),
    "PurchaseOrderByCustomer": ("purchase_order_by_customer", FieldType.STRING),
    "SalesOrderDate": ("order_date", FieldType.DATE),
    "RequestedDeliveryDate": ("requested_delivery_date", FieldType.DATE),
    "TotalNetAmount": ("total_net_amount", FieldType.DECIMAL),
    "TransactionCurrency": ("transaction_currency", FieldType.STRING),
    "BillingCompanyCode": ("company_code", FieldType.STRING),
    "OverallSDProcessStatus": ("overall_status", FieldType.STRING),
}

STANDARD_V2_ORDER_FIELDS = {name: field for name, field in STANDARD_V4_ORDER_FIELDS.items() if name != "BillingCompanyCode"}

STANDARD_V4_ITEM_FIELDS = {
    "SalesOrder": ("sales_order", FieldType.STRING),
    "SalesOrderItem": ("sales_order_item", FieldType.STRING),
    "Product": ("material", FieldType.STRING),
    "SalesOrderItemText": ("material_description", FieldType.STRING),
    "RequestedQuantity": ("quantity", FieldType.DECIMAL),
    "NetAmount": ("net_amount", FieldType.DECIMAL),
    "TransactionCurrency": ("transaction_currency", FieldType.STRING),
}

STANDARD_V2_ITEM_FIELDS = {("Material" if name == "Product" else name): field for name, field in STANDARD_V4_ITEM_FIELDS.items()}

STANDARD_REQUISITION_FIELDS = {
    "PurchaseRequisition": ("purchase_requisition", FieldType.STRING),
    "PurchaseRequisitionType": ("requisition_type", FieldType.STRING),
    "PurReqnDescription": ("description", FieldType.STRING),
}

STANDARD_REQUISITION_ITEM_FIELDS = {
    "PurchaseRequisition": ("purchase_requisition", FieldType.STRING),
    "PurchaseRequisitionItem": ("purchase_requisition_item", FieldType.STRING),
    "PurchasingDocument": ("purchasing_document", FieldType.STRING),
    "PurchasingDocumentItem": ("purchasing_document_item", FieldType.STRING),
    "PurReqnReleaseStatus": ("release_status", FieldType.STRING),
    "PurchaseRequisitionItemText": ("item_text", FieldType.STRING),
    "Material": ("material", FieldType.STRING),
    "MaterialGroup": ("material_group", FieldType.STRING),
    "RequestedQuantity": ("requested_quantity", FieldType.DECIMAL),
    "BaseUnit": ("base_unit", FieldType.STRING),
    "PurchaseRequisitionPrice": ("price", FieldType.DECIMAL),
    "PurchasingOrganization": ("purchasing_organization", FieldType.STRING),
    "PurchasingGroup": ("purchasing_group", FieldType.STRING),
    "Plant": ("plant", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
    "OrderedQuantity": ("ordered_quantity", FieldType.DECIMAL),
    "DeliveryDate": ("delivery_date", FieldType.DATE),
    "ProcessingStatus": ("processing_status", FieldType.STRING),
    "Supplier": ("supplier", FieldType.STRING),
    "CreatedByUser": ("created_by_user", FieldType.STRING),
    "PurReqCreationDate": ("creation_date", FieldType.DATE),
    "PurReqnItemCurrency": ("currency", FieldType.STRING),
    "ItemNetAmount": ("net_amount", FieldType.DECIMAL),
}

STANDARD_PRODUCT_FIELDS = {
    "Product": ("product", FieldType.STRING),
    "ProductType": ("product_type", FieldType.STRING),
    "ProductGroup": ("product_group", FieldType.STRING),
    "BaseUnit": ("base_unit", FieldType.STRING),
    "BaseISOUnit": ("base_iso_unit", FieldType.STRING),
    "Division": ("division", FieldType.STRING),
    "__description": ("description", FieldType.STRING),
}

STANDARD_PRODUCT_DESCRIPTION_FIELDS = {
    "Product": ("product", FieldType.STRING),
    "Language": ("language", FieldType.STRING),
    "ProductDescription": ("product_description", FieldType.STRING),
}

STANDARD_PRODUCT_PLANT_FIELDS = {
    "Product": ("product", FieldType.STRING),
    "Plant": ("plant", FieldType.STRING),
    "BaseUnit": ("base_unit", FieldType.STRING),
}

STANDARD_PRODUCT_UNIT_FIELDS = {
    "Product": ("product", FieldType.STRING),
    "AlternativeUnit": ("alternative_unit", FieldType.STRING),
    "BaseUnit": ("base_unit", FieldType.STRING),
}

STANDARD_PLANT_FIELDS = {
    "Plant": ("plant", FieldType.STRING),
    "PlantName": ("name", FieldType.STRING),
    "ValuationArea": ("plant", FieldType.STRING),
    "SalesOrganization": ("sales_organization", FieldType.STRING),
    "DefaultPurchasingOrganization": ("purchasing_organization", FieldType.STRING),
    "DistributionChannel": ("distribution_channel", FieldType.STRING),
    "Division": ("division", FieldType.STRING),
    "Language": ("language", FieldType.STRING),
}

STANDARD_CUSTOMER_FIELDS = {
    "Customer": ("customer", FieldType.STRING),
    "CustomerName": ("name", FieldType.STRING),
    "CustomerFullName": ("name", FieldType.STRING),
    "BPCustomerName": ("name", FieldType.STRING),
    "BPCustomerFullName": ("name", FieldType.STRING),
    "CustomerAccountGroup": ("account_group", FieldType.STRING),
}

STANDARD_CUSTOMER_COMPANY_FIELDS = {
    "Customer": ("customer", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
    "CustomerAccountGroup": ("account_group", FieldType.STRING),
}

STANDARD_CUSTOMER_SALES_AREA_FIELDS = {
    "Customer": ("customer", FieldType.STRING),
    "SalesOrganization": ("sales_organization", FieldType.STRING),
    "DistributionChannel": ("distribution_channel", FieldType.STRING),
    "Division": ("division", FieldType.STRING),
    "CustomerAccountGroup": ("account_group", FieldType.STRING),
}

STANDARD_SUPPLIER_FIELDS = {
    "Supplier": ("supplier", FieldType.STRING),
    "SupplierName": ("name", FieldType.STRING),
    "SupplierFullName": ("name", FieldType.STRING),
    "SupplierAccountGroup": ("account_group", FieldType.STRING),
}

STANDARD_SUPPLIER_COMPANY_FIELDS = {
    "Supplier": ("supplier", FieldType.STRING),
    "CompanyCode": ("company_code", FieldType.STRING),
    "SupplierAccountGroup": ("account_group", FieldType.STRING),
}

STANDARD_SUPPLIER_PURCHASING_ORG_FIELDS = {
    "Supplier": ("supplier", FieldType.STRING),
    "PurchasingOrganization": ("purchasing_organization", FieldType.STRING),
    "PurchasingGroup": ("purchasing_group", FieldType.STRING),
    "SupplierAccountGroup": ("account_group", FieldType.STRING),
}
