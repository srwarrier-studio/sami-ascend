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
    origin TEXT NOT NULL DEFAULT 'seed'
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
    country TEXT NOT NULL
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
"""

REPLACED_ON_RESEED = [
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
