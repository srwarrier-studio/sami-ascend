class SalesOrderNotFound(Exception):
    def __init__(self, sales_order: str):
        super().__init__(sales_order)
        self.sales_order = sales_order
