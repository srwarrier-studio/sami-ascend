TABLES = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS company (code TEXT PRIMARY KEY, name TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS customer (
    customer_id TEXT PRIMARY KEY, name TEXT NOT NULL, country TEXT NOT NULL, company_code TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS material (
    material_id TEXT PRIMARY KEY, description TEXT NOT NULL, unit TEXT NOT NULL, price INTEGER NOT NULL, company_code TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sales_order (
    sales_order TEXT PRIMARY KEY,
    sales_order_type TEXT NOT NULL,
    sold_to_party TEXT NOT NULL,
    customer_name TEXT,
    order_date TEXT NOT NULL,
    requested_delivery_date TEXT,
    transaction_currency TEXT NOT NULL,
    total_net_amount INTEGER NOT NULL,
    overall_status TEXT NOT NULL,
    created_by_user TEXT NOT NULL,
    creation_date_time TEXT NOT NULL,
    last_change_date_time TEXT NOT NULL,
    company_code TEXT NOT NULL,
    country TEXT NOT NULL,
    origin TEXT NOT NULL DEFAULT 'seed',
    total_net_amount_local INTEGER NOT NULL DEFAULT 0,
    local_currency TEXT NOT NULL DEFAULT 'INR'
);
CREATE INDEX IF NOT EXISTS sales_order_by_date ON sales_order (order_date, transaction_currency, company_code);

CREATE TABLE IF NOT EXISTS sales_order_item (
    sales_order TEXT NOT NULL REFERENCES sales_order (sales_order) ON DELETE CASCADE,
    sales_order_item TEXT NOT NULL,
    material TEXT NOT NULL,
    material_description TEXT,
    quantity INTEGER NOT NULL,
    quantity_unit TEXT NOT NULL,
    net_amount INTEGER NOT NULL,
    net_amount_local INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (sales_order, sales_order_item)
);

CREATE TABLE IF NOT EXISTS sales_contract (
    sales_contract TEXT PRIMARY KEY,
    predecessor_contract TEXT,
    sold_to_party TEXT NOT NULL,
    customer_name TEXT,
    valid_from TEXT NOT NULL,
    valid_to TEXT NOT NULL,
    contract_value INTEGER NOT NULL,
    transaction_currency TEXT NOT NULL,
    contract_status TEXT NOT NULL,
    company_code TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS purchase_delivery (
    purchase_order TEXT NOT NULL,
    purchase_order_item TEXT NOT NULL,
    supplier TEXT NOT NULL,
    supplier_name TEXT,
    material TEXT NOT NULL,
    material_description TEXT,
    order_date TEXT NOT NULL,
    ordered_quantity INTEGER NOT NULL,
    delivered_quantity INTEGER NOT NULL,
    quantity_unit TEXT NOT NULL,
    promised_delivery_date TEXT NOT NULL,
    actual_delivery_date TEXT,
    delivery_status TEXT NOT NULL,
    net_amount INTEGER NOT NULL,
    transaction_currency TEXT NOT NULL,
    company_code TEXT NOT NULL,
    net_amount_local INTEGER NOT NULL DEFAULT 0,
    local_currency TEXT NOT NULL DEFAULT 'INR',
    PRIMARY KEY (purchase_order, purchase_order_item)
);
CREATE INDEX IF NOT EXISTS purchase_delivery_by_date ON purchase_delivery (order_date, transaction_currency, company_code);

CREATE TABLE IF NOT EXISTS customer_invoice (
    invoice TEXT PRIMARY KEY,
    sold_to_party TEXT NOT NULL,
    customer_name TEXT,
    invoice_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    net_amount INTEGER NOT NULL,
    transaction_currency TEXT NOT NULL,
    cleared_amount INTEGER NOT NULL,
    clearing_date TEXT,
    company_code TEXT NOT NULL,
    country TEXT NOT NULL,
    net_amount_local INTEGER NOT NULL DEFAULT 0,
    cleared_amount_local INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS production_order (
    production_order TEXT PRIMARY KEY,
    material TEXT NOT NULL,
    material_description TEXT,
    planned_quantity INTEGER NOT NULL,
    confirmed_quantity INTEGER NOT NULL,
    quantity_unit TEXT NOT NULL,
    planned_start_date TEXT NOT NULL,
    planned_end_date TEXT NOT NULL,
    actual_end_date TEXT,
    production_status TEXT NOT NULL,
    delay_reason TEXT,
    company_code TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS production_order_component (
    production_order TEXT NOT NULL,
    material TEXT NOT NULL,
    material_description TEXT,
    required_quantity INTEGER NOT NULL,
    quantity_unit TEXT NOT NULL,
    company_code TEXT NOT NULL,
    PRIMARY KEY (production_order, material)
);

CREATE TABLE IF NOT EXISTS material_group (code TEXT PRIMARY KEY, name TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS material_group_of (material TEXT PRIMARY KEY, material_group TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS storage_location (
    plant TEXT NOT NULL, code TEXT NOT NULL, name TEXT NOT NULL, company_code TEXT NOT NULL, PRIMARY KEY (plant, code)
);

CREATE TABLE IF NOT EXISTS material_stock (
    material TEXT NOT NULL,
    material_description TEXT,
    material_group TEXT NOT NULL,
    plant TEXT NOT NULL,
    storage_location TEXT NOT NULL,
    stock_quantity INTEGER NOT NULL,
    quantity_unit TEXT NOT NULL,
    stock_value INTEGER NOT NULL,
    currency TEXT NOT NULL,
    reorder_level INTEGER NOT NULL,
    last_movement_date TEXT,
    company_code TEXT NOT NULL,
    PRIMARY KEY (material, plant, storage_location)
);

CREATE TABLE IF NOT EXISTS stock_movement (
    material_document TEXT NOT NULL,
    material_document_item TEXT NOT NULL,
    material_document_year TEXT NOT NULL,
    posting_date TEXT NOT NULL,
    entry_date_time TEXT NOT NULL,
    material TEXT NOT NULL,
    material_description TEXT,
    plant TEXT NOT NULL,
    storage_location TEXT NOT NULL,
    movement_type TEXT NOT NULL,
    debit_credit_code TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    quantity_unit TEXT NOT NULL,
    amount INTEGER NOT NULL,
    currency TEXT NOT NULL,
    company_code TEXT NOT NULL,
    PRIMARY KEY (material_document, material_document_item, material_document_year)
);
CREATE INDEX IF NOT EXISTS stock_movement_by_date ON stock_movement (posting_date, company_code);

CREATE TABLE IF NOT EXISTS stock_value_month (
    posting_period TEXT NOT NULL, currency TEXT NOT NULL, company_code TEXT NOT NULL, stock_value INTEGER NOT NULL,
    PRIMARY KEY (posting_period, currency, company_code)
);

CREATE TABLE IF NOT EXISTS work_center (
    plant TEXT NOT NULL, code TEXT NOT NULL, name TEXT NOT NULL, company_code TEXT NOT NULL, PRIMARY KEY (plant, code)
);

CREATE TABLE IF NOT EXISTS production_confirmation (
    confirmation_number TEXT NOT NULL,
    confirmation_counter TEXT NOT NULL,
    production_order TEXT NOT NULL,
    material TEXT NOT NULL,
    material_description TEXT,
    plant TEXT NOT NULL,
    work_center TEXT NOT NULL,
    shift TEXT NOT NULL,
    posting_date TEXT NOT NULL,
    yield_quantity INTEGER NOT NULL,
    scrap_quantity INTEGER NOT NULL,
    target_quantity INTEGER NOT NULL,
    quantity_unit TEXT NOT NULL,
    scrap_reason TEXT,
    run_hours INTEGER NOT NULL,
    yield_value INTEGER NOT NULL,
    scrap_value INTEGER NOT NULL,
    target_value INTEGER NOT NULL,
    currency TEXT NOT NULL,
    company_code TEXT NOT NULL,
    PRIMARY KEY (confirmation_number, confirmation_counter)
);
CREATE INDEX IF NOT EXISTS production_confirmation_by_date ON production_confirmation (posting_date, company_code);

CREATE TABLE IF NOT EXISTS work_center_downtime (
    downtime_number TEXT PRIMARY KEY,
    production_order TEXT,
    plant TEXT NOT NULL,
    work_center TEXT NOT NULL,
    posting_date TEXT NOT NULL,
    downtime_hours INTEGER NOT NULL,
    downtime_cause TEXT NOT NULL,
    company_code TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS work_center_downtime_by_date ON work_center_downtime (posting_date, company_code);

CREATE TABLE IF NOT EXISTS export_shipment (
    shipment TEXT PRIMARY KEY,
    sales_order TEXT NOT NULL,
    sold_to_party TEXT NOT NULL,
    customer_name TEXT,
    country TEXT NOT NULL,
    country_name TEXT,
    transport_mode TEXT NOT NULL,
    shipment_date TEXT NOT NULL,
    expected_arrival_date TEXT NOT NULL,
    actual_arrival_date TEXT,
    shipment_status TEXT NOT NULL,
    net_amount INTEGER NOT NULL,
    currency TEXT NOT NULL,
    document_amount INTEGER NOT NULL,
    document_currency TEXT NOT NULL,
    company_code TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS export_shipment_by_date ON export_shipment (shipment_date, company_code);

CREATE TABLE IF NOT EXISTS cash_payment (
    payment_document TEXT PRIMARY KEY,
    posting_date TEXT NOT NULL,
    direction TEXT NOT NULL,
    payment_type TEXT NOT NULL,
    partner TEXT,
    partner_name TEXT,
    expense_category TEXT,
    reference TEXT,
    amount INTEGER NOT NULL,
    currency TEXT NOT NULL,
    document_amount INTEGER NOT NULL,
    document_currency TEXT NOT NULL,
    company_code TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS cash_payment_by_date ON cash_payment (posting_date, company_code);
"""

ADDED_COLUMNS = [
    ("sales_order", "total_net_amount_local", "INTEGER NOT NULL DEFAULT 0"),
    ("sales_order", "local_currency", "TEXT NOT NULL DEFAULT 'INR'"),
    ("sales_order_item", "net_amount_local", "INTEGER NOT NULL DEFAULT 0"),
    ("purchase_delivery", "net_amount_local", "INTEGER NOT NULL DEFAULT 0"),
    ("purchase_delivery", "local_currency", "TEXT NOT NULL DEFAULT 'INR'"),
    ("customer_invoice", "net_amount_local", "INTEGER NOT NULL DEFAULT 0"),
    ("customer_invoice", "cleared_amount_local", "INTEGER NOT NULL DEFAULT 0"),
]

BACKFILL = [
    "UPDATE sales_order SET total_net_amount_local = CASE transaction_currency WHEN 'USD' THEN total_net_amount * 80 ELSE total_net_amount END WHERE total_net_amount_local = 0 AND total_net_amount != 0",
    "UPDATE sales_order_item SET net_amount_local = (SELECT CASE o.transaction_currency WHEN 'USD' THEN sales_order_item.net_amount * 80 ELSE sales_order_item.net_amount END FROM sales_order o WHERE o.sales_order = sales_order_item.sales_order) WHERE net_amount_local = 0 AND net_amount != 0",
]

REPLACED_ON_RESEED = [
    "cash_payment",
    "export_shipment",
    "work_center_downtime",
    "production_confirmation",
    "work_center",
    "stock_value_month",
    "stock_movement",
    "material_stock",
    "material_group_of",
    "material_group",
    "storage_location",
    "production_order_component",
    "production_order",
    "customer_invoice",
    "purchase_delivery",
    "sales_contract",
    "material",
    "customer",
    "company",
]
